"""Step 3 E: leakage and validity checks (plan.md §4.5 E). CM and LPL. Validity analysis."""
import hashlib
import os
import re
import sys
import time
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402
from features import KEYWORDS, TOKEN, strip  # noqa: E402


def keys(src):
    exact = re.sub(r"\s+", " ", strip(src, keep_literals=True)[0]).strip()
    code = strip(src)[0]
    toks = []
    for t in TOKEN.findall(code):
        if re.match(r"[A-Za-z_$]", t):
            toks.append(t if t in KEYWORDS else "ID")
        elif re.match(r"\d", t):
            toks.append("LIT")
        elif t in ('"', "'"):
            toks.append("LIT")
        else:
            toks.append(t)
    near = " ".join(toks)
    h = lambda s: hashlib.sha1(s.encode()).hexdigest()  # noqa: E731
    return h(exact), h(near)


def file_key(path):
    parts = path.strip("/").split("/")
    return "/".join(parts[1:5]) if parts[0] == "codesplit_java_method" else "/".join(parts[1:5]).replace(".code", "")


def main():
    t0 = time.time()
    best = load("step3_best")
    z = zipfile.ZipFile(ZIP)
    dup_rows, cross_rows, leak_rows, skew_rows, rerun_rows, groups_rows = [], [], [], [], [], []
    for smell in STEP3_SMELLS:
        cache = load(f"step3_B_{smell}")
        splits = cache["splits"]
        D = unanimous(dacos_entities(smell))
        assert (D.entity.values == cache["entities"]).all()
        kk = [keys(z.read(p.lstrip("/")).decode("utf-8", "replace")) for p in D.path]
        D["exact_key"], D["near_key"] = [a for a, _ in kk], [b for _, b in kk]
        D["file"] = [file_key(p) for p in D.path]
        for kind in ("exact_key", "near_key"):
            g = D.groupby(kind)
            sizes = g.size()
            multi = sizes[sizes >= 2]
            n_proj = g.project.nunique()
            lab_mix = g.target.nunique()
            dup_rows.append({"smell": smell, "duplicate_type": kind.replace("_key", ""), "entities": len(D),
                             "groups_size_ge2": len(multi), "entities_in_groups": int(multi.sum()),
                             "groups_spanning_projects": int((n_proj[multi.index] > 1).sum()),
                             "groups_with_conflicting_labels": int((lab_mix[multi.index] > 1).sum())})
            # how many test entities have a duplicate in the training fold, per split
            for r, k, tp in splits:
                te = D.project.isin(tp)
                train_keys = set(D[~te][kind])
                n_cross = int(D[te][kind].isin(train_keys).sum())
                cross_rows.append({"smell": smell, "duplicate_type": kind.replace("_key", ""), "repeat": r, "fold": k,
                                   "test_entities": int(te.sum()), "test_with_duplicate_in_train": n_cross})
        # leakage assertions per split
        X, _ = dacosx_entities(smell)
        for r, k, tp in splits:
            te = D.project.isin(tp)
            tr = ~te
            leak_rows.append({"smell": smell, "repeat": r, "fold": k,
                              "entity_overlap": len(set(D[te].entity) & set(D[tr].entity)),
                              "file_overlap": len(set(D[te].file) & set(D[tr].file)),
                              "project_overlap": len(set(D[te].project) & set(D[tr].project)),
                              "dacosx_train_projects_in_test (C3)": len(set(X[~X.project.isin(tp)].project) & set(tp))})
        # train-serve skew
        for f in full_features(smell):
            ks = ks_2samp(D[f].values, X[f].values)
            skew_rows.append({"smell": smell, "feature": f, "DACOS_n": len(D), "DACOSX_n": len(X),
                              "DACOS_median": float(D[f].median()), "DACOSX_median": float(X[f].median()),
                              "KS_D": float(ks.statistic), "KS_p": float(ks.pvalue),
                              "computed_identically": "yes: stored DesigniteJava value from the same tables" if f in ("cc", "pc", "loc")
                              else "yes: same lexer (src/features.py) on the same files.zip snippet type"})
        # dedupe (keep lowest designite id per near-duplicate group) and rerun B headline (best + LR)
        D["did"] = D.entity.str[1:].astype(int)
        keep_idx = D.sort_values("did").groupby("near_key").head(1).index
        Dd = D.loc[sorted(keep_idx)].reset_index(drop=True)
        feats = full_features(smell)
        sp_d = project_splits(Dd.project)
        assert [t for _, _, t in sp_d] == [t for _, _, t in splits]
        models = [best[smell]] + ([] if best[smell] == "LR" else ["LR"])
        for m in models:
            orig = cache["res"][m]
            new = run_protocol(m, Dd, feats, sp_d)
            s_new = summarise(new)
            s_orig = summarise(orig)
            # paired on retained entities: original OOF predictions restricted vs deduplicated run
            pos = {e: i for i, e in enumerate(orig["entity"])}
            ii = np.array([pos[e] for e in Dd.entity])
            orig_sub = {"S": orig["S"][:, ii], "P": orig["P"][:, ii], "y": orig["y"][ii], "entity": orig["entity"][ii]}
            dlt = paired_delta(new, orig_sub)
            rerun_rows.append({"smell": smell, "model": m, "n_original": len(D), "n_deduplicated": len(Dd),
                               **{f"orig_{k}": v for k, v in s_orig.items()}, **{f"dedup_{k}": v for k, v in s_new.items()},
                               **{f"delta_retained_{k}": v for k, v in dlt.items()}})
        print(smell, f"{time.time() - t0:.0f}s", flush=True)

    DU = pd.DataFrame(dup_rows)
    CR = pd.DataFrame(cross_rows)
    LK = pd.DataFrame(leak_rows)
    SK = pd.DataFrame(skew_rows)
    RR = pd.DataFrame(rerun_rows)
    crs = CR.groupby(["smell", "duplicate_type"]).agg(splits=("fold", "size"), test_entities_total=("test_entities", "sum"),
                                                     with_duplicate_in_train_total=("test_with_duplicate_in_train", "sum"),
                                                     max_per_split=("test_with_duplicate_in_train", "max")).reset_index()
    lk = LK.drop(columns=["repeat", "fold"]).groupby("smell").sum().reset_index()
    checks = []
    for r in DU.itertuples():
        checks.append({"check": f"{r.duplicate_type} duplicate groups (size ≥ 2)", "smell": r.smell, "value": r.groups_size_ge2,
                       "detail": f"{r.entities_in_groups} entities; {r.groups_spanning_projects} groups span >1 project; "
                                 f"{r.groups_with_conflicting_labels} groups have conflicting labels"})
    for r in crs.itertuples():
        checks.append({"check": f"test entities with a {r.duplicate_type} duplicate in the training fold (sum over 25 splits)",
                       "smell": r.smell, "value": r.with_duplicate_in_train_total,
                       "detail": f"of {r.test_entities_total} test-entity slots; max {r.max_per_split} in one split"})
    for r in lk.itertuples():
        for c, v in zip(lk.columns[1:], r[2:]):
            checks.append({"check": f"{c} (sum over 25 splits)", "smell": r.smell, "value": int(v), "detail": "must be 0"})
    CK = pd.DataFrame(checks)
    CK["analysis"] = "validity check"
    CK.to_csv(os.path.join(TAB, "leakage_checks.csv"), index=False)
    CR.to_csv(os.path.join(TAB, "leakage_duplicates_per_split.csv"), index=False)
    SK.to_csv(os.path.join(TAB, "train_serve_skew.csv"), index=False)
    RR["analysis"] = "validity check (rerun of B headline on deduplicated data)"
    RR.to_csv(os.path.join(TAB, "leakage_dedup_rerun.csv"), index=False)

    rr = []
    for r in RR.to_dict("records"):
        rr.append({"smell": r["smell"], "model": r["model"], "n original → deduplicated": f"{r['n_original']} → {r['n_deduplicated']}",
                   "macro-F1 original": fmt(r["orig_macro_F1"]), "macro-F1 dedup [95% CI]": fmt_ci(r["dedup_macro_F1"], r["dedup_macro_F1_lo"], r["dedup_macro_F1_hi"]),
                   "MCC original": fmt(r["orig_MCC"]), "MCC dedup [95% CI]": fmt_ci(r["dedup_MCC"], r["dedup_MCC_lo"], r["dedup_MCC_hi"]),
                   "Δ macro-F1 on retained [95% CI]": fmt_ci(r["delta_retained_macro_F1"], r["delta_retained_macro_F1_lo"], r["delta_retained_macro_F1_hi"]),
                   "Δ MCC on retained [95% CI]": fmt_ci(r["delta_retained_MCC"], r["delta_retained_MCC_lo"], r["delta_retained_MCC_hi"])})
    sk = SK.copy()
    for c in ("DACOS_median", "DACOSX_median", "KS_D"):
        sk[c] = sk[c].round(3)
    sk["KS_p"] = [fmt_p(v) for v in sk.KS_p]
    leak_ok = int(LK[["entity_overlap", "file_overlap", "project_overlap", "dacosx_train_projects_in_test (C3)"]].values.sum()) == 0
    txt = f"""**Analysis type: validity check** (not a primary or robustness result).

**Method.**
- Duplicate keys are computed from each snippet's text in `files.zip`:
  - exact: comments removed, whitespace collapsed;
  - near: additionally, every non-keyword identifier becomes `ID` and every literal becomes `LIT`.
- Data: primary unanimous entities. Splits: the 25 section-B splits.
- Deduplication keeps the entity with the lowest DesigniteJava id in each near-duplicate group. The B headline (best model and LR, full nested protocol) is then rerun.
  - Δ compares the deduplicated run with the original out-of-fold predictions on the same retained entities, using a paired bootstrap.
- Train-serve skew: two-sample KS, DACOS unanimous entities versus the D4-cleaned DACOSX pool.

**Checks**

{md_table(CK.drop(columns=["analysis"]))}

{"All entity, file and project overlap checks are 0 in every split." if leak_ok else "**At least one overlap check is non-zero; see the table.**"}

**B headline after near-duplicate removal**

{md_table(pd.DataFrame(rr))}

**Train-serve skew (DACOS versus DACOSX)**

{md_table(sk)}

- Every feature is computed by the same code path for both sources. Stored DesigniteJava metrics come from the same `method_metrics` / `class_metrics` tables; computed features come from the same lexer on the same kind of snippet file.
- Large KS statistics are expected for the primary metric and size-related features, because DACOSX is selected outside the borderline band by construction.

Tables: `tables/leakage_checks.csv`, `tables/leakage_duplicates_per_split.csv`, `tables/leakage_dedup_rerun.csv`, `tables/train_serve_skew.csv`. Runtime {time.time() - t0:.0f}s.
"""
    write_frag("step3_E", txt)
    print(txt)


if __name__ == "__main__":
    main()
