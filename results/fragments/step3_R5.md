**Analysis type: robustness (R5 applied to Step 3).** LPL only. plan.md §5.1.

**Method.**
- The 137 pc = 3 entities with an empty `smells` field are removed from training and test. This leaves 1189 unanimous entities (731 smelly).
- Everything else is identical to the primary Step 3 run: the same code, grids, nested tuning and seeds. The 25 splits have the same project-to-fold assignment (asserted).
- In each table the primary column repeats the primary result; the R5 column is new.

**A and B: baselines and five-model comparison** (mean ± SD not shown; cells are repeat-mean [95% CI])

| section | model/baseline | metric | primary | R5 |
|---|---|---|---|---|
| A baselines | majority class | macro_F1 | 0.396 [0.386, 0.405] | 0.381 [0.370, 0.391] |
| A baselines | majority class | MCC | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| A baselines | majority class | ROC_AUC | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| A baselines | majority class | PR_AUC | 0.654 [0.629, 0.680] | 0.615 [0.587, 0.642] |
| A baselines | DesigniteJava default rule | macro_F1 | 0.393 [0.367, 0.420] | 0.437 [0.410, 0.465] |
| A baselines | DesigniteJava default rule | MCC | -0.013 [-0.070, 0.044] | 0.031 [-0.024, 0.085] |
| A baselines | DesigniteJava default rule | ROC_AUC | 0.434 [0.409, 0.459] | 0.514 [0.490, 0.538] |
| A baselines | DesigniteJava default rule | PR_AUC | 0.628 [0.599, 0.658] | 0.623 [0.594, 0.653] |
| A baselines | Youden rule (fitted in training fold) | macro_F1 | 0.285 [0.268, 0.301] | 0.388 [0.364, 0.413] |
| A baselines | Youden rule (fitted in training fold) | MCC | -0.053 [-0.098, -0.008] | -0.019 [-0.073, 0.033] |
| A baselines | Youden rule (fitted in training fold) | ROC_AUC | 0.434 [0.409, 0.459] | 0.514 [0.490, 0.538] |
| A baselines | Youden rule (fitted in training fold) | PR_AUC | 0.628 [0.599, 0.658] | 0.623 [0.594, 0.653] |
| B models | LR | macro_F1 | 0.569 [0.542, 0.596] | 0.609 [0.583, 0.635] |
| B models | LR | MCC | 0.141 [0.088, 0.194] | 0.219 [0.167, 0.272] |
| B models | LR | ROC_AUC | 0.590 [0.557, 0.622] | 0.639 [0.606, 0.671] |
| B models | LR | PR_AUC | 0.710 [0.675, 0.746] | 0.699 [0.663, 0.738] |
| B models | RF | macro_F1 | 0.614 [0.590, 0.638] | 0.616 [0.589, 0.640] |
| B models | RF | MCC | 0.230 [0.182, 0.277] | 0.246 [0.194, 0.294] |
| B models | RF | ROC_AUC | 0.649 [0.619, 0.679] | 0.622 [0.589, 0.654] |
| B models | RF | PR_AUC | 0.763 [0.734, 0.794] | 0.673 [0.637, 0.711] |
| B models | XGB | macro_F1 | 0.607 [0.583, 0.630] | 0.606 [0.580, 0.632] |
| B models | XGB | MCC | 0.216 [0.169, 0.263] | 0.222 [0.170, 0.272] |
| B models | XGB | ROC_AUC | 0.675 [0.645, 0.704] | 0.628 [0.596, 0.659] |
| B models | XGB | PR_AUC | 0.796 [0.770, 0.822] | 0.683 [0.646, 0.721] |
| B models | GB | macro_F1 | 0.616 [0.591, 0.638] | 0.603 [0.577, 0.629] |
| B models | GB | MCC | 0.232 [0.184, 0.278] | 0.219 [0.169, 0.268] |
| B models | GB | ROC_AUC | 0.675 [0.646, 0.704] | 0.620 [0.587, 0.652] |
| B models | GB | PR_AUC | 0.796 [0.770, 0.822] | 0.680 [0.644, 0.719] |
| B models | SVM | macro_F1 | 0.612 [0.588, 0.637] | 0.619 [0.589, 0.645] |
| B models | SVM | MCC | 0.229 [0.182, 0.278] | 0.269 [0.213, 0.321] |
| B models | SVM | ROC_AUC | 0.631 [0.600, 0.662] | 0.642 [0.610, 0.672] |
| B models | SVM | PR_AUC | 0.727 [0.693, 0.761] | 0.704 [0.668, 0.742] |

**B: Friedman/Nemenyi and best model**

| statistic | primary | R5 |
|---|---|---|
| Friedman χ² | 12.882 | 20.453 |
| Friedman p | 0.0119 | 4.06e-04 |
| Nemenyi CD | 1.220 | 1.220 |
| mean rank LR | 3.92 | 3.40 |
| mean rank RF | 2.50 | 3.00 |
| mean rank XGB | 3.14 | 3.68 |
| mean rank GB | 2.80 | 3.10 |
| mean rank SVM | 2.64 | 1.82 |
| best model (MCC rule) | GB | SVM |
| best tree model | GB | RF |

Pairs with |Δ rank| > CD: primary LR vs RF, LR vs SVM; R5 LR vs SVM, XGB vs SVM, GB vs SVM.
Figure: `figures/model_cd_diagram_LPL_R5.pdf`.

**C1 and C3** (hyperparameters reused from the respective B run; Δ is versus (v) with a paired bootstrap CI)

| model | variant | primary | R5 |
|---|---|---|---|
| GB | (i) primary only | MCC 0.206; Δ MCC -0.027 [-0.082, 0.029] | n/a (not the best model of this run) |
| GB | (v) all features | reference | n/a (not the best model of this run) |
| GB | DACOS only (= v) | reference | n/a (not the best model of this run) |
| GB | DACOSX only | MCC -0.013; Δ MCC -0.245 [-0.325, -0.169] | n/a (not the best model of this run) |
| GB | DACOSX + DACOS | MCC -0.021; Δ MCC -0.253 [-0.300, -0.197] | n/a (not the best model of this run) |
| GB | DACOSX only, primary metric removed | MCC -0.163; Δ MCC -0.396 [-0.479, -0.314] | n/a (not the best model of this run) |
| LR | (i) primary only | MCC -0.055; Δ MCC -0.196 [-0.251, -0.142] | MCC -0.024; Δ MCC -0.243 [-0.316, -0.173] |
| LR | (v) all features | reference | reference |
| LR | DACOS only (= v) | reference | reference |
| LR | DACOSX only | MCC -0.056; Δ MCC -0.196 [-0.290, -0.104] | MCC 0.002; Δ MCC -0.217 [-0.299, -0.135] |
| LR | DACOSX + DACOS | MCC -0.088; Δ MCC -0.229 [-0.282, -0.175] | MCC 0.000; Δ MCC -0.219 [-0.272, -0.167] |
| LR | DACOSX only, primary metric removed | MCC -0.195; Δ MCC -0.336 [-0.430, -0.248] | MCC -0.182; Δ MCC -0.401 [-0.493, -0.309] |
| SVM | (i) primary only | n/a (not the best model of this run) | MCC -0.009; Δ MCC -0.278 [-0.339, -0.214] |
| SVM | (v) all features | n/a (not the best model of this run) | reference |
| SVM | DACOS only (= v) | n/a (not the best model of this run) | reference |
| SVM | DACOSX only | n/a (not the best model of this run) | MCC 0.046; Δ MCC -0.223 [-0.296, -0.150] |
| SVM | DACOSX + DACOS | n/a (not the best model of this run) | MCC 0.004; Δ MCC -0.265 [-0.318, -0.208] |
| SVM | DACOSX only, primary metric removed | n/a (not the best model of this run) | MCC -0.106; Δ MCC -0.375 [-0.452, -0.293] |

**RQ3 GEE** (annotation level, all features; R5: 3118 annotations, 1557 entities, working correlation 0.495). No R5 VIF exceeds 5.

| feature | primary OR per SD [95% CI] | primary p (BH) | R5 OR per SD [95% CI] | R5 p (BH) | R5 VIF |
|---|---|---|---|---|---|
| pc | 0.794 [0.742, 0.849] | 6.54e-11 | 0.969 [0.907, 1.035] | 0.4154 | 1.03 |
| loc | 1.249 [1.041, 1.497] | 0.0329 | 1.415 [1.143, 1.752] | 0.0044 | 4.76 |
| statements | 0.938 [0.783, 1.124] | 0.5851 | 0.899 [0.742, 1.089] | 0.4153 | 4.87 |
| max_nesting | 0.637 [0.560, 0.724] | 3.74e-11 | 0.597 [0.519, 0.688] | 4.02e-12 | 1.99 |
| comment_ratio | 1.076 [0.975, 1.188] | 0.2179 | 1.101 [0.997, 1.217] | 0.1172 | 1.16 |
| method_calls | 0.997 [0.845, 1.176] | 0.9675 | 0.983 [0.825, 1.170] | 0.8438 | 3.34 |

```
=== LPL R5: depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1189 unanimous entities (731 smelly / 458 benign).
|--- max_nesting <= 1.500
|   |--- statements <= 12.500
|   |   |--- pc <= 4.500
|   |   |   |--- weights: [273.885, 372.477] class: 1
|   |   |--- pc >  4.500
|   |   |   |--- weights: [55.816, 110.605] class: 1
|   |--- statements >  12.500
|   |   |--- method_calls <= 15.500
|   |   |   |--- weights: [29.855, 13.826] class: 0
|   |   |--- method_calls >  15.500
|   |   |   |--- weights: [20.769, 29.278] class: 1
|--- max_nesting >  1.500
|   |--- loc <= 58.500
|   |   |--- loc <= 20.500
|   |   |   |--- weights: [75.286, 32.531] class: 0
|   |   |--- loc >  20.500
|   |   |   |--- weights: [132.400, 19.518] class: 0
|   |--- loc >  58.500
|   |   |--- method_calls <= 32.500
|   |   |   |--- weights: [0.000, 6.506] class: 1
|   |   |--- method_calls >  32.500
|   |   |   |--- weights: [6.490, 9.759] class: 1

```

**D: LOPO per-project distribution** (best model of each run: primary GB, R5 SVM)

| statistic | primary | R5 |
|---|---|---|
| pooled_macro_F1 | 0.634 | 0.620 |
| pooled_MCC | 0.268 | 0.282 |
| MCC_median | 0.165 | 0.123 |
| MCC_q1 | 0.119 | 0.003 |
| MCC_q3 | 0.330 | 0.370 |
| MCC_worst | shuzheng_zheng (0.016) | linlinjava_litemall (-0.081) |
| macro_F1_median | 0.562 | 0.493 |
| projects_in_distribution | 9 | 8 |
| projects_flagged | macrozheng_mall [< 20 entities] | Blankj_AndroidUtilCode [single class]; macrozheng_mall [< 20 entities] |

**F: SHAP** (best tree model of each run). Figures: `figures/shap_summary_LPL_R5.pdf`, `figures/shap_dependence_LPL_R5.pdf`.

| feature | primary mean |SHAP| (GB) | primary rank | R5 mean |SHAP| (RF) | R5 rank |
|---|---|---|---|---|
| pc | 0.6944 | 1 | 0.0107 | 6 |
| loc | 0.1806 | 4 | 0.0254 | 3 |
| statements | 0.1765 | 5 | 0.0395 | 2 |
| max_nesting | 0.3488 | 2 | 0.0536 | 1 |
| method_calls | 0.0965 | 7 | 0.0072 | 7 |
| comment_ratio | 0.1738 | 6 | 0.0206 | 5 |
| mean_identifier_length | 0.3408 | 3 | 0.0241 | 4 |

**H: learning curve** (best model of each run)

| fraction | primary macro-F1 (±SD) | R5 macro-F1 (±SD) |
|---|---|---|
| 0.1 | 0.556 ± 0.011 | 0.492 ± 0.013 |
| 0.25 | 0.604 ± 0.010 | 0.522 ± 0.020 |
| 0.5 | 0.611 ± 0.019 | 0.610 ± 0.005 |
| 0.75 | 0.608 ± 0.010 | 0.623 ± 0.003 |
| 1.0 | 0.612 ± 0.000 | 0.622 ± 0.000 |
| gain 75%→100% [95% CI]; plateaued | 0.005 [-0.007, 0.016]; True | -0.001 [-0.004, 0.003]; True |

**E: duplicate groups and label conflicts**

| duplicate type | primary | R5 |
|---|---|---|
| exact | 71 groups; 169 entities; 0 groups span >1 project; 22 groups have conflicting labels | 51 groups; 129 entities; 0 groups span >1 project; 22 groups have conflicting labels |
| near | 160 groups; 462 entities; 6 groups span >1 project; 62 groups have conflicting labels | 131 groups; 399 entities; 6 groups span >1 project; 62 groups have conflicting labels |

Tables: `tables/lpl_r5_*.csv` (side by side), `tables/model_comparison_LPL_R5.csv`, `tables/baselines_LPL_R5.csv`, `tables/ablation_LPL_R5.csv`, `tables/rq3_odds_ratios_LPL_R5.csv`, `tables/rq3_tree_rules_LPL_R5.txt`, `tables/lopo_per_project_LPL_R5.csv`. Runtime 494s.

**Summary.** R5 best model SVM, MCC 0.269 [0.213, 0.321]; primary best model GB, MCC 0.232 [0.184, 0.278].
