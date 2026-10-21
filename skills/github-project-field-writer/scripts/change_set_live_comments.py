"""Settle comment ops against the comments that are really on GitHub (read-only calls).

- post ("comment"): every one is checked, whatever the logs say. Already on the issue (same sha8 of the
  body) -> skip; not there (never posted, or deleted later by revert-from-log / by hand) -> post.
- delete ("comment-") with an id: id no longer on the issue -> already deleted, skip.
- delete without id (pending / failed / legacy log row): find by sha8 of the body. 0 -> never posted,
  skip; 1 -> delete that id; 2+ -> error, a person deletes it by hand (we cannot tell which one).
"""
from __future__ import annotations

import hashlib
from typing import Dict, List


def sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def issue_comments(runner, repo: str, number) -> List[dict]:
    out, page = [], 1
    while True:
        chunk = runner.api_json(f"repos/{repo}/issues/{number}/comments?per_page=100&page={page}") or []
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def check_comment_ops(runner, repo: str, ops: List[dict]) -> None:
    cache: Dict[object, List[dict]] = {}
    for o in ops:
        if not o.get("check") or o.get("error") or (o["same"] and o["kind"] != "comment"):
            continue
        o["check"] = False
        n = o["number"]
        if n not in cache:
            cache[n] = issue_comments(runner, repo, n)
        if o["kind"] == "comment":
            o["same"] = any(sha8((c.get("body") or "").replace("\r\n", "\n")) == o["new"] for c in cache[n])
            o["note"] = ""  # the log label of the offline diff no longer applies
            continue
        if o["ref"]:
            o["same"] = not any(str(c.get("id")) == o["ref"] for c in cache[n])
            continue
        found = [c for c in cache[n] if sha8((c.get("body") or "").replace("\r\n", "\n")) == o["old"]]
        if len(found) == 1:
            o["ref"] = str(found[0]["id"])
        elif not found:
            o["same"] = True
        else:
            o["error"] = f"同じ内容のコメントが {len(found)} 件あり、どれを消すか決められない（GitHub 上で手で削除）"
