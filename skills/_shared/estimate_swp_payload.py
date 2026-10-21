"""Read the validated audit payload embedded in a tkm:estimate-swp HTML report.

The report embeds `<script id="report-data" type="application/json">…</script>`
(JSON with <, >, & escaped as \\u003c etc., which json.loads restores).
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Optional, Tuple

PAYLOAD_RX = re.compile(r'<script id="report-data" type="application/json">(.*?)</script>', re.S)
# run.calibrationStatus values that mean the representative issues were reviewed. github-project-field-writer
# refuses to write an estimate from any other report; estimate-swp-report-ja `check` fails on any other.
REVIEWED_CALIBRATION = ("accepted", "calibrated")
REF_RX = re.compile(r"^(?:(?P<repo>[\w.-]+/[\w.-]+))?#(?P<num>\d+)$")


def extract_payload(html_text: str) -> dict:
    m = PAYLOAD_RX.search(html_text)
    if not m:
        raise ValueError('HTML に <script id="report-data"> の埋め込みデータがありません')
    data = json.loads(m.group(1))
    if not isinstance(data, dict) or "issues" not in data:
        raise ValueError("埋め込みデータの形式が想定と違います（issues がない）")
    return data


def read_report(path: str) -> Tuple[dict, str]:
    """Return (payload, sha256 of the HTML file bytes)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    return extract_payload(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def split_ref(ref: str) -> Tuple[Optional[str], Optional[int]]:
    """'owner/repo#42' -> ('owner/repo', 42); unknown shapes -> (None, None)."""
    m = REF_RX.match(ref or "")
    if not m:
        return None, None
    return m.group("repo"), int(m.group("num"))
