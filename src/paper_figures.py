"""Paper-ready figures in IEEE sizes (no new analysis). Vector PDF, fonts >= 7 pt, into results/paper_figures/.

fig1_answer_runs (single column), fig2_spec_curves (double column), fig3_human_ceiling (single column),
fig4_ablation (single column: C1/C3 deltas for CM and LPL R5).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

OUT = os.path.join(ROOT, "results/paper_figures")
os.makedirs(OUT, exist_ok=True)
SINGLE, DOUBLE = 3.5, 7.16
SM_COL = {"CM": COL["blue"], "LPL": COL["orange"], "MA": COL["aqua"]}


def style():
    plt = plot_style()
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "legend.fontsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "savefig.bbox": "standard"})  # exact IEEE widths
    return plt


def save(fig, name):
    fig.savefig(os.path.join(OUT, f"{name}.pdf"))
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=300)


def fig1(plt):
    L = annotation_long()
    R = pd.read_csv(os.path.join(TAB, "audit_answer_runs.csv"))
    fig, axes = plt.subplots(3, 1, figsize=(SINGLE, 3.3), sharex=True)
    for ax, s in zip(axes, SMELLS):
        x = L[L.smell == s].sort_values("ann_id")
        roll = x.answer.rolling(50, center=True, min_periods=10).mean().values.astype(float)
        ids = x.ann_id.values.astype(float)
        gap = np.r_[False, np.diff(ids) > 200]
        ax.plot(np.insert(ids, np.where(gap)[0], np.nan), np.insert(roll, np.where(gap)[0], np.nan), color=SM_COL[s], lw=1.1)
        for r in R[R.smell == s].itertuples():
            ax.axvspan(r.first_ann_id, r.last_ann_id, color=COL["ink2"], alpha=0.15, lw=0)
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks([0, 0.5, 1])
        ax.set_ylabel("yes-rate")
        ax.set_title(f"{SMELL_NAME[s]} ({CHECKBOX[s]})", loc="left")
        ax.grid(axis="x", visible=False)
    axes[-1].set_xlabel("annotation id")
    axes[0].plot([], [], color=COL["ink2"], alpha=0.3, lw=5, label="run of ≥40 identical answers")
    axes[0].legend(loc="lower left", frameon=False)
    fig.tight_layout(h_pad=0.4)
    save(fig, "fig1_answer_runs")


def fig2(plt):
    S = pd.read_csv(os.path.join(TAB, "spec_curves.csv"))
    titles = {"alpha": "Krippendorff's α", "auc": "Primary-metric ROC-AUC", "rq4_LR": "RQ4 ΔMCC (LR)",
              "rq4_RF": "RQ4 ΔMCC (RF)", "best_mcc": "Best-model MCC"}
    keys = list(titles)
    from matplotlib.ticker import MaxNLocator
    fig, grid = plt.subplots(2, 3, figsize=(DOUBLE, 5.2))
    axes = grid.ravel()[:len(keys)]
    for ax, k in zip(axes, keys):
        x = S[S.spec == k].copy()
        x["smell"] = pd.Categorical(x.smell, SMELLS)
        x = x.sort_values(["smell", "estimate"]).reset_index(drop=True)
        ys = np.arange(len(x))[::-1]
        for yy, r in zip(ys, x.itertuples()):
            prim = str(r.condition).startswith("primary")
            ax.plot([r.lo, r.hi], [yy, yy], color=SM_COL[r.smell], lw=1)
            ax.scatter(r.estimate, yy, s=16 if prim else 10, color=SM_COL[r.smell], marker="D" if prim else "o", zorder=3,
                       edgecolor="black" if prim else "none", lw=0.5)
        ax.axvline(x.reference.iloc[0], color=COL["ink2"], lw=0.7, ls=":")
        ax.set_yticks(ys)
        ax.set_yticklabels([f"{r.smell} {str(r.condition).split(' (')[0]}" for r in x.itertuples()])
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.set_title(titles[k], loc="left")
        ax.grid(axis="y", visible=False)
    leg = grid.ravel()[-1]
    leg.axis("off")
    for s_ in SMELLS:
        leg.plot([], [], color=SM_COL[s_], lw=1.5, label=SMELL_NAME[s_])
    leg.scatter([], [], marker="D", color="white", edgecolor="black", s=16, label="primary")
    leg.scatter([], [], marker="o", color=COL["ink2"], s=10, label="robustness check")
    leg.plot([], [], color=COL["ink2"], ls=":", lw=0.7, label="reference line\n(α 0.667; AUC 0.5; MCC 0)")
    leg.legend(loc="center left", frameon=False)
    fig.tight_layout(w_pad=0.8, h_pad=1.0)
    save(fig, "fig2_spec_curves")


def fig3(plt):
    H = pd.read_csv(os.path.join(TAB, "human_ceiling.csv"))
    H = H[H.metric == "MCC"].reset_index(drop=True)
    Mm = pd.read_csv(os.path.join(TAB, "agreement_matched_neardup.csv")).set_index("population")
    fig, ax = plt.subplots(figsize=(SINGLE, 3.0))
    ys = np.arange(len(H))[::-1] * 1.0
    off = {"human–human, all entities": 0.27, "human–human, same snippet (matched)": 0.09,
           "human–human, identical-structure snippets": -0.09, "best model vs one human": -0.27}
    style_ = {"human–human, all entities": ("o", COL["orange"]), "human–human, same snippet (matched)": ("^", COL["orange"]),
              "human–human, identical-structure snippets": ("v", COL["aqua"]), "best model vs one human": ("s", COL["blue"])}
    for yy, r in zip(ys, H.itertuples()):
        m = Mm.loc[r.population]
        vals = {"human–human, all entities": (r.human_vs_human, r.human_lo, r.human_hi),
                "human–human, same snippet (matched)": (m.same_MCC, m.same_lo, m.same_hi),
                "human–human, identical-structure snippets": (m.cross_MCC, m.cross_lo, m.cross_hi),
                "best model vs one human": (r.model_vs_single_human, r.model_lo, r.model_hi)}
        for k, (e, lo, hi) in vals.items():
            mk, c = style_[k]
            ax.errorbar(e, yy + off[k], xerr=[[e - lo], [hi - e]], fmt=mk, color=c, ms=3.8, capsize=0, lw=1,
                        label=k if yy == ys[0] else None)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r.population} ({r.best_model})" for r in H.itertuples()])
    ax.set_xlim(-0.2, 1.02)
    ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
    ax.set_xlabel("MCC against a single annotation")
    ax.grid(axis="y", visible=False)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left", ncol=1, frameon=False, fontsize=7,
               handletextpad=0.3, bbox_to_anchor=(0.02, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.74))
    save(fig, "fig3_human_ceiling")


def fig4(plt):
    cm = pd.read_csv(os.path.join(TAB, "ablation_CM.csv"))
    r5 = pd.read_csv(os.path.join(TAB, "ablation_LPL_R5.csv"))
    bm = pd.read_csv(os.path.join(TAB, "model_comparison_LPL_R5.csv"))
    best_r5 = bm[bm.best_model].model.iloc[0]
    keep = ["(i) primary only", "DACOSX only", "DACOSX + DACOS", "DACOSX only, primary metric removed"]
    lab = {"(i) primary only": "C1 primary metric only", "DACOSX only": "C3 DACOSX only",
           "DACOSX + DACOS": "C3 DACOSX + DACOS", "DACOSX only, primary metric removed": "C3 DACOSX, no primary"}
    rows = []
    for name, d, m in (("CM (LR)", cm, "LR"), (f"LPL R5 ({best_r5})", r5, best_r5)):
        for v in keep:
            x = d[(d.model == m) & (d.variant == v)].iloc[0]
            rows.append((name, lab[v], x.d_MCC, x.d_MCC_lo, x.d_MCC_hi))
    fig, ax = plt.subplots(figsize=(SINGLE, 2.2))
    cats = [lab[v] for v in keep]
    for j, (name, c) in enumerate(((f"CM (LR)", COL["blue"]), (f"LPL R5 ({best_r5})", COL["orange"]))):
        xs = [r for r in rows if r[0] == name]
        ys = np.arange(len(cats))[::-1] + (0.15 if j == 0 else -0.15)
        ax.errorbar([r[2] for r in xs], ys, xerr=[[r[2] - r[3] for r in xs], [r[4] - r[2] for r in xs]], fmt="o", ms=3.5,
                    color=c, capsize=0, label=name)
    ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
    ax.set_yticks(np.arange(len(cats))[::-1])
    ax.set_yticklabels(cats)
    ax.set_xlabel("ΔMCC vs all features, DACOS-trained")
    ax.grid(axis="y", visible=False)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    save(fig, "fig4_ablation")


def main():
    plt = style()
    fig1(plt)
    fig2(plt)
    fig3(plt)
    fig4(plt)
    print("paper figures:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
