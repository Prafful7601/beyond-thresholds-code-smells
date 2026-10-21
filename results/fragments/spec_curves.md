**Analysis type: robustness summary (figures; no new tests).** plan.md §5.3.

Each panel plots one headline number per smell under every applicable condition (primary in orange, robustness checks in blue), sorted by estimate, with 95% CIs.
Reference lines: alpha 0.667, AUC 0.5, MCC difference 0, MCC 0. The B best-model MCC is shown for CM (primary) and LPL (primary and R5).

| spec | smell | condition | analysis | estimate [95% CI] | reference |
|---|---|---|---|---|---|
| alpha | CM | primary | primary | 0.804 [0.774, 0.832] | 0.667 |
| alpha | LPL | primary | primary | 0.540 [0.498, 0.577] | 0.667 |
| alpha | MA | primary | primary | 0.020 [-0.035, 0.077] | 0.667 |
| alpha | MA | R1 | robustness | -0.014 [-0.058, 0.031] | 0.667 |
| alpha | CM | R3 | robustness | 0.630 [0.597, 0.662] | 0.667 |
| alpha | LPL | R3 | robustness | 0.489 [0.443, 0.530] | 0.667 |
| alpha | MA | R3 | robustness | 0.561 [0.520, 0.603] | 0.667 |
| alpha | CM | R4 | robustness | 0.824 [0.792, 0.855] | 0.667 |
| alpha | LPL | R4 | robustness | 0.960 [0.916, 0.991] | 0.667 |
| alpha | MA | R4 | robustness | 0.056 [-0.026, 0.141] | 0.667 |
| alpha | LPL | R5 | robustness | 0.513 [0.466, 0.556] | 0.667 |
| alpha | CM | R6 | robustness | 0.599 [0.564, 0.635] | 0.667 |
| alpha | LPL | R6 | robustness | 0.540 [0.498, 0.577] | 0.667 |
| alpha | MA | R6 | robustness | 0.059 [0.010, 0.113] | 0.667 |
| alpha | CM | R7c | robustness | 0.804 [0.777, 0.832] | 0.667 |
| alpha | LPL | R7c | robustness | 0.513 [0.469, 0.554] | 0.667 |
| alpha | MA | R7c | robustness | -0.050 [-0.107, 0.012] | 0.667 |
| auc | CM | primary | primary | 0.541 [0.513, 0.568] | 0.5 |
| auc | LPL | primary | primary | 0.433 [0.409, 0.458] | 0.5 |
| auc | MA | primary | primary | 0.520 [0.299, 0.727] | 0.5 |
| auc | CM | R2 | robustness | 0.539 [0.511, 0.566] | 0.5 |
| auc | LPL | R2 | robustness | 0.495 [0.472, 0.518] | 0.5 |
| auc | MA | R2 | robustness | 0.525 [0.301, 0.740] | 0.5 |
| auc | CM | R3 | robustness | 0.547 [0.522, 0.574] | 0.5 |
| auc | LPL | R3 | robustness | 0.450 [0.425, 0.474] | 0.5 |
| auc | MA | R3 | robustness | 0.474 [0.434, 0.514] | 0.5 |
| auc | CM | R4 | robustness | 0.555 [0.524, 0.585] | 0.5 |
| auc | LPL | R4 | robustness | 0.577 [0.522, 0.628] | 0.5 |
| auc | MA | R4 | robustness | 0.606 [0.408, 0.779] | 0.5 |
| auc | LPL | R5 | robustness | 0.514 [0.490, 0.538] | 0.5 |
| auc | CM | R6 | robustness | 0.541 [0.515, 0.569] | 0.5 |
| auc | LPL | R6 | robustness | 0.433 [0.409, 0.458] | 0.5 |
| auc | MA | R6 | robustness | 0.506 [0.296, 0.717] | 0.5 |
| rq4_LR | CM | primary | primary | -0.024 [-0.072, 0.024] | 0.0 |
| rq4_LR | LPL | primary | primary | -0.224 [-0.322, -0.127] | 0.0 |
| rq4_LR | CM | R2 | robustness | -0.014 [-0.060, 0.031] | 0.0 |
| rq4_LR | LPL | R2 | robustness | -0.112 [-0.183, -0.037] | 0.0 |
| rq4_LR | CM | R3 | robustness | 0.033 [-0.010, 0.076] | 0.0 |
| rq4_LR | LPL | R3 | robustness | 0.078 [-0.008, 0.159] | 0.0 |
| rq4_LR | CM | R4 | robustness | -0.012 [-0.063, 0.037] | 0.0 |
| rq4_LR | LPL | R4 | robustness | -0.208 [-0.372, -0.062] | 0.0 |
| rq4_LR | LPL | R5 | robustness | -0.255 [-0.343, -0.160] | 0.0 |
| rq4_LR | CM | R6 | robustness | -0.011 [-0.058, 0.037] | 0.0 |
| rq4_LR | LPL | R6 | robustness | -0.224 [-0.322, -0.127] | 0.0 |
| rq4_RF | CM | primary | primary | 0.025 [-0.036, 0.089] | 0.0 |
| rq4_RF | LPL | primary | primary | -0.138 [-0.217, -0.062] | 0.0 |
| rq4_RF | CM | R2 | robustness | 0.052 [-0.007, 0.113] | 0.0 |
| rq4_RF | LPL | R2 | robustness | -0.061 [-0.127, 0.005] | 0.0 |
| rq4_RF | CM | R3 | robustness | 0.011 [-0.047, 0.072] | 0.0 |
| rq4_RF | LPL | R3 | robustness | 0.062 [-0.009, 0.126] | 0.0 |
| rq4_RF | CM | R4 | robustness | 0.025 [-0.044, 0.100] | 0.0 |
| rq4_RF | LPL | R4 | robustness | -0.113 [-0.274, 0.045] | 0.0 |
| rq4_RF | LPL | R5 | robustness | -0.062 [-0.137, 0.017] | 0.0 |
| rq4_RF | CM | R6 | robustness | 0.039 [-0.019, 0.101] | 0.0 |
| rq4_RF | LPL | R6 | robustness | -0.138 [-0.217, -0.062] | 0.0 |
| best_mcc | CM | primary (LR) | primary | 0.095 [0.052, 0.136] | 0.0 |
| best_mcc | LPL | primary (GB) | primary | 0.232 [0.184, 0.278] | 0.0 |
| best_mcc | LPL | R5 (SVM) | robustness | 0.269 [0.213, 0.321] | 0.0 |

Table: `tables/spec_curves.csv`. Figures: `figures/spec_curve_alpha.pdf`, `spec_curve_auc.pdf`, `spec_curve_rq4_LR.pdf`, `spec_curve_rq4_RF.pdf`, `spec_curve_best_mcc.pdf` (.png).
