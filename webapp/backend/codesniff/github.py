"""GitHub REST access (optional token from env GITHUB_TOKEN) with clear error messages."""
import datetime
import io
import os
import re
import tarfile
import urllib.parse

import httpx

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
REPO_RE = re.compile(r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$")
COMMIT_RE = re.compile(r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/commit/(?P<sha>[0-9a-fA-F]{7,40})/?$")
PR_RE = re.compile(r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)(?:/.*)?$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


class GitHubError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def parse_target(repo_url=None, commit_sha=None, pr_url=None):
    """Normalise the user's input into {"kind": "pr"|"commit"|"latest", owner, repo, sha|number}."""
    text = (pr_url or "").strip() or (repo_url or "").strip()
    if not text:
        raise GitHubError(400, "Enter a GitHub repository URL, a commit URL or a pull-request URL.")
    m = PR_RE.match(text)
    if m:
        return {"kind": "pr", "owner": m["owner"], "repo": m["repo"], "number": int(m["number"])}
    m = COMMIT_RE.match(text)
    if m:
        return {"kind": "commit", "owner": m["owner"], "repo": m["repo"], "sha": m["sha"]}
    m = REPO_RE.match(text)
    if not m:
        raise GitHubError(400, "That is not a GitHub URL. Use https://github.com/<owner>/<repo>, a commit URL or a "
                               "pull-request URL.")
    sha = (commit_sha or "").strip()
    if sha and not SHA_RE.match(sha):
        raise GitHubError(400, "A commit SHA is 7 to 40 hexadecimal characters.")
    return {"kind": "commit" if sha else "latest", "owner": m["owner"], "repo": m["repo"], "sha": sha or None}


class GitHub:
    def __init__(self, token=None, client=None, timeout=30.0):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN") or None
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                   "User-Agent": "CodeSniff"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.http = client or httpx.Client(headers=headers, timeout=timeout, follow_redirects=True)

    def _check(self, r, what):
        if r.status_code < 400:
            return r
        remaining = r.headers.get("x-ratelimit-remaining")
        if r.status_code in (403, 429) and (remaining == "0" or "rate limit" in r.text.lower()):
            reset = r.headers.get("x-ratelimit-reset")
            when = (datetime.datetime.fromtimestamp(int(reset), datetime.timezone.utc).strftime("%H:%M UTC")
                    if reset and reset.isdigit() else "later")
            hint = "" if self.token else " Set GITHUB_TOKEN on the server to raise the limit from 60 to 5,000 requests/hour."
            raise GitHubError(429, f"GitHub API rate limit reached; it resets at {when}.{hint}")
        if r.status_code == 401:
            raise GitHubError(401, "GitHub rejected the token (401). Check GITHUB_TOKEN.")
        if r.status_code == 404:
            raise GitHubError(404, f"{what} was not found. Check the URL; private repositories need a GITHUB_TOKEN "
                                   "with access.")
        if r.status_code == 422:
            raise GitHubError(422, f"GitHub could not resolve {what} (422). Check the commit SHA.")
        raise GitHubError(r.status_code, f"GitHub returned HTTP {r.status_code} for {what}.")

    def api(self, path, what):
        try:
            r = self.http.get(API + path)
        except httpx.HTTPError as exc:
            raise GitHubError(503, f"Could not reach GitHub: {exc.__class__.__name__}.") from exc
        return self._check(r, what).json()

    def raw(self, owner, repo, sha, path):
        url = f"{RAW}/{owner}/{repo}/{sha}/{urllib.parse.quote(path)}"
        try:
            r = self.http.get(url)
        except httpx.HTTPError as exc:
            raise GitHubError(503, f"Could not download {path}: {exc.__class__.__name__}.") from exc
        if r.status_code == 404:
            return None
        return self._check(r, path).content.decode("utf-8", "replace")

    def repo(self, owner, repo):
        return self.api(f"/repos/{owner}/{repo}", f"Repository {owner}/{repo}")

    def commit(self, owner, repo, sha):
        return self.api(f"/repos/{owner}/{repo}/commits/{sha}", f"Commit {sha[:12]} in {owner}/{repo}")

    def pull(self, owner, repo, number):
        return self.api(f"/repos/{owner}/{repo}/pulls/{number}", f"Pull request #{number} in {owner}/{repo}")

    def compare(self, owner, repo, base, head):
        return self.api(f"/repos/{owner}/{repo}/compare/{base}...{head}", f"Comparison {base[:7]}...{head[:7]}")

    def tarball(self, owner, repo, sha, dest, max_bytes=200_000_000):
        """Download and safely extract the repository at `sha` into `dest`; returns the extracted root."""
        try:
            r = self.http.get(f"{API}/repos/{owner}/{repo}/tarball/{sha}")
        except httpx.HTTPError as exc:
            raise GitHubError(503, f"Could not download the repository: {exc.__class__.__name__}.") from exc
        self._check(r, f"Repository archive {owner}/{repo}@{sha[:7]}")
        if len(r.content) > max_bytes:
            raise GitHubError(413, "The repository archive is too large to scan.")
        root = os.path.realpath(dest)
        with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
            members = []
            for m in tf.getmembers():
                target = os.path.realpath(os.path.join(dest, m.name))
                if not (target == root or target.startswith(root + os.sep)) or m.issym() or m.islnk():
                    continue
                if m.isfile() and not m.name.endswith(".java"):
                    continue
                members.append(m)
            tf.extractall(dest, members=members)
        tops = [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))]
        return os.path.join(dest, tops[0]) if len(tops) == 1 else dest
