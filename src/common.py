"""Shared data loading, label construction, statistics helpers and plot style.

All definitions follow plan.md (Phase 0 commit 1cde513, amendment bd03360).
"""
import os
import sqlite3

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_MAIN = os.path.join(ROOT, "data/db/dacos_main.sqlite")
DB_EXT = os.path.join(ROOT, "data/db/dacos_ext.sqlite")
ZIP = os.path.join(ROOT, "data/raw/files.zip")
FEAT_DIR = os.path.join(ROOT, "data/features")
TAB = os.path.join(ROOT, "results/tables")
FIG = os.path.join(ROOT, "results/figures")
LOG = os.path.join(ROOT, "results/logs")
FRAG = os.path.join(ROOT, "results/fragments")
for d in (TAB, FIG, LOG, FRAG, FEAT_DIR):
    os.makedirs(d, exist_ok=True)

SEED = 20261021
B = 2000
SMELLS = ["CM", "LPL", "MA"]
SMELL_NAME = {"CM": "Complex Method", "LPL": "Long Parameter List", "MA": "Multifaceted Abstraction"}
CHECKBOX = {"CM": "iscm", "LPL": "islp", "MA": "isma"}
PRIMARY = {"CM": "cc", "LPL": "pc", "MA": "lcom"}
DESIGNITE = {"CM": 8, "LPL": 5, "MA": 0.8}          # metric >= threshold (DesigniteJava ThresholdsDTO defaults)
TABLE_I = {"CM": (4, 7), "LPL": (3, 6), "MA": (0.4, 0.8)}  # DACOS paper Table I bands
DACOSX_CODES = {"CM": (3, 6), "LPL": (2, 5), "MA": (1, 4)}  # (present, absent)
METHOD_FEATS = ["loc", "statements", "max_nesting", "comment_ratio", "method_calls"]
CLASS_FEATS = ["loc", "statements", "max_nesting", "comment_ratio", "method_calls", "nom", "nof"]
RUN_MIN = 40


def feature_cols(smell):
    return [PRIMARY[smell]] + (CLASS_FEATS if smell == "MA" else METHOD_FEATS)


def _num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c])
    return df


def load_tables():
    con = sqlite3.connect(DB_MAIN)
    ann = pd.read_sql_query("select * from annotation", con)
    smp = pd.read_sql_query("select * from sample", con)
    mm = _num(pd.read_sql_query("select * from method_metrics", con), ["cc", "loc", "pc"])
    cm = _num(pd.read_sql_query("select * from class_metrics", con),
              ["dit", "fanin", "fanout", "lcom", "loc", "nc", "nof", "nom", "nopf", "nopm", "wmc"])
    ent = pd.read_sql_query("select * from entry", sqlite3.connect(DB_EXT))
    smp["smells"] = smp["smells"].fillna("")
    return ann, smp, mm, cm, ent


def find_runs(values, min_len=RUN_MIN):
    """Boolean mask: element lies in a maximal run of >= min_len identical values."""
    v = np.asarray(values)
    mask = np.zeros(len(v), bool)
    s = 0
    for i in range(1, len(v) + 1):
        if i == len(v) or v[i] != v[s]:
            if i - s >= min_len:
                mask[s:i] = True
            s = i
    return mask


def run_ids(values, min_len=RUN_MIN):
    """Run index (0, 1, ...) for elements in a maximal run of >= min_len identical values, else -1."""
    v = np.asarray(values)
    out = np.full(len(v), -1)
    s, k = 0, 0
    for i in range(1, len(v) + 1):
        if i == len(v) or v[i] != v[s]:
            if i - s >= min_len:
                out[s:i] = k
                k += 1
            s = i
    return out


def annotation_long():
    """One row per (annotation, smell) for every smell the snippet was offered for (plan §1.2, §3)."""
    ann, smp, mm, cm, _ = load_tables()
    a = ann.merge(smp, left_on="sample_id", right_on="id", suffixes=("", "_s"))
    rows = []
    for smell, mask in (("CM", a.smells.str.contains("1")),
                        ("LPL", a.smells.str.contains("2") | ((a.smells == "") & (a.is_class == 0))),
                        ("MA", a.smells == "3")):
        x = a[mask].copy()
        x["smell"] = smell
        x["answer"] = x[CHECKBOX[smell]].astype(int)
        x["pc3_empty"] = (x.smells == "") if smell == "LPL" else False
        rows.append(x)
    L = pd.concat(rows, ignore_index=True)
    L["entity"] = np.where(L.is_class == 1, "C", "M") + L.designite_id.astype(str)
    # D7 internal consistency: checkbox = 1 but is_smell = 0
    L["inconsistent"] = (L.answer == 1) & (L.is_smell == 0)
    # D5/R4 runs on the unfiltered checkbox stream, ordered by annotation id, within smell
    L = L.sort_values(["smell", "id"]).reset_index(drop=True)
    L["in_run"] = False
    L["run_id"] = ""
    for smell in SMELLS:
        m = L.smell == smell
        L.loc[m, "in_run"] = find_runs(L.loc[m, "answer"].values)
        L.loc[m, "run_id"] = [f"{smell}-{k}" if k >= 0 else "" for k in run_ids(L.loc[m, "answer"].values)]
    keep = ["id", "sample_id", "smell", "entity", "designite_id", "is_class", "project_name", "path_to_file",
            "answer", "is_smell", "inconsistent", "in_run", "run_id", "pc3_empty", "smells"]
    return L[keep].rename(columns={"id": "ann_id"})


def entity_labels(L, answer_col="answer", min_ann=2, ties_as=None):
    """Per (smell, entity) vote counts and labels (plan §1.4, D7a). L must already be filtered."""
    g = L.groupby(["smell", "entity"]).agg(n=(answer_col, "size"), y=(answer_col, "sum"),
                                         project=("project_name", "first"), path=("path_to_file", "first"),
                                         designite_id=("designite_id", "first"), is_class=("is_class", "first"),
                                         pc3_empty=("pc3_empty", "first")).reset_index()
    g = g[g.n >= min_ann].copy()
    g["label"] = np.select([g.y * 2 > g.n, g.y * 2 < g.n], ["smelly", "benign"], "tie")
    g["unanimous"] = (g.y == 0) | (g.y == g.n)
    g["target"] = np.where(g.label == "smelly", 1, np.where(g.label == "benign", 0, np.nan))
    if ties_as == "smelly":
        g.loc[g.label == "tie", "target"] = 1
    return g


VARIANTS = ["primary", "R1", "R2", "R3", "R4", "R5", "R6", "R7c"]
VARIANT_DESC = {
    "primary": "checkbox answer, consistency-filtered",
    "R1": "entities with >= 3 usable annotations (MA only)",
    "R2": "ties counted as smelly",
    "R3": "is_smell as answer, all annotations",
    "R4": "annotations inside runs removed",
    "R5": "LPL pc = 3 entities removed",
    "R6": "no consistency filter",
    "R7c": "entities with >= 2 annotations in the same run removed",
}


def variant_entities(L, variant, smells=None):
    """Entity label table for a plan.md §4.1 variant. Returns None where the variant does not apply."""
    A = L if smells is None else L[L.smell.isin(smells)]
    min_ann, ties_as = 2, None
    if variant in ("primary", "R1", "R2", "R5", "R7c"):
        A = A[~A.inconsistent]
    elif variant == "R3":
        A = A.assign(answer=A.is_smell.astype(int))
    elif variant == "R4":
        A = A[~A.inconsistent & ~A.in_run]
    elif variant == "R6":
        pass
    else:
        raise ValueError(variant)
    if variant == "R1":
        min_ann = 3
    if variant == "R2":
        ties_as = "smelly"
    if variant == "R5":
        A = A[~A.pc3_empty.astype(bool)]
    E = entity_labels(A, min_ann=min_ann, ties_as=ties_as)
    if variant == "R7c":
        co = A[A.run_id != ""].groupby(["smell", "entity", "run_id"]).size()
        co = co[co >= 2].reset_index()[["smell", "entity"]].drop_duplicates()
        key = set(zip(co.smell, co.entity))
        E = E[[(s, e) not in key for s, e in zip(E.smell, E.entity)]]
    return E


def variant_applies(variant, smell, quantity):
    """quantity in {'alpha', 'auc', 'youden', 'rq4', 'rq3', 'rq5'}"""
    if quantity in ("rq4", "rq3") and smell == "MA":
        return False  # D8: MA is descriptive only, never modelled
    if variant == "R1":
        return smell == "MA" and quantity in ("alpha", "auc", "youden")
    if variant == "R2":
        return quantity in ("auc", "youden", "rq4")
    if variant == "R5":
        return smell == "LPL"
    if variant == "R7c":
        return quantity == "alpha"
    if quantity in ("rq4", "rq3", "rq5") and smell == "MA":
        return False
    return True


def primary_filter(L):
    """Primary analysis annotation set: drop self-contradicting annotations (D7)."""
    return L[~L.inconsistent]


def attach_metrics(E):
    """Join stored DesigniteJava metrics and computed features onto an entity table."""
    _, smp, mm, cm, _ = load_tables()
    feats = load_features()
    out = []
    for is_class, tab in ((0, mm), (1, cm)):
        e = E[E.is_class == is_class]
        cols = ["id", "cc", "pc", "loc"] if is_class == 0 else ["id", "lcom", "nom", "nof", "loc", "wmc"]
        e = e.merge(tab[cols].rename(columns={"id": "designite_id"}), on="designite_id", how="left")
        out.append(e)
    E2 = pd.concat(out, ignore_index=True)
    E2 = E2.merge(feats, on="path", how="left")
    return E2


def load_features():
    p = os.path.join(FEAT_DIR, "features.csv.gz")
    f = pd.read_csv(p)
    return f[["path", "statements", "max_nesting", "comment_ratio", "method_calls"]]


# ---------------------------------------------------------------- statistics helpers
def rng():
    return np.random.default_rng(SEED)


def boot_ci(values, alpha=0.05):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)])
    if len(v) == 0:
        return (np.nan, np.nan)
    return (float(np.percentile(v, 100 * alpha / 2)), float(np.percentile(v, 100 * (1 - alpha / 2))))


def alpha_binary(n, y):
    """Krippendorff's alpha (nominal, binary) from per-unit counts. Units need n >= 2."""
    n = np.asarray(n, float)
    y = np.asarray(y, float)
    k = n - y
    o01 = np.sum(y * k / (n - 1))
    o11 = np.sum(y * (y - 1) / (n - 1))
    o00 = np.sum(k * (k - 1) / (n - 1))
    n1 = o11 + o01
    n0 = o00 + o01
    N = n0 + n1
    if n0 == 0 or n1 == 0:
        return np.nan
    return 1 - (N - 1) * (2 * o01) / (2 * n0 * n1)


def pct_agreement(n, y):
    n = np.asarray(n, float)
    y = np.asarray(y, float)
    pairs = n * (n - 1) / 2
    agree = (y * (y - 1) + (n - y) * (n - y - 1)) / 2
    return float(np.mean(agree / pairs))


def bh(p):
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    q = p[ok]
    m = len(q)
    order = np.argsort(q)
    ranked = q[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    res = np.empty(m)
    res[order] = np.minimum(ranked, 1)
    out[ok] = res
    return out


# ---------------------------------------------------------------- formatting
def fmt(x, d=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{x:.{d}f}"


def fmt_ci(est, lo, hi, d=3):
    return f"{fmt(est, d)} [{fmt(lo, d)}, {fmt(hi, d)}]"


def fmt_p(p):
    if p is None or not np.isfinite(p):
        return "n/a"
    return f"{p:.2e}" if p < 1e-3 else f"{p:.4f}"


def md_table(df, index=False):
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in d.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(out)


def write_frag(name, text):
    with open(os.path.join(FRAG, name + ".md"), "w") as f:
        f.write(text.rstrip() + "\n")


# ---------------------------------------------------------------- plot style (one style for every figure)
COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "ink": "#0b0b0b", "ink2": "#52514e",
       "grid": "#e4e3df"}


def plot_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": COL["ink2"],
        "axes.linewidth": 0.6, "xtick.color": COL["ink2"], "ytick.color": COL["ink2"],
        "axes.labelcolor": COL["ink"], "text.color": COL["ink"], "axes.grid": True, "grid.color": COL["grid"],
        "grid.linewidth": 0.5, "lines.linewidth": 1.4, "figure.dpi": 150, "savefig.dpi": 300,
        "savefig.bbox": "tight", "pdf.fonttype": 42,
    })
    return plt


def savefig(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"))
