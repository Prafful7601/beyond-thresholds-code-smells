"""CodeSniff cc/pc versus the stored DesigniteJava values on 200 DACOS snippets (paper: raw lizard 59% cc, 96% pc).

The check needs the DACOS data (downloaded by run_all.sh, not redistributed). Without it, the stored result written
by app/train_models.py is verified and reported instead.
"""
import json
import os

import pytest

from codesniff.resources import MODELS, REPO

STORED = os.path.join(MODELS, "lizard_agreement.json")
DATA = [os.path.join(REPO, "data/raw/files.zip"), os.path.join(REPO, "data/db/dacos_main.sqlite")]


def test_stored_agreement_report():
    a = json.load(open(STORED))
    assert a["n"] == 200
    print(f"\ncc exact: raw lizard {a['cc_exact_raw_lizard']:.3f}, CodeSniff {a['cc_exact_codesniff']:.3f} "
          f"(within 1: {a['cc_within_1_codesniff']:.3f}); pc exact {a['pc_exact_codesniff']:.3f}")
    assert a["cc_exact_codesniff"] >= a["cc_exact_raw_lizard"]          # the adjustment helps
    assert a["pc_exact_codesniff"] >= 0.85


@pytest.mark.skipif(not all(os.path.exists(p) for p in DATA), reason="DACOS data not present (run run_all.sh)")
def test_recompute_agreement_on_dacos():
    import sqlite3
    import sys
    import zipfile
    import numpy as np
    import pandas as pd
    from codesniff.extract import extract_methods
    con = sqlite3.connect(DATA[1])
    ann = pd.read_sql("select distinct sample_id from annotation", con)
    smp = pd.read_sql("select * from sample where is_class = 0", con)
    mm = pd.read_sql("select id, cc, pc, method_name from method_metrics", con)
    z = zipfile.ZipFile(DATA[0])
    names = set(z.namelist())
    a = smp[smp.id.isin(ann.sample_id)].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
    a = a[a.path_to_file.str.lstrip("/").isin(names)].reset_index(drop=True)
    stored = json.load(open(STORED))
    pick = np.random.default_rng(stored["seed"]).choice(len(a), 200, replace=False)
    ok_cc = ok_pc = 0
    for i in sorted(pick):
        r = a.iloc[i]
        ms = extract_methods(z.read(r.path_to_file.lstrip("/")).decode("utf-8", "replace"))
        same = [m for m in ms if m.name == r.method_name] or ms
        m = max(same, key=lambda m: m.loc)
        ok_cc += m.cc == int(r.cc)
        ok_pc += m.pc == int(r.pc)
    assert ok_cc / 200 == pytest.approx(stored["cc_exact_codesniff"])
    assert ok_pc / 200 == pytest.approx(stored["pc_exact_codesniff"])
