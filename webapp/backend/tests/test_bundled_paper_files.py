"""The bundled copy of the paper files (webapp/backend/paper/) must match the repository's files exactly."""
import filecmp
import os

import pytest

from codesniff.resources import BUNDLED, PAPER_FILES, REPO_ROOT


@pytest.mark.parametrize("rel", PAPER_FILES)
def test_bundled_copy_matches_repository(rel):
    src = os.path.join(REPO_ROOT, rel)
    if not os.path.exists(src):
        pytest.skip("repository files not present (deployed bundle)")
    assert filecmp.cmp(src, os.path.join(BUNDLED, rel), shallow=False), f"{rel} changed: run sync_paper_files.py"


def test_backend_runs_from_the_bundle_alone(tmp_path):
    """Without the repository's src/ and results/, the API must still serve findings, config and an analysis."""
    import subprocess
    import sys
    code = ("from fastapi.testclient import TestClient; import main; c = TestClient(main.app); "
            "import codesniff.resources as r; assert r.REPO == r.BUNDLED, r.REPO; "
            "assert c.get('/api/findings').json()['ceiling']['rows']; assert c.get('/config').json()['smells']['CM']['band']; "
            "from codesniff.analyze import analyze_text; print(len(analyze_text('class A { int f(int a, int b) { return a; } }', 'A.java')))")
    import shutil
    import stat
    # A read-only copy, as on serverless hosts (Vercel mounts the code at a read-only /var/task).
    ro = tmp_path / "paper"
    shutil.copytree(BUNDLED, ro)
    for root, dirs, files in os.walk(ro):
        for name in dirs + files:
            p = os.path.join(root, name)
            os.chmod(p, stat.S_IRUSR | (stat.S_IXUSR if os.path.isdir(p) else 0))
    os.chmod(ro, stat.S_IRUSR | stat.S_IXUSR)
    env = dict(os.environ, CODESNIFF_ROOT=str(ro), CODESNIFF_DB=str(tmp_path / "b.db"))
    try:
        out = subprocess.run([sys.executable, "-c", code.replace("assert r.REPO == r.BUNDLED, r.REPO; ", "")],
                             cwd=os.path.dirname(BUNDLED), env=env, capture_output=True, text=True)
    finally:
        for root, dirs, files in os.walk(ro):
            os.chmod(root, stat.S_IRWXU)
    assert out.returncode == 0, out.stderr[-2000:]
    assert not os.path.exists(ro / "results" / "figures")
