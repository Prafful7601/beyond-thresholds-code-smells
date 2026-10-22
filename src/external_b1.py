"""Prompt 4 Part 2 / plan.md §7.2: external check B1 on the C# dataset (Zenodo 10.5281/zenodo.10475432).

Tag: external check. Agreement via the adjudication rate and exact bounds on first-pair ordinal alpha (no raw alpha);
ROC-AUC and Youden cut-offs of oriented primary metrics against the consensus label. No models.
"""
import itertools
import os
import sys

import krippendorff
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402
from external_audit import DIR, SETS, load  # noqa: E402
from rq2 import youden  # noqa: E402

# (smell, metric column, label, sign): oriented value = sign * metric, so higher = smellier
METRICS_B1 = [("Data Class", "metric:WOC", "WOC", -1), ("Feature Envy", "metric:AID", "AID", 1),
              ("Refused Bequest", "metric:BOvR#1", "first `BOvR`-labelled column", -1),
              ("Refused Bequest", "metric:BOvR#2", "second `BOvR`-labelled column", -1)]
FILTERS = {"Data Class": "WOC < 0.33 ∨ NOPA > 1 ∨ NOPP > 1 (non-private, non-abstract classes)",
           "Feature Envy": "AID ≥ 4", "Refused Bequest": "BUR < 0.33 (non-abstract classes with a parent and with methods other than constructors)"}


def alpha_bounds(A):
    """Exact min/max ordinal alpha over first-pair assignments for 3-rated snippets."""
    two = A[A.notna().sum(axis=1) == 2]
    three = A[A.notna().all(axis=1)]
    fixed = [tuple(r.dropna().astype(int)) for _, r in two.iterrows()]
    fixed += [(int(r.ann2), int(r.ann1)) for _, r in three[three.ann1 == three.ann3].iterrows()]
    ch = three[three.ann1 != three.ann3]
    types = ch.apply(lambda r: (int(r.ann2), min(int(r.ann1), int(r.ann3)), max(int(r.ann1), int(r.ann3))), axis=1).value_counts()
    tlist = list(types.items())
    vals = []
    for counts in itertools.product(*[range(c + 1) for _, c in tlist]):
        pairs = list(fixed)
        for ((a2, lo, hi), n), k in zip(tlist, counts):
            pairs += [(a2, lo)] * k + [(a2, hi)] * (n - k)
        R = np.array(pairs, float).T
        vals.append(krippendorff.alpha(reliability_data=R, level_of_measurement="ordinal", value_domain=[0, 1, 2, 3]))
    return float(np.min(vals)), float(np.max(vals)), len(vals), int(len(ch)), len(tlist)


def main():
    rows_a, rows_m, rows_l = [], [], []
    r_ = rng()
    data = {}
    for smell, f in SETS.items():
        df, _ = load(os.path.join(DIR, f))
        A = df[["ann1", "ann2", "ann3"]].apply(pd.to_numeric, errors="coerce")
        n = A.notna().sum(axis=1).values
        third = (n == 3).astype(float)
        bs = [third[r_.integers(0, len(third), len(third))].mean() for _ in range(B)]
        lo_a, hi_a, n_comb, n_choice, n_types = alpha_bounds(A)
        fin = pd.to_numeric(df.final, errors="coerce")
        rows_a.append({"smell": smell, "snippets": len(df), "third_rating_share": float(third.mean()),
                       "third_lo": boot_ci(bs)[0], "third_hi": boot_ci(bs)[1], "snippets_3_rated": int(third.sum()),
                       "with_a_choice_(a1≠a3)": n_choice, "choice_types": n_types, "assignments_enumerated": n_comb,
                       "alpha_ordinal_min": lo_a, "alpha_ordinal_max": hi_a})
        rows_l.append({"smell": smell, "snippets": len(df), "positives_final_ge1": int((fin >= 1).sum()),
                       "share_ge1": float((fin >= 1).mean()), "positives_final_ge2": int((fin >= 2).sum()),
                       "share_ge2": float((fin >= 2).mean())})
        data[smell] = (df, fin)
    for smell, col, label, sign in METRICS_B1:
        df, fin = data[smell]
        x = pd.to_numeric(df[col], errors="coerce")
        proj = df["Project Link"].str.replace(r"/tree/.*", "", regex=True)
        ok = x.notna()
        for rule, thr in (("final ≥ 1 (primary)", 1), ("final ≥ 2 (sensitivity)", 2)):
            y = (fin[ok] >= thr).astype(int).values
            v = (sign * x[ok]).values.astype(float)
            p = proj[ok].values
            row = {"smell": smell, "metric": label, "orientation": "higher = smellier" if sign > 0 else "lower = smellier (negated)",
                   "label": rule, "n_with_metric": int(ok.sum()), "missing_metric": int((~ok).sum()),
                   "positives": int(y.sum()), "share_positive": float(y.mean()), "projects": len(set(p))}
            if y.sum() < 5 or (1 - y).sum() < 5:
                row["note"] = "fewer than 5 positives or negatives: counts only"
                rows_m.append(row)
                continue
            auc = roc_auc_score(y, v)
            c, j = youden(v, y)
            bsa, bsc, skip = [], [], 0
            for _ in range(B):
                i = r_.integers(0, len(y), len(y))
                if y[i].min() == y[i].max():
                    skip += 1
                    continue
                bsa.append(roc_auc_score(y[i], v[i]))
                bsc.append(youden(v[i], y[i])[0])
            up = np.unique(p)
            bsp, skip_p = [], 0
            for _ in range(B):
                pick = r_.choice(up, len(up))
                i = np.concatenate([np.where(p == q)[0] for q in pick])
                if y[i].min() == y[i].max():
                    skip_p += 1
                    continue
                bsp.append(roc_auc_score(y[i], v[i]))
            raw_c = sign * c
            clo, chi = boot_ci(bsc)
            rlo, rhi = sorted([sign * clo, sign * chi])
            name = label.split(" ")[0] if smell != "Refused Bequest" else label
            rule_txt = (f"{name} ≥ {raw_c:.3g}" if sign > 0 else f"{name} ≤ {raw_c:.3g}")
            row.update({"AUC": auc, "AUC_lo": boot_ci(bsa)[0], "AUC_hi": boot_ci(bsa)[1],
                        "AUC_project_lo": boot_ci(bsp)[0], "AUC_project_hi": boot_ci(bsp)[1],
                        "youden_rule": rule_txt, "youden_cut_raw": raw_c, "youden_cut_lo": rlo, "youden_cut_hi": rhi,
                        "youden_J": j, "boot_skipped": skip, "project_boot_skipped": skip_p, "note": ""})
            rows_m.append(row)
    TA, TM, TL = pd.DataFrame(rows_a), pd.DataFrame(rows_m), pd.DataFrame(rows_l)
    for t in (TA, TM, TL):
        t["analysis"] = "external check"
    TA.to_csv(os.path.join(TAB, "external_B1_agreement.csv"), index=False)
    TM.to_csv(os.path.join(TAB, "external_B1_auc.csv"), index=False)
    TL.to_csv(os.path.join(TAB, "external_B1_labels.csv"), index=False)

    ta = TA.copy()
    ta["third-rating share [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(ta.third_rating_share, ta.third_lo, ta.third_hi)]
    ta["first-pair ordinal alpha: min – max"] = [f"{a:.3f} – {b:.3f}" for a, b in zip(ta.alpha_ordinal_min, ta.alpha_ordinal_max)]
    ta = ta[["smell", "snippets", "snippets_3_rated", "third-rating share [95% CI]", "with_a_choice_(a1≠a3)", "choice_types",
             "assignments_enumerated", "first-pair ordinal alpha: min – max"]]
    tl = TL.drop(columns=["analysis"]).copy()
    tl["share_ge1"] = tl.share_ge1.round(3)
    tl["share_ge2"] = tl.share_ge2.round(3)
    tm = TM.copy()
    tm["share_positive"] = tm.share_positive.round(3)
    tm["ROC-AUC [95% CI snippets]"] = [fmt_ci(a, b, c) if np.isfinite(a) else "–" for a, b, c in
                                       zip(tm.get("AUC", np.nan), tm.get("AUC_lo", np.nan), tm.get("AUC_hi", np.nan))]
    tm["[95% CI projects]"] = [f"[{b:.3f}, {c:.3f}]" if np.isfinite(b) else "–" for b, c in
                               zip(tm.get("AUC_project_lo", np.nan), tm.get("AUC_project_hi", np.nan))]
    tm["Youden rule [95% CI of cut]"] = [f"{r} [{a:.3g}, {b:.3g}]" if isinstance(r, str) else "–" for r, a, b in
                                         zip(tm.get("youden_rule"), tm.get("youden_cut_lo"), tm.get("youden_cut_hi"))]
    tm = tm[["smell", "metric", "orientation", "label", "n_with_metric", "missing_metric", "positives", "share_positive",
             "projects", "ROC-AUC [95% CI snippets]", "[95% CI projects]", "Youden rule [95% CI of cut]", "note"]]
    filt = "\n".join(f"  - {k}: {v}" for k, v in FILTERS.items())
    txt = f"""**Analysis type: external check** (not a replication). plan.md §7.2.

**Context.**
- This dataset was **not sampled from a borderline band**. It is external context for DACOS, not a replication.
- However, per the dataset author's doctoral dissertation (S. Prokić, University of Novi Sad, 2025, p. 68), its snippets were pre-filtered one-sidedly on the same metrics:
{filt}
  - The primary metric is therefore range-restricted on one side.
- Annotation was adjudicated. Snippets were re-served until the annotations agreed, and conflicting annotations were discussed and could be revised to reach consensus (p. 66).
- Three annotators took part (p. 67).

**Agreement** (no raw alpha, because the design is adjudicated).
- (a) Share of snippets that needed a third rating: the pre-adjudication disagreement rate, with a bootstrap CI over snippets (B = {B}).
- (b) Exact bounds on first-pair Krippendorff's alpha (ordinal, values 0–3):
  - 2-rated snippets keep their released pair.
  - Each 3-rated snippet contributes annotator 2 plus annotator 1 or annotator 3. Snippets of the same type (a2, {{a1, a3}}) are interchangeable, so every count combination is enumerated.
  - Caveat: released scores may have been revised after discussion, so these bound the agreement of the released first pairs, not necessarily the original pre-discussion ratings.

{md_table(ta)}

**Labels.**
- Consensus rule found in the data: the released final score equals the strict majority of the released individual scores for every snippet (§8.1).
- Primary: smelly = final ≥ 1. Sensitivity: final ≥ 2.

{md_table(tl)}

**Primary metric versus consensus.**
- Each metric is oriented so that higher = smellier before the AUC is computed. The Youden rule is reported on the original scale.
- LAA and FDP are **not provided** in the Feature Envy sheet, so no secondary metrics are added.
- **Refused Bequest header is ambiguous.** The sheet labels two adjacent columns `BOvR`; the Data Class sheet has `BUR, BOvR` in those positions. Neither the Zenodo description nor the dissertation (which defines BUR and BOvR, p. 10) gives the column order. Both columns are therefore reported as "first column" and "second column", and neither is chosen as BUR.
- CIs: bootstrap over snippets (B = {B}) and a cluster bootstrap over projects. Rows with fewer than 5 positives or negatives report counts only. Snippets with a missing metric are dropped (counts shown).

{md_table(tm)}

Tables: `tables/external_B1_agreement.csv`, `external_B1_labels.csv`, `external_B1_auc.csv`.
"""
    write_frag("external_B1", txt)
    print(txt)


if __name__ == "__main__":
    main()
