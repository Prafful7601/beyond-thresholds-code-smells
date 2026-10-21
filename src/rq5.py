"""RQ5 Ambiguity (plan.md §2 RQ5, §4.3): unanimous vs split entities on every feature.

Two-sided Mann-Whitney U, Cliff's delta (split minus unanimous direction) with stratified bootstrap CI.
BH family = all CM and LPL tests; MA reported with raw p only (descriptive, D8).
"""
import functools
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

FAMILY = ["CM", "LPL"]


def cliffs_delta(a, b):
    """P(a > b) - P(a < b) via the U statistic (ties count half)."""
    u = mannwhitneyu(a, b, alternative="two-sided").statistic
    return 2 * u / (len(a) * len(b)) - 1


def tests(E, smells, boot=True):
    rows = []
    r_ = rng()
    for smell in smells:
        e = E[E.smell == smell]
        for f in feature_cols(smell):
            sp = e[~e.unanimous][f].dropna().values
            un = e[e.unanimous][f].dropna().values
            if len(sp) < 2 or len(un) < 2:
                rows.append({"smell": smell, "feature": f, "n_split": len(sp), "n_unanimous": len(un)})
                continue
            res = mannwhitneyu(sp, un, alternative="two-sided")
            d = 2 * res.statistic / (len(sp) * len(un)) - 1
            lo = hi = np.nan
            if boot:
                bs = [cliffs_delta(r_.choice(sp, len(sp)), r_.choice(un, len(un))) for _ in range(B)]
                lo, hi = boot_ci(bs)
            rows.append({"smell": smell, "feature": f, "n_split": len(sp), "n_unanimous": len(un),
                         "median_split": float(np.median(sp)), "median_unanimous": float(np.median(un)),
                         "U": float(res.statistic), "p": float(res.pvalue), "cliffs_delta": d,
                         "delta_lo": lo, "delta_hi": hi})
    T = pd.DataFrame(rows)
    fam = T.smell.isin(FAMILY) & T.p.notna()
    T["p_BH"] = np.nan
    T.loc[fam, "p_BH"] = bh(T.loc[fam, "p"].values)
    T["analysis"] = np.where(T.smell.isin(FAMILY), "primary", "descriptive (MA, D8; not in BH family)")
    return T


@functools.lru_cache(maxsize=None)
def _variant_tests(variant):
    L = annotation_long()
    E = attach_metrics(variant_entities(L, variant))
    return tests(E, FAMILY)


def headline(L, variant, smell):
    """Robustness hook: Cliff's delta of the primary metric and number of BH-significant features."""
    if smell not in FAMILY:
        return []
    T = _variant_tests(variant)
    t = T[T.smell == smell]
    r = t[t.feature == PRIMARY[smell]].iloc[0]
    return [{"headline": "RQ5 Cliff's delta (split − unanimous) of primary metric", "estimate": r.cliffs_delta,
             "lo": r.delta_lo, "hi": r.delta_hi, "n": int(r.n_split + r.n_unanimous),
             "note": f"{int(r.n_split)} split"},
            {"headline": "RQ5 features with BH p < 0.05 (of 6)", "estimate": float((t.p_BH < 0.05).sum()),
             "lo": np.nan, "hi": np.nan, "n": int(r.n_split + r.n_unanimous)}]


def main():
    L = annotation_long()
    E = attach_metrics(variant_entities(L, "primary"))
    T = tests(E, SMELLS)
    T.to_csv(os.path.join(TAB, "rq5_ambiguity.csv"), index=False)

    plt = plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.2), sharex=True)
    for ax, smell in zip(axes, SMELLS):
        x = T[T.smell == smell].reset_index(drop=True)
        ys = np.arange(len(x))[::-1]
        for yy, r in zip(ys, x.itertuples()):
            sig = (r.p_BH < 0.05) if smell in FAMILY else False
            c = COL["orange"] if sig else COL["ink2"]
            ax.plot([r.delta_lo, r.delta_hi], [yy, yy], color=c, lw=1.2)
            ax.scatter(r.cliffs_delta, yy, color=c, s=18, zorder=3, marker="o" if sig else "D")
        ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
        ax.set_yticks(ys)
        ax.set_yticklabels(x.feature)
        n_sp, n_un = int(x.n_split.iloc[0]), int(x.n_unanimous.iloc[0])
        ax.set_title(f"{smell}{' (descriptive)' if smell not in FAMILY else ''}\nsplit {n_sp} vs unanimous {n_un}",
                     loc="left")
        ax.set_xlabel("Cliff's delta (split − unanimous)")
        ax.grid(axis="y", visible=False)
    axes[0].scatter([], [], color=COL["orange"], s=18, label="BH p < 0.05")
    axes[0].scatter([], [], color=COL["ink2"], s=18, marker="D", label="not significant / MA")
    axes[0].legend(loc="lower left", fontsize=5.5)
    fig.tight_layout()
    savefig(fig, "rq5_ambiguity")

    M = T.copy()
    M["Cliff's delta [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(M.cliffs_delta, M.delta_lo, M.delta_hi)]
    M["U"] = M.U.round(0).astype(int)
    M["p"] = [fmt_p(v) for v in M.p]
    M["p (BH)"] = [fmt_p(v) if np.isfinite(v) else "n/a (MA)" for v in M.p_BH]
    for c in ("median_split", "median_unanimous"):
        M[c] = M[c].round(3)
    M = M[["smell", "analysis", "feature", "n_split", "n_unanimous", "median_split", "median_unanimous", "U", "p",
           "p (BH)", "Cliff's delta [95% CI]"]]
    fam = T[T.smell.isin(FAMILY)]
    n_sig = int((fam.p_BH < 0.05).sum())
    sent = (f"{n_sig} of {len(fam)} CM/LPL tests have BH p < 0.05; primary-metric deltas: " +
            "; ".join(f"{s} {PRIMARY[s]} {fmt_ci(*fam[(fam.smell == s) & (fam.feature == PRIMARY[s])][['cliffs_delta', 'delta_lo', 'delta_hi']].values[0])}"
                      for s in FAMILY))
    txt = f"""**Analysis type: primary (CM, LPL); MA descriptive.**

**Method.**
- Data: primary set, all entities with ≥ 2 usable annotations.
- Groups: unanimous (all answers equal) versus split (≥ 1 dissent). With 2 annotations, split = tie (D11).
- Test: two-sided Mann–Whitney U (`scipy` 1.13.1).
- Effect size: Cliff's delta = P(split > unanimous) − P(split < unanimous). 95% CI from a stratified bootstrap (B = {B}, resampling within groups, seed {SEED}).
- The BH family is all {len(fam)} CM and LPL tests. MA tests are shown with raw p only.

{md_table(M)}

Table: `tables/rq5_ambiguity.csv`. Figure: `figures/rq5_ambiguity.pdf` (.png).

**Summary.** {sent}.
"""
    write_frag("rq5", txt)
    print(txt)


if __name__ == "__main__":
    main()
