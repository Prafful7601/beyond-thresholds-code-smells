"""Prompt 3 §1 / plan.md §5.1: LPL Step 3 without the pc = 3 block (robustness R5).

Identical protocol, grids, seeds and section code as the primary Step 3 run; only the entity set differs.
Writes *_LPL_R5 tables, side-by-side primary vs R5 tables, and figures.
"""
import itertools
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import shap
from joblib import Parallel, delayed
from scipy.stats import friedmanchisquare
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402
import rq3  # noqa: E402
from step3_ab import BASELINES, baseline_res, cd_diagram, nemenyi  # noqa: E402
from step3_c import c1_sets  # noqa: E402
from step3_d import dist, per_project  # noqa: E402
from step3_e import keys  # noqa: E402
from step3_fh import FRACS, lc_job, refit_all  # noqa: E402

SMELL, VAR = "LPL", "R5"


def run():
    t0 = time.time()
    plt = plot_style()
    D = unanimous(dacos_entities(SMELL, VAR))
    feats = full_features(SMELL)
    splits = project_splits(D.project)
    prim = load(f"step3_B_{SMELL}")
    assert [t for _, _, t in splits] == [t for _, _, t in prim["splits"]], "R5 split assignment differs from primary"
    out = {"n": len(D), "n_smelly": int(D.target.sum())}

    # ---------------- A + B
    res, base_rows, model_rows = {}, [], []
    for b in BASELINES:
        res[b] = baseline_res(b, D, SMELL, splits)
        base_rows.append({"baseline": b, **summarise(res[b])})
    for m in MODEL_NAMES:
        res[m] = run_protocol(m, D, feats, splits)
        model_rows.append({"model": m, **summarise(res[m])})
        print("R5 B", m, f"{time.time() - t0:.0f}s", flush=True)
    MT = pd.DataFrame(model_rows).set_index("model")
    best = best_model({m: MT.loc[m].to_dict() for m in MODEL_NAMES})
    best_tree = MT.loc[TREE_MODELS].MCC.idxmax()
    ft = pd.DataFrame({m: [res[m]["fold_mcc"][(r, k)] for r, k, _ in splits] for m in MODEL_NAMES})
    chi2, p = friedmanchisquare(*[ft[m].values for m in MODEL_NAMES])
    avg, cd = nemenyi(ft)
    pairs = [{"model_a": a, "model_b": b, "rank_diff": abs(avg[a] - avg[b]), "CD": cd, "differ": abs(avg[a] - avg[b]) > cd}
             for a, b in itertools.combinations(MODEL_NAMES, 2)]
    fig, ax = plt.subplots(figsize=(3.5, 1.5))
    cd_diagram(ax, avg, cd, "LPL R5: mean rank of fold MCC (25 folds)")
    fig.tight_layout()
    savefig(fig, "model_cd_diagram_LPL_R5")
    save({"res": res, "splits": splits, "entities": D.entity.values, "best": best, "best_tree": best_tree}, "step3_B_LPL_R5")
    out.update(best=best, best_tree=best_tree, friedman=(chi2, p, cd, avg.to_dict()), pairs=pairs,
               base=pd.DataFrame(base_rows), models=MT.reset_index())

    # ---------------- C1 (i), (v) and C3, best + LR, reused params
    X, _ = dacosx_entities(SMELL)
    abl = []
    for m in dict.fromkeys([best, "LR"]):
        pb = res[m]["params"]
        full = res[m]
        fs_np = [f for f in feats if f != PRIMARY[SMELL]]
        variants = {("C1", "(i) primary only"): run_protocol(m, D, c1_sets(SMELL)["(i) primary only"], splits, pb),
                    ("C1", "(v) all features"): full,
                    ("C3", "DACOS only (= v)"): full,
                    ("C3", "DACOSX only"): run_protocol(m, D, feats, splits, pb, train_override=lambda tp: X[~X.project.isin(tp)][feats + ["target", "project"]]),
                    ("C3", "DACOSX + DACOS"): run_protocol(m, D, feats, splits, pb, train_override=lambda tp: pd.concat(
                        [X[~X.project.isin(tp)][feats + ["target", "project"]], D[~D.project.isin(tp)][feats + ["target", "project"]]])),
                    ("C3", "DACOSX only, primary metric removed"): run_protocol(m, D, fs_np, splits, pb, train_override=lambda tp: X[~X.project.isin(tp)][fs_np + ["target", "project"]])}
        for (blk, name), r_ in variants.items():
            s = summarise(r_)
            d = paired_delta(r_, full) if r_ is not full else {}
            abl.append({"model": m, "block": blk, "variant": name, **s, "d_MCC": d.get("MCC", 0.0), "d_MCC_lo": d.get("MCC_lo", np.nan),
                        "d_MCC_hi": d.get("MCC_hi", np.nan), "d_macro_F1": d.get("macro_F1", 0.0),
                        "d_macro_F1_lo": d.get("macro_F1_lo", np.nan), "d_macro_F1_hi": d.get("macro_F1_hi", np.nan),
                        "is_reference": r_ is full})
        print("R5 C", m, f"{time.time() - t0:.0f}s", flush=True)
    out["ablation"] = pd.DataFrame(abl)

    # ---------------- RQ3 GEE (all features) + tree
    L = annotation_long()
    f3 = feature_cols(SMELL)
    A, E = rq3.prep(L, VAR, SMELL)
    Dg, Ez = rq3.design(A, E, f3)
    v = rq3.vif_table(Ez, f3)
    g = rq3.fit_gee(Dg, f3)
    gee = pd.DataFrame(rq3.gee_rows(g, f3, SMELL, "full"))
    gee["p_BH"] = bh(gee.p.values)
    gee["VIF"] = gee.feature.map(v)
    U = E[E.unanimous].dropna(subset=f3)
    tree = DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=SEED).fit(U[f3].values, U.target.values.astype(int))
    out["gee"], out["gee_n"] = gee, (len(Dg), Dg.entity.nunique(), float(g.cov_struct.dep_params))
    out["tree"] = (f"=== LPL R5: depth-3 DecisionTreeClassifier(class_weight='balanced', random_state={SEED}) on {len(U)} unanimous "
                   f"entities ({int(U.target.sum())} smelly / {int((1 - U.target).sum())} benign).\n"
                   + export_text(tree, feature_names=f3, show_weights=True, decimals=3))

    # ---------------- D LOPO (R5 best, nested)
    projects = sorted(D.project.unique())
    jobs = Parallel(n_jobs=N_JOBS)(delayed(oof_job)(best, D, frozenset([pp]), 0, k, feats) for k, pp in enumerate(projects))
    sc = np.full(len(D), np.nan)
    pr = np.zeros(len(D), bool)
    for _, _, idx, s_, p_, _ in jobs:
        sc[idx], pr[idx] = s_, p_
    df = pd.DataFrame({"entity": D.entity, "project": D.project, "target": D.target, "score": sc, "pred": pr})
    rows = per_project(df, f"Step 3 LOPO {best} R5")
    y = D.target.values.astype(int)
    out["lopo_rows"] = rows
    out["lopo"] = {"pooled_macro_F1": macro_f1(y, pr), "pooled_MCC": mcc(y, pr), **dist(rows)}
    print("R5 D", f"{time.time() - t0:.0f}s", flush=True)

    # ---------------- F SHAP (R5 best tree)
    model, params = refit_all(best_tree, D, feats)
    sv = shap.TreeExplainer(model).shap_values(D[feats].values)
    sv = sv[1] if isinstance(sv, list) else sv
    if sv.ndim == 3:  # shap >= 0.45 returns (n, features, classes) for sklearn forests
        sv = sv[:, :, 1]
    mean_abs = np.abs(sv).mean(axis=0)
    out["shap"] = pd.DataFrame({"feature": feats, "mean_abs_SHAP": mean_abs,
                                "rank": (-mean_abs).argsort().argsort() + 1}).assign(model=best_tree, params=str(params))
    order = np.argsort(mean_abs)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.4), gridspec_kw={"width_ratios": [1, 1.6]})
    a1.barh(range(len(feats)), mean_abs[order], color=COL["blue"], height=0.6)
    a1.set_yticks(range(len(feats)))
    a1.set_yticklabels([feats[i] for i in order])
    a1.set_xlabel("mean |SHAP| (log-odds)")
    a1.set_title(f"LPL R5: {best_tree} global importance", loc="left")
    a1.grid(axis="y", visible=False)
    jr = np.random.default_rng(SEED)
    for row, i in enumerate(order):
        q = pd.Series(D[feats[i]].values.astype(float)).rank(pct=True).values
        a2.scatter(sv[:, i], row + jr.uniform(-0.28, 0.28, len(q)), c=q, cmap="Blues", vmin=-0.2, vmax=1, s=2.5, lw=0, rasterized=True)
    a2.axvline(0, color=COL["ink2"], lw=0.6)
    a2.set_yticks(range(len(feats)))
    a2.set_yticklabels([feats[i] for i in order])
    a2.set_xlabel("SHAP value (→ smelly)")
    a2.set_title("per-entity SHAP (colour = feature percentile, dark = high)", loc="left")
    a2.grid(axis="y", visible=False)
    fig.tight_layout()
    savefig(fig, "shap_summary_LPL_R5")
    i = feats.index("pc")
    x = D.pc.values.astype(float)
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    ax.scatter(x + jr.uniform(-0.15, 0.15, len(x)), sv[:, i], s=3, color=COL["blue"], alpha=0.5, lw=0, rasterized=True)
    ax.axvline(DESIGNITE[SMELL], color=COL["aqua"], lw=1.2, ls="--", label="DesigniteJava default (pc ≥ 5)")
    ax.axhline(0, color=COL["ink2"], lw=0.6)
    ax.set_xlabel("pc")
    ax.set_ylabel("SHAP of pc (log-odds)")
    ax.set_title(f"LPL R5: {best_tree} dependence", loc="left")
    ax.legend(loc="best", fontsize=5.5)
    fig.tight_layout()
    savefig(fig, "shap_dependence_LPL_R5")

    # ---------------- H learning curve (R5 best)
    r0 = [(r, k, tp) for r, k, tp in splits if r == 0]
    jobs = Parallel(n_jobs=N_JOBS)(delayed(lc_job)(best, D, feats, tp, res[best]["params"][(r, k)], f, s)
                                   for r, k, tp in r0 for f in FRACS for s in range(5))
    lc, byf = [], {}
    for f in FRACS:
        S = np.full((5, len(D)), np.nan)
        P = np.zeros((5, len(D)), bool)
        ntr = []
        for ff, s, idx, sc_, pr_, n in jobs:
            if ff == f:
                S[s, idx], P[s, idx] = sc_, pr_
                ntr.append(n)
        byf[f] = {"S": S, "P": P, "y": y, "entity": D.entity.values}
        vals = [macro_f1(y, P[s]) for s in range(5)]
        lc.append({"fraction": f, "mean_train_n": float(np.mean(ntr)), "macro_F1_mean": float(np.mean(vals)),
                   "macro_F1_sd": float(np.std(vals, ddof=1)), "MCC_mean": float(np.mean([mcc(y, P[s]) for s in range(5)]))})
    dl = paired_delta(byf[1.0], byf[0.75], metrics=("macro_F1", "MCC"))
    out["lc"] = pd.DataFrame(lc)
    out["plateau"] = (dl["macro_F1"], dl["macro_F1_lo"], dl["macro_F1_hi"],
                      dl["macro_F1"] < 0.01 and dl["macro_F1_lo"] <= 0 <= dl["macro_F1_hi"])

    # ---------------- E near-duplicate label conflicts
    z = zipfile.ZipFile(ZIP)
    kk = [keys(z.read(pth.lstrip("/")).decode("utf-8", "replace")) for pth in D.path]
    D["near_key"] = [b for _, b in kk]
    D["exact_key"] = [a for a, _ in kk]
    dup = {}
    for kind in ("exact_key", "near_key"):
        gg = D.groupby(kind)
        sz = gg.size()
        multi = sz[sz >= 2]
        dup[kind] = (len(multi), int(multi.sum()), int((gg.target.nunique()[multi.index] > 1).sum()),
                     int((gg.project.nunique()[multi.index] > 1).sum()))
    out["dup"] = dup
    out["runtime"] = time.time() - t0
    return out


def cell(r, k):
    return f"{r[k]:.3f} [{r[k + '_lo']:.3f}, {r[k + '_hi']:.3f}]"


def main():
    o = run()
    save(o, "step3_R5_summary")
    # ---------------- side-by-side tables
    pB = pd.read_csv(os.path.join(TAB, "model_comparison.csv"))
    pB = pB[pB.smell == SMELL].set_index("model")
    pA = pd.read_csv(os.path.join(TAB, "baselines.csv"))
    pA = pA[pA.smell == SMELL].set_index("baseline")
    rB = o["models"].set_index("model")
    rA = o["base"].set_index("baseline")
    rows = []
    for name, P_, R_ in [(b, pA.loc[b], rA.loc[b]) for b in BASELINES] + [(m, pB.loc[m], rB.loc[m]) for m in MODEL_NAMES]:
        for k in ("macro_F1", "MCC", "ROC_AUC", "PR_AUC"):
            rows.append({"section": "A baselines" if name in BASELINES else "B models", "model/baseline": name, "metric": k,
                         "primary": cell(P_, k), "R5": cell(R_, k)})
    AB = pd.DataFrame(rows)
    pf = pd.read_csv(os.path.join(TAB, "model_friedman.csv")).set_index("smell").loc[SMELL]
    chi2, p, cd, avg = o["friedman"]
    FR = pd.DataFrame([{"statistic": "Friedman χ²", "primary": f"{pf.friedman_chi2:.3f}", "R5": f"{chi2:.3f}"},
                       {"statistic": "Friedman p", "primary": fmt_p(pf.p), "R5": fmt_p(p)},
                       {"statistic": "Nemenyi CD", "primary": f"{pf.nemenyi_CD:.3f}", "R5": f"{cd:.3f}"}] +
                      [{"statistic": f"mean rank {m}", "primary": f"{pf[f'avg_rank_{m}']:.2f}", "R5": f"{avg[m]:.2f}"} for m in MODEL_NAMES] +
                      [{"statistic": "best model (MCC rule)", "primary": pB.index[pB.best_model].tolist()[0], "R5": o["best"]},
                       {"statistic": "best tree model", "primary": pB.index[pB.best_tree_model].tolist()[0], "R5": o["best_tree"]}])
    pp = pd.read_csv(os.path.join(TAB, "model_nemenyi_pairs.csv"))
    pp = pp[(pp.smell == SMELL) & pp.differ_at_alpha05]
    r5p = [f"{q['model_a']} vs {q['model_b']}" for q in o["pairs"] if q["differ"]]
    # ablation
    pab = pd.read_csv(os.path.join(TAB, "ablation_LPL.csv"))
    rab = o["ablation"]
    keep = ["(i) primary only", "(v) all features", "DACOS only (= v)", "DACOSX only", "DACOSX + DACOS", "DACOSX only, primary metric removed"]
    rows = []
    for m in dict.fromkeys(list(pab.model.unique()) + list(rab.model.unique())):
        for v in keep:
            P_ = pab[(pab.model == m) & (pab.variant == v)]
            R_ = rab[(rab.model == m) & (rab.variant == v)]
            fmtd = lambda X_: ("reference" if X_.iloc[0].is_reference else  # noqa: E731
                               f"MCC {X_.iloc[0].MCC:.3f}; Δ MCC {fmt_ci(X_.iloc[0].d_MCC, X_.iloc[0].d_MCC_lo, X_.iloc[0].d_MCC_hi)}") if len(X_) else "n/a (not the best model of this run)"
            rows.append({"model": m, "variant": v, "primary": fmtd(P_), "R5": fmtd(R_)})
    AB2 = pd.DataFrame(rows)
    # RQ3
    pg = pd.read_csv(os.path.join(TAB, "rq3_odds_ratios.csv"))
    pg = pg[(pg.smell == SMELL) & (pg.model == "full")].set_index("feature")
    rg = o["gee"].set_index("feature")
    G = pd.DataFrame([{"feature": f, "primary OR per SD [95% CI]": fmt_ci(pg.loc[f].OR_per_SD, pg.loc[f].OR_lo, pg.loc[f].OR_hi),
                       "primary p (BH)": fmt_p(pg.loc[f].p_BH_within_smell_model),
                       "R5 OR per SD [95% CI]": fmt_ci(rg.loc[f].OR_per_SD, rg.loc[f].OR_lo, rg.loc[f].OR_hi),
                       "R5 p (BH)": fmt_p(rg.loc[f].p_BH), "R5 VIF": f"{rg.loc[f].VIF:.2f}"} for f in feature_cols(SMELL)])
    # LOPO
    pl = pd.read_csv(os.path.join(TAB, "lopo_distribution.csv"))
    pl = pl[(pl.smell == SMELL) & pl.source.str.startswith(f"Step 3 LOPO {pB.index[pB.best_model].tolist()[0]}")].iloc[0]
    rl = o["lopo"]
    LO = pd.DataFrame([{"statistic": k, "primary": (f"{pl[k]:.3f}" if isinstance(pl[k], float) else str(pl[k])),
                        "R5": (f"{rl[k]:.3f}" if isinstance(rl[k], float) else str(rl[k]))}
                       for k in ("pooled_macro_F1", "pooled_MCC", "MCC_median", "MCC_q1", "MCC_q3", "MCC_worst",
                                 "macro_F1_median", "projects_in_distribution", "projects_flagged")])
    # SHAP
    ps = pd.read_csv(os.path.join(TAB, "shap_permutation_importance.csv"))
    ps = ps[ps.smell == SMELL].set_index("feature")
    rs = o["shap"].set_index("feature")
    SH = pd.DataFrame([{"feature": f, f"primary mean |SHAP| ({ps.model.iloc[0]})": f"{ps.loc[f].mean_abs_SHAP:.4f}",
                        "primary rank": int(ps.loc[f].rank_SHAP), f"R5 mean |SHAP| ({o['best_tree']})": f"{rs.loc[f].mean_abs_SHAP:.4f}",
                        "R5 rank": int(rs.loc[f]["rank"])} for f in full_features(SMELL)])
    # learning curve
    plc = pd.read_csv(os.path.join(TAB, "learning_curve.csv"))
    plc = plc[plc.smell == SMELL].set_index("fraction")
    rlc = o["lc"].set_index("fraction")
    LC = pd.DataFrame([{"fraction": f, "primary macro-F1 (±SD)": f"{plc.loc[f].macro_F1_mean:.3f} ± {plc.loc[f].macro_F1_sd:.3f}",
                        "R5 macro-F1 (±SD)": f"{rlc.loc[f].macro_F1_mean:.3f} ± {rlc.loc[f].macro_F1_sd:.3f}"} for f in FRACS])
    ppl = pd.read_csv(os.path.join(TAB, "learning_curve_plateau.csv")).set_index("smell").loc[SMELL]
    g, lo, hi, plat = o["plateau"]
    LC.loc[len(LC)] = {"fraction": "gain 75%→100% [95% CI]; plateaued",
                       "primary macro-F1 (±SD)": f"{fmt_ci(ppl.gain_75_to_100_macro_F1, ppl.lo, ppl.hi)}; {bool(ppl.plateaued_by_rule)}",
                       "R5 macro-F1 (±SD)": f"{fmt_ci(g, lo, hi)}; {plat}"}
    # duplicates
    pk = pd.read_csv(os.path.join(TAB, "leakage_checks.csv"))
    pk = pk[(pk.smell == SMELL) & pk.check.str.contains("duplicate groups")].set_index("check")
    du_rows = []
    for kind in ("exact_key", "near_key"):
        label = kind.replace("_key", "")
        prow = pk.loc[label + " duplicate groups (size ≥ 2)"]
        n_g, n_e, n_conf, n_span = o["dup"][kind]
        du_rows.append({"duplicate type": label, "primary": f"{int(prow.value)} groups; {prow.detail}",
                        "R5": f"{n_g} groups; {n_e} entities; {n_span} groups span >1 project; {n_conf} groups have conflicting labels"})
    DU = pd.DataFrame(du_rows)
    for name, T in (("lpl_r5_AB", AB), ("lpl_r5_friedman", FR), ("lpl_r5_ablation", AB2), ("lpl_r5_rq3", G),
                    ("lpl_r5_lopo", LO), ("lpl_r5_shap", SH), ("lpl_r5_learning_curve", LC), ("lpl_r5_duplicates", DU)):
        T.to_csv(os.path.join(TAB, name + ".csv"), index=False)
    o["ablation"].assign(analysis="robustness R5").to_csv(os.path.join(TAB, "ablation_LPL_R5.csv"), index=False)
    o["models"].assign(analysis="robustness R5", best_model=lambda d: d.model == o["best"]).to_csv(os.path.join(TAB, "model_comparison_LPL_R5.csv"), index=False)
    o["base"].assign(analysis="robustness R5").to_csv(os.path.join(TAB, "baselines_LPL_R5.csv"), index=False)
    pd.DataFrame(o["lopo_rows"]).to_csv(os.path.join(TAB, "lopo_per_project_LPL_R5.csv"), index=False)
    o["gee"].to_csv(os.path.join(TAB, "rq3_odds_ratios_LPL_R5.csv"), index=False)
    open(os.path.join(TAB, "rq3_tree_rules_LPL_R5.txt"), "w").write(o["tree"])
    n_entities, n_gee_ent, wc = o["gee_n"]
    txt = f"""**Analysis type: robustness (R5 applied to Step 3).** LPL only. plan.md §5.1.

**Method.**
- The 137 pc = 3 entities with an empty `smells` field are removed from training and test. This leaves {o['n']} unanimous entities ({o['n_smelly']} smelly).
- Everything else is identical to the primary Step 3 run: the same code, grids, nested tuning and seeds. The 25 splits have the same project-to-fold assignment (asserted).
- In each table the primary column repeats the primary result; the R5 column is new.

**A and B: baselines and five-model comparison** (mean ± SD not shown; cells are repeat-mean [95% CI])

{md_table(AB)}

**B: Friedman/Nemenyi and best model**

{md_table(FR)}

Pairs with |Δ rank| > CD: primary {', '.join(f'{r.model_a} vs {r.model_b}' for r in pp.itertuples()) or 'none'}; R5 {', '.join(r5p) or 'none'}.
Figure: `figures/model_cd_diagram_LPL_R5.pdf`.

**C1 and C3** (hyperparameters reused from the respective B run; Δ is versus (v) with a paired bootstrap CI)

{md_table(AB2)}

**RQ3 GEE** (annotation level, all features; R5: {n_entities} annotations, {n_gee_ent} entities, working correlation {wc:.3f}). {"No R5 VIF exceeds 5." if (o['gee'].VIF <= 5).all() else "At least one R5 VIF exceeds 5."}

{md_table(G)}

```
{o['tree']}
```

**D: LOPO per-project distribution** (best model of each run: primary {pB.index[pB.best_model].tolist()[0]}, R5 {o['best']})

{md_table(LO)}

**F: SHAP** (best tree model of each run). Figures: `figures/shap_summary_LPL_R5.pdf`, `figures/shap_dependence_LPL_R5.pdf`.

{md_table(SH)}

**H: learning curve** (best model of each run)

{md_table(LC)}

**E: duplicate groups and label conflicts**

{md_table(DU)}

Tables: `tables/lpl_r5_*.csv` (side by side), `tables/model_comparison_LPL_R5.csv`, `tables/baselines_LPL_R5.csv`, `tables/ablation_LPL_R5.csv`, `tables/rq3_odds_ratios_LPL_R5.csv`, `tables/rq3_tree_rules_LPL_R5.txt`, `tables/lopo_per_project_LPL_R5.csv`. Runtime {o['runtime']:.0f}s.

**Summary.** R5 best model {o['best']}, MCC {cell(rB.loc[o['best']], 'MCC')}; primary best model {pB.index[pB.best_model].tolist()[0]}, MCC {cell(pB.loc[pB.index[pB.best_model].tolist()[0]], 'MCC')}.
"""
    write_frag("step3_R5", txt)
    print(txt)


if __name__ == "__main__":
    main()
