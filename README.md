# Metric Thresholds Versus Human Judgment on Borderline Code Smells: A Robustness-First Audit of the DACOS Benchmark

Replication package for a study of how human annotators judge three code smells in the borderline snippets of the
[DACOS dataset](https://doi.org/10.5281/zenodo.7570428), compared with metric thresholds and with models trained on threshold-derived labels:
- Complex Method (CM)
- Long Parameter List (LPL)
- Multifaceted Abstraction (MA)

The analysis is **pre-registered and robustness-first**:
- [`plan.md`](plan.md) fixed every analysis before it was run. Each amendment is a separate git commit, and the commit hashes are listed at the top of [`results/results.md`](results/results.md).
- Every planned result is reported, including nulls.
- Each number in `results.md` is tagged as **primary**, **robustness**, **validity check** or **exploratory**.
- The data-quality problems found in the published dataset are documented first (results.md §1): answer runs, self-contradicting annotations, duplicate rows, wrong-granularity DACOSX entries, and threshold bands that differ from the paper. Every headline number is then repeated under each sensible alternative reading of the data (§4).

## What is in the study

| Part | Content | results.md |
|---|---|---|
| Dataset audit | loading, counts versus the DACOS paper, duplicates, DACOSX granularity, threshold bands, checkbox vs `is_smell`, answer runs | §1–2 |
| RQ1 | annotator agreement (Krippendorff's alpha, vote splits) | §3 |
| RQ2 | does the primary metric separate smelly from benign borderline snippets; Youden cut-off vs DesigniteJava default | §3 |
| RQ3 | which features drive the yes/no answer (annotation-level GEE, decision tree) | §3 |
| RQ4 | do models trained on threshold-labelled extremes (DACOSX) transfer to human-labelled borderline snippets | §3 |
| RQ5 | which features distinguish unanimous from split snippets | §3 |
| Robustness R1–R7 | the headline numbers under each alternative data reading; answer-run anatomy; sensitivity; LPL without the pc = 3 block; specification curves | §4 |
| Step 3 A–I | baselines, five-model comparison (nested grouped CV), ablation, generalisation (LOPO, cross-smell), leakage checks, SHAP and calibration, feature selection, learning curve, error analysis | §5 |
| Human ceiling and agreement anatomy | model MCC on the same scale as human-human agreement; why same-snippet agreement exceeds agreement between structurally identical snippets (matched and exact-duplicate comparisons, annotation-id gap, tool design) | §6 |
| Range restriction | how narrow the annotated band is and where the tool rule decides | §7 |
| External check | C# code-smell dataset: audit (B0), adjudication rate, alpha bounds and metric AUCs (B1); external context, not a replication | §8 |
| Headline numbers | key numbers with CI, analysis type and source table; also in `results/paper_numbers.json` | §13 |

## How to run

```bash
bash run_all.sh
```

This single command:
1. Creates `.venv` from the pinned `requirements.txt` (Python 3.9+).
2. Downloads both datasets from Zenodo and verifies their MD5 checksums.
3. Converts the MySQL dumps to SQLite. No database server is needed.
4. Rebuilds every table (`results/tables/`), figure (`results/figures/`, PDF and PNG at 300 dpi), paper figure (`results/paper_figures/`), `results/results.md` and `results/paper_numbers.json`.

- **Expected runtime:** about 18–28 minutes (two from-scratch runs took 18.3 and 27.5 min wall-clock on the hardware below). The step-by-step runtime of the last run is in `results/logs/runtime.tsv` and results.md §11.
- **Hardware and OS used:** Apple M5 (10 cores), 16 GB RAM, macOS 26.6.2 (arm64), Python 3.9.6.
- **Determinism:** seeds are fixed (20261021), models are single-threaded per fold, and two full regenerations produce byte-identical tables.
- **OpenMP:** xgboost needs an OpenMP runtime. On macOS without one installed, `run_all.sh` points xgboost at the `libomp` bundled with scikit-learn (`DYLD_LIBRARY_PATH`). On Linux, the system `libgomp` is used.

## Data (not redistributed)

This repository **does not contain or redistribute any dataset**. `run_all.sh` downloads them into `data/` (git-ignored):

| Dataset | Source | Files (MD5-verified) |
|---|---|---|
| DACOS | Zenodo record [7570428](https://doi.org/10.5281/zenodo.7570428), CC BY 4.0 | `DACOSMain.sql`, `DACOSExtended.sql`, `files.zip`, `contributors.txt` |
| C# Data Class / Feature Envy / Refused Bequest | Zenodo record [10475432](https://doi.org/10.5281/zenodo.10475432), CC BY 4.0 | six `.xlsx` files |

Please cite the original datasets:
- H. Nandani, M. Saad, T. Sharma. *DACOS—A Manually Annotated Dataset of Code Smells.* MSR 2023 Data and Tool Showcase (arXiv:2303.08729). Dataset: doi:10.5281/zenodo.7570428.
- S. Prokić, N. Luburić, J. Slivka, K.-G. Grujić, A. Kovačević. *C# Dataset of Data Class, Feature Envy and Refused Bequest code smells* (v1.0, 2024). doi:10.5281/zenodo.10475432.

The data-quality observations in results.md §1 describe what this analysis found in the published files. They are reported as findings that affect the analysis, and they describe the files only.

## Mapping to the paper

| Paper item | File | Built from |
|---|---|---|
| Fig. 1 (single column): answer runs | `results/paper_figures/fig1_answer_runs.pdf` | `tables/audit_answer_runs.csv` and annotation data |
| Fig. 2 (double column): specification curves | `results/paper_figures/fig2_spec_curves.pdf` | `tables/spec_curves.csv` |
| Fig. 3 (single column): human ceiling with matched same- and cross-snippet agreement | `results/paper_figures/fig3_human_ceiling.pdf` | `tables/human_ceiling.csv`, `tables/agreement_matched_neardup.csv` |
| Fig. 4 (single column): ablation | `results/paper_figures/fig4_ablation.pdf` | `tables/ablation_CM.csv`, `tables/ablation_LPL_R5.csv` |
| Dataset audit tables | results.md §1 | `tables/audit_*.csv`, `tables/eligibility.csv` |
| RQ1 / RQ2 / RQ4 tables | results.md §3 | `tables/rq1_*.csv`, `tables/rq2_*.csv`, `tables/rq4_*.csv` |
| RQ3 / RQ5 tables | results.md §3 | `tables/rq3_*.csv`, `tables/rq3_tree_rules*.txt`, `tables/rq5_ambiguity.csv` |
| Robustness table | results.md §4.1 | `tables/robustness_summary.csv`, `tables/robustness_long.csv` |
| LPL primary vs R5 | results.md §4.4 | `tables/lpl_r5_*.csv` |
| Model comparison, ablation, generalisation, leakage, SHAP, calibration, learning curve | results.md §5 | `tables/model_*.csv`, `ablation_*.csv`, `lopo_*.csv`, `cross_smell.csv`, `leakage_*.csv`, `train_serve_skew.csv`, `shap_*.csv`, `calibration.csv`, `learning_curve*.csv`, `feature_selection*.csv`, `sensitivity.csv`, `results/error_analysis/` |
| Human ceiling | results.md §6.1 | `tables/human_ceiling*.csv` |
| Agreement anatomy | results.md §6.2 | `tables/agreement_*.csv` |
| Range restriction | results.md §7 | `tables/range_A*.csv` |
| External check (B0, B1) | results.md §8 | `tables/external_B0_*.csv`, `tables/external_B1_*.csv` |
| Every number quoted in the text | `results/paper_numbers.json` | value, CI, analysis type and source table for each headline number |

## Repository layout

```
plan.md                  pre-registered analysis plan and amendments (git history = registration record)
run_all.sh               single entry point
requirements.txt         pinned Python packages
src/convert_sql.py       mysqldump -> SQLite converter
src/audit.py             Phase 0 schema/count audit
src/features.py          secondary features from snippet source (lexer-based)
src/common.py            loading, labels, robustness variants, statistics helpers, plot style
src/dataset_audit.py     results §1-2
src/rq1.py ... rq5.py    research questions
src/robustness.py        R1-R7c headline numbers; src/run_anatomy.py (R7)
src/protocol.py          Step 3 shared CV protocol; src/step3_*.py sections A-J and the R5 rerun
src/human_ceiling.py     human ceiling; src/extras.py spec curves and exploratory reweighting
src/range_restriction.py range-restriction analyses; src/agreement_anatomy.py agreement anatomy
src/external_audit.py    external dataset audit (B0); src/external_b1.py external check (B1)
src/build_report.py      assembles results/results.md and results/paper_numbers.json
src/paper_figures.py     IEEE-sized paper figures
results/                 tables, figures, paper_figures, error_analysis, logs, results.md, paper_numbers.json
```

## Deviations from the pre-registered plan

The full list, with limitations, is in results.md §10. In short:
1. MySQL was unavailable, so the dumps are converted to SQLite by a purpose-written parser.
2. CK was not needed: the primary metrics (cc, pc, LCOM) and NOM/NOF are stored DesigniteJava values.
3. Per-annotator analyses are impossible because the data have no annotator ids.
4. MA is descriptive only: after the consistency filter it has 8 unanimous benign entities, below the pre-registered minimum of 30.
5. DACOSX in-distribution scores are reported as exploratory.
6. R1 and R2 appear as extra columns of the robustness table. RQ4 robustness changes only the DACOS test labels.
7. Leave-one-project-out (pooled out-of-fold predictions) is the generalisation analysis.
8. In the C3 ablation, DACOSX entries from the held-out projects are excluded from training.
9. Ablation variants reuse the full model's tuned hyperparameters.
10. CM's best model is LR, so "best model and LR" is one model for CM.
11. The SHAP beeswarm is drawn as a jittered strip plot in the paper style.
12. xgboost uses scikit-learn's bundled `libomp`.
13. R3 (`is_smell` as answer) applies no consistency filter.
14. In robustness runs, the RQ5 BH family is that variant's CM and LPL tests.
15. The R5 ablation uses the R5 best model (SVM) and LR.
16. For forests, the 3-D SHAP output is reduced to the "smelly" slice.
17. Human-ceiling designations are simulated exactly through sufficient statistics.
18. Near-duplicate-ceiling designations are drawn as multinomial counts per pair type.
19. Feature extraction covers every sample path; earlier values are unchanged.
20. Paper figures are re-drawn from committed tables.
21. `openpyxl` is pinned for the external dataset.
22. Entities whose snippet file is missing are excluded from the duplicate-group comparisons only, and a quasi-separated logistic fit is reported as not estimable.
23. The external dataset's sampling filters and its discussion-based adjudication come from the dataset author's dissertation.
24. Both ambiguous Refused Bequest columns are reported, and neither is chosen as BUR.

## Citation and licence

- Code: MIT licence (`LICENSE`). The datasets keep their own CC BY 4.0 licences and are not included.
- How to cite this repository: `CITATION.cff`.
