"""Run CodeSniff on a snippet, a .java file, a folder, a .zip archive or a public GitHub repository."""
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

from . import model as mdl
from .extract import extract_methods
from .notes import note
from .resources import PRIMARY, SMELLS
from .zones import ZONE_ORDER, rule_flag, worst, zone

GITHUB_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?(\.git)?/?$")
SKIP_DIRS = {".git", "node_modules", "build", "target", "out", ".gradle", ".idea"}
MAX_FILE_BYTES = 1_000_000


def _score(methods):
    rows = [m.as_dict() for m in methods]
    for smell in SMELLS:
        probs = mdl.probability(smell, rows)
        for r, p in zip(rows, probs):
            v = r[PRIMARY[smell]]
            z = zone(smell, v)
            r[f"{smell}_zone"] = z
            r[f"{smell}_rule"] = rule_flag(smell, v)
            r[f"{smell}_probability"] = float(p)
            r[f"{smell}_note"] = note(smell, z, v)
    for r in rows:
        r["status"] = worst([r[f"{s}_zone"] for s in SMELLS])
    return rows


def analyze_text(text, filename="Snippet.java"):
    return _score(extract_methods(text, filename))


def java_files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
        for f in sorted(files):
            if f.endswith(".java"):
                yield os.path.join(d, f)


def analyze_dir(root, progress=None, max_files=None):
    files = list(java_files(root))
    if max_files:
        files = files[:max_files]
    rows, skipped = [], []
    for i, path in enumerate(files):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            if os.path.getsize(path) > MAX_FILE_BYTES:
                skipped.append((rel, "larger than 1 MB"))
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                rows += analyze_text(fh.read(), rel)
        except Exception as exc:   # one unparsable file must not stop a scan
            skipped.append((rel, f"{type(exc).__name__}: {exc}"))
        if progress:
            progress(i + 1, len(files), rel)
    return rows, skipped


def safe_extract(zip_path, dest):
    """Extract a zip archive, refusing entries that would escape `dest` (zip-slip)."""
    root = os.path.realpath(dest)
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = os.path.realpath(os.path.join(dest, info.filename))
            if target != root and not target.startswith(root + os.sep):
                raise ValueError(f"unsafe path in archive: {info.filename}")
        zf.extractall(dest)


def clone_github(url, dest, timeout=180):
    if not GITHUB_URL.match(url.strip()):
        raise ValueError("expected a public repository URL of the form https://github.com/<owner>/<repo>")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", url.strip(), dest], check=True, timeout=timeout, env=env,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def analyze_path(target, progress=None, max_files=None):
    """`target`: .java file, folder, .zip archive or https://github.com/<owner>/<repo>. Returns (rows, skipped, root)."""
    if target.startswith("https://"):
        tmp = tempfile.mkdtemp(prefix="codesniff_")
        try:
            clone_github(target, os.path.join(tmp, "repo"))
            rows, skipped = analyze_dir(os.path.join(tmp, "repo"), progress, max_files)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return rows, skipped, target
    if target.endswith(".zip") and os.path.isfile(target):
        tmp = tempfile.mkdtemp(prefix="codesniff_")
        try:
            safe_extract(target, tmp)
            rows, skipped = analyze_dir(tmp, progress, max_files)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return rows, skipped, target
    if os.path.isdir(target):
        rows, skipped = analyze_dir(target, progress, max_files)
        return rows, skipped, target
    if os.path.isfile(target):
        with open(target, encoding="utf-8", errors="replace") as fh:
            return analyze_text(fh.read(), os.path.basename(target)), [], os.path.dirname(target) or "."
    raise FileNotFoundError(target)


def sort_rows(rows):
    """Clear first, then borderline, then clean; within a zone by the highest model probability."""
    return sorted(rows, key=lambda r: (-ZONE_ORDER[r["status"]], -max(r[f"{s}_probability"] for s in SMELLS),
                                       r["file"], r["start_line"]))
