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
