"""Stable backlog key <-> GitHub issue map, rebuilt from issue bodies.

Each issue body carries `<!-- backlog-key: E02-I03-S02 -->`. The map is always
rebuilt by listing every issue of the repository (GraphQL connection, not the
search index), so re-running a push never creates duplicates.
Only issues opened by the account running the skill (GraphQL `viewer`) may carry a key: on a public
repository anyone can open an issue, so a marker in someone else's issue is ignored with a WARN
(it can neither block the run as a duplicate nor be adopted as one of the backlog's issues).
That holds only while the viewer is the repository owner. When the viewer is NOT the owner and an issue by
another account carries a key, the run is probably under a second gh account (the backlog's issues were
opened by the owner): ignoring them would create every issue again, so OtherAccountError stops the run
before any write (push-backlog.py: exit 2).
Keys are limited to KEY_CHARS (the marker regex reads nothing else back).
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Dict, List, Optional

from gh_runner import GhRunner

KEY_CHARS = r"[A-Za-z0-9._-]+"
KEY_RX = re.compile(KEY_CHARS)
MARKER_RX = re.compile(r"<!--\s*backlog-key:\s*(" + KEY_CHARS + r")\s*-->")

REPO_ISSUES_QUERY = """
query($owner:String!, $name:String!, $after:String) {
  viewer { login }
  repository(owner:$owner, name:$name) {
    issues(first:100, after:$after, states:[OPEN, CLOSED], orderBy:{field:CREATED_AT, direction:ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id databaseId number state title body
        author { login }
        parent { number }
        labels(first:30) { nodes { name } }
        projectItems(first:20) { nodes { id project { id } } }
      }
    }
  }
}"""


def marker(key: str) -> str:
    return f"<!-- backlog-key: {key} -->"


def parse_key(body: Optional[str]) -> Optional[str]:
    m = MARKER_RX.search(body or "")
    return m.group(1) if m else None


def is_valid_key(key) -> bool:
    return isinstance(key, str) and KEY_RX.fullmatch(key) is not None


class OtherAccountError(Exception):
    """Issues with a key were opened by another account and the viewer is not the repository owner."""


def own_issues(issues: List[dict], viewer: Optional[str], printer: Callable[[str], None] = print,
               repo_owner: Optional[str] = None) -> List[dict]:
    """Drop every issue that carries a backlog key but was not opened by `viewer` (WARN per issue).
    With `repo_owner` given and viewer != owner, such an issue raises OtherAccountError instead."""
    if not viewer:
        raise RuntimeError("実行中のアカウント（viewer）を取得できないため、キーの持ち主を確認できません")
    kept, foreign = [], []
    for issue in issues:
        login = ((issue.get("author") or {}).get("login") or "").lower()
        key = parse_key(issue.get("body"))
        if key and login != viewer.lower():
            foreign.append(f"#{issue['number']}（{key}、作成者 {login or '不明'}）")
            printer(f"WARN #{issue['number']}: キー {key} の印がありますが、作成者が実行中のアカウントではないため無視します"
                    f"（作成者: {login or '不明'}）")
            continue
        kept.append(issue)
    if foreign and repo_owner and viewer.lower() != repo_owner.lower():
        raise OtherAccountError(
            f"別のアカウントで実行しています: 実行中のアカウント {viewer} はリポジトリの owner {repo_owner} ではなく、"
            f"ほかのアカウントが作ったキー付き issue が {len(foreign)} 件あります（{', '.join(foreign[:5])}）。"
            "このまま続けると同じキーの issue を作り直すため、書き込みの前に止めます。"
            f"`gh auth status` で {repo_owner} のアカウントに切り替えてから再実行してください")
    return kept


def list_repo_issues(runner: GhRunner, repo: str, printer: Callable[[str], None] = print) -> List[dict]:
    """Every issue of the repo (OPEN + CLOSED) minus the ones that carry a key but were opened by others."""
    owner, name = repo.split("/", 1)
    after, out, viewer = None, [], None
    while True:
        data = runner.graphql(REPO_ISSUES_QUERY, {"owner": owner, "name": name, "after": after})
        viewer = viewer or (data.get("viewer") or {}).get("login")
        conn = data["repository"]["issues"]
        out.extend(conn["nodes"])
        if not conn["pageInfo"]["hasNextPage"]:
            return own_issues(out, viewer, printer, repo_owner=owner)
        after = conn["pageInfo"]["endCursor"]


def build_key_map(issues: List[dict], project_id: Optional[str] = None) -> Dict[str, dict]:
    """Return {key: entry}; raise ValueError if two issues carry the same key."""
    result: Dict[str, dict] = {}
    dupes: List[str] = []
    for issue in issues:
        key = parse_key(issue.get("body"))
        if not key:
            continue
        if key in result:
            dupes.append(f"{key}: #{result[key]['number']} / #{issue['number']}")
            continue
        items = (issue.get("projectItems") or {}).get("nodes") or []
        item_id = next((n["id"] for n in items
                        if project_id is None or (n.get("project") or {}).get("id") == project_id), None)
        result[key] = {
            "number": issue["number"], "id": issue.get("databaseId"), "nodeId": issue.get("id"),
            "state": issue.get("state"), "parentNumber": (issue.get("parent") or {}).get("number"),
            "labels": sorted(n["name"] for n in ((issue.get("labels") or {}).get("nodes") or [])),
            "projectItemId": item_id,
        }
    if dupes:
        raise ValueError("同じ backlog-key を持つ issue が複数あります: " + ", ".join(dupes))
    return result


def load_key_map(path: str) -> Dict[str, dict]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("keys", {})


def save_key_map(path: str, repo: str, keys: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"repo": repo, "keys": dict(sorted(keys.items()))}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
