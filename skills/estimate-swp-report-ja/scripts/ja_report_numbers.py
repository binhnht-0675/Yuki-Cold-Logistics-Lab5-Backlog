"""Number checks for the JA report: marked numbers vs the payload, coverage, bare numbers, sums.

expected() recomputes every data-v key from the embedded payload (never from the JA HTML).
scan_markers() then removes every verified marker and the fixed texts; any digit left is a
bare number (FAIL).
"""
from __future__ import annotations

import html
import re
from typing import Dict, List, Set, Tuple

from ja_report_block_numbers import NOT_MINE, block_required_keys, expected_block
from ja_report_html import FIXED_TEXTS, group_issues
from ja_report_text import OMITTED, OMITTED_FOREIGN, approval, fmt, payload_strings, short_ref

DATA_V_RX = re.compile(r'<span(?: class="[^"]*")? data-v="([^"]+)">([^<]*)</span>')
DATA_T_RX = re.compile(r'<span data-t="1">([^<]*)</span>')
DATA_X_RX = re.compile(r'<span data-x="(file|sha)">([^<]*)</span>')
DIGIT_RX = re.compile(r"[0-9０-９]+")
# SWP only: the axes are not shown (they are checked in the embedded payload, ja_report_payload_check.py).
ISSUE_FIELDS = {"final": "finalSWP", "initial": "initialSWP"}


def expected(payload: dict, key: str, notes: Dict[str, int]):
    kind, ident, field = key.split("|")
    block = expected_block(payload, kind, ident, field)
    if block is not NOT_MINE:
        return block
    issues = {i["issueRef"]: i for i in payload.get("issues", [])}
    parents = {p["issueRef"]: p for p in payload.get("parents", [])}
    if kind == "sum":
        if (ident, field) == ("total", "swp"):
            return sum(i.get("finalSWP") or 0 for i in issues.values())
        if ident == "count":
            return len(payload.get({"issues": "issues", "parents": "parents", "corrections": "corrections",
                                    "rules": "calibrationRules"}[field]) or [])
        if ident == "conf":
            return sum(1 for i in issues.values() if i.get("confidence") == field)
        if ident == "split":
            return sum(1 for i in issues.values() if i.get("splitRecommended"))
        if ident == "needs":
            return sum(1 for p in parents.values() if p.get("aggregationStatus") == "needs-breakdown")
    if kind == "wt":
        group = [i for i in issues.values() if str(i.get("workType")) == ident]
        return len(group) if field == "count" else sum(i.get("finalSWP") or 0 for i in group)
    if kind == "group":
        return len(group_issues(payload)[ident])
    if kind == "note":
        return notes[ident]
    if kind in ("issue", "rep"):
        return issues[ident][ISSUE_FIELDS[field]]
    if kind == "parent":
        return len(parents[ident].get("childRefs") or []) if field == "children" else parents[ident].get("finalSWP")
    raise KeyError(key)


def required_keys(payload: dict) -> Set[str]:
    """Every number cell of every table (the checker also adds the data-v keys of a fresh render)."""
    need = {"sum|total|swp", "sum|count|issues", "sum|count|parents", "sum|conf|high", "sum|conf|medium",
            "sum|conf|low", "sum|split|count", "sum|needs|count", "sum|count|corrections", "sum|count|rules",
            "note|omitted|count", "note|translated|count"}
    for i in payload.get("issues", []):
        need.add(f"issue|{i['issueRef']}|final")
        need.add(f"wt|{i.get('workType')}|count")
        need.add(f"wt|{i.get('workType')}|swp")
    need |= {f"parent|{p['issueRef']}|{f}" for p in payload.get("parents", []) for f in ("final", "children")}
    for r in payload.get("representatives") or []:
        need.add(f"rep|{r['issueRef']}|initial")
        a = approval(payload, r["issueRef"])
        if a["scope"] is not None or a["complexity"] is not None:
            need.add(f"rep|{r['issueRef']}|final")
    need |= {f"group|{ref}|count" for ref, members in group_issues(payload).items() if members}
    return need | block_required_keys(payload)


def compare_numbers(ja_html: str, payload: dict, notes: Dict[str, int]) -> List[tuple]:
    rows = []
    for m in DATA_V_RX.finditer(ja_html):
        key, shown = html.unescape(m.group(1)), html.unescape(m.group(2))
        try:
            exp = fmt(expected(payload, key, notes))
        except (KeyError, ValueError, IndexError):
            exp = "（不明なキー）"
        rows.append((key, exp, shown, exp == shown))
    return rows


def scan_markers(ja_html: str, payload: dict, translations: Dict[str, str], provenance: Dict[str, str]
                 ) -> Tuple[List[str], List[str]]:
    """Return (unknown free texts / provenance, bare numbers with context)."""
    allowed = payload_strings(payload) | set(translations.values()) | {OMITTED, OMITTED_FOREIGN}
    allowed |= {short_ref(s) for s in allowed if "#" in s}
    unknown: List[str] = []
    for m in DATA_T_RX.finditer(ja_html):
        if html.unescape(m.group(1)) not in allowed:
            unknown.append(html.unescape(m.group(1))[:40])
    for m in DATA_X_RX.finditer(ja_html):
        if html.unescape(m.group(2)) != provenance.get(m.group(1)):
            unknown.append(f"{m.group(1)}: {html.unescape(m.group(2))[:40]}")
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", ja_html, flags=re.S | re.I)
    for rx in (DATA_V_RX, DATA_T_RX, DATA_X_RX):
        body = rx.sub(" ", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    for fixed in FIXED_TEXTS:
        body = body.replace(fixed, " ")
    bare = [body[max(0, m.start() - 12):m.end() + 4].strip() for m in DIGIT_RX.finditer(body)]
    return unknown, bare


def parent_sum_errors(payload: dict) -> List[str]:
    """'derived' parents must equal the sum of their children's finalSWP (issues or child parents).

    A child that is missing from the payload or has no finalSWP is an error too (never counted as 0).
    Parents with another aggregationStatus (e.g. needs-breakdown) are not checked."""
    swp = {x["issueRef"]: x.get("finalSWP") for x in payload.get("issues", []) + payload.get("parents", [])}
    bad = []
    for p in payload.get("parents", []):
        if p.get("aggregationStatus") != "derived":
            continue
        children = p.get("childRefs") or []
        lacking = [short_ref(c) for c in children if swp.get(c) is None]
        if lacking:
            bad.append(f"{short_ref(p['issueRef'])}: SWP のない子 {' '.join(lacking)}")
            continue
        total = sum(swp[c] for c in children)
        if p.get("finalSWP") != total:
            bad.append(f"{short_ref(p['issueRef'])}: {fmt(p.get('finalSWP'))} ≠ {total}")
    return bad


def approval_errors(payload: dict) -> List[str]:
    """A representative's confirmed axes must be the final axes (the person edits axes only)."""
    issues = {i["issueRef"]: i for i in payload.get("issues", [])}
    bad = []
    for r in payload.get("representatives") or []:
        a, i = approval(payload, r["issueRef"]), issues.get(r["issueRef"]) or {}
        if a["scope"] is None and a["complexity"] is None:
            continue
        if (a["scope"], a["complexity"]) != (i.get("finalScope"), i.get("finalComplexity")):
            bad.append(short_ref(r["issueRef"]))
    return bad

