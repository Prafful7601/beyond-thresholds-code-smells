"""Step 3 C: ablation study (plan.md §4.5 C). Best model from B and LR, per smell (CM, LPL). Primary analysis.

Hyperparameters are reused from the full model's inner tuning in each outer fold (not re-tuned).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import *  # noqa: F401,F403,E402

C1_ORDER = ["(i) primary only", "(ii) size only", "(iii) structure only", "(iv) readability only", "(v) all features",
            "(vi) all − primary", "(vi) all − size", "(vi) all − structure", "(vi) all − readability"]


def c1_sets(smell):
    full = full_features(smell)
    out = {"(i) primary only": group_features(smell, "primary"), "(ii) size only": group_features(smell, "size"),
           "(iii) structure only": group_features(smell, "structure"),
           "(iv) readability only": group_features(smell, "readability"), "(v) all features": full}
    for g in ("primary", "size", "structure", "readability"):
        drop = set(group_features(smell, g))
        out[f"(vi) all − {g}"] = [f for f in full if f not in drop]
    return out


def main():
    t0 = time.time()
    best = load("step3_best")
    plt = plot_style()
    for smell in STEP3_SMELLS:
        cache = load(f"step3_B_{smell}")
        splits, resB = cache["splits"], cache["res"]
        Eall = dacos_entities(smell)
        D = unanimous(Eall)
        assert (D.entity.values == cache["entities"]).all()
        feats = full_features(smell)
        models = [best[smell]] + ([] if best[smell] == "LR" else ["LR"])
        X, xinfo = dacosx_entities(smell)
        # C2 training tables (all labelled entities of the training projects)
        L = annotation_long()
        Eties = attach_metrics(variant_entities(L, "R2"))
        Eties = Eties[Eties.smell == smell].dropna(subset=feats)
        rows = []
        for m in models:
            pb = resB[m]["params"]
            full = resB[m]
            variants = {}
            for name, fs in c1_sets(smell).items():
                if name == "(v) all features":
                    variants[("C1 feature groups", name)] = full
                else:
                    variants[("C1 feature groups", name)] = run_protocol(m, D, fs, splits, pb)
            # C2 label aggregation
            variants[("C2 label aggregation", "unanimous only (= v)")] = full

            def ties_train(tp, E=Eties):
                return E[~E.project.isin(tp)][feats + ["target", "project"]]

            def soft_train(tp, E=Eall):
                T = E[~E.project.isin(tp)]
                pos = T.assign(target=1, w=T.y / T.n)
                neg = T.assign(target=0, w=1 - T.y / T.n)
                S = pd.concat([pos, neg])
                return S[S.w > 0][feats + ["target", "project", "w"]]
            variants[("C2 label aggregation", "ties counted as smelly")] = run_protocol(m, D, feats, splits, pb,
                                                                                    train_override=ties_train)
            variants[("C2 label aggregation", "soft labels (y/n) as sample weights")] = run_protocol(
                m, D, feats, splits, pb, train_extra=True, train_override=soft_train)
            # C3 training source (DACOSX restricted to the training projects of each fold)

            def x_only(tp, X=X):
                return X[~X.project.isin(tp)][feats + ["target", "project"]]

            def x_plus_d(tp, X=X, D=D):
                return pd.concat([X[~X.project.isin(tp)][feats + ["target", "project"]],
                                  D[~D.project.isin(tp)][feats + ["target", "project"]]])
            variants[("C3 training source", "DACOS only (= v)")] = full
            variants[("C3 training source", "DACOSX only")] = run_protocol(m, D, feats, splits, pb, train_override=x_only)
            variants[("C3 training source", "DACOSX + DACOS")] = run_protocol(m, D, feats, splits, pb, train_override=x_plus_d)
            fs_np = [f for f in feats if f != PRIMARY[smell]]

            def x_only_np(tp, X=X):
                return X[~X.project.isin(tp)][fs_np + ["target", "project"]]
            variants[("C3 training source", "DACOSX only, primary metric removed")] = run_protocol(
                m, D, fs_np, splits, pb, train_override=x_only_np)
            # C4 class weighting
            variants[("C4 class weighting", "weights on (= v)")] = full
            variants[("C4 class weighting", "weights off")] = run_protocol(m, D, feats, splits, pb, weighted=False)
            print(smell, m, f"{time.time() - t0:.0f}s", flush=True)
            for (block, name), res in variants.items():
                s = summarise(res)
                is_full = res is full
                d = paired_delta(res, full) if not is_full else {}
                rows.append({"smell": smell, "model": m, "block": block, "variant": name, **s,
                             "d_macro_F1": d.get("macro_F1", 0.0), "d_macro_F1_lo": d.get("macro_F1_lo", np.nan),
                             "d_macro_F1_hi": d.get("macro_F1_hi", np.nan), "d_MCC": d.get("MCC", 0.0),
                             "d_MCC_lo": d.get("MCC_lo", np.nan), "d_MCC_hi": d.get("MCC_hi", np.nan),
                             "is_reference": is_full})
        A = pd.DataFrame(rows)
        A["analysis"] = "primary"
        A.to_csv(os.path.join(TAB, f"ablation_{smell}.csv"), index=False)
        save({"rows": A, "xinfo": xinfo}, f"step3_C_{smell}")

        # figure: delta MCC per variant (non-reference) per model
        V = A[~A.is_reference]
        labels = list(dict.fromkeys(f"{b.split(' ')[0]} {v}" for b, v in zip(V.block, V.variant)))
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 0.22 * len(labels) + 0.9), sharey=True)
        cols = [COL["blue"], COL["orange"]]
        for ax, met in zip(axes, ("d_MCC", "d_macro_F1")):
            for j, m in enumerate(models):
                x = V[V.model == m]
                ys = np.array([labels.index(f"{b.split(' ')[0]} {v}") for b, v in zip(x.block, x.variant)]) + (j - 0.5 * (len(models) - 1)) * 0.3
                ax.errorbar(x[met], ys, xerr=[x[met] - x[met + "_lo"], x[met + "_hi"] - x[met]], fmt="o", ms=3,
                            color=cols[j], lw=1, capsize=0, label=m)
            ax.axvline(0, color=COL["ink2"], lw=0.6, ls=":")
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=5.8)
            if ax is axes[0]:
                ax.invert_yaxis()  # shared y-axis: invert once
            ax.set_xlabel(("Δ MCC" if met == "d_MCC" else "Δ macro-F1") + " vs (v) all features")
            ax.grid(axis="y", visible=False)
        axes[0].legend(loc="lower left", fontsize=6)
        axes[0].set_title(f"{SMELL_NAME[smell]}: ablation (paired bootstrap 95% CI)", loc="left")
        fig.tight_layout()
        savefig(fig, f"ablation_{smell}")

    # markdown
    parts = []
    for smell in STEP3_SMELLS:
        A = pd.read_csv(os.path.join(TAB, f"ablation_{smell}.csv"))
        T = A.copy()
        T["macro-F1 mean ± SD [95% CI]"] = [metric_cell(r, "macro_F1") for r in T.to_dict("records")]
        T["MCC mean ± SD [95% CI]"] = [metric_cell(r, "MCC") for r in T.to_dict("records")]
        T["Δ macro-F1 [95% CI]"] = ["reference" if r["is_reference"] else fmt_ci(r["d_macro_F1"], r["d_macro_F1_lo"], r["d_macro_F1_hi"])
                                    for r in T.to_dict("records")]
        T["Δ MCC [95% CI]"] = ["reference" if r["is_reference"] else fmt_ci(r["d_MCC"], r["d_MCC_lo"], r["d_MCC_hi"])
                               for r in T.to_dict("records")]
        T = T[["model", "block", "variant", "macro-F1 mean ± SD [95% CI]", "MCC mean ± SD [95% CI]", "Δ macro-F1 [95% CI]",
               "Δ MCC [95% CI]"]]
        xinfo = load(f"step3_C_{smell}")["xinfo"]
        parts.append(f"**{SMELL_NAME[smell]}** (table `tables/ablation_{smell}.csv`, figure `figures/ablation_{smell}.pdf`)\n\n"
                     f"DACOSX training pool (D4-cleaned, features complete): {xinfo}\n\n{md_table(T)}\n")
    best_txt = "; ".join(f"{s}: {best[s]}" for s in STEP3_SMELLS)
    txt = f"""**Analysis type: primary.** Models: the best model from B and LR ({best_txt}).
Because LR is CM's best model, CM's ablation has a single model.

**Method.**
- The protocol and 25 splits are those of section B.
- Each variant **reuses the hyperparameters selected for the full model** in that outer fold; nothing is re-tuned (plan.md §4.5 C).
- Test set: always the held-out unanimous DACOS entities of the fold.
- Δ is the variant minus (v) all features, as a repeat-mean over 5 repeats. The 95% CI is a paired bootstrap over test entities (B = {B}).
- C1 feature groups:
  - primary = {{cc | pc}}
  - size = {{loc, statements}}
  - structure = {{max_nesting, method_calls}}
  - readability = {{comment_ratio, mean_identifier_length}}. Mean identifier length was computed with the existing lexer, so it is included.
- C2 training labels (test labels unchanged):
  - "ties counted as smelly" trains on unanimous entities plus ties labelled smelly. The rare non-unanimous majority entities keep their majority label.
  - "soft labels" enter each entity twice, once per class, with sample weights y/n and 1 − y/n multiplied by the class weights.
- C3 training source. DACOSX is the D4-cleaned set, with entries from the fold's held-out projects excluded so that no project is in both train and test (this restriction is a clarification of the plan). Class weights are recomputed on each training set.
- C4: class weighting switched off (no `class_weight`, `scale_pos_weight` = 1, no GB sample weights).

{chr(10).join(parts)}
Runtime {time.time() - t0:.0f}s.
"""
    write_frag("step3_C", txt)
    print(txt)


if __name__ == "__main__":
    main()
