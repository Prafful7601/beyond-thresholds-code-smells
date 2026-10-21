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
