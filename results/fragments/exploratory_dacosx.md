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
