"""The honest note shown with every result. All numbers are read from results/paper_numbers.json."""
import functools

from .resources import SMELL_NAME, paper_number
from .zones import anomalous_values, bands

# Which headline rows describe the band for each smell (labels in results/paper_numbers.json).
ROWS = {"CM": {"model": "Best model MCC, CM (", "same": "Human-vs-human MCC, CM",
               "copies": "Human-vs-human MCC between same-project near-duplicates, CM"},
        "LPL": {"model": "Best model MCC, LPL R5 (", "same": "Human-vs-human MCC, LPL R5",
                "copies": "Human-vs-human MCC between same-project near-duplicates, LPL R5"}}


def _ci(r):
    return f"{r['estimate']:.3f} [95% CI {r['ci_lo']:.3f}, {r['ci_hi']:.3f}]"


@functools.lru_cache(maxsize=4)
def evidence(smell):
    rows = {k: paper_number(v) for k, v in ROWS[smell].items()}
    return {k: {"estimate": r["estimate"], "ci_lo": r["ci_lo"], "ci_hi": r["ci_hi"], "label": r["number"],
                "source_table": r["source_table"]} for k, r in rows.items()}


def note(smell, zone, value):
    b = bands()[smell]
    m = b["metric"]
    band = f"{m} {b['lo']:g}–{b['hi']:g}"
    if zone == "borderline":
        e = evidence(smell)
        text = (f"Candidate to review, not a verdict. {m} = {value:g} lies inside the band that DACOS annotators judged "
                f"({band}). In this band the paper's best model reached MCC {_ci(e['model'])}. Two annotators of the "
                f"same snippet agreed at MCC {_ci(e['same'])}, but annotators of structurally identical copies "
                f"agreed at only MCC {_ci(e['copies'])}.")
        anom = anomalous_values().get(smell, {}).get(int(value)) if float(value).is_integer() else None
        if anom:
            text += (f" Note: {m} = {int(value)} is the anomalous block found in the paper (all {anom['entities']} unanimous "
                     f"entities labelled smelly, share {anom['share_smelly']:.2f}, inside one run of identical answers); "
                     "the LPL model was trained without it (R5), so treat this value with extra caution.")
        return text
    if zone == "clean":
        return (f"Below the annotated band ({band}). DACOS has no human labels here; threshold-based datasets treat "
                f"such code as not {SMELL_NAME[smell].lower()}. The model was trained only inside the band, so its "
                "probability is an extrapolation.")
    return (f"Above the annotated band ({band}). DACOS labels such code smelly by threshold (DACOSX), not by human "
            "judgment. The model was trained only inside the band, so its probability is an extrapolation.")
