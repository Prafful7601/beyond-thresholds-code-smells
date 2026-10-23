"""Every number the app shows comes from results files or the model card: no headline value is typed in source."""
import glob
import os

import pytest

from codesniff.resources import APP_DIR, paper_numbers


def sources():
    files = glob.glob(os.path.join(APP_DIR, "codesniff", "*.py")) + [os.path.join(APP_DIR, "streamlit_app.py")]
    return [f for f in files if os.path.exists(f)]


def test_no_headline_number_is_hard_coded():
    values = set()
    for r in paper_numbers():
        for k in ("estimate", "ci_lo", "ci_hi"):
            v = r[k]
            if v is not None and abs(v) not in (0.0, 1.0) and not float(v).is_integer():
                values.add(f"{v:.3f}")
    hits = []
    for f in sources():
        text = open(f, encoding="utf-8").read()
        hits += [(os.path.basename(f), v) for v in values if v in text]
    assert not hits, f"hard-coded paper numbers found: {hits}"


def test_app_requirements_match_root_file():
    root = os.path.dirname(APP_DIR)
    a = open(os.path.join(root, "requirements-app.txt")).read()
    b_path = os.path.join(APP_DIR, "requirements.txt")
    if not os.path.exists(b_path):
        pytest.skip("app/requirements.txt not created yet")
    assert a == open(b_path).read()
