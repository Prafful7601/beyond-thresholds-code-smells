"""Zone boundaries, rule verdicts, model loading and the honest note."""
import re

import numpy as np
import pytest

from codesniff import model as mdl
from codesniff.notes import evidence, note
from codesniff.resources import paper_numbers, table
from codesniff.zones import anomalous_values, bands, rule_flag, worst, zone


def test_bands_come_from_the_paper_table():
    t = table("audit_threshold_ranges.csv").set_index("smell")
    for s in ("CM", "LPL"):
        assert bands()[s]["lo"] == t.loc[s].observed_annotated_min
        assert bands()[s]["hi"] == t.loc[s].observed_annotated_max
        assert str(int(bands()[s]["rule_threshold"])) in t.loc[s].DesigniteJava_default


@pytest.mark.parametrize("smell", ["CM", "LPL"])
def test_zone_boundaries(smell):
    b = bands()[smell]
    assert zone(smell, b["lo"] - 1) == "clean"
    assert zone(smell, b["lo"]) == "borderline"
    assert zone(smell, b["hi"]) == "borderline"
    assert zone(smell, b["hi"] + 1) == "clear"
    t = b["rule_threshold"]
    assert rule_flag(smell, t) and not rule_flag(smell, t - 1)


def test_worst_zone():
    assert worst(["clean", "borderline"]) == "borderline"
    assert worst(["clean", "clear", "borderline"]) == "clear"


def test_lpl_pc3_anomaly_read_from_table():
    a = anomalous_values()["LPL"][3]
    assert a["entities"] > 0 and 0 <= a["share_smelly"] <= 1


def test_models_load_and_output_probabilities():
    rng = np.random.default_rng(0)
    for s in ("CM", "LPL"):
        c = mdl.card()[s]
        rows = [{f: float(rng.integers(0, 20)) for f in c["features"]} for _ in range(50)]
        p = mdl.probability(s, rows)
        assert p.shape == (50,) and np.all((p >= 0) & (p <= 1))
    assert mdl.probability("CM", []).size == 0


def test_model_card_matches_paper_tables():
    c = mdl.card()
    cm = table("model_comparison.csv")
    cm = cm[(cm.smell == "CM") & (cm.model == "LR")].iloc[0]
    assert c["CM"]["paper_cv"]["MCC"] == pytest.approx(cm.MCC)
    r5 = table("model_comparison_LPL_R5.csv")
    r5 = r5[r5.model == "SVM"].iloc[0]
    assert c["LPL"]["paper_cv"]["MCC"] == pytest.approx(r5.MCC)
    for s in ("CM", "LPL"):
        for k in ("training_data", "features", "hyperparameters", "trained_at", "repository_commit", "app_cv"):
            assert k in c[s]


@pytest.mark.parametrize("smell", ["CM", "LPL"])
def test_borderline_note_quotes_paper_numbers_and_is_not_a_verdict(smell):
    b = bands()[smell]
    v = b["lo"] + 2
    text = note(smell, "borderline", v)
    assert text.startswith("Candidate to review, not a verdict.")
    for e in evidence(smell).values():
        assert f"{e['estimate']:.3f}" in text
    assert not re.search(r"\b(certain|definitely|guaranteed)\b", text, re.I)


def test_lpl_pc3_note_mentions_anomaly():
    assert "anomalous block" in note("LPL", "borderline", 3)
    assert "anomalous block" not in note("LPL", "borderline", 4)


@pytest.mark.parametrize("z", ["clean", "clear"])
def test_out_of_band_notes_flag_extrapolation(z):
    assert "extrapolation" in note("CM", z, 1 if z == "clean" else 99)


def test_evidence_rows_exist_in_paper_numbers():
    labels = {r["number"] for r in paper_numbers()}
    for s in ("CM", "LPL"):
        for e in evidence(s).values():
            assert e["label"] in labels
