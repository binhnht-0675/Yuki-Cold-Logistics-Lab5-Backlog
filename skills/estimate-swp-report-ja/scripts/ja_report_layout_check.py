"""Layout and translation checks: the JA report must hold exactly the markers a fresh render puts there.

check renders the payload again (same translations, same provenance) and compares the ordered list of
markers (data-v key + number, data-t text, data-x provenance) with the JA HTML. So a number cell cannot
be swapped for a data-t text, a cell cannot be dropped, and a data-t text must be the very text the
TextPolicy gives for that place (not just "some payload string").
Translations: every original must be a payload string, and the numbers (digits after NFKC) in a
translation must be the numbers of its original (same multiset; Japanese word order may differ).
"""
from __future__ import annotations

import html
import itertools
import re
import unicodedata
from typing import Dict, List, Set, Tuple

from ja_report_text import payload_strings

MARKER_RX = re.compile(r'<span(?: class="[^"]*")? data-(v|t|x)="([^"]*)">([^<]*)</span>')
NUMBER_RX = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def markers(doc: str) -> List[Tuple[str, str, str]]:
    return [(m.group(1), html.unescape(m.group(2)), html.unescape(m.group(3))) for m in MARKER_RX.finditer(doc)]


def value_keys(doc: str) -> Set[str]:
    return {key for kind, key, _ in markers(doc) if kind == "v"}


def _show(m) -> str:
    if m is None:
        return "（なし）"
    kind, key, text = m
    return f"data-{kind}={key if kind != 't' else '…'}「{text[:20]}」"


def layout_errors(ja_html: str, rendered: str) -> List[str]:
    """Positions where the JA report differs from a fresh render (missing, extra or swapped markers)."""
    out = []
    for n, (got, want) in enumerate(itertools.zip_longest(markers(ja_html), markers(rendered)), 1):
        if got != want:
            out.append(f"{n} 番目: 期待 {_show(want)} / 実際 {_show(got)}")
    return out


def numbers_in(text: str) -> List[str]:
    return sorted(NUMBER_RX.findall(unicodedata.normalize("NFKC", text or "")))


def translation_errors(translations: Dict[str, str], payload: dict) -> List[str]:
    known = payload_strings(payload)
    out = []
    for original, ja in translations.items():
        if original not in known:
            out.append(f"訳の原文が埋め込みデータにない「{original[:20]}」")
        elif numbers_in(original) != numbers_in(ja):
            out.append(f"訳文の数値が原文と違う（原文 {numbers_in(original)} / 訳文 {numbers_in(ja)}）「{ja[:20]}」")
    return out
