"""Step 3 D: generalisation (plan.md §4.5 D). LOPO per-project scores and cross-smell transfer. CM and LPL."""
import os
import sys
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.model_selection import GridSearchCV, GroupKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402

METHOD_FEATS = ["cc", "pc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio", "mean_identifier_length"]
MIN_ENTITIES = 20


def per_project(df, label):
    """df: entity, project, target, score, pred."""
    rows = []
    for p, g in df.groupby("project"):
        y, s, pr = g.target.values.astype(int), g.score.values, g.pred.values.astype(bool)
        single = y.min() == y.max()
        rows.append({"source": label, "project": p, "n": len(g), "n_smelly": int(y.sum()), "single_class": single,
                     "flag": ("single class" if single else "") + ("; " if single and len(g) < MIN_ENTITIES else "") +
                             (f"< {MIN_ENTITIES} entities" if len(g) < MIN_ENTITIES else ""),
                     "macro_F1": macro_f1(y, pr), "MCC": mcc(y, pr) if not single else np.nan,
                     "ROC_AUC": roc_auc(y, s) if not single else np.nan})
    return rows


def dist(rows):
    d = pd.DataFrame(rows)
    ok = d[(d.flag == "")]
    out = {}
    for m in ("macro_F1", "MCC"):
        v = ok[m].dropna()
        out[f"{m}_median"] = float(v.median()) if len(v) else np.nan
        out[f"{m}_q1"] = float(v.quantile(.25)) if len(v) else np.nan
        out[f"{m}_q3"] = float(v.quantile(.75)) if len(v) else np.nan
        if len(v):
            w = ok.loc[v.idxmin()]
            out[f"{m}_worst"] = f"{w.project} ({w[m]:.3f})"
    out["projects_in_distribution"] = len(ok)
    out["projects_flagged"] = "; ".join(f"{r.project} [{r.flag}]" for r in d[d.flag != ""].itertuples()) or "none"
    return out


def main():
    t0 = time.time()
    best = load("step3_best")
    proj_rows, dist_rows, xs_rows = [], [], []
    tier1 = pd.read_csv(os.path.join(TAB, "rq4_predictions.csv.gz"))
    tier1 = tier1[tier1.setting == "DACOS leave-one-project-out"]
    for smell in STEP3_SMELLS:
        D = unanimous(dacos_entities(smell))
        feats = full_features(smell)
        projects = sorted(D.project.unique())
        models = [best[smell]] + ([] if best[smell] == "LR" else ["LR"])
        for m in models:
            jobs = Parallel(n_jobs=N_JOBS)(delayed(oof_job)(m, D, frozenset([p]), 0, k, feats)
                                           for k, p in enumerate(projects))
            sc = np.full(len(D), np.nan)
            pr = np.zeros(len(D), bool)
            for _, _, idx, s, p, _ in jobs:
                sc[idx], pr[idx] = s, p
            df = pd.DataFrame({"entity": D.entity, "project": D.project, "target": D.target, "score": sc, "pred": pr})
            label = f"Step 3 LOPO {m} (nested tuning, full features)"
            rows = per_project(df, label)
            proj_rows += [{"smell": smell, **r} for r in rows]
            y = D.target.values.astype(int)
            dist_rows.append({"smell": smell, "source": label, "pooled_macro_F1": macro_f1(y, pr), "pooled_MCC": mcc(y, pr),
                              **dist(rows)})
        for m in ("LR", "RF"):
            t = tier1[(tier1.smell == smell) & (tier1.model == m)]
            df = pd.DataFrame({"entity": t.entity, "project": t.project, "target": t.target, "score": t.p_smelly,
                               "pred": t.p_smelly >= 0.5})
            label = f"Tier 1 LOPO {m} (default hyperparameters, Tier 1 features)"
            rows = per_project(df, label)
            proj_rows += [{"smell": smell, **r} for r in rows]
            dist_rows.append({"smell": smell, "source": label, "pooled_macro_F1": macro_f1(df.target.values.astype(int), df.pred.values),
                              "pooled_MCC": mcc(df.target.values.astype(int), df.pred.values), **dist(rows)})
        print(smell, "LOPO", f"{time.time() - t0:.0f}s", flush=True)

    # cross-smell transfer
    data = {s: unanimous(dacos_entities(s)).dropna(subset=METHOD_FEATS) for s in STEP3_SMELLS}
    for src, tgt in (("CM", "LPL"), ("LPL", "CM")):
        S, T = data[src], data[tgt]
        shared = set(S.entity) & set(T.entity)
        T = T[~T.entity.isin(shared)].reset_index(drop=True)
        m = best[src]
        ys = S.target.values.astype(int)
        gs = GridSearchCV(make_model(m, SEED, ys), GRIDS[m], scoring=MCC_SCORER, cv=GroupKFold(5), n_jobs=N_JOBS, refit=False)
        gs.fit(S[METHOD_FEATS].values, ys, groups=S.project.values, **fit_kwargs(m, ys))
        model = fit(m, gs.best_params_, S[METHOD_FEATS].values, ys, SEED)
        s, p = score(model, m, T[METHOD_FEATS].values)
        yt = T.target.values.astype(int)
        res = {"S": np.tile(s, (N_REPEATS, 1)), "P": np.tile(p, (N_REPEATS, 1)), "y": yt, "entity": T.entity.values}
        point = all_metrics(yt, s, p)
        bs = boot_repeat_mean({"S": s[None, :], "P": p[None, :], "y": yt}, keys=list(METRICS)) if False else None
        idxs = boot_indices(len(yt))
        ci = {}
        for k, f in METRICS.items():
            ci[k] = boot_ci([f(yt[i], s[i], p[i]) for i in idxs])
        xs_rows.append({"source_smell": src, "target_smell": tgt, "model": m, "params": str(gs.best_params_),
                        "features": ", ".join(METHOD_FEATS), "train_n": len(S), "test_n": len(T),
                        "shared_entities_removed_from_test": len(shared),
                        **{k: point[k] for k in METRICS}, **{f"{k}_lo": ci[k][0] for k in METRICS},
                        **{f"{k}_hi": ci[k][1] for k in METRICS}})
    XS = pd.DataFrame(xs_rows)
    XS["analysis"] = "primary (generalisation)"
    XS.to_csv(os.path.join(TAB, "cross_smell.csv"), index=False)
    PP = pd.DataFrame(proj_rows)
    PP.to_csv(os.path.join(TAB, "lopo_per_project.csv"), index=False)
    DS = pd.DataFrame(dist_rows)
    DS.to_csv(os.path.join(TAB, "lopo_distribution.csv"), index=False)

    plt = plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3), sharey=True)
    for ax, smell in zip(axes, STEP3_SMELLS):
        srcs = list(DS[DS.smell == smell].source)
        for i, src in enumerate(srcs):
            x = PP[(PP.smell == smell) & (PP.source == src)]
            ok = x[x.flag == ""]
            bad = x[x.flag != ""]
            jit = np.random.default_rng(SEED).uniform(-0.12, 0.12, len(ok))
            ax.scatter(ok.MCC, i + jit, s=12, color=COL["blue"], zorder=3)
            ax.scatter(bad.MCC.fillna(0), i + np.zeros(len(bad)) + 0.25, s=12, facecolor="none", edgecolor=COL["ink2"],
                       zorder=3)
            if len(ok):
                ax.plot([ok.MCC.quantile(.25), ok.MCC.quantile(.75)], [i, i], color=COL["orange"], lw=3, alpha=0.6)
                ax.scatter(ok.MCC.median(), i, marker="|", s=120, color=COL["orange"], zorder=4)
        ax.set_yticks(range(len(srcs)))
        ax.set_yticklabels([s.split(" (")[0] for s in srcs], fontsize=6)
        ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
        ax.set_xlabel("per-project MCC (held-out project)")
        ax.set_title(SMELL_NAME[smell], loc="left")
        ax.grid(axis="y", visible=False)
    axes[0].scatter([], [], s=12, color=COL["blue"], label="project")
    axes[0].scatter([], [], s=12, facecolor="none", edgecolor=COL["ink2"], label="flagged (MCC undefined → drawn at 0)")
    axes[0].plot([], [], color=COL["orange"], lw=3, alpha=0.6, label="median and IQR")
    axes[0].legend(loc="lower left", fontsize=5.5)
    fig.tight_layout()
    savefig(fig, "lopo_distribution")

    ds = DS.copy()
    for c in ds.columns:
        if ds[c].dtype.kind == "f":
            ds[c] = ds[c].round(3)
    pp = PP.copy()
    for c in ("macro_F1", "MCC", "ROC_AUC"):
        pp[c] = pp[c].round(3)
    xs = XS.copy()
    for k in METRICS:
        xs[f"{k} [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(xs[k], xs[f"{k}_lo"], xs[f"{k}_hi"])]
    xs = xs[["source_smell", "target_smell", "model", "params", "train_n", "test_n", "shared_entities_removed_from_test"] +
            [f"{k} [95% CI]" for k in METRICS]]
    txt = f"""**Analysis type: primary (generalisation).**

**Method.**
- Leave-one-project-out (LOPO) with the best model and LR:
  - nested tuning with inner `GroupKFold(3)` by project on the 9 training projects;
  - full Step 3 features, seed 20261021.
- Per-project scores are also computed from the Tier 1 LOPO predictions (LR and RF with default hyperparameters and the Tier 1 feature set).
- Projects with fewer than {MIN_ENTITIES} test entities, or a single class, are flagged and excluded from the median, IQR and worst project. MCC and ROC-AUC are undefined for single-class projects. Pooled scores use every project.
- Cross-smell transfer:
  - The source smell's best model is tuned with `GridSearchCV(GroupKFold(5) by project)` on the source unanimous entities, then fitted on all of them.
  - It is tested on the target smell's unanimous entities, minus the entities annotated for both smells.
  - Method-level features only: {', '.join(METHOD_FEATS)}.
  - 95% CIs are a bootstrap over target entities (B = {B}).

**Per-project score distribution**

{md_table(ds)}

**Per-project scores**

{md_table(pp)}

**Cross-smell transfer**

{md_table(xs)}

Tables: `tables/lopo_per_project.csv`, `tables/lopo_distribution.csv`, `tables/cross_smell.csv`. Figure: `figures/lopo_distribution.pdf` (.png). Runtime {time.time() - t0:.0f}s.

**Summary.** {"; ".join(f"{r.source_smell}→{r.target_smell} ({r.model}): MCC {fmt_ci(r.MCC, r.MCC_lo, r.MCC_hi)}" for r in XS.itertuples())}.
"""
    write_frag("step3_D", txt)
    print(txt)


if __name__ == "__main__":
    main()
