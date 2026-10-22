# Results: human judgment versus metric thresholds in DACOS

Pre-registered plan: `plan.md`. Plan commits, in order:
- `1cde51313c96140bae7ca6515df94f21a4ee2ac3`: Phase 0: data audit and pre-registered analysis plan
- `bd033600ab963246f69698e22f2840dd175fe3b9`: Plan amendment: PI decisions after Phase 0 audit
- `a723d8e5b96a96c4e958ec10862f0bcc712716d4`: Plan amendment: pre-register Prompt 2 robustness, Tier 2 and Step 3 analyses
- `4963a18301b024f0e22314ae23c78783b757ff2c`: Plan amendment: pre-register Prompt 3 close-out analyses
- `86b0c3f6c01de5afcfbc5e7c8a7bbd48c5408f32`: Plan amendment: pre-register Prompt 3B range-restriction analyses and B0
- `8e4003ce8b9667202a7d26528493798b6f0c7b97`: Plan amendment: pre-register Prompt 4 agreement anatomy and external B1

Scope: **all planned analyses are complete**: Tier 1, Tier 2, Step 3 (Prompt 2), Prompt 3, Prompt 3B (range restriction and external B0) and Prompt 4 (agreement anatomy and external check B1).
- **Multifaceted Abstraction is reported descriptively only** (agreement, threshold ROC, RQ5 descriptives), because it fails the D8 eligibility rule after the consistency filter. Every model section (RQ4, RQ3 models, Step 3 A–J) covers CM and LPL only.
- Every section states its **analysis type**: *primary*, *robustness*, *validity check* or *exploratory*. Numbers from different types must not be mixed when the paper is written.

Conventions:
- The "primary set" is the consistency-filtered annotations (D7), with entities that have ≥ 2 usable annotations.
- With 2 annotations per entity, majority labels with ties excluded are exactly the unanimous entities. RQ2, RQ4 and all models use those (D11).
- All CIs are 95% bootstrap percentile intervals (B = 2000, seed 20261021), resampling entities, unless stated otherwise.

## 1 Dataset audit: data loading and integrity checks

**Analysis type: descriptive audit of the published data.**

### 1.1 Loading

- The four Zenodo files match the record's MD5 checksums (plan §0).
- No MySQL server was available. Both dumps were converted to SQLite by `src/convert_sql.py`, which parses the mysqldump `INSERT` tuples byte by byte.
- Row counts: `annotation` 10,267; `sample` 99,387; `method_metrics` 110,982; `class_metrics` 14,458; DACOSX `entry` 207,605.
- The `smell` table is empty in both dumps, and so is the `repository` table in the extended dump.
- The `sample`, `method_metrics` and `class_metrics` tables are identical in the two dumps.

### 1.2 Snippet and annotation counts versus the DACOS paper (Table II)

| smell | paper_snippets | paper_annotations | sample_rows | entities | annotations |
|---|---|---|---|---|---|
| CM | 2197 | 4349 | 2275 | 2275 | 4555 |
| LPL | 1634 | 3221 | 1694 | 1694 | 3392 |
| MA | 1361 | 2697 | 1341 | 1009 | 2710 |
| Total (distinct) | 5192 | 10267 | 5115 | 4783 | 10267 |

- The annotation total matches the paper (10,267).
- The number of distinct annotated `sample` rows is 5,115, not 5,192. The paper's 5,192 equals the sum of its per-smell snippet counts.
- 195 snippets were offered for both CM and LPL, so they appear in both rows above.
- Neither the sample-row counts nor the entity counts reproduce the paper's per-smell numbers.
- The `annotation` table has no annotator identifier and no timestamp. The number of distinct annotators cannot be determined from the data; the paper reports 86.

### 1.3 Duplicate sample rows

- 332 MA classes appear as two `sample` rows with the same `designite_id`, path and metrics. That leaves 1,009 distinct MA classes instead of 1,341.
- Each copy carries 2 annotations. All 1,328 annotation ids are distinct, so these are not copied rows. The two copies' (checkbox, `is_smell`) sequences, in id order, are identical for 155 of the 332 classes.
- Following plan D3, their annotations are pooled, giving 4 annotations per class.
- No method snippet is duplicated.

### 1.4 DACOSX entries

| smellPresented | label | entries | on_methods | on_classes | granularity_consistent | consistent_metric_range |
|---|---|---|---|---|---|---|
| 1 | MA present | 1218 | 573 | 645 | 645 | lcom 0.807107–1 |
| 2 | LPL present | 223 | 172 | 51 | 172 | pc 7–15 |
| 3 | CM present | 465 | 428 | 37 | 428 | cc 11–75 |
| 4 | MA absent | 18456 | 9187 | 9269 | 9269 | lcom -1–0.395349 |
| 5 | LPL absent | 93219 | 82987 | 10232 | 82987 | pc 0–2 |
| 6 | CM absent | 94024 | 83181 | 10843 | 83181 | cc 1–3 |

- 30,923 of 207,605 entries attach a smell to the other granularity (MA codes on method snippets; CM/LPL codes on class snippets). They are excluded (D4).
  - In these entries the label does not separate the stored metric of that granularity. MA codes on methods: cc 1–12 for 'present' versus 1–31 for 'absent'. CM codes on classes: lcom -1–1 versus -1–1. LPL codes on classes: lcom -1–1 versus -1–1.
- Within the consistent entries, present and absent are separated by the stored metric, as the column `consistent_metric_range` shows.
- 157 consistent DACOSX entries are the same snippet as a DACOS snippet annotated for the same smell (CM 50, LPL 41, MA 66; all are 'present'). They are removed before any training.
- The paper's DacosX totals (CM 94,489; LPL 93,442; MA 19,674) equal the raw entry counts per smell code pair, including the cross-granularity entries.

### 1.5 Primary-metric ranges: paper Table I versus annotated data (descriptive, D10)

Set: every annotated entity (all 10,267 annotations, before the consistency filter).

| smell | metric | paper_Table_I_band | observed_annotated_min | observed_annotated_max | share_inside_Table_I_band | share_above_band | share_below_band | DesigniteJava_default |
|---|---|---|---|---|---|---|---|---|
| CM | cc | 4–7 | 5.0 | 14.0 | 0.744 | 0.256 | 0.0 | >= 8 |
| LPL | pc | 3–6 | 3.0 | 10.0 | 0.976 | 0.024 | 0.0 | >= 5 |
| MA | lcom | 0.4–0.8 | 0.402 | 1.0 | 0.935 | 0.065 | 0.0 | >= 0.8 (and NOF>=7, NOM>=7) |

- Each smell's annotated range differs from the paper's Table I band. Of 1,562 method samples with cc = 4, 1,562 are neither offered for CM annotation nor included in DACOSX for CM.
- The DesigniteJava defaults come from `ThresholdsDTO` in github.com/tushartushar/DesigniteJava (commit 3321c56). The rule is metric ≥ threshold.

### 1.6 Smell checkbox versus `is_smell` (consistency filter, D7)

- In the public Tagman source, `is_smell` is set to true when any checkbox is ticked.
- An annotation with checkbox = 1 and `is_smell` = 0 contradicts itself. Such annotations are excluded from the primary analysis.

| smell | checkbox | is_smell=0 | is_smell=1 |
|---|---|---|---|
| CM | 0 | 1426 | 116 |
| CM | 1 | 416 | 2597 |
| LPL | 0 | 1083 | 205 |
| LPL | 1 | 0 | 2104 |
| MA | 0 | 210 | 5 |
| MA | 1 | 965 | 1530 |

| smell | excluded | excluded_in_run | share_in_run |
|---|---|---|---|
| CM | 416 | 416 | 1.0 |
| LPL | 0 | 0 | n/a |
| MA | 965 | 917 | 0.95 |

- The filter removes 1,381 annotations in total. Of these, 1,333 lie inside an answer run (section 1.7).

### 1.7 Runs of identical answers

- Annotations were ordered by annotation id within each smell. Runs are maximal sequences of at least 40 identical checkbox answers (the fixed rule for R4).
- The column `log10_P_run_if_independent` gives the log10 probability of one specific run of that length, if answers were independent draws at the smell's overall yes-rate. It is a scale reference, not a test.
- The data contain no annotator or time information. They cannot show whether a run reflects one annotator's sequence or a recording artefact.

| smell | first_ann_id | last_ann_id | length | answer | smell_yes_rate | log10_P_run_if_independent |
|---|---|---|---|---|---|---|
| CM | 787 | 1364 | 63 | 1 | 0.661 | -11.3 |
| CM | 2008 | 2090 | 40 | 1 | 0.661 | -7.2 |
| CM | 3854 | 4234 | 69 | 1 | 0.661 | -12.4 |
| CM | 4605 | 5066 | 50 | 1 | 0.661 | -9.0 |
| CM | 9225 | 9396 | 170 | 1 | 0.661 | -30.5 |
| CM | 9397 | 9469 | 73 | 0 | 0.661 | -34.3 |
| CM | 9470 | 9715 | 246 | 1 | 0.661 | -44.2 |
| CM | 9932 | 11111 | 133 | 0 | 0.661 | -62.6 |
| LPL | 941 | 1261 | 55 | 1 | 0.62 | -11.4 |
| LPL | 3068 | 4724 | 305 | 0 | 0.62 | -128.3 |
| LPL | 9254 | 9709 | 41 | 0 | 0.62 | -17.2 |
| LPL | 9927 | 11063 | 1054 | 1 | 0.62 | -218.6 |
| LPL | 11067 | 12114 | 296 | 0 | 0.62 | -124.5 |
| MA | 6 | 4859 | 1474 | 1 | 0.921 | -52.9 |
| MA | 9786 | 9926 | 141 | 1 | 0.921 | -5.1 |

Run coverage per smell:

| smell | annotations | in_run | share |
|---|---|---|---|
| CM | 4555 | 844 | 0.185 |
| LPL | 3392 | 1751 | 0.516 |
| MA | 2710 | 1615 | 0.596 |

Figure: `figures/audit_answer_runs.pdf` (.png): each smell's checkbox answers against annotation id, with a centred rolling yes-rate over 50 annotations and the runs shaded.

### 1.8 Source code, features and metric cross-check

- 5,113 of 5,115 annotated `sample` rows have their file in `files.zip`. The 2 missing are /codesplit_java_class/macrozheng_mall/macrozheng_mall/com.macro.mall.portal.service.impl/PortalBrandServiceImpl.code, /codesplit_java_method/macrozheng_mall/macrozheng_mall/com.macro.mall.portal.service/PortalBrandService/productList.code. These snippets have no computed features and drop out of feature-based analyses.
- Feature extraction (`src/features.py`): paths needed: 96299; computed: 96285; missing from zip: 14; failed: 0.
- Lizard 1.17.13 cross-check on 3,491 DACOS method snippets that lizard parsed:
  - cc matches DesigniteJava exactly for 0.592 of snippets (Spearman 0.920).
  - Parameter count matches exactly for 0.957 (Spearman 0.979).
  - The stored DesigniteJava values are used throughout.

### 1.9 Analysis sets after the consistency filter, and eligibility (D7a, D8)

| smell | annotation_set | entities_ge2_usable | unanimous_smelly | unanimous_benign | split | ties | minority_unanimous | eligible_for_models |
|---|---|---|---|---|---|---|---|---|
| CM | primary (filtered) | 1860 | 1129 | 566 | 165 | 164 | 566 | True |
| CM | unfiltered | 2275 | 1301 | 565 | 409 | 407 | 565 |  |
| LPL | primary (filtered) | 1694 | 868 | 458 | 368 | 366 | 458 | True |
| LPL | unfiltered | 1694 | 868 | 458 | 368 | 366 | 458 |  |
| MA | primary (filtered) | 587 | 400 | 8 | 179 | 78 | 8 | False |
| MA | unfiltered | 1009 | 822 | 7 | 180 | 76 | 7 |  |

- Entities left with fewer than 2 usable annotations after the filter are excluded (CM: 415; LPL: 0; MA: 422).
- Eligibility rule D8: at least 150 entities with ≥ 2 usable annotations and at least 30 unanimous entities in the minority class.
- **Multifaceted Abstraction does not meet the rule. It is reported descriptively only (RQ1 agreement, RQ2 threshold ROC), and every model section skips it.**

- For MA, reading the answer from `isma` gives alpha 0.020 [-0.035, 0.077] (primary, consistency-filtered) and 0.059 [0.010, 0.113] (unfiltered, R6). Reading it from `is_smell` gives 0.561 [0.520, 0.603] (all annotations, R3).

## 2 Descriptives

Primary analysis set: consistency-filtered annotations; entities with ≥ 2 usable annotations.

| smell | feature | n | mean | sd | median | q1 | q3 | min | max |
|---|---|---|---|---|---|---|---|---|---|
| CM | cc | 1860 | 6.617 | 1.707 | 6.0 | 5.0 | 8.0 | 5.0 | 14.0 |
| CM | loc | 1860 | 26.329 | 15.797 | 24.0 | 17.0 | 34.0 | 0.0 | 107.0 |
| CM | statements | 1860 | 20.47 | 11.097 | 18.0 | 13.0 | 25.0 | 4.0 | 132.0 |
| CM | max_nesting | 1860 | 2.646 | 1.338 | 3.0 | 2.0 | 3.0 | 0.0 | 9.0 |
| CM | comment_ratio | 1860 | 0.062 | 0.104 | 0.0 | 0.0 | 0.115 | 0.0 | 0.533 |
| CM | method_calls | 1860 | 17.523 | 14.132 | 14.0 | 8.0 | 23.0 | 0.0 | 117.0 |
| LPL | pc | 1694 | 4.308 | 0.915 | 4.0 | 4.0 | 5.0 | 3.0 | 10.0 |
| LPL | loc | 1694 | 10.501 | 17.58 | 5.0 | 3.0 | 12.0 | 0.0 | 352.0 |
| LPL | statements | 1693 | 9.302 | 14.815 | 4.0 | 2.0 | 12.0 | 0.0 | 258.0 |
| LPL | max_nesting | 1693 | 0.768 | 1.278 | 0.0 | 0.0 | 1.0 | 0.0 | 7.0 |
| LPL | comment_ratio | 1693 | 0.225 | 0.335 | 0.0 | 0.0 | 0.429 | 0.0 | 0.917 |
| LPL | method_calls | 1693 | 7.991 | 13.964 | 3.0 | 0.0 | 10.0 | 0.0 | 233.0 |
| MA | lcom | 587 | 0.589 | 0.103 | 0.6 | 0.5 | 0.667 | 0.409 | 0.778 |
| MA | loc | 587 | 69.109 | 89.513 | 42.0 | 25.0 | 78.5 | 0.0 | 1082.0 |
| MA | statements | 587 | 36.622 | 53.801 | 19.0 | 11.0 | 42.5 | 3.0 | 734.0 |
| MA | max_nesting | 587 | 1.586 | 1.612 | 1.0 | 0.0 | 3.0 | 0.0 | 9.0 |
| MA | comment_ratio | 587 | 0.14 | 0.145 | 0.1 | 0.0 | 0.214 | 0.0 | 0.681 |
| MA | method_calls | 587 | 32.446 | 56.578 | 15.0 | 6.0 | 37.0 | 0.0 | 811.0 |
| MA | nom | 587 | 8.365 | 10.352 | 6.0 | 4.0 | 8.0 | 3.0 | 107.0 |
| MA | nof | 587 | 3.968 | 6.987 | 2.0 | 1.0 | 4.0 | 1.0 | 103.0 |

Entities per project (primary set):

| project | CM | LPL | MA |
|---|---|---|---|
| Blankj_AndroidUtilCode | 129 | 245 | 0 |
| MovingBlocks_Terasology | 355 | 239 | 237 |
| MyCATApache_Mycat-Server | 436 | 209 | 91 |
| alibaba_arthas | 175 | 144 | 0 |
| igniterealtime_Smack | 237 | 214 | 196 |
| kevin-wayne_algs4 | 266 | 52 | 3 |
| lettuce-io_lettuce-core | 179 | 364 | 60 |
| linlinjava_litemall | 61 | 129 | 0 |
| macrozheng_mall | 18 | 55 | 0 |
| shuzheng_zheng | 4 | 43 | 0 |

## 3 Research questions

### RQ1 Agreement

**Analysis type: primary.**

**Method.**
- Primary annotation set: consistency-filtered (D7), with entities that have ≥ 2 usable annotations.
- Percent agreement is the mean over entities of the share of agreeing annotation pairs.
- Krippendorff's alpha is nominal and computed with `krippendorff` 0.8.1. Each entity's answers fill arbitrary coder rows, because the data have no annotator ids; nominal alpha depends only on within-unit value counts.
- An independent implementation from the coincidence matrix agrees with the package to within 1e-9 for every smell.
- 95% CIs are bootstrap percentile intervals (B = 2000, resampling entities, seed 20261021).
- Per-annotator counts and yes-rates are not computable, because there are no annotator ids (D12).
- No hypothesis test is planned for RQ1. Values are read against Krippendorff's 0.667 / 0.800 benchmarks.

**Agreement per smell**

| smell | entities | annotations | yes_rate | unanimous_share | percent agreement [95% CI] | Krippendorff alpha [95% CI] |
|---|---|---|---|---|---|---|
| CM | 1860 | 3724 | 0.651 | 0.911 | 0.912 [0.898, 0.924] | 0.804 [0.774, 0.832] |
| LPL | 1694 | 3392 | 0.62 | 0.783 | 0.783 [0.764, 0.802] | 0.540 [0.498, 0.577] |
| MA | 587 | 1716 | 0.875 | 0.695 | 0.786 [0.760, 0.814] | 0.020 [-0.035, 0.077] |

**Vote-split distribution (entities)**

| votes (yes/n) | CM | LPL | MA |
|---|---|---|---|
| 0/2 | 566 | 458 | 8 |
| 1/2 | 164 | 366 | 62 |
| 2/2 | 1128 | 868 | 217 |
| 1/3 | 0 | 1 | 2 |
| 2/3 | 0 | 0 | 11 |
| 3/3 | 1 | 0 | 45 |
| 1/4 | 0 | 0 | 1 |
| 2/4 | 0 | 0 | 16 |
| 3/4 | 0 | 0 | 87 |
| 4/4 | 0 | 0 | 138 |
| 1/5 | 0 | 1 | 0 |
| 2/5 | 1 | 0 | 0 |

Tables: `tables/rq1_agreement.csv`, `tables/rq1_vote_splits.csv`. Figure: `figures/rq1_vote_splits.pdf` (.png).

**Summary.** CM alpha = 0.804 [0.774, 0.832], percent agreement = 0.912; LPL alpha = 0.540 [0.498, 0.577], percent agreement = 0.783; MA alpha = 0.020 [-0.035, 0.077], percent agreement = 0.786.

### RQ2 Threshold validity in the borderline band

**Analysis type: primary** (MA descriptive only).

**Method.**
- Data: consistency-filtered annotations, unanimous entities only. With 2 annotations, majority labels with ties excluded are exactly the unanimous entities (D11).
- Each smell's primary metric is the stored DesigniteJava value (cc, pc, lcom).
- ROC-AUC uses `sklearn.metrics.roc_auc_score`. H2a is tested with a one-sided Mann–Whitney U test (smelly > benign).
- Youden cut-off: the rule is metric ≥ c, with c taken from the observed values; the smallest c maximising J = TPR − FPR is used.
- 95% CIs are bootstrap percentile intervals (B = 2000, resampling entities, seed 20261021). Resamples with a single class were skipped (CM 0, LPL 0, MA 0).
- Precision, recall and F1 treat "smelly" as the positive class. They are evaluated at fixed cut-offs: the full-sample Youden cut-off and the DesigniteJava default.
  - Their CIs resample entities with the cut-off held fixed.
  - The Youden figures are in-sample, so they are optimistic.
- For MA, the full DesigniteJava rule (LCOM ≥ 0.8, NOF ≥ 7, NOM ≥ 7) is also reported.
- A rule that predicts no entity as smelly has undefined precision (shown as n/a); its recall and F1 are 0.
- MA is descriptive only (D8): its unanimous set has 8 benign entities, so its CIs are wide.

**Discrimination and cut-offs**

| smell | metric | n (smelly/benign) | ROC-AUC [95% CI] | MWU U | p (one-sided, AUC>0.5) | Youden cut [95% CI] | Youden J | Designite default | default outside Youden CI | Table I band |
|---|---|---|---|---|---|---|---|---|---|---|
| CM | cc | 1695 (1129/566) | 0.541 [0.513, 0.568] | 345950 | 0.0021 | ≥ 6 [6, 9] | 0.063 | ≥ 8 | no | 4–7 |
| LPL | pc | 1326 (868/458) | 0.433 [0.409, 0.458] | 172182 | 1.0000 | ≥ 6 [3, 10] | 0.007 | ≥ 5 | no | 3–6 |
| MA | lcom | 408 (400/8) | 0.520 [0.299, 0.727] | 1662 | 0.4238 | ≥ 0.52 [0.52, 0.75] | 0.210 | ≥ 0.8 | yes | 0.4–0.8 |

**Precision, recall and F1 at each cut-off**

| smell | rule | precision [95% CI] | recall [95% CI] | F1 [95% CI] |
|---|---|---|---|---|
| CM | Youden: cc ≥ 6 | 0.687 [0.660, 0.715] | 0.683 [0.656, 0.710] | 0.685 [0.663, 0.707] |
| CM | DesigniteJava default: cc ≥ 8 | 0.701 [0.659, 0.746] | 0.270 [0.244, 0.296] | 0.390 [0.359, 0.421] |
| LPL | Youden: pc ≥ 6 | 0.719 [0.548, 0.875] | 0.026 [0.016, 0.038] | 0.051 [0.031, 0.072] |
| LPL | DesigniteJava default: pc ≥ 5 | 0.642 [0.586, 0.701] | 0.203 [0.176, 0.229] | 0.308 [0.273, 0.342] |
| MA | Youden: lcom ≥ 0.52 | 0.987 [0.971, 1.000] | 0.585 [0.537, 0.632] | 0.735 [0.696, 0.772] |
| MA | DesigniteJava default: lcom ≥ 0.8 | n/a [n/a, n/a] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| MA | DesigniteJava full MA rule: lcom ≥ 0.8 & NOF ≥ 7 & NOM ≥ 7 | n/a [n/a, n/a] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

**Share smelly by primary-metric value (unanimous entities)**

| smell | value | entities | share_smelly |
|---|---|---|---|
| CM | 5 | 573 | 0.625 |
| CM | 6 | 399 | 0.674 |
| CM | 7 | 288 | 0.684 |
| CM | 8 | 174 | 0.649 |
| CM | 9 | 133 | 0.729 |
| CM | 10 | 99 | 0.687 |
| CM | 11 | 9 | 1.0 |
| CM | 12 | 9 | 0.889 |
| CM | 13 | 8 | 0.875 |
| CM | 14 | 3 | 1.0 |
| LPL | 3 | 137 | 1.0 |
| LPL | 4 | 915 | 0.607 |
| LPL | 5 | 242 | 0.632 |
| LPL | 6 | 23 | 0.826 |
| LPL | 7 | 3 | 0.333 |
| LPL | 8 | 2 | 0.5 |
| LPL | 9 | 3 | 0.333 |
| LPL | 10 | 1 | 1.0 |
| MA | 0.4–0.5 | 171 | 0.971 |
| MA | 0.5–0.6 | 60 | 1.0 |
| MA | 0.6–0.7 | 121 | 0.992 |
| MA | 0.7–0.8 | 56 | 0.964 |

Tables: `tables/rq2_threshold_validity.csv`, `tables/rq2_share_smelly_by_metric.csv`. Figures: `figures/rq2_roc.pdf`, `figures/rq2_share_smelly_by_metric.pdf` (.png).

The positions of the paper's Table I bands relative to the annotated ranges are in section 1.5 (descriptive only, D10).

**Summary.** CM: AUC 0.541 [0.513, 0.568], Youden cut-off cc ≥ 6 [6, 9] against the default ≥ 8; LPL: AUC 0.433 [0.409, 0.458], Youden cut-off pc ≥ 6 [3, 10] against the default ≥ 5; MA: AUC 0.520 [0.299, 0.727], Youden cut-off lcom ≥ 0.52 [0.52, 0.75] against the default ≥ 0.8.

### RQ4 Extremes-to-borderline transfer

**Analysis type: primary** (CM and LPL; MA skipped under D8).

**Method.**
- Eligible smells under D8: Complex Method, Long Parameter List.
- **Multifaceted Abstraction is skipped** because it fails D8 (see section 1.9).
- **Features**: the primary metric plus the secondary features of plan §1.6. These are stored DesigniteJava loc, plus computed statements, max nesting, comment ratio and method calls.
- **Models**:
  - `StandardScaler` + `LogisticRegression(class_weight='balanced', max_iter=10000)`.
  - `RandomForestClassifier(class_weight='balanced', random_state=20261021)`.
  - All other hyperparameters are scikit-learn 1.5.2 defaults.
- **Transfer setting.**
  - Train on granularity-consistent DACOSX entries for the smell, using the full absent class with inverse-frequency weights and no subsampling (D14).
  - Same-smell DACOS overlaps are removed before training (D4).
  - Test on DACOS unanimous entities from the consistency-filtered set.
- **In-DACOS settings.** `GroupKFold(5)` and leave-one-project-out, grouped by `project_name`. Out-of-fold predictions are pooled before scoring.
- **Scoring.** Predicted class is p ≥ 0.5, and "smelly" is the positive class. ROC-AUC uses the pooled probabilities.
- **CIs.** Bootstrap percentile intervals (B = 2000, resampling DACOS test entities, seed 20261021). The same resamples are used for every setting, so differences are paired.
- **H4.** Primary test: transfer MCC − GroupKFold(5) MCC, judged by its paired bootstrap CI. The other differences are reported alongside it.
- **Caveat.** DACOSX labels are functions of the same metrics used as features, so near-perfect DACOSX in-distribution scores are expected and are not a finding. They are listed under EXPLORATORY only as a sanity check.

**Data**

| smell | features | DACOS_unanimous | DACOS_missing_features | DACOS_test_n | DACOS_smelly | DACOS_benign | DACOSX_consistent | DACOSX_overlap_removed | DACOSX_missing_features | DACOSX_train_n | DACOSX_present | DACOSX_absent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | cc, loc, statements, max_nesting, comment_ratio, method_calls | 1695 | 0 | 1695 | 1129 | 566 | 83609 | 50 | 10 | 83549 | 378 | 83171 |
| LPL | pc, loc, statements, max_nesting, comment_ratio, method_calls | 1326 | 1 | 1325 | 867 | 458 | 83159 | 41 | 8 | 83110 | 131 | 82979 |

**Performance on DACOS unanimous entities**

| smell | model | setting | n_test | F1 [95% CI] | MCC [95% CI] | ROC_AUC [95% CI] | predicted smelly share |
|---|---|---|---|---|---|---|---|
| CM | LR | transfer: DACOSX → DACOS | 1695 | 0.598 [0.573, 0.624] | 0.067 [0.021, 0.114] | 0.548 [0.519, 0.577] | 0.5 |
| CM | LR | DACOS GroupKFold(5) by project | 1695 | 0.578 [0.551, 0.604] | 0.092 [0.041, 0.137] | 0.554 [0.525, 0.582] | 0.453 |
| CM | LR | DACOS leave-one-project-out | 1695 | 0.566 [0.540, 0.592] | 0.089 [0.040, 0.136] | 0.552 [0.522, 0.580] | 0.438 |
| CM | RF | transfer: DACOSX → DACOS | 1695 | 0.390 [0.359, 0.421] | 0.044 [-0.003, 0.090] | 0.522 [0.495, 0.546] | 0.257 |
| CM | RF | DACOS GroupKFold(5) by project | 1695 | 0.745 [0.725, 0.764] | 0.018 [-0.029, 0.067] | 0.517 [0.487, 0.545] | 0.833 |
| CM | RF | DACOS leave-one-project-out | 1695 | 0.743 [0.723, 0.762] | 0.020 [-0.027, 0.067] | 0.505 [0.476, 0.533] | 0.827 |
| LPL | LR | transfer: DACOSX → DACOS | 1325 | 0.335 [0.300, 0.370] | -0.080 [-0.139, -0.023] | 0.385 [0.356, 0.417] | 0.26 |
| LPL | LR | DACOS GroupKFold(5) by project | 1325 | 0.683 [0.657, 0.708] | 0.144 [0.088, 0.198] | 0.601 [0.569, 0.634] | 0.608 |
| LPL | LR | DACOS leave-one-project-out | 1325 | 0.656 [0.629, 0.682] | 0.099 [0.044, 0.156] | 0.567 [0.532, 0.600] | 0.586 |
| LPL | RF | transfer: DACOSX → DACOS | 1325 | 0.309 [0.273, 0.345] | -0.013 [-0.070, 0.044] | 0.496 [0.470, 0.522] | 0.207 |
| LPL | RF | DACOS GroupKFold(5) by project | 1325 | 0.714 [0.690, 0.737] | 0.125 [0.069, 0.181] | 0.603 [0.570, 0.634] | 0.693 |
| LPL | RF | DACOS leave-one-project-out | 1325 | 0.715 [0.691, 0.739] | 0.127 [0.073, 0.182] | 0.605 [0.573, 0.635] | 0.696 |

**Paired differences (transfer minus in-DACOS CV)**

| smell | model | comparison | metric | difference [95% CI] | bootstrap share ≥ 0 | H4 primary test |
|---|---|---|---|---|---|---|
| CM | LR | transfer − DACOS GroupKFold(5) by project | MCC | -0.024 [-0.072, 0.024] | 0.1605 | yes |
| CM | LR | transfer − DACOS GroupKFold(5) by project | F1 | 0.020 [-0.004, 0.044] | 0.947 |  |
| CM | LR | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.006 [-0.032, 0.020] | 0.335 |  |
| CM | LR | transfer − DACOS leave-one-project-out | MCC | -0.021 [-0.069, 0.027] | 0.2 |  |
| CM | LR | transfer − DACOS leave-one-project-out | F1 | 0.032 [0.008, 0.056] | 0.9955 |  |
| CM | LR | transfer − DACOS leave-one-project-out | ROC_AUC | -0.004 [-0.029, 0.022] | 0.388 |  |
| CM | RF | transfer − DACOS GroupKFold(5) by project | MCC | 0.025 [-0.036, 0.089] | 0.7955 | yes |
| CM | RF | transfer − DACOS GroupKFold(5) by project | F1 | -0.355 [-0.388, -0.322] | 0.0 |  |
| CM | RF | transfer − DACOS GroupKFold(5) by project | ROC_AUC | 0.005 [-0.032, 0.041] | 0.6135 |  |
| CM | RF | transfer − DACOS leave-one-project-out | MCC | 0.023 [-0.036, 0.084] | 0.7765 |  |
| CM | RF | transfer − DACOS leave-one-project-out | F1 | -0.353 [-0.386, -0.321] | 0.0 |  |
| CM | RF | transfer − DACOS leave-one-project-out | ROC_AUC | 0.017 [-0.020, 0.053] | 0.8365 |  |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | MCC | -0.224 [-0.322, -0.127] | 0.0 | yes |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | F1 | -0.348 [-0.397, -0.297] | 0.0 |  |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.216 [-0.273, -0.155] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | MCC | -0.179 [-0.280, -0.079] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | F1 | -0.320 [-0.374, -0.267] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | ROC_AUC | -0.181 [-0.240, -0.121] | 0.0 |  |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | MCC | -0.138 [-0.217, -0.062] | 0.0 | yes |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | F1 | -0.405 [-0.446, -0.365] | 0.0 |  |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.107 [-0.145, -0.069] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | MCC | -0.139 [-0.215, -0.065] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | F1 | -0.407 [-0.447, -0.367] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | ROC_AUC | -0.109 [-0.147, -0.071] | 0.0 |  |

Tables: `tables/rq4_data.csv`, `tables/rq4_transfer.csv`, `tables/rq4_paired_differences.csv`, `tables/rq4_predictions.csv.gz`. Figure: `figures/rq4_transfer.pdf` (.png). Runtime 22s.

**Summary.** CM LR: transfer MCC − GroupKFold MCC = -0.024 [-0.072, 0.024]; CM RF: transfer MCC − GroupKFold MCC = 0.025 [-0.036, 0.089]; LPL LR: transfer MCC − GroupKFold MCC = -0.224 [-0.322, -0.127]; LPL RF: transfer MCC − GroupKFold MCC = -0.138 [-0.217, -0.062].

### RQ3 What drives human judgment

**Analysis type: primary.** MA is not modelled (D8).

**Method.**
- Annotation-level **GEE** (`statsmodels` 0.14.4 `GEE`): Binomial family, logit link, exchangeable working correlation, groups = entity, robust (sandwich) covariance.
- Data: consistency-filtered annotations for every entity with ≥ 2 usable annotations, unanimous and split (D11).
- Predictors: the primary metric and the §1.6 secondary features, each z-standardised over entities. ORs are per 1 SD.
- BH adjustment is within smell and model.
- VIFs are computed on the entity-level standardised design. If any non-primary VIF > 5, a reduced model drops the highest-VIF feature repeatedly (plan §4.3).
- Decision tree: depth 3, `class_weight='balanced'`, on unanimous entities, with raw (unstandardised) features.
- Entities with missing features are dropped (LPL: 1 entity).

**Model data**

| smell | model | annotations | entities | yes_rate | working_correlation | features |
|---|---|---|---|---|---|---|
| CM | full | 3724 | 1860 | 0.651 | 0.798 | cc, loc, statements, max_nesting, comment_ratio, method_calls |
| LPL | full | 3390 | 1693 | 0.62 | 0.524 | pc, loc, statements, max_nesting, comment_ratio, method_calls |

**Odds ratios per 1 SD**

| smell | model | feature | OR per SD [95% CI] | z | p | p (BH) |
|---|---|---|---|---|---|---|
| CM | full | cc | 1.074 [0.964, 1.197] | 1.3 | 0.1933 | 0.2899 |
| CM | full | loc | 1.053 [0.907, 1.224] | 0.68 | 0.4966 | 0.5960 |
| CM | full | statements | 0.995 [0.847, 1.168] | -0.06 | 0.9490 | 0.9490 |
| CM | full | max_nesting | 1.078 [0.973, 1.195] | 1.43 | 0.1521 | 0.2899 |
| CM | full | comment_ratio | 1.098 [0.996, 1.210] | 1.88 | 0.0603 | 0.1810 |
| CM | full | method_calls | 1.190 [1.027, 1.380] | 2.31 | 0.0210 | 0.1263 |
| LPL | full | pc | 0.794 [0.742, 0.849] | -6.69 | 2.18e-11 | 6.54e-11 |
| LPL | full | loc | 1.249 [1.041, 1.497] | 2.4 | 0.0164 | 0.0329 |
| LPL | full | statements | 0.938 [0.783, 1.124] | -0.69 | 0.4876 | 0.5851 |
| LPL | full | max_nesting | 0.637 [0.560, 0.724] | -6.87 | 6.24e-12 | 3.74e-11 |
| LPL | full | comment_ratio | 1.076 [0.975, 1.188] | 1.46 | 0.1452 | 0.2179 |
| LPL | full | method_calls | 0.997 [0.845, 1.176] | -0.04 | 0.9675 | 0.9675 |

**VIF**

| smell | model | cc | comment_ratio | loc | max_nesting | method_calls | pc | statements |
|---|---|---|---|---|---|---|---|---|
| CM | full | 1.38 | 1.13 | 2.42 | 1.26 | 2.32 | – | 3.1 |
| LPL | full | – | 1.15 | 4.32 | 1.96 | 3.25 | 1.03 | 4.87 |

No VIF exceeds 5, so no reduced model was fitted (plan §4.3 rule).

**Decision-tree rules** (`tables/rq3_tree_rules.txt`)

```
=== CM (Complex Method): depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1695 unanimous entities (1129 smelly / 566 benign), unstandardised features.
Leaf weights are class-weighted sample counts [benign, smelly].
|--- method_calls <= 20.500
|   |--- statements <= 17.500
|   |   |--- max_nesting <= 3.500
|   |   |   |--- weights: [377.332, 276.995] class: 0
|   |   |--- max_nesting >  3.500
|   |   |   |--- weights: [62.889, 64.557] class: 1
|   |--- statements >  17.500
|   |   |--- comment_ratio <= 0.172
|   |   |   |--- weights: [190.163, 171.151] class: 0
|   |   |--- comment_ratio >  0.172
|   |   |   |--- weights: [26.952, 40.536] class: 1
|--- method_calls >  20.500
|   |--- loc <= 27.500
|   |   |--- statements <= 16.500
|   |   |   |--- weights: [10.481, 21.769] class: 1
|   |   |--- statements >  16.500
|   |   |   |--- weights: [49.413, 36.032] class: 0
|   |--- loc >  27.500
|   |   |--- cc <= 10.500
|   |   |   |--- weights: [128.772, 221.446] class: 1
|   |   |--- cc >  10.500
|   |   |   |--- weights: [1.497, 15.013] class: 1

=== LPL (Long Parameter List): depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1325 unanimous entities (867 smelly / 458 benign), unstandardised features.
Leaf weights are class-weighted sample counts [benign, smelly].
|--- pc <= 3.500
|   |--- weights: [0.000, 103.922] class: 1
|--- pc >  3.500
|   |--- max_nesting <= 1.500
|   |   |--- statements <= 12.500
|   |   |   |--- weights: [367.413, 453.893] class: 1
|   |   |--- statements >  12.500
|   |   |   |--- weights: [56.414, 40.499] class: 0
|   |--- max_nesting >  1.500
|   |   |--- loc <= 63.000
|   |   |   |--- weights: [234.334, 51.197] class: 0
|   |   |--- loc >  63.000
|   |   |   |--- weights: [4.340, 12.990] class: 1

```

Tables: `tables/rq3_odds_ratios.csv`, `tables/rq3_vif.csv`, `tables/rq3_tree_rules.txt`. Figure: `figures/rq3_odds_ratios.pdf` (.png).

**Summary.** CM: OR per SD of cc = 1.074 [0.964, 1.197]; LPL: OR per SD of pc = 0.794 [0.742, 0.849].

### RQ5 Ambiguity

**Analysis type: primary (CM, LPL); MA descriptive.**

**Method.**
- Data: primary set, all entities with ≥ 2 usable annotations.
- Groups: unanimous (all answers equal) versus split (≥ 1 dissent). With 2 annotations, split = tie (D11).
- Test: two-sided Mann–Whitney U (`scipy` 1.13.1).
- Effect size: Cliff's delta = P(split > unanimous) − P(split < unanimous). 95% CI from a stratified bootstrap (B = 2000, resampling within groups, seed 20261021).
- The BH family is all 12 CM and LPL tests. MA tests are shown with raw p only.

| smell | analysis | feature | n_split | n_unanimous | median_split | median_unanimous | U | p | p (BH) | Cliff's delta [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| CM | primary | cc | 165 | 1695 | 6.0 | 6.0 | 139028 | 0.8993 | 0.8993 | -0.006 [-0.094, 0.086] |
| CM | primary | loc | 165 | 1695 | 24.0 | 24.0 | 141539 | 0.7960 | 0.8684 | 0.012 [-0.083, 0.106] |
| CM | primary | statements | 165 | 1695 | 17.0 | 18.0 | 134866 | 0.4500 | 0.6750 | -0.036 [-0.129, 0.063] |
| CM | primary | max_nesting | 165 | 1695 | 2.0 | 3.0 | 129632 | 0.1107 | 0.2519 | -0.073 [-0.165, 0.021] |
| CM | primary | comment_ratio | 165 | 1695 | 0.0 | 0.0 | 131444 | 0.1259 | 0.2519 | -0.060 [-0.129, 0.012] |
| CM | primary | method_calls | 165 | 1695 | 13.0 | 14.0 | 134046 | 0.3790 | 0.6497 | -0.041 [-0.124, 0.045] |
| LPL | primary | pc | 368 | 1326 | 4.0 | 4.0 | 328538 | 9.57e-34 | 1.15e-32 | 0.347 [0.294, 0.402] |
| LPL | primary | loc | 368 | 1326 | 5.0 | 5.0 | 262654 | 0.0234 | 0.0703 | 0.077 [0.011, 0.138] |
| LPL | primary | statements | 368 | 1325 | 4.0 | 5.0 | 221312 | 0.0064 | 0.0255 | -0.092 [-0.158, -0.028] |
| LPL | primary | max_nesting | 368 | 1325 | 0.0 | 0.0 | 246373 | 0.7199 | 0.8684 | 0.011 [-0.046, 0.068] |
| LPL | primary | comment_ratio | 368 | 1325 | 0.0 | 0.0 | 223998 | 0.0058 | 0.0255 | -0.081 [-0.133, -0.023] |
| LPL | primary | method_calls | 368 | 1325 | 3.0 | 3.0 | 246090 | 0.7805 | 0.8684 | 0.009 [-0.058, 0.074] |
| MA | descriptive (MA, D8; not in BH family) | lcom | 179 | 408 | 0.6 | 0.597 | 39047 | 0.1710 | n/a (MA) | 0.069 [-0.026, 0.172] |
| MA | descriptive (MA, D8; not in BH family) | loc | 179 | 408 | 34.0 | 43.0 | 32292 | 0.0256 | n/a (MA) | -0.116 [-0.219, -0.015] |
| MA | descriptive (MA, D8; not in BH family) | statements | 179 | 408 | 17.0 | 20.0 | 32742 | 0.0460 | n/a (MA) | -0.103 [-0.206, -0.002] |
| MA | descriptive (MA, D8; not in BH family) | max_nesting | 179 | 408 | 1.0 | 1.0 | 34392 | 0.2478 | n/a (MA) | -0.058 [-0.158, 0.037] |
| MA | descriptive (MA, D8; not in BH family) | comment_ratio | 179 | 408 | 0.088 | 0.104 | 35036 | 0.4296 | n/a (MA) | -0.041 [-0.137, 0.059] |
| MA | descriptive (MA, D8; not in BH family) | method_calls | 179 | 408 | 14.0 | 16.0 | 33087 | 0.0698 | n/a (MA) | -0.094 [-0.194, 0.011] |
| MA | descriptive (MA, D8; not in BH family) | nom | 179 | 408 | 5.0 | 6.0 | 33634 | 0.1234 | n/a (MA) | -0.079 [-0.188, 0.020] |
| MA | descriptive (MA, D8; not in BH family) | nof | 179 | 408 | 2.0 | 3.0 | 31283 | 0.0048 | n/a (MA) | -0.143 [-0.242, -0.041] |

Table: `tables/rq5_ambiguity.csv`. Figure: `figures/rq5_ambiguity.pdf` (.png).

**Summary.** 3 of 12 CM/LPL tests have BH p < 0.05; primary-metric deltas: CM cc -0.006 [-0.094, 0.086]; LPL pc 0.347 [0.294, 0.402].

## 4 Robustness

### 4.1 Robustness summary (R1–R7c; plan.md §4.1)

All cells are **robustness** results except the `primary` column, which repeats the primary analysis.
Definitions follow plan.md §4.1:
- **primary**: checkbox answer, consistency-filtered
- **R1**: entities with >= 3 usable annotations (MA only)
- **R2**: ties counted as smelly
- **R3**: is_smell as answer, all annotations
- **R4**: annotations inside runs removed
- **R5**: LPL pc = 3 entities removed
- **R6**: no consistency filter
- **R7c**: entities with >= 2 annotations in the same run removed

Cell format: estimate [95% bootstrap CI]; n = entities (labelled entities for RQ2/RQ4).
- Youden cut-offs are metric values (rule: metric ≥ cut-off). R1 and R2 are placed as extra columns.
- n/a means the check does not apply to that number (plan.md §4.1), or the number could not be computed. The reason is given in brackets.
- RQ4 rows use the same DACOSX-trained models in every column; only the DACOS test labels change.

| headline | smell | primary | R3 | R4 | R5 | R6 | R7c | R1 | R2 |
|---|---|---|---|---|---|---|---|---|---|
| RQ1 Krippendorff alpha | CM | 0.804 [0.774, 0.832]; n=1860 | 0.630 [0.597, 0.662]; n=2275 | 0.824 [0.792, 0.855]; n=1470 | n/a | 0.599 [0.564, 0.635]; n=2275 | 0.804 [0.777, 0.832]; n=1859 | n/a | n/a |
| RQ1 Krippendorff alpha | LPL | 0.540 [0.498, 0.577]; n=1694 | 0.489 [0.443, 0.530]; n=1694 | 0.960 [0.916, 0.991]; n=254 | 0.513 [0.466, 0.556]; n=1557 | 0.540 [0.498, 0.577]; n=1694 | 0.513 [0.469, 0.554]; n=1556 | n/a | n/a |
| RQ1 Krippendorff alpha | MA | 0.020 [-0.035, 0.077]; n=587 | 0.561 [0.520, 0.603]; n=1009 | 0.056 [-0.026, 0.141]; n=369 | n/a | 0.059 [0.010, 0.113]; n=1009 | -0.050 [-0.107, 0.012]; n=450 | -0.014 [-0.058, 0.031]; n=300 | n/a |
| RQ2 ROC-AUC (primary metric) | CM | 0.541 [0.513, 0.568]; n=1695 | 0.547 [0.522, 0.574]; n=1870 | 0.555 [0.524, 0.585]; n=1358 | n/a | 0.541 [0.515, 0.569]; n=1866 | n/a | n/a | 0.539 [0.511, 0.566]; n=1859 |
| RQ2 ROC-AUC (primary metric) | LPL | 0.433 [0.409, 0.458]; n=1326 | 0.450 [0.425, 0.474]; n=1317 | 0.577 [0.522, 0.628]; n=250 | 0.514 [0.490, 0.538]; n=1189 | 0.433 [0.409, 0.458]; n=1326 | n/a | n/a | 0.495 [0.472, 0.518]; n=1692 |
| RQ2 ROC-AUC (primary metric) | MA | 0.520 [0.299, 0.727]; n=408 | 0.474 [0.434, 0.514]; n=733 | 0.606 [0.408, 0.779]; n=250 | n/a | 0.506 [0.296, 0.717]; n=829 | n/a | n/a (single class; not computable) | 0.525 [0.301, 0.740]; n=486 |
| RQ2 Youden cut-off | CM | 6 [6, 9]; n=1695 | 6 [6, 9]; n=1870 | 6 [6, 8]; n=1358 | n/a | 6 [6, 9]; n=1866 | n/a | n/a | 6 [6, 9]; n=1859 |
| RQ2 Youden cut-off | LPL | 6 [3, 10]; n=1326 | 5 [5, 10]; n=1317 | 5 [5, 6]; n=250 | 5 [5, 6]; n=1189 | 6 [3, 10]; n=1326 | n/a | n/a | 6 [5, 6]; n=1692 |
| RQ2 Youden cut-off | MA | 0.520 [0.520, 0.750]; n=408 | 0.571 [0.417, 0.667]; n=733 | 0.520 [0.520, 0.750]; n=250 | n/a | 0.735 [0.507, 0.750]; n=829 | n/a | n/a | 0.520 [0.520, 0.750]; n=486 |
| RQ4 MCC transfer − GroupKFold (LR) | CM | -0.024 [-0.072, 0.024]; n=1695 | 0.033 [-0.010, 0.076]; n=1870 | -0.012 [-0.063, 0.037]; n=1358 | n/a | -0.011 [-0.058, 0.037]; n=1866 | n/a | n/a | -0.014 [-0.060, 0.031]; n=1859 |
| RQ4 MCC transfer − GroupKFold (LR) | LPL | -0.224 [-0.322, -0.127]; n=1325 | 0.078 [-0.008, 0.159]; n=1316 | -0.208 [-0.372, -0.062]; n=250 | -0.255 [-0.343, -0.160]; n=1189 | -0.224 [-0.322, -0.127]; n=1325 | n/a | n/a | -0.112 [-0.183, -0.037]; n=1691 |
| RQ4 MCC transfer − GroupKFold (RF) | CM | 0.025 [-0.036, 0.089]; n=1695 | 0.011 [-0.047, 0.072]; n=1870 | 0.025 [-0.044, 0.100]; n=1358 | n/a | 0.039 [-0.019, 0.101]; n=1866 | n/a | n/a | 0.052 [-0.007, 0.113]; n=1859 |
| RQ4 MCC transfer − GroupKFold (RF) | LPL | -0.138 [-0.217, -0.062]; n=1325 | 0.062 [-0.009, 0.126]; n=1316 | -0.113 [-0.274, 0.045]; n=250 | -0.062 [-0.137, 0.017]; n=1189 | -0.138 [-0.217, -0.062]; n=1325 | n/a | n/a | -0.061 [-0.127, 0.005]; n=1691 |
| RQ3 GEE OR per SD of primary metric | CM | 1.074 [0.964, 1.197]; n=1860 | 1.076 [0.984, 1.176]; n=2275 | 1.073 [0.945, 1.217]; n=1470 | n/a | 1.081 [0.988, 1.183]; n=2275 | n/a | n/a | n/a |
| RQ3 GEE OR per SD of primary metric | LPL | 0.794 [0.742, 0.849]; n=1693 | 0.794 [0.742, 0.851]; n=1693 | 2.040 [1.173, 3.550]; n=254 | 0.969 [0.907, 1.035]; n=1557 | 0.794 [0.742, 0.849]; n=1693 | n/a | n/a | n/a |
| RQ5 Cliff's delta (split − unanimous) of primary metric | CM | -0.006 [-0.094, 0.086]; n=1860; 165 split | 0.007 [-0.057, 0.067]; n=2275; 405 split | 0.009 [-0.095, 0.118]; n=1470; 112 split | n/a | -0.039 [-0.099, 0.022]; n=2275; 409 split | n/a | n/a | n/a |
| RQ5 Cliff's delta (split − unanimous) of primary metric | LPL | 0.347 [0.294, 0.402]; n=1694; 368 split | 0.316 [0.263, 0.371]; n=1694; 377 split | -0.272 [-0.328, -0.216]; n=254; 4 split | 0.271 [0.214, 0.333]; n=1557; 368 split | 0.347 [0.292, 0.401]; n=1694; 368 split | n/a | n/a | n/a |
| RQ5 features with BH p < 0.05 (of 6) | CM | 0; n=1860 | 0; n=2275 | 0; n=1470 | n/a | 0; n=2275 | n/a | n/a | n/a |
| RQ5 features with BH p < 0.05 (of 6) | LPL | 3; n=1694 | 2; n=1694 | 0; n=254 | 3; n=1557 | 3; n=1694 | n/a | n/a | n/a |

Tables: `tables/robustness_summary.csv` (this table), `tables/robustness_long.csv` (numeric). Runtime 96s.

### 4.2 R7 run anatomy (plan.md §4.2)

**Analysis type: robustness (R7, descriptive).** Method per plan.md §4.2.
- (a) Each run's annotations are taken in annotation-id order.
  - Spearman ρ of annotation id with `sample.id` and with the entity's primary metric, with their p-values.
  - Project switches along the run, compared with 2000 random permutations of the run's own order. The one-sided p is the share of permutations with ≤ the observed switches, so a small p means projects are more clustered than random order.
  - The `ALL (reference)` row applies the same statistics to the whole smell stream.
- (b) Co-location in the unfiltered stream: the share of entities with ≥ 2 annotations that have at least 2 annotations inside the same run. The null permutes annotation-to-position within smell 2000 times, keeping run positions fixed.
- (c) Alpha without co-located entities is reported in the robustness summary (column R7c).

**(a) Run anatomy**

| smell | run_id | length | answer | n_entities | n_projects | metric_median | metric_q1 | metric_q3 | rho_annid_sample_id | p_annid_sample_id | rho_annid_primary_metric | p_annid_primary_metric | project_switches | project_switches_null_mean | p_fewer_switches_than_random |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | ALL (reference) | 4555 | mixed | 2275 | 10 | 6.0 | 5.0 | 8.0 | 0.735 | 0.00e+00 | -0.1 | 1.12e-11 | 528 | 3862.084 | 5.00e-04 |
| CM | CM-0 | 63 | 1 | 62 | 3 | 6.0 | 5.0 | 8.0 | 0.963 | 1.98e-36 | -0.105 | 0.4130 | 14 | 32.508 | 5.00e-04 |
| CM | CM-1 | 40 | 1 | 40 | 1 | 7.0 | 5.0 | 9.25 | 0.437 | 0.0048 | 0.25 | 0.1192 | 0 | 0.0 | 1.0000 |
| CM | CM-2 | 69 | 1 | 69 | 1 | 7.0 | 5.0 | 8.0 | 0.977 | 1.36e-46 | 0.013 | 0.9132 | 0 | 0.0 | 1.0000 |
| CM | CM-3 | 50 | 1 | 50 | 1 | 6.0 | 5.0 | 7.0 | 0.968 | 1.33e-30 | 0.11 | 0.4471 | 0 | 0.0 | 1.0000 |
| CM | CM-4 | 170 | 1 | 170 | 5 | 6.0 | 5.0 | 8.0 | 0.992 | 4.77e-153 | 0.028 | 0.7135 | 11 | 102.07 | 5.00e-04 |
| CM | CM-5 | 73 | 0 | 73 | 1 | 7.0 | 6.0 | 8.0 | 0.984 | 3.93e-55 | -0.111 | 0.3479 | 0 | 0.0 | 1.0000 |
| CM | CM-6 | 246 | 1 | 246 | 2 | 6.0 | 5.0 | 7.0 | 0.549 | 9.74e-21 | 0.045 | 0.4840 | 73 | 121.146 | 5.00e-04 |
| CM | CM-7 | 133 | 0 | 133 | 10 | 6.0 | 5.0 | 7.0 | 0.825 | 2.49e-34 | -0.041 | 0.6369 | 21 | 105.274 | 5.00e-04 |
| LPL | ALL (reference) | 3392 | mixed | 1694 | 10 | 4.0 | 4.0 | 5.0 | 0.41 | 2.31e-137 | -0.35 | 1.27e-98 | 315 | 2938.536 | 5.00e-04 |
| LPL | LPL-0 | 55 | 1 | 54 | 3 | 5.0 | 4.0 | 6.0 | 0.854 | 1.23e-16 | 0.47 | 2.94e-04 | 3 | 21.34 | 5.00e-04 |
| LPL | LPL-1 | 305 | 0 | 305 | 5 | 4.0 | 4.0 | 6.0 | 0.532 | 1.03e-23 | 0.135 | 0.0183 | 13 | 225.641 | 5.00e-04 |
| LPL | LPL-2 | 41 | 0 | 41 | 6 | 4.0 | 4.0 | 5.0 | 0.916 | 4.47e-17 | -0.457 | 0.0027 | 11 | 28.994 | 5.00e-04 |
| LPL | LPL-3 | 1054 | 1 | 917 | 10 | 4.0 | 3.0 | 4.0 | -0.071 | 0.0206 | -0.703 | 7.02e-158 | 82 | 875.13 | 5.00e-04 |
| LPL | LPL-4 | 296 | 0 | 296 | 4 | 4.0 | 4.0 | 4.0 | 1.0 | 0.00e+00 | 0.122 | 0.0365 | 5 | 205.094 | 5.00e-04 |
| MA | ALL (reference) | 2710 | mixed | 1009 | 10 | 0.6 | 0.5 | 0.667 | 0.79 | 0.00e+00 | -0.001 | 0.9621 | 209 | 2175.887 | 5.00e-04 |
| MA | MA-0 | 1474 | 1 | 861 | 10 | 0.571 | 0.5 | 0.667 | 0.984 | 0.00e+00 | -0.008 | 0.7602 | 136 | 1237.181 | 5.00e-04 |
| MA | MA-1 | 141 | 1 | 141 | 5 | 0.6 | 0.5 | 0.667 | 0.043 | 0.6111 | 0.048 | 0.5755 | 14 | 97.61 | 5.00e-04 |

Project composition per run (counts; truncated in this table, full in the CSV):

| smell | run_id | projects |
|---|---|---|
| CM | ALL (reference) | MyCATApache_Mycat-Server 1150; MovingBlocks_Terasology 710; igniterealtime_Smack 688; alibaba_arthas 535; kevin-wayne_al |
| CM | CM-0 | linlinjava_litemall 40; macrozheng_mall 17; Blankj_AndroidUtilCode 6 |
| CM | CM-1 | alibaba_arthas 40 |
| CM | CM-2 | MyCATApache_Mycat-Server 69 |
| CM | CM-3 | MyCATApache_Mycat-Server 50 |
| CM | CM-4 | alibaba_arthas 93; Blankj_AndroidUtilCode 51; linlinjava_litemall 16; shuzheng_zheng 7; macrozheng_mall 3 |
| CM | CM-5 | MyCATApache_Mycat-Server 73 |
| CM | CM-6 | MyCATApache_Mycat-Server 139; igniterealtime_Smack 107 |
| CM | CM-7 | igniterealtime_Smack 50; MyCATApache_Mycat-Server 21; alibaba_arthas 17; Blankj_AndroidUtilCode 14; MovingBlocks_Terasol |
| LPL | ALL (reference) | lettuce-io_lettuce-core 728; Blankj_AndroidUtilCode 494; MovingBlocks_Terasology 478; igniterealtime_Smack 428; MyCATApa |
| LPL | LPL-0 | linlinjava_litemall 41; macrozheng_mall 13; Blankj_AndroidUtilCode 1 |
| LPL | LPL-1 | Blankj_AndroidUtilCode 117; linlinjava_litemall 83; macrozheng_mall 38; MyCATApache_Mycat-Server 34; alibaba_arthas 33 |
| LPL | LPL-2 | igniterealtime_Smack 17; MyCATApache_Mycat-Server 13; alibaba_arthas 5; Blankj_AndroidUtilCode 3; linlinjava_litemall 2; |
| LPL | LPL-3 | Blankj_AndroidUtilCode 297; lettuce-io_lettuce-core 230; MovingBlocks_Terasology 129; alibaba_arthas 96; igniterealtime_ |
| LPL | LPL-4 | lettuce-io_lettuce-core 121; MovingBlocks_Terasology 93; igniterealtime_Smack 53; kevin-wayne_algs4 29 |
| MA | ALL (reference) | MovingBlocks_Terasology 960; igniterealtime_Smack 464; MyCATApache_Mycat-Server 368; alibaba_arthas 300; Blankj_AndroidU |
| MA | MA-0 | MovingBlocks_Terasology 375; alibaba_arthas 300; Blankj_AndroidUtilCode 192; igniterealtime_Smack 162; linlinjava_litema |
| MA | MA-1 | MovingBlocks_Terasology 57; igniterealtime_Smack 46; lettuce-io_lettuce-core 24; MyCATApache_Mycat-Server 13; kevin-wayn |

Share of each LPL run's annotations on the pc = 3 entities with an empty `smells` field:

| run_id | share_pc3_empty |
|---|---|
| LPL-0 | 0.0 |
| LPL-1 | 0.0 |
| LPL-2 | 0.0 |
| LPL-3 | 0.26 |
| LPL-4 | 0.0 |

**(b) Co-location of an entity's annotations within runs**

| smell | entities_ge2_annotations | observed_colocated | observed_share | null_mean_share | null_q025 | null_q975 | p_one_sided | annotations_in_runs_share |
|---|---|---|---|---|---|---|---|---|
| CM | 2275 | 1 | 0.0 | 0.006 | 0.003 | 0.009 | 1.0000 | 0.185 |
| LPL | 1694 | 138 | 0.081 | 0.113 | 0.101 | 0.125 | 1.0000 | 0.516 |
| MA | 1009 | 585 | 0.58 | 0.453 | 0.435 | 0.47 | 5.00e-04 | 0.596 |

Tables: `tables/run_anatomy.csv`, `tables/run_colocation.csv`. Figure: `figures/run_anatomy.pdf` (.png).

**Summary.** Share of entities with ≥ 2 annotations inside the same run: CM: observed 0.000 versus null mean 0.006 (p = 1.0000); LPL: observed 0.081 versus null mean 0.113 (p = 1.0000); MA: observed 0.580 versus null mean 0.453 (p = 5.00e-04).

### 4.3 J Sensitivity of the best model to training labels (R4, R6)

**Analysis type: robustness (sensitivity; replaces annotator removal, which is impossible without annotator ids).**

**Method.**
- The section-B protocol (nested tuning, 25 splits) for the best model, with training labels from R4 (run annotations removed) or R6 (no consistency filter).
- Paired comparison: the variant-trained model and the primary model are evaluated on the same primary unanimous test entities. Δ = variant − primary, with a paired bootstrap CI.
- Unpaired: each variant is also evaluated on its own unanimous labels (own 5 × 5 project splits).

| smell | model | training labels | variant unanimous n | paired: macro-F1 (primary → variant) | Δ macro-F1 [95% CI] | paired: MCC (primary → variant) | Δ MCC [95% CI] | own labels macro-F1 [95% CI] | own labels MCC [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| CM | LR | R4 | 1358 | 0.525 → 0.526 | 0.002 [-0.010, 0.012] | 0.095 → 0.089 | -0.006 [-0.030, 0.016] | 0.510 [0.486, 0.536] | 0.095 [0.049, 0.146] |
| CM | LR | R6 | 1866 | 0.525 → 0.524 | -0.001 [-0.009, 0.007] | 0.095 → 0.084 | -0.011 [-0.028, 0.005] | 0.512 [0.492, 0.532] | 0.076 [0.038, 0.118] |
| LPL | GB | R4 | 250 | 0.616 → 0.570 | -0.046 [-0.069, -0.023] | 0.232 → 0.153 | -0.079 [-0.124, -0.034] | 0.633 [0.571, 0.695] | 0.267 [0.145, 0.395] |
| LPL | GB | R6 | 1325 | 0.616 → 0.616 | 0.000 [0.000, 0.000] | 0.232 → 0.232 | 0.000 [0.000, 0.000] | 0.616 [0.591, 0.638] | 0.232 [0.184, 0.278] |

Table: `tables/sensitivity.csv`. Runtime G+I+J 55s.

### 4.4 LPL Step 3 without the pc = 3 block (R5; plan.md §5.1)

**Analysis type: robustness (R5 applied to Step 3).** LPL only. plan.md §5.1.

**Method.**
- The 137 pc = 3 entities with an empty `smells` field are removed from training and test. This leaves 1189 unanimous entities (731 smelly).
- Everything else is identical to the primary Step 3 run: the same code, grids, nested tuning and seeds. The 25 splits have the same project-to-fold assignment (asserted).
- In each table the primary column repeats the primary result; the R5 column is new.

**A and B: baselines and five-model comparison** (mean ± SD not shown; cells are repeat-mean [95% CI])

| section | model/baseline | metric | primary | R5 |
|---|---|---|---|---|
| A baselines | majority class | macro_F1 | 0.396 [0.386, 0.405] | 0.381 [0.370, 0.391] |
| A baselines | majority class | MCC | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| A baselines | majority class | ROC_AUC | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| A baselines | majority class | PR_AUC | 0.654 [0.629, 0.680] | 0.615 [0.587, 0.642] |
| A baselines | DesigniteJava default rule | macro_F1 | 0.393 [0.367, 0.420] | 0.437 [0.410, 0.465] |
| A baselines | DesigniteJava default rule | MCC | -0.013 [-0.070, 0.044] | 0.031 [-0.024, 0.085] |
| A baselines | DesigniteJava default rule | ROC_AUC | 0.434 [0.409, 0.459] | 0.514 [0.490, 0.538] |
| A baselines | DesigniteJava default rule | PR_AUC | 0.628 [0.599, 0.658] | 0.623 [0.594, 0.653] |
| A baselines | Youden rule (fitted in training fold) | macro_F1 | 0.285 [0.268, 0.301] | 0.388 [0.364, 0.413] |
| A baselines | Youden rule (fitted in training fold) | MCC | -0.053 [-0.098, -0.008] | -0.019 [-0.073, 0.033] |
| A baselines | Youden rule (fitted in training fold) | ROC_AUC | 0.434 [0.409, 0.459] | 0.514 [0.490, 0.538] |
| A baselines | Youden rule (fitted in training fold) | PR_AUC | 0.628 [0.599, 0.658] | 0.623 [0.594, 0.653] |
| B models | LR | macro_F1 | 0.569 [0.542, 0.596] | 0.609 [0.583, 0.635] |
| B models | LR | MCC | 0.141 [0.088, 0.194] | 0.219 [0.167, 0.272] |
| B models | LR | ROC_AUC | 0.590 [0.557, 0.622] | 0.639 [0.606, 0.671] |
| B models | LR | PR_AUC | 0.710 [0.675, 0.746] | 0.699 [0.663, 0.738] |
| B models | RF | macro_F1 | 0.614 [0.590, 0.638] | 0.616 [0.589, 0.640] |
| B models | RF | MCC | 0.230 [0.182, 0.277] | 0.246 [0.194, 0.294] |
| B models | RF | ROC_AUC | 0.649 [0.619, 0.679] | 0.622 [0.589, 0.654] |
| B models | RF | PR_AUC | 0.763 [0.734, 0.794] | 0.673 [0.637, 0.711] |
| B models | XGB | macro_F1 | 0.607 [0.583, 0.630] | 0.606 [0.580, 0.632] |
| B models | XGB | MCC | 0.216 [0.169, 0.263] | 0.222 [0.170, 0.272] |
| B models | XGB | ROC_AUC | 0.675 [0.645, 0.704] | 0.628 [0.596, 0.659] |
| B models | XGB | PR_AUC | 0.796 [0.770, 0.822] | 0.683 [0.646, 0.721] |
| B models | GB | macro_F1 | 0.616 [0.591, 0.638] | 0.603 [0.577, 0.629] |
| B models | GB | MCC | 0.232 [0.184, 0.278] | 0.219 [0.169, 0.268] |
| B models | GB | ROC_AUC | 0.675 [0.646, 0.704] | 0.620 [0.587, 0.652] |
| B models | GB | PR_AUC | 0.796 [0.770, 0.822] | 0.680 [0.644, 0.719] |
| B models | SVM | macro_F1 | 0.612 [0.588, 0.637] | 0.619 [0.589, 0.645] |
| B models | SVM | MCC | 0.229 [0.182, 0.278] | 0.269 [0.213, 0.321] |
| B models | SVM | ROC_AUC | 0.631 [0.600, 0.662] | 0.642 [0.610, 0.672] |
| B models | SVM | PR_AUC | 0.727 [0.693, 0.761] | 0.704 [0.668, 0.742] |

**B: Friedman/Nemenyi and best model**

| statistic | primary | R5 |
|---|---|---|
| Friedman χ² | 12.882 | 20.453 |
| Friedman p | 0.0119 | 4.06e-04 |
| Nemenyi CD | 1.220 | 1.220 |
| mean rank LR | 3.92 | 3.40 |
| mean rank RF | 2.50 | 3.00 |
| mean rank XGB | 3.14 | 3.68 |
| mean rank GB | 2.80 | 3.10 |
| mean rank SVM | 2.64 | 1.82 |
| best model (MCC rule) | GB | SVM |
| best tree model | GB | RF |

Pairs with |Δ rank| > CD: primary LR vs RF, LR vs SVM; R5 LR vs SVM, XGB vs SVM, GB vs SVM.
Figure: `figures/model_cd_diagram_LPL_R5.pdf`.

**C1 and C3** (hyperparameters reused from the respective B run; Δ is versus (v) with a paired bootstrap CI)

| model | variant | primary | R5 |
|---|---|---|---|
| GB | (i) primary only | MCC 0.206; Δ MCC -0.027 [-0.082, 0.029] | n/a (not the best model of this run) |
| GB | (v) all features | reference | n/a (not the best model of this run) |
| GB | DACOS only (= v) | reference | n/a (not the best model of this run) |
| GB | DACOSX only | MCC -0.013; Δ MCC -0.245 [-0.325, -0.169] | n/a (not the best model of this run) |
| GB | DACOSX + DACOS | MCC -0.021; Δ MCC -0.253 [-0.300, -0.197] | n/a (not the best model of this run) |
| GB | DACOSX only, primary metric removed | MCC -0.163; Δ MCC -0.396 [-0.479, -0.314] | n/a (not the best model of this run) |
| LR | (i) primary only | MCC -0.055; Δ MCC -0.196 [-0.251, -0.142] | MCC -0.024; Δ MCC -0.243 [-0.316, -0.173] |
| LR | (v) all features | reference | reference |
| LR | DACOS only (= v) | reference | reference |
| LR | DACOSX only | MCC -0.056; Δ MCC -0.196 [-0.290, -0.104] | MCC 0.002; Δ MCC -0.217 [-0.299, -0.135] |
| LR | DACOSX + DACOS | MCC -0.088; Δ MCC -0.229 [-0.282, -0.175] | MCC 0.000; Δ MCC -0.219 [-0.272, -0.167] |
| LR | DACOSX only, primary metric removed | MCC -0.195; Δ MCC -0.336 [-0.430, -0.248] | MCC -0.182; Δ MCC -0.401 [-0.493, -0.309] |
| SVM | (i) primary only | n/a (not the best model of this run) | MCC -0.009; Δ MCC -0.278 [-0.339, -0.214] |
| SVM | (v) all features | n/a (not the best model of this run) | reference |
| SVM | DACOS only (= v) | n/a (not the best model of this run) | reference |
| SVM | DACOSX only | n/a (not the best model of this run) | MCC 0.046; Δ MCC -0.223 [-0.296, -0.150] |
| SVM | DACOSX + DACOS | n/a (not the best model of this run) | MCC 0.004; Δ MCC -0.265 [-0.318, -0.208] |
| SVM | DACOSX only, primary metric removed | n/a (not the best model of this run) | MCC -0.106; Δ MCC -0.375 [-0.452, -0.293] |

**RQ3 GEE** (annotation level, all features; R5: 3118 annotations, 1557 entities, working correlation 0.495). No R5 VIF exceeds 5.

| feature | primary OR per SD [95% CI] | primary p (BH) | R5 OR per SD [95% CI] | R5 p (BH) | R5 VIF |
|---|---|---|---|---|---|
| pc | 0.794 [0.742, 0.849] | 6.54e-11 | 0.969 [0.907, 1.035] | 0.4154 | 1.03 |
| loc | 1.249 [1.041, 1.497] | 0.0329 | 1.415 [1.143, 1.752] | 0.0044 | 4.76 |
| statements | 0.938 [0.783, 1.124] | 0.5851 | 0.899 [0.742, 1.089] | 0.4153 | 4.87 |
| max_nesting | 0.637 [0.560, 0.724] | 3.74e-11 | 0.597 [0.519, 0.688] | 4.02e-12 | 1.99 |
| comment_ratio | 1.076 [0.975, 1.188] | 0.2179 | 1.101 [0.997, 1.217] | 0.1172 | 1.16 |
| method_calls | 0.997 [0.845, 1.176] | 0.9675 | 0.983 [0.825, 1.170] | 0.8438 | 3.34 |

```
=== LPL R5: depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1189 unanimous entities (731 smelly / 458 benign).
|--- max_nesting <= 1.500
|   |--- statements <= 12.500
|   |   |--- pc <= 4.500
|   |   |   |--- weights: [273.885, 372.477] class: 1
|   |   |--- pc >  4.500
|   |   |   |--- weights: [55.816, 110.605] class: 1
|   |--- statements >  12.500
|   |   |--- method_calls <= 15.500
|   |   |   |--- weights: [29.855, 13.826] class: 0
|   |   |--- method_calls >  15.500
|   |   |   |--- weights: [20.769, 29.278] class: 1
|--- max_nesting >  1.500
|   |--- loc <= 58.500
|   |   |--- loc <= 20.500
|   |   |   |--- weights: [75.286, 32.531] class: 0
|   |   |--- loc >  20.500
|   |   |   |--- weights: [132.400, 19.518] class: 0
|   |--- loc >  58.500
|   |   |--- method_calls <= 32.500
|   |   |   |--- weights: [0.000, 6.506] class: 1
|   |   |--- method_calls >  32.500
|   |   |   |--- weights: [6.490, 9.759] class: 1

```

**D: LOPO per-project distribution** (best model of each run: primary GB, R5 SVM)

| statistic | primary | R5 |
|---|---|---|
| pooled_macro_F1 | 0.634 | 0.620 |
| pooled_MCC | 0.268 | 0.282 |
| MCC_median | 0.165 | 0.123 |
| MCC_q1 | 0.119 | 0.003 |
| MCC_q3 | 0.330 | 0.370 |
| MCC_worst | shuzheng_zheng (0.016) | linlinjava_litemall (-0.081) |
| macro_F1_median | 0.562 | 0.493 |
| projects_in_distribution | 9 | 8 |
| projects_flagged | macrozheng_mall [< 20 entities] | Blankj_AndroidUtilCode [single class]; macrozheng_mall [< 20 entities] |

**F: SHAP** (best tree model of each run). Figures: `figures/shap_summary_LPL_R5.pdf`, `figures/shap_dependence_LPL_R5.pdf`.

| feature | primary mean |SHAP| (GB) | primary rank | R5 mean |SHAP| (RF) | R5 rank |
|---|---|---|---|---|
| pc | 0.6944 | 1 | 0.0107 | 6 |
| loc | 0.1806 | 4 | 0.0254 | 3 |
| statements | 0.1765 | 5 | 0.0395 | 2 |
| max_nesting | 0.3488 | 2 | 0.0536 | 1 |
| method_calls | 0.0965 | 7 | 0.0072 | 7 |
| comment_ratio | 0.1738 | 6 | 0.0206 | 5 |
| mean_identifier_length | 0.3408 | 3 | 0.0241 | 4 |

**H: learning curve** (best model of each run)

| fraction | primary macro-F1 (±SD) | R5 macro-F1 (±SD) |
|---|---|---|
| 0.1 | 0.556 ± 0.011 | 0.492 ± 0.013 |
| 0.25 | 0.604 ± 0.010 | 0.522 ± 0.020 |
| 0.5 | 0.611 ± 0.019 | 0.610 ± 0.005 |
| 0.75 | 0.608 ± 0.010 | 0.623 ± 0.003 |
| 1.0 | 0.612 ± 0.000 | 0.622 ± 0.000 |
| gain 75%→100% [95% CI]; plateaued | 0.005 [-0.007, 0.016]; True | -0.001 [-0.004, 0.003]; True |

**E: duplicate groups and label conflicts**

| duplicate type | primary | R5 |
|---|---|---|
| exact | 71 groups; 169 entities; 0 groups span >1 project; 22 groups have conflicting labels | 51 groups; 129 entities; 0 groups span >1 project; 22 groups have conflicting labels |
| near | 160 groups; 462 entities; 6 groups span >1 project; 62 groups have conflicting labels | 131 groups; 399 entities; 6 groups span >1 project; 62 groups have conflicting labels |

Tables: `tables/lpl_r5_*.csv` (side by side), `tables/model_comparison_LPL_R5.csv`, `tables/baselines_LPL_R5.csv`, `tables/ablation_LPL_R5.csv`, `tables/rq3_odds_ratios_LPL_R5.csv`, `tables/rq3_tree_rules_LPL_R5.txt`, `tables/lopo_per_project_LPL_R5.csv`. Runtime 434s.

**Summary.** R5 best model SVM, MCC 0.269 [0.213, 0.321]; primary best model GB, MCC 0.232 [0.184, 0.278].

### 4.5 Specification curves (plan.md §5.3)

**Analysis type: robustness summary (figures; no new tests).** plan.md §5.3.

Each panel plots one headline number per smell under every applicable condition (primary in orange, robustness checks in blue), sorted by estimate, with 95% CIs.
Reference lines: alpha 0.667, AUC 0.5, MCC difference 0, MCC 0. The B best-model MCC is shown for CM (primary) and LPL (primary and R5).

| spec | smell | condition | analysis | estimate [95% CI] | reference |
|---|---|---|---|---|---|
| alpha | CM | primary | primary | 0.804 [0.774, 0.832] | 0.667 |
| alpha | LPL | primary | primary | 0.540 [0.498, 0.577] | 0.667 |
| alpha | MA | primary | primary | 0.020 [-0.035, 0.077] | 0.667 |
| alpha | MA | R1 | robustness | -0.014 [-0.058, 0.031] | 0.667 |
| alpha | CM | R3 | robustness | 0.630 [0.597, 0.662] | 0.667 |
| alpha | LPL | R3 | robustness | 0.489 [0.443, 0.530] | 0.667 |
| alpha | MA | R3 | robustness | 0.561 [0.520, 0.603] | 0.667 |
| alpha | CM | R4 | robustness | 0.824 [0.792, 0.855] | 0.667 |
| alpha | LPL | R4 | robustness | 0.960 [0.916, 0.991] | 0.667 |
| alpha | MA | R4 | robustness | 0.056 [-0.026, 0.141] | 0.667 |
| alpha | LPL | R5 | robustness | 0.513 [0.466, 0.556] | 0.667 |
| alpha | CM | R6 | robustness | 0.599 [0.564, 0.635] | 0.667 |
| alpha | LPL | R6 | robustness | 0.540 [0.498, 0.577] | 0.667 |
| alpha | MA | R6 | robustness | 0.059 [0.010, 0.113] | 0.667 |
| alpha | CM | R7c | robustness | 0.804 [0.777, 0.832] | 0.667 |
| alpha | LPL | R7c | robustness | 0.513 [0.469, 0.554] | 0.667 |
| alpha | MA | R7c | robustness | -0.050 [-0.107, 0.012] | 0.667 |
| auc | CM | primary | primary | 0.541 [0.513, 0.568] | 0.5 |
| auc | LPL | primary | primary | 0.433 [0.409, 0.458] | 0.5 |
| auc | MA | primary | primary | 0.520 [0.299, 0.727] | 0.5 |
| auc | CM | R2 | robustness | 0.539 [0.511, 0.566] | 0.5 |
| auc | LPL | R2 | robustness | 0.495 [0.472, 0.518] | 0.5 |
| auc | MA | R2 | robustness | 0.525 [0.301, 0.740] | 0.5 |
| auc | CM | R3 | robustness | 0.547 [0.522, 0.574] | 0.5 |
| auc | LPL | R3 | robustness | 0.450 [0.425, 0.474] | 0.5 |
| auc | MA | R3 | robustness | 0.474 [0.434, 0.514] | 0.5 |
| auc | CM | R4 | robustness | 0.555 [0.524, 0.585] | 0.5 |
| auc | LPL | R4 | robustness | 0.577 [0.522, 0.628] | 0.5 |
| auc | MA | R4 | robustness | 0.606 [0.408, 0.779] | 0.5 |
| auc | LPL | R5 | robustness | 0.514 [0.490, 0.538] | 0.5 |
| auc | CM | R6 | robustness | 0.541 [0.515, 0.569] | 0.5 |
| auc | LPL | R6 | robustness | 0.433 [0.409, 0.458] | 0.5 |
| auc | MA | R6 | robustness | 0.506 [0.296, 0.717] | 0.5 |
| rq4_LR | CM | primary | primary | -0.024 [-0.072, 0.024] | 0.0 |
| rq4_LR | LPL | primary | primary | -0.224 [-0.322, -0.127] | 0.0 |
| rq4_LR | CM | R2 | robustness | -0.014 [-0.060, 0.031] | 0.0 |
| rq4_LR | LPL | R2 | robustness | -0.112 [-0.183, -0.037] | 0.0 |
| rq4_LR | CM | R3 | robustness | 0.033 [-0.010, 0.076] | 0.0 |
| rq4_LR | LPL | R3 | robustness | 0.078 [-0.008, 0.159] | 0.0 |
| rq4_LR | CM | R4 | robustness | -0.012 [-0.063, 0.037] | 0.0 |
| rq4_LR | LPL | R4 | robustness | -0.208 [-0.372, -0.062] | 0.0 |
| rq4_LR | LPL | R5 | robustness | -0.255 [-0.343, -0.160] | 0.0 |
| rq4_LR | CM | R6 | robustness | -0.011 [-0.058, 0.037] | 0.0 |
| rq4_LR | LPL | R6 | robustness | -0.224 [-0.322, -0.127] | 0.0 |
| rq4_RF | CM | primary | primary | 0.025 [-0.036, 0.089] | 0.0 |
| rq4_RF | LPL | primary | primary | -0.138 [-0.217, -0.062] | 0.0 |
| rq4_RF | CM | R2 | robustness | 0.052 [-0.007, 0.113] | 0.0 |
| rq4_RF | LPL | R2 | robustness | -0.061 [-0.127, 0.005] | 0.0 |
| rq4_RF | CM | R3 | robustness | 0.011 [-0.047, 0.072] | 0.0 |
| rq4_RF | LPL | R3 | robustness | 0.062 [-0.009, 0.126] | 0.0 |
| rq4_RF | CM | R4 | robustness | 0.025 [-0.044, 0.100] | 0.0 |
| rq4_RF | LPL | R4 | robustness | -0.113 [-0.274, 0.045] | 0.0 |
| rq4_RF | LPL | R5 | robustness | -0.062 [-0.137, 0.017] | 0.0 |
| rq4_RF | CM | R6 | robustness | 0.039 [-0.019, 0.101] | 0.0 |
| rq4_RF | LPL | R6 | robustness | -0.138 [-0.217, -0.062] | 0.0 |
| best_mcc | CM | primary (LR) | primary | 0.095 [0.052, 0.136] | 0.0 |
| best_mcc | LPL | primary (GB) | primary | 0.232 [0.184, 0.278] | 0.0 |
| best_mcc | LPL | R5 (SVM) | robustness | 0.269 [0.213, 0.321] | 0.0 |

Table: `tables/spec_curves.csv`. Figures: `figures/spec_curve_alpha.pdf`, `spec_curve_auc.pdf`, `spec_curve_rq4_LR.pdf`, `spec_curve_rq4_RF.pdf`, `spec_curve_best_mcc.pdf` (.png).

## 5 Strengthening analyses (Step 3; CM and LPL)

### 5.1 A Baselines

**Analysis type: primary.** These baselines are reported alongside every model in sections B–J.
- Splits: the same 25 project-grouped splits as section B (5 repeats × 5 folds; projects shuffled with seed 20261021 + r and assigned round-robin).
- Majority class: the training fold's majority label is predicted for everyone. With a constant score, ROC-AUC = 0.5, PR-AUC = prevalence and MCC = 0.
- DesigniteJava rule: smelly if metric ≥ default (cc ≥ 8, pc ≥ 5). The score is the metric itself.
- Youden rule: smelly if metric ≥ c, with c chosen on the training fold only. The per-fold cut-offs are in `tables/baselines.csv`.
- Metrics: mean ± SD over the 5 repeats of pooled out-of-fold metrics. The CI is a bootstrap over entities (B = 2000) of the repeat-mean.

| smell | baseline | n | macro-F1 mean ± SD [95% CI] | MCC mean ± SD [95% CI] | ROC-AUC mean ± SD [95% CI] | PR-AUC mean ± SD [95% CI] |
|---|---|---|---|---|---|---|
| CM | majority class | 1695 | 0.400 ± 0.000 [0.392, 0.408] | 0.000 ± 0.000 [0.000, 0.000] | 0.500 ± 0.000 [0.500, 0.500] | 0.666 ± 0.000 [0.644, 0.689] |
| CM | DesigniteJava default rule | 1695 | 0.434 ± 0.000 [0.410, 0.456] | 0.044 ± 0.000 [-0.003, 0.090] | 0.541 ± 0.000 [0.513, 0.568] | 0.696 ± 0.000 [0.670, 0.725] |
| CM | Youden rule (fitted in training fold) | 1695 | 0.506 ± 0.018 [0.484, 0.527] | 0.032 ± 0.031 [-0.012, 0.074] | 0.541 ± 0.000 [0.513, 0.568] | 0.696 ± 0.000 [0.670, 0.725] |
| LPL | majority class | 1325 | 0.396 ± 0.000 [0.386, 0.405] | 0.000 ± 0.000 [0.000, 0.000] | 0.500 ± 0.000 [0.500, 0.500] | 0.654 ± 0.000 [0.629, 0.680] |
| LPL | DesigniteJava default rule | 1325 | 0.393 ± 0.000 [0.367, 0.420] | -0.013 ± 0.000 [-0.070, 0.044] | 0.434 ± 0.000 [0.409, 0.459] | 0.628 ± 0.000 [0.599, 0.658] |
| LPL | Youden rule (fitted in training fold) | 1325 | 0.285 ± 0.029 [0.268, 0.301] | -0.053 ± 0.022 [-0.098, -0.008] | 0.434 ± 0.000 [0.409, 0.459] | 0.628 ± 0.000 [0.599, 0.658] |

Table: `tables/baselines.csv`.

### 5.2 B Model comparison

**Analysis type: primary.**

**Algorithms and rationale**
- **LR**: linear, interpretable baseline; the same family as Tier 1 RQ4.
- **RF**: bagged trees; captures thresholds and interactions with little tuning; Tier 1 comparison model.
- **XGB**: regularised gradient boosting; a strong default for small tabular data.
- **GB**: scikit-learn gradient boosting; a boosting check that does not depend on the XGBoost implementation.
- **SVM**: RBF-kernel margin classifier; smooth non-linear boundaries, unlike tree splits.

**Protocol** (plan.md §4.4)
- Unanimous entities of the primary set with complete features (CM 1695, LPL 1325).
- Full feature set: cc|pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length.
- Outer CV: 5 × 5 grouped CV by project.
- Inner tuning: `GridSearchCV(GroupKFold(3) by project, scoring = MCC)` on the training fold only.
- Class imbalance: inverse-frequency class weights only (`class_weight='balanced'`; XGB `scale_pos_weight`; GB balanced sample weights).
  - No SMOTE or other synthetic oversampling: it would fabricate borderline neighbours, which is exactly the region this study examines.
- Fixed grids:
  - LR: `{'clf__C': [0.01, 0.1, 1, 10]}`
  - RF: `{'max_depth': [None, 5, 10], 'min_samples_leaf': [1, 5, 20]}`
  - XGB: `{'n_estimators': [100, 300], 'max_depth': [2, 4, 6], 'learning_rate': [0.05, 0.1]}`
  - GB: `{'n_estimators': [100, 300], 'max_depth': [2, 3], 'learning_rate': [0.05, 0.1]}`
  - SVM: `{'clf__C': [0.1, 1, 10], 'clf__gamma': ['scale', 0.01, 0.1]}`
- RF uses 300 trees and XGB `n_jobs=1`. Every model uses `random_state = 20261021 + repeat`.
- Best model = highest mean MCC.

**Results**

| smell | model | n | macro-F1 mean ± SD [95% CI] | MCC mean ± SD [95% CI] | ROC-AUC mean ± SD [95% CI] | PR-AUC mean ± SD [95% CI] | best |
|---|---|---|---|---|---|---|---|
| CM | LR | 1695 | 0.525 ± 0.010 [0.502, 0.545] | 0.095 ± 0.006 [0.052, 0.136] | 0.557 ± 0.008 [0.529, 0.583] | 0.709 ± 0.008 [0.679, 0.741] | best (MCC) |
| CM | RF | 1695 | 0.510 ± 0.004 [0.490, 0.529] | 0.029 ± 0.004 [-0.013, 0.068] | 0.523 ± 0.002 [0.497, 0.547] | 0.682 ± 0.004 [0.655, 0.711] |  |
| CM | XGB | 1695 | 0.504 ± 0.009 [0.482, 0.522] | 0.035 ± 0.022 [-0.006, 0.073] | 0.524 ± 0.010 [0.498, 0.547] | 0.691 ± 0.010 [0.662, 0.720] |  |
| CM | GB | 1695 | 0.505 ± 0.008 [0.484, 0.523] | 0.044 ± 0.021 [0.003, 0.081] | 0.527 ± 0.009 [0.502, 0.552] | 0.696 ± 0.008 [0.668, 0.725] | best tree |
| CM | SVM | 1695 | 0.494 ± 0.020 [0.471, 0.514] | 0.067 ± 0.016 [0.024, 0.107] | 0.542 ± 0.008 [0.515, 0.569] | 0.699 ± 0.009 [0.670, 0.729] |  |
| LPL | LR | 1325 | 0.569 ± 0.011 [0.542, 0.596] | 0.141 ± 0.021 [0.088, 0.194] | 0.590 ± 0.009 [0.557, 0.622] | 0.710 ± 0.004 [0.675, 0.746] |  |
| LPL | RF | 1325 | 0.614 ± 0.013 [0.590, 0.638] | 0.230 ± 0.026 [0.182, 0.277] | 0.649 ± 0.014 [0.619, 0.679] | 0.763 ± 0.021 [0.734, 0.794] |  |
| LPL | XGB | 1325 | 0.607 ± 0.010 [0.583, 0.630] | 0.216 ± 0.018 [0.169, 0.263] | 0.675 ± 0.006 [0.645, 0.704] | 0.796 ± 0.005 [0.770, 0.822] |  |
| LPL | GB | 1325 | 0.616 ± 0.007 [0.591, 0.638] | 0.232 ± 0.014 [0.184, 0.278] | 0.675 ± 0.008 [0.646, 0.704] | 0.796 ± 0.005 [0.770, 0.822] | best (MCC) |
| LPL | SVM | 1325 | 0.612 ± 0.002 [0.588, 0.637] | 0.229 ± 0.008 [0.182, 0.278] | 0.631 ± 0.006 [0.600, 0.662] | 0.727 ± 0.010 [0.693, 0.761] |  |

**Friedman test over 25 folds (fold-level MCC) and Nemenyi average ranks** (rank 1 = best). The Nemenyi CD uses q₀.₀₅ = 2.728 (k = 5).

| smell | blocks | k | friedman_chi2 | p | nemenyi_CD | avg_rank_LR | avg_rank_RF | avg_rank_XGB | avg_rank_GB | avg_rank_SVM |
|---|---|---|---|---|---|---|---|---|---|---|
| CM | 25 | 5 | 21.088 | 3.04e-04 | 1.22 | 1.96 | 3.56 | 3.76 | 3.08 | 2.64 |
| LPL | 25 | 5 | 12.882 | 0.0119 | 1.22 | 3.92 | 2.5 | 3.14 | 2.8 | 2.64 |

Pairs whose average ranks differ by more than the CD: CM: LR vs RF (|Δrank| 1.60 > CD 1.22); CM: LR vs XGB (|Δrank| 1.80 > CD 1.22); LPL: LR vs RF (|Δrank| 1.42 > CD 1.22); LPL: LR vs SVM (|Δrank| 1.28 > CD 1.22).
- All pairwise rank differences are in `tables/model_nemenyi_pairs.csv`.
- Caveat: the 25 folds come from 5 repeats of the same data, so they are not independent blocks. The test is therefore anti-conservative.

Tables: `tables/model_comparison.csv`, `tables/model_friedman.csv`, `tables/model_nemenyi_pairs.csv`, `tables/model_fold_mcc.csv`. Figure: `figures/model_cd_diagram.pdf` (.png). Runtime 103s.

**Summary.** CM: best model LR (MCC 0.095), Friedman p = 3.04e-04; LPL: best model GB (MCC 0.232), Friedman p = 0.0119.

### 5.3 C Ablation study

**Analysis type: primary.** Models: the best model from B and LR (CM: LR; LPL: GB).
Because LR is CM's best model, CM's ablation has a single model.

**Method.**
- The protocol and 25 splits are those of section B.
- Each variant **reuses the hyperparameters selected for the full model** in that outer fold; nothing is re-tuned (plan.md §4.5 C).
- Test set: always the held-out unanimous DACOS entities of the fold.
- Δ is the variant minus (v) all features, as a repeat-mean over 5 repeats. The 95% CI is a paired bootstrap over test entities (B = 2000).
- C1 feature groups:
  - primary = {cc | pc}
  - size = {loc, statements}
  - structure = {max_nesting, method_calls}
  - readability = {comment_ratio, mean_identifier_length}. Mean identifier length was computed with the existing lexer, so it is included.
- C2 training labels (test labels unchanged):
  - "ties counted as smelly" trains on unanimous entities plus ties labelled smelly. The rare non-unanimous majority entities keep their majority label.
  - "soft labels" enter each entity twice, once per class, with sample weights y/n and 1 − y/n multiplied by the class weights.
- C3 training source. DACOSX is the D4-cleaned set, with entries from the fold's held-out projects excluded so that no project is in both train and test (this restriction is a clarification of the plan). Class weights are recomputed on each training set.
- C4: class weighting switched off (no `class_weight`, `scale_pos_weight` = 1, no GB sample weights).

**Complex Method** (table `tables/ablation_CM.csv`, figure `figures/ablation_CM.pdf`)

DACOSX training pool (D4-cleaned, features complete): {'consistent_entries': 83609, 'overlap_removed': 50, 'missing_features': 10, 'missing_step3_features': 0}

| model | block | variant | macro-F1 mean ± SD [95% CI] | MCC mean ± SD [95% CI] | Δ macro-F1 [95% CI] | Δ MCC [95% CI] |
|---|---|---|---|---|---|---|
| LR | C1 feature groups | (i) primary only | 0.495 ± 0.000 [0.472, 0.518] | 0.052 ± 0.000 [0.005, 0.097] | -0.029 [-0.052, -0.006] | -0.044 [-0.090, 0.005] |
| LR | C1 feature groups | (ii) size only | 0.519 ± 0.002 [0.495, 0.541] | 0.102 ± 0.004 [0.055, 0.147] | -0.006 [-0.024, 0.012] | 0.006 [-0.031, 0.043] |
| LR | C1 feature groups | (iii) structure only | 0.509 ± 0.008 [0.485, 0.529] | 0.079 ± 0.010 [0.033, 0.123] | -0.016 [-0.033, 0.002] | -0.017 [-0.053, 0.018] |
| LR | C1 feature groups | (iv) readability only | 0.470 ± 0.019 [0.450, 0.489] | -0.023 ± 0.027 [-0.063, 0.015] | -0.055 [-0.080, -0.027] | -0.119 [-0.171, -0.062] |
| LR | C1 feature groups | (v) all features | 0.525 ± 0.010 [0.502, 0.545] | 0.095 ± 0.006 [0.052, 0.136] | reference | reference |
| LR | C1 feature groups | (vi) all − primary | 0.527 ± 0.013 [0.504, 0.548] | 0.098 ± 0.012 [0.052, 0.140] | 0.002 [-0.006, 0.010] | 0.002 [-0.014, 0.018] |
| LR | C1 feature groups | (vi) all − size | 0.527 ± 0.011 [0.504, 0.547] | 0.096 ± 0.006 [0.052, 0.138] | 0.002 [-0.007, 0.011] | 0.001 [-0.019, 0.020] |
| LR | C1 feature groups | (vi) all − structure | 0.518 ± 0.012 [0.494, 0.539] | 0.079 ± 0.020 [0.034, 0.122] | -0.007 [-0.021, 0.008] | -0.016 [-0.046, 0.015] |
| LR | C1 feature groups | (vi) all − readability | 0.512 ± 0.004 [0.489, 0.533] | 0.086 ± 0.010 [0.040, 0.127] | -0.012 [-0.027, 0.002] | -0.010 [-0.039, 0.019] |
| LR | C2 label aggregation | unanimous only (= v) | 0.525 ± 0.010 [0.502, 0.545] | 0.095 ± 0.006 [0.052, 0.136] | reference | reference |
| LR | C2 label aggregation | ties counted as smelly | 0.525 ± 0.006 [0.501, 0.545] | 0.086 ± 0.007 [0.040, 0.127] | 0.000 [-0.007, 0.007] | -0.009 [-0.023, 0.004] |
| LR | C2 label aggregation | soft labels (y/n) as sample weights | 0.538 ± 0.011 [0.516, 0.559] | 0.091 ± 0.016 [0.048, 0.134] | 0.014 [0.003, 0.023] | -0.004 [-0.024, 0.014] |
| LR | C3 training source | DACOS only (= v) | 0.525 ± 0.010 [0.502, 0.545] | 0.095 ± 0.006 [0.052, 0.136] | reference | reference |
| LR | C3 training source | DACOSX only | 0.505 ± 0.003 [0.482, 0.528] | 0.054 ± 0.008 [0.009, 0.102] | -0.019 [-0.041, 0.002] | -0.041 [-0.086, 0.003] |
| LR | C3 training source | DACOSX + DACOS | 0.400 ± 0.000 [0.392, 0.408] | 0.000 ± 0.000 [0.000, 0.000] | -0.125 [-0.148, -0.099] | -0.095 [-0.136, -0.052] |
| LR | C3 training source | DACOSX only, primary metric removed | 0.514 ± 0.005 [0.492, 0.537] | 0.044 ± 0.009 [-0.001, 0.091] | -0.011 [-0.039, 0.018] | -0.052 [-0.107, 0.003] |
| LR | C4 class weighting | weights on (= v) | 0.525 ± 0.010 [0.502, 0.545] | 0.095 ± 0.006 [0.052, 0.136] | reference | reference |
| LR | C4 class weighting | weights off | 0.406 ± 0.006 [0.397, 0.416] | 0.005 ± 0.017 [-0.027, 0.037] | -0.118 [-0.142, -0.092] | -0.090 [-0.142, -0.041] |

**Long Parameter List** (table `tables/ablation_LPL.csv`, figure `figures/ablation_LPL.pdf`)

DACOSX training pool (D4-cleaned, features complete): {'consistent_entries': 83159, 'overlap_removed': 41, 'missing_features': 8, 'missing_step3_features': 0}

| model | block | variant | macro-F1 mean ± SD [95% CI] | MCC mean ± SD [95% CI] | Δ macro-F1 [95% CI] | Δ MCC [95% CI] |
|---|---|---|---|---|---|---|
| GB | C1 feature groups | (i) primary only | 0.438 ± 0.012 [0.413, 0.462] | 0.206 ± 0.055 [0.174, 0.235] | -0.178 [-0.209, -0.145] | -0.027 [-0.082, 0.029] |
| GB | C1 feature groups | (ii) size only | 0.616 ± 0.006 [0.590, 0.642] | 0.247 ± 0.011 [0.197, 0.298] | 0.000 [-0.021, 0.024] | 0.014 [-0.029, 0.061] |
| GB | C1 feature groups | (iii) structure only | 0.611 ± 0.003 [0.584, 0.639] | 0.249 ± 0.007 [0.198, 0.303] | -0.005 [-0.026, 0.018] | 0.017 [-0.026, 0.060] |
| GB | C1 feature groups | (iv) readability only | 0.522 ± 0.010 [0.498, 0.545] | 0.068 ± 0.028 [0.022, 0.115] | -0.094 [-0.119, -0.069] | -0.164 [-0.213, -0.115] |
| GB | C1 feature groups | (v) all features | 0.616 ± 0.007 [0.591, 0.638] | 0.232 ± 0.014 [0.184, 0.278] | reference | reference |
| GB | C1 feature groups | (vi) all − primary | 0.610 ± 0.007 [0.584, 0.635] | 0.227 ± 0.014 [0.175, 0.276] | -0.006 [-0.019, 0.009] | -0.005 [-0.032, 0.023] |
| GB | C1 feature groups | (vi) all − size | 0.610 ± 0.010 [0.586, 0.634] | 0.223 ± 0.014 [0.176, 0.272] | -0.005 [-0.019, 0.007] | -0.009 [-0.036, 0.017] |
| GB | C1 feature groups | (vi) all − structure | 0.612 ± 0.006 [0.587, 0.634] | 0.226 ± 0.012 [0.177, 0.271] | -0.004 [-0.016, 0.008] | -0.007 [-0.032, 0.018] |
| GB | C1 feature groups | (vi) all − readability | 0.610 ± 0.020 [0.586, 0.633] | 0.224 ± 0.039 [0.176, 0.272] | -0.006 [-0.023, 0.014] | -0.009 [-0.044, 0.030] |
| GB | C2 label aggregation | unanimous only (= v) | 0.616 ± 0.007 [0.591, 0.638] | 0.232 ± 0.014 [0.184, 0.278] | reference | reference |
| GB | C2 label aggregation | ties counted as smelly | 0.634 ± 0.008 [0.608, 0.657] | 0.268 ± 0.016 [0.218, 0.316] | 0.018 [0.007, 0.029] | 0.036 [0.014, 0.057] |
| GB | C2 label aggregation | soft labels (y/n) as sample weights | 0.613 ± 0.006 [0.589, 0.636] | 0.228 ± 0.013 [0.179, 0.274] | -0.002 [-0.013, 0.009] | -0.004 [-0.026, 0.018] |
| GB | C3 training source | DACOS only (= v) | 0.616 ± 0.007 [0.591, 0.638] | 0.232 ± 0.014 [0.184, 0.278] | reference | reference |
| GB | C3 training source | DACOSX only | 0.393 ± 0.000 [0.367, 0.420] | -0.013 ± 0.000 [-0.070, 0.044] | -0.223 [-0.259, -0.186] | -0.245 [-0.325, -0.169] |
| GB | C3 training source | DACOSX + DACOS | 0.396 ± 0.001 [0.387, 0.406] | -0.021 ± 0.010 [-0.040, 0.009] | -0.219 [-0.244, -0.192] | -0.253 [-0.300, -0.197] |
| GB | C3 training source | DACOSX only, primary metric removed | 0.392 ± 0.005 [0.368, 0.416] | -0.163 ± 0.017 [-0.215, -0.115] | -0.223 [-0.263, -0.184] | -0.396 [-0.479, -0.314] |
| GB | C4 class weighting | weights on (= v) | 0.616 ± 0.007 [0.591, 0.638] | 0.232 ± 0.014 [0.184, 0.278] | reference | reference |
| GB | C4 class weighting | weights off | 0.607 ± 0.009 [0.581, 0.635] | 0.281 ± 0.017 [0.233, 0.331] | -0.008 [-0.028, 0.013] | 0.049 [0.011, 0.088] |
| LR | C1 feature groups | (i) primary only | 0.470 ± 0.015 [0.446, 0.494] | -0.055 ± 0.040 [-0.101, -0.006] | -0.100 [-0.127, -0.073] | -0.196 [-0.251, -0.142] |
| LR | C1 feature groups | (ii) size only | 0.606 ± 0.007 [0.579, 0.632] | 0.219 ± 0.013 [0.165, 0.271] | 0.037 [0.012, 0.063] | 0.078 [0.029, 0.130] |
| LR | C1 feature groups | (iii) structure only | 0.596 ± 0.006 [0.571, 0.623] | 0.193 ± 0.012 [0.141, 0.247] | 0.027 [0.008, 0.047] | 0.052 [0.014, 0.090] |
| LR | C1 feature groups | (iv) readability only | 0.545 ± 0.004 [0.518, 0.570] | 0.130 ± 0.009 [0.078, 0.179] | -0.024 [-0.051, 0.004] | -0.011 [-0.064, 0.045] |
| LR | C1 feature groups | (v) all features | 0.569 ± 0.011 [0.542, 0.596] | 0.141 ± 0.021 [0.088, 0.194] | reference | reference |
| LR | C1 feature groups | (vi) all − primary | 0.602 ± 0.003 [0.576, 0.628] | 0.204 ± 0.007 [0.152, 0.256] | 0.033 [0.019, 0.046] | 0.063 [0.037, 0.090] |
| LR | C1 feature groups | (vi) all − size | 0.571 ± 0.012 [0.544, 0.596] | 0.144 ± 0.023 [0.089, 0.195] | 0.001 [-0.004, 0.007] | 0.003 [-0.009, 0.013] |
| LR | C1 feature groups | (vi) all − structure | 0.536 ± 0.016 [0.511, 0.561] | 0.095 ± 0.028 [0.043, 0.146] | -0.033 [-0.052, -0.013] | -0.045 [-0.084, -0.006] |
| LR | C1 feature groups | (vi) all − readability | 0.572 ± 0.007 [0.547, 0.598] | 0.146 ± 0.014 [0.095, 0.198] | 0.003 [-0.012, 0.018] | 0.005 [-0.024, 0.034] |
| LR | C2 label aggregation | unanimous only (= v) | 0.569 ± 0.011 [0.542, 0.596] | 0.141 ± 0.021 [0.088, 0.194] | reference | reference |
| LR | C2 label aggregation | ties counted as smelly | 0.558 ± 0.010 [0.533, 0.582] | 0.120 ± 0.019 [0.070, 0.168] | -0.011 [-0.030, 0.006] | -0.021 [-0.057, 0.012] |
| LR | C2 label aggregation | soft labels (y/n) as sample weights | 0.594 ± 0.007 [0.568, 0.619] | 0.193 ± 0.015 [0.143, 0.244] | 0.024 [0.011, 0.039] | 0.052 [0.026, 0.080] |
| LR | C3 training source | DACOS only (= v) | 0.569 ± 0.011 [0.542, 0.596] | 0.141 ± 0.021 [0.088, 0.194] | reference | reference |
| LR | C3 training source | DACOSX only | 0.401 ± 0.003 [0.376, 0.426] | -0.056 ± 0.044 [-0.109, -0.003] | -0.168 [-0.211, -0.125] | -0.196 [-0.290, -0.104] |
| LR | C3 training source | DACOSX + DACOS | 0.390 ± 0.004 [0.380, 0.399] | -0.088 ± 0.031 [-0.104, -0.070] | -0.179 [-0.207, -0.151] | -0.229 [-0.282, -0.175] |
| LR | C3 training source | DACOSX only, primary metric removed | 0.370 ± 0.006 [0.345, 0.395] | -0.195 ± 0.010 [-0.249, -0.144] | -0.199 [-0.244, -0.157] | -0.336 [-0.430, -0.248] |
| LR | C4 class weighting | weights on (= v) | 0.569 ± 0.011 [0.542, 0.596] | 0.141 ± 0.021 [0.088, 0.194] | reference | reference |
| LR | C4 class weighting | weights off | 0.528 ± 0.017 [0.503, 0.554] | 0.147 ± 0.017 [0.098, 0.197] | -0.041 [-0.067, -0.014] | 0.006 [-0.043, 0.056] |

Runtime 156s.

### 5.4 D Generalisation

**Analysis type: primary (generalisation).**

**Method.**
- Leave-one-project-out (LOPO) with the best model and LR:
  - nested tuning with inner `GroupKFold(3)` by project on the 9 training projects;
  - full Step 3 features, seed 20261021.
- Per-project scores are also computed from the Tier 1 LOPO predictions (LR and RF with default hyperparameters and the Tier 1 feature set).
- Projects with fewer than 20 test entities, or a single class, are flagged and excluded from the median, IQR and worst project. MCC and ROC-AUC are undefined for single-class projects. Pooled scores use every project.
- Cross-smell transfer:
  - The source smell's best model is tuned with `GridSearchCV(GroupKFold(5) by project)` on the source unanimous entities, then fitted on all of them.
  - It is tested on the target smell's unanimous entities, minus the entities annotated for both smells.
  - Method-level features only: cc, pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length.
  - 95% CIs are a bootstrap over target entities (B = 2000).

**Per-project score distribution**

| smell | source | pooled_macro_F1 | pooled_MCC | macro_F1_median | macro_F1_q1 | macro_F1_q3 | macro_F1_worst | MCC_median | MCC_q1 | MCC_q3 | MCC_worst | projects_in_distribution | projects_flagged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | Step 3 LOPO LR (nested tuning, full features) | 0.527 | 0.113 | 0.504 | 0.473 | 0.643 | lettuce-io_lettuce-core (0.419) | 0.075 | 0.025 | 0.323 | lettuce-io_lettuce-core (-0.079) | 8 | macrozheng_mall [< 20 entities]; shuzheng_zheng [< 20 entities] |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | 0.516 | 0.089 | 0.51 | 0.442 | 0.64 | lettuce-io_lettuce-core (0.427) | 0.084 | -0.015 | 0.331 | lettuce-io_lettuce-core (-0.079) | 8 | macrozheng_mall [< 20 entities]; shuzheng_zheng [< 20 entities] |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | 0.492 | 0.02 | 0.496 | 0.474 | 0.543 | igniterealtime_Smack (0.416) | 0.04 | -0.014 | 0.176 | kevin-wayne_algs4 (-0.064) | 8 | macrozheng_mall [< 20 entities]; shuzheng_zheng [< 20 entities] |
| LPL | Step 3 LOPO GB (nested tuning, full features) | 0.634 | 0.268 | 0.562 | 0.5 | 0.636 | kevin-wayne_algs4 (0.444) | 0.165 | 0.119 | 0.33 | shuzheng_zheng (0.016) | 9 | macrozheng_mall [< 20 entities] |
| LPL | Step 3 LOPO LR (nested tuning, full features) | 0.567 | 0.136 | 0.52 | 0.406 | 0.618 | alibaba_arthas (0.258) | 0.041 | -0.076 | 0.236 | shuzheng_zheng (-0.148) | 9 | macrozheng_mall [< 20 entities] |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | 0.547 | 0.099 | 0.514 | 0.426 | 0.601 | alibaba_arthas (0.220) | 0.132 | 0.005 | 0.21 | shuzheng_zheng (-0.228) | 9 | macrozheng_mall [< 20 entities] |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | 0.562 | 0.127 | 0.497 | 0.467 | 0.59 | shuzheng_zheng (0.345) | 0.073 | -0.039 | 0.184 | shuzheng_zheng (-0.298) | 9 | macrozheng_mall [< 20 entities] |

**Per-project scores**

| smell | source | project | n | n_smelly | single_class | flag | macro_F1 | MCC | ROC_AUC |
|---|---|---|---|---|---|---|---|---|---|
| CM | Step 3 LOPO LR (nested tuning, full features) | Blankj_AndroidUtilCode | 77 | 37 | False |  | 0.786 | 0.601 | 0.75 |
| CM | Step 3 LOPO LR (nested tuning, full features) | MovingBlocks_Terasology | 355 | 217 | False |  | 0.526 | 0.07 | 0.525 |
| CM | Step 3 LOPO LR (nested tuning, full features) | MyCATApache_Mycat-Server | 412 | 303 | False |  | 0.475 | 0.033 | 0.516 |
| CM | Step 3 LOPO LR (nested tuning, full features) | alibaba_arthas | 167 | 141 | False |  | 0.596 | 0.231 | 0.738 |
| CM | Step 3 LOPO LR (nested tuning, full features) | igniterealtime_Smack | 199 | 108 | False |  | 0.482 | 0.0 | 0.472 |
| CM | Step 3 LOPO LR (nested tuning, full features) | kevin-wayne_algs4 | 263 | 181 | False |  | 0.468 | 0.079 | 0.522 |
| CM | Step 3 LOPO LR (nested tuning, full features) | lettuce-io_lettuce-core | 173 | 106 | False |  | 0.419 | -0.079 | 0.505 |
| CM | Step 3 LOPO LR (nested tuning, full features) | linlinjava_litemall | 34 | 23 | False |  | 0.828 | 0.657 | 0.889 |
| CM | Step 3 LOPO LR (nested tuning, full features) | macrozheng_mall | 12 | 11 | False | < 20 entities | 0.496 | 0.302 | 0.727 |
| CM | Step 3 LOPO LR (nested tuning, full features) | shuzheng_zheng | 3 | 2 | False | < 20 entities | 0.25 | -0.5 | 0.5 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | Blankj_AndroidUtilCode | 77 | 37 | False |  | 0.742 | 0.531 | 0.813 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | MovingBlocks_Terasology | 355 | 217 | False |  | 0.534 | 0.075 | 0.542 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | MyCATApache_Mycat-Server | 412 | 303 | False |  | 0.439 | -0.027 | 0.511 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | alibaba_arthas | 167 | 141 | False |  | 0.606 | 0.268 | 0.765 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | igniterealtime_Smack | 199 | 108 | False |  | 0.486 | -0.01 | 0.476 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | kevin-wayne_algs4 | 263 | 181 | False |  | 0.443 | 0.092 | 0.515 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | lettuce-io_lettuce-core | 173 | 106 | False |  | 0.427 | -0.079 | 0.506 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | linlinjava_litemall | 34 | 23 | False |  | 0.759 | 0.519 | 0.854 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | macrozheng_mall | 12 | 11 | False | < 20 entities | 0.621 | 0.426 | 0.909 |
| CM | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | shuzheng_zheng | 3 | 2 | False | < 20 entities | 0.667 | 0.5 | 0.5 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | Blankj_AndroidUtilCode | 77 | 37 | False |  | 0.54 | 0.199 | 0.564 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | MovingBlocks_Terasology | 355 | 217 | False |  | 0.494 | 0.06 | 0.53 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | MyCATApache_Mycat-Server | 412 | 303 | False |  | 0.497 | -0.004 | 0.503 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | alibaba_arthas | 167 | 141 | False |  | 0.583 | 0.169 | 0.584 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | igniterealtime_Smack | 199 | 108 | False |  | 0.416 | -0.044 | 0.513 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | kevin-wayne_algs4 | 263 | 181 | False |  | 0.447 | -0.064 | 0.458 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | lettuce-io_lettuce-core | 173 | 106 | False |  | 0.484 | 0.019 | 0.515 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | linlinjava_litemall | 34 | 23 | False |  | 0.55 | 0.228 | 0.538 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | macrozheng_mall | 12 | 11 | False | < 20 entities | 0.478 | 0.0 | 0.318 |
| CM | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | shuzheng_zheng | 3 | 2 | False | < 20 entities | 0.25 | -0.5 | 0.5 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | Blankj_AndroidUtilCode | 151 | 122 | False |  | 0.675 | 0.416 | 0.958 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | MovingBlocks_Terasology | 239 | 140 | False |  | 0.635 | 0.27 | 0.7 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | MyCATApache_Mycat-Server | 179 | 105 | False |  | 0.636 | 0.33 | 0.76 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | alibaba_arthas | 59 | 53 | False |  | 0.497 | 0.165 | 0.604 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | igniterealtime_Smack | 197 | 115 | False |  | 0.676 | 0.352 | 0.682 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | kevin-wayne_algs4 | 51 | 22 | False |  | 0.444 | 0.119 | 0.539 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | lettuce-io_lettuce-core | 360 | 238 | False |  | 0.5 | 0.042 | 0.543 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | linlinjava_litemall | 40 | 37 | False |  | 0.562 | 0.146 | 0.757 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | macrozheng_mall | 17 | 15 | False | < 20 entities | 0.469 | 0.0 | 1.0 |
| LPL | Step 3 LOPO GB (nested tuning, full features) | shuzheng_zheng | 32 | 20 | False |  | 0.508 | 0.016 | 0.398 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | Blankj_AndroidUtilCode | 151 | 122 | False |  | 0.394 | -0.121 | 0.382 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | MovingBlocks_Terasology | 239 | 140 | False |  | 0.618 | 0.236 | 0.655 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | MyCATApache_Mycat-Server | 179 | 105 | False |  | 0.637 | 0.313 | 0.733 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | alibaba_arthas | 59 | 53 | False |  | 0.258 | -0.076 | 0.355 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | igniterealtime_Smack | 197 | 115 | False |  | 0.678 | 0.358 | 0.683 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | kevin-wayne_algs4 | 51 | 22 | False |  | 0.52 | 0.041 | 0.574 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | lettuce-io_lettuce-core | 360 | 238 | False |  | 0.49 | 0.034 | 0.556 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | linlinjava_litemall | 40 | 37 | False |  | 0.531 | 0.208 | 0.721 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | macrozheng_mall | 17 | 15 | False | < 20 entities | 0.433 | -0.133 | 0.8 |
| LPL | Step 3 LOPO LR (nested tuning, full features) | shuzheng_zheng | 32 | 20 | False |  | 0.406 | -0.148 | 0.51 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | Blankj_AndroidUtilCode | 151 | 122 | False |  | 0.426 | -0.099 | 0.251 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | MovingBlocks_Terasology | 239 | 140 | False |  | 0.564 | 0.132 | 0.634 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | MyCATApache_Mycat-Server | 179 | 105 | False |  | 0.62 | 0.292 | 0.723 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | alibaba_arthas | 59 | 53 | False |  | 0.22 | 0.123 | 0.34 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | igniterealtime_Smack | 197 | 115 | False |  | 0.601 | 0.21 | 0.686 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | kevin-wayne_algs4 | 51 | 22 | False |  | 0.604 | 0.28 | 0.603 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | lettuce-io_lettuce-core | 360 | 238 | False |  | 0.483 | 0.005 | 0.533 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | linlinjava_litemall | 40 | 37 | False |  | 0.514 | 0.189 | 0.775 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | macrozheng_mall | 17 | 15 | False | < 20 entities | 0.433 | -0.133 | 0.867 |
| LPL | Tier 1 LOPO LR (default hyperparameters, Tier 1 features) | shuzheng_zheng | 32 | 20 | False |  | 0.373 | -0.228 | 0.429 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | Blankj_AndroidUtilCode | 151 | 122 | False |  | 0.609 | 0.236 | 0.681 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | MovingBlocks_Terasology | 239 | 140 | False |  | 0.59 | 0.184 | 0.624 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | MyCATApache_Mycat-Server | 179 | 105 | False |  | 0.609 | 0.22 | 0.688 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | alibaba_arthas | 59 | 53 | False |  | 0.457 | -0.004 | 0.566 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | igniterealtime_Smack | 197 | 115 | False |  | 0.536 | 0.073 | 0.571 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | kevin-wayne_algs4 | 51 | 22 | False |  | 0.497 | 0.092 | 0.658 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | lettuce-io_lettuce-core | 360 | 238 | False |  | 0.473 | -0.039 | 0.503 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | linlinjava_litemall | 40 | 37 | False |  | 0.467 | -0.065 | 0.649 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | macrozheng_mall | 17 | 15 | False | < 20 entities | 0.469 | 0.0 | 1.0 |
| LPL | Tier 1 LOPO RF (default hyperparameters, Tier 1 features) | shuzheng_zheng | 32 | 20 | False |  | 0.345 | -0.298 | 0.325 |

**Cross-smell transfer**

| source_smell | target_smell | model | params | train_n | test_n | shared_entities_removed_from_test | macro_F1 [95% CI] | MCC [95% CI] | ROC_AUC [95% CI] | PR_AUC [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| CM | LPL | LR | {'clf__C': 0.01} | 1695 | 1205 | 120 | 0.255 [0.234, 0.276] | -0.060 [-0.126, 0.002] | 0.468 [0.429, 0.505] | 0.690 [0.656, 0.727] |
| LPL | CM | GB | {'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100} | 1325 | 1575 | 120 | 0.285 [0.268, 0.302] | 0.051 [0.008, 0.090] | 0.516 [0.486, 0.546] | 0.692 [0.662, 0.723] |

Tables: `tables/lopo_per_project.csv`, `tables/lopo_distribution.csv`, `tables/cross_smell.csv`. Figure: `figures/lopo_distribution.pdf` (.png). Runtime 13s.

**Summary.** CM→LPL (LR): MCC -0.060 [-0.126, 0.002]; LPL→CM (GB): MCC 0.051 [0.008, 0.090].

### 5.5 E Leakage and validity checks

**Analysis type: validity check** (not a primary or robustness result).

**Method.**
- Duplicate keys are computed from each snippet's text in `files.zip`:
  - exact: comments removed, whitespace collapsed;
  - near: additionally, every non-keyword identifier becomes `ID` and every literal becomes `LIT`.
- Data: primary unanimous entities. Splits: the 25 section-B splits.
- Deduplication keeps the entity with the lowest DesigniteJava id in each near-duplicate group. The B headline (best model and LR, full nested protocol) is then rerun.
  - Δ compares the deduplicated run with the original out-of-fold predictions on the same retained entities, using a paired bootstrap.
- Train-serve skew: two-sample KS, DACOS unanimous entities versus the D4-cleaned DACOSX pool.

**Checks**

| check | smell | value | detail |
|---|---|---|---|
| exact duplicate groups (size ≥ 2) | CM | 22 | 46 entities; 0 groups span >1 project; 8 groups have conflicting labels |
| near duplicate groups (size ≥ 2) | CM | 56 | 126 entities; 0 groups span >1 project; 27 groups have conflicting labels |
| exact duplicate groups (size ≥ 2) | LPL | 71 | 169 entities; 0 groups span >1 project; 22 groups have conflicting labels |
| near duplicate groups (size ≥ 2) | LPL | 160 | 462 entities; 6 groups span >1 project; 62 groups have conflicting labels |
| test entities with a exact duplicate in the training fold (sum over 25 splits) | CM | 0 | of 8475 test-entity slots; max 0 in one split |
| test entities with a near duplicate in the training fold (sum over 25 splits) | CM | 0 | of 8475 test-entity slots; max 0 in one split |
| test entities with a exact duplicate in the training fold (sum over 25 splits) | LPL | 0 | of 6625 test-entity slots; max 0 in one split |
| test entities with a near duplicate in the training fold (sum over 25 splits) | LPL | 69 | of 6625 test-entity slots; max 8 in one split |
| entity_overlap (sum over 25 splits) | CM | 0 | must be 0 |
| file_overlap (sum over 25 splits) | CM | 0 | must be 0 |
| project_overlap (sum over 25 splits) | CM | 0 | must be 0 |
| dacosx_train_projects_in_test (C3) (sum over 25 splits) | CM | 0 | must be 0 |
| entity_overlap (sum over 25 splits) | LPL | 0 | must be 0 |
| file_overlap (sum over 25 splits) | LPL | 0 | must be 0 |
| project_overlap (sum over 25 splits) | LPL | 0 | must be 0 |
| dacosx_train_projects_in_test (C3) (sum over 25 splits) | LPL | 0 | must be 0 |

All entity, file and project overlap checks are 0 in every split.

**B headline after near-duplicate removal**

| smell | model | n original → deduplicated | macro-F1 original | macro-F1 dedup [95% CI] | MCC original | MCC dedup [95% CI] | Δ macro-F1 on retained [95% CI] | Δ MCC on retained [95% CI] |
|---|---|---|---|---|---|---|---|---|
| CM | LR | 1695 → 1625 | 0.525 | 0.516 [0.494, 0.539] | 0.095 | 0.081 [0.036, 0.126] | -0.006 [-0.010, -0.002] | -0.009 [-0.016, -0.002] |
| LPL | GB | 1325 → 1023 | 0.616 | 0.633 [0.606, 0.660] | 0.232 | 0.267 [0.212, 0.320] | 0.008 [-0.005, 0.022] | 0.014 [-0.013, 0.040] |
| LPL | LR | 1325 → 1023 | 0.569 | 0.588 [0.558, 0.616] | 0.141 | 0.179 [0.121, 0.236] | 0.017 [0.006, 0.027] | 0.025 [0.005, 0.046] |

**Train-serve skew (DACOS versus DACOSX)**

| smell | feature | DACOS_n | DACOSX_n | DACOS_median | DACOSX_median | KS_D | KS_p | computed_identically |
|---|---|---|---|---|---|---|---|---|
| CM | cc | 1695 | 83549 | 6.0 | 1.0 | 0.995 | 0.00e+00 | yes: stored DesigniteJava value from the same tables |
| CM | loc | 1695 | 83549 | 24.0 | 4.0 | 0.811 | 0.00e+00 | yes: stored DesigniteJava value from the same tables |
| CM | statements | 1695 | 83549 | 18.0 | 2.0 | 0.897 | 0.00e+00 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| CM | max_nesting | 1695 | 83549 | 3.0 | 0.0 | 0.83 | 0.00e+00 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| CM | method_calls | 1695 | 83549 | 14.0 | 1.0 | 0.728 | 0.00e+00 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| CM | comment_ratio | 1695 | 83549 | 0.0 | 0.0 | 0.183 | 3.20e-49 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| CM | mean_identifier_length | 1695 | 83549 | 8.05 | 9.182 | 0.223 | 2.43e-73 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| LPL | pc | 1325 | 83110 | 4.0 | 1.0 | 0.998 | 0.00e+00 | yes: stored DesigniteJava value from the same tables |
| LPL | loc | 1325 | 83110 | 5.0 | 4.0 | 0.306 | 9.71e-109 | yes: stored DesigniteJava value from the same tables |
| LPL | statements | 1325 | 83110 | 5.0 | 2.0 | 0.386 | 4.48e-175 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| LPL | max_nesting | 1325 | 83110 | 0.0 | 0.0 | 0.207 | 1.17e-49 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| LPL | method_calls | 1325 | 83110 | 3.0 | 1.0 | 0.279 | 4.90e-90 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| LPL | comment_ratio | 1325 | 83110 | 0.0 | 0.0 | 0.16 | 1.87e-29 | yes: same lexer (src/features.py) on the same files.zip snippet type |
| LPL | mean_identifier_length | 1325 | 83110 | 7.879 | 9.184 | 0.256 | 1.22e-75 | yes: same lexer (src/features.py) on the same files.zip snippet type |

- Every feature is computed by the same code path for both sources. Stored DesigniteJava metrics come from the same `method_metrics` / `class_metrics` tables; computed features come from the same lexer on the same kind of snippet file.
- Large KS statistics are expected for the primary metric and size-related features, because DACOSX is selected outside the borderline band by construction.

Tables: `tables/leakage_checks.csv`, `tables/leakage_duplicates_per_split.csv`, `tables/leakage_dedup_rerun.csv`, `tables/train_serve_skew.csv`. Runtime 29s.

### 5.6 F Interpretability and calibration

**Analysis type: primary (interpretability, calibration).**

**Method.**
- SHAP: `shap` 0.46.0 `TreeExplainer` on the best tree model (CM: GB, LPL: GB).
  - The model is refitted on all unanimous entities, with hyperparameters from `GridSearchCV(GroupKFold(5) by project, MCC)` on all data. Parameters are in the table below.
  - SHAP values are in log-odds of "smelly".
- Permutation importance: on the held-out folds of repeat 0, using each fold's section-B parameters; scoring MCC, 10 permutations, averaged over the 5 folds.
- Spearman ρ compares the two importance vectors.
- Calibration: pooled repeat-0 out-of-fold probabilities of the best model and LR (CM's best model is LR), as a Brier score and a 10-bin reliability diagram.
  - The reference Brier score is that of a constant prediction equal to the observed prevalence.
  - Class weighting shifts predicted probabilities towards 0.5 by design; the calibration figures reflect the weighted models as evaluated.

**Importance rankings**

| smell | model | feature | mean_abs_SHAP | permutation_importance_MCC | rank_SHAP | rank_permutation |
|---|---|---|---|---|---|---|
| CM | GB | cc | 0.0444 | 0.0043 | 7 | 2 |
| CM | GB | loc | 0.2033 | -0.0004 | 3 | 3 |
| CM | GB | statements | 0.0671 | -0.0041 | 5 | 5 |
| CM | GB | max_nesting | 0.0645 | -0.0043 | 6 | 6 |
| CM | GB | method_calls | 0.2297 | 0.0285 | 1 | 1 |
| CM | GB | comment_ratio | 0.1276 | -0.0193 | 4 | 7 |
| CM | GB | mean_identifier_length | 0.2231 | -0.0025 | 2 | 4 |
| LPL | GB | pc | 0.6944 | 0.0381 | 1 | 2 |
| LPL | GB | loc | 0.1806 | 0.0215 | 4 | 3 |
| LPL | GB | statements | 0.1765 | -0.0014 | 5 | 4 |
| LPL | GB | max_nesting | 0.3488 | 0.0539 | 2 | 1 |
| LPL | GB | method_calls | 0.0965 | -0.0085 | 7 | 5 |
| LPL | GB | comment_ratio | 0.1738 | -0.0215 | 6 | 6 |
| LPL | GB | mean_identifier_length | 0.3408 | -0.0342 | 3 | 7 |

| smell | model | refit_params | spearman_rho | p | n_features |
|---|---|---|---|---|---|
| CM | GB | {'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 300} | 0.321 | 0.4821 | 7 |
| LPL | GB | {'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 300} | 0.571 | 0.1802 | 7 |

**Calibration**

| smell | model | n | brier | brier_reference_constant_prevalence | mean_predicted | observed_prevalence | bins |
|---|---|---|---|---|---|---|---|
| CM | LR | 1695 | 0.2483 | 0.2224 | 0.4993 | 0.6661 | [0.38→0.59, n=70]; [0.46→0.63, n=883]; [0.54→0.71, n=607]; [0.63→0.77, n=112]; [0.74→0.77, n=22]; [0.83→0.00, n=1] |
| LPL | GB | 1325 | 0.2169 | 0.2262 | 0.5278 | 0.6543 | [0.08→0.26, n=31]; [0.14→0.27, n=51]; [0.25→0.29, n=86]; [0.35→0.56, n=96]; [0.46→0.68, n=187]; [0.56→0.69, n=478]; [0.65→0.70, n=230]; [0.74→0.76, n=70]; [0.84→1.00, n=83]; [0.95→1.00, n=13] |
| LPL | LR | 1325 | 0.2465 | 0.2262 | 0.5081 | 0.6543 | [0.06→0.50, n=6]; [0.16→0.52, n=31]; [0.26→0.49, n=81]; [0.35→0.49, n=164]; [0.46→0.68, n=251]; [0.55→0.69, n=454]; [0.65→0.71, n=263]; [0.72→0.73, n=75] |

Tables: `tables/shap_permutation_importance.csv`, `tables/shap_rank_correlation.csv`, `tables/calibration.csv`.

Figures: `figures/shap_summary_<smell>.pdf`, `figures/shap_dependence_<smell>.pdf` (DesigniteJava default and RQ2 Youden cut-off marked), `figures/reliability_<smell>.pdf` (.png).

### 5.7 G Feature selection

**Analysis type: primary, report-only (pre-registered in plan.md §4.5 G; never used to choose the final model).**

**Method.**
- Repeat-0 folds of section B; selection uses the training fold only.
1. Mutual-information filter: keep features with `mutual_info_classif` > 0 (random_state 20261021).
2. Pearson |r| > 0.85 pruning: drop the feature with lower MI.
3. `RFECV` with standardised class-weighted LR (`GroupKFold(3)` by project, scoring MCC).
- The best model, with fold parameters, is then trained on the selected subset. Performance on pooled repeat-0 out-of-fold predictions is compared with the full feature set using a paired bootstrap.
- Pre-registered decision: keep the full feature set if selection lowers MCC or the mean pairwise Jaccard across folds is < 0.7.

**Selected features per fold**

| smell | model | fold | after_MI_filter | after_correlation_pruning | after_RFECV | n_selected |
|---|---|---|---|---|---|---|
| CM | LR | 0 | statements, max_nesting, method_calls | statements, max_nesting, method_calls | method_calls | 1 |
| CM | LR | 1 | loc, statements, max_nesting | loc, statements, max_nesting | statements | 1 |
| CM | LR | 2 | statements, mean_identifier_length | statements, mean_identifier_length | statements, mean_identifier_length | 2 |
| CM | LR | 3 | cc, loc, statements, max_nesting, comment_ratio | cc, loc, statements, max_nesting, comment_ratio | cc, loc, statements, max_nesting, comment_ratio | 5 |
| CM | LR | 4 | loc, max_nesting, method_calls, comment_ratio | loc, max_nesting, method_calls, comment_ratio | method_calls | 1 |
| LPL | GB | 0 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 1 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 2 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 3 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, max_nesting, comment_ratio | 4 |
| LPL | GB | 4 | loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | max_nesting, mean_identifier_length | 2 |

**Selected versus all features**

| smell | model | selected_macro_F1 | all_macro_F1 | selected_MCC | all_MCC | Δ macro-F1 [95% CI] | Δ MCC [95% CI] | mean_pairwise_jaccard | decision |
|---|---|---|---|---|---|---|---|---|---|
| CM | LR | 0.53 | 0.521 | 0.135 | 0.1 | 0.008 [-0.012, 0.028] | 0.035 [-0.006, 0.077] | 0.187 | keep full feature set |
| LPL | GB | 0.606 | 0.612 | 0.226 | 0.225 | -0.006 [-0.032, 0.019] | 0.001 [-0.050, 0.052] | 0.57 | keep full feature set |

Tables: `tables/feature_selection.csv` (including per-fold MI values), `tables/feature_selection_performance.csv`.

### 5.8 H Learning curve

**Analysis type: primary.**

**Method.**
- Best model with each fold's section-B parameters, on the repeat-0 folds.
- Each training fold is subsampled per class (stratified) to 10/25/50/75/100%, with 5 seeds (seed 20261021 + s, also used as the model seed).
- Macro-F1 is computed on pooled out-of-fold predictions per seed.
- Plateau rule (fixed in plan.md): plateaued if the macro-F1 gain from 75% to 100% is < 0.01 and its paired bootstrap CI includes 0.

| smell | model | fraction | mean_train_n | macro_F1_mean | macro_F1_sd | MCC_mean |
|---|---|---|---|---|---|---|
| CM | LR | 0.1 | 135.6 | 0.513 | 0.027 | 0.055 |
| CM | LR | 0.25 | 338.8 | 0.53 | 0.021 | 0.096 |
| CM | LR | 0.5 | 677.8 | 0.512 | 0.012 | 0.083 |
| CM | LR | 0.75 | 1017.2 | 0.506 | 0.006 | 0.077 |
| CM | LR | 1.0 | 1356.0 | 0.521 | 0.0 | 0.1 |
| LPL | GB | 0.1 | 106.2 | 0.556 | 0.011 | 0.122 |
| LPL | GB | 0.25 | 265.0 | 0.604 | 0.01 | 0.213 |
| LPL | GB | 0.5 | 530.0 | 0.611 | 0.019 | 0.223 |
| LPL | GB | 0.75 | 795.0 | 0.608 | 0.01 | 0.217 |
| LPL | GB | 1.0 | 1060.0 | 0.612 | 0.0 | 0.225 |

| smell | model | gain 75%→100% [95% CI] | plateaued_by_rule |
|---|---|---|---|
| CM | LR | 0.015 [0.005, 0.025] | False |
| LPL | GB | 0.005 [-0.007, 0.016] | True |

Tables: `tables/learning_curve.csv`, `tables/learning_curve_plateau.csv`. Figure: `figures/learning_curve.pdf` (.png). Runtime F+H 9s.

**Summary.** CM (LR): gain 75%→100% = 0.015 [0.005, 0.025], plateaued by rule: no; macro-F1 across all fractions ranges 0.506–0.530; LPL (GB): gain 75%→100% = 0.005 [-0.007, 0.016], plateaued by rule: yes; macro-F1 across all fractions ranges 0.556–0.612.

### 5.9 I Error analysis

**Analysis type: primary (descriptive error analysis).**

**Method.**
- Best model on the repeat-0 folds with section-B fold parameters, trained on unanimous training entities.
- Every entity of the held-out projects is predicted: unanimous, non-unanimous majority (n ≥ 3), and ties.
- Errors are counted on majority-labelled entities. Ties have no label, so their predicted-smelly share is reported instead.
- An entity is "in run" if any of its annotations (unfiltered) lies in an answer run.
- Samples: 15 FP and 15 FN per smell (seed 20261021), saved with code, features, vote split, run membership and score.

| smell | model | group | entities | share_of_all_entities | errors | share_of_errors | error_rate |
|---|---|---|---|---|---|---|---|
| CM | LR | unanimous | 1695 | 0.999 | 803 | 1.0 | 0.474 |
| CM | LR | split (non-unanimous majority) | 1 | 0.001 | 0 | 0.0 | 0.0 |
| CM | LR | in run | 338 | 0.199 | 147 | 0.183 | 0.435 |
| CM | LR | not in run | 1358 | 0.801 | 656 | 0.817 | 0.483 |
| CM | LR | all majority-labelled | 1696 | 1.0 | 803 | 1.0 | 0.473 |
| CM | LR | ties (no label; predicted-smelly share) | 164 | n/a | n/a | n/a | 0.354 |
| LPL | GB | unanimous | 1325 | 0.998 | 463 | 0.996 | 0.349 |
| LPL | GB | split (non-unanimous majority) | 2 | 0.002 | 2 | 0.004 | 1.0 |
| LPL | GB | in run | 1077 | 0.812 | 375 | 0.806 | 0.348 |
| LPL | GB | not in run | 250 | 0.188 | 90 | 0.194 | 0.36 |
| LPL | GB | all majority-labelled | 1327 | 1.0 | 465 | 1.0 | 0.35 |
| LPL | GB | ties (no label; predicted-smelly share) | 366 | n/a | n/a | n/a | 0.667 |

- Split entities with a majority label are rare in CM and LPL, because nearly all entities have 2 annotations and splits are ties. The "split" row is therefore very small.

Files: `results/error_analysis/error_rates.csv`, `error_samples.csv`, `error_samples_code.md`.

Section J (sensitivity) is reported in §4.3, because it is a robustness analysis.

## 6 Human ceiling and agreement anatomy

### 6.1 Human ceiling (plan.md §5.2)

**Analysis type: primary (human ceiling).** plan.md §5.2.

**Method.**
- Population: primary-set entities (R5 set for "LPL R5") with exactly 2 usable annotations, unanimous and split.
- **Human vs human.** One annotation is the prediction and the other the target, with random roles in each of 2000 designations. MCC, macro-F1 and accuracy are computed over entities and averaged over designations.
  - Only split entities depend on the designation. Each designation is therefore simulated exactly by binomial draws on the split counts (sufficient statistics), which is equivalent to drawing roles entity by entity.
- **Model vs one human.**
  - The best model of the run (CM LR, LPL GB, LPL R5 SVM) uses section-B fold hyperparameters on the 25 splits, trained on unanimous training entities only.
  - It predicts every held-out entity in the population, ties included.
  - In designation d it is scored against the same target annotation as the human, using repeat d mod 5. The comparison is paired.
- **CIs.** Bootstrap over entities (B = 2000); each resample re-draws 2000 designations. The gap and the ratio use the same resamples and draws.
- **Second ceiling: near-duplicate pairs.**
  - Pairs of different entities in the same project with identical near-duplicate keys (identifiers → ID, literals → LIT), primary set (R5 set for LPL R5).
  - One random annotation per entity, random roles, 2000 designations. CI from a bootstrap over near-duplicate groups (clusters).

Population sizes:

| population | entities_with_exactly_2_usable | dropped_missing_features |
|---|---|---|
| CM | 1858 | 0 |
| LPL | 1692 | 1 |
| LPL R5 | 1555 | 0 |

**Ceiling table**

| population | best_model | metric | entities | unanimous | split | human vs human [95% CI] | model vs one human [95% CI] | gap human − model [95% CI] | ratio model/human MCC [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| CM | LR | MCC | 1858 | 1694 | 164 | 0.806 [0.776, 0.833] | 0.091 [0.053, 0.130] | 0.715 [0.666, 0.760] | 0.113 [0.066, 0.162] |
| CM | LR | macro_F1 | 1858 | 1694 | 164 | 0.903 [0.888, 0.916] | 0.524 [0.505, 0.544] | 0.379 [0.354, 0.402] |  |
| CM | LR | accuracy | 1858 | 1694 | 164 | 0.912 [0.899, 0.924] | 0.530 [0.511, 0.550] | 0.381 [0.357, 0.404] |  |
| LPL | GB | MCC | 1691 | 1325 | 366 | 0.540 [0.498, 0.581] | 0.171 [0.133, 0.210] | 0.369 [0.317, 0.421] | 0.317 [0.248, 0.391] |
| LPL | GB | macro_F1 | 1691 | 1325 | 366 | 0.770 [0.749, 0.790] | 0.584 [0.565, 0.603] | 0.186 [0.161, 0.212] |  |
| LPL | GB | accuracy | 1691 | 1325 | 366 | 0.784 [0.763, 0.803] | 0.618 [0.600, 0.636] | 0.166 [0.141, 0.191] |  |
| LPL R5 | SVM | MCC | 1555 | 1189 | 366 | 0.515 [0.472, 0.558] | 0.201 [0.162, 0.243] | 0.313 [0.257, 0.366] | 0.391 [0.314, 0.478] |
| LPL R5 | SVM | macro_F1 | 1555 | 1189 | 366 | 0.757 [0.736, 0.779] | 0.576 [0.556, 0.598] | 0.181 [0.153, 0.208] |  |
| LPL R5 | SVM | accuracy | 1555 | 1189 | 366 | 0.765 [0.745, 0.786] | 0.631 [0.612, 0.650] | 0.134 [0.108, 0.160] |  |

**Second ceiling: human-vs-human agreement between structurally identical snippets of the same project**

| smell | groups | pairs | MCC [95% CI] | macro_F1 [95% CI] | accuracy [95% CI] |
|---|---|---|---|---|---|
| CM | 63 | 104 | 0.082 [-0.112, 0.301] | 0.539 [0.441, 0.648] | 0.573 [0.470, 0.687] |
| LPL | 209 | 1393 | 0.099 [0.039, 0.183] | 0.549 [0.519, 0.591] | 0.625 [0.583, 0.648] |
| LPL R5 | 180 | 1352 | 0.087 [0.028, 0.158] | 0.543 [0.514, 0.579] | 0.613 [0.563, 0.638] |

Tables: `tables/human_ceiling.csv`, `tables/human_ceiling_neardup.csv`. Figure: `figures/human_ceiling.pdf` (.png). Runtime 39s.

**Summary (MCC).** CM: human 0.806, model 0.091, ratio 0.11; LPL: human 0.540, model 0.171, ratio 0.32; LPL R5: human 0.515, model 0.201, ratio 0.39.

### 6.2 Why same-snippet agreement exceeds cross-snippet agreement (plan.md §7.1)

**Analysis type: primary** (R4 rows of 1.3 are robustness). plan.md §7.1.

**Population.** Primary-set entities with exactly 2 usable annotations (R5 set for "LPL R5"). Entities whose snippet file is missing from `files.zip` (§1.8) get no duplicate key and are excluded from 1.1–1.2, but are kept in 1.3. Groups are entities of the same project with the same near-duplicate key (identifiers → ID, literals → LIT) or the same exact key (comments removed, whitespace collapsed, names kept), with at least 2 entities.

**1.1 Matched comparison on near-duplicate groups**
- (a) Same-snippet MCC: one annotation versus the other, random roles, 2000 designations.
- (b) Cross-snippet MCC: for every entity pair within a group, one random annotation per entity, random roles, 2000 draws.
- CIs: bootstrap over groups (B = 2000); the difference is paired.
- The Prompt 3 cross-snippet number (§6, last column) used every primary-set entity with ≥ 2 usable annotations, drawing each entity's annotation with probability y/n. (b) uses the same construction restricted to entities with exactly 2 usable annotations, so both sides here are computed on identical entities.

| population | groups | entities | pairs | same-snippet MCC [95% CI] | cross-snippet MCC [95% CI] | difference [95% CI] | Prompt 3 cross-snippet MCC |
|---|---|---|---|---|---|---|---|
| CM | 62 | 140 | 103 | 0.865 [0.754, 0.954] | 0.078 [-0.128, 0.280] | 0.787 [0.563, 1.015] | 0.082 |
| LPL | 207 | 614 | 1391 | 0.456 [0.321, 0.590] | 0.098 [0.038, 0.189] | 0.358 [0.204, 0.498] | 0.099 |
| LPL R5 | 178 | 551 | 1350 | 0.424 [0.286, 0.576] | 0.086 [0.030, 0.156] | 0.337 [0.191, 0.495] | 0.087 |

**1.2 Exact duplicates**

| population | key | reported_as | groups | entities | pairs | same_MCC | same_lo | same_hi | cross_MCC | cross_lo | cross_hi | diff_MCC | diff_lo | diff_hi | same_raw_agreement | cross_raw_agreement | diff_raw_agreement | diff_raw_lo | diff_raw_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | exact duplicate | CI (≥ 20 groups) | 26 | 54 | 30 | 0.803 | 0.582 | 0.962 | 0.18 | -0.112 | 0.465 | 0.623 | 0.269 | 0.972 | 0.907 | 0.601 | 0.306 | 0.116 | 0.477 |
| LPL | exact duplicate | CI (≥ 20 groups) | 92 | 227 | 683 | 0.49 | 0.311 | 0.696 | 0.042 | -0.002 | 0.315 | 0.448 | 0.217 | 0.575 | 0.784 | 0.65 | 0.134 | 0.062 | 0.236 |
| LPL R5 | exact duplicate | CI (≥ 20 groups) | 72 | 187 | 663 | 0.438 | 0.254 | 0.633 | 0.033 | -0.022 | 0.224 | 0.405 | 0.199 | 0.587 | 0.738 | 0.64 | 0.098 | 0.018 | 0.277 |

**1.3 Annotation-id gap** (|id₁ − id₂| per entity; R4 = run annotations removed first)

| population | entities | min | q1 | median | q3 | max | share_gap_le_10 | share_gap_le_100 | set |
|---|---|---|---|---|---|---|---|---|---|
| CM | 1858 | 1 | 1826.25 | 2944.0 | 3098.0 | 8288 | 0.034 | 0.074 | primary |
| CM | 1468 | 1 | 1578.5 | 2975.0 | 3114.0 | 3787 | 0.042 | 0.073 | R4 |
| LPL | 1692 | 1 | 1830.75 | 2536.5 | 3225.5 | 9624 | 0.018 | 0.035 | primary |
| LPL | 252 | 1 | 126.5 | 300.5 | 1726.0 | 2944 | 0.115 | 0.226 | R4 |
| LPL R5 | 1555 | 1 | 2061.5 | 2616.0 | 3314.5 | 9624 | 0.02 | 0.038 | R5 |

| population | set | quintile | gap range | entities | share unanimous [95% CI] | same-snippet MCC [95% CI] |
|---|---|---|---|---|---|---|
| CM | primary | 1 | 1–1494 | 372 | 0.841 [0.804, 0.879] | 0.574 [0.468, 0.665] |
| CM | primary | 2 | 1497–2626 | 371 | 0.865 [0.827, 0.900] | 0.595 [0.491, 0.695] |
| CM | primary | 3 | 2629–3007 | 372 | 0.892 [0.860, 0.925] | 0.785 [0.721, 0.849] |
| CM | primary | 4 | 3009–3131 | 371 | 0.987 [0.973, 0.997] | 0.971 [0.942, 0.994] |
| CM | primary | 5 | 3131–8288 | 372 | 0.973 [0.954, 0.987] | 0.946 [0.908, 0.973] |
| CM | R4 | 1 | 1–1393 | 294 | 0.833 [0.789, 0.874] | 0.585 [0.479, 0.682] |
| CM | R4 | 2 | 1395–2785 | 293 | 0.863 [0.826, 0.901] | 0.640 [0.532, 0.734] |
| CM | R4 | 3 | 2805–3053 | 294 | 0.925 [0.895, 0.952] | 0.841 [0.778, 0.901] |
| CM | R4 | 4 | 3053–3135 | 293 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| CM | R4 | 5 | 3135–3787 | 294 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| LPL | primary | 1 | 1–1614 | 339 | 0.968 [0.947, 0.985] | 0.864 [0.779, 0.935] |
| LPL | primary | 2 | 1615–2375 | 338 | 0.766 [0.722, 0.811] | 0.328 [0.206, 0.441] |
| LPL | primary | 3 | 2375–2944 | 338 | 0.855 [0.814, 0.891] | 0.650 [0.551, 0.735] |
| LPL | primary | 4 | 2944–3405 | 338 | 0.861 [0.822, 0.896] | 0.611 [0.506, 0.708] |
| LPL | primary | 5 | 3406–9624 | 339 | 0.469 [0.416, 0.519] | -0.063 [-0.170, 0.038] |
| LPL | R4 | 1 | 1–75 | 51 | 0.941 [0.863, 1.000] | 0.773 [0.472, 1.000] |
| LPL | R4 | 2 | 76–271 | 50 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| LPL | R4 | 3 | 273–1270 | 50 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| LPL | R4 | 4 | 1270–1870 | 50 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| LPL | R4 | 5 | 1874–2944 | 51 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| LPL R5 | R5 | 1 | 1–1870 | 311 | 0.965 [0.942, 0.984] | 0.875 [0.797, 0.941] |
| LPL R5 | R5 | 2 | 1874–2475 | 311 | 0.736 [0.688, 0.785] | 0.333 [0.211, 0.446] |
| LPL R5 | R5 | 3 | 2475–3000 | 311 | 0.817 [0.775, 0.859] | 0.622 [0.531, 0.710] |
| LPL R5 | R5 | 4 | 3000–3484 | 311 | 0.884 [0.849, 0.920] | 0.698 [0.601, 0.786] |
| LPL R5 | R5 | 5 | 3486–9624 | 311 | 0.421 [0.370, 0.476] | -0.160 [-0.266, -0.051] |

Logistic regression of unanimous on log(gap) and the raw primary metric:

| population | set | entities | OR per unit log(gap) [95% CI] | p | OR per unit metric (p) | note |
|---|---|---|---|---|---|---|
| CM | primary | 1858 | 1.214 [1.133, 1.302] | 4.49e-08 | 1.005 (0.9079) |  |
| CM | R4 | 1468 | 1.312 [1.220, 1.410] | 1.82e-13 | 1.025 (0.6648) |  |
| LPL | primary | 1692 | 0.186 [0.141, 0.247] | 1.28e-31 | 0.391 (2.41e-23) |  |
| LPL | R4 | 252 | n/a | n/a | n/a | not estimable: quasi-complete separation (robust SE > 5) |
| LPL R5 | R5 | 1555 | 0.187 [0.141, 0.249] | 4.11e-31 | 0.391 (2.89e-23) |  |

**1.4 Tool design** (public source SMART-Dal/Tagman @ 40f3aa67bc16d780c6a0e1da63995b7d92789ddc (2023-01-19); the deployed version may differ)

| question | finding | reference |
|---|---|---|
| (a) Does serving prevent one user from annotating the same sample twice? | Yes for the same `sample` row. Once a user has any annotation, candidate samples are filtered by `id NOT IN (<sample ids this user annotated>)`. The filter does not apply across different `sample` rows of the same code entity, such as the 332 MA classes imported twice (§1.3). | src/main/java/com/smartlab/tagman/service/AnnotationService.java:99-120, 131-133 |
| (b) What does the annotator see? | Only the contents of the snippet's own file (`sample.path_to_file`, the CodeSplit method or class file), read line by line. It is shown in a code block titled with the file path. The surrounding class or source file is not shown. | src/main/java/com/smartlab/tagman/web/AnnotationController.java:107-118; src/main/resources/templates/indexNonAdmin.html:438-439; src/main/java/com/smartlab/tagman/util/TagmanUtil.java:53-58 |
| (c) How are samples assigned and ordered? | Each request picks methods with probability 0.7 and classes with 0.3 (`random.nextInt(10) < 7`). It first queries samples with `has_smell = true` and `sample_constraints = 1` (already annotated once), then falls back to `sample_constraints < 2`. Both queries use `LIMIT 10` with no `ORDER BY`, and the tool picks uniformly at random among the ≤ 10 rows returned. Without `ORDER BY`, the rows returned follow the database's storage order, so serving tends to follow sample-id order. Preferring samples with one annotation tends to bring a sample's second annotation soon after its first. The counter `sample_constraints` is incremented on submit. Each user is capped at `MaxUserAnnotations` = 2500. | AnnotationService.java:76-79, 92-93, 117-120, 131-133, 142-143; util/Constants.java:41, 51 |

**1.5 Interpretation (rules fixed in plan.md §7.1)**

In the matched comparison, same-snippet MCC exceeds cross-snippet MCC on the same entities for 3 of 3 populations (CI of the difference excluding 0). This shows that the gap is not an artefact of comparing different populations. It does not discriminate between the two explanations. For exact duplicates, which share names and text (CM: same − cross MCC 0.623 [0.269, 0.972]; LPL: same − cross MCC 0.448 [0.217, 0.575]; LPL R5: same − cross MCC 0.405 [0.199, 0.587]), cross-snippet agreement is below same-snippet agreement in 3 of 3 populations. Where it is lower, this is inconsistent with the view that information inside the snippet text explains the gap; context outside the snippet and collection effects remain possible. The annotation-id gap shows an OR per unit log(gap) below 1 with a CI excluding 1 for LPL, LPL R5. That is consistent with collection or session effects. The OR is above 1 with a CI excluding 1 for CM, meaning agreement rises with the gap. A null result here is not evidence against collection effects. The public tool source shows annotators only the snippet's own file, which is inconsistent with an explanation based on context outside the snippet, unless the deployed version differed. It prevents the same user from annotating the same sample row twice, so a same-annotator explanation is possible only through duplicated sample rows or multiple accounts. Neither can be checked, because the data have no annotator ids.

Tables: `tables/agreement_matched_neardup.csv`, `agreement_exact_dup.csv`, `agreement_gap_distribution.csv`, `agreement_gap_quintiles.csv`, `agreement_gap_logit.csv`, `agreement_tool_design.csv`. Runtime 24s.

## 7 Range restriction (plan.md §6.1)

**Analysis type: A1–A3 primary (descriptive or tested as stated); A4 exploratory.** plan.md §6.1.

**Snippet universe:** 87,523 method snippets and 8,325 class snippets in the 10 projects, deduplicated by DesigniteJava id. A further 1 class snippets have no `class_metrics` row and are excluded.
Annotated bands are the observed [min, max] of each primary metric over all annotated entities (§1.5). LPL R5 excludes the pc = 3 entities.

**A1: where the tool rule decides**

| smell/band | metric | annotated_band | universe_snippets | inside_band | share_inside_band | DesigniteJava_rule | flagged | share_flagged | flagged_inside_band | share_of_flagged_inside_band | flagged_above_band | analysis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | cc | 5–14 | 87523 | 2601 | 0.0297 | cc ≥ 8 | 987 | 0.0113 | 808 | 0.8186 | 179 | primary (descriptive) |
| LPL | pc | 3–10 | 87523 | 4528 | 0.0517 | pc ≥ 5 | 710 | 0.0081 | 702 | 0.9887 | 8 | primary (descriptive) |
| LPL R5 | pc | 4–10 | 87523 | 1888 | 0.0216 | pc ≥ 5 | 710 | 0.0081 | 702 | 0.9887 | 8 | primary (descriptive) |
| MA | lcom | 0.402174–1 | 8325 | 1411 | 0.1695 | LCOM ≥ 0.8 & NOF ≥ 7 & NOM ≥ 7 | 12 | 0.0014 | 12 | 1.0 | 0 | primary (descriptive) |

**A2: within-band trend** (unanimous entities; Cochran–Armitage two-sided; logistic regression of label on metric)

| smell | n | n_smelly | CA z (p) | logistic OR per unit [95% CI] (p) |
|---|---|---|---|---|
| CM | 1695 | 1129 | 3.15 (0.0016) | 1.105 [1.038, 1.176] (0.0017) |
| LPL R5 | 1189 | 731 | 0.87 (0.3869) | 1.094 [0.892, 1.341] (0.3879) |

Share smelly by metric value:

| value | CM entities | LPL R5 entities | CM share_smelly | LPL R5 share_smelly |
|---|---|---|---|---|
| 4.0 | – | 915.0 | – | 0.607 |
| 5.0 | 573.0 | 242.0 | 0.625 | 0.632 |
| 6.0 | 399.0 | 23.0 | 0.674 | 0.826 |
| 7.0 | 288.0 | 3.0 | 0.684 | 0.333 |
| 8.0 | 174.0 | 2.0 | 0.649 | 0.5 |
| 9.0 | 133.0 | 3.0 | 0.729 | 0.333 |
| 10.0 | 99.0 | 1.0 | 0.687 | 1.0 |
| 11.0 | 9.0 | – | 1.0 | – |
| 12.0 | 9.0 | – | 0.889 | – |
| 13.0 | 8.0 | – | 0.875 | – |
| 14.0 | 3.0 | – | 1.0 | – |

**A3: SD of each feature, annotated versus universe**
- An SD ratio near 1 means the feature is not range-restricted in the annotated set.
- RQ3 ORs come from the primary GEE (LPL R5 from §5.10). MA has no RQ3 model.

| smell | feature | role | SD_annotated | SD_universe | SD_ratio | RQ3 OR per SD [95% CI] |
|---|---|---|---|---|---|---|
| CM | cc | primary metric | 1.707 | 1.579 | 1.081 | 1.074 [0.964, 1.197] |
| CM | loc | secondary | 15.797 | 7.87 | 2.007 | 1.053 [0.907, 1.224] |
| CM | statements | secondary | 11.097 | 9.559 | 1.161 | 0.995 [0.847, 1.168] |
| CM | max_nesting | secondary | 1.338 | 0.773 | 1.731 | 1.078 [0.973, 1.195] |
| CM | comment_ratio | secondary | 0.104 | 0.25 | 0.414 | 1.098 [0.996, 1.210] |
| CM | method_calls | secondary | 14.132 | 9.243 | 1.529 | 1.190 [1.027, 1.380] |
| CM | mean_identifier_length | secondary | 2.736 | 3.083 | 0.887 | n/a |
| LPL | pc | primary metric | 0.915 | 0.97 | 0.944 | 0.794 [0.742, 0.849] |
| LPL | loc | secondary | 17.58 | 7.87 | 2.234 | 1.249 [1.041, 1.497] |
| LPL | statements | secondary | 14.815 | 9.559 | 1.55 | 0.938 [0.783, 1.124] |
| LPL | max_nesting | secondary | 1.278 | 0.773 | 1.653 | 0.637 [0.560, 0.724] |
| LPL | comment_ratio | secondary | 0.335 | 0.25 | 1.339 | 1.076 [0.975, 1.188] |
| LPL | method_calls | secondary | 13.964 | 9.243 | 1.511 | 0.997 [0.845, 1.176] |
| LPL | mean_identifier_length | secondary | 2.495 | 3.083 | 0.809 | n/a |
| LPL R5 | pc | primary metric | 0.864 | 0.97 | 0.891 | 0.969 [0.907, 1.035] |
| LPL R5 | loc | secondary | 18.198 | 7.87 | 2.312 | 1.415 [1.143, 1.752] |
| LPL R5 | statements | secondary | 15.227 | 9.559 | 1.593 | 0.899 [0.742, 1.089] |
| LPL R5 | max_nesting | secondary | 1.295 | 0.773 | 1.674 | 0.597 [0.519, 0.688] |
| LPL R5 | comment_ratio | secondary | 0.336 | 0.25 | 1.342 | 1.101 [0.997, 1.217] |
| LPL R5 | method_calls | secondary | 14.17 | 9.243 | 1.533 | 0.983 [0.825, 1.170] |
| LPL R5 | mean_identifier_length | secondary | 2.528 | 3.083 | 0.82 | n/a |
| MA | lcom | primary metric | 0.103 | 0.653 | 0.158 | n/a |
| MA | loc | secondary | 89.513 | 167.058 | 0.536 | n/a |
| MA | statements | secondary | 53.801 | 268.241 | 0.201 | n/a |
| MA | max_nesting | secondary | 1.612 | 1.503 | 1.072 | n/a |
| MA | comment_ratio | secondary | 0.145 | 0.235 | 0.615 | n/a |
| MA | method_calls | secondary | 56.578 | 224.084 | 0.252 | n/a |
| MA | mean_identifier_length | secondary | 2.408 | 2.913 | 0.827 | n/a |
| MA | nom | secondary | 10.352 | 28.685 | 0.361 | n/a |
| MA | nof | secondary | 6.987 | 8.295 | 0.842 | n/a |

**A4 (EXPLORATORY): Thorndike Case II correction**
- r is the point-biserial correlation between the primary metric and the unanimous label. u = SD(universe) / SD(annotated) of the primary metric.
- Implied AUC = Φ(d/√2), with d = r / √((1 − r²)pq).
- **Assumptions:**
  - the relation is linear and homoscedastic across the full metric range;
  - selection into the annotated set depends on the metric only;
  - the label/metric relation is binormal.
- These corrected values are model-based extrapolations, not observed quantities. The observed AUC from RQ2 is shown for comparison.
- CI: bootstrap over entities (B = 2000) with u fixed.

| smell | n | point_biserial_r | u_SD_universe_over_annotated | corrected r [95% CI] | implied_AUC_uncorrected | implied AUC corrected [95% CI] | observed_AUC_RQ2 |
|---|---|---|---|---|---|---|---|
| CM | 1695 | 0.076 | 0.925 | 0.071 [0.028, 0.111] | 0.546 | 0.542 [0.517, 0.567] | 0.541 |
| LPL | 1326 | -0.121 | 1.06 | -0.128 [-0.182, -0.075] | 0.428 | 0.424 [0.391, 0.455] | 0.433 |
| LPL R5 | 1189 | 0.025 | 1.122 | 0.028 [-0.035, 0.090] | 0.515 | 0.516 [0.480, 0.552] | 0.514 |

For CM and LPL, u is close to or below 1. The universe distribution is concentrated below the band: 0.968 of methods have cc < 5 and 0.948 have pc < 3. An SD-based correction therefore does not represent restriction to an upper-tail band. A1, the share of snippets and of tool flags inside the band, is the more direct description of the restriction.

Tables: `tables/range_A1_tool_flags.csv`, `range_A2_trend.csv`, `range_A2_share_by_value.csv`, `range_A3_sd_ratios.csv`, `range_A4_thorndike.csv`.

**Summary.** CM: 0.030 of snippets inside the band, 0.819 of DesigniteJava-flagged snippets inside the band; LPL: 0.052 of snippets inside the band, 0.989 of DesigniteJava-flagged snippets inside the band; LPL R5: 0.022 of snippets inside the band, 0.989 of DesigniteJava-flagged snippets inside the band; MA: 0.169 of snippets inside the band, 1.000 of DesigniteJava-flagged snippets inside the band.

## 8 External check: C# dataset (plan.md §6.2)

### 8.1 B0 audit

**Analysis type: descriptive audit (B0).** Nothing beyond counts is computed; B1 waits for the PI's go-ahead.

- Source: Zenodo 10.5281/zenodo.10475432 (v1.0, 2024-01-09, CC BY 4.0), by Prokić, Luburić, Slivka, Grujić and Kovačević.
- Six xlsx files, MD5-verified: three datasets (one per smell) and three per-annotator heuristic files.

| smell | file | snippets | unique_snippet_ids | granularity | projects | annotator_columns | snippets_by_n_annotations | severity_values_individual | final_distribution | final_missing | snippets_without_strict_majority | final_differs_from_strict_majority | n_metrics | duplicate_metric_names |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Data Class | DataSet_Data_Class.xlsx | 231 | 231 | class | 15 | 3 | {2: 202, 3: 29} | [0, 1, 2] | {0: 216, 1: 12, 2: 3} | 0 | 0 | 0 | 31 | none |
| Feature Envy | DataSet_Feature_Envy.xlsx | 220 | 220 | method | 11 | 3 | {2: 111, 3: 109} | [0, 1, 2, 3] | {0: 184, 1: 28, 2: 8} | 0 | 0 | 0 | 19 | none |
| Refused Bequest | DataSet_Refused_Bequest.xlsx | 209 | 209 | class | 15 | 3 | {2: 161, 3: 48} | [0, 1, 2] | {0: 173, 1: 35, 2: 1} | 0 | 0 | 0 | 31 | BOvR |

Pairwise exact agreement of the released severity scores (descriptive; uses the annotator columns as released):

| smell | annotator_pair | snippets_both | exact_agreement |
|---|---|---|---|
| Data Class | ann1-ann2 | 132 | 0.947 |
| Data Class | ann1-ann3 | 29 | 0.793 |
| Data Class | ann2-ann3 | 128 | 0.945 |
| Feature Envy | ann1-ann2 | 166 | 0.88 |
| Feature Envy | ann1-ann3 | 109 | 0.817 |
| Feature Envy | ann2-ann3 | 163 | 0.89 |
| Refused Bequest | ann1-ann2 | 127 | 0.953 |
| Refused Bequest | ann1-ann3 | 48 | 0.5 |
| Refused Bequest | ann2-ann3 | 130 | 0.8 |

Provided metrics:

| smell | metrics |
|---|---|
| Data Class | CLOC, CELOC, NMD, NAD, NMD_NAD, WMC, WMC_NO_CASE, LCOM, LCOM3, LCOM4, TCC, ATFD, CNOR, CNOL, CNOC, CNOA, NOPM, NOPF, CMNB, RFC, CBO, DIT, DCC, ATFD_10, NIC, WOC, NOPA, NOPP, WMCNAMM, BUR, BOvR |
| Feature Envy | CYCLO, CYCLO_SWITCH, MLOC, MELOC, NOP, NOLV, NOTC, MNOL, MNOR, MNOC, MNOA, NONL, NOSL, NOMO, NOPE, NOLE, MMNB, NOUW, AID |
| Refused Bequest | CLOC, CELOC, NMD, NAD, NMD_NAD, WMC, WMC_NO_CASE, LCOM, LCOM3, LCOM4, TCC, ATFD, CNOR, CNOL, CNOC, CNOA, NOPM, NOPF, CMNB, RFC, CBO, DIT, DCC, ATFD_10, NIC, WOC, NOPA, NOPP, WMCNAMM, BOvR, BOvR |

```
Data Class: projects = https://github.com/Jackett/Jackett, https://github.com/NickeManarin/ScreenToGif, https://github.com/OpenRA/OpenRA, https://github.com/Radarr/Radarr, https://github.com/Ryujinx/Ryujinx, https://github.com/ShareX/ShareX, https://github.com/Sonarr/Sonarr, https://github.com/Unity-Technologies/ml-agents, https://github.com/duplicati/duplicati, https://github.com/egordorichev/BurningKnight, https://github.com/files-community/Files, https://github.com/jellyfin/jellyfin, https://github.com/mRemoteNG/mRemoteNG, https://github.com/mbdavid/LiteDB, https://github.com/ppy/osu
Data Class heuristics file Data_Class_Heuristics.xlsx: 231 snippets; heuristics per annotator: No logic in methods., Used by other classes.
Feature Envy: projects = https://github.com/JamesNK/Newtonsoft.Json, https://github.com/NickeManarin/ScreenToGif, https://github.com/Radarr/Radarr, https://github.com/ShareX/ShareX, https://github.com/Sonarr/Sonarr, https://github.com/Unity-Technologies/ml-agents, https://github.com/duplicati/duplicati, https://github.com/files-community/Files, https://github.com/gitextensions/gitextensions, https://github.com/jellyfin/jellyfin, https://github.com/ppy/osu
Feature Envy heuristics file Feature_Envy_Heuristics.xlsx: 220 snippets; heuristics per annotator: Function has method chains., Function uses foreign data., Function has few foreign providers., Function does not belong here semantically.
Refused Bequest: projects = https://github.com/Jackett/Jackett, https://github.com/JamesNK/Newtonsoft.Json, https://github.com/NickeManarin/ScreenToGif, https://github.com/Radarr/Radarr, https://github.com/Ryujinx/Ryujinx, https://github.com/ShareX/ShareX, https://github.com/SixLabors/ImageSharp, https://github.com/Sonarr/Sonarr, https://github.com/Unity-Technologies/ml-agents, https://github.com/duplicati/duplicati, https://github.com/files-community/Files, https://github.com/gitextensions/gitextensions, https://github.com/jellyfin/jellyfin, https://github.com/mRemoteNG/mRemoteNG, https://github.com/ppy/osu
Refused Bequest heuristics file Refused_Bequest_Heuristics.xlsx: 209 snippets; heuristics per annotator: Few parent members used., Many members overriden., Unnecessary hierarchy.
```

**Annotation design (from the released columns)**

| smell | rated_by_annotator_1 | rated_by_annotator_2 | rated_by_annotator_3 | snippets_with_2_annotations | of_which_agree | snippets_with_3_annotations |
|---|---|---|---|---|---|---|
| Data Class | 132 | 231 | 128 | 202 | 202 | 29 |
| Feature Envy | 166 | 220 | 163 | 111 | 111 | 109 |
| Refused Bequest | 127 | 209 | 130 | 161 | 161 | 48 |

**Proposed primary metric per smell (for the PI's decision; not yet used).**
Metric definitions are from the Clean-CaDET platform's `CaDETMetrics.cs`, linked from the Zenodo record. The detection rules are from Lanza & Marinescu, *Object-Oriented Metrics in Practice* (Springer, 2006), and Marinescu, "Detection strategies" (ICSM 2004).

| smell | proposed primary metric | direction | justification | alternatives |
|---|---|---|---|---|
| Data Class | **WOC** (Weight Of Class: functional public methods / all public members) | lower = smellier | The defining condition of the Lanza–Marinescu Data Class strategy is WOC < 1/3: the interface exposes data rather than services. The other conditions (NOPA+NOAM, WMC) are size/complexity guards. | NOPA_NOPP-type counts (NOPA, NOPP); WMCNAMM |
| Feature Envy | **AID** (Access to Import Data: foreign attributes and methods accessed by the method) | higher = smellier | The Lanza–Marinescu Feature Envy strategy is ATFD > FEW ∧ LAA < 1/3 ∧ FDP ≤ FEW. ATFD is its primary "uses foreign data" condition. LAA and FDP are not provided at method level; AID is the method-level analogue of ATFD in this dataset. | none of LAA/FDP is available; the class-level ATFD is not a method metric |
| Refused Bequest | **BUR** (Base-class Usage Ratio) | lower = smellier | The Lanza–Marinescu Refused Bequest strategy is (NProtM > FEW ∧ BUR < 1/3) ∨ BOvR < 1/3, plus complexity guards. BUR is the "uses few inherited members" condition. | BOvR (Base-class Overriding Ratio) |

**Issues to decide before B1:**
1. **Adjudicated annotation.** Every snippet with exactly 2 annotations shows perfect agreement (Data Class 202/202; Feature Envy 111/111; Refused Bequest 161/161). A third annotation exists only where disagreement occurred. The released per-annotator scores therefore over-represent agreement, so a raw alpha would be biased upward and not comparable with DACOS. Options:
   - (a) alpha on the first two annotations only. This is not possible as released, because the slot of the "first" pair is not identifiable when three exist.
   - (b) report the raw alpha with this caveat.
   - (c) report only the share of snippets that needed a third annotator. Annotator 2 rated every snippet; annotators 1 and 3 split the second slot.
2. **Refused Bequest header.** The Refused Bequest sheet labels two adjacent columns `BOvR`, where the Data Class sheet has `BUR, BOvR` in the same positions. The single class present in both sheets has identical values in the two BUR positions. I propose treating the first column as BUR, but this rests on one shared class and the column order.
3. **Few positives.** Final severity ≥ 1 occurs in Data Class 15/231; Feature Envy 36/220; Refused Bequest 36/209. RQ2 CIs will be wide, especially for Data Class.
4. **Severity scale.** Individual scores are 0–3 for Feature Envy and 0–2 for the other two (observed values). Ordinal alpha applies to severity and nominal alpha to presence (severity ≥ 1).

Tables: `tables/external_B0_audit.csv`, `external_B0_metrics.csv`, `external_B0_annotator_pairs.csv`. Log: `logs/external_audit.txt`.

### 8.2 B1 (plan.md §7.2)

**Analysis type: external check** (not a replication). plan.md §7.2.

**Context.**
- This dataset was **not sampled from a borderline band**. It is external context for DACOS, not a replication.
- However, per the dataset author's doctoral dissertation (S. Prokić, University of Novi Sad, 2025, p. 68), its snippets were pre-filtered one-sidedly on the same metrics:
  - Data Class: WOC < 0.33 ∨ NOPA > 1 ∨ NOPP > 1 (non-private, non-abstract classes)
  - Feature Envy: AID ≥ 4
  - Refused Bequest: BUR < 0.33 (non-abstract classes with a parent and with methods other than constructors)
  - The primary metric is therefore range-restricted on one side.
- Annotation was adjudicated. Snippets were re-served until the annotations agreed, and conflicting annotations were discussed and could be revised to reach consensus (p. 66).
- Three annotators took part (p. 67).

**Agreement** (no raw alpha, because the design is adjudicated).
- (a) Share of snippets that needed a third rating: the pre-adjudication disagreement rate, with a bootstrap CI over snippets (B = 2000).
- (b) Exact bounds on first-pair Krippendorff's alpha (ordinal, values 0–3):
  - 2-rated snippets keep their released pair.
  - Each 3-rated snippet contributes annotator 2 plus annotator 1 or annotator 3. Snippets of the same type (a2, {a1, a3}) are interchangeable, so every count combination is enumerated.
  - Caveat: released scores may have been revised after discussion, so these bound the agreement of the released first pairs, not necessarily the original pre-discussion ratings.

| smell | snippets | snippets_3_rated | third-rating share [95% CI] | with_a_choice_(a1≠a3) | choice_types | assignments_enumerated | first-pair ordinal alpha: min – max |
|---|---|---|---|---|---|---|---|
| Data Class | 231 | 29 | 0.126 [0.087, 0.173] | 6 | 4 | 36 | 0.779 – 0.927 |
| Feature Envy | 220 | 109 | 0.495 [0.432, 0.559] | 20 | 5 | 960 | 0.651 – 0.920 |
| Refused Bequest | 209 | 48 | 0.230 [0.172, 0.287] | 24 | 3 | 480 | 0.606 – 0.927 |

**Labels.**
- Consensus rule found in the data: the released final score equals the strict majority of the released individual scores for every snippet (§8.1).
- Primary: smelly = final ≥ 1. Sensitivity: final ≥ 2.

| smell | snippets | positives_final_ge1 | share_ge1 | positives_final_ge2 | share_ge2 |
|---|---|---|---|---|---|
| Data Class | 231 | 15 | 0.065 | 3 | 0.013 |
| Feature Envy | 220 | 36 | 0.164 | 8 | 0.036 |
| Refused Bequest | 209 | 36 | 0.172 | 1 | 0.005 |

**Primary metric versus consensus.**
- Each metric is oriented so that higher = smellier before the AUC is computed. The Youden rule is reported on the original scale.
- LAA and FDP are **not provided** in the Feature Envy sheet, so no secondary metrics are added.
- **Refused Bequest header is ambiguous.** The sheet labels two adjacent columns `BOvR`; the Data Class sheet has `BUR, BOvR` in those positions. Neither the Zenodo description nor the dissertation (which defines BUR and BOvR, p. 10) gives the column order. Both columns are therefore reported as "first column" and "second column", and neither is chosen as BUR.
- CIs: bootstrap over snippets (B = 2000) and a cluster bootstrap over projects. Rows with fewer than 5 positives or negatives report counts only. Snippets with a missing metric are dropped (counts shown).

| smell | metric | orientation | label | n_with_metric | missing_metric | positives | share_positive | projects | ROC-AUC [95% CI snippets] | [95% CI projects] | Youden rule [95% CI of cut] | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Data Class | WOC | lower = smellier (negated) | final ≥ 1 (primary) | 231 | 0 | 15 | 0.065 | 15 | 0.424 [0.302, 0.545] | [0.264, 0.554] | WOC ≤ 0.143 [0.0909, 0.286] |  |
| Data Class | WOC | lower = smellier (negated) | final ≥ 2 (sensitivity) | 231 | 0 | 3 | 0.013 | 15 | – | – | – | fewer than 5 positives or negatives: counts only |
| Feature Envy | AID | higher = smellier | final ≥ 1 (primary) | 220 | 0 | 36 | 0.164 | 11 | 0.683 [0.577, 0.782] | [0.617, 0.757] | AID ≥ 11 [7, 17] |  |
| Feature Envy | AID | higher = smellier | final ≥ 2 (sensitivity) | 220 | 0 | 8 | 0.036 | 11 | 0.722 [0.503, 0.907] | [0.438, 0.883] | AID ≥ 7 [7, 29] |  |
| Refused Bequest | first `BOvR`-labelled column | lower = smellier (negated) | final ≥ 1 (primary) | 168 | 41 | 30 | 0.179 | 15 | 0.372 [0.283, 0.463] | [0.212, 0.602] | first `BOvR`-labelled column ≤ 0.167 [0.154, 0.25] |  |
| Refused Bequest | first `BOvR`-labelled column | lower = smellier (negated) | final ≥ 2 (sensitivity) | 168 | 41 | 1 | 0.006 | 15 | – | – | – | fewer than 5 positives or negatives: counts only |
| Refused Bequest | second `BOvR`-labelled column | lower = smellier (negated) | final ≥ 1 (primary) | 41 | 168 | 4 | 0.098 | 11 | – | – | – | fewer than 5 positives or negatives: counts only |
| Refused Bequest | second `BOvR`-labelled column | lower = smellier (negated) | final ≥ 2 (sensitivity) | 41 | 168 | 0 | 0.0 | 11 | – | – | – | fewer than 5 positives or negatives: counts only |

Tables: `tables/external_B1_agreement.csv`, `external_B1_labels.csv`, `external_B1_auc.csv`.

## 9 Exploratory

**Analysis type: exploratory.** Not part of the pre-registered primary or robustness analyses; A4 in §7 is also exploratory.

**DACOSX in-distribution performance** (sanity check; not in plan.md).
- Setting: GroupKFold(5) by project within DACOSX, with the same models and features as RQ4.
- These scores are expected to be near-perfect, because DACOSX labels are thresholds on features in the model.

| smell | model | n | F1 | MCC | ROC_AUC |
|---|---|---|---|---|---|
| CM | LR | 83549 | 0.9974 | 0.9974 | 1.0 |
| CM | RF | 83549 | 1.0 | 1.0 | 1.0 |
| LPL | LR | 83110 | 1.0 | 1.0 | 1.0 |
| LPL | RF | 83110 | 1.0 | 1.0 | 1.0 |

Table: `tables/exploratory_dacosx_in_distribution.csv`.

**CM C3 "DACOSX + DACOS" collapse under equal source weight** (exploratory; not in plan.md §4).

Method:
- CM best model (LR) with section-B fold hyperparameters on the 25 splits, tested on held-out DACOS unanimous entities.
- Class-balanced weights are computed within each source, then rescaled so that DACOSX and DACOS contribute equal total weight. The model's own class weighting is switched off, so the weights are not applied twice.

| model | variant | macro_F1 | MCC | predicted_smelly_share |
|---|---|---|---|---|
| LR | as in C3 (pooled class weights) | 0.400 ± 0.000 [0.392, 0.408] | 0.000 ± 0.000 [0.000, 0.000] | 1.0 |
| LR | equal source weight (class-balanced within source) | 0.508 ± 0.004 [0.485, 0.530] | 0.077 ± 0.009 [0.030, 0.123] | 0.43 |

The collapse does not persist under equal source weighting: MCC 0.077 [0.030, 0.123] with predicted-smelly share 0.430, versus MCC 0.000 and share 1.000 with pooled weights. Table: `tables/exploratory_cm_c3_reweight.csv`. Runtime 11s.

## 10 Deviations from plan.md and known limitations

**Deviations from plan.md**

1. **Data loading.** MySQL/MariaDB was unavailable, so the dumps were converted to SQLite with a purpose-written parser (`src/convert_sql.py`). Row counts match the dump statements; see section 1.1.
2. **CK not used.** The primary metrics are the stored DesigniteJava values, and NOM and NOF are stored too, so no CK computation was needed (plan §1.5–1.6).
3. **Per-annotator analyses dropped.** RQ1's per-annotator counts and yes-rates are not computable, because the data have no annotator ids (D12).
4. **MA excluded from models.** Multifaceted Abstraction fails the D8 rule after filtering (8 unanimous benign entities), so it is excluded from RQ4. Its RQ2 statistics are reported with very wide CIs.
5. **DACOSX in-distribution scores.** These were not listed as an analysis in plan.md and are reported under EXPLORATORY.
6. **Robustness checks.** R1–R7 are complete (§4). R1 and R2 appear as extra columns of the robustness summary table, and RQ3/RQ5 rows are included. In every RQ4 robustness cell the DACOSX-trained models are unchanged; only the DACOS test labels vary.
7. **LOPO CV.** Leave-one-project-out with pooled out-of-fold predictions was accepted in Prompt 2 as the plan's generalisation analysis. Section 5.4 adds per-project distributions.
8. **C3 training-source ablation.** DACOSX entries from the held-out fold's projects are excluded from training, so that no project is in both train and test. plan.md §4.5 C did not state this; it is a protocol clarification, and section E asserts it holds in all 25 splits.
9. **Ablation hyperparameters.** All ablation variants reuse the full model's tuned hyperparameters per fold, as pre-registered. The "(i) primary only" and similar subsets are therefore not individually tuned.
10. **CM ablation, sensitivity and calibration use one model.** CM's best model in B is LR, so "best model and LR" is the same model.
11. **SHAP beeswarm.** It is drawn as a jittered strip plot in the paper figure style, rather than with `shap.summary_plot`. The SHAP values themselves come from `shap.TreeExplainer`.
12. **XGBoost runtime library.** No system OpenMP is installed, so xgboost loads scikit-learn's bundled `libomp` via `DYLD_LIBRARY_PATH`, which `run_all.sh` sets.
13. **R3 applies no consistency filter.** The filter is defined on the checkbox, so it does not apply when `is_smell` is the answer column (plan.md §4.1).
14. **RQ5 robustness BH family.** In robustness runs, the BH family is that variant's CM and LPL tests.
15. **R5 ablation models.** In the R5 rerun (§4.4), C1/C3 use the R5 best model (SVM) and LR, as pre-registered. The primary best model (GB) was not rerun under R5, so side-by-side cells for models that were not the best model of a run show "n/a".
16. **SHAP output shape.** shap 0.46 returns a 3-D array (n, features, classes) for scikit-learn forests. The "smelly" slice is used. This affects only the R5 SHAP (best tree model RF); the primary best tree model is GB.
17. **Human-ceiling designations are simulated through sufficient statistics.** Only split entities depend on the random role assignment, so each designation is drawn as binomial counts. This is exactly equivalent to entity-level role draws; a brute-force check agreed to 1e-4.
18. **Near-duplicate ceiling.** Designations are drawn as multinomial cell counts per pair type (pairs sharing the two entities' yes-rates). This is equivalent to per-pair draws.
19. **Feature extraction now covers every sample path** (the §6.1 snippet universe). The values for the previously computed 95,496 paths are verified identical, so no earlier table changes.
20. **Paper figures** (`results/paper_figures/`) are re-drawn from the committed tables at IEEE sizes. They contain no new analysis.
21. **External dataset.** `openpyxl` 3.1.5 is pinned to read the xlsx files. B0 only reads and counts. The Refused Bequest header assumption (first `BOvR` column = BUR) is a proposal awaiting the PI's decision and is not used in any result.
22. **Agreement anatomy.** Entities whose snippet file is missing from `files.zip` get no duplicate key and are excluded from the duplicate-group comparisons (1.1–1.2) only. A logistic fit with quasi-complete separation (LPL R4) is reported as not estimable, not as an OR.
23. **External check sources.** The sampling filters and the adjudication-by-discussion are taken from the dataset author's doctoral dissertation (Prokić, Univ. Novi Sad, 2025, pp. 66–68). The Zenodo record does not describe them.
24. **External Refused Bequest columns.** Both `BOvR`-labelled columns are reported, and neither is chosen as BUR, because the header order is not documented. The second column has only 41 non-missing values and 4 positives, so it is reported as counts only.

**Known limitations**

- **No annotator identity or timestamps.**
  - The same annotator may have rated a snippet twice, and this cannot be checked.
  - Annotator-level effects cannot be modelled.
  - Whether the answer runs (section 1.7) come from individual annotators or from recording artefacts cannot be determined.
- **The consistency filter overlaps the runs.** All 416 excluded CM annotations and 917 of the 965 excluded MA annotations lie inside answer runs (section 1.6). The primary results therefore depend partly on how those stretches are handled. R4 and R6 quantify this (§4.1, §4.3).
- **The pc = 3 LPL entities.**
  - All 274 annotations on the 137 pc = 3 LPL entities are "yes", and all lie inside the 1,054-answer run (ids 10790–11063).
  - They form the whole pc = 3 column of the LPL share-smelly table in RQ2.
  - R5 repeats the analysis without them (§4.1).
- **Two annotations per entity.** For most entities, majority labels coincide with unanimous labels and every split is a tie. The labelled sets in RQ2 and RQ4 therefore exclude all disagreement cases.
- **MA labels are very imbalanced.** After filtering, 400 of 408 unanimous MA entities are smelly. Nominal alpha is near 0 even though percent agreement is 0.79; this is the expected behaviour of chance-corrected agreement under such a skewed marginal.
- **Thresholds.**
  - The DesigniteJava defaults come from the current master branch (commit 3321c56); the DesigniteJava version DACOS used is not recorded in the data.
  - The annotated metric ranges differ from the paper's Table I.
- **Youden cut-offs are chosen and evaluated on the same data,** so their P/R/F1 are optimistic.
- **Grouped CV uses 10 projects of unequal size** (section 2), so fold sizes vary.
- **The computed secondary features come from a lightweight lexer** (`src/features.py`), not a full Java parser. Method-call counting uses token heuristics, documented in the module docstring.
- **Label noise in near-duplicates.** Many near-duplicate code groups carry conflicting human labels (CM 27 of 56 groups, LPL 62 of 160; §5.5). Structurally identical snippets were judged differently, which caps any model's attainable accuracy.
- **R4 changes LPL a lot.** Removing run annotations leaves 254 LPL entities (from 1,694) and only 4 split LPL entities. R4 results for LPL rest on a small, selected subset.
- **Friedman/Nemenyi blocks are not independent.** The 25 folds come from 5 repeats of the same data, so the test is anti-conservative.
- **Class weighting and calibration.** Balanced class weights move predicted probabilities towards 0.5. The calibration results describe the weighted models as trained.
- **CM learning curve is non-monotone.** macro-F1 lies between 0.506 and 0.530 at every training fraction. The pre-registered plateau rule classifies it as not plateaued.
- **Feature selection is unstable across folds** (mean pairwise Jaccard 0.19 for CM, 0.57 for LPL), so the full feature set is kept.
- **Two human ceilings disagree strongly.**
  - Within an entity, two annotations agree at MCC 0.806 (CM) and 0.540 (LPL).
  - Between structurally identical snippets of the same project, agreement is MCC 0.082 (CM) and 0.099 (LPL).
  - The data cannot distinguish genuine context differences between near-duplicates from same-annotator or same-session effects within an entity. Annotator ids and timestamps are absent.
- **Range restriction is a property of the design.** The annotated band holds 3.0% (CM) and 5.2% (LPL) of all methods but 81.9% and 98.9% of DesigniteJava flags. The SD-based Thorndike correction (A4, exploratory) cannot represent this upper-tail restriction.
- **External dataset annotation is adjudicated.** Every snippet with exactly two annotations agrees, and a third annotation exists only after disagreement. Raw agreement on the released scores would therefore be biased upward relative to DACOS.
- **Same-snippet agreement is a sequential, tool-mediated measurement.** On matched entities it exceeds cross-snippet agreement, also for exact duplicates with identical names. Its relation to the annotation-id gap runs in opposite directions for CM (rising) and LPL (falling). The data cannot separate annotator, session and serving-order effects.
- **The external dataset is metric-filtered and adjudicated.** Its AUCs are computed within one-sided ranges of the same metrics, and its agreement is bounded rather than observed.
- **Data-integrity cross-check with lizard 1.17.13.** Cyclomatic complexity matches DesigniteJava exactly for 59% of method snippets (Spearman 0.92); parameter count matches for 96%.

## 11 Reproducibility notes

- Regenerate everything with `bash run_all.sh` from `paper3/`. It downloads the data if absent, verifies the MD5s and rebuilds every table, figure and this file.
- Python 3.9.6 (Darwin arm64). Pinned packages (full list in `requirements.txt`): krippendorff==0.8.1, lizard==1.17.13, matplotlib==3.9.4, numpy==1.26.4, pandas==2.2.3, scikit-learn==1.5.2, scipy==1.13.1, shap==0.46.0, statsmodels==0.14.4, xgboost==2.1.4.
- Seeds: every bootstrap and model uses seed 20261021 (`numpy.random.default_rng`, `random_state`). Bootstrap B = 2000.
- GroupKFold and LeaveOneGroupOut are deterministic. The random forest runs single-threaded (scikit-learn default `n_jobs`), because multi-threaded probability accumulation varied in the last floating-point digits between runs.
- Determinism check: a full `run_all.sh` regeneration from freshly converted databases (with the model cache cleared) reproduced every committed CSV table byte for byte, including all Step 1–3 tables produced in earlier, separate runs. `rq4_predictions.csv.gz` differs only in its gzip header timestamp; its decompressed content is identical.
- Parallelism: Step 3 parallelises over outer folds with `joblib`. Each fold's model is single-threaded and seeded (RF/GB/XGB `n_jobs=1`, `random_state = 20261021 + repeat`), so results do not depend on scheduling.
- xgboost uses scikit-learn's bundled `libomp` (`DYLD_LIBRARY_PATH` set by `run_all.sh`), because no system OpenMP runtime is installed.
- Code commit at report build: `c95dd71e8b81837301ab387b55055d323d6487b7`; the working tree may contain uncommitted changes at build time.
- Runtime of the last `run_all.sh` (seconds), total 1098s:

| step | seconds |
|---|---|
| convert_main | 4 |
| convert_extended | 3 |
| audit | 3 |
| features | 21 |
| dataset_audit | 5 |
| rq1 | 2 |
| rq2 | 6 |
| rq4 | 23 |
| rq3 | 5 |
| rq5 | 11 |
| robustness | 97 |
| run_anatomy | 4 |
| step3_A_B | 105 |
| step3_C | 158 |
| step3_E | 32 |
| step3_D | 15 |
| step3_F_H | 13 |
| step3_G_I_J | 57 |
| step3_R5 | 438 |
| human_ceiling | 41 |
| extras | 13 |
| range_restrict | 5 |
| external_B0 | 1 |
| agreement | 26 |
| external_B1 | 7 |
| build_report | 1 |
| paper_figures | 2 |

- Logs: `results/logs/` (one log per step, plus `audit.txt`, `features.log`, `lizard_crosscheck.csv` and `runtime.tsv`).

## 12 Completion status

- Complete: Prompt 2 (Step 1 R3–R7; Step 2 RQ3, RQ5, R1, R2, R3–R6 on RQ3/RQ5; Step 3 A–J), Prompt 3 sections 1–4, and Prompt 3B part A (range restriction).
- Prompt 3B part B (B0 audit) and Prompt 4 (Part 1 agreement anatomy 1.1–1.5; Part 2 external check B1) are complete. No section was skipped for time.

## 13 Headline numbers

| # | number | value [95% CI] | analysis type | table |
|---|---|---|---|---|
| 1 | Krippendorff's alpha, CM | 0.804 [0.774, 0.832] | primary | `tables/rq1_agreement.csv` |
| 2 | Krippendorff's alpha, LPL | 0.540 [0.498, 0.577] | primary | `tables/rq1_agreement.csv` |
| 3 | Krippendorff's alpha, MA | 0.020 [-0.035, 0.077] (percent agreement 0.786) | primary | `tables/rq1_agreement.csv` |
| 4 | Krippendorff's alpha, CM, without the consistency filter | 0.599 [0.564, 0.635] | robustness R6 | `tables/robustness_long.csv` |
| 5 | Primary-metric ROC-AUC, CM | 0.541 [0.513, 0.568] (one-sided MWU p = 0.0021) | primary | `tables/rq2_threshold_validity.csv` |
| 6 | Primary-metric ROC-AUC, LPL | 0.433 [0.409, 0.458] (one-sided MWU p = 1) | primary | `tables/rq2_threshold_validity.csv` |
| 7 | Primary-metric ROC-AUC, LPL, without the pc = 3 block | 0.514 [0.490, 0.538] | robustness R5 | `tables/robustness_long.csv` |
| 8 | Youden cut-off for CM (cc ≥ c) versus DesigniteJava default cc ≥ 8 | 6 [6, 9] (cut-off value; DesigniteJava default 8) | primary | `tables/rq2_threshold_validity.csv` |
| 9 | RQ4 transfer MCC − GroupKFold MCC, LPL, LR | -0.224 [-0.322, -0.127] | primary | `tables/rq4_paired_differences.csv` |
| 10 | RQ4 transfer MCC − GroupKFold MCC, LPL, LR, `is_smell` labels | 0.078 [-0.008, 0.159] | robustness R3 | `tables/robustness_long.csv` |
| 11 | RQ3 GEE OR per SD of cc, CM | 1.074 [0.964, 1.197] (BH p = 0.29) | primary | `tables/rq3_odds_ratios.csv` |
| 12 | RQ3 GEE OR per SD of pc, LPL | 0.794 [0.742, 0.849] (R5: 0.969 [0.907, 1.035] (robustness_long.csv)) | primary | `tables/rq3_odds_ratios.csv` |
| 13 | Best model MCC, CM (LR, 5×5 grouped CV) | 0.095 [0.052, 0.136] (SD over repeats 0.006) | primary | `tables/model_comparison.csv` |
| 14 | Best model MCC, LPL (GB, 5×5 grouped CV) | 0.232 [0.184, 0.278] (SD over repeats 0.014) | primary | `tables/model_comparison.csv` |
| 15 | Δ MCC, LPL GB, training on DACOSX only versus DACOS | -0.245 [-0.325, -0.169] | primary (ablation C3) | `tables/ablation_LPL.csv` |
| 16 | Best model MCC, LPL R5 (SVM, 5×5 grouped CV) [R5 value of row 14] | 0.269 [0.213, 0.321] (SD over repeats 0.022) | robustness R5 | `tables/model_comparison_LPL_R5.csv` |
| 17 | Δ MCC, LPL R5 SVM, training on DACOSX only versus DACOS [R5 value of row 15] | -0.223 [-0.296, -0.150] | robustness R5 | `tables/ablation_LPL_R5.csv` |
| 18 | Human-vs-human MCC, CM | 0.806 [0.776, 0.833] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 19 | Best model vs one human MCC, CM (LR) | 0.091 [0.053, 0.130] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 20 | Model/human MCC ratio, CM | 0.113 [0.066, 0.162] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 21 | Human-vs-human MCC, LPL | 0.540 [0.498, 0.581] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 22 | Best model vs one human MCC, LPL (GB) | 0.171 [0.133, 0.210] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 23 | Model/human MCC ratio, LPL | 0.317 [0.248, 0.391] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 24 | Human-vs-human MCC, LPL R5 | 0.515 [0.472, 0.558] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 25 | Best model vs one human MCC, LPL R5 (SVM) | 0.201 [0.162, 0.243] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 26 | Model/human MCC ratio, LPL R5 | 0.391 [0.314, 0.478] | primary (human ceiling) | `tables/human_ceiling.csv` |
| 27 | Human-vs-human MCC between same-project near-duplicates, CM | 0.082 [-0.112, 0.301] (104 pairs in 63 groups) | primary (second ceiling) | `tables/human_ceiling_neardup.csv` |
| 28 | Human-vs-human MCC between same-project near-duplicates, LPL | 0.099 [0.039, 0.183] (1393 pairs in 209 groups) | primary (second ceiling) | `tables/human_ceiling_neardup.csv` |
| 29 | Human-vs-human MCC between same-project near-duplicates, LPL R5 | 0.087 [0.028, 0.158] (1352 pairs in 180 groups) | primary (second ceiling) | `tables/human_ceiling_neardup.csv` |
| 30 | Share of DesigniteJava-flagged snippets inside the annotated band, CM | 0.819 (808/987 flags; band holds 0.030 of all snippets) | primary (range restriction, descriptive) | `tables/range_A1_tool_flags.csv` |
| 31 | Share of DesigniteJava-flagged snippets inside the annotated band, LPL | 0.989 (702/710 flags; band holds 0.052 of all snippets) | primary (range restriction, descriptive) | `tables/range_A1_tool_flags.csv` |
| 32 | Within-band logistic OR per unit of the primary metric, CM | 1.105 [1.038, 1.176] (Cochran–Armitage z = 3.15, p = 0.0016) | primary (range restriction) | `tables/range_A2_trend.csv` |
| 33 | Within-band logistic OR per unit of the primary metric, LPL R5 | 1.094 [0.892, 1.341] (Cochran–Armitage z = 0.87, p = 0.39) | primary (range restriction) | `tables/range_A2_trend.csv` |
| 34 | Same-snippet minus cross-snippet human MCC on matched near-duplicate entities, CM | 0.787 [0.563, 1.015] (same 0.865, cross 0.078; 62 groups, 140 entities) | primary (agreement anatomy) | `tables/agreement_matched_neardup.csv` |
| 35 | Same-snippet minus cross-snippet human MCC on matched near-duplicate entities, LPL | 0.358 [0.204, 0.498] (same 0.456, cross 0.098; 207 groups, 614 entities) | primary (agreement anatomy) | `tables/agreement_matched_neardup.csv` |
| 36 | Same-snippet minus cross-snippet human MCC on exact duplicates, CM | 0.623 [0.269, 0.972] (26 groups) | primary (agreement anatomy) | `tables/agreement_exact_dup.csv` |
| 37 | Same-snippet minus cross-snippet human MCC on exact duplicates, LPL | 0.448 [0.217, 0.575] (92 groups) | primary (agreement anatomy) | `tables/agreement_exact_dup.csv` |
| 38 | OR of unanimous per unit log(annotation-id gap), CM | 1.214 [1.133, 1.302] (adjusted for the primary metric; p = 4.5e-08) | primary (agreement anatomy) | `tables/agreement_gap_logit.csv` |
| 39 | OR of unanimous per unit log(annotation-id gap), LPL | 0.186 [0.141, 0.247] (adjusted for the primary metric; p = 1.3e-31) | primary (agreement anatomy) | `tables/agreement_gap_logit.csv` |
| 40 | External C#: share needing a third rating, Data Class | 0.126 [0.087, 0.173] (first-pair ordinal alpha bounds 0.779–0.927) | external check | `tables/external_B1_agreement.csv` |
| 41 | External C#: share needing a third rating, Feature Envy | 0.495 [0.432, 0.559] (first-pair ordinal alpha bounds 0.651–0.920) | external check | `tables/external_B1_agreement.csv` |
| 42 | External C#: share needing a third rating, Refused Bequest | 0.230 [0.172, 0.287] (first-pair ordinal alpha bounds 0.606–0.927) | external check | `tables/external_B1_agreement.csv` |
| 43 | External C#: ROC-AUC of WOC (lower = smellier (negated)), Data Class | 0.424 [0.302, 0.545] (15/231 positives; project-cluster CI [0.264, 0.554]) | external check | `tables/external_B1_auc.csv` |
| 44 | External C#: ROC-AUC of AID (higher = smellier), Feature Envy | 0.683 [0.577, 0.782] (36/220 positives; project-cluster CI [0.617, 0.757]) | external check | `tables/external_B1_auc.csv` |
| 45 | External C#: ROC-AUC of first `BOvR`-labelled column (lower = smellier (negated)), Refused Bequest | 0.372 [0.283, 0.463] (30/168 positives; project-cluster CI [0.212, 0.602]) | external check | `tables/external_B1_auc.csv` |

Rows 1–15 are the Prompt 2 headline numbers; rows 16 onward were added in Prompt 3 and 3B. All values are read programmatically from the listed tables when this file is built, and the same rows are written to `results/paper_numbers.json`.

