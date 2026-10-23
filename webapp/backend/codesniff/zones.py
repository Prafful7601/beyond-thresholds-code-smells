"""Zones and the DesigniteJava rule, both read from the paper's tables (never typed by hand).

* Band = the observed range of the primary metric over all DACOS-annotated entities
  (results/tables/audit_threshold_ranges.csv: CM cc 5-14, LPL pc 3-10).
* clean = below the band, borderline = inside it, clear = above it.
* Rule = the DesigniteJava default threshold in the same table (metric >= threshold).
"""
import functools
import re

from .resources import PRIMARY, table

ZONE_ORDER = {"clean": 0, "borderline": 1, "clear": 2}


@functools.lru_cache(maxsize=1)
def bands():
    t = table("audit_threshold_ranges.csv").set_index("smell")
    out = {}
    for smell in ("CM", "LPL"):
        r = t.loc[smell]
        thr = float(re.search(r"([\d.]+)", str(r.DesigniteJava_default)).group(1))
        out[smell] = {"metric": PRIMARY[smell], "lo": float(r.observed_annotated_min), "hi": float(r.observed_annotated_max),
                      "rule_threshold": thr}
    return out


@functools.lru_cache(maxsize=1)
def anomalous_values():
    """Primary-metric values that the paper identified as an anomalous answer block (LPL pc = 3; results.md §1.7, R5)."""
    t = table("rq2_share_smelly_by_metric.csv")
    r = t[(t.smell == "LPL") & (t.value.astype(str).str.strip() == "3")]
    if len(r) != 1:
        return {}
    return {"LPL": {3: {"entities": int(r.entities.iloc[0]), "share_smelly": float(r.share_smelly.iloc[0])}}}


def zone(smell, value):
    b = bands()[smell]
    if value < b["lo"]:
        return "clean"
    if value > b["hi"]:
        return "clear"
    return "borderline"


def rule_flag(smell, value):
    return bool(value >= bands()[smell]["rule_threshold"])


def worst(zones):
    return max(zones, key=lambda z: ZONE_ORDER[z])
