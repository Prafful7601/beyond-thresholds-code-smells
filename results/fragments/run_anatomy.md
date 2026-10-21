**Analysis type: robustness (R7, descriptive).** Method per plan.md §4.2.
- (a) Each run's annotations are taken in annotation-id order.
  - Spearman ρ of annotation id with `sample.id` and with the entity's primary metric, with their p-values.
  - Project switches along the run, compared with 2000 random permutations of the run's own order. The one-sided p is the share of permutations with ≤ the observed switches, so a small p means projects are more clustered than random order.
  - The `ALL (reference)` row applies the same statistics to the whole smell stream.
- (b) Co-location in the unfiltered stream: the share of entities with ≥ 2 annotations that have at least 2 annotations inside the same run. The null permutes annotation-to-position within smell 2000 times, keeping run positions fixed.
- (c) Alpha without co-located entities is reported in the robustness summary (column R7c).

**(a) Run anatomy**

| smell | run_id | length | answer | n_entities | n_projects | metric_median | metric_q1 | metric_q3 | rho_annid_sample_id | p_annid_sample_id | rho_annid_primary_metric | p_annid_primary_metric | project_switches | project_switches_null_mean | p_fewer_switches_than_random |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CM | ALL (reference) | 4555 | mixed | 2275 | 10 | 6.0 | 5.0 | 8.0 | 0.735 | 0.00e+00 | -0.1 | 1.12e-11 | 528 | 3862.084 | 5.00e-04 |
| CM | CM-0 | 63 | 1 | 62 | 3 | 6.0 | 5.0 | 8.0 | 0.963 | 1.98e-36 | -0.105 | 0.4130 | 14 | 32.508 | 5.00e-04 |
| CM | CM-1 | 40 | 1 | 40 | 1 | 7.0 | 5.0 | 9.25 | 0.437 | 0.0048 | 0.25 | 0.1192 | 0 | 0.0 | 1.0000 |
| CM | CM-2 | 69 | 1 | 69 | 1 | 7.0 | 5.0 | 8.0 | 0.977 | 1.36e-46 | 0.013 | 0.9132 | 0 | 0.0 | 1.0000 |
| CM | CM-3 | 50 | 1 | 50 | 1 | 6.0 | 5.0 | 7.0 | 0.968 | 1.33e-30 | 0.11 | 0.4471 | 0 | 0.0 | 1.0000 |
| CM | CM-4 | 170 | 1 | 170 | 5 | 6.0 | 5.0 | 8.0 | 0.992 | 4.77e-153 | 0.028 | 0.7135 | 11 | 102.07 | 5.00e-04 |
| CM | CM-5 | 73 | 0 | 73 | 1 | 7.0 | 6.0 | 8.0 | 0.984 | 3.93e-55 | -0.111 | 0.3479 | 0 | 0.0 | 1.0000 |
| CM | CM-6 | 246 | 1 | 246 | 2 | 6.0 | 5.0 | 7.0 | 0.549 | 9.74e-21 | 0.045 | 0.4840 | 73 | 121.146 | 5.00e-04 |
| CM | CM-7 | 133 | 0 | 133 | 10 | 6.0 | 5.0 | 7.0 | 0.825 | 2.49e-34 | -0.041 | 0.6369 | 21 | 105.274 | 5.00e-04 |
| LPL | ALL (reference) | 3392 | mixed | 1694 | 10 | 4.0 | 4.0 | 5.0 | 0.41 | 2.31e-137 | -0.35 | 1.27e-98 | 315 | 2938.536 | 5.00e-04 |
| LPL | LPL-0 | 55 | 1 | 54 | 3 | 5.0 | 4.0 | 6.0 | 0.854 | 1.23e-16 | 0.47 | 2.94e-04 | 3 | 21.34 | 5.00e-04 |
| LPL | LPL-1 | 305 | 0 | 305 | 5 | 4.0 | 4.0 | 6.0 | 0.532 | 1.03e-23 | 0.135 | 0.0183 | 13 | 225.641 | 5.00e-04 |
| LPL | LPL-2 | 41 | 0 | 41 | 6 | 4.0 | 4.0 | 5.0 | 0.916 | 4.47e-17 | -0.457 | 0.0027 | 11 | 28.994 | 5.00e-04 |
| LPL | LPL-3 | 1054 | 1 | 917 | 10 | 4.0 | 3.0 | 4.0 | -0.071 | 0.0206 | -0.703 | 7.02e-158 | 82 | 875.13 | 5.00e-04 |
| LPL | LPL-4 | 296 | 0 | 296 | 4 | 4.0 | 4.0 | 4.0 | 1.0 | 0.00e+00 | 0.122 | 0.0365 | 5 | 205.094 | 5.00e-04 |
| MA | ALL (reference) | 2710 | mixed | 1009 | 10 | 0.6 | 0.5 | 0.667 | 0.79 | 0.00e+00 | -0.001 | 0.9621 | 209 | 2175.887 | 5.00e-04 |
| MA | MA-0 | 1474 | 1 | 861 | 10 | 0.571 | 0.5 | 0.667 | 0.984 | 0.00e+00 | -0.008 | 0.7602 | 136 | 1237.181 | 5.00e-04 |
| MA | MA-1 | 141 | 1 | 141 | 5 | 0.6 | 0.5 | 0.667 | 0.043 | 0.6111 | 0.048 | 0.5755 | 14 | 97.61 | 5.00e-04 |

Project composition per run (counts; truncated in this table, full in the CSV):

| smell | run_id | projects |
|---|---|---|
| CM | ALL (reference) | MyCATApache_Mycat-Server 1150; MovingBlocks_Terasology 710; igniterealtime_Smack 688; alibaba_arthas 535; kevin-wayne_al |
| CM | CM-0 | linlinjava_litemall 40; macrozheng_mall 17; Blankj_AndroidUtilCode 6 |
| CM | CM-1 | alibaba_arthas 40 |
| CM | CM-2 | MyCATApache_Mycat-Server 69 |
| CM | CM-3 | MyCATApache_Mycat-Server 50 |
| CM | CM-4 | alibaba_arthas 93; Blankj_AndroidUtilCode 51; linlinjava_litemall 16; shuzheng_zheng 7; macrozheng_mall 3 |
| CM | CM-5 | MyCATApache_Mycat-Server 73 |
| CM | CM-6 | MyCATApache_Mycat-Server 139; igniterealtime_Smack 107 |
| CM | CM-7 | igniterealtime_Smack 50; MyCATApache_Mycat-Server 21; alibaba_arthas 17; Blankj_AndroidUtilCode 14; MovingBlocks_Terasol |
| LPL | ALL (reference) | lettuce-io_lettuce-core 728; Blankj_AndroidUtilCode 494; MovingBlocks_Terasology 478; igniterealtime_Smack 428; MyCATApa |
| LPL | LPL-0 | linlinjava_litemall 41; macrozheng_mall 13; Blankj_AndroidUtilCode 1 |
| LPL | LPL-1 | Blankj_AndroidUtilCode 117; linlinjava_litemall 83; macrozheng_mall 38; MyCATApache_Mycat-Server 34; alibaba_arthas 33 |
| LPL | LPL-2 | igniterealtime_Smack 17; MyCATApache_Mycat-Server 13; alibaba_arthas 5; Blankj_AndroidUtilCode 3; linlinjava_litemall 2; |
| LPL | LPL-3 | Blankj_AndroidUtilCode 297; lettuce-io_lettuce-core 230; MovingBlocks_Terasology 129; alibaba_arthas 96; igniterealtime_ |
| LPL | LPL-4 | lettuce-io_lettuce-core 121; MovingBlocks_Terasology 93; igniterealtime_Smack 53; kevin-wayne_algs4 29 |
| MA | ALL (reference) | MovingBlocks_Terasology 960; igniterealtime_Smack 464; MyCATApache_Mycat-Server 368; alibaba_arthas 300; Blankj_AndroidU |
| MA | MA-0 | MovingBlocks_Terasology 375; alibaba_arthas 300; Blankj_AndroidUtilCode 192; igniterealtime_Smack 162; linlinjava_litema |
| MA | MA-1 | MovingBlocks_Terasology 57; igniterealtime_Smack 46; lettuce-io_lettuce-core 24; MyCATApache_Mycat-Server 13; kevin-wayn |

Share of each LPL run's annotations on the pc = 3 entities with an empty `smells` field:

| run_id | share_pc3_empty |
|---|---|
| LPL-0 | 0.0 |
| LPL-1 | 0.0 |
| LPL-2 | 0.0 |
| LPL-3 | 0.26 |
| LPL-4 | 0.0 |

**(b) Co-location of an entity's annotations within runs**

| smell | entities_ge2_annotations | observed_colocated | observed_share | null_mean_share | null_q025 | null_q975 | p_one_sided | annotations_in_runs_share |
|---|---|---|---|---|---|---|---|---|
| CM | 2275 | 1 | 0.0 | 0.006 | 0.003 | 0.009 | 1.0000 | 0.185 |
| LPL | 1694 | 138 | 0.081 | 0.113 | 0.101 | 0.125 | 1.0000 | 0.516 |
| MA | 1009 | 585 | 0.58 | 0.453 | 0.435 | 0.47 | 5.00e-04 | 0.596 |

Tables: `tables/run_anatomy.csv`, `tables/run_colocation.csv`. Figure: `figures/run_anatomy.pdf` (.png).

**Summary.** Share of entities with ≥ 2 annotations inside the same run: CM: observed 0.000 versus null mean 0.006 (p = 1.0000); LPL: observed 0.081 versus null mean 0.113 (p = 1.0000); MA: observed 0.580 versus null mean 0.453 (p = 5.00e-04).
