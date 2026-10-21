"""Prompt 3B A: range restriction (plan.md §6.1). A1-A3 primary (descriptive/tests), A4 exploratory."""
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

SEC = ["loc", "statements", "max_nesting", "comment_ratio", "method_calls", "mean_identifier_length"]


def universe():
    ann, smp, mm, cm, _ = load_tables()
    feats = load_features()
    m = smp[smp.is_class == 0].drop_duplicates("designite_id")
    m = m.merge(mm[["id", "cc", "pc", "loc"]], left_on="designite_id", right_on="id", suffixes=("", "_m"))
    m = m.merge(feats, left_on="path_to_file", right_on="path", how="left")
    c = smp[smp.is_class == 1].drop_duplicates("designite_id")
    n_c0 = len(c)
    c = c.merge(cm[["id", "lcom", "nof", "nom", "loc"]], left_on="designite_id", right_on="id", suffixes=("", "_c"))
    c = c.merge(feats, left_on="path_to_file", right_on="path", how="left")
    return m, c, {"method_snippets": len(m), "class_snippets_with_metrics": len(c),
                  "class_snippets_without_class_metrics": n_c0 - len(c)}


def cochran_armitage(x, y):
    """Two-sided Cochran-Armitage trend test; x scores, y binary."""
    df = pd.DataFrame({"x": x, "y": y}).groupby("x").y.agg(["sum", "size"])
    xs, s, n = df.index.values.astype(float), df["sum"].values, df["size"].values
    N, p = n.sum(), s.sum() / n.sum()
    T = np.sum(xs * (s - n * p))
    V = p * (1 - p) * (np.sum(n * xs ** 2) - np.sum(n * xs) ** 2 / N)
    z = T / np.sqrt(V)
    return float(z), float(2 * norm.sf(abs(z)))


def thorndike(r, u):
    return r * u / np.sqrt(1 + r ** 2 * (u ** 2 - 1))


def implied_auc(rc, p):
    d = rc / np.sqrt((1 - rc ** 2) * p * (1 - p))
    return float(norm.cdf(d / np.sqrt(2)))


def main():
    L = annotation_long()
    M, C, uinfo = universe()
    Eall = attach_metrics(entity_labels(L, min_ann=1))
    Ep = attach_metrics(variant_entities(L, "primary"))
    Er5 = attach_metrics(variant_entities(L, "R5"))
    bands = {}
    for s in SMELLS:
        x = Eall[Eall.smell == s][PRIMARY[s]]
        bands[s] = (float(x.min()), float(x.max()))
    x = Eall[(Eall.smell == "LPL") & ~Eall.pc3_empty.astype(bool)].pc
    bands["LPL R5"] = (float(x.min()), float(x.max()))

    # ---------------- A1
    a1 = []
    for key, s, U in (("CM", "CM", M), ("LPL", "LPL", M), ("LPL R5", "LPL", M), ("MA", "MA", C)):
        lo, hi = bands[key]
        v = U[PRIMARY[s]]
        inside = (v >= lo) & (v <= hi)
        if s == "MA":
            flag = (U.lcom >= 0.8) & (U.nof >= 7) & (U.nom >= 7)
            rule = "LCOM ≥ 0.8 & NOF ≥ 7 & NOM ≥ 7"
        else:
            flag = v >= DESIGNITE[s]
            rule = f"{PRIMARY[s]} ≥ {DESIGNITE[s]}"
        a1.append({"smell/band": key, "metric": PRIMARY[s], "annotated_band": f"{lo:g}–{hi:g}", "universe_snippets": len(U),
                   "inside_band": int(inside.sum()), "share_inside_band": float(inside.mean()),
                   "DesigniteJava_rule": rule, "flagged": int(flag.sum()), "share_flagged": float(flag.mean()),
                   "flagged_inside_band": int((flag & inside).sum()),
                   "share_of_flagged_inside_band": float((flag & inside).sum() / max(flag.sum(), 1)),
                   "flagged_above_band": int((flag & (v > hi)).sum())})
    A1 = pd.DataFrame(a1)
    A1["analysis"] = "primary (descriptive)"
    A1.to_csv(os.path.join(TAB, "range_A1_tool_flags.csv"), index=False)

    # ---------------- A2
    a2, a2v = [], []
    for key, E, s in (("CM", Ep, "CM"), ("LPL R5", Er5, "LPL")):
        u = E[(E.smell == s) & E.unanimous]
        x, y = u[PRIMARY[s]].values.astype(float), u.target.values.astype(int)
        z, p = cochran_armitage(x, y)
        fit = sm.Logit(y, sm.add_constant(x)).fit(disp=0)
        ci = fit.conf_int()[1]
        a2.append({"smell": key, "n": len(u), "n_smelly": int(y.sum()), "CA_z": z, "CA_p": p,
                   "logit_OR_per_unit": float(np.exp(fit.params[1])), "OR_lo": float(np.exp(ci[0])),
                   "OR_hi": float(np.exp(ci[1])), "logit_p": float(fit.pvalues[1])})
        g = u.groupby(PRIMARY[s]).target.agg(["size", "mean"]).reset_index()
        for r in g.itertuples(index=False):
            a2v.append({"smell": key, "value": r[0], "entities": int(r[1]), "share_smelly": float(r[2])})
    A2 = pd.DataFrame(a2)
    A2["analysis"] = "primary"
    A2.to_csv(os.path.join(TAB, "range_A2_trend.csv"), index=False)
    pd.DataFrame(a2v).to_csv(os.path.join(TAB, "range_A2_share_by_value.csv"), index=False)

    # ---------------- A3
    o = pd.read_csv(os.path.join(TAB, "rq3_odds_ratios.csv"))
    o = o[o.model == "full"]
    o5 = pd.read_csv(os.path.join(TAB, "rq3_odds_ratios_LPL_R5.csv"))
    a3 = []
    for key, E, s in (("CM", Ep, "CM"), ("LPL", Ep, "LPL"), ("LPL R5", Er5, "LPL"), ("MA", Ep, "MA")):
        U = C if s == "MA" else M
        e = E[E.smell == s]
        for f in [PRIMARY[s]] + SEC + (["nom", "nof"] if s == "MA" else []):
            sd_a, sd_u = float(e[f].std()), float(U[f].std())
            orow = (o5 if key == "LPL R5" else o)
            orow = orow[(orow.smell == s) & (orow.feature == f)] if key != "MA" else orow.iloc[0:0]
            a3.append({"smell": key, "feature": f, "role": "primary metric" if f == PRIMARY[s] else "secondary",
                       "SD_annotated": sd_a, "SD_universe": sd_u, "SD_ratio": sd_a / sd_u,
                       "n_annotated": int(e[f].notna().sum()), "n_universe": int(U[f].notna().sum()),
                       "RQ3_OR_per_SD": float(orow.OR_per_SD.iloc[0]) if len(orow) else np.nan,
                       "OR_lo": float(orow.OR_lo.iloc[0]) if len(orow) else np.nan,
                       "OR_hi": float(orow.OR_hi.iloc[0]) if len(orow) else np.nan})
    A3 = pd.DataFrame(a3)
    A3["analysis"] = "primary (descriptive)"
    A3.to_csv(os.path.join(TAB, "range_A3_sd_ratios.csv"), index=False)

    # ---------------- A4 (exploratory)
    a4 = []
    r_ = rng()
    for key, E, s in (("CM", Ep, "CM"), ("LPL", Ep, "LPL"), ("LPL R5", Er5, "LPL")):
        uu = E[(E.smell == s) & E.unanimous]
        x, y = uu[PRIMARY[s]].values.astype(float), uu.target.values.astype(float)
        u = float(M[PRIMARY[s]].std() / E[E.smell == s][PRIMARY[s]].std())
        r = float(np.corrcoef(x, y)[0, 1])
        p = float(y.mean())
        rc = thorndike(r, u)
        bs_rc, bs_auc = [], []
        for _ in range(B):
            i = r_.integers(0, len(x), len(x))
            if y[i].min() == y[i].max():
                continue
            rb = float(np.corrcoef(x[i], y[i])[0, 1])
            rcb = thorndike(rb, u)
            bs_rc.append(rcb)
            bs_auc.append(implied_auc(rcb, float(y[i].mean())))
        q2 = pd.read_csv(os.path.join(TAB, "rq2_threshold_validity.csv")).set_index("smell")
        obs_auc = float(q2.loc[s].auc) if key != "LPL R5" else float(
            pd.read_csv(os.path.join(TAB, "robustness_long.csv")).query("check == 'R5' and smell == 'LPL' and headline == 'RQ2 ROC-AUC (primary metric)'").estimate.iloc[0])
        a4.append({"smell": key, "n": len(x), "point_biserial_r": r, "u_SD_universe_over_annotated": u, "corrected_r": rc,
                   "corrected_r_lo": boot_ci(bs_rc)[0], "corrected_r_hi": boot_ci(bs_rc)[1],
                   "implied_AUC_uncorrected": implied_auc(r, p), "implied_AUC_corrected": implied_auc(rc, p),
                   "implied_AUC_lo": boot_ci(bs_auc)[0], "implied_AUC_hi": boot_ci(bs_auc)[1], "observed_AUC_RQ2": obs_auc})
    A4 = pd.DataFrame(a4)
    A4["analysis"] = "exploratory"
    A4.to_csv(os.path.join(TAB, "range_A4_thorndike.csv"), index=False)

    # ---------------- markdown
    t1 = A1.copy()
    for c in ("share_inside_band", "share_flagged", "share_of_flagged_inside_band"):
        t1[c] = t1[c].round(4)
    t2 = A2.copy()
    t2["CA z (p)"] = [f"{a:.2f} ({fmt_p(b)})" for a, b in zip(t2.CA_z, t2.CA_p)]
    t2["logistic OR per unit [95% CI] (p)"] = [f"{fmt_ci(a, b, c)} ({fmt_p(d)})" for a, b, c, d in zip(t2.logit_OR_per_unit, t2.OR_lo, t2.OR_hi, t2.logit_p)]
    t2 = t2[["smell", "n", "n_smelly", "CA z (p)", "logistic OR per unit [95% CI] (p)"]]
    v = pd.DataFrame(a2v)
    v["share_smelly"] = v.share_smelly.round(3)
    v = v.pivot_table(index="value", columns="smell", values=["entities", "share_smelly"], aggfunc="first")
    v.columns = [f"{b} {a}" for a, b in v.columns]
    v = v.reset_index().astype(object).where(lambda d: d.notna(), "–")
    t3 = A3.copy()
    for c in ("SD_annotated", "SD_universe", "SD_ratio"):
        t3[c] = t3[c].round(3)
    t3["RQ3 OR per SD [95% CI]"] = [fmt_ci(a, b, c) if np.isfinite(a) else "n/a" for a, b, c in zip(t3.RQ3_OR_per_SD, t3.OR_lo, t3.OR_hi)]
    t3 = t3[["smell", "feature", "role", "SD_annotated", "SD_universe", "SD_ratio", "RQ3 OR per SD [95% CI]"]]
    t4 = A4.copy()
    t4["corrected r [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(t4.corrected_r, t4.corrected_r_lo, t4.corrected_r_hi)]
    t4["implied AUC corrected [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(t4.implied_AUC_corrected, t4.implied_AUC_lo, t4.implied_AUC_hi)]
    for c in ("point_biserial_r", "u_SD_universe_over_annotated", "implied_AUC_uncorrected", "observed_AUC_RQ2"):
        t4[c] = t4[c].round(3)
    t4 = t4[["smell", "n", "point_biserial_r", "u_SD_universe_over_annotated", "corrected r [95% CI]", "implied_AUC_uncorrected",
             "implied AUC corrected [95% CI]", "observed_AUC_RQ2"]]
    below = {k: float((M[PRIMARY[k]] < bands[k][0]).mean()) for k in ("CM", "LPL")}
    below_note = (f"For CM and LPL, u is close to or below 1. The universe distribution is concentrated below the band: "
                  f"{below['CM']:.3f} of methods have cc < {bands['CM'][0]:g} and {below['LPL']:.3f} have pc < {bands['LPL'][0]:g}. "
                  "An SD-based correction therefore does not represent restriction to an upper-tail band. "
                  "A1, the share of snippets and of tool flags inside the band, is the more direct description of the restriction.")
    sent = "; ".join(f"{r['smell/band']}: {r['share_inside_band']:.3f} of snippets inside the band, {r['share_of_flagged_inside_band']:.3f} of DesigniteJava-flagged snippets inside the band"
                     for r in a1)
    txt = f"""**Analysis type: A1–A3 primary (descriptive or tested as stated); A4 exploratory.** plan.md §6.1.

**Snippet universe:** {uinfo['method_snippets']:,} method snippets and {uinfo['class_snippets_with_metrics']:,} class snippets in the 10 projects, deduplicated by DesigniteJava id. A further {uinfo['class_snippets_without_class_metrics']} class snippets have no `class_metrics` row and are excluded.
Annotated bands are the observed [min, max] of each primary metric over all annotated entities (§1.5). LPL R5 excludes the pc = 3 entities.

**A1: where the tool rule decides**

{md_table(t1)}

**A2: within-band trend** (unanimous entities; Cochran–Armitage two-sided; logistic regression of label on metric)

{md_table(t2)}

Share smelly by metric value:

{md_table(v)}

**A3: SD of each feature, annotated versus universe**
- An SD ratio near 1 means the feature is not range-restricted in the annotated set.
- RQ3 ORs come from the primary GEE (LPL R5 from §5.10). MA has no RQ3 model.

{md_table(t3)}

**A4 (EXPLORATORY): Thorndike Case II correction**
- r is the point-biserial correlation between the primary metric and the unanimous label. u = SD(universe) / SD(annotated) of the primary metric.
- Implied AUC = Φ(d/√2), with d = r / √((1 − r²)pq).
- **Assumptions:**
  - the relation is linear and homoscedastic across the full metric range;
  - selection into the annotated set depends on the metric only;
  - the label/metric relation is binormal.
- These corrected values are model-based extrapolations, not observed quantities. The observed AUC from RQ2 is shown for comparison.
- CI: bootstrap over entities (B = {B}) with u fixed.

{md_table(t4)}

{below_note}

Tables: `tables/range_A1_tool_flags.csv`, `range_A2_trend.csv`, `range_A2_share_by_value.csv`, `range_A3_sd_ratios.csv`, `range_A4_thorndike.csv`.

**Summary.** {sent}.
"""
    write_frag("range_restriction", txt)
    print(txt)


if __name__ == "__main__":
    main()
