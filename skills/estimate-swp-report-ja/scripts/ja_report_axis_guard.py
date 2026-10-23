"""Scope x Complexity stays out of the visible report (source contract, references/html-report.md:
"never render S x C notation or raw axis values anywhere visible — they live only in the embedded payload").

Visible = the page minus <script> / <style> and minus the collapsed 技術的な詳細 block (id="tech-details"),
which may name the bands, multipliers and valid values. In the rest:
- no data-v number whose field is an axis (…scope / …complexity; the band steps of an applied rule,
  `rule|n|scope` / `rule|n|complexity`, are allowed: contract item 6 phrases rules with band steps);
- fixed text (everything outside data-t) holds no "Scope", "Complexity" or "×";
- free text (data-t: translations, titles, reasons) holds no axis notation (AXIS_NOTATION_RX), e.g.
  "S5 × C3", "S×C", "Scope × Complexity", "Scope を 2", "複雑さが C3", and the band labels of assessor rationales
  ("Scope 3:", "Complexity 2", a lone "S5" / "C3" — never a reference such as "S3-04" nor a product such as
  "Amazon S3" / "S3 バケット") and, since the 22/10 review, "Scope: 3" and 「スコープ 3」「複雑度 2」「範囲 3」「複雑さ 2」
  when the number stands alone (followed by punctuation or the end — "Scope: 3 new tables" / 「範囲:3 セクション」 is a count).
Matching runs on the NFKC form, so full-width 「Ｓ５ × Ｃ３」 counts too.
The 照合表 keeps S x C (verification record, not the report).
"""
from __future__ import annotations

import html
import re
import unicodedata
from typing import List

TECH_DETAILS_ID = "tech-details"
# a band value stands alone: punctuation, "×" or the end follows (not "3 new tables" / 「3 セクション」 / 「2個」)
# (run 261023: "1,000" / "239/240" are counts — "," and "/" end a band value only when no digit follows)
_BAND_END = r"(?=\s*(?:$|[:;)\]、。」】×]|[.,/](?!\d)))"
AXIS_NOTATION_RX = re.compile(
    r"S\s*\d+\s*[×xX*]\s*C\s*\d+"
    r"|(?<![A-Za-z])S\s*[×xX]\s*C(?![A-Za-z])"
    r"|Scope\s*[×xX*]\s*Complexity"
    r"|(?:Scope|Complexity)\s*(?:を|は|が|=)\s*\d+"
    r"|(?:範囲|複雑さ)\s*(?:が|は|を|=|:)?\s*[SC]\d+"
    # band labels in assessor rationales ("Scope 3:", "Complexity 2", a lone "S5" / "C3"; not "S3-04"), 22/10
    r"|\b(?:Scope|Complexity)\s+\d+\b"
    # 22/10 review: "Scope: 3", 「スコープ 3」「複雑度 2」「範囲 3」「複雑さ 2」 — only a number that stands alone
    r"|(?<![A-Za-z])(?:Scope|Complexity|スコープ|複雑度|範囲|複雑さ|難易度)\s*(?::|=|を|は|が)?\s*\d+" + _BAND_END +
    # run 261023: a level word marks a band value 「難易度は水準2」; Vietnamese reviewer rationales
    # "<scope> 8, <difficulty> 1" / "<difficulty> at level 2" (a count such as "<scope> 3 tables" stays a count)
    r"|(?:スコープ|複雑度|範囲|複雑さ|難易度)\s*(?::|=|を|は|が)?\s*(?:水準|レベル|段階)\s*\d+"
    r"|(?<!\w)(?:ph\u1ea1m vi|\u0111\u1ed9 kh\u00f3)\s*(?::|=|l\u00e0)?\s*(?:\u1edf\s+)?m\u1ee9c\s*\d+"
    r"|(?<!\w)(?:ph\u1ea1m vi|\u0111\u1ed9 kh\u00f3)\s*(?::|=|l\u00e0)?\s*\d+" + _BAND_END +
    # a lone "S5" / "C3", but not the product "Amazon S3" / "AWS S3" / "S3 バケット" (22/10 review)
    r"|(?<!Amazon\s)(?<!AWS\s)(?<![\w-])[SC]\d+(?![\w-])(?!\s*(?:buckets?\b|バケット))", re.I)
FIXED_AXIS_RX = re.compile(r"Scope|Complexity|×", re.I)
_HIDDEN_RX = re.compile(r"<(script|style)\b.*?</\1>|<details id=\"" + TECH_DETAILS_ID + r"\">.*?</details>",
                        re.S | re.I)
_DATA_V_RX = re.compile(r'data-v="([^"]+)"')
_DATA_T_RX = re.compile(r'<span data-t="1">([^<]*)</span>')


def _axis_key(key: str) -> bool:
    parts = key.split("|")
    return len(parts) == 3 and parts[0] != "rule" and parts[2].endswith(("scope", "complexity"))


def visible_axis_errors(doc: str) -> List[str]:
    """Places where Scope / Complexity show outside the payload and the technical block."""
    body = _HIDDEN_RX.sub(" ", doc)
    out = [f"軸の値の欄 {html.unescape(k)}" for k in _DATA_V_RX.findall(body) if _axis_key(html.unescape(k))]
    for m in _DATA_T_RX.finditer(body):
        hit = AXIS_NOTATION_RX.search(_nfkc(html.unescape(m.group(1))))
        if hit:
            out.append(f"自由記述「{hit.group(0)}」")
    fixed = html.unescape(re.sub(r"<[^>]+>", " ", _DATA_T_RX.sub(" ", body)))
    out += [f"固定文「{fixed[max(0, m.start() - 10):m.end() + 10].strip()}」" for m in FIXED_AXIS_RX.finditer(fixed)]
    return out


def _nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def without_axis_notation(text: str) -> str:
    """The text (NFKC form) with every axis notation removed (a translation may leave those numbers out)."""
    return AXIS_NOTATION_RX.sub(" ", _nfkc(text))
