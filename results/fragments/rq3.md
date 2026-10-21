**Analysis type: primary.** MA is not modelled (D8).

**Method.**
- Annotation-level **GEE** (`statsmodels` 0.14.4 `GEE`): Binomial family, logit link, exchangeable working correlation, groups = entity, robust (sandwich) covariance.
- Data: consistency-filtered annotations for every entity with ≥ 2 usable annotations, unanimous and split (D11).
- Predictors: the primary metric and the §1.6 secondary features, each z-standardised over entities. ORs are per 1 SD.
- BH adjustment is within smell and model.
- VIFs are computed on the entity-level standardised design. If any non-primary VIF > 5, a reduced model drops the highest-VIF feature repeatedly (plan §4.3).
- Decision tree: depth 3, `class_weight='balanced'`, on unanimous entities, with raw (unstandardised) features.
- Entities with missing features are dropped (LPL: 1 entity).

**Model data**

| smell | model | annotations | entities | yes_rate | working_correlation | features |
|---|---|---|---|---|---|---|
| CM | full | 3724 | 1860 | 0.651 | 0.798 | cc, loc, statements, max_nesting, comment_ratio, method_calls |
| LPL | full | 3390 | 1693 | 0.62 | 0.524 | pc, loc, statements, max_nesting, comment_ratio, method_calls |

**Odds ratios per 1 SD**

| smell | model | feature | OR per SD [95% CI] | z | p | p (BH) |
|---|---|---|---|---|---|---|
| CM | full | cc | 1.074 [0.964, 1.197] | 1.3 | 0.1933 | 0.2899 |
| CM | full | loc | 1.053 [0.907, 1.224] | 0.68 | 0.4966 | 0.5960 |
| CM | full | statements | 0.995 [0.847, 1.168] | -0.06 | 0.9490 | 0.9490 |
| CM | full | max_nesting | 1.078 [0.973, 1.195] | 1.43 | 0.1521 | 0.2899 |
| CM | full | comment_ratio | 1.098 [0.996, 1.210] | 1.88 | 0.0603 | 0.1810 |
| CM | full | method_calls | 1.190 [1.027, 1.380] | 2.31 | 0.0210 | 0.1263 |
| LPL | full | pc | 0.794 [0.742, 0.849] | -6.69 | 2.18e-11 | 6.54e-11 |
| LPL | full | loc | 1.249 [1.041, 1.497] | 2.4 | 0.0164 | 0.0329 |
| LPL | full | statements | 0.938 [0.783, 1.124] | -0.69 | 0.4876 | 0.5851 |
| LPL | full | max_nesting | 0.637 [0.560, 0.724] | -6.87 | 6.24e-12 | 3.74e-11 |
| LPL | full | comment_ratio | 1.076 [0.975, 1.188] | 1.46 | 0.1452 | 0.2179 |
| LPL | full | method_calls | 0.997 [0.845, 1.176] | -0.04 | 0.9675 | 0.9675 |

**VIF**

| smell | model | cc | comment_ratio | loc | max_nesting | method_calls | pc | statements |
|---|---|---|---|---|---|---|---|---|
| CM | full | 1.38 | 1.13 | 2.42 | 1.26 | 2.32 | – | 3.1 |
| LPL | full | – | 1.15 | 4.32 | 1.96 | 3.25 | 1.03 | 4.87 |

No VIF exceeds 5, so no reduced model was fitted (plan §4.3 rule).

**Decision-tree rules** (`tables/rq3_tree_rules.txt`)

```
=== CM (Complex Method): depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1695 unanimous entities (1129 smelly / 566 benign), unstandardised features.
Leaf weights are class-weighted sample counts [benign, smelly].
|--- method_calls <= 20.500
|   |--- statements <= 17.500
|   |   |--- max_nesting <= 3.500
|   |   |   |--- weights: [377.332, 276.995] class: 0
|   |   |--- max_nesting >  3.500
|   |   |   |--- weights: [62.889, 64.557] class: 1
|   |--- statements >  17.500
|   |   |--- comment_ratio <= 0.172
|   |   |   |--- weights: [190.163, 171.151] class: 0
|   |   |--- comment_ratio >  0.172
|   |   |   |--- weights: [26.952, 40.536] class: 1
|--- method_calls >  20.500
|   |--- loc <= 27.500
|   |   |--- statements <= 16.500
|   |   |   |--- weights: [10.481, 21.769] class: 1
|   |   |--- statements >  16.500
|   |   |   |--- weights: [49.413, 36.032] class: 0
|   |--- loc >  27.500
|   |   |--- cc <= 10.500
|   |   |   |--- weights: [128.772, 221.446] class: 1
|   |   |--- cc >  10.500
|   |   |   |--- weights: [1.497, 15.013] class: 1

=== LPL (Long Parameter List): depth-3 DecisionTreeClassifier(class_weight='balanced', random_state=20261021) on 1325 unanimous entities (867 smelly / 458 benign), unstandardised features.
Leaf weights are class-weighted sample counts [benign, smelly].
|--- pc <= 3.500
|   |--- weights: [0.000, 103.922] class: 1
|--- pc >  3.500
|   |--- max_nesting <= 1.500
|   |   |--- statements <= 12.500
|   |   |   |--- weights: [367.413, 453.893] class: 1
|   |   |--- statements >  12.500
|   |   |   |--- weights: [56.414, 40.499] class: 0
|   |--- max_nesting >  1.500
|   |   |--- loc <= 63.000
|   |   |   |--- weights: [234.334, 51.197] class: 0
|   |   |--- loc >  63.000
|   |   |   |--- weights: [4.340, 12.990] class: 1

```

Tables: `tables/rq3_odds_ratios.csv`, `tables/rq3_vif.csv`, `tables/rq3_tree_rules.txt`. Figure: `figures/rq3_odds_ratios.pdf` (.png).

**Summary.** CM: OR per SD of cc = 1.074 [0.964, 1.197]; LPL: OR per SD of pc = 0.794 [0.742, 0.849].
