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
            {"numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "krippendorff", "lizard", "matplotlib", "xgboost", "shap"}]
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
    w("Scope: **Tier 1, Tier 2 and Step 3 (Prompt 2) are complete.** Every planned section below was run; none is outstanding.")
    w(f"- **{', '.join(SMELL_NAME[s] for s in inel)} is reported descriptively only** (agreement, threshold ROC, RQ5 descriptives), "
      "because it fails the D8 eligibility rule after the consistency filter. Every model section (RQ4, RQ3 models, Step 3 A–J) covers CM and LPL only.")
    w("- Every section states its **analysis type**: *primary*, *robustness*, *validity check* or *exploratory*. "
      "Numbers from different types must not be mixed when the paper is written.\n")
    w("Conventions:")
    w("- The \"primary set\" is the consistency-filtered annotations (D7), with entities that have ≥ 2 usable annotations.")
    w("- With 2 annotations per entity, majority labels with ties excluded are exactly the unanimous entities. RQ2, RQ4 and all models use those (D11).")
    w(f"- All CIs are 95% bootstrap percentile intervals (B = {B}, seed {SEED}), resampling entities, unless stated otherwise.\n")

    w("## 1 Dataset audit: data loading and integrity checks\n")
    w("**Analysis type: descriptive audit of the published data.**\n")
    w(frag("s1_audit"))
    w("## 2 Descriptives\n")
    w(frag("s2_descriptives"))
    w("## 3 Research questions\n")
    w("### RQ1 Agreement\n")
    w("**Analysis type: primary.**\n")
    w(frag("rq1"))
    w("### RQ2 Threshold validity in the borderline band\n")
    w("**Analysis type: primary** (MA descriptive only).\n")
    w(frag("rq2"))
    w("### RQ4 Extremes-to-borderline transfer\n")
    w("**Analysis type: primary** (CM and LPL; MA skipped under D8).\n")
    w(frag("rq4"))
    w("### RQ3 What drives human judgment\n")
    w(frag("rq3"))
    w("### RQ5 Ambiguity\n")
    w(frag("rq5"))
    w("## 4 Robustness\n")
    w("### 4.1 Robustness summary (R1–R7c; plan.md §4.1)\n")
    w(frag("robustness"))
    w("### 4.2 R7 run anatomy (plan.md §4.2)\n")
    w(frag("run_anatomy"))
    w("### 4.3 J Sensitivity of the best model to training labels (R4, R6)\n")
    w(frag("step3_J"))
    w("## 5 Strengthening analyses (Step 3; CM and LPL)\n")
    for key, title in (("A", "A Baselines"), ("B", "B Model comparison"), ("C", "C Ablation study"),
                       ("D", "D Generalisation"), ("E", "E Leakage and validity checks"),
                       ("F", "F Interpretability and calibration"), ("G", "G Feature selection"),
                       ("H", "H Learning curve"), ("I", "I Error analysis")):
        w(f"### 5.{'ABCDEFGHI'.index(key) + 1} {title}\n")
        w(frag(f"step3_{key}"))
    w("Section J (sensitivity) is reported in §4.3, because it is a robustness analysis.\n")
    w("## 6 Exploratory\n")
    w("**Analysis type: exploratory.** Nothing in this section was pre-registered in plan.md.\n")
    w(frag("exploratory_dacosx"))
    w("## 7 Deviations from plan.md and known limitations\n")
    w(frag("s6_deviations"))
    w("## 8 Reproducibility notes\n")
    w("- Regenerate everything with `bash run_all.sh` from `paper3/`. It downloads the data if absent, verifies the MD5s and rebuilds every table, figure and this file.")
    w(f"- Python {platform.python_version()} ({platform.system()} {platform.machine()}). Pinned packages (full list in `requirements.txt`): {', '.join(keep)}.")
    w(f"- Seeds: every bootstrap and model uses seed {SEED} (`numpy.random.default_rng`, `random_state`). Bootstrap B = {B}.")
    w("- GroupKFold and LeaveOneGroupOut are deterministic. The random forest runs single-threaded (scikit-learn default `n_jobs`), because multi-threaded probability accumulation varied in the last floating-point digits between runs.")
    w("- Determinism check: a full `run_all.sh` regeneration from freshly converted databases (with the model cache cleared) reproduced every committed CSV table byte for byte, including all Step 1–3 tables produced in earlier, separate runs. `rq4_predictions.csv.gz` differs only in its gzip header timestamp; its decompressed content is identical.")
    w("- Parallelism: Step 3 parallelises over outer folds with `joblib`. Each fold's model is single-threaded and seeded (RF/GB/XGB `n_jobs=1`, `random_state = 20261021 + repeat`), so results do not depend on scheduling.")
    w("- xgboost uses scikit-learn's bundled `libomp` (`DYLD_LIBRARY_PATH` set by `run_all.sh`), because no system OpenMP runtime is installed.")
    w(f"- Code commit at report build: `{git('rev-parse', 'HEAD')}`; the working tree may contain uncommitted changes at build time.")
    if runtime is not None:
        w(f"- Runtime of the last `run_all.sh` (seconds), total {runtime.seconds.sum():.0f}s:\n")
        w("| step | seconds |\n|---|---|")
        for r in runtime.itertuples():
            w(f"| {r.step} | {r.seconds} |")
    w("")
    w("- Logs: `results/logs/` (one log per step, plus `audit.txt`, `features.log`, `lizard_crosscheck.csv` and `runtime.tsv`).")
    w("")
    w("## 9 Completion status\n")
    w("All sections requested in Prompt 2 were completed: Step 1 (R3–R7), Step 2 (RQ3, RQ5, R1, R2, R3–R6 on RQ3/RQ5) and Step 3 A–J. No section was skipped for time.\n")
    w("## 10 Headline numbers\n")
    w(headline_block())
    open(os.path.join(ROOT, "results/results.md"), "w").write("\n".join(md) + "\n")


def headline_block():
    T = os.path.join(ROOT, "results/tables")
    rd = lambda n: pd.read_csv(os.path.join(T, n))  # noqa: E731
    f3 = lambda e, l, h: f"{e:.3f} [{l:.3f}, {h:.3f}]"  # noqa: E731
    rows = []
    a = rd("rq1_agreement.csv").set_index("smell")
    rob = rd("robustness_long.csv")

    def rb(check, smell, head):
        x = rob[(rob.check == check) & (rob.smell == smell) & (rob.headline == head)].iloc[0]
        return x
    for s_ in ("CM", "LPL", "MA"):
        r = a.loc[s_]
        extra = f"; percent agreement {r.pct_agreement:.3f}" if s_ == "MA" else ""
        rows.append((f"Krippendorff's alpha, {s_}", f3(r.kripp_alpha, r.alpha_lo, r.alpha_hi) + extra, "primary", "rq1_agreement.csv"))
    x = rb("R6", "CM", "RQ1 Krippendorff alpha")
    rows.append(("Krippendorff's alpha, CM, without the consistency filter", f3(x.estimate, x.lo, x.hi), "robustness R6", "robustness_long.csv"))
    q = rd("rq2_threshold_validity.csv").set_index("smell")
    for s_ in ("CM", "LPL"):
        r = q.loc[s_]
        rows.append((f"Primary-metric ROC-AUC, {s_}", f3(r.auc, r.auc_lo, r.auc_hi) + f" (one-sided MWU p = {r.mwu_p_one_sided:.2g})",
                     "primary", "rq2_threshold_validity.csv"))
    x = rb("R5", "LPL", "RQ2 ROC-AUC (primary metric)")
    rows.append(("Primary-metric ROC-AUC, LPL, without the pc = 3 block", f3(x.estimate, x.lo, x.hi), "robustness R5", "robustness_long.csv"))
    r = q.loc["CM"]
    rows.append(("Youden cut-off for CM versus DesigniteJava default", f"cc ≥ {r.youden_cut:g} [{r.youden_cut_lo:g}, {r.youden_cut_hi:g}] vs cc ≥ 8",
                 "primary", "rq2_threshold_validity.csv"))
    d = rd("rq4_paired_differences.csv")
    r = d[(d.smell == "LPL") & (d.model == "LR") & d.primary_H4_test].iloc[0]
    rows.append(("RQ4 transfer MCC − GroupKFold MCC, LPL, LR", f3(r.difference, r.lo, r.hi), "primary", "rq4_paired_differences.csv"))
    x = rb("R3", "LPL", "RQ4 MCC transfer − GroupKFold (LR)")
    rows.append(("RQ4 transfer MCC − GroupKFold MCC, LPL, LR, `is_smell` labels", f3(x.estimate, x.lo, x.hi), "robustness R3", "robustness_long.csv"))
    o = rd("rq3_odds_ratios.csv")
    o = o[o.model == "full"]
    r = o[(o.smell == "CM") & (o.feature == "cc")].iloc[0]
    rows.append(("RQ3 GEE OR per SD of cc, CM", f3(r.OR_per_SD, r.OR_lo, r.OR_hi) + f" (BH p = {r.p_BH_within_smell_model:.2g})", "primary", "rq3_odds_ratios.csv"))
    r = o[(o.smell == "LPL") & (o.feature == "pc")].iloc[0]
    x = rb("R5", "LPL", "RQ3 GEE OR per SD of primary metric")
    rows.append(("RQ3 GEE OR per SD of pc, LPL (primary; without the pc = 3 block)",
                 f3(r.OR_per_SD, r.OR_lo, r.OR_hi) + "; R5: " + f3(x.estimate, x.lo, x.hi), "primary; robustness R5",
                 "rq3_odds_ratios.csv; robustness_long.csv"))
    m = rd("model_comparison.csv")
    for s_ in ("CM", "LPL"):
        r = m[(m.smell == s_) & m.best_model].iloc[0]
        rows.append((f"Best model MCC, {s_} ({r.model}, 5×5 grouped CV)", f"{r.MCC:.3f} ± {r.MCC_sd:.3f} [{r.MCC_lo:.3f}, {r.MCC_hi:.3f}]",
                     "primary", "model_comparison.csv"))
    ab = rd("ablation_LPL.csv")
    r = ab[(ab.model == ab.model.iloc[0]) & (ab.variant == "DACOSX only")].iloc[0]
    rows.append((f"Δ MCC, LPL {r.model}, training on DACOSX only versus DACOS", f3(r.d_MCC, r.d_MCC_lo, r.d_MCC_hi), "primary (ablation C3)", "ablation_LPL.csv"))
    out = ["| # | number | value [95% CI] | analysis type | table |", "|---|---|---|---|---|"]
    for i, (n, v, t, tb) in enumerate(rows, 1):
        out.append(f"| {i} | {n} | {v} | {t} | `tables/{tb.replace('; ', '`, `tables/')}` |")
    return "\n".join(out) + "\n\nAll values are read programmatically from the listed tables when this file is built.\n"


if __name__ == "__main__":
    main()
