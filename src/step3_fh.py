"""Step 3 F (interpretability, calibration) and H (learning curve), plan.md §4.5. CM and LPL; primary analysis."""
import os
import sys
import time

import numpy as np
import pandas as pd
import shap
from joblib import Parallel, delayed
from scipy.stats import spearmanr
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GridSearchCV, GroupKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402

FRACS = [0.10, 0.25, 0.50, 0.75, 1.00]


def refit_all(m, D, feats):
    y = D.target.values.astype(int)
    gs = GridSearchCV(make_model(m, SEED, y), GRIDS[m], scoring=MCC_SCORER, cv=GroupKFold(5), n_jobs=N_JOBS, refit=False)
    gs.fit(D[feats].values, y, groups=D.project.values, **fit_kwargs(m, y))
    return fit(m, gs.best_params_, D[feats].values, y, SEED), gs.best_params_


def perm_job(m, D, feats, tp, params):
    te = D.project.isin(tp).values
    y = D.target.values.astype(int)
    model = fit(m, params, D[~te][feats].values, y[~te], SEED)
    pi = permutation_importance(model, D[te][feats].values, y[te], scoring=MCC_SCORER, n_repeats=10, random_state=SEED)
    return pi.importances_mean


def lc_job(m, D, feats, tp, params, frac, s):
    te = D.project.isin(tp).values
    tr_idx = np.where(~te)[0]
    y = D.target.values.astype(int)
    r_ = np.random.default_rng(SEED + s)
    if frac < 1:
        keep = []
        for c in (0, 1):
            ci = tr_idx[y[tr_idx] == c]
            keep.append(r_.choice(ci, max(1, int(round(frac * len(ci)))), replace=False))
        tr_idx = np.sort(np.concatenate(keep))
    model = fit(m, params, D.iloc[tr_idx][feats].values, y[tr_idx], SEED + s)
    sc, pr = score(model, m, D[te][feats].values)
    return frac, s, np.where(te)[0], sc, pr, len(tr_idx)


def main():
    t0 = time.time()
    best = load("step3_best")
    plt = plot_style()
    rank_rows, calib_rows, lc_rows, plateau_rows, imp_rows = [], [], [], [], []
    rel = {}
    for smell in STEP3_SMELLS:
        cache = load(f"step3_B_{smell}")
        splits, resB = cache["splits"], cache["res"]
        D = unanimous(dacos_entities(smell))
        feats = full_features(smell)
        tm = best[f"{smell}_tree"]
        # ---------------- F: SHAP on the best tree model refitted on all data
        model, params = refit_all(tm, D, feats)
        ex = shap.TreeExplainer(model)
        sv = ex.shap_values(D[feats].values)
        sv = sv[1] if isinstance(sv, list) else sv
        mean_abs = np.abs(sv).mean(axis=0)
        # permutation importance on repeat-0 held-out folds (fold parameters from section B)
        r0 = [(r, k, tp) for r, k, tp in splits if r == 0]
        pis = Parallel(n_jobs=N_JOBS)(delayed(perm_job)(tm, D, feats, tp, resB[tm]["params"][(r, k)]) for r, k, tp in r0)
        pi_mean = np.mean(pis, axis=0)
        rho, p_rho = spearmanr(mean_abs, pi_mean)
        for f, a, b in zip(feats, mean_abs, pi_mean):
            imp_rows.append({"smell": smell, "model": tm, "feature": f, "mean_abs_SHAP": a, "permutation_importance_MCC": b,
                             "rank_SHAP": int((-mean_abs).argsort().argsort()[feats.index(f)] + 1),
                             "rank_permutation": int((-pi_mean).argsort().argsort()[feats.index(f)] + 1)})
        rank_rows.append({"smell": smell, "model": tm, "refit_params": str(params), "spearman_rho": rho, "p": p_rho,
                          "n_features": len(feats)})
        # SHAP summary figure: bar + beeswarm-style strip
        order = np.argsort(mean_abs)
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.4), gridspec_kw={"width_ratios": [1, 1.6]})
        a1.barh(range(len(feats)), mean_abs[order], color=COL["blue"], height=0.6)
        a1.set_yticks(range(len(feats)))
        a1.set_yticklabels([feats[i] for i in order])
        a1.set_xlabel("mean |SHAP| (log-odds)")
        a1.set_title(f"{SMELL_NAME[smell]}: {tm} global importance", loc="left")
        a1.grid(axis="y", visible=False)
        jr = np.random.default_rng(SEED)
        for row, i in enumerate(order):
            v = D[feats[i]].values.astype(float)
            q = pd.Series(v).rank(pct=True).values
            a2.scatter(sv[:, i], row + jr.uniform(-0.28, 0.28, len(v)), c=q, cmap="Blues", vmin=-0.2, vmax=1, s=2.5,
                       lw=0, rasterized=True)
        a2.axvline(0, color=COL["ink2"], lw=0.6)
        a2.set_yticks(range(len(feats)))
        a2.set_yticklabels([feats[i] for i in order])
        a2.set_xlabel("SHAP value (→ smelly)")
        a2.set_title("per-entity SHAP (colour = feature percentile, dark = high)", loc="left")
        a2.grid(axis="y", visible=False)
        fig.tight_layout()
        savefig(fig, f"shap_summary_{smell}")
        # dependence plot of primary metric
        rq2 = pd.read_csv(os.path.join(TAB, "rq2_threshold_validity.csv")).set_index("smell")
        i = feats.index(PRIMARY[smell])
        x = D[PRIMARY[smell]].values.astype(float)
        fig, ax = plt.subplots(figsize=(3.4, 2.3))
        ax.scatter(x + jr.uniform(-0.15, 0.15, len(x)), sv[:, i], s=3, color=COL["blue"], alpha=0.5, lw=0, rasterized=True)
        ax.axvline(DESIGNITE[smell], color=COL["aqua"], lw=1.2, ls="--", label=f"DesigniteJava default ({PRIMARY[smell]} ≥ {DESIGNITE[smell]})")
        ax.axvline(rq2.loc[smell, "youden_cut"], color=COL["orange"], lw=1.2, ls=":",
                   label=f"RQ2 Youden ({PRIMARY[smell]} ≥ {rq2.loc[smell, 'youden_cut']:g})")
        ax.axhline(0, color=COL["ink2"], lw=0.6)
        ax.set_xlabel(PRIMARY[smell])
        ax.set_ylabel(f"SHAP of {PRIMARY[smell]} (log-odds)")
        ax.set_title(f"{SMELL_NAME[smell]}: {tm} dependence", loc="left")
        ax.legend(loc="best", fontsize=5.5)
        fig.tight_layout()
        savefig(fig, f"shap_dependence_{smell}")
        # calibration (repeat-0 OOF), best model and LR
        for m in dict.fromkeys([best[smell], "LR"]):
            y = resB[m]["y"]
            if m == "SVM":
                raise RuntimeError("best model is SVM: refit with probability=True required (plan §4.5 F)")
            pr = resB[m]["S"][0]
            brier = float(np.mean((pr - y) ** 2))
            bins = np.linspace(0, 1, 11)
            idx = np.clip(np.digitize(pr, bins) - 1, 0, 9)
            curve = [(float(pr[idx == b].mean()), float(y[idx == b].mean()), int((idx == b).sum())) for b in range(10) if (idx == b).any()]
            rel[(smell, m)] = curve
            calib_rows.append({"smell": smell, "model": m, "n": len(y), "brier": brier,
                               "brier_reference_constant_prevalence": float(y.mean() * (1 - y.mean())),
                               "mean_predicted": float(pr.mean()), "observed_prevalence": float(y.mean()),
                               "bins": "; ".join(f"[{c[0]:.2f}→{c[1]:.2f}, n={c[2]}]" for c in curve)})
        # ---------------- H: learning curve (best model, repeat-0 folds, fold params)
        bm = best[smell]
        jobs = Parallel(n_jobs=N_JOBS)(delayed(lc_job)(bm, D, feats, tp, resB[bm]["params"][(r, k)], f, s)
                                       for r, k, tp in r0 for f in FRACS for s in range(5))
        y = D.target.values.astype(int)
        res_by_frac = {}
        for f in FRACS:
            S = np.full((5, len(D)), np.nan)
            P = np.zeros((5, len(D)), bool)
            ntr = []
            for ff, s, idx, sc, pr, n in jobs:
                if ff == f:
                    S[s, idx], P[s, idx] = sc, pr
                    ntr.append(n)
            res_by_frac[f] = {"S": S, "P": P, "y": y, "entity": D.entity.values}
            vals = [macro_f1(y, P[s]) for s in range(5)]
            lc_rows.append({"smell": smell, "model": bm, "fraction": f, "mean_train_n": float(np.mean(ntr)),
                            "macro_F1_mean": float(np.mean(vals)), "macro_F1_sd": float(np.std(vals, ddof=1)),
                            "MCC_mean": float(np.mean([mcc(y, P[s]) for s in range(5)]))})
        dlt = paired_delta(res_by_frac[1.0], res_by_frac[0.75], metrics=("macro_F1", "MCC"))
        plateau = dlt["macro_F1"] < 0.01 and dlt["macro_F1_lo"] <= 0 <= dlt["macro_F1_hi"]
        plateau_rows.append({"smell": smell, "model": bm, "gain_75_to_100_macro_F1": dlt["macro_F1"],
                             "lo": dlt["macro_F1_lo"], "hi": dlt["macro_F1_hi"], "plateaued_by_rule": plateau})
        print(smell, f"{time.time() - t0:.0f}s", flush=True)

    IM = pd.DataFrame(imp_rows)
    RK = pd.DataFrame(rank_rows)
    CA = pd.DataFrame(calib_rows)
    LC = pd.DataFrame(lc_rows)
    PL = pd.DataFrame(plateau_rows)
    IM.to_csv(os.path.join(TAB, "shap_permutation_importance.csv"), index=False)
    RK.to_csv(os.path.join(TAB, "shap_rank_correlation.csv"), index=False)
    CA.to_csv(os.path.join(TAB, "calibration.csv"), index=False)
    LC.to_csv(os.path.join(TAB, "learning_curve.csv"), index=False)
    PL.to_csv(os.path.join(TAB, "learning_curve_plateau.csv"), index=False)

    for smell in STEP3_SMELLS:
        fig, ax = plt.subplots(figsize=(3.0, 2.6))
        ax.plot([0, 1], [0, 1], color=COL["grid"], ls="--", lw=0.8)
        for (s, m), c in zip([k for k in rel if k[0] == smell], [COL["orange"], COL["blue"]]):
            cv = rel[(s, m)]
            ax.plot([a for a, _, _ in cv], [b for _, b, _ in cv], marker="o", ms=3.5, color=c, label=m)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.set_xlabel("mean predicted P(smelly)")
        ax.set_ylabel("observed share smelly")
        ax.set_title(f"{SMELL_NAME[smell]}: reliability (repeat 0)", loc="left")
        ax.legend(loc="upper left", fontsize=6)
        fig.tight_layout()
        savefig(fig, f"reliability_{smell}")
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    for smell, c in zip(STEP3_SMELLS, [COL["blue"], COL["orange"]]):
        x = LC[LC.smell == smell]
        ax.errorbar(x.mean_train_n, x.macro_F1_mean, yerr=x.macro_F1_sd, color=c, marker="o", ms=3.5, capsize=0,
                    label=f"{smell} ({x.model.iloc[0]})")
    ax.set_xlabel("training entities per fold (mean)")
    ax.set_ylabel("macro-F1 (mean ± SD over 5 seeds)")
    ax.set_title("Learning curve (repeat-0 folds)", loc="left")
    ax.legend(loc="lower right", fontsize=6)
    fig.tight_layout()
    savefig(fig, "learning_curve")

    im = IM.copy()
    for c in ("mean_abs_SHAP", "permutation_importance_MCC"):
        im[c] = im[c].round(4)
    rk = RK.copy()
    rk["spearman_rho"] = rk.spearman_rho.round(3)
    rk["p"] = [fmt_p(v) for v in rk.p]
    ca = CA.copy()
    for c in ("brier", "brier_reference_constant_prevalence", "mean_predicted", "observed_prevalence"):
        ca[c] = ca[c].round(4)
    lc = LC.copy()
    for c in lc.columns:
        if lc[c].dtype.kind == "f":
            lc[c] = lc[c].round(3)
    pl = PL.copy()
    pl["gain 75%→100% [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(pl.gain_75_to_100_macro_F1, pl.lo, pl.hi)]
    pl = pl[["smell", "model", "gain 75%→100% [95% CI]", "plateaued_by_rule"]]
    txt_f = f"""**Analysis type: primary (interpretability, calibration).**

**Method.**
- SHAP: `shap` 0.46.0 `TreeExplainer` on the best tree model ({', '.join(f"{s}: {best[s + '_tree']}" for s in STEP3_SMELLS)}).
  - The model is refitted on all unanimous entities, with hyperparameters from `GridSearchCV(GroupKFold(5) by project, MCC)` on all data. Parameters are in the table below.
  - SHAP values are in log-odds of "smelly".
- Permutation importance: on the held-out folds of repeat 0, using each fold's section-B parameters; scoring MCC, 10 permutations, averaged over the 5 folds.
- Spearman ρ compares the two importance vectors.
- Calibration: pooled repeat-0 out-of-fold probabilities of the best model and LR (CM's best model is LR), as a Brier score and a 10-bin reliability diagram.
  - The reference Brier score is that of a constant prediction equal to the observed prevalence.
  - Class weighting shifts predicted probabilities towards 0.5 by design; the calibration figures reflect the weighted models as evaluated.

**Importance rankings**

{md_table(im)}

{md_table(rk)}

**Calibration**

{md_table(ca)}

Tables: `tables/shap_permutation_importance.csv`, `tables/shap_rank_correlation.csv`, `tables/calibration.csv`.

Figures: `figures/shap_summary_<smell>.pdf`, `figures/shap_dependence_<smell>.pdf` (DesigniteJava default and RQ2 Youden cut-off marked), `figures/reliability_<smell>.pdf` (.png).
"""
    txt_h = f"""**Analysis type: primary.**

**Method.**
- Best model with each fold's section-B parameters, on the repeat-0 folds.
- Each training fold is subsampled per class (stratified) to 10/25/50/75/100%, with 5 seeds (seed 20261021 + s, also used as the model seed).
- Macro-F1 is computed on pooled out-of-fold predictions per seed.
- Plateau rule (fixed in plan.md): plateaued if the macro-F1 gain from 75% to 100% is < 0.01 and its paired bootstrap CI includes 0.

{md_table(lc)}

{md_table(pl)}

Tables: `tables/learning_curve.csv`, `tables/learning_curve_plateau.csv`. Figure: `figures/learning_curve.pdf` (.png). Runtime F+H {time.time() - t0:.0f}s.

**Summary.** {"; ".join(f"{r.smell} ({r.model}): gain 75%→100% = {fmt_ci(r.gain_75_to_100_macro_F1, r.lo, r.hi)}, plateaued by rule: {'yes' if r.plateaued_by_rule else 'no'}; macro-F1 across all fractions ranges {LC[LC.smell == r.smell].macro_F1_mean.min():.3f}–{LC[LC.smell == r.smell].macro_F1_mean.max():.3f}" for r in PL.itertuples())}.
"""
    write_frag("step3_F", txt_f)
    write_frag("step3_H", txt_h)
    print(txt_f)
    print(txt_h)


if __name__ == "__main__":
    main()
