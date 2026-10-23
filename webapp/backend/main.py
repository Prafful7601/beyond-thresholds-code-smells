"""CodeSniff website API (FastAPI).   Run:  uvicorn main:app --app-dir webapp/backend --port 8000

Endpoints: POST /analyze, GET /analysis/{id}, GET /analysis/{id}/report.{json,csv,pdf}, GET /history,
GET /findings, GET /config, GET /health. The same routes also answer under CODESNIFF_API_PREFIX (default /api), so the
API works whether or not a proxy (e.g. a Vercel rewrite of /api/*) strips the prefix.

On serverless hosts (VERCEL set, or CODESNIFF_INLINE=1) POST /analyze runs the analysis inside the request and returns
the finished record, because a background job on one instance cannot be polled from another.
"""
import csv
import io
import os
import sys
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codesniff import __version__  # noqa: E402
from codesniff.findings import config, findings  # noqa: E402
from codesniff.github import GitHub, GitHubError, parse_target  # noqa: E402
from codesniff.model import card, model  # noqa: E402
from codesniff.pdf import report_pdf  # noqa: E402
from codesniff.resources import PRIMARY, SMELLS  # noqa: E402
from codesniff.service import analyze_commit, cache_key  # noqa: E402
from codesniff.store import Store  # noqa: E402

API_PREFIX = os.environ.get("CODESNIFF_API_PREFIX", "/api").rstrip("/")
INLINE = bool(os.environ.get("VERCEL") or os.environ.get("CODESNIFF_INLINE"))

app = FastAPI(title="CodeSniff API", version=__version__,
              description="Smell risk of the Java methods changed by a commit (Complex Method, Long Parameter List). "
                          "The score measures code-smell risk; it is not a bug or build-failure prediction.")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CODESNIFF_CORS", "*").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["*"])
STATE = {"store": None, "github": GitHub, "inline": INLINE}


class PrefixRoot:
    """Serve every route under API_PREFIX too: a matching request gets root_path = API_PREFIX, which Starlette strips
    before routing (and which /docs uses to find /api/openapi.json)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] in ("http", "websocket") and API_PREFIX and (path == API_PREFIX or path.startswith(API_PREFIX + "/")):
            scope = dict(scope, root_path=scope.get("root_path", "") + API_PREFIX)
        await self.app(scope, receive, send)


app.add_middleware(PrefixRoot)


def store():
    if STATE["store"] is None:
        # Serverless file systems are read-only except /tmp (and /tmp is per instance).
        STATE["store"] = Store(os.environ.get("CODESNIFF_DB") or ("/tmp/codesniff.db" if os.environ.get("VERCEL") else None))
    return STATE["store"]


class AnalyzeRequest(BaseModel):
    repo_url: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    mode: str = "commit"           # "commit" (diff of a commit / PR) or "repo" (scan the whole repository, capped)
    max_files: Optional[int] = None


def run_job(aid, req):
    st = store()
    try:
        gh = STATE["github"]()
        target = parse_target(req["repo_url"], req.get("commit_sha"), req.get("pr_url"))
        if target["kind"] == "commit" and len(target["sha"]) == 40:
            hit = st.find_done(cache_key(target, req["mode"], target["sha"].lower(), req.get("max_files")))
            if hit:
                st.finish(aid, cache_key(target, req["mode"], hit["target"]["sha"], req.get("max_files")), {**hit, "cached": True})
                return
        result = analyze_commit(req["repo_url"], req.get("commit_sha"), req.get("pr_url"), req["mode"],
                                req.get("max_files"), gh=gh, progress=lambda s: st.stage(aid, s))
        st.finish(aid, cache_key(target, req["mode"], result["target"]["sha"], req.get("max_files")), result)
    except GitHubError as exc:
        st.fail(aid, exc.message)
    except Exception as exc:  # pragma: no cover - surfaced to the user as a friendly error
        st.fail(aid, f"Analysis failed: {exc.__class__.__name__}: {exc}")


@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest, background: BackgroundTasks):
    if req.mode not in ("commit", "repo"):
        raise HTTPException(400, "mode must be 'commit' or 'repo'")
    try:
        parse_target(req.repo_url, req.commit_sha, req.pr_url)
    except GitHubError as exc:
        raise HTTPException(exc.status, exc.message)
    body = req.model_dump()
    aid = store().create(body)
    if STATE["inline"]:
        run_job(aid, body)
        return JSONResponse(store().get(aid), status_code=200)
    background.add_task(run_job, aid, body)
    return {"id": aid, "status": "running", "stage": "queued"}


@app.get("/analysis/{aid}")
def get_analysis(aid: str):
    a = store().get(aid)
    if not a:
        raise HTTPException(404, "No analysis with this id.")
    return a


def _done(aid):
    a = get_analysis(aid)
    if a["status"] != "done":
        raise HTTPException(409, "The analysis is not finished.")
    return a["result"]


@app.get("/analysis/{aid}/report.json")
def report_json(aid: str):
    return _done(aid)


@app.get("/analysis/{aid}/report.csv")
def report_csv(aid: str):
    r = _done(aid)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["file", "method", "change", "start_line", "end_line", "cc_before", "cc_after", "pc_before", "pc_after"]
               + [f"{s}_{k}" for s in SMELLS for k in ("zone", "rule", "probability", "status")] + ["points", "status"])
    for m in r["methods"]:
        b, a = m["before"] or {}, m["after"] or {}
        w.writerow([m["file"], m["name"], m["change_type"], m["start_line"], m["end_line"], b.get("cc"), a.get("cc"),
                    b.get("pc"), a.get("pc")]
                   + [x for s in SMELLS for x in (m["smells"][s]["zone"], m["smells"][s]["rule"],
                                                   round(m["smells"][s]["probability"], 4), m["smells"][s]["status"])]
                   + [m["points"], m["status"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="codesniff-{aid}.csv"'})


@app.get("/analysis/{aid}/report.pdf")
def report_pdf_endpoint(aid: str):
    return Response(report_pdf(_done(aid)), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="codesniff-{aid}.pdf"'})


@app.get("/history")
def history(limit: int = 50):
    return store().history(min(max(limit, 1), 200))


@app.get("/findings")
def get_findings():
    return findings()


@app.get("/config")
def get_config():
    return config()


@app.get("/health")
def health():
    loaded = {s: type(model(s)).__name__ for s in SMELLS}
    return {"status": "ok", "version": __version__, "models": loaded,
            "model_commit": card()["CM"]["repository_commit"], "metrics": PRIMARY,
            "github_token": bool(os.environ.get("GITHUB_TOKEN"))}
