"""Prompt 3B B0: audit of the C# code-smell dataset (Zenodo 10.5281/zenodo.10475432). Descriptive only; no analysis.

Usage: python -I src/external_audit.py   (expects data/external/csharp/*.xlsx; run_all.sh downloads them)
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LOG, ROOT, md_table, write_frag  # noqa: E402

DIR = os.path.join(ROOT, "data/external/csharp")
SETS = {"Data Class": "DataSet_Data_Class.xlsx", "Feature Envy": "DataSet_Feature_Envy.xlsx",
        "Refused Bequest": "DataSet_Refused_Bequest.xlsx"}
HEUR = {"Data Class": "Data_Class_Heuristics.xlsx", "Feature Envy": "Feature_Envy_Heuristics.xlsx",
        "Refused Bequest": "Refused_Bequest_Heuristics.xlsx"}


def load(path):
    raw = pd.read_excel(path, header=None)
    names = [str(v) for v in raw.iloc[1]]
    groups = list(raw.iloc[0])
    m0 = next(i for i, g in enumerate(groups) if g == "Metrics")
    a0 = next(i for i, g in enumerate(groups) if g == "Annotators")
    fin = names.index("Final annotation")
    df = raw.iloc[2:].reset_index(drop=True)
    mnames, seen = [], {}
    for n in names[m0:fin]:   # disambiguate repeated headers by position (Refused Bequest has two `BOvR` columns)
        seen[n] = seen.get(n, 0) + 1
        mnames.append(f"metric:{n}" if names[m0:fin].count(n) == 1 else f"metric:{n}#{seen[n]}")
    cols = names[:m0] + mnames + ["final"] + [f"ann{n.replace('.0', '')}" for n in names[a0:]]
    df.columns = cols
    return df, names[m0:fin]


def main():
    lines, rows, met_rows, pair_rows = [], [], [], []
    for smell, f in SETS.items():
        df, metrics = load(os.path.join(DIR, f))
        ann = [c for c in df.columns if c.startswith("ann")]
        A = df[ann].apply(pd.to_numeric, errors="coerce")
        final = pd.to_numeric(df.final, errors="coerce")
        n_ann = A.notna().sum(axis=1)
        projects = df["Project Link"].str.replace(r"/tree/.*", "", regex=True)
        dup_metric_names = sorted({m for m in metrics if metrics.count(m) > 1})
        # majority-vote consistency check of the released final score
        def maj(r):
            v = r.dropna().astype(int).tolist()
            if not v:
                return np.nan
            c = pd.Series(v).value_counts()
            top = c[c == c.max()].index
            return top[0] if len(top) == 1 else np.nan   # no strict majority
        mv = A.apply(maj, axis=1)
        agree_final = (mv == final) | mv.isna()
        rows.append({"smell": smell, "file": f, "snippets": len(df), "unique_snippet_ids": df["Code Snippet ID"].nunique(),
                     "granularity": "method" if smell == "Feature Envy" else "class",
                     "projects": projects.nunique(), "annotator_columns": len(ann),
                     "snippets_by_n_annotations": dict(n_ann.value_counts().sort_index()),
                     "severity_values_individual": sorted(pd.unique(A.values.ravel()[~np.isnan(A.values.ravel())]).astype(int).tolist()),
                     "final_distribution": dict(final.value_counts().sort_index().astype(int)),
                     "final_missing": int(final.isna().sum()),
                     "snippets_without_strict_majority": int(mv.isna().sum() - (n_ann == 0).sum()),
                     "final_differs_from_strict_majority": int((~agree_final).sum()),
                     "n_metrics": len(metrics), "duplicate_metric_names": ", ".join(dup_metric_names) or "none"})
        met_rows.append({"smell": smell, "metrics": ", ".join(metrics)})
        for a, b in itertools.combinations(ann, 2):
            both = A[[a, b]].dropna()
            pair_rows.append({"smell": smell, "annotator_pair": f"{a}-{b}", "snippets_both": len(both),
                              "exact_agreement": float((both[a] == both[b]).mean()) if len(both) else np.nan})
        lines.append(f"{smell}: projects = {', '.join(sorted(projects.unique()))}")
        h = pd.read_excel(os.path.join(DIR, HEUR[smell]), header=None)
        lines.append(f"{smell} heuristics file {HEUR[smell]}: {h.shape[0] - 4} snippets; heuristics per annotator: "
                     f"{', '.join(str(v) for v in h.iloc[3, 1:].unique())}")
    R = pd.DataFrame(rows)
    M = pd.DataFrame(met_rows)
    P = pd.DataFrame(pair_rows)
    out = "\n".join(lines)
    open(os.path.join(LOG, "external_audit.txt"), "w").write(R.to_string() + "\n\n" + M.to_string() + "\n\n" + P.to_string() + "\n\n" + out + "\n")
    R.to_csv(os.path.join(ROOT, "results/tables/external_B0_audit.csv"), index=False)
    M.to_csv(os.path.join(ROOT, "results/tables/external_B0_metrics.csv"), index=False)
    P.to_csv(os.path.join(ROOT, "results/tables/external_B0_annotator_pairs.csv"), index=False)
    design_rows, two_agree, pos = [], [], []
    for smell, f in SETS.items():
        df, _ = load(os.path.join(DIR, f))
        A = df[[c for c in df.columns if c.startswith("ann")]].apply(pd.to_numeric, errors="coerce")
        n = A.notna().sum(axis=1)
        agree = int(A[n == 2].apply(lambda r: r.dropna().nunique() == 1, axis=1).sum())
        two_agree.append(f"{smell} {agree}/{int((n == 2).sum())}")
        fin = pd.to_numeric(df.final, errors="coerce")
        pos.append(f"{smell} {int((fin >= 1).sum())}/{len(fin)}")
        design_rows.append({"smell": smell, "rated_by_annotator_1": int(A.ann1.notna().sum()),
                            "rated_by_annotator_2": int(A.ann2.notna().sum()), "rated_by_annotator_3": int(A.ann3.notna().sum()),
                            "snippets_with_2_annotations": int((n == 2).sum()), "of_which_agree": agree,
                            "snippets_with_3_annotations": int((n == 3).sum())})
    design = "**Annotation design (from the released columns)**\n\n" + md_table(pd.DataFrame(design_rows))
    two_agree = "; ".join(two_agree)
    pos = "; ".join(pos)
    r = R.copy()
    for c in ("snippets_by_n_annotations", "final_distribution"):
        r[c] = r[c].astype(str)
    p = P.copy()
    p["exact_agreement"] = p.exact_agreement.round(3)
    txt = f"""**Analysis type: descriptive audit (B0).** Nothing beyond counts is computed; B1 waits for the PI's go-ahead.

- Source: Zenodo 10.5281/zenodo.10475432 (v1.0, 2024-01-09, CC BY 4.0), by Prokić, Luburić, Slivka, Grujić and Kovačević.
- Six xlsx files, MD5-verified: three datasets (one per smell) and three per-annotator heuristic files.

{md_table(r)}

Pairwise exact agreement of the released severity scores (descriptive; uses the annotator columns as released):

{md_table(p)}

Provided metrics:

{md_table(M)}

```
{out}
```

{design}

**Proposed primary metric per smell (for the PI's decision; not yet used).**
Metric definitions are from the Clean-CaDET platform's `CaDETMetrics.cs`, linked from the Zenodo record. The detection rules are from Lanza & Marinescu, *Object-Oriented Metrics in Practice* (Springer, 2006), and Marinescu, "Detection strategies" (ICSM 2004).

| smell | proposed primary metric | direction | justification | alternatives |
|---|---|---|---|---|
| Data Class | **WOC** (Weight Of Class: functional public methods / all public members) | lower = smellier | The defining condition of the Lanza–Marinescu Data Class strategy is WOC < 1/3: the interface exposes data rather than services. The other conditions (NOPA+NOAM, WMC) are size/complexity guards. | NOPA_NOPP-type counts (NOPA, NOPP); WMCNAMM |
| Feature Envy | **AID** (Access to Import Data: foreign attributes and methods accessed by the method) | higher = smellier | The Lanza–Marinescu Feature Envy strategy is ATFD > FEW ∧ LAA < 1/3 ∧ FDP ≤ FEW. ATFD is its primary "uses foreign data" condition. LAA and FDP are not provided at method level; AID is the method-level analogue of ATFD in this dataset. | none of LAA/FDP is available; the class-level ATFD is not a method metric |
| Refused Bequest | **BUR** (Base-class Usage Ratio) | lower = smellier | The Lanza–Marinescu Refused Bequest strategy is (NProtM > FEW ∧ BUR < 1/3) ∨ BOvR < 1/3, plus complexity guards. BUR is the "uses few inherited members" condition. | BOvR (Base-class Overriding Ratio) |

**Issues to decide before B1:**
1. **Adjudicated annotation.** Every snippet with exactly 2 annotations shows perfect agreement ({two_agree}). A third annotation exists only where disagreement occurred. The released per-annotator scores therefore over-represent agreement, so a raw alpha would be biased upward and not comparable with DACOS. Options:
   - (a) alpha on the first two annotations only. This is not possible as released, because the slot of the "first" pair is not identifiable when three exist.
   - (b) report the raw alpha with this caveat.
   - (c) report only the share of snippets that needed a third annotator. Annotator 2 rated every snippet; annotators 1 and 3 split the second slot.
2. **Refused Bequest header.** The Refused Bequest sheet labels two adjacent columns `BOvR`, where the Data Class sheet has `BUR, BOvR` in the same positions. The single class present in both sheets has identical values in the two BUR positions. I propose treating the first column as BUR, but this rests on one shared class and the column order.
3. **Few positives.** Final severity ≥ 1 occurs in {pos}. RQ2 CIs will be wide, especially for Data Class.
4. **Severity scale.** Individual scores are 0–3 for Feature Envy and 0–2 for the other two (observed values). Ordinal alpha applies to severity and nominal alpha to presence (severity ≥ 1).

Tables: `tables/external_B0_audit.csv`, `external_B0_metrics.csv`, `external_B0_annotator_pairs.csv`. Log: `logs/external_audit.txt`.
"""
    write_frag("external_B0", txt)
    print(txt)


if __name__ == "__main__":
    main()
