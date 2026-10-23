"""Copy the paper files the backend reads (resources.PAPER_FILES) into webapp/backend/paper/.

Run after regenerating results:  python webapp/backend/sync_paper_files.py
tests/test_bundled_paper_files.py fails if the copy differs from the repository's files.
"""
import os
import shutil

from codesniff.resources import BUNDLED, PAPER_FILES, REPO_ROOT

if __name__ == "__main__":
    shutil.rmtree(BUNDLED, ignore_errors=True)
    for rel in PAPER_FILES:
        dst = os.path.join(BUNDLED, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(REPO_ROOT, rel), dst)
        print("copied", rel)
