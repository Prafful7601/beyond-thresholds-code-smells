"""Data for the research-findings charts and the site configuration, all read from results files and model cards."""
import functools

from .model import card
from .notes import evidence
from .resources import PAPER_TITLE, PRIMARY, REPO_URL, SMELL_NAME, SMELLS, table
from .scoring import DISCLAIMER, RISK, formula_lines
from .zones import anomalous_values, bands

RESULTS_MD = f"{REPO_URL}/blob/main/results/results.md"
ABLATION_VARIANTS = ["(i) primary only", "DACOSX only", "DACOSX + DACOS", "DACOSX only, primary metric removed"]


def _records(df):
    return df.where(df.notna(), None).to_dict("records")


@functools.lru_cache(maxsize=1)
def findings():
    runs = table("audit_answer_runs.csv")
    longest = runs.loc[runs.length.idxmax()]
    hc = table("human_ceiling.csv")
    hc = hc[hc.metric == "MCC"]
    mm = table("agreement_matched_neardup.csv").set_index("population")
    ceiling = [{"population": r.population, "model": r.best_model,
                "human": [r.human_vs_human, r.human_lo, r.human_hi],
                "copies": [float(mm.loc[r.population].cross_MCC), float(mm.loc[r.population].cross_lo),
                           float(mm.loc[r.population].cross_hi)],
                "model_mcc": [r.model_vs_single_human, r.model_lo, r.model_hi]} for r in hc.itertuples()]
    spec = table("spec_curves.csv")
    r5best = table("model_comparison_LPL_R5.csv").query("best_model").model.iloc[0]
    abl = []
    for label, name, model in (("CM", "ablation_CM.csv", "LR"), ("LPL R5", "ablation_LPL_R5.csv", r5best)):
        a = table(name)
        a = a[(a.model == model) & (~a.is_reference) & (a.variant.isin(ABLATION_VARIANTS))]
        abl += [{"population": label, "model": model, "variant": r.variant, "delta_mcc": [r.d_MCC, r.d_MCC_lo, r.d_MCC_hi]}
                for r in a.itertuples()]
    cm = ceiling[[c["population"] for c in ceiling].index("CM")]
    return {
        "runs": {"rows": _records(runs[["smell", "first_ann_id", "last_ann_id", "length", "answer"]]),
                 "caption": (f"Ordered by annotation id, DACOS answers contain {len(runs)} runs of at least "
                             f"{int(runs.length.min())} identical answers; the longest is {int(longest.length)} consecutive "
                             f"'{'yes' if longest.answer == 1 else 'no'}' answers ({longest.smell}). The paper repeats every "
                             "result without them.")},
        "ceiling": {"rows": ceiling,
                    "caption": (f"Two annotators of the same Complex Method snippet agree at MCC {cm['human'][0]:.2f}; the "
                                f"best model reaches {cm['model_mcc'][0]:.2f}; annotators of structurally identical copies "
                                f"agree at only {cm['copies'][0]:.2f}.")},
        "spec": {"rows": _records(spec[["spec", "smell", "condition", "estimate", "lo", "hi", "reference"]]),
                 "labels": {"alpha": "Krippendorff's alpha", "auc": "Primary-metric ROC-AUC",
                            "rq4_LR": "Transfer MCC difference (LR)", "rq4_RF": "Transfer MCC difference (RF)",
                            "best_mcc": "Best-model MCC"},
                 "caption": "Each headline number under the primary analysis and every robustness reading of the data."},
        "ablation": {"rows": abl,
                     "caption": "Training on threshold-labelled DACOSX snippets, or on the primary metric alone, does worse "
                                "than training on human-labelled borderline snippets with all features."},
        "links": {"repository": REPO_URL, "results": RESULTS_MD, "paper": PAPER_TITLE},
    }


@functools.lru_cache(maxsize=1)
def config():
    c = card()
    return {
        "risk": {"params": dict(RISK), "formula": formula_lines(), "disclaimer": DISCLAIMER},
        "smells": {s: {"name": SMELL_NAME[s], "metric": PRIMARY[s], "band": bands()[s],
                       "anomalous_values": {str(k): v for k, v in anomalous_values().get(s, {}).items()},
                       "evidence": evidence(s),
                       "model": {k: c[s][k] for k in ("model", "features", "hyperparameters", "trained_at",
                                                      "repository_commit", "training_data", "paper_cv", "app_cv",
                                                      "probability")}}
                   for s in SMELLS},
        "excluded": {"MA": "Multifaceted Abstraction is descriptive only in the paper: after the consistency filter it "
                           "has too few benign labels to train or evaluate a model."},
        "links": {"repository": REPO_URL, "results": RESULTS_MD, "paper": PAPER_TITLE},
    }
