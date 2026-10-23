"""Change status per method and smell, and the commit's smell risk score.

The score measures code-smell risk in the changed code. It is NOT a probability of bugs or build failure.

    method points = 1.0                                   if any smell is clear
                  = 0.5 x (highest model probability among borderline smells)   if any smell is borderline
                  = 0                                     if all smells are clean
                  + 0.25 for each introduced or worsened smell, capped at 1.0 per method
    score = 100 x (sum of method points) / (number of changed methods)
    small-sample flag if fewer than 3 changed methods; bands: Low < 25, Medium 25-50, High > 50

Deleted methods are reported but not scored (they have no code after the change).
A probability rise of >= 0.2 counts as "worsened" only when the method is borderline after the change, because the
model is only meaningful inside the band it was trained on.
"""
from .zones import ZONE_ORDER

RISK = {
    "clear_points": 1.0,
    "borderline_weight": 0.5,
    "change_bonus": 0.25,
    "method_cap": 1.0,
    "probability_delta": 0.2,
    "small_sample_below": 3,
    "medium_from": 25.0,
    "high_above": 50.0,
}
FORMULA = [
    "method points = {clear_points:g} if any smell is clear",
    "otherwise {borderline_weight:g} × model probability if borderline (highest among borderline smells); 0 if clean",
    "+ {change_bonus:g} for each introduced or worsened smell, capped at {method_cap:g} per method",
    "score = 100 × (sum of method points) / (number of changed methods); deleted methods are not scored",
    "Low < {medium_from:g}, Medium {medium_from:g}–{high_above:g}, High > {high_above:g}; "
    "small-sample flag if fewer than {small_sample_below:g} methods changed",
]
DISCLAIMER = ("The smell risk score measures code-smell risk in the changed Java methods (Complex Method and Long "
              "Parameter List). It is not a probability of bugs, defects or build failure.")


def formula_lines(params=RISK):
    return [line.format(**params) for line in FORMULA]


def change_status(before, after, params=RISK):
    """before/after: {"zone", "probability"} for one smell, or None if the method does not exist on that side."""
    if after is None:
        return "removed"
    if before is None or before["zone"] == "clean":
        if after["zone"] != "clean":
            return "introduced"
        return "unchanged"
    up = ZONE_ORDER[after["zone"]] - ZONE_ORDER[before["zone"]]
    if up > 0:
        return "worsened"
    if up < 0:
        return "improved"
    if after["zone"] == "borderline":
        delta = after["probability"] - before["probability"]
        if delta >= params["probability_delta"]:
            return "worsened"
        if delta <= -params["probability_delta"]:
            return "improved"
    return "unchanged"


def method_points(after, statuses, params=RISK):
    """after: {smell: {"zone", "probability"}} or None (deleted); statuses: {smell: status}."""
    if after is None:
        return None
    zones = {s: a["zone"] for s, a in after.items()}
    if "clear" in zones.values():
        base = params["clear_points"]
    elif "borderline" in zones.values():
        base = params["borderline_weight"] * max(a["probability"] for a in after.values() if a["zone"] == "borderline")
    else:
        base = 0.0
    bonus = params["change_bonus"] * sum(1 for st in statuses.values() if st in ("introduced", "worsened"))
    return min(params["method_cap"], base + bonus)


def band(score, params=RISK):
    if score is None:
        return "n/a"
    if score > params["high_above"]:
        return "High"
    if score >= params["medium_from"]:
        return "Medium"
    return "Low"


def risk_score(points, params=RISK):
    """points: list of method points (None = deleted, not scored)."""
    scored = [p for p in points if p is not None]
    n = len(scored)
    score = 100.0 * sum(scored) / n if n else None
    return {"score": score, "band": band(score, params), "scored_methods": n, "sum_points": float(sum(scored)),
            "small_sample": n < params["small_sample_below"], "params": dict(params),
            "formula": formula_lines(params), "disclaimer": DISCLAIMER}


def method_status(statuses):
    """One label per method for summaries: introduced > worsened > improved > removed > unchanged."""
    for s in ("introduced", "worsened", "improved", "removed"):
        if s in statuses.values():
            return s
    return "unchanged"
