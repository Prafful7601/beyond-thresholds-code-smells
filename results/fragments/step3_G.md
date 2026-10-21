**Analysis type: primary, report-only (pre-registered in plan.md §4.5 G; never used to choose the final model).**

**Method.**
- Repeat-0 folds of section B; selection uses the training fold only.
1. Mutual-information filter: keep features with `mutual_info_classif` > 0 (random_state 20261021).
2. Pearson |r| > 0.85 pruning: drop the feature with lower MI.
3. `RFECV` with standardised class-weighted LR (`GroupKFold(3)` by project, scoring MCC).
- The best model, with fold parameters, is then trained on the selected subset. Performance on pooled repeat-0 out-of-fold predictions is compared with the full feature set using a paired bootstrap.
- Pre-registered decision: keep the full feature set if selection lowers MCC or the mean pairwise Jaccard across folds is < 0.7.

**Selected features per fold**

| smell | model | fold | after_MI_filter | after_correlation_pruning | after_RFECV | n_selected |
|---|---|---|---|---|---|---|
| CM | LR | 0 | statements, max_nesting, method_calls | statements, max_nesting, method_calls | method_calls | 1 |
| CM | LR | 1 | loc, statements, max_nesting | loc, statements, max_nesting | statements | 1 |
| CM | LR | 2 | statements, mean_identifier_length | statements, mean_identifier_length | statements, mean_identifier_length | 2 |
| CM | LR | 3 | cc, loc, statements, max_nesting, comment_ratio | cc, loc, statements, max_nesting, comment_ratio | cc, loc, statements, max_nesting, comment_ratio | 5 |
| CM | LR | 4 | loc, max_nesting, method_calls, comment_ratio | loc, max_nesting, method_calls, comment_ratio | method_calls | 1 |
| LPL | GB | 0 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 1 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 2 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, max_nesting | 2 |
| LPL | GB | 3 | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | pc, loc, max_nesting, comment_ratio | 4 |
| LPL | GB | 4 | loc, statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | statements, max_nesting, method_calls, comment_ratio, mean_identifier_length | max_nesting, mean_identifier_length | 2 |

**Selected versus all features**

| smell | model | selected_macro_F1 | all_macro_F1 | selected_MCC | all_MCC | Δ macro-F1 [95% CI] | Δ MCC [95% CI] | mean_pairwise_jaccard | decision |
|---|---|---|---|---|---|---|---|---|---|
| CM | LR | 0.53 | 0.521 | 0.135 | 0.1 | 0.008 [-0.012, 0.028] | 0.035 [-0.006, 0.077] | 0.187 | keep full feature set |
| LPL | GB | 0.606 | 0.612 | 0.226 | 0.225 | -0.006 [-0.032, 0.019] | 0.001 [-0.050, 0.052] | 0.57 | keep full feature set |

Tables: `tables/feature_selection.csv` (including per-fold MI values), `tables/feature_selection_performance.csv`.
