# Analysis plan: human judgment vs. metric thresholds in DACOS

Status: written after the Phase 0 data audit and committed before any outcome analysis.
Every number cited here comes from `results/logs/audit.txt`, produced by `src/audit.py`.
Any analysis not listed here is reported under EXPLORATORY.

## 0. Data and provenance

- Source: Zenodo record 7570428. MD5 checksums are verified against the Zenodo API:
  `DACOSMain.sql` 30fe42bd366da825908e86d901702b79, `DACOSExtended.sql` 081b9725362b34a78e18de303aa35fb2,
  `files.zip` d38d4a2526123c66f6b30e871e50cd4c, `contributors.txt` 453d08349206d1d99822f2e23e72f9f6.
- Loading: no MySQL or MariaDB is available on the analysis machine. Both dumps are converted to SQLite by
  `src/convert_sql.py`, a byte-level parser of the mysqldump `INSERT` tuples. `bit(1)` columns become the integers 0 and 1.
  Metric columns are stored as text in the dump and are cast to numbers at analysis time.
- External references used to interpret the schema (read-only, not executed):
  - The Tagman annotation tool, github.com/SMART-Dal/Tagman at commit 40f3aa6 (2023-01-19).
  - DesigniteJava, github.com/tushartushar/DesigniteJava at commit 3321c56 (2025-03-21), for default thresholds and the LCOM definition.
  - The DACOS paper, arXiv:2303.08729v1, Tables I–II.

## 1. Definitions

### 1.1 Annotation answer (yes/no)
Tagman showed one checkbox per smell listed in `sample.smells` ("Select the smells this sample contains").
`iscm`, `islp` and `isma` are those checkboxes. `is_smell` is set by the tool when any box was ticked (`oneSmellDetected` in the public source).
**Primary answer** for smell S on a snippet offered for S is the S-specific checkbox:
CM uses `iscm`, LPL uses `islp`, MA uses `isma`.
`is_smell` is used only in robustness check R3. `isim` is always 0 and is not used.

### 1.2 Smell membership of a snippet (DACOS)
`sample.smells` codes are 1 = Complex Method (CM), 2 = Long Parameter List (LPL) and 3 = Multifaceted Abstraction (MA). The coding was inferred from the stored metric ranges and confirmed by the Tagman source.
- CM: method snippets whose `smells` field contains 1 (2,275 snippets).
- LPL: method snippets whose `smells` field contains 2 (1,557 snippets), plus 137 method snippets that have an empty `smells` field and pc = 3. All of these were answered via `islp`, and the paper's LPL band is pc 3–6. That gives 1,694 snippets.
- MA: class snippets with `smells` = 3.
- Snippets with `smells` = "1,2" (195) enter both the CM analysis and the LPL analysis, each with its own checkbox.

### 1.3 Unit of analysis
A snippet is a distinct code entity `(is_class, designite_id)`. 332 MA classes were imported twice as separate `sample`
rows that share the same `designite_id`, path and metrics. Their annotations are pooled, which gives 4,783 entities
(1,009 MA classes). For grouping, a snippet's source file is its project/package/Type path, and its project is `project_name` (10 projects).

### 1.4 Human label per snippet
y = number of "yes" answers and n = number of annotations.
- **smelly** if y > n/2
- **benign** if y < n/2
- **ambiguous (tie)** if y = n/2. Ties are kept as their own group and are never assigned to a class.

**Unanimous** means y = 0 or y = n. **Split** means 0 < y < n.
Note: 4,442 of 4,783 entities have exactly 2 annotations. For them, "majority" equals "unanimous" and every split is a tie.

### 1.5 Primary metric per smell (stored DesigniteJava values; not recomputed)
- CM: cyclomatic complexity `method_metrics.cc`.
- LPL: parameter count `method_metrics.pc`.
- MA: `class_metrics.lcom`, DesigniteJava's LCOM. This is the number of connected method/field components, excluding lone fields, divided by the number of methods. It is 0 when there is a single component and -1 when not computable; no annotated MA class has -1.

Reference thresholds:
- DesigniteJava defaults: CM cc ≥ 8; LPL pc ≥ 5; MA LCOM ≥ 0.8 and NOF ≥ 7 and NOM ≥ 7.
- DACOS paper Table I bands: cc 4–7, pc 3–6, LCOM 0.4–0.8.
- **Observed bands in the data differ from Table I:** annotated CM cc 5–14, LPL pc 3–10, MA LCOM 0.402–1.0.

The Designite default is the comparison threshold in RQ2. For MA, precision, recall and F1 are reported both for LCOM ≥ 0.8 alone and for the full three-condition Designite rule.

### 1.6 Secondary features (exactly how each is computed)
Stored values come from the DesigniteJava tables.

Computed values are taken from the snippet's source text in `files.zip`, after removing comments, string literals and char literals with a small Java lexer (`src/features.py`).

| Feature | Methods | Classes |
|---|---|---|
| Lines of code | stored `method_metrics.loc` | stored `class_metrics.loc` |
| Statement count | computed: number of `;` outside comments and literals, excluding the two `;` inside each `for(...)` header, plus the number of `if`, `for`, `while`, `do`, `switch`, `try` keywords | same, over the whole class file |
| Max nesting depth | computed: maximum `{` depth inside the body; the method body itself is depth 0 | computed: maximum `{` depth minus 2 (class body and method body), floored at 0 |
| Comment ratio | computed: comment lines / non-blank lines. A comment line is any line that contains part of a `//` or `/* */` comment, including Javadoc | same |
| Method calls | computed: occurrences of `identifier (` where the identifier is not a Java keyword, plus `new Type(`; the method's own declaration is excluded | same, excluding method/constructor declarations |
| Number of methods / fields | n/a | stored `nom`, `nof` |

A **lizard 1.17.13** cross-check of cc and parameter count against the stored values is reported as a data-integrity check only.
CK is not needed because LCOM, NOM and NOF are stored.

If a snippet's file is missing from the zip, its computed features are missing and the snippet is dropped from feature-based analyses.
The audit found 2 annotated snippets with no file. Every such drop is counted in results.md.

### 1.7 DACOSX
Uses `entry.smellPresented` with codes 3/6 = CM present/absent, 2/5 = LPL present/absent, and 1/4 = MA present/absent. The join is `entry.sampleId = sample.id`.
- **Only granularity-consistent entries are used**: CM and LPL on methods, MA on classes. That leaves CM 428 / 83,181, LPL 172 / 82,987 and MA 645 / 9,269 (present / absent).
- Cross-granularity entries (MA codes on methods; CM/LPL codes on classes; 30,923 in total) carry metric values unrelated to their label and are excluded.
- **Leakage:** 157 DACOSX entries are the same snippet as a DACOS snippet annotated for the same smell (CM 50, LPL 41, MA 66, all "present").
  They are removed from DACOSX before any DACOSX-trained model is fitted.

## 2. Hypotheses, tests and settings

Global settings:
- alpha = 0.05, two-sided.
- Bootstrap: B = 2,000 percentile intervals that resample snippets (entities), seed 20261021.
- All models use `random_state = 20261021`.

**RQ1 Agreement** (descriptive; no null hypothesis). Computed per smell:
- Percent agreement: the mean over snippets of the proportion of agreeing annotation pairs.
- Krippendorff's alpha (nominal, `krippendorff` 0.8.1). It is computed on a reliability matrix in which each snippet's answers fill arbitrary coder rows, because the dump has no annotator identity. Nominal alpha depends only on within-unit value counts, so this is exact. A 95% bootstrap CI is computed over snippets.
- The distribution of vote splits (y, n).

Values are interpreted against Krippendorff's 0.667 / 0.800 benchmarks.
Per-annotator counts and yes-rates **cannot be computed**, because the annotation table has no user column. This is reported as not computable.

**RQ2 Threshold validity.** Uses majority labels with ties excluded. Per smell:
- ROC-AUC of the primary metric alone, with a bootstrap CI and a one-sided Mann–Whitney U p-value for H2a (AUC > 0.5).
- Youden-optimal cut-off: the decision rule is metric ≥ c, with c taken from the observed values. If several values maximise J, the smallest is used. A bootstrap CI is computed for c.
- H2b: the Youden cut-off differs from the Designite default. It is judged by whether the default lies outside the bootstrap CI.
- Precision, recall and F1 (positive class = smelly) at both cut-offs, with bootstrap CIs.

**RQ4 Transfer from extremes to borderline.** Per smell:
- Features: the primary metric plus the secondary features of §1.6.
- Models: `LogisticRegression` (after `StandardScaler`, `class_weight='balanced'`, `max_iter=10000` only to ensure convergence) and `RandomForestClassifier` (`class_weight='balanced'`). Everything else is left at default.
- Transfer: train on DACOSX after the leakage removal in §1.7; test on DACOS majority labels with ties excluded.
- In-distribution comparison: `GroupKFold(5)` by project on DACOS, using pooled out-of-fold predictions.
- Metrics: F1 and MCC at predicted class (probability ≥ 0.5) and ROC-AUC, each with a bootstrap CI over test snippets.
- H4: transfer MCC is lower than in-DACOS CV MCC. Tested with a paired bootstrap CI of the difference on the same DACOS snippets.
- Stated up front: DACOSX labels are functions of the same metrics, so near-perfect in-distribution DACOSX scores are expected and are not a finding.

**RQ3 Drivers of human judgment.** Per smell:
- Annotation-level GEE: binomial with logit link, exchangeable working correlation, clustered by snippet, robust (sandwich) SEs. Predictors are the primary metric and the secondary features, each z-standardised over snippets.
- Reports: odds ratio per 1 SD with 95% CI and Wald p-value, BH-adjusted within smell, plus VIFs.
- H3: OR of the primary metric > 1.
- Also a depth-3 `DecisionTreeClassifier` (`class_weight='balanced'`) on majority labels with ties excluded, with its rules printed via `export_text`.

**RQ5 Ambiguity.** Per smell and feature:
- Unanimous vs split snippets compared with a two-sided Mann–Whitney U test and Cliff's delta, with a bootstrap CI for delta.
- BH correction is applied jointly across all smell × feature tests.

**Robustness** (each repeats RQ2 and RQ4 only):
- R1: only entities with ≥ 3 annotations. The audit shows this leaves about 336 MA entities and fewer than 5 CM/LPL snippets. Analyses are run where both classes have at least 10 snippets; otherwise they are reported as not computable.
- R2: ties counted as smelly.
- R3 *(added after the audit; pending confirmation)*: `is_smell` used as the answer instead of the smell-specific checkbox.
- R4 *(added after the audit; pending confirmation)*: annotations inside constant-answer runs are excluded. A run is a maximal sequence of at least 40 consecutive identical answers within a smell, ordered by annotation id. The rule is fixed now and the runs are listed in the audit log, section 11. Labels are recomputed from the remaining annotations.

## 3. Decisions (confirmed by PI after Phase 0; this section supersedes earlier sections where they conflict)

**Approved as recommended**
- D1: The answer is the smell-specific checkbox (§1.1). The `is_smell` version is robustness check R3.
- D2: The 137 LPL snippets with pc = 3 and an empty `smells` field are included. Robustness check **R5** repeats the analysis without them.
- D3: Duplicate MA sample rows are pooled into one entity.
  - Check performed before this commit: the 332 duplicated classes carry 1,328 annotation rows with distinct ids, answered at different times (each copy has 2 annotations).
  - The (`isma`, `is_smell`) sequences of the two copies are identical for 155 of 332 classes. They are independent answers, not copied rows, so the annotations are pooled (n = 4).
- D4: Wrong-granularity DACOSX entries (30,923) and the 157 DACOS/DACOSX same-smell overlaps are dropped before any training.
- D5: R3 and R4 are planned robustness checks.
  - R4 rule (fixed): runs are maximal sequences of ≥ 40 identical checkbox answers within a smell, ordered by annotation id, computed on the unfiltered checkbox stream.
- D6: In-DACOS CV is `GroupKFold(5)` by `project_name`. **Leave-one-project-out (LOPO)** CV is reported alongside it.

**Changes**
- D7 **Internal-consistency filter (primary analysis, all smells).**
  - An annotation is excluded when its smell's checkbox = 1 but `is_smell` = 0, because it contradicts itself.
  - Checkbox = 0 with `is_smell` = 1 is kept, since another box may have been ticked.
  - Reported first: a per-smell cross-tab of checkbox × `is_smell`, the number excluded, and how many excluded rows fall inside R4 runs.
  - Robustness check **R6** reruns the headline results without the filter.
- D7a: After filtering, an entity's labels use only its usable annotations. Entities with < 2 usable annotations are excluded from agreement and label analyses, and are counted.
- D8 **Eligibility rule.** After filtering, a smell is reported as **descriptive only** (RQ1 agreement and RQ2 threshold ROC) and skips all model sections (RQ4, RQ3 models, Prompt-2 models) if either holds:
  - fewer than 150 entities have ≥ 2 usable annotations, or
  - fewer than 30 unanimous entities fall in its minority class.
  This is stated explicitly in results.md.
- D9: results.md opens with a factual "Dataset audit" section. It includes a figure of answer value against annotation id per smell.
- D10: RQ2 compares against the DesigniteJava defaults as the primary reference. The positions of the paper's Table I ranges relative to the observed annotated ranges are reported descriptively only.

**Consequences accepted**
- D11: With 2 annotations per entity, majority = unanimous and every split is a tie.
  - RQ2, RQ4 and all model sections use **unanimous** entities.
  - RQ5 and the annotation-level RQ3 GEE use **all** entities (with ≥ 2 usable annotations).
- D12: RQ1 drops all per-annotator analyses because no annotator ids exist. Krippendorff's alpha and the vote-split distribution are kept.
  - Limitation recorded: the same annotator may have rated a snippet twice, and this cannot be checked.
- D13: R1 (≥ 3 annotations) is run for MA only, noting that it consists mostly of pooled duplicates.
- D14: DACOSX training keeps the full absent class, with inverse-frequency class weights (`class_weight='balanced'`) and no subsampling.

**Robustness scope (Tier 2).** R1–R6 each repeat the headline results: RQ1 alpha, RQ2 AUC, Youden cut-off and P/R/F1, and RQ4.

**Pre-registered adjustments to Prompt 2.** The full text of Prompt 2 had not been received when this was committed; these are recorded as instructed.
- C2: "majority vote" and "unanimous-only" are the same training set. Three label variants are kept: unanimous only; ties counted as smelly; soft labels (0, 0.5, 1) used as sample weights.
- J: annotator removal is impossible. It is replaced by R4 (run exclusion) and R6 (no consistency filter), applied to the B headline.
- I: each error is tagged as unanimous or split, and flagged as inside or outside an R4 run.

## 4. Prompt 2: robustness, Tier 2 and strengthening analyses (added before any of them was run)

Everything in §1–3 still applies. Scope:
- All model sections (A–J) cover **CM and LPL only**. MA stays descriptive (D8).
- Every reported number is tagged as **primary**, **robustness (R1–R7)** or **exploratory**.
- Compute environment: xgboost 2.1.4 and shap 0.46.0, pinned. xgboost loads scikit-learn's bundled `libomp` through `DYLD_LIBRARY_PATH`, which `run_all.sh` sets.

### 4.1 Annotation-set variants (robustness definitions)

| id | answer column | annotations kept | entity filter |
|---|---|---|---|
| primary | smell checkbox | consistency-filtered (D7) | ≥ 2 usable annotations |
| R1 | checkbox | consistency-filtered | ≥ 3 usable annotations; **MA only** (mostly pooled duplicates) |
| R2 | checkbox | consistency-filtered | as primary, but ties count as smelly in labelled analyses (RQ2, RQ4, B) |
| R3 | `is_smell` | **all** (D7 is defined on the checkbox, so no filter applies when `is_smell` is the answer) | ≥ 2 |
| R4 | checkbox | consistency-filtered, then annotations inside runs (§3 D5 rule, computed on the unfiltered checkbox stream) are removed | ≥ 2 remaining |
| R5 | checkbox | consistency-filtered | LPL only; the 137 pc = 3 entities (empty `smells` field) are removed |
| R6 | checkbox | all (no consistency filter) | ≥ 2 |
| R7c | checkbox | consistency-filtered | entities with at least 2 usable annotations inside the **same** run are removed; applies to RQ1 alpha only |

**Headline numbers repeated under R3–R6 and R7c** (Step 1):
- RQ1 alpha (all smells).
- RQ2 ROC-AUC and Youden cut-off (all smells).
- RQ4 paired MCC difference, transfer − GroupKFold(5), for LR and RF (CM, LPL).

In RQ4 the DACOSX training data never changes; only the DACOS test labels follow the variant.

**Robustness summary table** (`tables/robustness_summary.csv`):
- One row per headline number per smell.
- Columns: primary / R3 / R4 / R5 / R6 / R7c, with n/a where a check does not apply.
- R1 and R2 are reported in their own rows, and RQ3 and RQ5 rows are added in Step 2.

### 4.2 R7 Run anatomy (descriptive)

(a) **Each run** (as listed in `audit_answer_runs.csv`) gets:
- its project composition and primary-metric median and IQR;
- Spearman ρ of annotation id with `sample.id` and with the primary metric, with their p-values;
- its number of project switches along the id order, compared with 2,000 random permutations of the run's own order. The one-sided p is the share of permutations with ≤ the observed number of switches.

The same statistics over the whole smell stream are given as a reference.

(b) **Co-location.**
- Observed: the share of entities, among those with ≥ 2 annotations in the unfiltered stream, that have at least 2 annotations inside the same run.
- Null: the annotation-to-position assignment is permuted within smell 2,000 times, keeping run positions fixed. p = (#null ≥ observed + 1)/(2001).

(c) **Alpha after removing co-located entities** (primary set; R7c above).

### 4.3 Tier 2

**RQ3** (CM, LPL; primary set; all entities with ≥ 2 usable annotations, D11):
- Model: annotation-level **GEE**, `statsmodels` Binomial family with logit link, exchangeable working correlation, groups = entity, robust (sandwich) SEs.
- Predictors: primary metric and §1.6 secondary features, z-standardised over entities.
- Reported: OR per 1 SD with 95% CI, Wald p, and BH within smell.
- VIF is computed on the entity-level design. If any VIF > 5, a **reduced model** is also fitted, dropping the non-primary feature with the highest VIF repeatedly until all VIFs ≤ 5. The primary metric is never dropped.
- Depth-3 `DecisionTreeClassifier(class_weight='balanced', random_state=SEED)` on unanimous entities, with rules from `export_text`.
- Robustness: R3–R6 on the primary-metric OR.

**RQ5:**
- Unanimous vs split entities, primary set, on every feature: two-sided Mann–Whitney U and Cliff's delta (bootstrap CI, B = 2000).
- The BH family is all CM and LPL tests. MA is reported with raw p only, labelled descriptive.
- Robustness: R3–R6 on the primary-metric delta and on the number of BH-significant features.

**R1** (MA: alpha, AUC, Youden) and **R2** (CM, LPL: AUC, Youden, RQ4 paired MCC difference).

### 4.4 Step 3: shared protocol

- **Data:** primary set, unanimous entities with complete features (CM 1,695; LPL 1,325).
- **Full feature set:** primary metric, loc, statements, max_nesting, method_calls, comment_ratio and **mean_identifier_length**. The last is the mean length of identifier tokens that are not keywords, computed by the same lexer and added to `src/features.py`.
- **Feature groups:**
  - primary = {cc | pc}
  - size = {loc, statements}
  - structure = {max_nesting, method_calls}
  - readability = {comment_ratio, mean_identifier_length}
- **Outer CV:** grouped 5-fold by project, **repeated 5 times**. In repeat r (r = 0..4, seed 20261021 + r), the projects are shuffled and assigned round-robin to 5 folds (2 projects per fold). The same 25 splits are used by every model, baseline and variant in A–J.
- **Inner tuning (nested):** `GridSearchCV` with `GroupKFold(3)` by project on the training fold, scoring MCC; ties broken by the first grid entry.
- **Fixed grids:**
  - LR: `StandardScaler` + `LogisticRegression(class_weight='balanced', max_iter=10000)`, C ∈ {0.01, 0.1, 1, 10}.
  - RF: `RandomForestClassifier(n_estimators=300, class_weight='balanced')`, max_depth ∈ {None, 5, 10}, min_samples_leaf ∈ {1, 5, 20}.
  - XGB: `XGBClassifier(scale_pos_weight=n_neg/n_pos of the training fold, n_jobs=1)`, n_estimators ∈ {100, 300}, max_depth ∈ {2, 4, 6}, learning_rate ∈ {0.05, 0.1}.
  - GB: `GradientBoostingClassifier` with balanced sample weights, n_estimators ∈ {100, 300}, max_depth ∈ {2, 3}, learning_rate ∈ {0.05, 0.1}.
  - SVM: `StandardScaler` + `SVC(kernel='rbf', class_weight='balanced')`, C ∈ {0.1, 1, 10}, gamma ∈ {'scale', 0.01, 0.1}. Scores come from `decision_function` for AUCs; predicted class is the sign.
  - All models use `random_state = SEED + r`.
- **Imbalance:** inverse-frequency class weights only. No SMOTE or other synthetic oversampling, because it fabricates borderline neighbours, which is exactly the region under study.
- **Metrics:**
  - macro-F1 and MCC at the predicted class (probability ≥ 0.5, or decision ≥ 0);
  - ROC-AUC and PR-AUC (average precision, positive = smelly) on scores.
  - Each metric is computed on pooled out-of-fold predictions per repeat and reported as mean ± SD over the 5 repeats.
  - Its 95% CI is a bootstrap over entities (B = 2000) of the repeat-mean.
  - Paired differences use the same resamples.
- **Best model** per smell: the highest mean MCC over repeats among the five algorithms. The **best tree model** (for SHAP) is the highest among RF, XGB and GB.

### 4.5 Step 3 sections

**A. Baselines**, on the same 25 splits:
- majority class of the training fold (constant score);
- primary metric ≥ DesigniteJava default (score = metric);
- primary metric ≥ Youden cut-off fitted on the training fold only.

**B. Model comparison:**
- Five algorithms with the grids above; metrics as in 4.4.
- Statistical comparison: **Friedman test over the 25 outer folds** on fold-level MCC.
- Then **Nemenyi** post-hoc with a critical difference CD = q₀.₀₅ √(k(k+1)/(6N)), with q₀.₀₅ = 2.728 for k = 5, plus a CD diagram.
- Fold-level MCC on a single-class fold is defined as 0 by scikit-learn.

**C. Ablation** (best model and LR; hyperparameters **reused** from the full model's inner tuning in each outer fold, not re-tuned):
- C1: (i) primary only; (ii) size; (iii) structure; (iv) readability; (v) all; (vi) all minus each of the 4 groups.
- C2: training labels are unanimous only / ties as smelly / soft labels.
  - Soft labels: each entity enters twice, once per class, with weights y/n and 1 − y/n times the class weight.
  - The test set is always the held-out unanimous entities.
- C3: training source is DACOSX only / DACOS only / DACOSX + DACOS training folds / DACOSX only without the primary metric.
  - DACOSX is the D4-cleaned set; the test set is always the held-out DACOS fold.
  - Class weights are recomputed on each training set.
- C4: class weights on vs off.
- Reported: Δ macro-F1 and Δ MCC versus (v), with paired bootstrap CIs.

**D. Generalisation:**
- Leave-one-project-out with the best model and LR (nested tuning, inner `GroupKFold(3)`).
- Per-project macro-F1 and MCC: median, IQR and worst project. Projects with < 20 entities or a single class are listed; metrics are computed where defined and excluded from the distribution otherwise.
- Per-project scores are also computed from the Tier 1 LOPO predictions (LR, RF).
- Cross-smell transfer: CM → LPL and LPL → CM, using method-level features only (cc, pc and the secondary features). The source smell's best model is tuned by grouped CV on the source data. Entities present in both smells (the 195 `1,2` snippets) are removed from the target test set.

**E. Leakage and validity:**
- Duplicates:
  - Exact: comments stripped, whitespace collapsed.
  - Near: additionally, identifiers become `ID` and literals become `LIT`.
  - Count duplicate groups and how many cross train/test in the 25 splits.
  - Deduplicate by keeping the lowest entity id per near-duplicate group, then rerun the B headline (best model and LR).
- Assert that no entity, file or project is in both train and test in any split.
- KS statistic DACOS (unanimous) versus DACOSX (D4-cleaned training set) for every feature, plus a statement of how each feature is computed for each source.

**F. Interpretability and calibration:**
- SHAP TreeExplainer on the best tree model. It is refitted on all unanimous entities with hyperparameters chosen by `GridSearchCV(GroupKFold(5))` on all data.
- Plots: mean |SHAP| bar and beeswarm, plus a dependence plot of the primary metric with the DesigniteJava default and the RQ2 Youden cut-off marked.
- Permutation importance (MCC, 10 repeats) on the held-out folds of repeat 0, averaged over folds. Spearman ρ between its ranking and the mean |SHAP| ranking.
- Calibration on pooled out-of-fold probabilities of repeat 0 for the best model and LR: Brier score and a 10-bin reliability diagram. If the best model is the SVM, its probabilities come from `SVC(probability=True)`, refitted for calibration only.

**G. Feature selection** (repeat-0 folds; reported only, never used to choose the final model):
1. Mutual-information filter: keep features with `mutual_info_classif` > 0 (random_state = SEED).
2. Pearson |r| > 0.85 pruning: drop the member with lower MI.
3. `RFECV` with LR (scoring MCC, `GroupKFold(3)`).
- Reported: surviving features per fold, Jaccard stability, and best-model performance on the selected subset versus all features.
- If selection lowers mean MCC or the mean pairwise Jaccard is < 0.7, the full set is kept, and this is stated.

**H. Learning curve:**
- Best model with fold hyperparameters, on repeat-0 folds.
- Training fractions 10/25/50/75/100%, stratified subsampling, 5 seeds (SEED + s).
- Plateau rule (fixed): plateaued if the macro-F1 gain from 75% to 100% is < 0.01 and its bootstrap CI includes 0.

**I. Error analysis:**
- Uses the best model's repeat-0 out-of-fold predictions. Models are trained on unanimous entities, and every entity with a majority label in the held-out projects (unanimous or non-unanimous majority) is predicted. Ties are reported separately as a predicted-smelly share.
- 15 FP and 15 FN are sampled per smell (seed SEED) and saved with code, features, vote split, run membership and score to `results/error_analysis/`.
- Error rate on split vs unanimous entities, and in-run vs not-in-run, against the base rates. An entity is "in run" if any of its annotations lies in a run.

**J. Sensitivity:**
- The B protocol for the best model, with training labels taken from R4 and from R6.
- Paired comparison: the variant-trained model and the primary model are evaluated on the same primary unanimous test entities. Reported as Δ macro-F1 and Δ MCC with paired bootstrap CIs.
- Also reported, unpaired: each variant evaluated on its own labels.

**Priority if time runs short:** Step 1 → Step 2 → A, B, C, E → D, F, H → G, I, J. Unfinished sections are listed in results.md.
