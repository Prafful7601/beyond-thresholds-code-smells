"""Step 3 shared protocol (plan.md §4.4): splits, models, grids, nested tuning, metrics, bootstrap, cache."""
import os
import pickle
import sys
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import rankdata
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, matthews_corrcoef
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402

warnings.filterwarnings("ignore")
STEP3_SMELLS = ["CM", "LPL"]
MODEL_NAMES = ["LR", "RF", "XGB", "GB", "SVM"]
TREE_MODELS = ["RF", "XGB", "GB"]
N_REPEATS, N_FOLDS = 5, 5
N_JOBS = max(1, (os.cpu_count() or 2) - 1)
CACHE = os.path.join(ROOT, "data/cache")
os.makedirs(CACHE, exist_ok=True)
RATIONALE = {
    "LR": "linear, interpretable baseline; the same family as Tier 1 RQ4",
    "RF": "bagged trees; captures thresholds and interactions with little tuning; Tier 1 comparison model",
    "XGB": "regularised gradient boosting; a strong default for small tabular data",
    "GB": "scikit-learn gradient boosting; a boosting check that does not depend on the XGBoost implementation",
    "SVM": "RBF-kernel margin classifier; smooth non-linear boundaries, unlike tree splits",
}
GRIDS = {
    "LR": {"clf__C": [0.01, 0.1, 1, 10]},
    "RF": {"max_depth": [None, 5, 10], "min_samples_leaf": [1, 5, 20]},
    "XGB": {"n_estimators": [100, 300], "max_depth": [2, 4, 6], "learning_rate": [0.05, 0.1]},
    "GB": {"n_estimators": [100, 300], "max_depth": [2, 3], "learning_rate": [0.05, 0.1]},
    "SVM": {"clf__C": [0.1, 1, 10], "clf__gamma": ["scale", 0.01, 0.1]},
}
MCC_SCORER = make_scorer(matthews_corrcoef)


# ---------------------------------------------------------------- data
def dacos_entities(smell, variant="primary"):
    """All entities of the variant (unanimous, split, ties) with complete Step 3 features."""
    L = annotation_long()
    E = attach_metrics(variant_entities(L, variant))
    E = E[E.smell == smell].dropna(subset=full_features(smell)).reset_index(drop=True)
    return E


def unanimous(E):
    return E[E.unanimous].reset_index(drop=True)


def dacosx_entities(smell):
    from rq4 import dacosx_frame
    L = annotation_long()
    X, info = dacosx_frame(smell, L)
    feats = full_features(smell)
    n0 = len(X)
    X = X.dropna(subset=feats).reset_index(drop=True)
    info["missing_step3_features"] = n0 - len(X)
    return X, info


def project_splits(projects):
    """25 splits: repeat r shuffles projects with seed SEED + r and assigns them round-robin to 5 folds."""
    projs = sorted(set(projects))
    out = []
    for r in range(N_REPEATS):
        perm = list(np.random.default_rng(SEED + r).permutation(projs))
        fold_of = {p: i % N_FOLDS for i, p in enumerate(perm)}
        for k in range(N_FOLDS):
            out.append((r, k, frozenset(p for p, f in fold_of.items() if f == k)))
    return out


# ---------------------------------------------------------------- models
def make_model(name, seed, y=None, weighted=True):
    cw = "balanced" if weighted else None
    if name == "LR":
        return Pipeline([("sc", StandardScaler()), ("clf", LogisticRegression(class_weight=cw, max_iter=10000))])
    if name == "RF":
        return RandomForestClassifier(n_estimators=300, class_weight=cw, random_state=seed)
    if name == "XGB":
        spw = float((y == 0).sum() / max((y == 1).sum(), 1)) if (weighted and y is not None) else 1.0
        return XGBClassifier(scale_pos_weight=spw, n_jobs=1, random_state=seed, eval_metric="logloss", verbosity=0)
    if name == "GB":
        return GradientBoostingClassifier(random_state=seed)
    if name == "SVM":
        return Pipeline([("sc", StandardScaler()), ("clf", SVC(kernel="rbf", class_weight=cw))])
    raise ValueError(name)


def fit_kwargs(name, y, weighted=True, extra_w=None):
    """Sample weights: GB carries the class weights here; extra_w (soft labels) applies to every model."""
    w = None
    if name == "GB" and weighted:
        w = compute_sample_weight("balanced", y)
    if extra_w is not None:
        w = extra_w if w is None else w * extra_w
    if w is None:
        return {}
    key = "clf__sample_weight" if name in ("LR", "SVM") else "sample_weight"
    return {key: w}


def tune(name, X, y, groups, seed, weighted=True, extra_w=None):
    """Nested inner GridSearchCV (GroupKFold(3) by project, MCC). Returns best params."""
    gs = GridSearchCV(make_model(name, seed, y, weighted), GRIDS[name], scoring=MCC_SCORER,
                      cv=GroupKFold(3), n_jobs=1, refit=False, error_score=np.nan)
    gs.fit(X, y, groups=groups, **fit_kwargs(name, y, weighted, extra_w))
    return gs.best_params_


def fit(name, params, X, y, seed, weighted=True, extra_w=None):
    m = make_model(name, seed, y, weighted).set_params(**params)
    m.fit(X, y, **fit_kwargs(name, y, weighted, extra_w))
    return m


def score(m, name, X):
    if name == "SVM":
        s = m.decision_function(X)
        return s, s >= 0
    s = m.predict_proba(X)[:, 1]
    return s, s >= 0.5


# ---------------------------------------------------------------- fast metrics (verified against sklearn)
def _counts(y, p):
    tp = np.sum(p & (y == 1))
    tn = np.sum(~p & (y == 0))
    fp = np.sum(p & (y == 0))
    fn = np.sum(~p & (y == 1))
    return tp, tn, fp, fn


def macro_f1(y, p):
    tp, tn, fp, fn = _counts(y, p)
    f_pos = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    f_neg = 2 * tn / (2 * tn + fn + fp) if (2 * tn + fn + fp) else 0.0
    return (f_pos + f_neg) / 2


def mcc(y, p):
    tp, tn, fp, fn = _counts(y, p)
    den = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / den if den > 0 else 0.0


def roc_auc(y, s):
    npos = int(y.sum())
    nneg = len(y) - npos
    if npos == 0 or nneg == 0:
        return np.nan
    r = rankdata(s)
    return (r[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)


def pr_auc(y, s):
    """Average precision, step-wise over distinct thresholds (sklearn definition)."""
    npos = int(y.sum())
    if npos == 0:
        return np.nan
    order = np.argsort(-s, kind="mergesort")
    s_, y_ = s[order], y[order]
    last = np.r_[np.where(np.diff(s_) != 0)[0], len(s_) - 1]
    tp = np.cumsum(y_)[last]
    fp = (last + 1) - tp
    prec = tp / (tp + fp)
    rec = tp / npos
    return float(np.sum(np.diff(np.r_[0, rec]) * prec))


METRICS = {"macro_F1": lambda y, s, p: macro_f1(y, p), "MCC": lambda y, s, p: mcc(y, p),
           "ROC_AUC": lambda y, s, p: roc_auc(y, s), "PR_AUC": lambda y, s, p: pr_auc(y, s)}


def all_metrics(y, s, p):
    return {k: f(y, s, p) for k, f in METRICS.items()}


# ---------------------------------------------------------------- run the protocol
def oof_job(name, D, test_projects, r, k, feats, params=None, weighted=True, train_extra=None, train_override=None):
    """One outer fold. D = unanimous test-universe table. Returns (r, k, test_index, scores, preds, params)."""
    te = D.project.isin(test_projects).values
    if train_override is not None:
        T = train_override(test_projects)          # custom training table with columns feats, target, project, [w]
    else:
        T = D[~te]
    Xtr, ytr, gtr = T[feats].values, T.target.values.astype(int), T.project.values
    extra = T["w"].values if (train_extra and "w" in T) else None
    seed = SEED + r
    if params is None:
        params = tune(name, Xtr, ytr, gtr, seed, weighted, extra)
    m = fit(name, params, Xtr, ytr, seed, weighted, extra)
    s, p = score(m, name, D[te][feats].values)
    return r, k, np.where(te)[0], s, p, params


def run_protocol(name, D, feats, splits, params_by_fold=None, weighted=True, train_extra=False, train_override=None,
                 n_jobs=N_JOBS):
    """Pooled OOF predictions per repeat. Returns dict with scores/preds (R x n), fold MCC, params."""
    jobs = Parallel(n_jobs=n_jobs)(
        delayed(oof_job)(name, D, tp, r, k, feats,
                         None if params_by_fold is None else params_by_fold[(r, k)],
                         weighted, train_extra, train_override)
        for r, k, tp in splits)
    n = len(D)
    S = np.full((N_REPEATS, n), np.nan)
    P = np.zeros((N_REPEATS, n), bool)
    fold_mcc, params = {}, {}
    y = D.target.values.astype(int)
    for r, k, idx, s, p, prm in jobs:
        S[r, idx], P[r, idx] = s, p
        fold_mcc[(r, k)] = mcc(y[idx], p)
        params[(r, k)] = prm
    assert not np.isnan(S).any()
    return {"S": S, "P": P, "y": y, "fold_mcc": fold_mcc, "params": params, "entity": D.entity.values}


def summarise(res, b=B):
    """Mean +- SD over repeats of pooled-OOF metrics, and bootstrap CI of the repeat-mean."""
    y, S, P = res["y"], res["S"], res["P"]
    per = {k: [METRICS[k](y, S[r], P[r]) for r in range(N_REPEATS)] for k in METRICS}
    out = {}
    for k, v in per.items():
        out[k] = float(np.mean(v))
        out[f"{k}_sd"] = float(np.std(v, ddof=1))
    bs = boot_repeat_mean(res, b)
    for k in METRICS:
        out[f"{k}_lo"], out[f"{k}_hi"] = boot_ci(bs[k])
    return out


def boot_indices(n, b=B):
    r_ = rng()
    return [r_.integers(0, n, n) for _ in range(b)]


def boot_repeat_mean(res, b=B, idxs=None, keys=None):
    y, S, P = res["y"], res["S"], res["P"]
    idxs = idxs if idxs is not None else boot_indices(len(y), b)
    keys = list(METRICS) if keys is None else list(keys)
    out = {k: np.empty(len(idxs)) for k in keys}
    for j, i in enumerate(idxs):
        for k in keys:
            f = METRICS[k]
            out[k][j] = np.mean([f(y[i], S[r][i], P[r][i]) for r in range(N_REPEATS)])
    return out


def paired_delta(res_a, res_b, metrics=("macro_F1", "MCC"), b=B):
    """Repeat-mean metric difference a - b on the same entities, with paired bootstrap CI."""
    assert (res_a["entity"] == res_b["entity"]).all()
    idxs = boot_indices(len(res_a["y"]), b)
    ba, bb = boot_repeat_mean(res_a, b, idxs, metrics), boot_repeat_mean(res_b, b, idxs, metrics)
    sa, sb = summarise_point(res_a), summarise_point(res_b)
    out = {}
    for k in metrics:
        d = ba[k] - bb[k]
        out[k] = sa[k] - sb[k]
        out[f"{k}_lo"], out[f"{k}_hi"] = boot_ci(d)
        out[f"{k}_share_ge0"] = float(np.mean(d >= 0))
    return out


def summarise_point(res):
    y, S, P = res["y"], res["S"], res["P"]
    return {k: float(np.mean([METRICS[k](y, S[r], P[r]) for r in range(N_REPEATS)])) for k in METRICS}


def save(obj, name):
    with open(os.path.join(CACHE, name + ".pkl"), "wb") as f:
        pickle.dump(obj, f)


def load(name):
    with open(os.path.join(CACHE, name + ".pkl"), "rb") as f:
        return pickle.load(f)


def metric_cell(d, k, digits=3):
    return f"{d[k]:.{digits}f} ± {d[k + '_sd']:.{digits}f} [{d[k + '_lo']:.{digits}f}, {d[k + '_hi']:.{digits}f}]"


def best_model(results):
    """results: {name: summary}. Highest mean MCC; ties -> order of MODEL_NAMES (simpler first)."""
    return max(MODEL_NAMES, key=lambda m: (round(results[m]["MCC"], 12), -MODEL_NAMES.index(m)))
