"""One write log per change-set run, so revert-from-log undoes exactly that run.

Default path: <state-dir>/write-logs/<change-set name>-<sha8 of its changes>.csv. Re-applying the same
change-set appends to the same log (resume after exit 75); a different change-set gets its own log.
A first row with field "#run" records the change-set name and its review stamp (not a write).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
from typing import Dict, List

from write_log import read_log

LEGACY_LOG = "field-write-log.csv"
META_FIELD = "#run"


def default_log_path(state_dir: str, change_set_path: str, cs: dict) -> str:
    stem = os.path.splitext(os.path.basename(change_set_path))[0]
    digest = hashlib.sha256(json.dumps(cs.get("changes", []), ensure_ascii=False, sort_keys=True)
                            .encode("utf-8")).hexdigest()[:8]
    return os.path.join(state_dir, "write-logs", f"{stem}-{digest}.csv")


def all_log_rows(state_dir: str, extra: str) -> List[Dict[str, str]]:
    """Rows of every field-writer log in the state dir (used to never post the same comment twice)."""
    paths = set(glob.glob(os.path.join(state_dir, "write-logs", "*.csv")))
    paths |= {p for p in (os.path.join(state_dir, LEGACY_LOG), extra) if os.path.exists(p)}
    rows: List[Dict[str, str]] = []
    for p in sorted(paths):
        rows.extend(read_log(p))
    return rows


def write_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [r for r in rows if not r.get("field", "").startswith("#")]


def write_run_meta(log, change_set_path: str, cs: dict) -> None:
    src = cs.get("source") or {}
    review = src.get("review") or {}
    note = ";".join(f"{k}={v}" for k, v in (("kind", src.get("kind")), ("reviewedBy", review.get("reviewedBy")),
                                            ("reviewedAt", review.get("reviewedAt")), ("sha256", src.get("sha256")))
                    if v)
    log.write("-", "", META_FIELD, os.path.basename(change_set_path), note)
