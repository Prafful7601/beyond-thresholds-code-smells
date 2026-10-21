"""Robustness checks (plan.md §4.1): headline numbers under primary / R1-R7c.

Writes tables/robustness_long.csv (numeric) and tables/robustness_summary.csv (one row per headline number
per smell, one column per check). RQ3 and RQ5 rows are added when src/rq3.py and src/rq5.py provide
`headline(L, variant, smell)`.
"""
import importlib
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402
import rq2  # noqa: E402
from rq4 import MODELS, dacosx_frame, metrics  # noqa: E402

CHECK_COLS = ["primary", "R3", "R4", "R5", "R6", "R7c", "R1", "R2"]


def alpha_ci(E):
    n, y = E.n.values, E.y.values
    est = alpha_binary(n, y)
    r = rng()
    bs = [alpha_binary(n[i], y[i]) for i in (r.integers(0, len(n), len(n)) for _ in range(B))]
    lo, hi = boot_ci(bs)
    return est, lo, hi


def labelled(E, variant):
    if variant == "R2":
        return E[E.unanimous | (E.label == "tie")]
    return E[E.unanimous]


_X_CACHE = {}


def rq4_mcc_diff(smell, D, L):
    """Transfer MCC - GroupKFold(5) MCC, paired bootstrap; same procedure as src/rq4.py."""
    feats = feature_cols(smell)
    if smell not in _X_CACHE:
        X, _ = dacosx_frame(smell, L)
        _X_CACHE[smell] = {m: clone(model).fit(X[feats].values, X.target.values) for m, model in MODELS.items()}
    D = D.dropna(subset=feats).reset_index(drop=True)
    y = D.target.values.astype(int)
    r_ = rng()
    idxs = [r_.integers(0, len(y), len(y)) for _ in range(B)]
    out = {}
    for mname, model in MODELS.items():
        pt = _X_CACHE[smell][mname].predict_proba(D[feats].values)[:, 1]
        oof = np.full(len(D), np.nan)
        for tr, te in GroupKFold(5).split(D[feats], y, groups=D.project):
            m = clone(model).fit(D[feats].values[tr], y[tr])
            oof[te] = m.predict_proba(D[feats].values[te])[:, 1]
        est = metrics(y, pt)[1] - metrics(y, oof)[1]
        d = [metrics(y[i], pt[i])[1] - metrics(y[i], oof[i])[1] for i in idxs]
        lo, hi = boot_ci(d)
        out[mname] = (est, lo, hi, len(y))
    return out


def optional_headlines():
    mods = []
    for name in ("rq3", "rq5"):
        try:
            mods.append(importlib.import_module(name))
        except ImportError:
            pass
    return mods


def main():
    t0 = time.time()
    L = annotation_long()
    rows = []
    extra = optional_headlines()
    for variant in ["primary", "R1", "R2", "R3", "R4", "R5", "R6", "R7c"]:
        Ev = attach_metrics(variant_entities(L, variant))
        for smell in SMELLS:
            E = Ev[Ev.smell == smell]
            base = {"check": variant, "smell": smell}
            if variant_applies(variant, smell, "alpha") and variant != "R2":
                est, lo, hi = alpha_ci(E)
                rows.append({**base, "headline": "RQ1 Krippendorff alpha", "estimate": est, "lo": lo, "hi": hi, "n": len(E)})
            El = labelled(E, variant)
            if variant_applies(variant, smell, "auc"):
                o, _, e = rq2.analyse(El, smell, variant)
                if "auc" in o:
                    rows.append({**base, "headline": "RQ2 ROC-AUC (primary metric)", "estimate": o["auc"],
                                 "lo": o["auc_lo"], "hi": o["auc_hi"], "n": o["n"],
                                 "note": f"{o['n_smelly']} smelly / {o['n_benign']} benign"})
                    rows.append({**base, "headline": "RQ2 Youden cut-off", "estimate": o["youden_cut"],
                                 "lo": o["youden_cut_lo"], "hi": o["youden_cut_hi"], "n": o["n"]})
                else:
                    rows.append({**base, "headline": "RQ2 ROC-AUC (primary metric)", "estimate": np.nan, "n": o["n"],
                                 "note": "single class; not computable"})
            if variant_applies(variant, smell, "rq4"):
                res = rq4_mcc_diff(smell, El, L)
                for mname, (est, lo, hi, n) in res.items():
                    rows.append({**base, "headline": f"RQ4 MCC transfer − GroupKFold ({mname})", "estimate": est,
                                 "lo": lo, "hi": hi, "n": n})
            for mod in extra:
                for q in ("rq3", "rq5"):
                    if mod.__name__ == q and variant_applies(variant, smell, q) and variant not in ("R1", "R2", "R7c"):
                        for r in mod.headline(L, variant, smell):
                            rows.append({**base, **r})
        print(variant, f"{time.time() - t0:.0f}s", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(TAB, "robustness_long.csv"), index=False)

    def cell(r):
        if not np.isfinite(r.estimate):
            return f"n/a ({r.get('note', '')})"
        d = 0 if "cut-off" in r.headline and r.smell != "MA" else 3
        ci = f" [{fmt(r.lo, d)}, {fmt(r.hi, d)}]" if np.isfinite(r.lo) else ""
        return f"{fmt(r.estimate, d)}{ci}; n={int(r.n)}"
    R["cell"] = [cell(r) for _, r in R.iterrows()]
    order = list(dict.fromkeys(R.headline))
    W = R.pivot_table(index=["headline", "smell"], columns="check", values="cell", aggfunc="first")
    W = W.reindex(columns=CHECK_COLS).fillna("n/a")
    W = W.reindex(pd.MultiIndex.from_tuples(sorted(W.index, key=lambda t: (order.index(t[0]), SMELLS.index(t[1])))))
    W.index.names = ["headline", "smell"]
    W.to_csv(os.path.join(TAB, "robustness_summary.csv"))
    legend = "\n".join(f"- **{k}**: {v}" for k, v in VARIANT_DESC.items())
    txt = f"""All cells are **robustness** results except the `primary` column, which repeats the primary analysis.
Definitions follow plan.md §4.1:
{legend}

Cell format: estimate [95% bootstrap CI]; n = entities (labelled entities for RQ2/RQ4).
- Youden cut-offs are metric values (rule: metric ≥ cut-off). R1 and R2 are placed as extra columns.
- n/a means the check does not apply to that number (plan.md §4.1), or the number could not be computed. The reason is given in brackets.
- RQ4 rows use the same DACOSX-trained models in every column; only the DACOS test labels change.

{md_table(W, index=True)}

Tables: `tables/robustness_summary.csv` (this table), `tables/robustness_long.csv` (numeric). Runtime {time.time() - t0:.0f}s.
"""
    write_frag("robustness", txt)
    print(txt)


if __name__ == "__main__":
    main()
