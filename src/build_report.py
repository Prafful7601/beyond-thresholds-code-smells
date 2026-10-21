"""Assemble results/results.md from the fragments written by each analysis script."""
import os
import platform
import subprocess
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import B, FRAG, LOG, ROOT, SEED, SMELL_NAME  # noqa: E402


def frag(name):
    p = os.path.join(FRAG, name + ".md")
    return open(p).read() if os.path.exists(p) else f"*Fragment `{name}` not generated.*\n"


def git(*args):
    try:
        return subprocess.check_output(["git", "-C", ROOT] + list(args), text=True).strip()
    except Exception:
        return "n/a"


def main():
    commits = git("log", "--format=%h %H %s", "--", "plan.md").splitlines()
    req = open(os.path.join(ROOT, "requirements.txt")).read().strip().splitlines()
    keep = [r for r in req if r.split("==")[0].lower() in
            {"numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "krippendorff", "lizard", "matplotlib"}]
    rt_path = os.path.join(LOG, "runtime.tsv")
    runtime = pd.read_csv(rt_path, sep="\t", names=["step", "seconds"]) if os.path.exists(rt_path) else None
    el = pd.read_csv(os.path.join(ROOT, "results/tables/eligibility.csv"))
    inel = el[(el.annotation_set == "primary (filtered)") & (el.eligible_for_models == False)].smell.tolist()  # noqa: E712

    md = []
    w = md.append
    w("# Results: human judgment versus metric thresholds in DACOS\n")
    w("Pre-registered plan: `plan.md`. Plan commits, in order:")
    for c in reversed(commits):
        h_short, h_full, msg = c.split(" ", 2)
        w(f"- `{h_full}`: {msg}")
    w("")
    w("Scope of this version: **Tier 1** (dataset audit, RQ1, RQ2, RQ4).")
    w("- RQ3, RQ5 and the robustness checks R1–R6 are Tier 2 and **have not been run yet**. Their sections below say so.")
    w(f"- **{', '.join(SMELL_NAME[s] for s in inel)} is reported descriptively only** (RQ1 agreement and RQ2 threshold ROC), "
      "because it fails the D8 eligibility rule after the consistency filter. All model sections skip it.\n")
    w("Conventions:")
    w("- The \"primary set\" is the consistency-filtered annotations (D7), with entities that have ≥ 2 usable annotations.")
    w("- With 2 annotations per entity, majority labels with ties excluded are exactly the unanimous entities. RQ2 and RQ4 use those (D11).")
    w(f"- All CIs are 95% bootstrap percentile intervals (B = {B}, seed {SEED}), resampling entities, unless stated otherwise.\n")

    w("## 1 Dataset audit: data loading and integrity checks\n")
    w(frag("s1_audit"))
    w("## 2 Descriptives\n")
    w(frag("s2_descriptives"))
    w("## 3 Research questions\n")
    w("### RQ1 Agreement\n")
    w(frag("rq1"))
    w("### RQ2 Threshold validity in the borderline band\n")
    w(frag("rq2"))
    w("### RQ4 Extremes-to-borderline transfer\n")
    w(frag("rq4"))
    w("### RQ3 What drives human judgment\n")
    w("Not run yet. This is Tier 2.\n")
    w("### RQ5 Ambiguity\n")
    w("Not run yet. This is Tier 2.\n")
    w("## 4 Robustness\n")
    w("Not run yet. R1 (MA only), R2, R3, R4, R5 and R6 are Tier 2, as specified in plan.md §2–3.\n")
    w("## 5 Exploratory\n")
    w("Nothing in this section was pre-registered in plan.md.\n")
    w(frag("exploratory_dacosx"))
    w("## 6 Deviations from plan.md and known limitations\n")
    w(frag("s6_deviations"))
    w("## 7 Reproducibility notes\n")
    w("- Regenerate everything with `bash run_all.sh` from `paper3/`. It downloads the data if absent, verifies the MD5s and rebuilds every table, figure and this file.")
    w(f"- Python {platform.python_version()} ({platform.system()} {platform.machine()}). Pinned packages (full list in `requirements.txt`): {', '.join(keep)}.")
    w(f"- Seeds: every bootstrap and model uses seed {SEED} (`numpy.random.default_rng`, `random_state`). Bootstrap B = {B}.")
    w("- GroupKFold and LeaveOneGroupOut are deterministic. The random forest runs single-threaded (scikit-learn default `n_jobs`), because multi-threaded probability accumulation varied in the last floating-point digits between runs.")
    w("- Two consecutive full runs of `run_all.sh` produced byte-identical CSV tables. `rq4_predictions.csv.gz` differs only in its gzip header timestamp; its decompressed content is identical.")
    w(f"- Code commit at report build: `{git('rev-parse', 'HEAD')}`; the working tree may contain uncommitted changes at build time.")
    if runtime is not None:
        w(f"- Runtime of the last `run_all.sh` (seconds), total {runtime.seconds.sum():.0f}s:\n")
        w("| step | seconds |\n|---|---|")
        for r in runtime.itertuples():
            w(f"| {r.step} | {r.seconds} |")
    w("")
    w("- Logs: `results/logs/` (one log per step, plus `audit.txt`, `features.log`, `lizard_crosscheck.csv` and `runtime.tsv`).")
    open(os.path.join(ROOT, "results/results.md"), "w").write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
