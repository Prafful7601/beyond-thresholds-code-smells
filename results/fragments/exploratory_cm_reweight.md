**CM C3 "DACOSX + DACOS" collapse under equal source weight** (exploratory; not in plan.md §4).

Method:
- CM best model (LR) with section-B fold hyperparameters on the 25 splits, tested on held-out DACOS unanimous entities.
- Class-balanced weights are computed within each source, then rescaled so that DACOSX and DACOS contribute equal total weight. The model's own class weighting is switched off, so the weights are not applied twice.

| model | variant | macro_F1 | MCC | predicted_smelly_share |
|---|---|---|---|---|
| LR | as in C3 (pooled class weights) | 0.400 ± 0.000 [0.392, 0.408] | 0.000 ± 0.000 [0.000, 0.000] | 1.0 |
| LR | equal source weight (class-balanced within source) | 0.508 ± 0.004 [0.485, 0.530] | 0.077 ± 0.009 [0.030, 0.123] | 0.43 |

The collapse does not persist under equal source weighting: MCC 0.077 [0.030, 0.123] with predicted-smelly share 0.430, versus MCC 0.000 and share 1.000 with pooled weights. Table: `tables/exploratory_cm_c3_reweight.csv`. Runtime 97s.
