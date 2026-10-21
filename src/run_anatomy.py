"""R7 Run anatomy (plan.md §4.2 a, b; c is in src/robustness.py). Descriptive robustness analysis."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402


def switches(seq):
    seq = np.asarray(seq)
    return int(np.sum(seq[1:] != seq[:-1]))


def order_stats(x, r_):
    """x: one smell's annotations (or one run) in annotation-id order."""
    out = {}
    for col, name in (("sample_id", "sample_id"), ("metric", "primary_metric")):
        if x[col].nunique() > 1:
            rho, p = spearmanr(x.ann_id, x[col])
        else:
            rho, p = np.nan, np.nan
        out[f"rho_annid_{name}"], out[f"p_annid_{name}"] = rho, p
    obs = switches(x.project.values)
    proj = x.project.values
    null = np.array([switches(r_.permutation(proj)) for _ in range(B)])
    out["project_switches"] = obs
    out["project_switches_null_mean"] = float(null.mean())
    out["p_fewer_switches_than_random"] = float((np.sum(null <= obs) + 1) / (B + 1))
    return out


def main():
    L = annotation_long()
    E = attach_metrics(entity_labels(L, min_ann=1))
    met = {(r.smell, r.entity): r[PRIMARY[r.smell]] for _, r in E.iterrows()}
    L["metric"] = [met.get((s, e), np.nan) for s, e in zip(L.smell, L.entity)]
    L = L.rename(columns={"project_name": "project"})
    r_ = rng()
    rows = []
    for smell in SMELLS:
        S = L[L.smell == smell].sort_values("ann_id")
        ref = {"smell": smell, "run_id": "ALL (reference)", "first_ann_id": int(S.ann_id.min()),
               "last_ann_id": int(S.ann_id.max()), "length": len(S), "answer": "mixed",
               "n_projects": S.project.nunique(), "n_entities": S.entity.nunique()}
        ref.update({"metric_median": S.metric.median(), "metric_q1": S.metric.quantile(.25), "metric_q3": S.metric.quantile(.75)})
        ref.update(order_stats(S, r_))
        ref["projects"] = "; ".join(f"{k} {v}" for k, v in S.project.value_counts().items())
        rows.append(ref)
        for rid, x in S[S.run_id != ""].groupby("run_id", sort=False):
            row = {"smell": smell, "run_id": rid, "first_ann_id": int(x.ann_id.min()), "last_ann_id": int(x.ann_id.max()),
                   "length": len(x), "answer": int(x.answer.iloc[0]), "n_projects": x.project.nunique(),
                   "n_entities": x.entity.nunique(), "metric_median": x.metric.median(),
                   "metric_q1": x.metric.quantile(.25), "metric_q3": x.metric.quantile(.75)}
            row.update(order_stats(x, r_))
            row["projects"] = "; ".join(f"{k} {v}" for k, v in x.project.value_counts().items())
            if smell == "LPL":
                row["share_pc3_empty"] = float(x.pc3_empty.mean())
            rows.append(row)
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(TAB, "run_anatomy.csv"), index=False)

    # (b) co-location permutation test (unfiltered stream, entities with >= 2 annotations)
    co_rows = []
    for smell in SMELLS:
        S = L[L.smell == smell].sort_values("ann_id").reset_index(drop=True)
        ent_codes, ent_idx = np.unique(S.entity.values, return_inverse=True)
        n_per = np.bincount(ent_idx)
        multi = n_per >= 2
        runs = S.run_id.values
        run_codes, run_idx = np.unique(runs, return_inverse=True)
        none = np.where(run_codes == "")[0]
        none = none[0] if len(none) else -1
        nr = len(run_codes)

        def share(eidx):
            m = run_idx != none
            key = eidx[m] * nr + run_idx[m]
            k, c = np.unique(key, return_counts=True)
            co = np.zeros(len(ent_codes), bool)
            co[(k[c >= 2] // nr)] = True
            return co[multi].mean(), int(co[multi].sum())
        obs, n_obs = share(ent_idx)
        null = np.array([share(r_.permutation(ent_idx))[0] for _ in range(B)])
        co_rows.append({"smell": smell, "entities_ge2_annotations": int(multi.sum()), "observed_colocated": n_obs,
                        "observed_share": obs, "null_mean_share": float(null.mean()),
                        "null_q025": float(np.percentile(null, 2.5)), "null_q975": float(np.percentile(null, 97.5)),
                        "p_one_sided": float((np.sum(null >= obs) + 1) / (B + 1)),
                        "annotations_in_runs_share": float((runs != "").mean())})
    C = pd.DataFrame(co_rows)
    C.to_csv(os.path.join(TAB, "run_colocation.csv"), index=False)

    # figure: per run, primary-metric distribution vs the smell's overall distribution, and co-location
    plt = plot_style()
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.3), gridspec_kw={"width_ratios": [1.6, 1.2, 0.6, 1.1]})
    for ax, smell in zip(axes[:3], SMELLS):
        S = L[L.smell == smell]
        runs = [rid for rid in A[(A.smell == smell) & (A.run_id != "ALL (reference)")].run_id]
        data = [S.metric.dropna().values] + [S[S.run_id == rid].metric.dropna().values for rid in runs]
        labels = ["all"] + [f"{rid.split('-')[1]}:{'Y' if A.set_index('run_id').loc[rid, 'answer'] == 1 else 'N'}" for rid in runs]
        bp = ax.boxplot(data, vert=True, widths=0.6, patch_artist=True, showfliers=False,
                        medianprops={"color": COL["ink"], "lw": 1})
        for i, b in enumerate(bp["boxes"]):
            b.set_facecolor(COL["grid"] if i == 0 else (COL["orange"] if labels[i].endswith("Y") else COL["blue"]))
            b.set_edgecolor(COL["ink2"])
            b.set_linewidth(0.6)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=90, fontsize=5.5)
        ax.set_title(f"{smell}: {PRIMARY[smell]} by run", loc="left")
        ax.grid(axis="x", visible=False)
    ax = axes[3]
    xs = np.arange(len(C))
    ax.errorbar(xs, C.null_mean_share, yerr=[C.null_mean_share - C.null_q025, C.null_q975 - C.null_mean_share],
                fmt="o", color=COL["ink2"], ms=3, capsize=0, label="permutation null (95%)")
    ax.scatter(xs, C.observed_share, color=COL["orange"], s=18, zorder=3, label="observed")
    ax.set_xticks(xs)
    ax.set_xticklabels(C.smell)
    ax.set_ylim(0, 1)
    ax.set_title("entities with ≥2 annotations\nin the same run", loc="left")
    ax.legend(loc="upper left", fontsize=5.5)
    ax.grid(axis="x", visible=False)
    fig.text(0.01, -0.02, "Run labels: run index : answer (Y = all yes, N = all no). Box = IQR, whiskers = 1.5 IQR.",
             fontsize=5.5, color=COL["ink2"])
    fig.tight_layout()
    savefig(fig, "run_anatomy")

    show = A.copy()
    for c in ("metric_median", "metric_q1", "metric_q3", "rho_annid_sample_id", "rho_annid_primary_metric",
              "project_switches_null_mean"):
        show[c] = show[c].round(3)
    for c in ("p_annid_sample_id", "p_annid_primary_metric", "p_fewer_switches_than_random"):
        show[c] = [fmt_p(v) for v in show[c]]
    show["projects"] = show.projects.str.slice(0, 120)
    cols = ["smell", "run_id", "length", "answer", "n_entities", "n_projects", "metric_median", "metric_q1", "metric_q3",
            "rho_annid_sample_id", "p_annid_sample_id", "rho_annid_primary_metric", "p_annid_primary_metric",
            "project_switches", "project_switches_null_mean", "p_fewer_switches_than_random"]
    lpl = A[(A.smell == "LPL") & A.share_pc3_empty.notna()][["run_id", "share_pc3_empty"]] if "share_pc3_empty" in A else None
    Cm = C.copy()
    for c in ("observed_share", "null_mean_share", "null_q025", "null_q975", "annotations_in_runs_share"):
        Cm[c] = Cm[c].round(3)
    Cm["p_one_sided"] = [fmt_p(v) for v in Cm.p_one_sided]
    sent = "; ".join(f"{r.smell}: observed {r.observed_share:.3f} versus null mean {r.null_mean_share:.3f} "
                     f"(p = {fmt_p(r.p_one_sided)})" for r in C.itertuples())
    txt = f"""**Analysis type: robustness (R7, descriptive).** Method per plan.md §4.2.
- (a) Each run's annotations are taken in annotation-id order.
  - Spearman ρ of annotation id with `sample.id` and with the entity's primary metric, with their p-values.
  - Project switches along the run, compared with {B} random permutations of the run's own order. The one-sided p is the share of permutations with ≤ the observed switches, so a small p means projects are more clustered than random order.
  - The `ALL (reference)` row applies the same statistics to the whole smell stream.
- (b) Co-location in the unfiltered stream: the share of entities with ≥ 2 annotations that have at least 2 annotations inside the same run. The null permutes annotation-to-position within smell {B} times, keeping run positions fixed.
- (c) Alpha without co-located entities is reported in the robustness summary (column R7c).

**(a) Run anatomy**

{md_table(show[cols])}

Project composition per run (counts; truncated in this table, full in the CSV):

{md_table(show[["smell", "run_id", "projects"]])}
"""
    if lpl is not None and len(lpl):
        txt += f"\nShare of each LPL run's annotations on the pc = 3 entities with an empty `smells` field:\n\n{md_table(lpl.round(3))}\n"
    txt += f"""
**(b) Co-location of an entity's annotations within runs**

{md_table(Cm)}

Tables: `tables/run_anatomy.csv`, `tables/run_colocation.csv`. Figure: `figures/run_anatomy.pdf` (.png).

**Summary.** Share of entities with ≥ 2 annotations inside the same run: {sent}.
"""
    write_frag("run_anatomy", txt)
    print(txt)


if __name__ == "__main__":
    main()
