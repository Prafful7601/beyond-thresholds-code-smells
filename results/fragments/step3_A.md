**Analysis type: primary.** These baselines are reported alongside every model in sections B–J.
- Splits: the same 25 project-grouped splits as section B (5 repeats × 5 folds; projects shuffled with seed 20261021 + r and assigned round-robin).
- Majority class: the training fold's majority label is predicted for everyone. With a constant score, ROC-AUC = 0.5, PR-AUC = prevalence and MCC = 0.
- DesigniteJava rule: smelly if metric ≥ default (cc ≥ 8, pc ≥ 5). The score is the metric itself.
- Youden rule: smelly if metric ≥ c, with c chosen on the training fold only. The per-fold cut-offs are in `tables/baselines.csv`.
- Metrics: mean ± SD over the 5 repeats of pooled out-of-fold metrics. The CI is a bootstrap over entities (B = 2000) of the repeat-mean.

| smell | baseline | n | macro-F1 mean ± SD [95% CI] | MCC mean ± SD [95% CI] | ROC-AUC mean ± SD [95% CI] | PR-AUC mean ± SD [95% CI] |
|---|---|---|---|---|---|---|
| CM | majority class | 1695 | 0.400 ± 0.000 [0.392, 0.408] | 0.000 ± 0.000 [0.000, 0.000] | 0.500 ± 0.000 [0.500, 0.500] | 0.666 ± 0.000 [0.644, 0.689] |
| CM | DesigniteJava default rule | 1695 | 0.434 ± 0.000 [0.410, 0.456] | 0.044 ± 0.000 [-0.003, 0.090] | 0.541 ± 0.000 [0.513, 0.568] | 0.696 ± 0.000 [0.670, 0.725] |
| CM | Youden rule (fitted in training fold) | 1695 | 0.506 ± 0.018 [0.484, 0.527] | 0.032 ± 0.031 [-0.012, 0.074] | 0.541 ± 0.000 [0.513, 0.568] | 0.696 ± 0.000 [0.670, 0.725] |
| LPL | majority class | 1325 | 0.396 ± 0.000 [0.386, 0.405] | 0.000 ± 0.000 [0.000, 0.000] | 0.500 ± 0.000 [0.500, 0.500] | 0.654 ± 0.000 [0.629, 0.680] |
| LPL | DesigniteJava default rule | 1325 | 0.393 ± 0.000 [0.367, 0.420] | -0.013 ± 0.000 [-0.070, 0.044] | 0.434 ± 0.000 [0.409, 0.459] | 0.628 ± 0.000 [0.599, 0.658] |
| LPL | Youden rule (fitted in training fold) | 1325 | 0.285 ± 0.029 [0.268, 0.301] | -0.053 ± 0.022 [-0.098, -0.008] | 0.434 ± 0.000 [0.409, 0.459] | 0.628 ± 0.000 [0.599, 0.658] |

Table: `tables/baselines.csv`.
