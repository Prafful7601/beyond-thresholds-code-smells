"""Analyse a commit, a pull request, the latest commit of a repository, or a whole repository (capped)."""
import os
import tempfile
import time

from .analyze import _score, analyze_dir
from .diff import changed_methods
from .github import GitHub, GitHubError, parse_target
from .resources import SMELLS
from .scoring import change_status, method_points, method_status, risk_score

MAX_CHANGED_FILES = int(os.environ.get("CODESNIFF_MAX_CHANGED_FILES", "150"))
DEFAULT_SCAN_FILES = int(os.environ.get("CODESNIFF_SCAN_FILES", "300"))
METRIC_KEYS = ("cc", "cc_lizard", "pc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio",
               "mean_identifier_length")


def _side(row):
    if row is None:
        return None
    return {**{k: row[k] for k in METRIC_KEYS}, "start_line": row["start_line"], "end_line": row["end_line"],
            **{s: {"zone": row[f"{s}_zone"], "rule": row[f"{s}_rule"], "probability": row[f"{s}_probability"],
                   "note": row[f"{s}_note"]} for s in SMELLS}}


def _entry(file, ch, brow, arow, scored=True):
    before, after = _side(brow), _side(arow)
    smells, statuses = {}, {}
    for s in SMELLS:
        st = change_status(before and before[s], after and after[s]) if scored else "n/a"
        statuses[s] = st
        cur = (after or before)[s]
        smells[s] = {"status": st, **cur}
    pts = method_points({s: after[s] for s in SMELLS} if after else None,
                        {s: v for s, v in statuses.items() if v != "n/a"})
    code_row = arow or brow
    return {"file": file, "name": code_row["name"], "change_type": ch["change_type"] if ch else "scanned",
            "start_line": code_row["start_line"], "end_line": code_row["end_line"],
            "changed_lines": ch["changed_lines"] if ch else [], "code": code_row["code"], "has_body": code_row["has_body"],
            "before": before, "after": after, "smells": smells, "points": pts,
            "status": method_status(statuses) if scored else ("n/a" if after else "removed")}


def _summary(methods):
    scored = [m for m in methods if m["points"] is not None]
    count = lambda pred: sum(1 for m in methods if pred(m))  # noqa: E731
    return {"changed_methods": len(scored), "added": count(lambda m: m["change_type"] == "added"),
            "modified": count(lambda m: m["change_type"] == "modified"),
            "deleted": count(lambda m: m["change_type"] == "deleted"),
            "introduced": count(lambda m: m["status"] == "introduced"),
            "worsened": count(lambda m: m["status"] == "worsened"),
            "improved": count(lambda m: m["status"] == "improved"),
            "clean": count(lambda m: m["after"] is not None and all(m["after"][s]["zone"] == "clean" for s in SMELLS)),
            "borderline": count(lambda m: m["after"] is not None and any(m["after"][s]["zone"] == "borderline" for s in SMELLS)
                                and not any(m["after"][s]["zone"] == "clear" for s in SMELLS)),
            "clear": count(lambda m: m["after"] is not None and any(m["after"][s]["zone"] == "clear" for s in SMELLS))}


def _order(methods):
    rank = {"introduced": 0, "worsened": 1, "improved": 2, "unchanged": 3, "n/a": 3, "removed": 4}
    return sorted(methods, key=lambda m: (rank.get(m["status"], 5), -(m["points"] or 0), m["file"], m["start_line"]))


def analyze_files(file_pairs):
    """file_pairs: [(path, before_text or "", after_text or "")]. Pure function used by the API, CLI and tests."""
    methods = []
    for path, old, new in file_pairs:
        changes = changed_methods(old, new, path)
        if not changes:
            continue
        b_rows = _score([c["before"] for c in changes if c["before"]])
        a_rows = _score([c["after"] for c in changes if c["after"]])
        bi = iter(b_rows)
        ai = iter(a_rows)
        for c in changes:
            brow = next(bi) if c["before"] else None
            arow = next(ai) if c["after"] else None
            methods.append(_entry(path, c, brow, arow))
    return _order(methods)


def analyze_commit(repo_url=None, commit_sha=None, pr_url=None, mode="commit", max_files=None, gh=None, progress=None):
    t0 = time.time()
    say = progress or (lambda stage: None)
    gh = gh or GitHub()
    target = parse_target(repo_url, commit_sha, pr_url)
    owner, repo = target["owner"], target["repo"]
    say("fetching commit")
    if target["kind"] == "pr":
        pr = gh.pull(owner, repo, target["number"])
        head = pr["head"]["sha"]
        cmp = gh.compare(owner, repo, pr["base"]["sha"], head)
        base = cmp["merge_base_commit"]["sha"]
        files = cmp.get("files", [])
        info = {"kind": "pull request", "number": target["number"], "title": pr.get("title"),
                "url": pr.get("html_url"), "sha": head, "base_sha": base, "author": (pr.get("user") or {}).get("login")}
    else:
        sha = target.get("sha")
        if not sha:
            sha = gh.repo(owner, repo)["default_branch"]
        c = gh.commit(owner, repo, sha)
        head = c["sha"]
        parents = c.get("parents") or []
        base = parents[0]["sha"] if parents else None
        files = c.get("files", [])
        info = {"kind": "commit" if target["kind"] == "commit" else "latest commit on the default branch",
                "title": (c.get("commit", {}).get("message") or "").split("\n")[0], "url": c.get("html_url"),
                "sha": head, "base_sha": base, "author": (c.get("commit", {}).get("author") or {}).get("name"),
                "date": (c.get("commit", {}).get("author") or {}).get("date")}
    warnings = []
    if mode == "repo":
        say("downloading repository")
        cap = int(max_files or DEFAULT_SCAN_FILES)
        with tempfile.TemporaryDirectory() as tmp:
            root = gh.tarball(owner, repo, head, tmp)
            say("parsing methods")
            rows, skipped = analyze_dir(root, max_files=cap)
            n_java = sum(1 for _ in __import__("codesniff.analyze", fromlist=["java_files"]).java_files(root))
        say("scoring")
        methods = _order([_entry(r["file"], None, None, r, scored=False) for r in rows])
        if n_java > cap:
            warnings.append(f"Scanned the first {cap} of {n_java} Java files (cap).")
        warnings += [f"Skipped {f}: {why}" for f, why in skipped]
    else:
        java = [f for f in files if f.get("filename", "").endswith(".java") or f.get("previous_filename", "").endswith(".java")]
        if len(files) >= 300:
            warnings.append("GitHub lists at most 300 changed files per commit; later files are not included.")
        if len(java) > MAX_CHANGED_FILES:
            warnings.append(f"Analysed the first {MAX_CHANGED_FILES} of {len(java)} changed Java files (cap).")
            java = java[:MAX_CHANGED_FILES]
        say("fetching files")
        pairs = []
        for f in java:
            status = f.get("status")
            new = "" if status == "removed" else (gh.raw(owner, repo, head, f["filename"]) or "")
            old_path = f.get("previous_filename") or f["filename"]
            old = "" if (status == "added" or not base) else (gh.raw(owner, repo, base, old_path) or "")
            pairs.append((f["filename"], old, new))
        say("parsing methods")
        methods = analyze_files(pairs)
        say("scoring")
        if not java:
            warnings.append("This commit changes no Java files.")
    risk = risk_score([m["points"] for m in methods])
    return {"repo": f"{owner}/{repo}", "repo_url": f"https://github.com/{owner}/{repo}", "mode": mode, "target": info,
            "risk": risk, "summary": _summary(methods), "methods": methods, "warnings": warnings,
            "java_files": len({m["file"] for m in methods}), "duration_s": round(time.time() - t0, 2)}


def cache_key(target, mode, sha, max_files=None):
    return f"{target['owner'].lower()}/{target['repo'].lower()}@{sha}#{mode}" + (f":{max_files}" if mode == "repo" else "")


__all__ = ["analyze_commit", "analyze_files", "GitHubError", "cache_key"]
