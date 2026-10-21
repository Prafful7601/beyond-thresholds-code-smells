"""Results section 1: dataset audit, integrity checks, descriptives, eligibility (plan D7, D8, D9)."""
import os
import sys
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

ann, smp, mm, cm, ent = load_tables()
L = annotation_long()
out = []
w = out.append

# ---------------------------------------------------------------- 1. counts vs paper
a = ann.merge(smp, left_on="sample_id", right_on="id", suffixes=("", "_s"))
paper = {"CM": (2197, 4349), "LPL": (1634, 3221), "MA": (1361, 2697)}
rows = []
for s in SMELLS:
    x = L[L.smell == s]
    rows.append({"smell": s, "paper_snippets": paper[s][0], "paper_annotations": paper[s][1],
                 "sample_rows": x.sample_id.nunique(), "entities": x.entity.nunique(), "annotations": len(x)})
T1 = pd.DataFrame(rows)
T1.loc[len(T1)] = {"smell": "Total (distinct)", "paper_snippets": 5192, "paper_annotations": 10267,
                   "sample_rows": ann.sample_id.nunique(),
                   "entities": a.assign(e=np.where(a.is_class == 1, "C", "M") + a.designite_id.astype(str)).e.nunique(),
                   "annotations": len(ann)}
T1.to_csv(os.path.join(TAB, "audit_counts_vs_paper.csv"), index=False)

w("### 1.1 Loading\n")
w("- The four Zenodo files match the record's MD5 checksums (plan §0).")
w("- No MySQL server was available. Both dumps were converted to SQLite by `src/convert_sql.py`, which parses the mysqldump `INSERT` tuples byte by byte.")
w(f"- Row counts: `annotation` {len(ann):,}; `sample` {len(smp):,}; `method_metrics` {len(mm):,}; `class_metrics` {len(cm):,}; DACOSX `entry` {len(ent):,}.")
w("- The `smell` table is empty in both dumps, and so is the `repository` table in the extended dump.")
w("- The `sample`, `method_metrics` and `class_metrics` tables are identical in the two dumps.\n")

w("### 1.2 Snippet and annotation counts versus the DACOS paper (Table II)\n")
w(md_table(T1))
w("")
w("- The annotation total matches the paper (10,267).")
w(f"- The number of distinct annotated `sample` rows is {ann.sample_id.nunique():,}, not 5,192. "
  "The paper's 5,192 equals the sum of its per-smell snippet counts.")
w(f"- {int((a.smells == '1,2').groupby(a.sample_id).first().sum())} snippets were offered for both CM and LPL, so they appear in both rows above.")
w("- Neither the sample-row counts nor the entity counts reproduce the paper's per-smell numbers.")
w("- The `annotation` table has no annotator identifier and no timestamp. The number of distinct annotators cannot be determined from the data; the paper reports 86.\n")

# ---------------------------------------------------------------- duplicates
dup = L[L.smell == "MA"].groupby("entity").sample_id.nunique()
w("### 1.3 Duplicate sample rows\n")
w(f"- {int((dup > 1).sum())} MA classes appear as two `sample` rows with the same `designite_id`, path and metrics. "
  f"That leaves {L[L.smell == 'MA'].entity.nunique():,} distinct MA classes instead of 1,341.")
dd = L[(L.smell == "MA") & L.entity.isin(dup[dup > 1].index)].sort_values("ann_id")
seq = dd.groupby(["entity", "sample_id"]).apply(lambda g: tuple(zip(g.answer, g.is_smell)), include_groups=False)
same = int(seq.groupby(level=0).nunique().eq(1).sum())
per_copy = dd.groupby(["entity", "sample_id"]).size()
nrange = f"{int(per_copy.min())}" if per_copy.min() == per_copy.max() else f"{int(per_copy.min())}–{int(per_copy.max())}"
w(f"- Each copy carries {nrange} annotations. All {dd.ann_id.nunique():,} annotation ids are distinct, so these are not copied rows. "
  f"The two copies' (checkbox, `is_smell`) sequences, in id order, are identical for {same} of the {int((dup > 1).sum())} classes.")
w("- Following plan D3, their annotations are pooled, giving 4 annotations per class.")
w("- No method snippet is duplicated.\n")

# ---------------------------------------------------------------- DACOSX
e = ent.merge(smp, left_on="sampleId", right_on="id", how="left")
code = {1: "MA present", 4: "MA absent", 2: "LPL present", 5: "LPL absent", 3: "CM present", 6: "CM absent"}
e["label"] = e.smellPresented.map(code)
e["consistent"] = (e.smellPresented.isin([2, 3, 5, 6]) & (e.is_class == 0)) | (e.smellPresented.isin([1, 4]) & (e.is_class == 1))
T = e.groupby(["smellPresented", "label"]).agg(entries=("sampleId", "size"), on_methods=("is_class", lambda s: int((s == 0).sum())),
                                              on_classes=("is_class", lambda s: int((s == 1).sum())),
                                              granularity_consistent=("consistent", "sum")).reset_index()
emm = e[e.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
ecm = e[e.is_class == 1].merge(cm, left_on="designite_id", right_on="id", suffixes=("", "_c"))
rng_ = []
for k in T.smellPresented:
    if k in (2, 3, 5, 6):
        x = emm[emm.smellPresented == k]
        col = "cc" if k in (3, 6) else "pc"
    else:
        x = ecm[ecm.smellPresented == k]
        col = "lcom"
    rng_.append(f"{col} {x[col].min():g}–{x[col].max():g}")
T["consistent_metric_range"] = rng_
annotated_ids = {s: set(L[L.smell == s].sample_id) for s in SMELLS}
ov = {}
for s, (pcode, acode) in DACOSX_CODES.items():
    c = e[e.consistent & e.smellPresented.isin([pcode, acode])]
    ov[s] = int(c.sampleId.isin(annotated_ids[s]).sum())
T.to_csv(os.path.join(TAB, "audit_dacosx_granularity.csv"), index=False)
w("### 1.4 DACOSX entries\n")
w(md_table(T))
w("")
w(f"- {int((~e.consistent).sum()):,} of {len(e):,} entries attach a smell to the other granularity "
  "(MA codes on method snippets; CM/LPL codes on class snippets). They are excluded (D4).")
xr = lambda d, col: f"{d[col].min():g}–{d[col].max():g}"
w(f"  - In these entries the label does not separate the stored metric of that granularity. "
  f"MA codes on methods: cc {xr(emm[emm.smellPresented == 1], 'cc')} for 'present' versus {xr(emm[emm.smellPresented == 4], 'cc')} for 'absent'. "
  f"CM codes on classes: lcom {xr(ecm[ecm.smellPresented == 3], 'lcom')} versus {xr(ecm[ecm.smellPresented == 6], 'lcom')}. "
  f"LPL codes on classes: lcom {xr(ecm[ecm.smellPresented == 2], 'lcom')} versus {xr(ecm[ecm.smellPresented == 5], 'lcom')}.")
w(f"- Within the consistent entries, present and absent are separated by the stored metric, as the column `consistent_metric_range` shows.")
w(f"- {sum(ov.values())} consistent DACOSX entries are the same snippet as a DACOS snippet annotated for the same smell "
  f"(CM {ov['CM']}, LPL {ov['LPL']}, MA {ov['MA']}; all are 'present'). They are removed before any training.")
w("- The paper's DacosX totals (CM 94,489; LPL 93,442; MA 19,674) equal the raw entry counts per smell code pair, including the cross-granularity entries.\n")

# ---------------------------------------------------------------- thresholds
E_all = entity_labels(L, min_ann=1)
E_all = attach_metrics(E_all)
rows = []
for s in SMELLS:
    x = E_all[E_all.smell == s][PRIMARY[s]]
    lo, hi = TABLE_I[s]
    if s == "LPL":
        x_core = E_all[(E_all.smell == s) & ~E_all.pc3_empty.astype(bool)][PRIMARY[s]]
    rows.append({"smell": s, "metric": PRIMARY[s], "paper_Table_I_band": f"{lo}–{hi}",
                 "observed_annotated_min": round(x.min(), 3), "observed_annotated_max": round(x.max(), 3),
                 "share_inside_Table_I_band": round(float(((x >= lo) & (x <= hi)).mean()), 3),
                 "share_above_band": round(float((x > hi).mean()), 3), "share_below_band": round(float((x < lo).mean()), 3),
                 "DesigniteJava_default": f">= {DESIGNITE[s]}" + (" (and NOF>=7, NOM>=7)" if s == "MA" else "")})
T = pd.DataFrame(rows)
T.to_csv(os.path.join(TAB, "audit_threshold_ranges.csv"), index=False)
w("### 1.5 Primary-metric ranges: paper Table I versus annotated data (descriptive, D10)\n")
w("Set: every annotated entity (all 10,267 annotations, before the consistency filter).\n")
w(md_table(T))
w("")
msm = smp[smp.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
cmx = set(e[e.consistent & e.smellPresented.isin([3, 6])].sampleId)
c4 = msm[msm.cc == 4]
c4_none = int((~c4.smells.str.contains("1") & ~c4.id.isin(cmx)).sum())
w(f"- Each smell's annotated range differs from the paper's Table I band. Of {len(c4):,} method samples with cc = 4, "
  f"{c4_none:,} are neither offered for CM annotation nor included in DACOSX for CM.")
w("- The DesigniteJava defaults come from `ThresholdsDTO` in github.com/tushartushar/DesigniteJava (commit 3321c56). The rule is metric ≥ threshold.\n")

# ---------------------------------------------------------------- checkbox vs is_smell
rows = []
for s in SMELLS:
    x = L[L.smell == s]
    ct = pd.crosstab(x.answer, x.is_smell)
    for cb in (0, 1):
        for iss in (0, 1):
            rows.append({"smell": s, "checkbox": cb, "is_smell": iss,
                         "annotations": int(ct.loc[cb, iss]) if cb in ct.index and iss in ct.columns else 0})
CT = pd.DataFrame(rows)
CT.to_csv(os.path.join(TAB, "audit_checkbox_vs_is_smell.csv"), index=False)
pv = CT.pivot_table(index=["smell", "checkbox"], columns="is_smell", values="annotations").reset_index()
pv.columns = ["smell", "checkbox", "is_smell=0", "is_smell=1"]
pv[["is_smell=0", "is_smell=1"]] = pv[["is_smell=0", "is_smell=1"]].astype(int)
ex = L[L.inconsistent].groupby("smell").agg(excluded=("ann_id", "size"), excluded_in_run=("in_run", "sum"))
ex = ex.reindex(SMELLS, fill_value=0).reset_index()
ex["share_in_run"] = (ex.excluded_in_run / ex.excluded.replace(0, np.nan)).round(3).astype(object).where(ex.excluded > 0, "n/a")
ex.to_csv(os.path.join(TAB, "audit_consistency_filter.csv"), index=False)
w("### 1.6 Smell checkbox versus `is_smell` (consistency filter, D7)\n")
w("- In the public Tagman source, `is_smell` is set to true when any checkbox is ticked.")
w("- An annotation with checkbox = 1 and `is_smell` = 0 contradicts itself. Such annotations are excluded from the primary analysis.\n")
w(md_table(pv))
w("")
w(md_table(ex))
w("")
w(f"- The filter removes {int(ex.excluded.sum()):,} annotations in total. Of these, {int(ex.excluded_in_run.sum()):,} lie inside an answer run (section 1.7).\n")

# ---------------------------------------------------------------- runs
rows = []
for s in SMELLS:
    x = L[L.smell == s].sort_values("ann_id").reset_index(drop=True)
    v = x.answer.values
    st = 0
    for i in range(1, len(v) + 1):
        if i == len(v) or v[i] != v[st]:
            if i - st >= RUN_MIN:
                p = v.mean() if v[st] == 1 else 1 - v.mean()
                rows.append({"smell": s, "first_ann_id": int(x.ann_id[st]), "last_ann_id": int(x.ann_id[i - 1]),
                             "length": i - st, "answer": int(v[st]), "smell_yes_rate": round(v.mean(), 3),
                             "log10_P_run_if_independent": round((i - st) * np.log10(p), 1)})
            st = i
R = pd.DataFrame(rows)
R.to_csv(os.path.join(TAB, "audit_answer_runs.csv"), index=False)
w("### 1.7 Runs of identical answers\n")
w(f"- Annotations were ordered by annotation id within each smell. Runs are maximal sequences of at least {RUN_MIN} identical checkbox answers (the fixed rule for R4).")
w("- The column `log10_P_run_if_independent` gives the log10 probability of one specific run of that length, if answers were independent draws at the smell's overall yes-rate. "
  "It is a scale reference, not a test.")
w("- The data contain no annotator or time information. They cannot show whether a run reflects one annotator's sequence or a recording artefact.\n")
w(md_table(R))
w("")
w("Run coverage per smell:\n")
cov = L.groupby("smell").agg(annotations=("ann_id", "size"), in_run=("in_run", "sum")).reindex(SMELLS).reset_index()
cov["share"] = (cov.in_run / cov.annotations).round(3)
w(md_table(cov))
w("")
w("Figure: `figures/audit_answer_runs.pdf` (.png): each smell's checkbox answers against annotation id, with a centred rolling yes-rate over 50 annotations and the runs shaded.\n")

plt = plot_style()
fig, axes = plt.subplots(3, 1, figsize=(7.0, 4.2), sharex=True)
for ax, s in zip(axes, SMELLS):
    x = L[L.smell == s].sort_values("ann_id")
    jit = np.random.default_rng(SEED).uniform(-0.12, 0.12, len(x))
    ax.scatter(x.ann_id, x.answer + jit, s=1.2, color=COL["ink2"], alpha=0.35, lw=0, rasterized=True)
    roll = x.answer.rolling(50, center=True, min_periods=10).mean().values.astype(float)
    ids = x.ann_id.values.astype(float)
    gap = np.r_[False, np.diff(ids) > 200]          # break the line where a smell has no annotations
    ids_b = np.insert(ids, np.where(gap)[0], np.nan)
    roll_b = np.insert(roll, np.where(gap)[0], np.nan)
    ax.plot(ids_b, roll_b, color=COL["blue"], lw=1.2, label="rolling yes-rate (50 annotations)")
    for r in R[R.smell == s].itertuples():
        ax.axvspan(r.first_ann_id, r.last_ann_id, color=COL["orange"], alpha=0.18, lw=0)
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels(["no", "0.5", "yes"])
    ax.set_ylim(-0.2, 1.2)
    ax.set_title(f"{SMELL_NAME[s]} ({CHECKBOX[s]})", loc="left")
    ax.grid(axis="x", visible=False)
axes[-1].set_xlabel("annotation id")
axes[0].plot([], [], color=COL["orange"], alpha=0.4, lw=6, label=f"run of ≥{RUN_MIN} identical answers")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.legend(*axes[0].get_legend_handles_labels(), loc="upper right", ncol=2, bbox_to_anchor=(1.0, 1.0))
savefig(fig, "audit_answer_runs")

# ---------------------------------------------------------------- files / features
feats = pd.read_csv(os.path.join(FEAT_DIR, "features.csv.gz"))
miss_ann = smp[smp.id.isin(ann.sample_id) & ~smp.path_to_file.isin(feats.path)]
w("### 1.8 Source code, features and metric cross-check\n")
w(f"- {smp.id.isin(ann.sample_id).sum() - len(miss_ann):,} of {ann.sample_id.nunique():,} annotated `sample` rows have their file in `files.zip`. "
  f"The {len(miss_ann)} missing are {', '.join(miss_ann.path_to_file)}. These snippets have no computed features and drop out of feature-based analyses.")
w("- Feature extraction (`src/features.py`): " + open(os.path.join(LOG, "features.log")).read().split("\n")[0].rsplit(";", 1)[0] + ".")
lz = pd.read_csv(os.path.join(LOG, "lizard_crosscheck.csv"))
w(f"- Lizard 1.17.13 cross-check on {len(lz):,} DACOS method snippets that lizard parsed:")
w(f"  - cc matches DesigniteJava exactly for {np.mean(lz.cc_designite == lz.cc_lizard):.3f} of snippets (Spearman {lz.cc_designite.corr(lz.cc_lizard, method='spearman'):.3f}).")
w(f"  - Parameter count matches exactly for {np.mean(lz.pc_designite == lz.pc_lizard):.3f} (Spearman {lz.pc_designite.corr(lz.pc_lizard, method='spearman'):.3f}).")
w("  - The stored DesigniteJava values are used throughout.\n")

# ---------------------------------------------------------------- eligibility
rows = []
for s in SMELLS:
    for lab, LL in (("primary (filtered)", primary_filter(L)), ("unfiltered", L)):
        E = entity_labels(LL[LL.smell == s])
        un = E[E.unanimous]
        vc = un.label.value_counts()
        minority = int(min(vc.get("smelly", 0), vc.get("benign", 0)))
        rows.append({"smell": s, "annotation_set": lab, "entities_ge2_usable": len(E),
                     "unanimous_smelly": int(vc.get("smelly", 0)), "unanimous_benign": int(vc.get("benign", 0)),
                     "split": int((~E.unanimous).sum()), "ties": int((E.label == "tie").sum()),
                     "minority_unanimous": minority,
                     "eligible_for_models": (len(E) >= 150 and minority >= 30) if lab.startswith("primary") else ""})
EL = pd.DataFrame(rows)
EL.to_csv(os.path.join(TAB, "eligibility.csv"), index=False)
dropped = []
for s in SMELLS:
    before = L[L.smell == s].entity.nunique()
    after = len(entity_labels(primary_filter(L)[lambda d: d.smell == s]))
    dropped.append(f"{s}: {before - after}")
w("### 1.9 Analysis sets after the consistency filter, and eligibility (D7a, D8)\n")
w(md_table(EL))
w("")
w(f"- Entities left with fewer than 2 usable annotations after the filter are excluded ({'; '.join(dropped)}).")
w("- Eligibility rule D8: at least 150 entities with ≥ 2 usable annotations and at least 30 unanimous entities in the minority class.")
inel = EL[(EL.annotation_set == "primary (filtered)") & (EL.eligible_for_models == False)].smell.tolist()  # noqa: E712
if inel:
    w(f"- **{', '.join(SMELL_NAME[s] for s in inel)} does not meet the rule. It is reported descriptively only (RQ1 agreement, RQ2 threshold ROC), and every model section skips it.**")
w("")

# ---------------------------------------------------------------- descriptives
E = attach_metrics(entity_labels(primary_filter(L)))
rows = []
for s in SMELLS:
    x = E[E.smell == s]
    for f in feature_cols(s):
        v = x[f]
        rows.append({"smell": s, "feature": f, "n": int(v.notna().sum()), "mean": round(v.mean(), 3),
                     "sd": round(v.std(), 3), "median": round(v.median(), 3), "q1": round(v.quantile(.25), 3),
                     "q3": round(v.quantile(.75), 3), "min": round(v.min(), 3), "max": round(v.max(), 3)})
D = pd.DataFrame(rows)
D.to_csv(os.path.join(TAB, "descriptives_features.csv"), index=False)
P = E.groupby(["smell", "project"]).size().unstack(0).fillna(0).astype(int).reindex(columns=SMELLS)
P.to_csv(os.path.join(TAB, "descriptives_projects.csv"))
desc = ["Primary analysis set: consistency-filtered annotations; entities with ≥ 2 usable annotations.\n",
        md_table(D), "", "Entities per project (primary set):\n", md_table(P, index=True), ""]
write_frag("s1_audit", "\n".join(out))
write_frag("s2_descriptives", "\n".join(desc))
print("\n".join(out))
