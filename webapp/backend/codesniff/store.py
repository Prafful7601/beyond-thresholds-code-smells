"""SQLite storage for analyses (path from env CODESNIFF_DB, default webapp/backend/codesniff.db)."""
import datetime
import json
import os
import sqlite3
import uuid

from .resources import BACKEND_DIR

SCHEMA = """CREATE TABLE IF NOT EXISTS analyses (
  id TEXT PRIMARY KEY, cache_key TEXT, status TEXT, stage TEXT, created_at TEXT, finished_at TEXT,
  request TEXT, repo TEXT, sha TEXT, mode TEXT, score REAL, band TEXT, error TEXT, result TEXT);
CREATE INDEX IF NOT EXISTS idx_key ON analyses(cache_key);"""


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path=None):
        self.path = path or os.environ.get("CODESNIFF_DB") or os.path.join(BACKEND_DIR, "codesniff.db")
        with self._c() as c:
            c.executescript(SCHEMA)

    def _c(self):
        c = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def create(self, request):
        aid = uuid.uuid4().hex[:12]
        with self._c() as c:
            c.execute("INSERT INTO analyses (id, status, stage, created_at, request) VALUES (?, 'running', 'queued', ?, ?)",
                      (aid, _now(), json.dumps(request)))
        return aid

    def stage(self, aid, stage):
        with self._c() as c:
            c.execute("UPDATE analyses SET stage = ? WHERE id = ?", (stage, aid))

    def finish(self, aid, key, result):
        with self._c() as c:
            c.execute("UPDATE analyses SET status='done', stage='done', finished_at=?, cache_key=?, repo=?, sha=?, mode=?, "
                      "score=?, band=?, result=? WHERE id=?",
                      (_now(), key, result["repo"], result["target"]["sha"], result["mode"], result["risk"]["score"],
                       result["risk"]["band"], json.dumps(result), aid))

    def fail(self, aid, error):
        with self._c() as c:
            c.execute("UPDATE analyses SET status='error', stage='error', finished_at=?, error=? WHERE id=?",
                      (_now(), error, aid))

    def get(self, aid):
        with self._c() as c:
            r = c.execute("SELECT * FROM analyses WHERE id = ?", (aid,)).fetchone()
        if not r:
            return None
        out = {k: r[k] for k in r.keys() if k not in ("result", "request")}
        out["request"] = json.loads(r["request"] or "{}")
        out["result"] = json.loads(r["result"]) if r["result"] else None
        return out

    def find_done(self, key):
        with self._c() as c:
            r = c.execute("SELECT result FROM analyses WHERE cache_key = ? AND status = 'done' ORDER BY finished_at DESC LIMIT 1",
                          (key,)).fetchone()
        return json.loads(r["result"]) if r else None

    def history(self, limit=50):
        with self._c() as c:
            rows = c.execute("SELECT id, status, created_at, repo, sha, mode, score, band, error, request FROM analyses "
                             "ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall()
        return [{**{k: r[k] for k in r.keys() if k != "request"}, "request": json.loads(r["request"] or "{}")} for r in rows]
