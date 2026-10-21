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
