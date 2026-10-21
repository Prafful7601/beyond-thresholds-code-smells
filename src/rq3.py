"""RQ3 What drives human judgment (plan.md §2 RQ3, §4.3). CM and LPL; primary set.

Annotation-level GEE (Binomial, logit, exchangeable, groups = entity, robust SEs) on the primary metric and the
§1.6 secondary features, z-standardised over entities. VIF check with a reduced model if any VIF > 5.
Depth-3 decision tree on unanimous entities.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.tree import DecisionTreeClassifier, export_text
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

warnings.filterwarnings("ignore")
MODEL_SMELLS = ["CM", "LPL"]


def design(A, E, feats):
    """Standardise features over entities, then attach to annotation rows."""
    Ez = E[["entity"] + feats].dropna().copy()
    mu, sd = Ez[feats].mean(), Ez[feats].std(ddof=0)
    Ez[feats] = (Ez[feats] - mu) / sd
    D = A[["entity", "answer"]].merge(Ez, on="entity", how="inner")
    return D, Ez


def vif_table(Ez, feats):
    X = sm.add_constant(Ez[feats].values)
    return {f: float(variance_inflation_factor(X, i + 1)) for i, f in enumerate(feats)}


def fit_gee(D, feats):
    X = sm.add_constant(D[feats])
    m = sm.GEE(D.answer.astype(float), X, groups=D.entity, family=sm.families.Binomial(),
               cov_struct=sm.cov_struct.Exchangeable())
    return m.fit(cov_type="robust")


def gee_rows(res, feats, smell, model_name):
    ci = res.conf_int()
    rows = []
    for f in feats:
        rows.append({"smell": smell, "model": model_name, "feature": f, "OR_per_SD": float(np.exp(res.params[f])),
                     "OR_lo": float(np.exp(ci.loc[f, 0])), "OR_hi": float(np.exp(ci.loc[f, 1])),
                     "beta": float(res.params[f]), "se_robust": float(res.bse[f]), "z": float(res.tvalues[f]),
                     "p": float(res.pvalues[f])})
    return rows


def prep(L, variant, smell):
    A, E = variant_annotations(L, variant)
    A, E = A[A.smell == smell], attach_metrics(E[E.smell == smell])
    return A, E


def headline(L, variant, smell):
    """Robustness hook: OR per SD of the primary metric from the full GEE."""
    feats = feature_cols(smell)
    A, E = prep(L, variant, smell)
    D, Ez = design(A, E, feats)
    res = fit_gee(D, feats)
    f = PRIMARY[smell]
    ci = res.conf_int()
    return [{"headline": "RQ3 GEE OR per SD of primary metric", "estimate": float(np.exp(res.params[f])),
             "lo": float(np.exp(ci.loc[f, 0])), "hi": float(np.exp(ci.loc[f, 1])), "n": int(Ez.shape[0]),
             "note": f"p={fmt_p(float(res.pvalues[f]))}"}]


def main():
    L = annotation_long()
    rows, vifs, info, rules = [], [], [], []
    for smell in MODEL_SMELLS:
        feats = feature_cols(smell)
        A, E = prep(L, "primary", smell)
        D, Ez = design(A, E, feats)
        v = vif_table(Ez, feats)
        vifs += [{"smell": smell, "model": "full", "feature": f, "VIF": x} for f, x in v.items()]
        res = fit_gee(D, feats)
        rows += gee_rows(res, feats, smell, "full")
        info.append({"smell": smell, "model": "full", "annotations": len(D), "entities": D.entity.nunique(),
                     "yes_rate": round(D.answer.mean(), 3), "working_correlation": round(float(res.cov_struct.dep_params), 3),
                     "features": ", ".join(feats)})
        # reduced model rule (plan §4.3)
        red = list(feats)
        dropped = []
        while True:
            vv = vif_table(Ez, red)
            cand = {f: x for f, x in vv.items() if f != PRIMARY[smell] and x > 5}
            if not cand:
                break
            worst = max(cand, key=cand.get)
            red.remove(worst)
            dropped.append(f"{worst} (VIF {cand[worst]:.2f})")
        if dropped:
            vifs += [{"smell": smell, "model": "reduced", "feature": f, "VIF": x} for f, x in vif_table(Ez, red).items()]
            res_r = fit_gee(D, red)
            rows += gee_rows(res_r, red, smell, "reduced")
            info.append({"smell": smell, "model": "reduced", "annotations": len(D), "entities": D.entity.nunique(),
                         "yes_rate": round(D.answer.mean(), 3),
                         "working_correlation": round(float(res_r.cov_struct.dep_params), 3),
                         "features": ", ".join(red) + "; dropped: " + "; ".join(dropped)})
        # decision tree on unanimous entities
        U = E[E.unanimous].dropna(subset=feats)
        tree = DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=SEED)
        tree.fit(U[feats].values, U.target.values.astype(int))
        txt = export_text(tree, feature_names=feats, show_weights=True, decimals=3)
        rules.append(f"=== {smell} ({SMELL_NAME[smell]}): depth-3 DecisionTreeClassifier(class_weight='balanced', "
                     f"random_state={SEED}) on {len(U)} unanimous entities "
                     f"({int(U.target.sum())} smelly / {int((1 - U.target).sum())} benign), unstandardised features.\n"
                     f"Leaf weights are class-weighted sample counts [benign, smelly].\n{txt}")
    R = pd.DataFrame(rows)
    R["p_BH_within_smell_model"] = np.nan
    for (s, m), idx in R.groupby(["smell", "model"]).groups.items():
        R.loc[idx, "p_BH_within_smell_model"] = bh(R.loc[idx, "p"].values)
    R["analysis"] = "primary"
    R.to_csv(os.path.join(TAB, "rq3_odds_ratios.csv"), index=False)
    V = pd.DataFrame(vifs)
    V.to_csv(os.path.join(TAB, "rq3_vif.csv"), index=False)
    I = pd.DataFrame(info)
    open(os.path.join(TAB, "rq3_tree_rules.txt"), "w").write("\n".join(rules))

    plt = plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2), sharex=True)
    for ax, smell in zip(axes, MODEL_SMELLS):
        x = R[(R.smell == smell) & (R.model == "full")].reset_index(drop=True)
        ys = np.arange(len(x))[::-1]
        for yy, r in zip(ys, x.itertuples()):
            sig = r.p_BH_within_smell_model < 0.05
            c = COL["orange"] if sig else COL["ink2"]
            ax.plot([r.OR_lo, r.OR_hi], [yy, yy], color=c, lw=1.2)
            ax.scatter(r.OR_per_SD, yy, color=c, s=18, zorder=3, marker="o" if sig else "D")
        ax.axvline(1, color=COL["ink2"], lw=0.6, ls=":")
        ax.set_yticks(ys)
        ax.set_yticklabels(x.feature)
        ax.set_xscale("log")
        ax.set_xlabel("odds ratio per 1 SD (log scale)")
        ax.set_title(f"{SMELL_NAME[smell]} (full GEE)", loc="left")
        ax.grid(axis="y", visible=False)
    axes[1].scatter([], [], color=COL["orange"], s=18, label="BH p < 0.05")
    axes[1].scatter([], [], color=COL["ink2"], s=18, marker="D", label="BH p ≥ 0.05")
    axes[1].legend(loc="lower right", fontsize=6)
    fig.tight_layout()
    savefig(fig, "rq3_odds_ratios")

    T = R.copy()
    T["OR per SD [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(T.OR_per_SD, T.OR_lo, T.OR_hi)]
    T["z"] = T.z.round(2)
    T["p"] = [fmt_p(v) for v in T.p]
    T["p (BH)"] = [fmt_p(v) for v in T.p_BH_within_smell_model]
    T = T[["smell", "model", "feature", "OR per SD [95% CI]", "z", "p", "p (BH)"]]
    Vm = V.copy()
    Vm["VIF"] = Vm.VIF.round(2)
    Vw = Vm.pivot_table(index=["smell", "model"], columns="feature", values="VIF").reset_index().astype(object).fillna("–")
    full = R[R.model == "full"]
    sent = "; ".join(f"{s}: OR per SD of {PRIMARY[s]} = {fmt_ci(*full[(full.smell == s) & (full.feature == PRIMARY[s])][['OR_per_SD', 'OR_lo', 'OR_hi']].values[0])}"
                     for s in MODEL_SMELLS)
    txt = f"""**Analysis type: primary.** MA is not modelled (D8).

**Method.**
- Annotation-level **GEE** (`statsmodels` 0.14.4 `GEE`): Binomial family, logit link, exchangeable working correlation, groups = entity, robust (sandwich) covariance.
- Data: consistency-filtered annotations for every entity with ≥ 2 usable annotations, unanimous and split (D11).
- Predictors: the primary metric and the §1.6 secondary features, each z-standardised over entities. ORs are per 1 SD.
- BH adjustment is within smell and model.
- VIFs are computed on the entity-level standardised design. If any non-primary VIF > 5, a reduced model drops the highest-VIF feature repeatedly (plan §4.3).
- Decision tree: depth 3, `class_weight='balanced'`, on unanimous entities, with raw (unstandardised) features.
- Entities with missing features are dropped (LPL: 1 entity).

**Model data**

{md_table(I)}

**Odds ratios per 1 SD**

{md_table(T)}

**VIF**

{md_table(Vw)}

{"No VIF exceeds 5, so no reduced model was fitted (plan §4.3 rule)." if not (V.VIF > 5).any() else "At least one VIF exceeds 5; the reduced model is reported above."}

**Decision-tree rules** (`tables/rq3_tree_rules.txt`)

```
{chr(10).join(rules)}
```

Tables: `tables/rq3_odds_ratios.csv`, `tables/rq3_vif.csv`, `tables/rq3_tree_rules.txt`. Figure: `figures/rq3_odds_ratios.pdf` (.png).

**Summary.** {sent}.
"""
    write_frag("rq3", txt)
    print(txt)


if __name__ == "__main__":
    main()
