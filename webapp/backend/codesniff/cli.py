"""CodeSniff command line.

    codesniff check --repo URL [--sha SHA | --pr PR_URL] [--mode commit|repo] [--format table|json|markdown]
                    [--fail-on high|medium|never] [--output FILE]
    codesniff scan PATH [--format table|json|markdown|sarif] [--fail-on high|medium|never] [--output FILE]

`check` scores the Java methods changed by a commit or pull request; `scan` scores every method in a local file,
folder or zip (no before/after, so no change bonus). The smell risk score measures code-smell risk; it is not a
probability of bugs or build failure.
Exit codes: 0 = below the --fail-on band, 1 = band reached, 2 = input or GitHub error.
"""
import argparse
import json
import sys

from . import __version__
from .analyze import analyze_path
from .github import GitHubError
from .report import to_sarif
from .resources import PRIMARY, REPO_URL, SMELLS
from .scoring import risk_score
from .service import _entry, _order, _summary, analyze_commit

FAIL_BANDS = {"high": {"High"}, "medium": {"Medium", "High"}, "never": set()}


def scan_result(path, max_files=None):
    rows, skipped, source = analyze_path(path, max_files=max_files)
    methods = _order([_entry(r["file"], None, None, r, scored=False) for r in rows])
    return {"repo": source, "mode": "scan", "target": {"kind": "local scan", "sha": "", "title": source},
            "risk": risk_score([m["points"] for m in methods]), "summary": _summary(methods), "methods": methods,
            "warnings": [f"Skipped {f}: {why}" for f, why in skipped]}, rows


def _fmt_score(risk):
    return "n/a" if risk["score"] is None else f"{risk['score']:.1f}"


def to_table(result):
    r, s = result["risk"], result["summary"]
    out = [f"Smell risk score: {_fmt_score(r)} / 100 ({r['band']})" + ("  [small sample]" if r["small_sample"] else ""),
           r["disclaimer"], ""]
    head = f"{'status':<11}{'change':<9}{'method':<30}{'file:line':<44}{'cc':>8}{'pc':>8}  {'CM':<11}{'LPL':<11}{'points':>6}"
    out += [head, "-" * len(head)]
    for m in result["methods"]:
        b, a = m["before"] or {}, m["after"] or {}
        ba = lambda k: f"{b.get(k, '–')}→{a.get(k, '–')}" if m["change_type"] != "scanned" else str(a.get(k))  # noqa: E731
        loc = f"{m['file']}:{m['start_line']}"
        out.append(f"{m['status']:<11}{m['change_type']:<9}{m['name'][:29]:<30}{loc[-43:]:<44}{ba('cc'):>8}{ba('pc'):>8}  "
                   f"{m['smells']['CM']['zone']:<11}{m['smells']['LPL']['zone']:<11}"
                   f"{'–' if m['points'] is None else format(m['points'], '.2f'):>6}")
    out += ["", f"{s['changed_methods']} scored methods: {s['clear']} clear, {s['borderline']} borderline (candidates to "
                f"review, not verdicts), {s['clean']} clean; introduced {s['introduced']}, worsened {s['worsened']}, "
                f"improved {s['improved']}, deleted {s['deleted']}."]
    out += [f"warning: {w}" for w in result.get("warnings", [])]
    return "\n".join(out)


def to_markdown(result, limit=40):
    r, s, t = result["risk"], result["summary"], result["target"]
    lines = [f"### CodeSniff smell risk: **{_fmt_score(r)} / 100 ({r['band']})**" + (" · ⚠️ small sample" if r["small_sample"] else ""),
             "", f"> {r['disclaimer']}", "",
             f"{s['changed_methods']} changed methods · {s['introduced']} introduced · {s['worsened']} worsened · "
             f"{s['improved']} improved · {s['clean']} clean · {s['deleted']} deleted", "",
             "| Status | Change | Method | File | cc | pc | Complex Method | Long Parameter List |",
             "|---|---|---|---|---|---|---|---|"]
    for m in result["methods"][:limit]:
        b, a = m["before"] or {}, m["after"] or {}
        ba = lambda k: f"{b.get(k, '–')} → {a.get(k, '–')}"  # noqa: E731
        cell = lambda sm: f"{m['smells'][sm]['zone']} ({m['smells'][sm]['probability']:.2f})"  # noqa: E731
        lines.append(f"| {m['status']} | {m['change_type']} | `{m['name']}` | `{m['file']}:{m['start_line']}` | {ba('cc')} | "
                     f"{ba('pc')} | {cell('CM')} | {cell('LPL')} |")
    if len(result["methods"]) > limit:
        lines.append(f"\n…and {len(result['methods']) - limit} more methods (see the JSON report).")
    notes = {(sm, m["smells"][sm]["note"]) for m in result["methods"] for sm in SMELLS
             if m["smells"][sm]["zone"] == "borderline"}
    if notes:
        lines += ["", "<details><summary>Borderline results are candidates to review, not verdicts</summary>", ""]
        lines += [f"- **{sm}**: {n}" for sm, n in sorted(notes)] + ["", "</details>"]
    lines += ["", "<details><summary>How this score is calculated</summary>", ""] + [f"- {x}" for x in r["formula"]]
    lines += ["", "</details>", "", f"<sub>CodeSniff {__version__} · [method and paper]({REPO_URL})</sub>"]
    return "\n".join(lines)


def build_parser():
    p = argparse.ArgumentParser(prog="codesniff", description="Smell risk of Java code changes (Complex Method, "
                                "Long Parameter List). Not a bug or build-failure predictor.")
    p.add_argument("--version", action="version", version=f"CodeSniff {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="score the methods changed by a commit or pull request")
    c.add_argument("--repo", help="https://github.com/<owner>/<repo> (or a commit URL)")
    c.add_argument("--sha", help="commit SHA (default: latest commit on the default branch)")
    c.add_argument("--pr", help="pull-request URL")
    c.add_argument("--mode", choices=["commit", "repo"], default="commit")
    c.add_argument("--max-files", type=int, default=None)
    s = sub.add_parser("scan", help="score every method in a local .java file, folder or .zip")
    s.add_argument("path")
    s.add_argument("--max-files", type=int, default=None)
    for sp, fmts in ((c, ["table", "json", "markdown"]), (s, ["table", "json", "markdown", "sarif"])):
        sp.add_argument("--format", choices=fmts, default="table")
        sp.add_argument("--fail-on", choices=list(FAIL_BANDS), default="high")
        sp.add_argument("--output", "-o")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    rows = None
    try:
        if args.command == "check":
            if not (args.repo or args.pr):
                print("codesniff: give --repo or --pr", file=sys.stderr)
                return 2
            result = analyze_commit(args.repo, args.sha, args.pr, args.mode, args.max_files)
        else:
            result, rows = scan_result(args.path, args.max_files)
    except GitHubError as exc:
        print(f"codesniff: {exc.message}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError) as exc:
        print(f"codesniff: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        out = json.dumps(result, indent=2)
    elif args.format == "markdown":
        out = to_markdown(result)
    elif args.format == "sarif":
        out = to_sarif(rows)
    else:
        out = to_table(result)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        print(out)
    return int(result["risk"]["band"] in FAIL_BANDS[args.fail_on])


__all__ = ["main", "to_markdown", "to_table", "scan_result", "PRIMARY"]
