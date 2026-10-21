**Method.**
- Primary annotation set: consistency-filtered (D7), with entities that have ≥ 2 usable annotations.
- Percent agreement is the mean over entities of the share of agreeing annotation pairs.
- Krippendorff's alpha is nominal and computed with `krippendorff` 0.8.1. Each entity's answers fill arbitrary coder rows, because the data have no annotator ids; nominal alpha depends only on within-unit value counts.
- An independent implementation from the coincidence matrix agrees with the package to within 1e-9 for every smell.
- 95% CIs are bootstrap percentile intervals (B = 2000, resampling entities, seed 20261021).
- Per-annotator counts and yes-rates are not computable, because there are no annotator ids (D12).
- No hypothesis test is planned for RQ1. Values are read against Krippendorff's 0.667 / 0.800 benchmarks.

**Agreement per smell**

| smell | entities | annotations | yes_rate | unanimous_share | percent agreement [95% CI] | Krippendorff alpha [95% CI] |
|---|---|---|---|---|---|---|
| CM | 1860 | 3724 | 0.651 | 0.911 | 0.912 [0.898, 0.924] | 0.804 [0.774, 0.832] |
| LPL | 1694 | 3392 | 0.62 | 0.783 | 0.783 [0.764, 0.802] | 0.540 [0.498, 0.577] |
| MA | 587 | 1716 | 0.875 | 0.695 | 0.786 [0.760, 0.814] | 0.020 [-0.035, 0.077] |

**Vote-split distribution (entities)**

| votes (yes/n) | CM | LPL | MA |
|---|---|---|---|
| 0/2 | 566 | 458 | 8 |
| 1/2 | 164 | 366 | 62 |
| 2/2 | 1128 | 868 | 217 |
| 1/3 | 0 | 1 | 2 |
| 2/3 | 0 | 0 | 11 |
| 3/3 | 1 | 0 | 45 |
| 1/4 | 0 | 0 | 1 |
| 2/4 | 0 | 0 | 16 |
| 3/4 | 0 | 0 | 87 |
| 4/4 | 0 | 0 | 138 |
| 1/5 | 0 | 1 | 0 |
| 2/5 | 1 | 0 | 0 |

Tables: `tables/rq1_agreement.csv`, `tables/rq1_vote_splits.csv`. Figure: `figures/rq1_vote_splits.pdf` (.png).

**Summary.** CM alpha = 0.804 [0.774, 0.832], percent agreement = 0.912; LPL alpha = 0.540 [0.498, 0.577], percent agreement = 0.783; MA alpha = 0.020 [-0.035, 0.077], percent agreement = 0.786.
