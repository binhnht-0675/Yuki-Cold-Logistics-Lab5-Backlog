"""Scope x Complexity stays out of the visible report (source contract, references/html-report.md:
"never render S x C notation or raw axis values anywhere visible — they live only in the embedded payload").

Visible = the page minus <script> / <style> and minus the collapsed 技術的な詳細 block (id="tech-details"),
which may name the bands, multipliers and valid values. In the rest:
- no data-v number whose field is an axis (…scope / …complexity; the band steps of an applied rule,
  `rule|n|scope` / `rule|n|complexity`, are allowed: contract item 6 phrases rules with band steps);
- fixed text (everything outside data-t) holds no "Scope", "Complexity" or "×";
- free text (data-t: translations, titles, reasons) holds no axis notation (AXIS_NOTATION_RX), e.g.
  "S5 × C3", "S×C", "Scope × Complexity", "Scope を 2", "複雑さが C3", and the band labels of assessor rationales
  ("Scope 3:", "Complexity 2", a lone "S5" / "C3" — never a reference such as "S3-04").
The 照合表 keeps S x C (verification record, not the report).
"""
from __future__ import annotations

import html
import re
from typing import List

TECH_DETAILS_ID = "tech-details"
AXIS_NOTATION_RX = re.compile(
    r"S\s*\d+\s*[×xX*]\s*C\s*\d+"
    r"|(?<![A-Za-z])S\s*[×xX]\s*C(?![A-Za-z])"
    r"|Scope\s*[×xX*]\s*Complexity"
    r"|(?:Scope|Complexity)\s*(?:を|は|が|=)\s*\d+"
    r"|(?:範囲|複雑さ)\s*(?:が|は|を|=|:|：)?\s*[SC]\d+"
    # band labels in assessor rationales ("Scope 3:", "Complexity 2", a lone "S5" / "C3"; not "S3-04"), 22/10
    r"|\b(?:Scope|Complexity)\s+\d+\b"
    r"|(?<![\w-])[SC]\d+(?![\w-])", re.I)
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
        hit = AXIS_NOTATION_RX.search(html.unescape(m.group(1)))
        if hit:
            out.append(f"自由記述「{hit.group(0)}」")
    fixed = html.unescape(re.sub(r"<[^>]+>", " ", _DATA_T_RX.sub(" ", body)))
    out += [f"固定文「{fixed[max(0, m.start() - 10):m.end() + 10].strip()}」" for m in FIXED_AXIS_RX.finditer(fixed)]
    return out


def without_axis_notation(text: str) -> str:
    """The text with every axis notation removed (a translation may leave those numbers out)."""
    return AXIS_NOTATION_RX.sub(" ", text or "")
