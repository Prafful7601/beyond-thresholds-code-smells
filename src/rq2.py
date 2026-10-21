"""RQ2 Threshold validity in the borderline band (plan §2 RQ2, D10, D11).

Primary set: consistency-filtered annotations; unanimous entities (= majority labels with ties excluded).
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score, roc_curve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402


def youden(x, y):
    cands = np.unique(x)
    P, N = y.sum(), (1 - y).sum()
    best, bestc = -np.inf, np.nan
    for c in cands:  # ascending -> ties resolved to the smallest c
        pred = x >= c
        j = (pred & (y == 1)).sum() / P - (pred & (y == 0)).sum() / N
        if j > best + 1e-12:
            best, bestc = j, c
    return bestc, best


def prf(pred, y):
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    p = tp / (tp + fp) if tp + fp else np.nan
    r = tp / (tp + fn) if tp + fn else np.nan
    f = 2 * p * r / (p + r) if (tp + fp) and (tp + fn) and (p + r) else (0.0 if tp + fn else np.nan)
    return p, r, f


def analyse(E, smell, label="primary"):
    e = E[(E.smell == smell) & E.target.notna()].dropna(subset=[PRIMARY[smell]])
    x = e[PRIMARY[smell]].values.astype(float)
    y = e.target.values.astype(int)
    rules = {"Youden": None, "DesigniteJava default": lambda d: d[PRIMARY[smell]].values >= DESIGNITE[smell]}
    if smell == "MA":
        rules["DesigniteJava full MA rule"] = lambda d: ((d.lcom.values >= 0.8) & (d.nof.values >= 7) & (d.nom.values >= 7))
    out = {"set": label, "smell": smell, "metric": PRIMARY[smell], "n": len(e), "n_smelly": int(y.sum()),
           "n_benign": int((1 - y).sum())}
    if y.sum() == 0 or y.sum() == len(y):
        out["note"] = "single class"
        return out, None, e
    auc = roc_auc_score(y, x)
    u = mannwhitneyu(x[y == 1], x[y == 0], alternative="greater")
    c, j = youden(x, y)
    out.update({"auc": auc, "mwu_U": float(u.statistic), "mwu_p_one_sided": float(u.pvalue), "youden_cut": c,
                "youden_J": j, "designite_cut": DESIGNITE[smell]})
    preds = {"Youden": x >= c}
    for k, fn in rules.items():
        if fn is not None:
            preds[k] = fn(e)
    for k, pr in preds.items():
        p, r, f = prf(pr, y)
        out[f"{k}|precision"], out[f"{k}|recall"], out[f"{k}|F1"] = p, r, f
    # bootstrap
    r_ = rng()
    bs = {"auc": [], "youden_cut": []}
    for k in preds:
        for m in ("precision", "recall", "F1"):
            bs[f"{k}|{m}"] = []
    skipped = 0
    cols = {k: v for k, v in preds.items()}
    for _ in range(B):
        idx = r_.integers(0, len(y), len(y))
        yb = y[idx]
        if yb.min() == yb.max():
            skipped += 1
            continue
        xb = x[idx]
        bs["auc"].append(roc_auc_score(yb, xb))
        bs["youden_cut"].append(youden(xb, yb)[0])
        for k, pr in cols.items():
            p, r, f = prf(pr[idx], yb)
            bs[f"{k}|precision"].append(p)
            bs[f"{k}|recall"].append(r)
            bs[f"{k}|F1"].append(f)
    for k, v in bs.items():
        lo, hi = boot_ci(v)
        out[f"{k}_lo"], out[f"{k}_hi"] = lo, hi
    out["boot_skipped_single_class"] = skipped
    out["designite_outside_youden_CI"] = bool(DESIGNITE[smell] < out["youden_cut_lo"] or DESIGNITE[smell] > out["youden_cut_hi"])
    out["table_I_band"] = f"{TABLE_I[smell][0]}–{TABLE_I[smell][1]}"
    return out, roc_curve(y, x), e


def run(E, label):
    res, rocs, data = [], {}, {}
    for s in SMELLS:
        o, rc, e = analyse(E, s, label)
        res.append(o)
        rocs[s] = rc
        data[s] = e
    return pd.DataFrame(res), rocs, data


def main():
    L = annotation_long()
    E = attach_metrics(entity_labels(primary_filter(L)))
    E = E[E.unanimous]
    R, rocs, data = run(E, "primary")
    R.to_csv(os.path.join(TAB, "rq2_threshold_validity.csv"), index=False)

    # P(smelly | metric value) table
    rate_rows = []
    for s in SMELLS:
        e = data[s]
        if s != "MA":
            v = e[PRIMARY[s]].astype(int).astype(str)
        else:
            bins = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            v = pd.cut(e.lcom, bins, include_lowest=True, labels=[f"{a:.1f}–{b:.1f}" for a, b in zip(bins[:-1], bins[1:])]).astype(str)
        g = e.groupby(v, sort=False).target.agg(["size", "mean"]).reset_index()
        g = g.iloc[np.argsort([float(str(t).split("–")[0]) for t in g.iloc[:, 0]])]
        g.columns = ["value", "entities", "share_smelly"]
        g.insert(0, "smell", s)
        rate_rows.append(g)
    RT = pd.concat(rate_rows, ignore_index=True)
    RT["share_smelly"] = RT.share_smelly.round(3)
    RT.to_csv(os.path.join(TAB, "rq2_share_smelly_by_metric.csv"), index=False)

    # figures
    plt = plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    for ax, s in zip(axes, SMELLS):
        r = R[R.smell == s].iloc[0]
        fpr, tpr, thr = rocs[s]
        ax.plot([0, 1], [0, 1], color=COL["grid"], lw=0.8, ls="--")
        ax.plot(fpr, tpr, color=COL["blue"], lw=1.4)
        e = data[s]
        x, y = e[PRIMARY[s]].values, e.target.values.astype(int)
        for cut, name, c, mk in ((r.youden_cut, "Youden", COL["orange"], "o"), (DESIGNITE[s], "Designite default", COL["aqua"], "s")):
            pred = x >= cut
            ax.scatter(((pred) & (y == 0)).sum() / (y == 0).sum(), ((pred) & (y == 1)).sum() / (y == 1).sum(),
                       s=28, color=c, marker=mk, zorder=3, edgecolor="white", lw=0.8,
                       label=f"{name} ({PRIMARY[s]} ≥ {cut:g})")
        ax.set_title(f"{SMELL_NAME[s]}\nAUC {r.auc:.3f} [{r.auc_lo:.3f}, {r.auc_hi:.3f}], n={int(r.n)}", loc="left")
        ax.set_xlabel("false positive rate")
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect("equal")
        ax.legend(loc="upper left", fontsize=5.8, handletextpad=0.3)
    axes[0].set_ylabel("true positive rate")
    fig.tight_layout()
    savefig(fig, "rq2_roc")

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.0))
    for ax, s in zip(axes, SMELLS):
        g = RT[RT.smell == s].reset_index(drop=True)
        xs = np.arange(len(g))
        ax.bar(xs, g.share_smelly, color=COL["orange"], width=0.7)
        for i, (sh, n) in enumerate(zip(g.share_smelly, g.entities)):
            ax.text(i, sh + 0.02, f"n={n}", ha="center", va="bottom", fontsize=5, color=COL["ink2"], rotation=90)
        lab = [str(v) for v in g.value]
        ax.set_xticks(xs)
        ax.set_xticklabels(lab, rotation=0 if s != "MA" else 45, ha="center" if s != "MA" else "right")
        ax.set_ylim(0, 1.25)
        ax.set_yticks([0, 0.5, 1])
        ax.set_title(SMELL_NAME[s], loc="left")
        ax.set_xlabel(PRIMARY[s])
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("share smelly\n(unanimous entities)")
    fig.tight_layout()
    savefig(fig, "rq2_share_smelly_by_metric")

    # markdown
    rows = []
    for r in R.itertuples():
        rows.append({"smell": r.smell, "metric": r.metric, "n (smelly/benign)": f"{r.n} ({r.n_smelly}/{r.n_benign})",
                     "ROC-AUC [95% CI]": fmt_ci(r.auc, r.auc_lo, r.auc_hi),
                     "MWU U": f"{r.mwu_U:.0f}", "p (one-sided, AUC>0.5)": fmt_p(r.mwu_p_one_sided),
                     "Youden cut [95% CI]": f"≥ {r.youden_cut:g} [{r.youden_cut_lo:g}, {r.youden_cut_hi:g}]",
                     "Youden J": fmt(r.youden_J), "Designite default": f"≥ {DESIGNITE[r.smell]:g}",
                     "default outside Youden CI": "yes" if r.designite_outside_youden_CI else "no",
                     "Table I band": r.table_I_band})
    T1 = pd.DataFrame(rows)
    rows = []
    for r in R.to_dict("records"):
        for k in ("Youden", "DesigniteJava default", "DesigniteJava full MA rule"):
            if f"{k}|F1" not in r or not np.isfinite(r.get(f"{k}|recall", np.nan)):
                continue
            cut = (f"{r['metric']} ≥ {r['youden_cut']:g}" if k == "Youden" else
                   f"{r['metric']} ≥ {DESIGNITE[r['smell']]:g}" if k == "DesigniteJava default" else "lcom ≥ 0.8 & NOF ≥ 7 & NOM ≥ 7")
            rows.append({"smell": r["smell"], "rule": f"{k}: {cut}",
                         "precision [95% CI]": fmt_ci(r[f"{k}|precision"], r[f"{k}|precision_lo"], r[f"{k}|precision_hi"]),
                         "recall [95% CI]": fmt_ci(r[f"{k}|recall"], r[f"{k}|recall_lo"], r[f"{k}|recall_hi"]),
                         "F1 [95% CI]": fmt_ci(r[f"{k}|F1"], r[f"{k}|F1_lo"], r[f"{k}|F1_hi"])})
    T2 = pd.DataFrame(rows)
    rt = RT.copy()
    sent = "; ".join(f"{r.smell}: AUC {r.auc:.3f} [{r.auc_lo:.3f}, {r.auc_hi:.3f}], Youden cut-off {r.metric} ≥ {r.youden_cut:g} "
                     f"[{r.youden_cut_lo:g}, {r.youden_cut_hi:g}] against the default ≥ {DESIGNITE[r.smell]:g}"
                     for r in R.itertuples())
    skipped = ", ".join(f"{r.smell} {r.boot_skipped_single_class}" for r in R.itertuples())
    txt = f"""**Method.**
- Data: consistency-filtered annotations, unanimous entities only. With 2 annotations, majority labels with ties excluded are exactly the unanimous entities (D11).
- Each smell's primary metric is the stored DesigniteJava value (cc, pc, lcom).
- ROC-AUC uses `sklearn.metrics.roc_auc_score`. H2a is tested with a one-sided Mann–Whitney U test (smelly > benign).
- Youden cut-off: the rule is metric ≥ c, with c taken from the observed values; the smallest c maximising J = TPR − FPR is used.
- 95% CIs are bootstrap percentile intervals (B = {B}, resampling entities, seed {SEED}). Resamples with a single class were skipped ({skipped}).
- Precision, recall and F1 treat "smelly" as the positive class. They are evaluated at fixed cut-offs: the full-sample Youden cut-off and the DesigniteJava default.
  - Their CIs resample entities with the cut-off held fixed.
  - The Youden figures are in-sample, so they are optimistic.
- For MA, the full DesigniteJava rule (LCOM ≥ 0.8, NOF ≥ 7, NOM ≥ 7) is also reported.
- A rule that predicts no entity as smelly has undefined precision (shown as n/a); its recall and F1 are 0.
- MA is descriptive only (D8): its unanimous set has {int(R[R.smell == 'MA'].n_benign.iloc[0])} benign entities, so its CIs are wide.

**Discrimination and cut-offs**

{md_table(T1)}

**Precision, recall and F1 at each cut-off**

{md_table(T2)}

**Share smelly by primary-metric value (unanimous entities)**

{md_table(rt)}

Tables: `tables/rq2_threshold_validity.csv`, `tables/rq2_share_smelly_by_metric.csv`. Figures: `figures/rq2_roc.pdf`, `figures/rq2_share_smelly_by_metric.pdf` (.png).

The positions of the paper's Table I bands relative to the annotated ranges are in section 1.5 (descriptive only, D10).

**Summary.** {sent}.
"""
    write_frag("rq2", txt)
    print(txt)


if __name__ == "__main__":
    main()
