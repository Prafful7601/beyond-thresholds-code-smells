"""Output formats: plain table, JSON, CSV and SARIF 2.1.0 (GitHub code scanning)."""
import io
import json

from . import __version__
from .model import card
from .resources import PAPER_TITLE, PRIMARY, REPO_URL, SMELL_NAME, SMELLS
from .zones import bands

COLUMNS = ["file", "name", "start_line", "end_line", "has_body", "cc", "cc_lizard", "pc", "loc", "statements",
           "max_nesting", "method_calls", "comment_ratio", "mean_identifier_length", "status"]
SMELL_COLUMNS = ["zone", "rule", "probability", "note"]
SARIF_LEVEL = {"clear": "error", "borderline": "warning"}


def flat(rows):
    return [{**{c: r[c] for c in COLUMNS}, **{f"{s}_{k}": r[f"{s}_{k}"] for s in SMELLS for k in SMELL_COLUMNS}}
            for r in rows]


def to_json(rows, source=None, skipped=()):
    meta = {"tool": "CodeSniff", "version": __version__, "source": source, "paper": PAPER_TITLE, "repository": REPO_URL,
            "bands": bands(), "models": {s: {k: card()[s][k] for k in ("model", "hyperparameters", "trained_at",
                                                                         "repository_commit")} for s in SMELLS},
            "skipped_files": [{"file": f, "reason": why} for f, why in skipped]}
    return json.dumps({"meta": meta, "methods": flat(rows)}, indent=2)


def to_csv(rows):
    import csv
    buf = io.StringIO()
    data = flat(rows)
    fields = COLUMNS + [f"{s}_{k}" for s in SMELLS for k in SMELL_COLUMNS]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    w.writerows(data)
    return buf.getvalue()


def to_table(rows):
    head = f"{'status':<11}{'method':<34}{'file:line':<42}{'cc':>4}{'pc':>4}  {'CM zone':<11}{'P(CM)':>6}  {'LPL zone':<11}{'P(LPL)':>6}"
    out = [head, "-" * len(head)]
    for r in rows:
        loc = f"{r['file']}:{r['start_line']}"
        out.append(f"{r['status']:<11}{r['name'][:33]:<34}{loc[-41:]:<42}{r['cc']:>4}{r['pc']:>4}  "
                   f"{r['CM_zone']:<11}{r['CM_probability']:>6.2f}  {r['LPL_zone']:<11}{r['LPL_probability']:>6.2f}")
    n = {z: sum(1 for r in rows if r["status"] == z) for z in ("clear", "borderline", "clean")}
    out += ["", f"{len(rows)} methods: {n['clear']} clear, {n['borderline']} borderline (candidates to review, not "
                f"verdicts), {n['clean']} clean."]
    return "\n".join(out)


def _rules():
    out = []
    for s in SMELLS:
        b = bands()[s]
        for z, desc in (("borderline", f"{PRIMARY[s]} inside the band DACOS annotators judged ({b['lo']:g}-{b['hi']:g}); "
                                       "candidate to review, not a verdict"),
                        ("clear", f"{PRIMARY[s]} above the annotated band (> {b['hi']:g})")):
            out.append({"id": f"{s}-{z}", "name": f"{SMELL_NAME[s].replace(' ', '')}{z.capitalize()}",
                        "shortDescription": {"text": f"{SMELL_NAME[s]}: {z}"},
                        "fullDescription": {"text": desc},
                        "helpUri": REPO_URL,
                        "defaultConfiguration": {"level": SARIF_LEVEL[z]}})
    return out


def to_sarif(rows):
    results = []
    for r in rows:
        for s in SMELLS:
            z = r[f"{s}_zone"]
            if z == "clean":
                continue
            results.append({
                "ruleId": f"{s}-{z}",
                "level": SARIF_LEVEL[z],
                "message": {"text": f"{SMELL_NAME[s]} {z} in {r['name']}: {PRIMARY[s]} = {r[PRIMARY[s]]}, "
                                    f"model P(smelly) = {r[f'{s}_probability']:.2f}. {r[f'{s}_note']}"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": r["file"].replace("\\", "/")},
                    "region": {"startLine": max(1, int(r["start_line"])), "endLine": max(1, int(r["end_line"]))}}}],
                "properties": {"zone": z, "metric": PRIMARY[s], "value": r[PRIMARY[s]],
                               "probability": r[f"{s}_probability"], "designiteRuleFlag": r[f"{s}_rule"]},
            })
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "CodeSniff", "version": __version__, "informationUri": REPO_URL,
                                      "rules": _rules()}},
                  "results": results}]}, indent=2)
