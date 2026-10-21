"""Prompt 3 §3 / plan.md §5.3: specification curves, MA audit sentence, exploratory CM C3 reweighting."""
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_sample_weight

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402

SPEC = [("alpha", "RQ1 Krippendorff alpha", 0.667, "Krippendorff's alpha"),
        ("auc", "RQ2 ROC-AUC (primary metric)", 0.5, "primary-metric ROC-AUC"),
        ("rq4_LR", "RQ4 MCC transfer − GroupKFold (LR)", 0.0, "MCC transfer − GroupKFold (LR)"),
        ("rq4_RF", "RQ4 MCC transfer − GroupKFold (RF)", 0.0, "MCC transfer − GroupKFold (RF)")]


def spec_rows():
    R = pd.read_csv(os.path.join(TAB, "robustness_long.csv"))
    rows = []
    for key, head, ref, lab in SPEC:
        x = R[(R.headline == head) & R.estimate.notna()]
        for r in x.itertuples():
            rows.append({"spec": key, "smell": r.smell, "condition": r.check, "estimate": r.estimate, "lo": r.lo, "hi": r.hi,
                         "n": r.n, "reference": ref, "label": lab})
    mc = pd.read_csv(os.path.join(TAB, "model_comparison.csv"))
    for r in mc[mc.best_model].itertuples():
        rows.append({"spec": "best_mcc", "smell": r.smell, "condition": f"primary ({r.model})", "estimate": r.MCC,
                     "lo": r.MCC_lo, "hi": r.MCC_hi, "n": r.n, "reference": 0.0, "label": "B best-model MCC"})
    r5 = pd.read_csv(os.path.join(TAB, "model_comparison_LPL_R5.csv"))
    r = r5[r5.best_model].iloc[0]
    rows.append({"spec": "best_mcc", "smell": "LPL", "condition": f"R5 ({r.model})", "estimate": r.MCC, "lo": r.MCC_lo,
                 "hi": r.MCC_hi, "n": int(r.n) if "n" in r5.columns else np.nan,
                 "reference": 0.0, "label": "B best-model MCC"})
    return pd.DataFrame(rows)


def plot_spec(S, plt):
    for key in S.spec.unique():
        x = S[S.spec == key]
        smells = [s for s in SMELLS if s in set(x.smell)]
        fig, axes = plt.subplots(1, len(smells), figsize=(2.35 * len(smells), 2.2), sharey=False, squeeze=False)
        for ax, s in zip(axes[0], smells):
            d = x[x.smell == s].sort_values("estimate").reset_index(drop=True)
            xs = np.arange(len(d))
            col = [COL["orange"] if c.startswith("primary") else COL["blue"] for c in d.condition]
            ax.errorbar(xs, d.estimate, yerr=[d.estimate - d.lo, d.hi - d.estimate], fmt="none", ecolor=COL["ink2"], lw=1)
            ax.scatter(xs, d.estimate, c=col, s=18, zorder=3)
            ax.axhline(d.reference.iloc[0], color=COL["ink2"], lw=0.7, ls=":")
            ax.set_xticks(xs)
            ax.set_xticklabels(d.condition, rotation=60, ha="right", fontsize=6)
            ax.set_title(s, loc="left")
            ax.grid(axis="x", visible=False)
        axes[0][0].set_ylabel(x.label.iloc[0])
        fig.tight_layout()
        savefig(fig, f"spec_curve_{key}")


def cm_reweight():
    """EXPLORATORY: CM C3 DACOSX + DACOS with equal total weight per source (class-balanced within source)."""
    smell = "CM"
    cache = load(f"step3_B_{smell}")
    splits = cache["splits"]
    m = load("step3_best")[smell]
    pb = cache["res"][m]["params"]
    D = unanimous(dacos_entities(smell))
    feats = full_features(smell)
    X, _ = dacosx_entities(smell)

    def build(tp, equal):
        xa = X[~X.project.isin(tp)][feats + ["target", "project"]].copy()
        da = D[~D.project.isin(tp)][feats + ["target", "project"]].copy()
        if equal:
            xa["w"] = compute_sample_weight("balanced", xa.target.astype(int))
            da["w"] = compute_sample_weight("balanced", da.target.astype(int))
            tot = (xa.w.sum() + da.w.sum()) / 2
            xa["w"] *= tot / xa.w.sum()
            da["w"] *= tot / da.w.sum()
        return pd.concat([xa, da])
    out = []
    for name, eq in (("as in C3 (pooled class weights)", False), ("equal source weight (class-balanced within source)", True)):
        res = run_protocol(m, D, feats, splits, pb, weighted=not eq, train_extra=eq,
                           train_override=lambda tp, eq=eq: build(tp, eq))
        s = summarise(res)
        out.append({"smell": smell, "model": m, "variant": name, **s,
                    "predicted_smelly_share": float(res["P"].mean())})
    return pd.DataFrame(out)


def main():
    t0 = time.time()
    plt = plot_style()
    S = spec_rows()
    S["analysis"] = np.where(S.condition.str.startswith("primary"), "primary", "robustness")
    S.to_csv(os.path.join(TAB, "spec_curves.csv"), index=False)
    plot_spec(S, plt)
    R = pd.read_csv(os.path.join(TAB, "robustness_long.csv"))
    a = R[(R.smell == "MA") & (R.headline == "RQ1 Krippendorff alpha")].set_index("check")
    ma = (f"- For MA, reading the answer from `isma` gives alpha {a.loc['primary'].estimate:.3f} [{a.loc['primary'].lo:.3f}, {a.loc['primary'].hi:.3f}] "
          f"(primary, consistency-filtered) and {a.loc['R6'].estimate:.3f} [{a.loc['R6'].lo:.3f}, {a.loc['R6'].hi:.3f}] (unfiltered, R6). "
          f"Reading it from `is_smell` gives {a.loc['R3'].estimate:.3f} [{a.loc['R3'].lo:.3f}, {a.loc['R3'].hi:.3f}] (all annotations, R3).\n")
    write_frag("audit_ma_note", ma)
    CW = cm_reweight()
    CW["analysis"] = "exploratory"
    CW.to_csv(os.path.join(TAB, "exploratory_cm_c3_reweight.csv"), index=False)
    s = S.copy()
    s["estimate [95% CI]"] = [fmt_ci(a_, b_, c_) for a_, b_, c_ in zip(s.estimate, s.lo, s.hi)]
    s = s[["spec", "smell", "condition", "analysis", "estimate [95% CI]", "reference"]]
    cw = CW.copy()
    for k in ("macro_F1", "MCC"):
        cw[k] = [metric_cell(r, k) for r in CW.to_dict("records")]
    cw["predicted_smelly_share"] = cw.predicted_smelly_share.round(3)
    cw = cw[["model", "variant", "macro_F1", "MCC", "predicted_smelly_share"]]
    collapse = CW.iloc[0]
    eq = CW.iloc[1]
    verdict = ("The collapse does not persist under equal source weighting" if abs(eq.MCC) > 0.02 and 0.02 < eq.predicted_smelly_share < 0.98
               else "The collapse persists under equal source weighting")
    txt_s = f"""**Analysis type: robustness summary (figures; no new tests).** plan.md §5.3.

Each panel plots one headline number per smell under every applicable condition (primary in orange, robustness checks in blue), sorted by estimate, with 95% CIs.
Reference lines: alpha 0.667, AUC 0.5, MCC difference 0, MCC 0. The B best-model MCC is shown for CM (primary) and LPL (primary and R5).

{md_table(s)}

Table: `tables/spec_curves.csv`. Figures: `figures/spec_curve_alpha.pdf`, `spec_curve_auc.pdf`, `spec_curve_rq4_LR.pdf`, `spec_curve_rq4_RF.pdf`, `spec_curve_best_mcc.pdf` (.png).
"""
    txt_x = f"""**CM C3 "DACOSX + DACOS" collapse under equal source weight** (exploratory; not in plan.md §4).

Method:
- CM best model ({collapse.model}) with section-B fold hyperparameters on the 25 splits, tested on held-out DACOS unanimous entities.
- Class-balanced weights are computed within each source, then rescaled so that DACOSX and DACOS contribute equal total weight. The model's own class weighting is switched off, so the weights are not applied twice.

{md_table(cw)}

{verdict}: MCC {eq.MCC:.3f} [{eq.MCC_lo:.3f}, {eq.MCC_hi:.3f}] with predicted-smelly share {eq.predicted_smelly_share:.3f}, versus MCC {collapse.MCC:.3f} and share {collapse.predicted_smelly_share:.3f} with pooled weights. Table: `tables/exploratory_cm_c3_reweight.csv`. Runtime {time.time() - t0:.0f}s.
"""
    write_frag("spec_curves", txt_s)
    write_frag("exploratory_cm_reweight", txt_x)
    print(ma, txt_s[-600:], txt_x)


if __name__ == "__main__":
    main()
