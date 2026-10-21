**Analysis type: primary.**

**Method.**
- Best model with each fold's section-B parameters, on the repeat-0 folds.
- Each training fold is subsampled per class (stratified) to 10/25/50/75/100%, with 5 seeds (seed 20261021 + s, also used as the model seed).
- Macro-F1 is computed on pooled out-of-fold predictions per seed.
- Plateau rule (fixed in plan.md): plateaued if the macro-F1 gain from 75% to 100% is < 0.01 and its paired bootstrap CI includes 0.

| smell | model | fraction | mean_train_n | macro_F1_mean | macro_F1_sd | MCC_mean |
|---|---|---|---|---|---|---|
| CM | LR | 0.1 | 135.6 | 0.513 | 0.027 | 0.055 |
| CM | LR | 0.25 | 338.8 | 0.53 | 0.021 | 0.096 |
| CM | LR | 0.5 | 677.8 | 0.512 | 0.012 | 0.083 |
| CM | LR | 0.75 | 1017.2 | 0.506 | 0.006 | 0.077 |
| CM | LR | 1.0 | 1356.0 | 0.521 | 0.0 | 0.1 |
| LPL | GB | 0.1 | 106.2 | 0.556 | 0.011 | 0.122 |
| LPL | GB | 0.25 | 265.0 | 0.604 | 0.01 | 0.213 |
| LPL | GB | 0.5 | 530.0 | 0.611 | 0.019 | 0.223 |
| LPL | GB | 0.75 | 795.0 | 0.608 | 0.01 | 0.217 |
| LPL | GB | 1.0 | 1060.0 | 0.612 | 0.0 | 0.225 |

| smell | model | gain 75%→100% [95% CI] | plateaued_by_rule |
|---|---|---|---|
| CM | LR | 0.015 [0.005, 0.025] | False |
| LPL | GB | 0.005 [-0.007, 0.016] | True |

Tables: `tables/learning_curve.csv`, `tables/learning_curve_plateau.csv`. Figure: `figures/learning_curve.pdf` (.png). Runtime F+H 10s.

**Summary.** CM (LR): gain 75%→100% = 0.015 [0.005, 0.025], plateaued by rule: no; macro-F1 across all fractions ranges 0.506–0.530; LPL (GB): gain 75%→100% = 0.005 [-0.007, 0.016], plateaued by rule: yes; macro-F1 across all fractions ranges 0.556–0.612.
