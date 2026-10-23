"""Locations of repository resources and read-only access to the paper's results.

Every number CodeSniff shows comes from results/paper_numbers.json, results/tables/*.csv or the saved model
card; nothing is typed by hand.
"""
import functools
import json
import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(APP_DIR)
SRC = os.path.join(REPO, "src")
RESULTS = os.path.join(REPO, "results")
TABLES = os.path.join(RESULTS, "tables")
MODELS = os.path.join(APP_DIR, "models")
REPO_URL = "https://github.com/Prafful7601/beyond-thresholds-code-smells"
PAPER_TITLE = ("Metric Thresholds Versus Human Judgment on Borderline Code Smells: "
               "A Robustness-First Audit of the DACOS Benchmark")
SMELLS = ("CM", "LPL")
SMELL_NAME = {"CM": "Complex Method", "LPL": "Long Parameter List"}
PRIMARY = {"CM": "cc", "LPL": "pc"}


@functools.lru_cache(maxsize=1)
def paper_features():
    """The paper's feature extraction (src/features.py), imported unchanged so definitions match exactly."""
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import features  # noqa: E402  (src/features.py)
    return features


@functools.lru_cache(maxsize=1)
def paper_numbers():
    with open(os.path.join(RESULTS, "paper_numbers.json"), encoding="utf-8") as f:
        return json.load(f)


def paper_number(startswith):
    """Return the unique headline row whose label starts with `startswith`."""
    rows = [r for r in paper_numbers() if r["number"].startswith(startswith)]
    if len(rows) != 1:
        raise KeyError(f"expected one headline row starting with {startswith!r}, found {len(rows)}")
    return rows[0]


def table(name):
    import pandas as pd
    return pd.read_csv(os.path.join(TABLES, name))
