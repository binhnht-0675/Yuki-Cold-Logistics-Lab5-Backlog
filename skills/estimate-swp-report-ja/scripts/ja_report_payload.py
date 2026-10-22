"""The payload embedded in the JA report (source contract item 9 and "Embedded audit payload").

The JA report embeds the source report's validated payload with the SAME structure. Only the free-text
slots of FREE_TEXT_FIELDS are replaced, through TextPolicy (supplied translation > the original when it
needs none, e.g. Japanese or an identifier > the fixed omission note). `run.sourceLabel` (a display name that
may hold an organization or a private Project name; the header never shows it either) becomes the fixed
SOURCE_NEUTRAL text; the original HTML is traced by its sha256. Everything else stays as in the source
payload: numbers and axes, enum codes, signatures, refs, URLs, labels, run.sourceUrl (it passes the content
guard like every embedded string: render stops on a Project URL of another owner or an internal URL). An
issue `body` is never embedded (the contract forbids raw bodies; the source renderer drops it too). JSON is escaped like the source renderer: < > & U+2028 U+2029, so no
(case-insensitive) script-closing sequence can appear.
"""
from __future__ import annotations

import copy
import json
import re
from typing import Dict, List, Optional, Tuple

from ja_report_text import TextPolicy

PAYLOAD_ID = "report-data"
PAYLOAD_RX = re.compile(r'<script id="report-data" type="application/json">(.*?)</script>', re.S)
FREE_TEXT_FIELDS = ("issues[].title", "issues[].rationale", "issues[].assumptions[]", "issues[].gaps[]",
                    "issues[].splitReason", "issues[].supportingEvidence[]", "issues[].provenance.notes[]",
                    "issues[].assessorCheck.witness.rationale", "parents[].title", "parents[].provenance.notes[]",
                    "corrections[].rationale", "caveats[]")
SOURCE_NEUTRAL = "estimate-swp の評価結果（対象の名前は公開版に載せない。原本 HTML の sha256 で照合）"
LABEL_PATH = ("run", "sourceLabel")
_ROW_TEXT = ("title", "rationale", "splitReason")
_ROW_LISTS = ("assumptions", "gaps", "supportingEvidence")


def free_text_paths(payload: dict) -> List[tuple]:
    """Key paths of every free-text slot present in the payload (same order for the same structure)."""
    out: List[tuple] = []
    for group in ("issues", "parents"):
        for n, row in enumerate(payload.get(group) or []):
            out += [(group, n, f) for f in _ROW_TEXT if isinstance(row.get(f), str)]
            for f in _ROW_LISTS:
                out += [(group, n, f, k) for k, _ in enumerate(row.get(f) or [])]
            notes = (row.get("provenance") or {}).get("notes") or []
            out += [(group, n, "provenance", "notes", k) for k, _ in enumerate(notes)]
            witness = (row.get("assessorCheck") or {}).get("witness") or {}
            if isinstance(witness.get("rationale"), str):
                out.append((group, n, "assessorCheck", "witness", "rationale"))
    out += [("corrections", n, "rationale") for n, c in enumerate(payload.get("corrections") or [])
            if isinstance(c.get("rationale"), str)]
    out += [("caveats", k) for k, _ in enumerate(payload.get("caveats") or [])]
    return out


def replaced_paths(payload: dict) -> List[tuple]:
    """Every slot the JA payload may change: the free text plus run.sourceLabel."""
    label = isinstance((payload.get("run") or {}).get("sourceLabel"), str)
    return free_text_paths(payload) + ([LABEL_PATH] if label else [])


def get_at(obj, path: tuple):
    for step in path:
        obj = obj[step]
    return obj


def _set_at(obj, path: tuple, value) -> None:
    get_at(obj, path[:-1])[path[-1]] = value


def _drop_bodies(payload: dict) -> None:
    for row in (payload.get("issues") or []) + (payload.get("parents") or []):
        row.pop("body", None)


def embedded_copy(payload: dict, translations: Optional[Dict[str, str]]) -> Tuple[dict, TextPolicy]:
    """(payload to embed, its own TextPolicy: counts of translated / omitted payload texts)."""
    out, policy = copy.deepcopy(payload), TextPolicy(translations)
    for path in free_text_paths(out):
        value = get_at(out, path)
        if isinstance(value, str) and value:
            _set_at(out, path, policy(value))
    if LABEL_PATH in replaced_paths(out):
        _set_at(out, LABEL_PATH, SOURCE_NEUTRAL)
    _drop_bodies(out)
    return out, policy


def without_free_text(payload: dict) -> dict:
    """The payload with every replaced slot set to None and no body: the part that must stay identical."""
    out = copy.deepcopy(payload)
    for path in replaced_paths(out):
        _set_at(out, path, None)
    _drop_bodies(out)
    return out


def safe_json(value) -> str:
    """JSON for a <script type="application/json"> block (same escaping as the source _safe_json)."""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def payload_block(payload: dict, translations: Optional[Dict[str, str]]) -> str:
    data, _ = embedded_copy(payload, translations)
    return f'<script id="{PAYLOAD_ID}" type="application/json">{safe_json(data)}</script>'
