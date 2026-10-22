"""Checks of the payload embedded in the JA report (decision 3A; see ja_report_payload.py).

These checks carry the facts that are no longer shown as cells (Scope / Complexity of every issue, the
person-confirmed axes): the embedded payload must pass the source skill's validate_payload (axes in the
bands, SWP = matrix cell, parent rollups, calibration audit) and equal the original payload in every field
except the free text, which must be exactly the Japanese text of the same TextPolicy.
"""
from __future__ import annotations

import copy
import json
import re
from typing import Dict, List, Optional, Tuple

from ja_report_metrics import SRC_SCHEMA
from ja_report_payload import PAYLOAD_RX, embedded_copy, get_at, replaced_paths, without_free_text
from ja_report_text import vi_count

VALID = "埋め込みデータ（全項目）が原本スキルの validate_payload に合格"
SAME = "埋め込みデータの自由記述以外の全項目 = 原本の埋め込みデータ（Scope・Complexity・列挙値・署名を含む。issue 本文は入れない）"
TEXT = "埋め込みデータの自由記述 = 訳文（訳文表の原文 → 訳。日本語の原文と識別子はそのまま。対象の名前は固定の文）"
ROWS = "埋め込みデータの issue・親 = 表示した行（件数・識別子）"
SAFE = "埋め込みデータのエスケープ（< > & U+2028 U+2029）・issue 本文なし・ベトナム語の文字なし"
SHOWN_RX = {"issues": re.compile(r'data-v="issue\|([^|"]+)\|final"'),
            "parents": re.compile(r'data-v="parent\|([^|"]+)\|final"')}


_MISSING = object()


def _first_diff(a, b, path: str = "$") -> str:
    """Key path of the first difference (for the 照合表 detail)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            x, y = a.get(k, _MISSING), b.get(k, _MISSING)
            if x != y:
                return _first_diff(x, y, f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for n, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return _first_diff(x, y, f"{path}[{n}]")
    return path


def _same(emb: dict, payload: dict) -> Tuple[bool, str]:
    try:
        mine, theirs = without_free_text(emb), without_free_text(payload)
    except (AttributeError, KeyError, IndexError, TypeError):
        return False, "構造の違い"
    return (True, "") if mine == theirs else (False, "最初の違い " + _first_diff(mine, theirs))


def _valid(emb: dict) -> Tuple[bool, str]:
    try:
        SRC_SCHEMA.validate_payload(copy.deepcopy(emb))
    except Exception as err:  # SchemaError (code, path) or a shape error of the embedded JSON
        return False, f"{getattr(err, 'code', type(err).__name__)} {getattr(err, 'path', '')}".strip()
    return True, ""


def _rows(ja_html: str, emb: dict) -> List[str]:
    bad = []
    for group, rx in SHOWN_RX.items():
        shown, kept = sorted(rx.findall(ja_html)), sorted(r.get("issueRef") or "" for r in emb.get(group) or [])
        if shown != kept:
            bad.append(f"{group}: 表示 {len(shown)} / 埋め込み {len(kept)}")
    return bad


def payload_checks(ja_html: str, payload: dict, translations: Optional[Dict[str, str]]
                   ) -> Tuple[List[tuple], int]:
    """(checks, number of payload free texts left untranslated) for the embedded payload."""
    expected, policy = embedded_copy(payload, translations)
    m = PAYLOAD_RX.search(ja_html)
    try:
        emb = json.loads(m.group(1)) if m else None
    except ValueError:
        emb = None
    if not isinstance(emb, dict):
        return [(name, False, "埋め込みデータなし") for name in (VALID, SAME, TEXT, ROWS, SAFE)], policy.omitted
    ok_valid, why = _valid(emb)
    same, where = _same(emb, payload)
    try:
        wrong = [p for p in replaced_paths(expected) if get_at(emb, p) != get_at(expected, p)]
    except (AttributeError, KeyError, IndexError, TypeError):
        wrong = ["（構造の違い）"]
    rows = _rows(ja_html, emb)
    raw = m.group(1)
    unsafe = [c for c in ("<", ">", "&", "\u2028", "\u2029") if c in raw]
    bodies = sum(1 for r in (emb.get("issues") or []) + (emb.get("parents") or []) if "body" in r)
    checks = [(VALID, ok_valid, why),
              (SAME, same, where),
              (TEXT, not wrong, f"自由記述 {len(replaced_paths(expected))} 箇所、不一致 {len(wrong)}"
               + f"（訳文に置換 {policy.translated}・省略 {policy.omitted}）"),
              (ROWS, not rows, " / ".join(rows) or f"issue {len(emb.get('issues') or [])}・親 {len(emb.get('parents') or [])}"),
              (SAFE, not unsafe and not bodies and not vi_count(raw),
               f"未エスケープ {len(unsafe)} 種・本文 {bodies} 件・ベトナム語 {vi_count(raw)} 文字")]
    return checks, policy.omitted
