**Analysis type: robustness (sensitivity; replaces annotator removal, which is impossible without annotator ids).**

**Method.**
- The section-B protocol (nested tuning, 25 splits) for the best model, with training labels from R4 (run annotations removed) or R6 (no consistency filter).
- Paired comparison: the variant-trained model and the primary model are evaluated on the same primary unanimous test entities. Δ = variant − primary, with a paired bootstrap CI.
- Unpaired: each variant is also evaluated on its own unanimous labels (own 5 × 5 project splits).

| smell | model | training labels | variant unanimous n | paired: macro-F1 (primary → variant) | Δ macro-F1 [95% CI] | paired: MCC (primary → variant) | Δ MCC [95% CI] | own labels macro-F1 [95% CI] | own labels MCC [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| CM | LR | R4 | 1358 | 0.525 → 0.526 | 0.002 [-0.010, 0.012] | 0.095 → 0.089 | -0.006 [-0.030, 0.016] | 0.510 [0.486, 0.536] | 0.095 [0.049, 0.146] |
| CM | LR | R6 | 1866 | 0.525 → 0.524 | -0.001 [-0.009, 0.007] | 0.095 → 0.084 | -0.011 [-0.028, 0.005] | 0.512 [0.492, 0.532] | 0.076 [0.038, 0.118] |
| LPL | GB | R4 | 250 | 0.616 → 0.570 | -0.046 [-0.069, -0.023] | 0.232 → 0.153 | -0.079 [-0.124, -0.034] | 0.633 [0.571, 0.695] | 0.267 [0.145, 0.395] |
| LPL | GB | R6 | 1325 | 0.616 → 0.616 | 0.000 [0.000, 0.000] | 0.232 → 0.232 | 0.000 [0.000, 0.000] | 0.616 [0.591, 0.638] | 0.232 [0.184, 0.278] |

Table: `tables/sensitivity.csv`. Runtime G+I+J 58s.
