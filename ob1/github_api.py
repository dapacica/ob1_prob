import base64
import os
import requests
from typing import Iterable

from ob1.utils.logging_utils import log

GH_API = "https://api.github.com"

# Global context optionally set by orchestrator
_repo_ctx = {"owner": None, "repo": None}


# ---------- Helpers ----------
def set_repo_context(owner: str | None = None, repo: str | None = None):
    """Optionally override GH_OWNER / GH_REPO values from environment."""
    if owner:
        _repo_ctx["owner"] = owner
    if repo:
        _repo_ctx["repo"] = repo


def _auth_headers():
    tok = os.getenv("GITHUB_TOKEN")
    if not tok:
        raise RuntimeError("GITHUB_TOKEN not set in environment")
    return {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _repo():
    owner = _repo_ctx["owner"] or os.getenv("GH_OWNER")
    repo = _repo_ctx["repo"] or os.getenv("GH_REPO")
    if not owner or not repo:
        raise RuntimeError("GH_OWNER / GH_REPO not set (in env or via set_repo_context)")
    return owner, repo


# ---------- Core GitHub API Calls ----------
def get_default_branch():
    owner, repo = _repo()
    r = requests.get(f"{GH_API}/repos/{owner}/{repo}", headers=_auth_headers())
    r.raise_for_status()
    return r.json()["default_branch"]


def get_branch_head_sha(branch: str) -> str:
    owner, repo = _repo()
    r = requests.get(
        f"{GH_API}/repos/{owner}/{repo}/git/refs/heads/{branch}",
        headers=_auth_headers(),
    )
    r.raise_for_status()
    return r.json()["object"]["sha"]


def create_branch(new_branch: str, base_branch: str | None = None) -> None:
    owner, repo = _repo()
    base_branch = base_branch or get_default_branch()
    base_sha = get_branch_head_sha(base_branch)
    r = requests.post(
        f"{GH_API}/repos/{owner}/{repo}/git/refs",
        headers=_auth_headers(),
        json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
    )
    # 422 if branch exists; treat as idempotent
    if r.status_code not in (201, 422):
        r.raise_for_status()


# ---------- Simple Contents API (for small sets of files) ----------
def put_file(branch: str, path: str, content_utf8: str, message: str):
    owner, repo = _repo()
    b64 = base64.b64encode(content_utf8.encode("utf-8")).decode("ascii")
    r = requests.put(
        f"{GH_API}/repos/{owner}/{repo}/contents/{path}",
        headers=_auth_headers(),
        json={
            "message": message,
            "content": b64,
            "branch": branch,
        },
    )
    r.raise_for_status()
    return r.json()


# ---------- Git DB API (multiple files per commit) ----------
def _get_commit_and_tree_sha(branch: str):
    owner, repo = _repo()
    sha = get_branch_head_sha(branch)
    r = requests.get(f"{GH_API}/repos/{owner}/{repo}/git/commits/{sha}", headers=_auth_headers())
    r.raise_for_status()
    j = r.json()
    return sha, j["tree"]["sha"]


def _create_blob(content_utf8: str) -> str:
    owner, repo = _repo()
    r = requests.post(
        f"{GH_API}/repos/{owner}/{repo}/git/blobs",
        headers=_auth_headers(),
        json={"content": content_utf8, "encoding": "utf-8"},
    )
    r.raise_for_status()
    return r.json()["sha"]


def _create_tree(base_tree_sha: str, entries: Iterable[dict]) -> str:
    owner, repo = _repo()
    r = requests.post(
        f"{GH_API}/repos/{owner}/{repo}/git/trees",
        headers=_auth_headers(),
        json={"base_tree": base_tree_sha, "tree": list(entries)},
    )
    r.raise_for_status()
    return r.json()["sha"]


def _create_commit(message: str, tree_sha: str, parent_commit_sha: str) -> str:
    owner, repo = _repo()
    r = requests.post(
        f"{GH_API}/repos/{owner}/{repo}/git/commits",
        headers=_auth_headers(),
        json={"message": message, "tree": tree_sha, "parents": [parent_commit_sha]},
    )
    r.raise_for_status()
    return r.json()["sha"]


def _update_branch_ref(branch: str, new_commit_sha: str):
    owner, repo = _repo()
    r = requests.patch(
        f"{GH_API}/repos/{owner}/{repo}/git/refs/heads/{branch}",
        headers=_auth_headers(),
        json={"sha": new_commit_sha, "force": False},
    )
    r.raise_for_status()


def commit_files_batch(branch: str, files: dict[str, str], message: str):
    """Create one commit containing all given files."""
    parent_sha, base_tree_sha = _get_commit_and_tree_sha(branch)
    entries = []
    for path, content in files.items():
        blob_sha = _create_blob(content)
        entries.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha,
        })
    tree_sha = _create_tree(base_tree_sha, entries)
    commit_sha = _create_commit(message, tree_sha, parent_sha)
    _update_branch_ref(branch, commit_sha)
    return commit_sha


def create_pr(title: str, head_branch: str, base_branch: str = None, body: str = "", draft: bool = False):
    owner, repo = _repo()
    base_branch = base_branch or get_default_branch()
    r = requests.post(
        f"{GH_API}/repos/{owner}/{repo}/pulls",
        headers=_auth_headers(),
        json={"title": title, "head": head_branch, "base": base_branch, "body": body, "draft": draft},
    )
    if r.status_code == 422:
        log(f"[GitHubAPI] PR creation failed: {r.text}")
    r.raise_for_status()
    return r.json()["html_url"]

