# Beyond thresholds: human judgment of code smells in DACOS

This repository holds the analysis code and results for a study of how human annotators judge three code smells in the [DACOS dataset](https://doi.org/10.5281/zenodo.7570428), compared with metric thresholds:
- Complex Method
- Long Parameter List
- Multifaceted Abstraction

The analysis is pre-registered. [`plan.md`](plan.md) was committed before any outcome analysis was run, and every amendment is a separate commit. [`results/results.md`](results/results.md) reports every planned analysis, including null results, and keeps anything unplanned in a separate Exploratory section.

## Research questions

| RQ / section | Question | Status |
|---|---|---|
| RQ1 | How much do annotators agree? (Krippendorff's alpha, vote splits) | done |
| RQ2 | Does the primary metric separate smelly from benign snippets in the borderline band? Where is the optimal cut-off relative to the DesigniteJava default? | done |
| RQ3 | Which code features drive human judgment? (GEE, decision tree) | done |
| RQ4 | Do models trained on the metric-labelled extremes (DACOSX) transfer to the human-labelled borderline snippets (DACOS)? | done |
| RQ5 | Which features distinguish unanimous snippets from split ones? | done |
| R1–R7 | Robustness checks, including the anatomy of answer runs | done |
| Step 3 A–J | Baselines, five-model comparison, ablation, generalisation, leakage checks, SHAP and calibration, feature selection, learning curve, error analysis, sensitivity | done |

## Reproducing

Requirements: Python 3.9+ and `curl`. No database server is needed; the MySQL dumps are converted to SQLite. On macOS without a system OpenMP runtime, `run_all.sh` points xgboost at the `libomp` bundled with scikit-learn.

```bash
bash run_all.sh
```

The script does the following:
1. Creates `.venv` from the pinned `requirements.txt`.
2. Downloads the DACOS files from Zenodo and verifies their MD5 checksums.
3. Converts the dumps.
4. Regenerates every table in `results/tables/`, every figure in `results/figures/` (PDF and PNG, 300 dpi), and `results/results.md`.

A full run takes about 10 minutes on a 10-core laptop. Seeds are fixed, and two consecutive runs produce byte-identical tables.

## Layout

```
plan.md                  pre-registered analysis plan (+ amendments)
run_all.sh               single entry point
src/convert_sql.py       mysqldump -> SQLite converter
src/audit.py             Phase 0 schema/count audit -> results/logs/audit.txt
src/features.py          secondary features from snippet source (lexer-based)
src/dataset_audit.py     results §1–2: data-quality findings, descriptives, eligibility
src/rq1.py … rq5.py      research questions
src/robustness.py        R1-R7c headline numbers; src/run_anatomy.py (R7)
src/protocol.py          Step 3 shared CV protocol; src/step3_*.py sections A-J
src/build_report.py      assembles results/results.md
results/                 tables, figures, logs, results.md
```

The raw data (`data/raw`), the SQLite databases (`data/db`) and the feature cache (`data/features`) are not committed. `run_all.sh` recreates them.

## Data and attribution

DACOS was created by Himesh Nandani, Mootez Saad and Tushar Sharma, and is published on Zenodo (doi:10.5281/zenodo.7570428) under CC BY 4.0. The companion paper is "DACOS—A Manually Annotated Dataset of Code Smells" (MSR 2023, arXiv:2303.08729).

The data-quality observations in `results/results.md` §1 describe what this analysis found in the published files. They are reported as findings that affect the analysis, and they describe the files only.
