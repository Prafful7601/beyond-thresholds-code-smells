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
