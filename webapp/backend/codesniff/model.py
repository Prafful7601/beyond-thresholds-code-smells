"""Saved models and their card (app/models/). Loading needs only the joblib files and model_card.json."""
import functools
import json
import os

import joblib
import numpy as np

from .resources import MODELS


@functools.lru_cache(maxsize=1)
def card():
    with open(os.path.join(MODELS, "model_card.json"), encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=2)
def model(smell):
    return joblib.load(os.path.join(MODELS, card()[smell]["file"]))


def probability(smell, rows):
    """P(smelly) for a list of feature dicts, using the feature order recorded in the model card."""
    if not rows:
        return np.array([])
    feats = card()[smell]["features"]
    X = np.array([[float(r[f]) for f in feats] for r in rows])
    return model(smell).predict_proba(X)[:, 1]
