"""Labels, Vietnamese detection, payload shape, free-text policy and number formatting for the JA report."""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from typing import Dict, Optional, Set

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL_MAP_PATH = os.path.join(HERE, "..", "references", "label-map-ja.json")
SKILL_MD = os.path.join(HERE, "..", "SKILL.md")

# Vietnamese letters (precomposed), written as escapes so this public file holds no Vietnamese text.
VI_RX = re.compile("[\u00c0-\u00c3\u00c8-\u00ca\u00cc\u00cd\u00d2-\u00d5\u00d9\u00da\u00dd\u00e0-\u00e3"
                   "\u00e8-\u00ea\u00ec\u00ed\u00f2-\u00f5\u00f9\u00fa\u00fd\u0102\u0103\u0110\u0111"
                   "\u0128\u0129\u0168\u0169\u01a0\u01a1\u01af\u01b0\u1ea0-\u1ef9]")
# A Latin letter still followed by a combining mark after NFC (decomposed text that did not compose).
COMBINING_RX = re.compile("[A-Za-z][\u0300-\u036f]")
OMITTED = "（原文がベトナム語のため省略。原本 HTML を参照）"
GITHUB_ISSUE_RX = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/\d+$")
SCHEMA_VERSION, SCORING_MODEL_VERSION = "2.0", "swp-matrix-v2"


def load_labels() -> dict:
    with open(LABEL_MAP_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def skill_version() -> str:
    with open(SKILL_MD, encoding="utf-8") as fh:
        m = re.search(r'version:\s*"([^"]+)"', fh.read())
    return m.group(1) if m else "unknown"


def vi_count(text: str) -> int:
    """Vietnamese letters in NFC or NFD form (NFD text is composed first, leftovers counted too)."""
    t = unicodedata.normalize("NFC", text or "")
    return len(VI_RX.findall(t)) + len(COMBINING_RX.findall(t))


def check_payload_shape(payload: dict) -> None:
    """Raise ValueError (Japanese message) when the payload is not the version this skill reads."""
    for key, want in (("schemaVersion", SCHEMA_VERSION), ("scoringModelVersion", SCORING_MODEL_VERSION)):
        if payload.get(key) != want:
            raise ValueError(f"埋め込みデータの {key} が {payload.get(key)!r} です（本スキルは {want} のみ対応）")
    for group in ("issues", "parents", "representatives"):
        items = payload.get(group) or []
        if not isinstance(items, list) or any(not isinstance(i, dict) or not isinstance(i.get("issueRef"), str)
                                              for i in items):
            raise ValueError(f"埋め込みデータの {group} に issueRef のない項目があります")


def fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def approval(payload: dict, ref: str) -> dict:
    """Person's decision for a representative: corrections[] first, else issue.calibration.approved*.

    Returns {"scope", "complexity", "reason"}; values are None when the payload has none.
    """
    for c in payload.get("corrections") or []:
        if (c.get("representative") or {}).get("issueRef") == ref:
            return {"scope": c.get("approvedScope"), "complexity": c.get("approvedComplexity"),
                    "reason": c.get("rationale") or None}
    issue = next((i for i in payload.get("issues", []) if i.get("issueRef") == ref), {})
    cal = issue.get("calibration") or {}
    return {"scope": cal.get("approvedScope"), "complexity": cal.get("approvedComplexity"), "reason": None}


def payload_strings(payload) -> Set[str]:
    """Every string anywhere in the payload (free text shown in the JA report must be one of them)."""
    out: Set[str] = set()
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            out.add(cur)
        elif isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return out


class TextPolicy:
    """Pick the Japanese text for a free-text field.

    Order: supplied translation (exact original text -> JA) > original if it has no
    Vietnamese letters > a fixed omission note. Counts omissions for the caveats.
    """

    def __init__(self, translations: Optional[Dict[str, str]] = None):
        self.translations = translations or {}
        self.omitted = 0
        self.translated = 0

    def __call__(self, text: Optional[str]) -> str:
        if not text:
            return ""
        if text in self.translations:
            self.translated += 1
            return self.translations[text]
        if vi_count(text):
            self.omitted += 1
            return OMITTED
        return text


def label(labels: dict, group: str, value) -> str:
    return labels.get(group, {}).get(value, str(value))


def difficulty(labels: dict, swp) -> str:
    if swp is None:
        return "—"
    for upper, name in labels["difficulty"]:
        if swp <= upper:
            return name
    return labels["difficulty"][-1][1]


def safe_issue_url(url) -> Optional[str]:
    return url if isinstance(url, str) and GITHUB_ISSUE_RX.match(url) else None


def short_ref(ref: str) -> str:
    return "#" + ref.rsplit("#", 1)[1] if "#" in (ref or "") else (ref or "")
