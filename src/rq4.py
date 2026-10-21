"""RQ4 Extremes-to-borderline transfer (plan §2 RQ4, D4, D6, D8, D11, D14).

Train on DACOSX (threshold-derived labels), test on DACOS unanimous entities; compare with in-DACOS
GroupKFold(5) by project and leave-one-project-out CV. Smells failing D8 are skipped.
"""
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

warnings.filterwarnings("ignore", category=UserWarning)

MODELS = {
    "LR": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=10000)),
    "RF": RandomForestClassifier(class_weight="balanced", random_state=SEED),
}


def f1_mcc(y, pred):
    tp = np.sum(pred & (y == 1))
    tn = np.sum(~pred & (y == 0))
    fp = np.sum(pred & (y == 0))
    fn = np.sum(~pred & (y == 1))
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else np.nan
    den = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / den if den > 0 else 0.0
    return f1, mcc


def metrics(y, p):
    pred = p >= 0.5
    f1, mcc = f1_mcc(y, pred)
    auc = roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan
    return f1, mcc, auc


def eligible():
    el = pd.read_csv(os.path.join(TAB, "eligibility.csv"))
    el = el[el.annotation_set == "primary (filtered)"]
    return {r.smell: bool(r.eligible_for_models) for r in el.itertuples()}


def dacosx_frame(smell, L):
    _, smp, mm, cm, ent = load_tables()
    pcode, acode = DACOSX_CODES[smell]
    is_class = 1 if smell == "MA" else 0
    e = ent[ent.smellPresented.isin([pcode, acode])].merge(smp, left_on="sampleId", right_on="id")
    e = e[e.is_class == is_class]
    n_cons = len(e)
    overlap = set(L[L.smell == smell].sample_id)
    n_overlap = int(e.sampleId.isin(overlap).sum())
    e = e[~e.sampleId.isin(overlap)]
    e["target"] = (e.smellPresented == pcode).astype(int)
    E = e[["sampleId", "designite_id", "is_class", "path_to_file", "project_name", "target"]].rename(
        columns={"path_to_file": "path", "project_name": "project"})
    E = attach_metrics(E)
    n_before = len(E)
    E = E.dropna(subset=feature_cols(smell))
    return E, {"consistent_entries": n_cons, "overlap_removed": n_overlap, "missing_features": n_before - len(E)}


def main():
    t0 = time.time()
    L = annotation_long()
    elig = eligible()
    Eall = attach_metrics(entity_labels(primary_filter(L)))
    res, preds, info_rows, diffs, xin = [], [], [], [], []
    for smell in SMELLS:
        if not elig[smell]:
            continue
        feats = feature_cols(smell)
        D = Eall[(Eall.smell == smell) & Eall.unanimous]
        n_d0 = len(D)
        D = D.dropna(subset=feats).reset_index(drop=True)
        X, Xd = dacosx_frame(smell, L)
        info_rows.append({"smell": smell, "features": ", ".join(feats), "DACOS_unanimous": n_d0,
                          "DACOS_missing_features": n_d0 - len(D), "DACOS_test_n": len(D),
                          "DACOS_smelly": int(D.target.sum()), "DACOS_benign": int((1 - D.target).sum()),
                          "DACOSX_consistent": Xd["consistent_entries"], "DACOSX_overlap_removed": Xd["overlap_removed"],
                          "DACOSX_missing_features": Xd["missing_features"], "DACOSX_train_n": len(X),
                          "DACOSX_present": int(X.target.sum()), "DACOSX_absent": int((1 - X.target).sum())})
        y = D.target.values.astype(int)
        P = {}
        for mname, model in MODELS.items():
            m = clone(model).fit(X[feats].values, X.target.values)
            P[(mname, "transfer: DACOSX → DACOS")] = m.predict_proba(D[feats].values)[:, 1]
            for cvname, cv in (("DACOS GroupKFold(5) by project", GroupKFold(5)),
                               ("DACOS leave-one-project-out", LeaveOneGroupOut())):
                oof = np.full(len(D), np.nan)
                for tr, te in cv.split(D[feats], y, groups=D.project):
                    mm_ = clone(model).fit(D[feats].values[tr], y[tr])
                    oof[te] = mm_.predict_proba(D[feats].values[te])[:, 1]
                P[(mname, cvname)] = oof
            # exploratory: DACOSX in-distribution, GroupKFold(5) by project
            oofx = np.full(len(X), np.nan)
            for tr, te in GroupKFold(5).split(X[feats], X.target, groups=X.project):
                mx = clone(model).fit(X[feats].values[tr], X.target.values[tr])
                oofx[te] = mx.predict_proba(X[feats].values[te])[:, 1]
            f1x, mccx, aucx = metrics(X.target.values, oofx)
            xin.append({"smell": smell, "model": mname, "n": len(X), "F1": f1x, "MCC": mccx, "ROC_AUC": aucx})
        # point estimates + bootstrap (same resamples for all settings -> paired differences)
        r_ = rng()
        idxs = [r_.integers(0, len(y), len(y)) for _ in range(B)]
        boot = {k: np.array([metrics(y[i], p[i]) for i in idxs]) for k, p in P.items()}
        for (mname, setting), p in P.items():
            f1, mcc, auc = metrics(y, p)
            bb = boot[(mname, setting)]
            row = {"smell": smell, "model": mname, "setting": setting, "n_test": len(y)}
            for j, (nm, v) in enumerate((("F1", f1), ("MCC", mcc), ("ROC_AUC", auc))):
                lo, hi = boot_ci(bb[:, j])
                row.update({nm: v, f"{nm}_lo": lo, f"{nm}_hi": hi})
            row["pred_positive_share"] = float(np.mean(p >= 0.5))
            res.append(row)
            preds.append(pd.DataFrame({"smell": smell, "entity": D.entity, "project": D.project, "target": y,
                                       "model": mname, "setting": setting, "p_smelly": p}))
        for mname in MODELS:
            t = boot[(mname, "transfer: DACOSX → DACOS")]
            for cvname in ("DACOS GroupKFold(5) by project", "DACOS leave-one-project-out"):
                c = boot[(mname, cvname)]
                for j, nm in enumerate(("MCC", "F1", "ROC_AUC")):
                    jj = {"F1": 0, "MCC": 1, "ROC_AUC": 2}[nm]
                    d = t[:, jj] - c[:, jj]
                    est = metrics(y, P[(mname, "transfer: DACOSX → DACOS")])[jj] - metrics(y, P[(mname, cvname)])[jj]
                    lo, hi = boot_ci(d)
                    diffs.append({"smell": smell, "model": mname, "comparison": f"transfer − {cvname}", "metric": nm,
                                  "difference": est, "lo": lo, "hi": hi,
                                  "boot_share_diff_ge_0": float(np.mean(d >= 0)),
                                  "primary_H4_test": nm == "MCC" and cvname.startswith("DACOS GroupKFold")})
    R = pd.DataFrame(res)
    R.to_csv(os.path.join(TAB, "rq4_transfer.csv"), index=False)
    Dif = pd.DataFrame(diffs)
    Dif.to_csv(os.path.join(TAB, "rq4_paired_differences.csv"), index=False)
    I = pd.DataFrame(info_rows)
    I.to_csv(os.path.join(TAB, "rq4_data.csv"), index=False)
    XI = pd.DataFrame(xin)
    XI.to_csv(os.path.join(TAB, "exploratory_dacosx_in_distribution.csv"), index=False)
    pd.concat(preds).to_csv(os.path.join(TAB, "rq4_predictions.csv.gz"), index=False)

    # figure: MCC with CI per smell/model/setting
    plt = plot_style()
    sm = [s for s in SMELLS if elig[s]]
    settings = ["transfer: DACOSX → DACOS", "DACOS GroupKFold(5) by project", "DACOS leave-one-project-out"]
    colors = [COL["orange"], COL["blue"], COL["aqua"]]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.1), sharey=True)
    for ax, met in zip(axes, ("F1", "MCC", "ROC_AUC")):
        ticks, labels = [], []
        for i, s in enumerate(sm):
            for j, mn in enumerate(MODELS):
                base = i * 3 + j * 1.2
                for k, (st, c) in enumerate(zip(settings, colors)):
                    r = R[(R.smell == s) & (R.model == mn) & (R.setting == st)].iloc[0]
                    yy = base + (k - 1) * 0.3
                    ax.errorbar(r[met], yy, xerr=[[r[met] - r[f"{met}_lo"]], [r[f"{met}_hi"] - r[met]]], fmt="o",
                                color=c, ms=3.5, lw=1, capsize=0, label=st if (i == 0 and j == 0) else None)
                ticks.append(base)
                labels.append(f"{s} {mn}")
        ax.set_yticks(ticks)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_title(met.replace("_", "-"), loc="left")
        ax.axvline(0.5 if met == "ROC_AUC" else 0, color=COL["ink2"], lw=0.6, ls=":")
        ax.grid(axis="y", visible=False)
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.06))
    fig.tight_layout()
    savefig(fig, "rq4_transfer")

    # markdown
    T = R.copy()
    for m in ("F1", "MCC", "ROC_AUC"):
        T[f"{m} [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(T[m], T[f"{m}_lo"], T[f"{m}_hi"])]
    T["predicted smelly share"] = T.pred_positive_share.round(3)
    T = T[["smell", "model", "setting", "n_test", "F1 [95% CI]", "MCC [95% CI]", "ROC_AUC [95% CI]", "predicted smelly share"]]
    Dm = Dif.copy()
    Dm["difference [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(Dm.difference, Dm.lo, Dm.hi)]
    Dm["bootstrap share ≥ 0"] = Dm.boot_share_diff_ge_0.round(4)
    Dm["H4 primary test"] = np.where(Dm.primary_H4_test, "yes", "")
    Dm = Dm[["smell", "model", "comparison", "metric", "difference [95% CI]", "bootstrap share ≥ 0", "H4 primary test"]]
    skipped = [SMELL_NAME[s] for s in SMELLS if not elig[s]]
    h4 = Dif[Dif.primary_H4_test]
    sent = "; ".join(f"{r.smell} {r.model}: transfer MCC − GroupKFold MCC = {r.difference:.3f} [{r.lo:.3f}, {r.hi:.3f}]"
                     for r in h4.itertuples())
    XI_md = XI.copy()
    for c in ("F1", "MCC", "ROC_AUC"):
        XI_md[c] = XI_md[c].round(4)
    txt = f"""**Method.**
- Eligible smells under D8: {', '.join(SMELL_NAME[s] for s in sm)}.
- **{', '.join(skipped)} is skipped** because it fails D8 (see section 1.9).
- **Features**: the primary metric plus the secondary features of plan §1.6. These are stored DesigniteJava loc, plus computed statements, max nesting, comment ratio and method calls.
- **Models**:
  - `StandardScaler` + `LogisticRegression(class_weight='balanced', max_iter=10000)`.
  - `RandomForestClassifier(class_weight='balanced', random_state={SEED})`.
  - All other hyperparameters are scikit-learn 1.5.2 defaults.
- **Transfer setting.**
  - Train on granularity-consistent DACOSX entries for the smell, using the full absent class with inverse-frequency weights and no subsampling (D14).
  - Same-smell DACOS overlaps are removed before training (D4).
  - Test on DACOS unanimous entities from the consistency-filtered set.
- **In-DACOS settings.** `GroupKFold(5)` and leave-one-project-out, grouped by `project_name`. Out-of-fold predictions are pooled before scoring.
- **Scoring.** Predicted class is p ≥ 0.5, and "smelly" is the positive class. ROC-AUC uses the pooled probabilities.
- **CIs.** Bootstrap percentile intervals (B = {B}, resampling DACOS test entities, seed {SEED}). The same resamples are used for every setting, so differences are paired.
- **H4.** Primary test: transfer MCC − GroupKFold(5) MCC, judged by its paired bootstrap CI. The other differences are reported alongside it.
- **Caveat.** DACOSX labels are functions of the same metrics used as features, so near-perfect DACOSX in-distribution scores are expected and are not a finding. They are listed under EXPLORATORY only as a sanity check.

**Data**

{md_table(I)}

**Performance on DACOS unanimous entities**

{md_table(T)}

**Paired differences (transfer minus in-DACOS CV)**

{md_table(Dm)}

Tables: `tables/rq4_data.csv`, `tables/rq4_transfer.csv`, `tables/rq4_paired_differences.csv`, `tables/rq4_predictions.csv.gz`. Figure: `figures/rq4_transfer.pdf` (.png). Runtime {time.time() - t0:.0f}s.

**Summary.** {sent}.
"""
    write_frag("rq4", txt)
    xin_txt = f"""**DACOSX in-distribution performance** (sanity check; not in plan.md).
- Setting: GroupKFold(5) by project within DACOSX, with the same models and features as RQ4.
- These scores are expected to be near-perfect, because DACOSX labels are thresholds on features in the model.

{md_table(XI_md)}

Table: `tables/exploratory_dacosx_in_distribution.csv`.
"""
    write_frag("exploratory_dacosx", xin_txt)
    print(txt)
    print(xin_txt)


if __name__ == "__main__":
    main()
