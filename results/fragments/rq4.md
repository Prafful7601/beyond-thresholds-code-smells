**Method.**
- Eligible smells under D8: Complex Method, Long Parameter List.
- **Multifaceted Abstraction is skipped** because it fails D8 (see section 1.9).
- **Features**: the primary metric plus the secondary features of plan §1.6. These are stored DesigniteJava loc, plus computed statements, max nesting, comment ratio and method calls.
- **Models**:
  - `StandardScaler` + `LogisticRegression(class_weight='balanced', max_iter=10000)`.
  - `RandomForestClassifier(class_weight='balanced', random_state=20261021)`.
  - All other hyperparameters are scikit-learn 1.5.2 defaults.
- **Transfer setting.**
  - Train on granularity-consistent DACOSX entries for the smell, using the full absent class with inverse-frequency weights and no subsampling (D14).
  - Same-smell DACOS overlaps are removed before training (D4).
  - Test on DACOS unanimous entities from the consistency-filtered set.
- **In-DACOS settings.** `GroupKFold(5)` and leave-one-project-out, grouped by `project_name`. Out-of-fold predictions are pooled before scoring.
- **Scoring.** Predicted class is p ≥ 0.5, and "smelly" is the positive class. ROC-AUC uses the pooled probabilities.
- **CIs.** Bootstrap percentile intervals (B = 2000, resampling DACOS test entities, seed 20261021). The same resamples are used for every setting, so differences are paired.
- **H4.** Primary test: transfer MCC − GroupKFold(5) MCC, judged by its paired bootstrap CI. The other differences are reported alongside it.
- **Caveat.** DACOSX labels are functions of the same metrics used as features, so near-perfect DACOSX in-distribution scores are expected and are not a finding. They are listed under EXPLORATORY only as a sanity check.

**Data**

| smell | features | DACOS_unanimous | DACOS_missing_features | DACOS_test_n | DACOS_smelly | DACOS_benign | DACOSX_consistent | DACOSX_overlap_removed | DACOSX_missing_features | DACOSX_train_n | DACOSX_present | DACOSX_absent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | cc, loc, statements, max_nesting, comment_ratio, method_calls | 1695 | 0 | 1695 | 1129 | 566 | 83609 | 50 | 10 | 83549 | 378 | 83171 |
| LPL | pc, loc, statements, max_nesting, comment_ratio, method_calls | 1326 | 1 | 1325 | 867 | 458 | 83159 | 41 | 8 | 83110 | 131 | 82979 |

**Performance on DACOS unanimous entities**

| smell | model | setting | n_test | F1 [95% CI] | MCC [95% CI] | ROC_AUC [95% CI] | predicted smelly share |
|---|---|---|---|---|---|---|---|
| CM | LR | transfer: DACOSX → DACOS | 1695 | 0.598 [0.573, 0.624] | 0.067 [0.021, 0.114] | 0.548 [0.519, 0.577] | 0.5 |
| CM | LR | DACOS GroupKFold(5) by project | 1695 | 0.578 [0.551, 0.604] | 0.092 [0.041, 0.137] | 0.554 [0.525, 0.582] | 0.453 |
| CM | LR | DACOS leave-one-project-out | 1695 | 0.566 [0.540, 0.592] | 0.089 [0.040, 0.136] | 0.552 [0.522, 0.580] | 0.438 |
| CM | RF | transfer: DACOSX → DACOS | 1695 | 0.390 [0.359, 0.421] | 0.044 [-0.003, 0.090] | 0.522 [0.495, 0.546] | 0.257 |
| CM | RF | DACOS GroupKFold(5) by project | 1695 | 0.745 [0.725, 0.764] | 0.018 [-0.029, 0.067] | 0.517 [0.487, 0.545] | 0.833 |
| CM | RF | DACOS leave-one-project-out | 1695 | 0.743 [0.723, 0.762] | 0.020 [-0.027, 0.067] | 0.505 [0.476, 0.533] | 0.827 |
| LPL | LR | transfer: DACOSX → DACOS | 1325 | 0.335 [0.300, 0.370] | -0.080 [-0.139, -0.023] | 0.385 [0.356, 0.417] | 0.26 |
| LPL | LR | DACOS GroupKFold(5) by project | 1325 | 0.683 [0.657, 0.708] | 0.144 [0.088, 0.198] | 0.601 [0.569, 0.634] | 0.608 |
| LPL | LR | DACOS leave-one-project-out | 1325 | 0.656 [0.629, 0.682] | 0.099 [0.044, 0.156] | 0.567 [0.532, 0.600] | 0.586 |
| LPL | RF | transfer: DACOSX → DACOS | 1325 | 0.309 [0.273, 0.345] | -0.013 [-0.070, 0.044] | 0.496 [0.470, 0.522] | 0.207 |
| LPL | RF | DACOS GroupKFold(5) by project | 1325 | 0.714 [0.690, 0.737] | 0.125 [0.069, 0.181] | 0.603 [0.570, 0.634] | 0.693 |
| LPL | RF | DACOS leave-one-project-out | 1325 | 0.715 [0.691, 0.739] | 0.127 [0.073, 0.182] | 0.605 [0.573, 0.635] | 0.696 |

**Paired differences (transfer minus in-DACOS CV)**

| smell | model | comparison | metric | difference [95% CI] | bootstrap share ≥ 0 | H4 primary test |
|---|---|---|---|---|---|---|
| CM | LR | transfer − DACOS GroupKFold(5) by project | MCC | -0.024 [-0.072, 0.024] | 0.1605 | yes |
| CM | LR | transfer − DACOS GroupKFold(5) by project | F1 | 0.020 [-0.004, 0.044] | 0.947 |  |
| CM | LR | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.006 [-0.032, 0.020] | 0.335 |  |
| CM | LR | transfer − DACOS leave-one-project-out | MCC | -0.021 [-0.069, 0.027] | 0.2 |  |
| CM | LR | transfer − DACOS leave-one-project-out | F1 | 0.032 [0.008, 0.056] | 0.9955 |  |
| CM | LR | transfer − DACOS leave-one-project-out | ROC_AUC | -0.004 [-0.029, 0.022] | 0.388 |  |
| CM | RF | transfer − DACOS GroupKFold(5) by project | MCC | 0.025 [-0.036, 0.089] | 0.7955 | yes |
| CM | RF | transfer − DACOS GroupKFold(5) by project | F1 | -0.355 [-0.388, -0.322] | 0.0 |  |
| CM | RF | transfer − DACOS GroupKFold(5) by project | ROC_AUC | 0.005 [-0.032, 0.041] | 0.6135 |  |
| CM | RF | transfer − DACOS leave-one-project-out | MCC | 0.023 [-0.036, 0.084] | 0.7765 |  |
| CM | RF | transfer − DACOS leave-one-project-out | F1 | -0.353 [-0.386, -0.321] | 0.0 |  |
| CM | RF | transfer − DACOS leave-one-project-out | ROC_AUC | 0.017 [-0.020, 0.053] | 0.8365 |  |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | MCC | -0.224 [-0.322, -0.127] | 0.0 | yes |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | F1 | -0.348 [-0.397, -0.297] | 0.0 |  |
| LPL | LR | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.216 [-0.273, -0.155] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | MCC | -0.179 [-0.280, -0.079] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | F1 | -0.320 [-0.374, -0.267] | 0.0 |  |
| LPL | LR | transfer − DACOS leave-one-project-out | ROC_AUC | -0.181 [-0.240, -0.121] | 0.0 |  |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | MCC | -0.138 [-0.217, -0.062] | 0.0 | yes |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | F1 | -0.405 [-0.446, -0.365] | 0.0 |  |
| LPL | RF | transfer − DACOS GroupKFold(5) by project | ROC_AUC | -0.107 [-0.145, -0.069] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | MCC | -0.139 [-0.215, -0.065] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | F1 | -0.407 [-0.447, -0.367] | 0.0 |  |
| LPL | RF | transfer − DACOS leave-one-project-out | ROC_AUC | -0.109 [-0.147, -0.071] | 0.0 |  |

Tables: `tables/rq4_data.csv`, `tables/rq4_transfer.csv`, `tables/rq4_paired_differences.csv`, `tables/rq4_predictions.csv.gz`. Figure: `figures/rq4_transfer.pdf` (.png). Runtime 22s.

**Summary.** CM LR: transfer MCC − GroupKFold MCC = -0.024 [-0.072, 0.024]; CM RF: transfer MCC − GroupKFold MCC = 0.025 [-0.036, 0.089]; LPL LR: transfer MCC − GroupKFold MCC = -0.224 [-0.322, -0.127]; LPL RF: transfer MCC − GroupKFold MCC = -0.138 [-0.217, -0.062].
