# Beyond thresholds: human judgment of code smells in DACOS

This repository holds the analysis code and results for a study of how human annotators judge three code smells in the [DACOS dataset](https://doi.org/10.5281/zenodo.7570428), compared with metric thresholds:
- Complex Method
- Long Parameter List
- Multifaceted Abstraction

The analysis is pre-registered. [`plan.md`](plan.md) was committed before any outcome analysis was run, and every amendment is a separate commit. [`results/results.md`](results/results.md) reports every planned analysis, including null results, and keeps anything unplanned in a separate Exploratory section.

## Research questions

| RQ | Question | Status |
|---|---|---|
| RQ1 | How much do annotators agree? (Krippendorff's alpha, vote splits) | done |
| RQ2 | Does the primary metric separate smelly from benign snippets in the borderline band? Where is the optimal cut-off relative to the DesigniteJava default? | done |
| RQ4 | Do models trained on the metric-labelled extremes (DACOSX) transfer to the human-labelled borderline snippets (DACOS)? | done |
| RQ3 | Which code features drive human judgment? | Tier 2, pending |
| RQ5 | Which features distinguish unanimous snippets from split ones? | Tier 2, pending |
| R1–R6 | Robustness checks | Tier 2, pending |

## Reproducing

Requirements: Python 3.9+ and `curl`. No database server is needed; the MySQL dumps are converted to SQLite.

```bash
bash run_all.sh
```

The script does the following:
1. Creates `.venv` from the pinned `requirements.txt`.
2. Downloads the DACOS files from Zenodo and verifies their MD5 checksums.
3. Converts the dumps.
4. Regenerates every table in `results/tables/`, every figure in `results/figures/` (PDF and PNG, 300 dpi), and `results/results.md`.

A full run takes about a minute. Seeds are fixed, and two consecutive runs produce byte-identical tables.

## Layout

```
plan.md                  pre-registered analysis plan (+ amendments)
run_all.sh               single entry point
src/convert_sql.py       mysqldump -> SQLite converter
src/audit.py             Phase 0 schema/count audit -> results/logs/audit.txt
src/features.py          secondary features from snippet source (lexer-based)
src/dataset_audit.py     results §1–2: data-quality findings, descriptives, eligibility
src/rq1.py, rq2.py, rq4.py
src/build_report.py      assembles results/results.md
results/                 tables, figures, logs, results.md
```

The raw data (`data/raw`), the SQLite databases (`data/db`) and the feature cache (`data/features`) are not committed. `run_all.sh` recreates them.

## Data and attribution

DACOS was created by Himesh Nandani, Mootez Saad and Tushar Sharma, and is published on Zenodo (doi:10.5281/zenodo.7570428) under CC BY 4.0. The companion paper is "DACOS—A Manually Annotated Dataset of Code Smells" (MSR 2023, arXiv:2303.08729).

The data-quality observations in `results/results.md` §1 describe what this analysis found in the published files. They are reported as findings that affect the analysis, and they describe the files only.
