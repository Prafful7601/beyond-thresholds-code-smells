"""Step 3 G (feature selection), I (error analysis), J (sensitivity), plan.md §4.5. CM and LPL."""
import itertools
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.feature_selection import RFECV, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402

ERR_DIR = os.path.join(ROOT, "results/error_analysis")
os.makedirs(ERR_DIR, exist_ok=True)


# ---------------------------------------------------------------- G
def select_job(m, D, feats, tp, params, r, k):
    te = D.project.isin(tp).values
    T = D[~te]
    X, y, g = T[feats].values, T.target.values.astype(int), T.project.values
    mi = mutual_info_classif(X, y, random_state=SEED)
    s1 = [f for f, v in zip(feats, mi) if v > 0]
    mi_of = dict(zip(feats, mi))
    s2 = list(s1)
    if len(s2) > 1:
        C = T[s2].corr().abs()
        changed = True
        while changed:
            changed = False
            for a, b in itertools.combinations(list(s2), 2):
                if a in s2 and b in s2 and C.loc[a, b] > 0.85:
                    s2.remove(a if mi_of[a] < mi_of[b] else b)
                    changed = True
    s3 = list(s2)
    if len(s2) > 1:
        est = Pipeline([("sc", StandardScaler()), ("clf", LogisticRegression(class_weight="balanced", max_iter=10000))])
        rfe = RFECV(est, step=1, cv=GroupKFold(3), scoring=MCC_SCORER, importance_getter="named_steps.clf.coef_",
                    min_features_to_select=1)
        rfe.fit(T[s2].values, y, groups=g)
        s3 = [f for f, keep in zip(s2, rfe.support_) if keep]
    model = fit(m, params, T[s3].values, y, SEED + r)
    sc, pr = score(model, m, D[te][s3].values)
    return r, k, np.where(te)[0], sc, pr, s1, s2, s3, mi


# ---------------------------------------------------------------- I
def err_job(m, Dall, feats, tp, params, r):
    """Train on unanimous entities of the training projects; predict every entity of the test projects."""
    te = Dall.project.isin(tp).values
    T = Dall[~te & Dall.unanimous.values]
    model = fit(m, params, T[feats].values, T.target.values.astype(int), SEED + r)
    sc, pr = score(model, m, Dall[te][feats].values)
    return np.where(te)[0], sc, pr


def main():
    t0 = time.time()
    best = load("step3_best")
    fs_rows, fs_perf, err_rows, err_summary, sens_rows = [], [], [], [], []
    L = annotation_long()
    in_run_entities = set(zip(L[L.in_run].smell, L[L.in_run].entity))
    z = zipfile.ZipFile(ZIP)
    for smell in STEP3_SMELLS:
        cache = load(f"step3_B_{smell}")
        splits, resB = cache["splits"], cache["res"]
        Eall = dacos_entities(smell)
        D = unanimous(Eall)
        feats = full_features(smell)
        bm = best[smell]
        r0 = [(r, k, tp) for r, k, tp in splits if r == 0]
        # ------------------------------------------------ G feature selection (repeat 0)
        jobs = Parallel(n_jobs=N_JOBS)(delayed(select_job)(bm, D, feats, tp, resB[bm]["params"][(r, k)], r, k)
                                       for r, k, tp in r0)
        S = np.full(len(D), np.nan)
        P = np.zeros(len(D), bool)
        sets = []
        for r, k, idx, sc, pr, s1, s2, s3, mi in jobs:
            S[idx], P[idx] = sc, pr
            sets.append(set(s3))
            fs_rows.append({"smell": smell, "model": bm, "fold": k, "after_MI_filter": ", ".join(s1),
                            "after_correlation_pruning": ", ".join(s2), "after_RFECV": ", ".join(s3),
                            "n_selected": len(s3), **{f"MI_{f}": v for f, v in zip(feats, mi)}})
        y = D.target.values.astype(int)
        jac = [len(a & b) / len(a | b) if (a | b) else 1.0 for a, b in itertools.combinations(sets, 2)]
        sel = {"S": S[None, :], "P": P[None, :], "y": y}
        allf = {"S": resB[bm]["S"][:1], "P": resB[bm]["P"][:1], "y": y}
        idxs = boot_indices(len(y))
        d = {}
        for kname in ("macro_F1", "MCC"):
            f = METRICS[kname]
            dd = [f(y[i], S[i], P[i]) - f(y[i], allf["S"][0][i], allf["P"][0][i]) for i in idxs]
            d[kname] = (METRICS[kname](y, S, P) - METRICS[kname](y, allf["S"][0], allf["P"][0]),) + boot_ci(dd)
        keep_full = (d["MCC"][0] < 0) or (np.mean(jac) < 0.7)
        fs_perf.append({"smell": smell, "model": bm, "selected_macro_F1": METRICS["macro_F1"](y, S, P),
                        "all_macro_F1": METRICS["macro_F1"](y, allf["S"][0], allf["P"][0]),
                        "selected_MCC": METRICS["MCC"](y, S, P), "all_MCC": METRICS["MCC"](y, allf["S"][0], allf["P"][0]),
                        "delta_macro_F1": d["macro_F1"][0], "delta_macro_F1_lo": d["macro_F1"][1], "delta_macro_F1_hi": d["macro_F1"][2],
                        "delta_MCC": d["MCC"][0], "delta_MCC_lo": d["MCC"][1], "delta_MCC_hi": d["MCC"][2],
                        "mean_pairwise_jaccard": float(np.mean(jac)), "decision": "keep full feature set" if keep_full else
                        "selection neither hurt MCC nor was unstable (reported only; final model unchanged)"})
        print(smell, "G", f"{time.time() - t0:.0f}s", flush=True)

        # ------------------------------------------------ I error analysis (repeat 0, best model)
        lab = Eall[Eall.target.notna() | (Eall.label == "tie")].reset_index(drop=True)
        jobs = Parallel(n_jobs=N_JOBS)(delayed(err_job)(bm, lab, feats, tp, resB[bm]["params"][(r, k)], r) for r, k, tp in r0)
        sc_all = np.full(len(lab), np.nan)
        pr_all = np.zeros(len(lab), bool)
        for idx, sc, pr in jobs:
            sc_all[idx], pr_all[idx] = sc, pr
        lab["score"], lab["pred_smelly"] = sc_all, pr_all
        lab["in_run"] = [(smell, e) in in_run_entities for e in lab.entity]
        lab["vote_split"] = lab.y.astype(int).astype(str) + "/" + lab.n.astype(int).astype(str)
        maj = lab[lab.label != "tie"].copy()
        maj["error"] = maj.pred_smelly != (maj.target == 1)
        maj["error_type"] = np.where(~maj.error, "", np.where(maj.pred_smelly, "FP", "FN"))
        ties = lab[lab.label == "tie"]
        for grp, mask in (("unanimous", maj.unanimous), ("split (non-unanimous majority)", ~maj.unanimous),
                          ("in run", maj.in_run), ("not in run", ~maj.in_run), ("all majority-labelled", maj.index >= 0)):
            g = maj[mask]
            err_summary.append({"smell": smell, "model": bm, "group": grp, "entities": len(g),
                                "share_of_all_entities": len(g) / len(maj), "errors": int(g.error.sum()),
                                "share_of_errors": float(g.error.sum() / max(maj.error.sum(), 1)),
                                "error_rate": float(g.error.mean()) if len(g) else np.nan})
        err_summary.append({"smell": smell, "model": bm, "group": "ties (no label; predicted-smelly share)",
                            "entities": len(ties), "share_of_all_entities": np.nan, "errors": np.nan,
                            "share_of_errors": np.nan, "error_rate": float(ties.pred_smelly.mean()) if len(ties) else np.nan})
        rs = np.random.default_rng(SEED)
        for et in ("FP", "FN"):
            pool = maj[maj.error_type == et]
            pick = pool.iloc[np.sort(rs.choice(len(pool), min(15, len(pool)), replace=False))] if len(pool) else pool
            for r in pick.itertuples():
                code = z.read(r.path.lstrip("/")).decode("utf-8", "replace") if r.path.lstrip("/") in z.namelist() else ""
                err_rows.append({"smell": smell, "model": bm, "error_type": et, "entity": r.entity, "project": r.project,
                                 "path": r.path, "vote_split": r.vote_split, "unanimous": r.unanimous, "in_run": r.in_run,
                                 "score": r.score, **{f: getattr(r, f) for f in feats}, "code": code})
        print(smell, "I", f"{time.time() - t0:.0f}s", flush=True)

        # ------------------------------------------------ J sensitivity (training labels from R4, R6)
        for variant in ("R4", "R6"):
            Ev = dacos_entities(smell, variant)
            Uv = unanimous(Ev)

            def train_v(tp, Uv=Uv):
                return Uv[~Uv.project.isin(tp)][feats + ["target", "project"]]
            paired = run_protocol(bm, D, feats, splits, train_override=train_v)
            dlt = paired_delta(paired, resB[bm])
            sv = summarise(paired)
            own = run_protocol(bm, Uv, feats, project_splits(Uv.project)) if Uv.project.nunique() >= N_FOLDS else None
            so = summarise(own) if own is not None else {}
            sens_rows.append({"smell": smell, "model": bm, "variant": variant, "variant_unanimous_n": len(Uv),
                              "paired_test_n": len(D), "paired_macro_F1": sv["macro_F1"], "paired_MCC": sv["MCC"],
                              "primary_macro_F1": summarise_point(resB[bm])["macro_F1"],
                              "primary_MCC": summarise_point(resB[bm])["MCC"],
                              "delta_macro_F1": dlt["macro_F1"], "delta_macro_F1_lo": dlt["macro_F1_lo"],
                              "delta_macro_F1_hi": dlt["macro_F1_hi"], "delta_MCC": dlt["MCC"],
                              "delta_MCC_lo": dlt["MCC_lo"], "delta_MCC_hi": dlt["MCC_hi"],
                              "own_labels_macro_F1": so.get("macro_F1", np.nan), "own_labels_macro_F1_lo": so.get("macro_F1_lo", np.nan),
                              "own_labels_macro_F1_hi": so.get("macro_F1_hi", np.nan), "own_labels_MCC": so.get("MCC", np.nan),
                              "own_labels_MCC_lo": so.get("MCC_lo", np.nan), "own_labels_MCC_hi": so.get("MCC_hi", np.nan)})
        print(smell, "J", f"{time.time() - t0:.0f}s", flush=True)

    FS = pd.DataFrame(fs_rows)
    FP_ = pd.DataFrame(fs_perf)
    FS.to_csv(os.path.join(TAB, "feature_selection.csv"), index=False)
    FP_.to_csv(os.path.join(TAB, "feature_selection_performance.csv"), index=False)
    ER = pd.DataFrame(err_rows)
    ES = pd.DataFrame(err_summary)
    ER.drop(columns=["code"]).to_csv(os.path.join(ERR_DIR, "error_samples.csv"), index=False)
    ES.to_csv(os.path.join(ERR_DIR, "error_rates.csv"), index=False)
    with open(os.path.join(ERR_DIR, "error_samples_code.md"), "w") as f:
        f.write("# Error-analysis samples (best model, repeat-0 out-of-fold predictions)\n\n")
        for r in ER.itertuples():
            f.write(f"## {r.smell} {r.error_type} {r.entity} ({r.project}); votes {r.vote_split}; in run: {r.in_run}; "
                    f"score {r.score:.3f}\n\n`{r.path}`\n\n```java\n{r.code.rstrip()}\n```\n\n")
    SE = pd.DataFrame(sens_rows)
    SE["analysis"] = "robustness (sensitivity J)"
    SE.to_csv(os.path.join(TAB, "sensitivity.csv"), index=False)

    fs = FS[["smell", "model", "fold", "after_MI_filter", "after_correlation_pruning", "after_RFECV", "n_selected"]]
    fp = FP_.copy()
    fp["Δ macro-F1 [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(fp.delta_macro_F1, fp.delta_macro_F1_lo, fp.delta_macro_F1_hi)]
    fp["Δ MCC [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(fp.delta_MCC, fp.delta_MCC_lo, fp.delta_MCC_hi)]
    for c in ("selected_macro_F1", "all_macro_F1", "selected_MCC", "all_MCC", "mean_pairwise_jaccard"):
        fp[c] = fp[c].round(3)
    fp = fp[["smell", "model", "selected_macro_F1", "all_macro_F1", "selected_MCC", "all_MCC", "Δ macro-F1 [95% CI]",
             "Δ MCC [95% CI]", "mean_pairwise_jaccard", "decision"]]
    txt_g = f"""**Analysis type: exploratory-transparent (reported only; never used to choose the final model).**

**Method.**
- Repeat-0 folds of section B; selection uses the training fold only.
1. Mutual-information filter: keep features with `mutual_info_classif` > 0 (random_state 20261021).
2. Pearson |r| > 0.85 pruning: drop the feature with lower MI.
3. `RFECV` with standardised class-weighted LR (`GroupKFold(3)` by project, scoring MCC).
- The best model, with fold parameters, is then trained on the selected subset. Performance on pooled repeat-0 out-of-fold predictions is compared with the full feature set using a paired bootstrap.
- Pre-registered decision: keep the full feature set if selection lowers MCC or the mean pairwise Jaccard across folds is < 0.7.

**Selected features per fold**

{md_table(fs)}

**Selected versus all features**

{md_table(fp)}

Tables: `tables/feature_selection.csv` (including per-fold MI values), `tables/feature_selection_performance.csv`.
"""
    es = ES.copy()
    for c in ("share_of_all_entities", "share_of_errors", "error_rate"):
        es[c] = es[c].round(3)
    es["errors"] = es["errors"].astype("Int64").astype(object).fillna("n/a")
    es = es.astype(object).where(es.notna(), "n/a")
    txt_i = f"""**Analysis type: primary (descriptive error analysis).**

**Method.**
- Best model on the repeat-0 folds with section-B fold parameters, trained on unanimous training entities.
- Every entity of the held-out projects is predicted: unanimous, non-unanimous majority (n ≥ 3), and ties.
- Errors are counted on majority-labelled entities. Ties have no label, so their predicted-smelly share is reported instead.
- An entity is "in run" if any of its annotations (unfiltered) lies in an answer run.
- Samples: 15 FP and 15 FN per smell (seed 20261021), saved with code, features, vote split, run membership and score.

{md_table(es)}

- Split entities with a majority label are rare in CM and LPL, because nearly all entities have 2 annotations and splits are ties. The "split" row is therefore very small.

Files: `results/error_analysis/error_rates.csv`, `error_samples.csv`, `error_samples_code.md`.
"""
    se = SE.copy()
    rows = []
    for r in se.to_dict("records"):
        rows.append({"smell": r["smell"], "model": r["model"], "training labels": r["variant"],
                     "variant unanimous n": r["variant_unanimous_n"],
                     "paired: macro-F1 (primary → variant)": f"{r['primary_macro_F1']:.3f} → {r['paired_macro_F1']:.3f}",
                     "Δ macro-F1 [95% CI]": fmt_ci(r["delta_macro_F1"], r["delta_macro_F1_lo"], r["delta_macro_F1_hi"]),
                     "paired: MCC (primary → variant)": f"{r['primary_MCC']:.3f} → {r['paired_MCC']:.3f}",
                     "Δ MCC [95% CI]": fmt_ci(r["delta_MCC"], r["delta_MCC_lo"], r["delta_MCC_hi"]),
                     "own labels macro-F1 [95% CI]": fmt_ci(r["own_labels_macro_F1"], r["own_labels_macro_F1_lo"], r["own_labels_macro_F1_hi"]),
                     "own labels MCC [95% CI]": fmt_ci(r["own_labels_MCC"], r["own_labels_MCC_lo"], r["own_labels_MCC_hi"])})
    txt_j = f"""**Analysis type: robustness (sensitivity; replaces annotator removal, which is impossible without annotator ids).**

**Method.**
- The section-B protocol (nested tuning, 25 splits) for the best model, with training labels from R4 (run annotations removed) or R6 (no consistency filter).
- Paired comparison: the variant-trained model and the primary model are evaluated on the same primary unanimous test entities. Δ = variant − primary, with a paired bootstrap CI.
- Unpaired: each variant is also evaluated on its own unanimous labels (own 5 × 5 project splits).

{md_table(pd.DataFrame(rows))}

Table: `tables/sensitivity.csv`. Runtime G+I+J {time.time() - t0:.0f}s.
"""
    write_frag("step3_G", txt_g)
    write_frag("step3_I", txt_i)
    write_frag("step3_J", txt_j)
    print(txt_g)
    print(txt_i)
    print(txt_j)


if __name__ == "__main__":
    main()
