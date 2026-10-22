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
    w("Scope: **all planned analyses are complete**: Tier 1, Tier 2, Step 3 (Prompt 2), Prompt 3, Prompt 3B (range restriction and external B0) and Prompt 4 (agreement anatomy and external check B1).")
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
    w(frag("audit_ma_note"))
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
    w("### 4.4 LPL Step 3 without the pc = 3 block (R5; plan.md §5.1)\n")
    w(frag("step3_R5"))
    w("### 4.5 Specification curves (plan.md §5.3)\n")
    w(frag("spec_curves"))
    w("## 5 Strengthening analyses (Step 3; CM and LPL)\n")
    for key, title in (("A", "A Baselines"), ("B", "B Model comparison"), ("C", "C Ablation study"),
                       ("D", "D Generalisation"), ("E", "E Leakage and validity checks"),
                       ("F", "F Interpretability and calibration"), ("G", "G Feature selection"),
                       ("H", "H Learning curve"), ("I", "I Error analysis")):
        w(f"### 5.{'ABCDEFGHI'.index(key) + 1} {title}\n")
        w(frag(f"step3_{key}"))
    w("Section J (sensitivity) is reported in §4.3, because it is a robustness analysis.\n")
    w("## 6 Human ceiling and agreement anatomy\n")
    w("### 6.1 Human ceiling (plan.md §5.2)\n")
    w(frag("human_ceiling"))
    w("### 6.2 Why same-snippet agreement exceeds cross-snippet agreement (plan.md §7.1)\n")
    w(frag("agreement_anatomy"))
    w("## 7 Range restriction (plan.md §6.1)\n")
    w(frag("range_restriction"))
    w("## 8 External check: C# dataset (plan.md §6.2)\n")
    w("### 8.1 B0 audit\n")
    w(frag("external_B0"))
    w("### 8.2 B1 (plan.md §7.2)\n")
    w(frag("external_B1"))
    w("## 9 Exploratory\n")
    w("**Analysis type: exploratory.** Not part of the pre-registered primary or robustness analyses; A4 in §7 is also exploratory.\n")
    w(frag("exploratory_dacosx"))
    w(frag("exploratory_cm_reweight"))
    w("## 10 Deviations from plan.md and known limitations\n")
    w(frag("s6_deviations"))
    w("## 11 Reproducibility notes\n")
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
    w("## 12 Completion status\n")
    w("- Complete: Prompt 2 (Step 1 R3–R7; Step 2 RQ3, RQ5, R1, R2, R3–R6 on RQ3/RQ5; Step 3 A–J), Prompt 3 sections 1–4, and Prompt 3B part A (range restriction).")
    w("- Prompt 3B part B (B0 audit) and Prompt 4 (Part 1 agreement anatomy 1.1–1.5; Part 2 external check B1) are complete. No section was skipped for time.\n")
    w("## 13 Headline numbers\n")
    w(headline_block())
    open(os.path.join(ROOT, "results/results.md"), "w").write("\n".join(md) + "\n")


def headline_rows():
    T = os.path.join(ROOT, "results/tables")
    rd = lambda n: pd.read_csv(os.path.join(T, n))  # noqa: E731
    rows = []

    def add(name, est, lo, hi, kind, table, note="", fmt3=True):
        rows.append({"number": name, "estimate": None if est is None else float(est), "ci_lo": None if lo is None or pd.isna(lo) else float(lo),
                     "ci_hi": None if hi is None or pd.isna(hi) else float(hi), "note": note, "analysis_type": kind, "source_table": table})
    a = rd("rq1_agreement.csv").set_index("smell")
    rob = rd("robustness_long.csv")
    rb = lambda c, s_, h: rob[(rob.check == c) & (rob.smell == s_) & (rob.headline == h)].iloc[0]  # noqa: E731
    for s_ in ("CM", "LPL", "MA"):
        r = a.loc[s_]
        add(f"Krippendorff's alpha, {s_}", r.kripp_alpha, r.alpha_lo, r.alpha_hi, "primary", "rq1_agreement.csv",
            f"percent agreement {r.pct_agreement:.3f}" if s_ == "MA" else "")
    x = rb("R6", "CM", "RQ1 Krippendorff alpha")
    add("Krippendorff's alpha, CM, without the consistency filter", x.estimate, x.lo, x.hi, "robustness R6", "robustness_long.csv")
    q = rd("rq2_threshold_validity.csv").set_index("smell")
    for s_ in ("CM", "LPL"):
        r = q.loc[s_]
        add(f"Primary-metric ROC-AUC, {s_}", r.auc, r.auc_lo, r.auc_hi, "primary", "rq2_threshold_validity.csv",
            f"one-sided MWU p = {r.mwu_p_one_sided:.2g}")
    x = rb("R5", "LPL", "RQ2 ROC-AUC (primary metric)")
    add("Primary-metric ROC-AUC, LPL, without the pc = 3 block", x.estimate, x.lo, x.hi, "robustness R5", "robustness_long.csv")
    r = q.loc["CM"]
    add("Youden cut-off for CM (cc ≥ c) versus DesigniteJava default cc ≥ 8", r.youden_cut, r.youden_cut_lo, r.youden_cut_hi,
        "primary", "rq2_threshold_validity.csv", "cut-off value; DesigniteJava default 8")
    d = rd("rq4_paired_differences.csv")
    r = d[(d.smell == "LPL") & (d.model == "LR") & d.primary_H4_test].iloc[0]
    add("RQ4 transfer MCC − GroupKFold MCC, LPL, LR", r.difference, r.lo, r.hi, "primary", "rq4_paired_differences.csv")
    x = rb("R3", "LPL", "RQ4 MCC transfer − GroupKFold (LR)")
    add("RQ4 transfer MCC − GroupKFold MCC, LPL, LR, `is_smell` labels", x.estimate, x.lo, x.hi, "robustness R3", "robustness_long.csv")
    o = rd("rq3_odds_ratios.csv")
    o = o[o.model == "full"]
    r = o[(o.smell == "CM") & (o.feature == "cc")].iloc[0]
    add("RQ3 GEE OR per SD of cc, CM", r.OR_per_SD, r.OR_lo, r.OR_hi, "primary", "rq3_odds_ratios.csv", f"BH p = {r.p_BH_within_smell_model:.2g}")
    r = o[(o.smell == "LPL") & (o.feature == "pc")].iloc[0]
    x = rb("R5", "LPL", "RQ3 GEE OR per SD of primary metric")
    add("RQ3 GEE OR per SD of pc, LPL", r.OR_per_SD, r.OR_lo, r.OR_hi, "primary", "rq3_odds_ratios.csv",
        f"R5: {x.estimate:.3f} [{x.lo:.3f}, {x.hi:.3f}] (robustness_long.csv)")
    m = rd("model_comparison.csv")
    for s_ in ("CM", "LPL"):
        r = m[(m.smell == s_) & m.best_model].iloc[0]
        add(f"Best model MCC, {s_} ({r.model}, 5×5 grouped CV)", r.MCC, r.MCC_lo, r.MCC_hi, "primary", "model_comparison.csv", f"SD over repeats {r.MCC_sd:.3f}")
    ab = rd("ablation_LPL.csv")
    r = ab[(ab.model == ab.model.iloc[0]) & (ab.variant == "DACOSX only")].iloc[0]
    add(f"Δ MCC, LPL {r.model}, training on DACOSX only versus DACOS", r.d_MCC, r.d_MCC_lo, r.d_MCC_hi, "primary (ablation C3)", "ablation_LPL.csv")
    # ---- Prompt 3 / 3B additions
    m5 = rd("model_comparison_LPL_R5.csv")
    r = m5[m5.best_model].iloc[0]
    add(f"Best model MCC, LPL R5 ({r.model}, 5×5 grouped CV) [R5 value of row 14]", r.MCC, r.MCC_lo, r.MCC_hi, "robustness R5",
        "model_comparison_LPL_R5.csv", f"SD over repeats {r.MCC_sd:.3f}")
    a5 = rd("ablation_LPL_R5.csv")
    r = a5[(a5.model == m5[m5.best_model].model.iloc[0]) & (a5.variant == "DACOSX only")].iloc[0]
    add(f"Δ MCC, LPL R5 {r.model}, training on DACOSX only versus DACOS [R5 value of row 15]", r.d_MCC, r.d_MCC_lo, r.d_MCC_hi,
        "robustness R5", "ablation_LPL_R5.csv")
    hc = rd("human_ceiling.csv")
    hc = hc[hc.metric == "MCC"]
    for r in hc.itertuples():
        add(f"Human-vs-human MCC, {r.population}", r.human_vs_human, r.human_lo, r.human_hi, "primary (human ceiling)", "human_ceiling.csv")
        add(f"Best model vs one human MCC, {r.population} ({r.best_model})", r.model_vs_single_human, r.model_lo, r.model_hi,
            "primary (human ceiling)", "human_ceiling.csv")
        add(f"Model/human MCC ratio, {r.population}", r.ratio_model_over_human, r.ratio_lo, r.ratio_hi, "primary (human ceiling)", "human_ceiling.csv")
    nd = rd("human_ceiling_neardup.csv")
    for r in nd.itertuples():
        add(f"Human-vs-human MCC between same-project near-duplicates, {r.smell}", r.MCC, r.MCC_lo, r.MCC_hi,
            "primary (second ceiling)", "human_ceiling_neardup.csv", f"{r.pairs} pairs in {r.groups} groups")
    a1 = rd("range_A1_tool_flags.csv")
    for r in a1[a1["smell/band"].isin(["CM", "LPL"])].itertuples():
        add(f"Share of DesigniteJava-flagged snippets inside the annotated band, {r[1]}", r.share_of_flagged_inside_band, None, None,
            "primary (range restriction, descriptive)", "range_A1_tool_flags.csv", f"{r.flagged_inside_band}/{r.flagged} flags; band holds {r.share_inside_band:.3f} of all snippets")
    a2 = rd("range_A2_trend.csv")
    for r in a2.itertuples():
        add(f"Within-band logistic OR per unit of the primary metric, {r.smell}", r.logit_OR_per_unit, r.OR_lo, r.OR_hi,
            "primary (range restriction)", "range_A2_trend.csv", f"Cochran–Armitage z = {r.CA_z:.2f}, p = {r.CA_p:.2g}")
    # ---- Prompt 4 additions
    mm = rd("agreement_matched_neardup.csv")
    for r in mm[mm.population.isin(["CM", "LPL"])].itertuples():
        add(f"Same-snippet minus cross-snippet human MCC on matched near-duplicate entities, {r.population}", r.diff_MCC, r.diff_lo, r.diff_hi,
            "primary (agreement anatomy)", "agreement_matched_neardup.csv",
            f"same {r.same_MCC:.3f}, cross {r.cross_MCC:.3f}; {r.groups} groups, {r.entities} entities")
    ex = rd("agreement_exact_dup.csv")
    for r in ex[ex.population.isin(["CM", "LPL"])].itertuples():
        if str(r.reported_as).startswith("CI"):
            add(f"Same-snippet minus cross-snippet human MCC on exact duplicates, {r.population}", r.diff_MCC, r.diff_lo, r.diff_hi,
                "primary (agreement anatomy)", "agreement_exact_dup.csv", f"{r.groups} groups")
    lg = rd("agreement_gap_logit.csv")
    for r in lg[(lg.set == "primary")].itertuples():
        add(f"OR of unanimous per unit log(annotation-id gap), {r.population}", r.OR_per_log_gap, r.OR_lo, r.OR_hi,
            "primary (agreement anatomy)", "agreement_gap_logit.csv", f"adjusted for the primary metric; p = {r.p:.2g}")
    ea = rd("external_B1_agreement.csv")
    for r in ea.itertuples():
        add(f"External C#: share needing a third rating, {r.smell}", r.third_rating_share, r.third_lo, r.third_hi, "external check",
            "external_B1_agreement.csv", f"first-pair ordinal alpha bounds {r.alpha_ordinal_min:.3f}–{r.alpha_ordinal_max:.3f}")
    eu = rd("external_B1_auc.csv")
    eu = eu[(eu.label == "final ≥ 1 (primary)") & eu.AUC.notna()]
    for r in eu.itertuples():
        add(f"External C#: ROC-AUC of {r.metric} ({r.orientation}), {r.smell}", r.AUC, r.AUC_lo, r.AUC_hi, "external check",
            "external_B1_auc.csv", f"{r.positives}/{r.n_with_metric} positives; project-cluster CI [{r.AUC_project_lo:.3f}, {r.AUC_project_hi:.3f}]")
    return rows


def headline_block():
    rows = headline_rows()
    out = ["| # | number | value [95% CI] | analysis type | table |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        if r["estimate"] is None:
            v = "n/a"
        elif r["ci_lo"] is None:
            v = f"{r['estimate']:.3f}"
        else:
            d = 0 if r["number"].startswith("Youden") else 3
            v = f"{r['estimate']:.{d}f} [{r['ci_lo']:.{d}f}, {r['ci_hi']:.{d}f}]"
        if r["note"]:
            v += f" ({r['note']})"
        out.append(f"| {i} | {r['number']} | {v} | {r['analysis_type']} | `tables/{r['source_table']}` |")
    import json
    with open(os.path.join(ROOT, "results/paper_numbers.json"), "w") as f:
        json.dump([{"id": i, **r, "ci_level": 0.95 if r["ci_lo"] is not None else None} for i, r in enumerate(rows, 1)],
                  f, indent=2, ensure_ascii=False)
    return ("\n".join(out) + "\n\nRows 1–15 are the Prompt 2 headline numbers; rows 16 onward were added in Prompt 3 and 3B. "
            "All values are read programmatically from the listed tables when this file is built, and the same rows are written to "
            "`results/paper_numbers.json`.\n")


if __name__ == "__main__":
    main()
