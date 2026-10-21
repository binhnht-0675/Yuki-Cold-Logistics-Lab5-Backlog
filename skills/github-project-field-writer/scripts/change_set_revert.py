"""revert-from-log: turn ONE run's log into a change-set that restores what that run changed.

Every write of the run counts, whatever its outcome row says: done, failed (effect may be unknown) and
pending with no outcome (the process died between the write and its log row). The change-set only
names the target; apply diffs it against the live Project / issue comments, so a write that never
reached GitHub shows up as "same" and is skipped - nothing is guessed from the log alone.
Every restore is conditional on GitHub still holding what this run wrote, done row or not:
- field: `ifCurrent` = the last value this run wrote; another value on GitHub -> skipped (WARN in the diff).
- state: `ifCurrentState` = the state this run left; labels: removed only while still on the issue,
  re-added only while still absent (the label op's own "same" check).
Labels are handled one by one (every label of an issue, not only the first).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from change_set_builders import SCHEMA, now
from write_log import DONE, outcome_rows


def _ident(r: dict) -> Tuple[str, str, str]:
    """(key, field, label name): every label is its own target; other fields have one per issue."""
    name = r["new"] if r["field"] == "labels+" else r["old"] if r["field"] == "labels-" else ""
    return r["key"], r["field"], name


def revert_change_set(rows: List[dict], fmap: dict, skill: str) -> Tuple[dict, List[str]]:
    """First write per target -> its old value (only while GitHub holds this run's last value);
    every posted comment -> delete (by id, else by sha8)."""
    first: Dict[Tuple[str, str, str], dict] = {}
    last: Dict[Tuple[str, str, str], dict] = {}
    comments: Dict[Tuple[str, str], str] = {}
    warns: List[str] = []
    for r in outcome_rows(rows):
        if r["field"].startswith("#") or r["skill"] != skill or r["command"] not in ("apply", "revert-from-log"):
            continue
        if r["field"] == "comment":
            ref = r["ref"] if r["status"] == DONE else ""
            if ref or (r["key"], r["new"]) not in comments:
                comments[(r["key"], r["new"])] = ref
        elif r["field"] == "comment-":
            warns.append(f"{r['key']}: 削除したコメントは元に戻せません（ログに本文を残さないため）")
        else:
            first.setdefault(_ident(r), r)
            last[_ident(r)] = r
    changes: Dict[str, dict] = {}
    for ident, r in first.items():
        key, field, _name = ident
        c = changes.setdefault(key, {"key": key, "fields": {}})
        if field == "state":
            c["reopen" if r["old"] == "OPEN" else "close"] = True
            c["ifCurrentState"] = last[ident]["new"]
        elif field == "labels+":
            c.setdefault("removeLabels", []).append(r["new"])
        elif field == "labels-":
            c.setdefault("addLabels", []).append(r["old"])
        else:
            c["fields"][field] = _typed(fmap, field, r["old"])
            c.setdefault("ifCurrent", {})[field] = _typed(fmap, field, last[ident]["new"])
    for (key, digest), ref in comments.items():
        c = changes.setdefault(key, {"key": key, "fields": {}})
        c.setdefault("deleteComments", []).append({"id": ref, "sha8": digest})
    return {"schema": SCHEMA, "source": {"kind": "revert", "createdAt": now()},
            "changes": [c for c in changes.values() if len(c) > 2 or c["fields"]]}, warns


def _typed(fmap: dict, field: str, raw: str) -> Optional[object]:
    if raw == "":
        return None
    if fmap["fields"].get(field, {}).get("type") == "number":
        v = float(raw)
        return int(v) if v.is_integer() else v
    return raw
