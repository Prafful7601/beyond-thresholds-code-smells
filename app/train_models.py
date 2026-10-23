"""Train the CodeSniff models and write their model cards (offline; needs the DACOS data and the paper's caches).

Run once from the repository root, with the analysis environment:
    DYLD_LIBRARY_PATH=.venv/lib/python3.9/site-packages/sklearn/.dylibs .venv/bin/python -I app/train_models.py

Models follow the paper (results.md §5.2, §4.4):
* CM: logistic regression, the paper's best CM model, on primary-set unanimous entities.
* LPL: SVM (RBF), the best LPL model without the pc = 3 block (R5), on R5 unanimous entities.
Hyperparameters: the parameter set selected most often across the paper's 25 outer folds (section B caches).
Features: computed by CodeSniff's own extraction (lizard-based cc/pc/loc + the paper's compute()), so training
and serving use identical definitions. The model card reports both the paper's CV MCC (DesigniteJava features,
read from results/tables) and the app models' CV MCC on the same 25 project-grouped splits.
"""
import collections
import datetime
import json
import os
import subprocess
import sys
import zipfile

import joblib
import numpy as np
import pandas as pd
import sklearn

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, HERE)
from common import ZIP, annotation_long, attach_metrics, load_tables, variant_entities  # noqa: E402
import protocol  # noqa: E402
from codesniff.extract import extract_methods  # noqa: E402

SEED = protocol.SEED
FEATURES = {"CM": ["cc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio", "mean_identifier_length"],
            "LPL": ["pc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio", "mean_identifier_length"]}
SPEC = {"CM": {"variant": "primary", "model": "LR", "cache": "step3_B_CM", "table": "model_comparison.csv",
               "headline": "Best model MCC, CM (LR"},
        "LPL": {"variant": "R5", "model": "SVM", "cache": "step3_B_LPL_R5", "table": "model_comparison_LPL_R5.csv",
                "headline": "Best model MCC, LPL R5 (SVM"}}
OUT = os.path.join(HERE, "models")
os.makedirs(OUT, exist_ok=True)


def pick_method(methods, name, stored_pc, stored_cc):
    """The extracted method that corresponds to the DesigniteJava entity (training-label alignment)."""
    same = [m for m in methods if m.name == name] or methods
    exact = [m for m in same if m.pc == stored_pc] or same
    exact2 = [m for m in exact if m.cc == stored_cc] or exact
    return max(exact2, key=lambda m: m.loc)


def training_table(smell, z, mm):
    L = annotation_long()
    E = attach_metrics(variant_entities(L, SPEC[smell]["variant"]))
    E = E[(E.smell == smell) & E.unanimous].reset_index(drop=True)
    names = dict(zip(mm.id, mm.method_name))
    rows = []
    for r in E.itertuples():
        src = z.read(r.path.lstrip("/")).decode("utf-8", "replace")
        ms = extract_methods(src)
        m = pick_method(ms, names.get(r.designite_id), r.pc, r.cc)
        rows.append({"entity": r.entity, "project": r.project, "target": int(r.target), "designite_cc": r.cc,
                     "designite_pc": r.pc, "designite_loc": r.loc, **{k: getattr(m, k) for k in
                     ["cc", "cc_lizard", "pc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio",
                      "mean_identifier_length"]}})
    return pd.DataFrame(rows)


def mode_params(cache, model):
    plist = [json.dumps(p, sort_keys=True) for p in cache["res"][model]["params"].values()]
    counts = collections.Counter(plist)
    best, n = counts.most_common(1)[0]
    return json.loads(best), {k: v for k, v in counts.items()}, n


def lizard_agreement(z, mm, smp, ann):
    """200 random annotated DACOS method snippets: CodeSniff cc/pc versus stored DesigniteJava values."""
    annotated = smp[smp.id.isin(ann.sample_id) & (smp.is_class == 0)].merge(
        mm[["id", "cc", "pc", "method_name"]], left_on="designite_id", right_on="id", suffixes=("", "_m"))
    names = set(z.namelist())
    annotated = annotated[annotated.path_to_file.str.lstrip("/").isin(names)].reset_index(drop=True)
    pick = np.random.default_rng(SEED).choice(len(annotated), 200, replace=False)
    rows = []
    for i in sorted(pick):
        r = annotated.iloc[i]
        ms = extract_methods(z.read(r.path_to_file.lstrip("/")).decode("utf-8", "replace"))
        same = [m for m in ms if m.name == r.method_name] or ms
        m = max(same, key=lambda m: m.loc)     # name-based alignment only; stored values are not used to pick
        rows.append({"sample_id": int(r.id), "designite_cc": int(r.cc), "lizard_cc_raw": m.cc_lizard,
                     "codesniff_cc": m.cc, "designite_pc": int(r.pc), "codesniff_pc": m.pc,
                     "methods_in_file": len(ms), "has_body": m.has_body})
    R = pd.DataFrame(rows)
    return {"n": len(R), "seed": SEED, "selection": "random 200 annotated DACOS method snippets (files present)",
            "alignment": "extracted method with the DesigniteJava method name (largest NLOC among overloads)",
            "cc_exact_raw_lizard": float((R.lizard_cc_raw == R.designite_cc).mean()),
            "cc_exact_codesniff": float((R.codesniff_cc == R.designite_cc).mean()),
            "cc_within_1_codesniff": float(((R.codesniff_cc - R.designite_cc).abs() <= 1).mean()),
            "pc_exact_codesniff": float((R.codesniff_pc == R.designite_pc).mean()),
            "paper_crosscheck_for_reference": "results.md §1.8: raw lizard cc 0.592 exact, pc 0.957 exact (n = 3,491)",
            "rows": rows}


def main():
    z = zipfile.ZipFile(ZIP)
    ann, smp, mm, cm, ent = load_tables()
    commit = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], text=True).strip()
    agreement = lizard_agreement(z, mm, smp, ann)
    with open(os.path.join(OUT, "lizard_agreement.json"), "w") as f:
        json.dump(agreement, f, indent=2)
    print("lizard agreement:", {k: v for k, v in agreement.items() if k != "rows"})
    cards = {}
    for smell, spec in SPEC.items():
        T = training_table(smell, z, mm)
        cache = protocol.load(spec["cache"])
        params, counts, n_mode = mode_params(cache, spec["model"])
        feats = FEATURES[smell]
        X, y = T[feats].values.astype(float), T.target.values.astype(int)
        # CV of the app-feature model on the paper's 25 splits with the fixed parameters
        D = T.rename(columns={})
        splits = protocol.project_splits(D.project)
        res = protocol.run_protocol(spec["model"], D, feats, splits, params_by_fold={(r, k): params for r, k, _ in splits})
        s = protocol.summarise(res)
        # final model on all unanimous entities
        model = protocol.fit(spec["model"], params, X, y, SEED)
        if spec["model"] == "SVM":   # probabilities for display via Platt scaling (decision sign = paper's class rule)
            model.set_params(clf__probability=True, clf__random_state=SEED)
            model.fit(X, y)
        fname = f"{smell.lower()}_{spec['model'].lower()}.joblib"
        joblib.dump(model, os.path.join(OUT, fname))
        paper = pd.read_csv(os.path.join(REPO, "results/tables", spec["table"]))
        paper = paper[(paper.model == spec["model"]) & ((paper.smell == smell) if "smell" in paper else True)].iloc[0]
        cards[smell] = {
            "smell": smell, "model": spec["model"], "file": fname, "features": feats,
            "hyperparameters": params, "hyperparameter_rule": f"most frequent selection across the paper's 25 outer folds ({n_mode}/25)",
            "hyperparameter_selection_counts": counts,
            "class_weighting": "inverse-frequency (balanced), as in the paper",
            "probability": ("logistic regression predict_proba" if spec["model"] == "LR" else
                            "SVC(probability=True): Platt scaling; the paper's class rule is the decision-function sign"),
            "training_data": {"source": "DACOS (Zenodo 10.5281/zenodo.7570428), primary analysis set",
                              "set": "unanimous entities, consistency-filtered" + ("; R5: pc = 3 block removed" if smell == "LPL" else ""),
                              "n": int(len(T)), "smelly": int(T.target.sum()), "benign": int((1 - T.target).sum()),
                              "projects": int(T.project.nunique())},
            "feature_definitions": "CodeSniff extraction (app/codesniff/extract.py): lizard-based cc (DesigniteJava-compatible), "
                                   "declaration pc, lizard NLOC; paper's compute() for the other features",
            "paper_cv": {"source": f"results/tables/{spec['table']} (DesigniteJava features)",
                         "MCC": float(paper.MCC), "MCC_sd": float(paper.MCC_sd), "MCC_lo": float(paper.MCC_lo),
                         "MCC_hi": float(paper.MCC_hi), "macro_F1": float(paper.macro_F1), "ROC_AUC": float(paper.ROC_AUC)},
            "app_cv": {"protocol": "the paper's 25 project-grouped splits (5 repeats x 5 folds), fixed hyperparameters",
                       "caveat": ("hyperparameters are the modal choice of the paper's nested tuning over these same folds, "
                                  "so this estimate is slightly optimistic; the paper's nested-CV value (paper_cv) is the one "
                                  "CodeSniff quotes"),
                       **{k: float(v) for k, v in s.items()}},
            "feature_agreement_with_designite": {
                "cc_exact": float((T["cc"] == T["designite_cc"]).mean()), "pc_exact": float((T["pc"] == T["designite_pc"]).mean()),
                "loc_exact": float((T["loc"] == T["designite_loc"]).mean()),
                "note": ("upper bounds: the alignment picks, among overloads in a snippet file, the method matching the stored pc "
                         "(then cc); the unbiased rates are in lizard_agreement.json")},
            "versions": {"scikit-learn": sklearn.__version__, "joblib": joblib.__version__, "python": sys.version.split()[0]},
            "trained_at": datetime.datetime.now().strftime("%Y-%m-%d"), "repository_commit": commit,
            "intended_use": "rank borderline methods for human review; not a verdict",
        }
        print(smell, spec["model"], params, "app CV MCC", round(s["MCC"], 3), "paper CV MCC", round(float(paper.MCC), 3))
    with open(os.path.join(OUT, "model_card.json"), "w") as f:
        json.dump(cards, f, indent=2)
    with open(os.path.join(OUT, "MODEL_CARD.md"), "w") as f:
        f.write(render_card(cards, agreement))


def render_card(cards, agreement):
    out = ["# CodeSniff model cards", "",
           "Generated by `app/train_models.py` from the values in `model_card.json`; do not edit by hand.", ""]
    for smell, c in cards.items():
        pc, ac, td = c["paper_cv"], c["app_cv"], c["training_data"]
        out += [f"## {smell}: {c['model']} (`{c['file']}`)", "",
                f"- Intended use: {c['intended_use']}.",
                f"- Training data: {td['source']}; {td['set']}; n = {td['n']} ({td['smelly']} smelly, {td['benign']} benign), "
                f"{td['projects']} projects.",
                f"- Features (in order): {', '.join(c['features'])}. {c['feature_definitions']}.",
                f"- Hyperparameters: `{c['hyperparameters']}` ({c['hyperparameter_rule']}). Class weighting: {c['class_weighting']}.",
                f"- Probability: {c['probability']}.",
                f"- **Paper CV MCC** (nested 5x5 project-grouped CV, DesigniteJava features): {pc['MCC']:.3f} "
                f"± {pc['MCC_sd']:.3f} [95% CI {pc['MCC_lo']:.3f}, {pc['MCC_hi']:.3f}]; macro-F1 {pc['macro_F1']:.3f}; "
                f"ROC-AUC {pc['ROC_AUC']:.3f}. Source: {pc['source']}.",
                f"- App-feature CV MCC (same 25 splits, fixed hyperparameters): {ac['MCC']:.3f} ± {ac['MCC_sd']:.3f} "
                f"[{ac['MCC_lo']:.3f}, {ac['MCC_hi']:.3f}]. Caveat: {ac['caveat']}.",
                f"- Feature agreement with DesigniteJava on the training set: cc exact {c['feature_agreement_with_designite']['cc_exact']:.3f}, "
                f"pc exact {c['feature_agreement_with_designite']['pc_exact']:.3f}, loc exact {c['feature_agreement_with_designite']['loc_exact']:.3f} "
                f"({c['feature_agreement_with_designite']['note']}).",
                f"- Trained {c['trained_at']} at repository commit `{c['repository_commit']}`; scikit-learn "
                f"{c['versions']['scikit-learn']}, joblib {c['versions']['joblib']}, Python {c['versions']['python']}.", ""]
    a = agreement
    out += ["## Metric agreement check (200 random annotated DACOS method snippets)", "",
            f"- cc exact: raw lizard {a['cc_exact_raw_lizard']:.3f}; CodeSniff (DesigniteJava-compatible) {a['cc_exact_codesniff']:.3f}; "
            f"CodeSniff within ±1 {a['cc_within_1_codesniff']:.3f}.",
            f"- pc exact: CodeSniff {a['pc_exact_codesniff']:.3f}.",
            f"- Alignment: {a['alignment']}. Reference: {a['paper_crosscheck_for_reference']}.",
            "- The remaining cc differences come from how the tools count `case`, `catch` and nested lambdas or anonymous classes. "
            "The zones therefore use an approximation of the paper's metric, not the paper's metric itself.", ""]
    return "\n".join(out)


if __name__ == "__main__":
    main()
