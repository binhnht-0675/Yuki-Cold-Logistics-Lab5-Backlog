"""Diff a change-set against current Project values and apply only real changes (write-ahead log)."""
from __future__ import annotations

import urllib.parse
from typing import Dict, FrozenSet, List, Set, Tuple

from change_set_live_comments import sha8
from gh_runner import EXIT_RATE_LIMIT_STOP, RateLimitStop
from project_fields import set_item_field
from write_log import DONE, outcome_rows

FOREIGN = "この実行の値ではないので戻さない"

def same_value(old, new) -> bool:
    if old in (None, "") and new in (None, ""):
        return True
    if isinstance(old, (int, float)) and isinstance(new, (int, float)):
        return abs(float(old) - float(new)) < 1e-9
    return old == new


def change_set_entries(cs: dict):
    """Every string apply can publish: comments, added labels, text field values (numbers skipped)."""
    for c in cs.get("changes", []):
        k = c.get("key")
        yield k, "comment", c.get("comment") or ""
        yield from ((k, "label+", lab) for lab in c.get("addLabels") or [])
        yield from ((k, f, v) for f, v in (c.get("fields") or {}).items() if isinstance(v, str))


def plan_ops(cs: dict, snap: dict, posted: Set[Tuple[str, str]],
             unsure: FrozenSet[Tuple[str, str]] = frozenset()) -> List[dict]:
    """Ops with `check` must be settled against GitHub comments (check_comment_ops) before apply.
    Every comment to post has `check`: whether it is already on the issue is decided from the comments on
    GitHub, not from old log rows (a comment deleted by revert-from-log, or by hand, is posted again).
    `posted` / `unsure` (from the logs) only label the offline diff (`diff --snapshot`)."""
    by_key = {i["key"]: i for i in snap["items"] if i.get("key")}
    ops: List[dict] = []
    for c in cs["changes"]:
        item = by_key.get(c["key"])
        base = {"key": c["key"], "number": item["number"] if item else None,
                "itemId": item["itemId"] if item else None}
        if not item:
            ops.append(dict(base, kind="missing", field="-", old="", new="", same=False,
                            error="Project にない（key-map / スナップショットを確認）"))
            continue
        guard = c.get("ifCurrent") or {}  # revert: only while GitHub still holds the value the run wrote
        for field, new in (c.get("fields") or {}).items():
            old = item["fields"].get(field)
            foreign = field in guard and not same_value(old, guard[field])
            ops.append(dict(base, kind="field", field=field, old=old, new=new, same=foreign or same_value(old, new),
                            note=FOREIGN if foreign else ""))
        for flag, target in (("close", "CLOSED"), ("reopen", "OPEN")):
            if c.get(flag):
                foreign = bool(c.get("ifCurrentState")) and item["state"] != c["ifCurrentState"]
                ops.append(dict(base, kind="state", field="state", old=item["state"], new=target,
                                same=foreign or item["state"] == target, note=FOREIGN if foreign else ""))
        for lab in c.get("addLabels") or []:
            ops.append(dict(base, kind="label+", field="labels+", old="", new=lab, same=lab in item["labels"]))
        for lab in c.get("removeLabels") or []:
            ops.append(dict(base, kind="label-", field="labels-", old=lab, new="", same=lab not in item["labels"]))
        if c.get("comment"):
            h = sha8(c["comment"])
            ops.append(dict(base, kind="comment", field="comment", old="", new=h, body=c["comment"],
                            same=(c["key"], h) in posted, check=True,
                            note="ログでは投稿済み（apply は GitHub のコメントで確認）" if (c["key"], h) in posted else
                            "ログでは結果不明（apply は GitHub のコメントで確認）" if (c["key"], h) in unsure else ""))
        for d in c.get("deleteComments") or []:
            ops.append(dict(base, kind="comment-", field="comment-", old=d.get("sha8", ""), new="",
                            ref=str(d.get("id") or ""), same=False, check=True))
    return ops


def _show(v) -> str:
    if v is None or v == "":
        return "（空）"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def render_diff(ops: List[dict]) -> str:
    lines = ["| キー | # | 項目 | 旧 | 新 | 判定 |", "|---|---|---|---|---|---|"]
    for o in ops:
        verdict = "エラー: " + o["error"] if o.get("error") else (
            (o.get("note") or "同じ") if o["same"] else "変更（GitHub のコメントで確認）" if o.get("check") else "変更")
        lines.append(f"| {o['key']} | {o['number'] or '-'} | {o['field']} | {_show(o['old'])} | {_show(o['new'])} | {verdict} |")
    return "\n".join(lines)


def summary(ops: List[dict]) -> Dict[str, int]:
    return {"変更": sum(1 for o in ops if not o["same"] and not o.get("error")),
            "同じ": sum(1 for o in ops if o["same"]), "エラー": sum(1 for o in ops if o.get("error"))}


def execute(runner, ops: List[dict], fmap: dict, repo: str, log) -> int:
    """Each write: pending row on disk -> gh write -> done row (with the comment id) or failed row."""
    done = 0
    for o in ops:
        if o["same"] or o.get("error"):
            continue
        if o.get("check") or (o["kind"] == "comment-" and not o.get("ref")):
            raise ValueError(f"{o['key']}: コメントを GitHub で確認していないため書き込みません")
        n, ref = o["number"], o.get("ref", "")
        op = log.begin(o["key"], n, o["field"], o["old"], o["new"], ref=ref)
        try:
            if o["kind"] == "field":
                set_item_field(runner, fmap, o["itemId"], o["field"], o["new"])
            elif o["kind"] == "state":
                body = {"state": "closed", "state_reason": "completed"} if o["new"] == "CLOSED" else {"state": "open"}
                runner.api_json(f"repos/{repo}/issues/{n}", "PATCH", body, write=True)
            elif o["kind"] == "label+":
                runner.api_json(f"repos/{repo}/issues/{n}/labels", "POST", {"labels": [o["new"]]}, write=True)
            elif o["kind"] == "label-":
                runner.api_json(f"repos/{repo}/issues/{n}/labels/{urllib.parse.quote(o['old'], safe='')}", "DELETE", write=True)
            elif o["kind"] == "comment":  # text already passed content_guard (write-fields.py) before any write
                res = runner.api_json(f"repos/{repo}/issues/{n}/comments", "POST", {"body": o["body"]}, write=True)
                ref = (res or {}).get("id", "")
            elif o["kind"] == "comment-":
                runner.api_json(f"repos/{repo}/issues/comments/{ref}", "DELETE", write=True)
        except Exception as e:  # log the failed write with its exit code, then stop
            code = EXIT_RATE_LIMIT_STOP if isinstance(e, RateLimitStop) else getattr(e, "code", 1)
            log.write(o["key"], n, o["field"], o["old"], o["new"], exit_code=code, op=op, ref=ref)
            raise
        log.write(o["key"], n, o["field"], o["old"], o["new"], op=op, ref=ref)
        done += 1
    return done


def comment_marks(rows: List[dict]) -> Tuple[Set[Tuple[str, str]], FrozenSet[Tuple[str, str]]]:
    """(key, sha8) of comments surely posted (done row) / maybe posted (pending or failed, no done row)."""
    rows = [r for r in outcome_rows(rows) if r["field"] == "comment"]
    posted = {(r["key"], r["new"]) for r in rows if r["status"] == DONE}
    return posted, frozenset((r["key"], r["new"]) for r in rows if r["status"] != DONE) - posted


def comment_note(ops: List[dict]) -> str:
    n = sum(1 for o in ops if o["kind"] == "comment" and not o["same"] and not o.get("error"))
    if not n:
        return ""
    return (f"INFO コメント {n} 件を投稿します。ログにコメント id を残すので revert-from-log で削除できます"
            "（削除したコメントは元に戻せません）")


