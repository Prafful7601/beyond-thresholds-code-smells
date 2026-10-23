"""Every number the app shows comes from results files or the model card: no headline value is typed in source."""
import glob
import os

from codesniff.resources import APP_DIR, paper_numbers


def sources():
    return glob.glob(os.path.join(APP_DIR, "codesniff", "*.py")) + glob.glob(os.path.join(APP_DIR, "*.py"))


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
