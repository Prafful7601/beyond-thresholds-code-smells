"""The smell risk formula (scoring.py), unit by unit."""
import pytest

from codesniff.scoring import RISK, band, change_status, formula_lines, method_points, method_status, risk_score


def z(zone, p=0.5):
    return {"zone": zone, "probability": p}


@pytest.mark.parametrize("before, after, expected", [
    (None, z("clean"), "unchanged"),
    (None, z("borderline"), "introduced"),
    (None, z("clear"), "introduced"),
    (z("clean"), z("borderline"), "introduced"),
    (z("borderline"), z("clear"), "worsened"),
    (z("clear"), z("borderline"), "improved"),
    (z("borderline", 0.40), z("borderline", 0.60), "worsened"),     # +0.20
    (z("borderline", 0.40), z("borderline", 0.59), "unchanged"),
    (z("borderline", 0.70), z("borderline", 0.50), "improved"),
    (z("clean", 0.30), z("clean", 0.70), "unchanged"),             # probability outside the band is not used
    (z("borderline"), None, "removed"),
])
def test_change_status(before, after, expected):
    assert change_status(before, after) == expected


def test_method_points_cases():
    assert method_points(None, {}) is None                                               # deleted: not scored
    assert method_points({"CM": z("clean"), "LPL": z("clean")}, {}) == 0
    assert method_points({"CM": z("clear"), "LPL": z("clean")}, {}) == RISK["clear_points"]
    assert method_points({"CM": z("borderline", 0.6), "LPL": z("borderline", 0.8)}, {}) == pytest.approx(0.5 * 0.8)
    assert method_points({"CM": z("borderline", 0.6), "LPL": z("clean", 0.99)}, {"CM": "introduced"}) == pytest.approx(0.3 + 0.25)
    assert method_points({"CM": z("borderline", 0.6), "LPL": z("borderline", 0.6)},
                         {"CM": "introduced", "LPL": "worsened"}) == pytest.approx(0.3 + 0.5)
    assert method_points({"CM": z("clear"), "LPL": z("clear")}, {"CM": "introduced", "LPL": "worsened"}) == 1.0   # cap


def test_bands_and_edges():
    assert band(None) == "n/a"
    assert band(24.99) == "Low" and band(25) == "Medium" and band(50) == "Medium" and band(50.01) == "High"


def test_risk_score():
    r = risk_score([1.0, 0.0, None, 0.5])
    assert r["scored_methods"] == 3 and r["score"] == pytest.approx(50.0) and r["band"] == "Medium"
    assert not r["small_sample"]
    assert risk_score([1.0, 1.0])["small_sample"]
    empty = risk_score([None])
    assert empty["score"] is None and empty["band"] == "n/a" and empty["small_sample"]


def test_formula_text_uses_parameters_and_disclaimer():
    lines = formula_lines()
    assert any(f"{RISK['change_bonus']:g}" in l for l in lines) and any(f"{RISK['high_above']:g}" in l for l in lines)
    assert "not a probability of bugs" in risk_score([0.2])["disclaimer"]


def test_method_status_priority():
    assert method_status({"CM": "improved", "LPL": "introduced"}) == "introduced"
    assert method_status({"CM": "worsened", "LPL": "improved"}) == "worsened"
    assert method_status({"CM": "unchanged", "LPL": "unchanged"}) == "unchanged"
