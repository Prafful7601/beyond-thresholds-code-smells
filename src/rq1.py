"""RQ1 Agreement (plan §2 RQ1, D12). Primary set: consistency-filtered annotations, entities with >= 2 usable."""
import os
import sys

import krippendorff
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402


def agreement_table(L, label):
    E = entity_labels(L)
    rows, splits = [], []
    for s in SMELLS:
        e = E[E.smell == s]
        n, y = e.n.values, e.y.values
        a_own = alpha_binary(n, y)
        m = int(n.max())
        R = np.full((m, len(e)), np.nan)
        for j, (nn, yy) in enumerate(zip(n, y)):
            R[:nn, j] = [1] * yy + [0] * (nn - yy)
        a_pkg = krippendorff.alpha(reliability_data=R, level_of_measurement="nominal")
        assert abs(a_own - a_pkg) < 1e-9, (s, a_own, a_pkg)
        r = rng()
        bs_a, bs_p = [], []
        for _ in range(B):
            idx = r.integers(0, len(e), len(e))
            bs_a.append(alpha_binary(n[idx], y[idx]))
            bs_p.append(pct_agreement(n[idx], y[idx]))
        alo, ahi = boot_ci(bs_a)
        plo, phi = boot_ci(bs_p)
        rows.append({"set": label, "smell": s, "entities": len(e), "annotations": int(n.sum()),
                     "yes_rate": round(y.sum() / n.sum(), 3),
                     "pct_agreement": round(pct_agreement(n, y), 3), "pct_agreement_lo": round(plo, 3),
                     "pct_agreement_hi": round(phi, 3),
                     "kripp_alpha": round(a_own, 3), "alpha_lo": round(alo, 3), "alpha_hi": round(ahi, 3),
                     "unanimous_share": round(float(e.unanimous.mean()), 3)})
        vs = e.groupby(["n", "y"]).size().rename("entities").reset_index()
        vs.insert(0, "smell", s)
        vs["share"] = (vs.entities / len(e)).round(3)
        splits.append(vs)
    return pd.DataFrame(rows), pd.concat(splits, ignore_index=True)


def main():
    L = annotation_long()
    T, S = agreement_table(primary_filter(L), "primary")
    T.to_csv(os.path.join(TAB, "rq1_agreement.csv"), index=False)
    S.to_csv(os.path.join(TAB, "rq1_vote_splits.csv"), index=False)

    # figure: vote-split composition per smell
    plt = plot_style()
    E = entity_labels(primary_filter(L))
    fig, ax = plt.subplots(figsize=(3.4, 1.5))
    cats = [("unanimous no", COL["blue"]), ("split", "#b9b8b2"), ("unanimous yes", COL["orange"])]
    for i, s in enumerate(SMELLS[::-1]):
        e = E[E.smell == s]
        shares = [float((e.y == 0).mean()), float((~e.unanimous).mean()), float(((e.y == e.n) & (e.n > 0)).mean())]
        left = 0
        for (name, c), v in zip(cats, shares):
            ax.barh(i, v, left=left, color=c, height=0.6, edgecolor="white", linewidth=1, label=name if i == 0 else None)
            if v >= 0.06:
                ax.text(left + v / 2, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                        color="white" if name != "split" else COL["ink"])
            left += v
    ax.set_yticks(range(3))
    ax.set_yticklabels([f"{s} (n={int((E.smell == s).sum())})" for s in SMELLS[::-1]])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of entities")
    ax.grid(False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    fig.tight_layout()
    savefig(fig, "rq1_vote_splits")

    t = T.copy()
    t["percent agreement [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(t.pct_agreement, t.pct_agreement_lo, t.pct_agreement_hi)]
    t["Krippendorff alpha [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(t.kripp_alpha, t.alpha_lo, t.alpha_hi)]
    t = t[["smell", "entities", "annotations", "yes_rate", "unanimous_share", "percent agreement [95% CI]",
           "Krippendorff alpha [95% CI]"]]
    s_md = S.copy()
    s_md["votes (yes/n)"] = s_md.y.astype(str) + "/" + s_md.n.astype(str)
    s_md = s_md.pivot_table(index="votes (yes/n)", columns="smell", values="entities", aggfunc="sum").reindex(columns=SMELLS)
    s_md = s_md.fillna(0).astype(int)
    order = sorted(s_md.index, key=lambda v: (int(v.split("/")[1]), int(v.split("/")[0])))
    s_md = s_md.loc[order]
    sent = "; ".join(f"{r.smell} alpha = {r.kripp_alpha:.3f} [{r.alpha_lo:.3f}, {r.alpha_hi:.3f}], "
                     f"percent agreement = {r.pct_agreement:.3f}" for r in T.itertuples())
    txt = f"""**Method.**
- Primary annotation set: consistency-filtered (D7), with entities that have ≥ 2 usable annotations.
- Percent agreement is the mean over entities of the share of agreeing annotation pairs.
- Krippendorff's alpha is nominal and computed with `krippendorff` 0.8.1. Each entity's answers fill arbitrary coder rows, because the data have no annotator ids; nominal alpha depends only on within-unit value counts.
- An independent implementation from the coincidence matrix agrees with the package to within 1e-9 for every smell.
- 95% CIs are bootstrap percentile intervals (B = {B}, resampling entities, seed {SEED}).
- Per-annotator counts and yes-rates are not computable, because there are no annotator ids (D12).
- No hypothesis test is planned for RQ1. Values are read against Krippendorff's 0.667 / 0.800 benchmarks.

**Agreement per smell**

{md_table(t)}

**Vote-split distribution (entities)**

{md_table(s_md, index=True)}

Tables: `tables/rq1_agreement.csv`, `tables/rq1_vote_splits.csv`. Figure: `figures/rq1_vote_splits.pdf` (.png).

**Summary.** {sent}.
"""
    write_frag("rq1", txt)
    print(txt)


if __name__ == "__main__":
    main()
