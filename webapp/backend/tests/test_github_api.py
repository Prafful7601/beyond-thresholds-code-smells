"""GitHub error handling (mocked HTTP) and the API endpoints (TestClient with a fake GitHub)."""
import os

import httpx
import pytest
import respx

from codesniff.github import GitHub, GitHubError, parse_target
from conftest import APP

C1 = os.path.join(APP, "tests", "data", "commits", "c1")


# ------------------------------------------------------------------ parsing
@pytest.mark.parametrize("args, kind", [
    (("https://github.com/o/r",), "latest"),
    (("https://github.com/o/r.git", "abc1234"), "commit"),
    (("https://github.com/o/r/commit/abcdef1234567",), "commit"),
    ((None, None, "https://github.com/o/r/pull/12"), "pr"),
    (("https://github.com/o/r/pull/12/files",), "pr"),
])
def test_parse_target(args, kind):
    assert parse_target(*args)["kind"] == kind


@pytest.mark.parametrize("args", [(None,), ("https://gitlab.com/o/r",), ("https://github.com/o/r", "xyz")])
def test_parse_target_errors(args):
    with pytest.raises(GitHubError) as e:
        parse_target(*args)
    assert e.value.status == 400


# ------------------------------------------------------------------ HTTP errors
@respx.mock
def test_rate_limit_message():
    respx.get("https://api.github.com/repos/o/r").mock(return_value=httpx.Response(
        403, json={"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"}))
    with pytest.raises(GitHubError) as e:
        GitHub(token="").repo("o", "r")
    assert e.value.status == 429 and "rate limit" in e.value.message and "GITHUB_TOKEN" in e.value.message


@respx.mock
@pytest.mark.parametrize("code, status, text", [(404, 404, "private"), (401, 401, "token"), (422, 422, "SHA"),
                                                (500, 500, "HTTP 500")])
def test_http_errors(code, status, text):
    respx.get("https://api.github.com/repos/o/r/commits/abc1234").mock(return_value=httpx.Response(code, json={}))
    with pytest.raises(GitHubError) as e:
        GitHub(token="").commit("o", "r", "abc1234")
    assert e.value.status == status and text in e.value.message


@respx.mock
def test_network_error():
    respx.get("https://api.github.com/repos/o/r").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(GitHubError) as e:
        GitHub(token="").repo("o", "r")
    assert e.value.status == 503


@respx.mock
def test_raw_missing_file_returns_none_and_token_header():
    route = respx.get("https://raw.githubusercontent.com/o/r/abc/src/A.java").mock(return_value=httpx.Response(404))
    assert GitHub(token="t0k").raw("o", "r", "abc", "src/A.java") is None
    assert route.calls[0].request.headers["authorization"] == "Bearer t0k"


# ------------------------------------------------------------------ API
class FakeGitHub:
    FILES = {"before": open(os.path.join(C1, "before.java")).read(), "after": open(os.path.join(C1, "after.java")).read()}

    def repo(self, o, r):
        return {"default_branch": "main"}

    def commit(self, o, r, sha):
        if sha.startswith("bad"):
            raise GitHubError(404, "Commit not found. Check the URL; private repositories need a GITHUB_TOKEN with access.")
        return {"sha": "a" * 40, "html_url": "https://github.com/o/r/commit/" + "a" * 40, "parents": [{"sha": "b" * 40}],
                "commit": {"message": "Refactor pricing", "author": {"name": "Dev", "date": "2026-01-01T00:00:00Z"}},
                "files": [{"filename": "src/Pricing.java", "status": "modified"}, {"filename": "README.md", "status": "modified"}]}

    def raw(self, o, r, sha, path):
        return self.FILES["after" if sha == "a" * 40 else "before"]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main
    from codesniff.store import Store
    main.STATE["store"] = Store(str(tmp_path / "t.db"))
    main.STATE["github"] = FakeGitHub
    return TestClient(main.app)


def test_health_config_findings(client):
    h = client.get("/health").json()
    assert h["status"] == "ok" and set(h["models"]) == {"CM", "LPL"}
    cfg = client.get("/config").json()
    assert cfg["risk"]["params"]["high_above"] > cfg["risk"]["params"]["medium_from"]
    assert "not a probability of bugs" in cfg["risk"]["disclaimer"] and "MA" in cfg["excluded"]
    f = client.get("/findings").json()
    assert {"runs", "ceiling", "spec", "ablation", "links"} <= set(f) and f["ceiling"]["rows"]


def test_analyze_flow_cache_reports_history(client):
    r = client.post("/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "a" * 40})
    assert r.status_code == 202
    a = client.get(f"/analysis/{r.json()['id']}").json()
    assert a["status"] == "done" and a["result"]["summary"]["changed_methods"] == 2
    assert a["result"]["risk"]["small_sample"] and a["result"]["risk"]["band"] in {"Low", "Medium", "High"}
    second = client.post("/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "a" * 40}).json()
    assert client.get(f"/analysis/{second['id']}").json()["result"].get("cached") is True
    aid = r.json()["id"]
    assert client.get(f"/analysis/{aid}/report.json").json()["repo"] == "o/r"
    csv_text = client.get(f"/analysis/{aid}/report.csv").text
    assert csv_text.splitlines()[0].startswith("file,method,change")
    pdf = client.get(f"/analysis/{aid}/report.pdf")
    assert pdf.headers["content-type"] == "application/pdf" and pdf.content[:4] == b"%PDF"
    hist = client.get("/history").json()
    assert len(hist) == 2 and hist[0]["status"] == "done"


def test_analyze_errors(client):
    assert client.post("/analyze", json={"repo_url": "nope"}).status_code == 400
    assert client.post("/analyze", json={"repo_url": "https://github.com/o/r", "mode": "x"}).status_code == 400
    r = client.post("/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "bad1234"})
    a = client.get(f"/analysis/{r.json()['id']}").json()
    assert a["status"] == "error" and "not found" in a["error"]
    assert client.get("/analysis/doesnotexist").status_code == 404
    assert client.get(f"/analysis/{r.json()['id']}/report.json").status_code == 409


def test_routes_also_answer_under_api_prefix(client):
    assert client.get("/api/health").json()["status"] == "ok"
    r = client.post("/api/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "a" * 40})
    assert r.status_code == 202
    assert client.get(f"/api/analysis/{r.json()['id']}").json()["status"] == "done"
    assert client.get(f"/api/analysis/{r.json()['id']}/report.pdf").content[:4] == b"%PDF"
    assert client.get("/apiary").status_code == 404           # only the exact prefix segment is stripped
    assert "'/api/openapi.json'" in client.get("/api/docs").text


def test_inline_mode_returns_the_finished_analysis(client, monkeypatch):
    import main
    monkeypatch.setitem(main.STATE, "inline", True)
    r = client.post("/api/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "a" * 40})
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert r.json()["result"]["summary"]["changed_methods"] == 2
    bad = client.post("/api/analyze", json={"repo_url": "https://github.com/o/r", "commit_sha": "bad1234"})
    assert bad.status_code == 200 and bad.json()["status"] == "error" and "not found" in bad.json()["error"]
