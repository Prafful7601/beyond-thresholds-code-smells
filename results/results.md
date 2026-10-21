# Results: human judgment versus metric thresholds in DACOS

Pre-registered plan: `plan.md`. Plan commits, in order:
- `1cde51313c96140bae7ca6515df94f21a4ee2ac3`: Phase 0: data audit and pre-registered analysis plan
- `bd033600ab963246f69698e22f2840dd175fe3b9`: Plan amendment: PI decisions after Phase 0 audit

Scope of this version: **Tier 1** (dataset audit, RQ1, RQ2, RQ4).
- RQ3, RQ5 and the robustness checks R1–R6 are Tier 2 and **have not been run yet**. Their sections below say so.
- **Multifaceted Abstraction is reported descriptively only** (RQ1 agreement and RQ2 threshold ROC), because it fails the D8 eligibility rule after the consistency filter. All model sections skip it.

Conventions:
- The "primary set" is the consistency-filtered annotations (D7), with entities that have ≥ 2 usable annotations.
- With 2 annotations per entity, majority labels with ties excluded are exactly the unanimous entities. RQ2 and RQ4 use those (D11).
- All CIs are 95% bootstrap percentile intervals (B = 2000, seed 20261021), resampling entities, unless stated otherwise.

## 1 Dataset audit: data loading and integrity checks

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
- Feature extraction (`src/features.py`): paths needed: 95510; computed: 95496; missing from zip: 14; failed: 0.
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

Tables: `tables/rq4_data.csv`, `tables/rq4_transfer.csv`, `tables/rq4_paired_differences.csv`, `tables/rq4_predictions.csv.gz`. Figure: `figures/rq4_transfer.pdf` (.png). Runtime 23s.

**Summary.** CM LR: transfer MCC − GroupKFold MCC = -0.024 [-0.072, 0.024]; CM RF: transfer MCC − GroupKFold MCC = 0.025 [-0.036, 0.089]; LPL LR: transfer MCC − GroupKFold MCC = -0.224 [-0.322, -0.127]; LPL RF: transfer MCC − GroupKFold MCC = -0.138 [-0.217, -0.062].

### RQ3 What drives human judgment

Not run yet. This is Tier 2.

### RQ5 Ambiguity

Not run yet. This is Tier 2.

## 4 Robustness

Not run yet. R1 (MA only), R2, R3, R4, R5 and R6 are Tier 2, as specified in plan.md §2–3.

## 5 Exploratory

Nothing in this section was pre-registered in plan.md.

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

## 6 Deviations from plan.md and known limitations

**Deviations from plan.md**

1. **Data loading.** MySQL/MariaDB was unavailable, so the dumps were converted to SQLite with a purpose-written parser (`src/convert_sql.py`). Row counts match the dump statements; see section 1.1.
2. **CK not used.** The primary metrics are the stored DesigniteJava values, and NOM and NOF are stored too, so no CK computation was needed (plan §1.5–1.6).
3. **Per-annotator analyses dropped.** RQ1's per-annotator counts and yes-rates are not computable, because the data have no annotator ids (D12).
4. **MA excluded from models.** Multifaceted Abstraction fails the D8 rule after filtering (8 unanimous benign entities), so it is excluded from RQ4. Its RQ2 statistics are reported with very wide CIs.
5. **DACOSX in-distribution scores.** These were not listed as an analysis in plan.md and are reported under EXPLORATORY.
6. **Robustness R1–R6 deferred to Tier 2,** following the tier order. They are not yet run, including R6, which the PI asked for after the consistency filter.
7. **LOPO CV.** Leave-one-project-out CV is reported alongside GroupKFold(5) as instructed (D6). It is referred to in the PI's instruction as "planned in Prompt 2 section D", whose full text has not been received; its implementation here (pooled out-of-fold predictions, same metrics) is my reading of it.

**Known limitations**

- **No annotator identity or timestamps.**
  - The same annotator may have rated a snippet twice, and this cannot be checked.
  - Annotator-level effects cannot be modelled.
  - Whether the answer runs (section 1.7) come from individual annotators or from recording artefacts cannot be determined.
- **The consistency filter overlaps the runs.** All 416 excluded CM annotations and 917 of the 965 excluded MA annotations lie inside answer runs (section 1.6). The primary results therefore depend partly on how those stretches are handled. R4 and R6 (Tier 2) quantify this.
- **The pc = 3 LPL entities.**
  - All 274 annotations on the 137 pc = 3 LPL entities are "yes", and all lie inside the 1,054-answer run (ids 10790–11063).
  - They form the whole pc = 3 column of the LPL share-smelly table in RQ2.
  - R5 (Tier 2) repeats the analysis without them.
- **Two annotations per entity.** For most entities, majority labels coincide with unanimous labels and every split is a tie. The labelled sets in RQ2 and RQ4 therefore exclude all disagreement cases.
- **MA labels are very imbalanced.** After filtering, 400 of 408 unanimous MA entities are smelly. Nominal alpha is near 0 even though percent agreement is 0.79; this is the expected behaviour of chance-corrected agreement under such a skewed marginal.
- **Thresholds.**
  - The DesigniteJava defaults come from the current master branch (commit 3321c56); the DesigniteJava version DACOS used is not recorded in the data.
  - The annotated metric ranges differ from the paper's Table I.
- **Youden cut-offs are chosen and evaluated on the same data,** so their P/R/F1 are optimistic.
- **Grouped CV uses 10 projects of unequal size** (section 2), so fold sizes vary.
- **The computed secondary features come from a lightweight lexer** (`src/features.py`), not a full Java parser. Method-call counting uses token heuristics, documented in the module docstring.
- **Data-integrity cross-check with lizard 1.17.13.** Cyclomatic complexity matches DesigniteJava exactly for 59% of method snippets (Spearman 0.92); parameter count matches for 96%.

## 7 Reproducibility notes

- Regenerate everything with `bash run_all.sh` from `paper3/`. It downloads the data if absent, verifies the MD5s and rebuilds every table, figure and this file.
- Python 3.9.6 (Darwin arm64). Pinned packages (full list in `requirements.txt`): krippendorff==0.8.1, lizard==1.17.13, matplotlib==3.9.4, numpy==1.26.4, pandas==2.2.3, scikit-learn==1.5.2, scipy==1.13.1, statsmodels==0.14.4.
- Seeds: every bootstrap and model uses seed 20261021 (`numpy.random.default_rng`, `random_state`). Bootstrap B = 2000.
- GroupKFold and LeaveOneGroupOut are deterministic. The random forest runs single-threaded (scikit-learn default `n_jobs`), because multi-threaded probability accumulation varied in the last floating-point digits between runs.
- Two consecutive full runs of `run_all.sh` produced byte-identical CSV tables. `rq4_predictions.csv.gz` differs only in its gzip header timestamp; its decompressed content is identical.
- Code commit at report build: `767552a5d241b66181a50fc51f22babd7356f80e`; the working tree may contain uncommitted changes at build time.
- Runtime of the last `run_all.sh` (seconds), total 65s:

| step | seconds |
|---|---|
| convert_main | 3 |
| convert_extended | 4 |
| audit | 2 |
| features | 19 |
| dataset_audit | 4 |
| rq1 | 1 |
| rq2 | 7 |
| rq4 | 24 |
| build_report | 1 |

- Logs: `results/logs/` (one log per step, plus `audit.txt`, `features.log`, `lizard_crosscheck.csv` and `runtime.tsv`).
