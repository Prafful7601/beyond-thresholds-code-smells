"""Step 3 A (baselines) and B (model comparison), plan.md §4.4-4.5. CM and LPL; primary analysis."""
import itertools
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402
from rq2 import youden  # noqa: E402

Q_NEMENYI_K5 = 2.728  # Studentized range q_0.05 / sqrt(2) for k = 5 (Demsar 2006, Table 5)
BASELINES = ["majority class", "DesigniteJava default rule", "Youden rule (fitted in training fold)"]


def baseline_res(name, D, smell, splits):
    y = D.target.values.astype(int)
    x = D[PRIMARY[smell]].values.astype(float)
    S = np.full((N_REPEATS, len(D)), np.nan)
    P = np.zeros((N_REPEATS, len(D)), bool)
    fold_mcc, params = {}, {}
    for r, k, tp in splits:
        te = D.project.isin(tp).values
        tr = ~te
        if name == "majority class":
            maj = int(y[tr].mean() >= 0.5)
            S[r, te], P[r, te] = float(maj), bool(maj)
            params[(r, k)] = {"majority": maj}
        elif name == "DesigniteJava default rule":
            S[r, te], P[r, te] = x[te], x[te] >= DESIGNITE[smell]
            params[(r, k)] = {"cut": DESIGNITE[smell]}
        else:
            c, _ = youden(x[tr], y[tr])
            S[r, te], P[r, te] = x[te], x[te] >= c
            params[(r, k)] = {"cut": float(c)}
        fold_mcc[(r, k)] = mcc(y[te], P[r, te])
    return {"S": S, "P": P, "y": y, "fold_mcc": fold_mcc, "params": params, "entity": D.entity.values}


def nemenyi(fold_tab):
    """fold_tab: rows = blocks (folds), cols = models, values = MCC. Rank 1 = best."""
    ranks = fold_tab.rank(axis=1, ascending=False, method="average")
    avg = ranks.mean()
    k, N = fold_tab.shape[1], fold_tab.shape[0]
    cd = Q_NEMENYI_K5 * np.sqrt(k * (k + 1) / (6 * N))
    return avg, cd


def cd_diagram(ax, avg, cd, title):
    avg = avg.sort_values()
    k = len(avg)
    ax.set_xlim(0.8, k + 0.2)
    ax.set_ylim(0.25, 1.02)
    ax.axhline(0.8, color=COL["ink2"], lw=0.8)
    for i in range(1, k + 1):
        ax.plot([i, i], [0.8, 0.83], color=COL["ink2"], lw=0.8)
        ax.text(i, 0.86, str(i), ha="center", fontsize=6)
    ax.plot([1, 1 + cd], [0.95, 0.95], color=COL["ink"], lw=1.2)
    ax.text(1 + cd / 2, 0.97, f"CD = {cd:.2f}", ha="center", fontsize=6)
    names = list(avg.index)
    for j, (m, rk) in enumerate(avg.items()):
        left = j < (k + 1) // 2
        yy = 0.65 - 0.12 * (j if left else (k - 1 - j))
        ax.plot([rk, rk], [0.8, yy], color=COL["ink2"], lw=0.6)
        xt = 0.85 if left else k + 0.15
        ax.plot([rk, xt], [yy, yy], color=COL["ink2"], lw=0.6)
        ax.text(xt + (-0.02 if left else 0.02), yy, f"{m} ({rk:.2f})", ha="right" if left else "left", va="center",
                fontsize=6)
    # cliques: maximal groups whose rank range <= cd
    cliques = []
    for i in range(k):
        j = i
        while j + 1 < k and avg.iloc[j + 1] - avg.iloc[i] <= cd:
            j += 1
        if j > i and not any(a <= i and j <= b for a, b in cliques):
            cliques.append((i, j))
    for n, (i, j) in enumerate(cliques):
        yy = 0.76 - 0.04 * n
        ax.plot([avg.iloc[i] - 0.03, avg.iloc[j] + 0.03], [yy, yy], color=COL["orange"], lw=2)
    ax.axis("off")
    ax.set_title(title, loc="left")


def main():
    t0 = time.time()
    base_rows, model_rows, fried_rows, pair_rows, fold_rows = [], [], [], [], []
    plt = plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 1.5))
    for ai, smell in enumerate(STEP3_SMELLS):
        D = unanimous(dacos_entities(smell))
        feats = full_features(smell)
        splits = project_splits(D.project)
        res = {}
        for b in BASELINES:
            res[b] = baseline_res(b, D, smell, splits)
            s = summarise(res[b])
            base_rows.append({"smell": smell, "baseline": b, "n": len(D), **s,
                              "cut_by_fold": ";".join(str(v.get("cut", v.get("majority"))) for v in res[b]["params"].values())})
        for m in MODEL_NAMES:
            res[m] = run_protocol(m, D, feats, splits)
            s = summarise(res[m])
            model_rows.append({"smell": smell, "model": m, "n": len(D), **s})
            print(smell, m, f"{time.time() - t0:.0f}s", round(s["MCC"], 3), flush=True)
        save({"res": res, "splits": splits, "entities": D.entity.values}, f"step3_B_{smell}")
        # Friedman + Nemenyi on fold-level MCC of the 5 algorithms
        ft = pd.DataFrame({m: [res[m]["fold_mcc"][(r, k)] for r, k, _ in splits] for m in MODEL_NAMES})
        for (r, k, _), row in zip(splits, ft.itertuples(index=False)):
            fold_rows.append({"smell": smell, "repeat": r, "fold": k, **dict(zip(MODEL_NAMES, row))})
        chi2, p = friedmanchisquare(*[ft[m].values for m in MODEL_NAMES])
        avg, cd = nemenyi(ft)
        fried_rows.append({"smell": smell, "blocks": len(ft), "k": len(MODEL_NAMES), "friedman_chi2": chi2, "p": p,
                           "nemenyi_CD": cd, **{f"avg_rank_{m}": avg[m] for m in MODEL_NAMES}})
        for a, b in itertools.combinations(MODEL_NAMES, 2):
            pair_rows.append({"smell": smell, "model_a": a, "model_b": b, "avg_rank_a": avg[a], "avg_rank_b": avg[b],
                              "rank_diff": abs(avg[a] - avg[b]), "CD": cd, "differ_at_alpha05": abs(avg[a] - avg[b]) > cd})
        cd_diagram(axes[ai], avg, cd, f"{SMELL_NAME[smell]}: mean rank of fold MCC (25 folds)")
    fig.tight_layout()
    savefig(fig, "model_cd_diagram")

    BT = pd.DataFrame(base_rows)
    BT["analysis"] = "primary"
    BT.to_csv(os.path.join(TAB, "baselines.csv"), index=False)
    MT = pd.DataFrame(model_rows)
    MT["analysis"] = "primary"
    best = {}
    for smell in STEP3_SMELLS:
        x = MT[MT.smell == smell].set_index("model")
        best[smell] = best_model({m: x.loc[m].to_dict() for m in MODEL_NAMES})
        trees = x.loc[TREE_MODELS].MCC
        best[f"{smell}_tree"] = trees.idxmax()
    MT["best_model"] = [m == best[s] for s, m in zip(MT.smell, MT.model)]
    MT["best_tree_model"] = [m == best[f"{s}_tree"] for s, m in zip(MT.smell, MT.model)]
    MT.to_csv(os.path.join(TAB, "model_comparison.csv"), index=False)
    FT = pd.DataFrame(fried_rows)
    PT = pd.DataFrame(pair_rows)
    FT.to_csv(os.path.join(TAB, "model_friedman.csv"), index=False)
    PT.to_csv(os.path.join(TAB, "model_nemenyi_pairs.csv"), index=False)
    pd.DataFrame(fold_rows).to_csv(os.path.join(TAB, "model_fold_mcc.csv"), index=False)
    save(best, "step3_best")

    def tab(df, key):
        t = df.copy()
        for k in METRICS:
            t[k.replace("_", "-") + " mean ± SD [95% CI]"] = [metric_cell(r, k) for r in t.to_dict("records")]
        cols = ["smell", key, "n"] + [k.replace("_", "-") + " mean ± SD [95% CI]" for k in METRICS]
        return t[cols]
    A = tab(BT, "baseline")
    Bm = tab(MT, "model")
    Bm["best"] = ["best (MCC)" if b else ("best tree" if bt else "") for b, bt in zip(MT.best_model, MT.best_tree_model)]
    F = FT.copy()
    F["friedman_chi2"] = F.friedman_chi2.round(3)
    F["p"] = [fmt_p(v) for v in F.p]
    F["nemenyi_CD"] = F.nemenyi_CD.round(3)
    for m in MODEL_NAMES:
        F[f"avg_rank_{m}"] = F[f"avg_rank_{m}"].round(2)
    sig = PT[PT.differ_at_alpha05]
    sig_txt = ("; ".join(f"{r.smell}: {r.model_a} vs {r.model_b} (|Δrank| {r.rank_diff:.2f} > CD {r.CD:.2f})"
                         for r in sig.itertuples()) or "none")
    rat = "\n".join(f"- **{m}**: {RATIONALE[m]}." for m in MODEL_NAMES)
    grids = "\n".join(f"  - {m}: `{GRIDS[m]}`" for m in MODEL_NAMES)
    txt_a = f"""**Analysis type: primary.** These baselines are reported alongside every model in sections B–J.
- Splits: the same 25 project-grouped splits as section B (5 repeats × 5 folds; projects shuffled with seed 20261021 + r and assigned round-robin).
- Majority class: the training fold's majority label is predicted for everyone. With a constant score, ROC-AUC = 0.5, PR-AUC = prevalence and MCC = 0.
- DesigniteJava rule: smelly if metric ≥ default (cc ≥ 8, pc ≥ 5). The score is the metric itself.
- Youden rule: smelly if metric ≥ c, with c chosen on the training fold only. The per-fold cut-offs are in `tables/baselines.csv`.
- Metrics: mean ± SD over the 5 repeats of pooled out-of-fold metrics. The CI is a bootstrap over entities (B = {B}) of the repeat-mean.

{md_table(A)}

Table: `tables/baselines.csv`.
"""
    txt_b = f"""**Analysis type: primary.**

**Algorithms and rationale**
{rat}

**Protocol** (plan.md §4.4)
- Unanimous entities of the primary set with complete features (CM {len(unanimous(dacos_entities('CM')))}, LPL {len(unanimous(dacos_entities('LPL')))}).
- Full feature set: {', '.join(full_features('CM')).replace('cc', 'cc|pc')}.
- Outer CV: 5 × 5 grouped CV by project.
- Inner tuning: `GridSearchCV(GroupKFold(3) by project, scoring = MCC)` on the training fold only.
- Class imbalance: inverse-frequency class weights only (`class_weight='balanced'`; XGB `scale_pos_weight`; GB balanced sample weights).
  - No SMOTE or other synthetic oversampling: it would fabricate borderline neighbours, which is exactly the region this study examines.
- Fixed grids:
{grids}
- RF uses 300 trees and XGB `n_jobs=1`. Every model uses `random_state = 20261021 + repeat`.
- Best model = highest mean MCC.

**Results**

{md_table(Bm)}

**Friedman test over 25 folds (fold-level MCC) and Nemenyi average ranks** (rank 1 = best). The Nemenyi CD uses q₀.₀₅ = 2.728 (k = 5).

{md_table(F)}

Pairs whose average ranks differ by more than the CD: {sig_txt}.
- All pairwise rank differences are in `tables/model_nemenyi_pairs.csv`.
- Caveat: the 25 folds come from 5 repeats of the same data, so they are not independent blocks. The test is therefore anti-conservative.

Tables: `tables/model_comparison.csv`, `tables/model_friedman.csv`, `tables/model_nemenyi_pairs.csv`, `tables/model_fold_mcc.csv`. Figure: `figures/model_cd_diagram.pdf` (.png). Runtime {time.time() - t0:.0f}s.

**Summary.** {"; ".join(f"{s}: best model {best[s]} (MCC {MT[(MT.smell == s) & (MT.model == best[s])].MCC.iloc[0]:.3f}), Friedman p = {fmt_p(FT[FT.smell == s].p.iloc[0])}" for s in STEP3_SMELLS)}.
"""
    write_frag("step3_A", txt_a)
    write_frag("step3_B", txt_b)
    print(txt_a)
    print(txt_b)


if __name__ == "__main__":
    main()
