"""Human ceiling (plan.md §5.2; primary). CM, LPL and LPL-R5.

Designations are simulated exactly through sufficient statistics: with two annotations per entity, a random
prediction/target designation only matters for split entities. For a split entity, the target is "yes" with
probability 0.5, and the same draw fixes both the human prediction (the other annotation) and the model
comparison, so human and model scores are paired by construction.
"""
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402
from step3_e import keys  # noqa: E402

N_DESIG = 2000
POPS = [("CM", "primary", "step3_B_CM"), ("LPL", "primary", "step3_B_LPL"), ("LPL", "R5", "step3_B_LPL_R5")]


def m_from_counts(tp, tn, fp, fn):
    tp, tn, fp, fn = (np.asarray(v, float) for v in (tp, tn, fp, fn))
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc_ = np.where(den > 0, (tp * tn - fp * fn) / np.where(den > 0, den, 1), 0.0)
    f1p = np.where(2 * tp + fp + fn > 0, 2 * tp / np.maximum(2 * tp + fp + fn, 1e-12), 0.0)
    f1n = np.where(2 * tn + fp + fn > 0, 2 * tn / np.maximum(2 * tn + fp + fn, 1e-12), 0.0)
    acc = (tp + tn) / (tp + tn + fp + fn)
    return {"MCC": mcc_, "macro_F1": (f1p + f1n) / 2, "accuracy": acc}


def simulate(cat, r_, n_desig=N_DESIG):
    """cat: array (5 repeats, 6) counts for model pred m in {0,1} x votes in {both0, both1, split}.
    Column order: (m0,b0), (m0,b1), (m0,sp), (m1,b0), (m1,b1), (m1,sp). Returns dict of arrays over designations."""
    rep = np.arange(n_desig) % N_REPEATS
    c = cat[rep]
    k0 = r_.binomial(c[:, 2].astype(int), 0.5)   # model 0, split: target = 1
    k1 = r_.binomial(c[:, 5].astype(int), 0.5)   # model 1, split: target = 1
    s0, s1 = c[:, 2], c[:, 5]
    b0 = c[:, 0] + c[:, 3]
    b1 = c[:, 1] + c[:, 4]
    # human: the other annotation predicts; split entities give FN when target = 1, FP otherwise
    hum = m_from_counts(b1, b0, (s0 - k0) + (s1 - k1), k0 + k1)
    mod = m_from_counts(c[:, 4] + k1, c[:, 0] + (s0 - k0), c[:, 3] + (s1 - k1), c[:, 1] + k0)
    return hum, mod


def categories(votes, M):
    """votes: 0 both no, 1 both yes, 2 split; M: (5, n) bool model predictions."""
    out = np.zeros((N_REPEATS, 6))
    for r in range(N_REPEATS):
        for mi in (0, 1):
            for v in (0, 1, 2):
                out[r, mi * 3 + v] = np.sum((M[r] == bool(mi)) & (votes == v))
    return out


def neardup_ceiling(Eall, smell, r_):
    """Same-project near-duplicate pairs of different entities; one random annotation per entity, random roles."""
    z = zipfile.ZipFile(ZIP)
    E = Eall.copy()
    E["near_key"] = [keys(z.read(p.lstrip("/")).decode("utf-8", "replace"))[1] for p in E.path]
    E["p_yes"] = E.y / E.n
    groups = [g for _, g in E.groupby(["project", "near_key"]) if len(g) >= 2]
    gp = []
    for gi, g in enumerate(groups):
        p = g.p_yes.values
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                gp.append((gi, p[i], p[j]))
    if not gp:
        return None
    G = pd.DataFrame(gp, columns=["group", "pa", "pb"])
    G["c11"] = G.pa * G.pb
    G["c10"] = 0.5 * (G.pa * (1 - G.pb) + G.pb * (1 - G.pa))
    G["c01"] = G.c10
    G["c00"] = (1 - G.pa) * (1 - G.pb)
    G["type"] = list(zip(G.pa.round(6), G.pb.round(6)))

    def draw(Gs):
        T = Gs.groupby("type").agg(n=("group", "size"), c11=("c11", "first"), c10=("c10", "first"),
                                   c01=("c01", "first"), c00=("c00", "first"))
        tot = np.zeros((N_DESIG, 4))
        for t in T.itertuples():
            pr = np.array([t.c11, t.c10, t.c01, t.c00])
            tot += r_.multinomial(int(t.n), pr / pr.sum(), size=N_DESIG)
        # cells: (pred1,target1)=TP, (pred1,target0)=FP, (pred0,target1)=FN, (pred0,target0)=TN
        return m_from_counts(tot[:, 0], tot[:, 3], tot[:, 1], tot[:, 2])
    point = {k: float(v.mean()) for k, v in draw(G).items()}
    gids = G.group.unique()
    bs = {k: [] for k in point}
    byg = {g: d for g, d in G.groupby("group")}
    for _ in range(B):
        pick = r_.choice(gids, len(gids))
        Gs = pd.concat([byg[g] for g in pick])
        d = draw(Gs)
        for k in bs:
            bs[k].append(float(d[k].mean()))
    return {"smell": smell, "groups": len(groups), "pairs": len(G),
            **{k: point[k] for k in point}, **{f"{k}_lo": boot_ci(bs[k])[0] for k in point},
            **{f"{k}_hi": boot_ci(bs[k])[1] for k in point}}


def main():
    t0 = time.time()
    best = load("step3_best")
    rows, nd_rows, pop_info = [], [], []
    for smell, variant, cache_name in POPS:
        cache = load(cache_name)
        splits = cache["splits"]
        bm = cache.get("best", best[smell]) if variant == "R5" else best[smell]
        params = cache["res"][bm]["params"]
        Eall = dacos_entities(smell, variant)
        U = unanimous(Eall)
        assert (U.entity.values == cache["entities"]).all()
        L = annotation_long()
        A, Ev = variant_annotations(L, variant)
        A = A[A.smell == smell]
        Pop = Eall[Eall.n == 2].reset_index(drop=True)
        n_pop_all = int((Ev[Ev.smell == smell].n == 2).sum())
        Pop["target"] = Pop.target.fillna(0)   # placeholder for ties; not used by the ceiling computation
        feats = full_features(smell)
        res = run_protocol(bm, Pop, feats, splits, params_by_fold=params,
                           train_override=lambda tp, U=U: U[~U.project.isin(tp)][feats + ["target", "project"]])
        M = res["P"]
        votes = np.where(Pop.y == 0, 0, np.where(Pop.y == 2, 1, 2))
        cat = categories(votes, M)
        r_ = rng()
        hum, mod = simulate(cat, r_)
        point = {f"human_{k}": float(v.mean()) for k, v in hum.items()}
        point.update({f"model_{k}": float(v.mean()) for k, v in mod.items()})
        bs = {k: [] for k in ("human_MCC", "model_MCC", "gap_MCC", "ratio_MCC", "human_macro_F1", "model_macro_F1",
                              "gap_macro_F1", "human_accuracy", "model_accuracy", "gap_accuracy")}
        n = len(Pop)
        for _ in range(B):
            idx = r_.integers(0, n, n)
            h, m = simulate(categories(votes[idx], M[:, idx]), r_)
            for k in ("MCC", "macro_F1", "accuracy"):
                hm, mm_ = float(h[k].mean()), float(m[k].mean())
                bs[f"human_{k}"].append(hm)
                bs[f"model_{k}"].append(mm_)
                bs[f"gap_{k}"].append(hm - mm_)
            bs["ratio_MCC"].append(float(m["MCC"].mean() / h["MCC"].mean()) if h["MCC"].mean() != 0 else np.nan)
        label = f"{smell}" + (" R5" if variant == "R5" else "")
        for k in ("MCC", "macro_F1", "accuracy"):
            hl, hh = boot_ci(bs[f"human_{k}"])
            ml, mh = boot_ci(bs[f"model_{k}"])
            gl, gh = boot_ci(bs[f"gap_{k}"])
            rows.append({"population": label, "best_model": bm, "metric": k, "entities": n,
                         "unanimous": int((votes != 2).sum()), "split": int((votes == 2).sum()),
                         "human_vs_human": point[f"human_{k}"], "human_lo": hl, "human_hi": hh,
                         "model_vs_single_human": point[f"model_{k}"], "model_lo": ml, "model_hi": mh,
                         "gap_human_minus_model": point[f"human_{k}"] - point[f"model_{k}"], "gap_lo": gl, "gap_hi": gh,
                         "ratio_model_over_human": (point["model_MCC"] / point["human_MCC"]) if k == "MCC" else np.nan,
                         "ratio_lo": boot_ci(bs["ratio_MCC"])[0] if k == "MCC" else np.nan,
                         "ratio_hi": boot_ci(bs["ratio_MCC"])[1] if k == "MCC" else np.nan})
        pop_info.append({"population": label, "entities_with_exactly_2_usable": n_pop_all,
                         "dropped_missing_features": n_pop_all - n})
        nd = neardup_ceiling(Eall, label, rng())
        if nd:
            nd_rows.append(nd)
        print(label, f"{time.time() - t0:.0f}s", flush=True)

    HC = pd.DataFrame(rows)
    HC["analysis"] = "primary (human ceiling)"
    HC.to_csv(os.path.join(TAB, "human_ceiling.csv"), index=False)
    ND = pd.DataFrame(nd_rows)
    ND["analysis"] = "primary (second ceiling: near-duplicate pairs)"
    ND.to_csv(os.path.join(TAB, "human_ceiling_neardup.csv"), index=False)

    plt = plot_style()
    mc = HC[HC.metric == "MCC"].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    ys = np.arange(len(mc))[::-1]
    for yy, r in zip(ys, mc.itertuples()):
        ax.errorbar(r.human_vs_human, yy + 0.12, xerr=[[r.human_vs_human - r.human_lo], [r.human_hi - r.human_vs_human]],
                    fmt="o", color=COL["orange"], ms=4, capsize=0, label="human vs human" if yy == ys[0] else None)
        ax.errorbar(r.model_vs_single_human, yy - 0.12, xerr=[[r.model_vs_single_human - r.model_lo], [r.model_hi - r.model_vs_single_human]],
                    fmt="s", color=COL["blue"], ms=4, capsize=0, label="best model vs one human" if yy == ys[0] else None)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r.population} ({r.best_model})" for r in mc.itertuples()])
    ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
    ax.set_xlabel("MCC against a single annotation")
    ax.set_title("Human ceiling (2 annotations per entity)", loc="left")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=6)
    fig.tight_layout()
    savefig(fig, "human_ceiling")

    T = HC.copy()
    T["human vs human [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(T.human_vs_human, T.human_lo, T.human_hi)]
    T["model vs one human [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(T.model_vs_single_human, T.model_lo, T.model_hi)]
    T["gap human − model [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(T.gap_human_minus_model, T.gap_lo, T.gap_hi)]
    T["ratio model/human MCC [95% CI]"] = [fmt_ci(a, b, c) if np.isfinite(a) else "" for a, b, c in zip(T.ratio_model_over_human, T.ratio_lo, T.ratio_hi)]
    T = T[["population", "best_model", "metric", "entities", "unanimous", "split", "human vs human [95% CI]",
           "model vs one human [95% CI]", "gap human − model [95% CI]", "ratio model/human MCC [95% CI]"]]
    N = ND.copy()
    for k in ("MCC", "macro_F1", "accuracy"):
        N[f"{k} [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(N[k], N[f"{k}_lo"], N[f"{k}_hi"])]
    N = N[["smell", "groups", "pairs", "MCC [95% CI]", "macro_F1 [95% CI]", "accuracy [95% CI]"]]
    sent = "; ".join(f"{r.population}: human {r.human_vs_human:.3f}, model {r.model_vs_single_human:.3f}, ratio {r.ratio_model_over_human:.2f}"
                     for r in HC[HC.metric == "MCC"].itertuples())
    txt = f"""**Analysis type: primary (human ceiling).** plan.md §5.2.

**Method.**
- Population: primary-set entities (R5 set for "LPL R5") with exactly 2 usable annotations, unanimous and split.
- **Human vs human.** One annotation is the prediction and the other the target, with random roles in each of {N_DESIG} designations. MCC, macro-F1 and accuracy are computed over entities and averaged over designations.
  - Only split entities depend on the designation. Each designation is therefore simulated exactly by binomial draws on the split counts (sufficient statistics), which is equivalent to drawing roles entity by entity.
- **Model vs one human.**
  - The best model of the run (CM LR, LPL GB, LPL R5 SVM) uses section-B fold hyperparameters on the 25 splits, trained on unanimous training entities only.
  - It predicts every held-out entity in the population, ties included.
  - In designation d it is scored against the same target annotation as the human, using repeat d mod 5. The comparison is paired.
- **CIs.** Bootstrap over entities (B = {B}); each resample re-draws {N_DESIG} designations. The gap and the ratio use the same resamples and draws.
- **Second ceiling: near-duplicate pairs.**
  - Pairs of different entities in the same project with identical near-duplicate keys (identifiers → ID, literals → LIT), primary set (R5 set for LPL R5).
  - One random annotation per entity, random roles, {N_DESIG} designations. CI from a bootstrap over near-duplicate groups (clusters).

Population sizes:

{md_table(pd.DataFrame(pop_info))}

**Ceiling table**

{md_table(T)}

**Second ceiling: human-vs-human agreement between structurally identical snippets of the same project**

{md_table(N)}

Tables: `tables/human_ceiling.csv`, `tables/human_ceiling_neardup.csv`. Figure: `figures/human_ceiling.pdf` (.png). Runtime {time.time() - t0:.0f}s.

**Summary (MCC).** {sent}.
"""
    write_frag("human_ceiling", txt)
    print(txt)


if __name__ == "__main__":
    main()
