"""Append-only CSV log for every GitHub write (no issue bodies, no secrets). Write-ahead:

    op = log.begin(key, number, field, old, new)   # status=pending, flushed to disk BEFORE the write
    ... the gh write ...
    log.write(key, number, field, old, new, op=op, ref=<id the write returned>)   # status=done
    (on error: log.write(..., exit_code=<code>, op=op) -> status=failed)

A pending row with no done / failed row of the same op means the process died between the write and
its log row: the write may or may not have reached GitHub, so readers must check GitHub, not guess.

Logs written before the status / op / ref columns existed (9 columns) are still read: read_log fills
status from exit_code (0 -> done, else failed).
A cell that starts with = + - @ is written with a leading ' so a spreadsheet does not run it as a formula
(CSV injection); read_log removes that quote again, so readers get the original value back. Appending to such a log first rewrites its header
(old rows kept, padded) so every row of one file has the same columns.
"""
from __future__ import annotations

import csv
import datetime as _dt
import os
import uuid
from typing import Any, Dict, Iterator, List, Optional

LEGACY_COLUMNS = ["timestamp", "skill", "command", "key", "number", "field", "old", "new", "exit_code"]
COLUMNS = LEGACY_COLUMNS + ["status", "op", "ref"]
PENDING, DONE, FAILED = "pending", "done", "failed"


FORMULA_START = "=+-@"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")[:200]
    if text[:1] in tuple(FORMULA_START) or (text[:1] == "'" and text[1:2] in tuple(FORMULA_START + "'")):
        return "'" + text  # a genuine leading ' before such a char is quoted too, so reading back is exact
    return text


def _uncell(text: str) -> str:
    return text[1:] if text[:1] == "'" and text[1:2] in tuple(FORMULA_START + "'") else text


def _status_of(exit_code: str) -> str:
    return DONE if exit_code == "0" else FAILED


def _migrate_legacy(path: str) -> None:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or rows[0] != LEGACY_COLUMNS:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for r in rows[1:]:
            r = (r + [""] * len(LEGACY_COLUMNS))[:len(LEGACY_COLUMNS)]
            w.writerow(r + [_status_of(r[-1]), "", ""])
    os.replace(tmp, path)


class WriteLog:
    def __init__(self, path: str, skill: str, command: str):
        self.path, self.skill, self.command = path, skill, command
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(COLUMNS)
        else:
            _migrate_legacy(path)

    def _append(self, key, number, field, old, new, exit_code: str, status: str, op: str, ref: Any) -> None:
        row = [
            _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
            self.skill, self.command, _cell(key), _cell(number), _cell(field),
            _cell(old), _cell(new), exit_code, status, op, _cell(ref),
        ]
        with open(self.path, "a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(row)
            fh.flush()
            os.fsync(fh.fileno())  # the pending row must be on disk before the write it announces

    def begin(self, key: Optional[str], number: Any, field: str, old: Any, new: Any, ref: Any = "") -> str:
        """Write-ahead row (status=pending) for a write that is about to be sent; returns its op id."""
        op = uuid.uuid4().hex[:12]
        self._append(key, number, field, old, new, "", PENDING, op, ref)
        return op

    def write(self, key: Optional[str], number: Any, field: str, old: Any, new: Any,
              exit_code: int = 0, op: str = "", ref: Any = "") -> None:
        """Outcome row: done (exit_code 0) or failed. Pass the op from begin() to close that pending row."""
        code = str(exit_code)
        self._append(key, number, field, old, new, code, _status_of(code), op or uuid.uuid4().hex[:12], ref)


def read_log(path: str) -> Iterator[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            row = {k: _uncell(v or "") for k, v in row.items() if k is not None}
            row.setdefault("exit_code", "")
            if not row.get("status"):
                row["status"] = _status_of(row["exit_code"])
            row.setdefault("op", "")
            row.setdefault("ref", "")
            yield row


def unresolved(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Pending rows whose op never got a done / failed row (the process died mid-write)."""
    closed = {r["op"] for r in rows if r["status"] != PENDING and r["op"]}
    return [r for r in rows if r["status"] == PENDING and r["op"] not in closed]


def outcome_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """One row per write: its done / failed row, or the pending row if nothing followed it."""
    closed = {r["op"] for r in rows if r["status"] != PENDING and r["op"]}
    return [r for r in rows if r["status"] != PENDING or r["op"] not in closed]
