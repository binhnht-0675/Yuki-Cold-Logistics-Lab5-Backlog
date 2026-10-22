"""Cell / row builders for the JA report.

Markers the checker reads (ja_report_numbers.py):
  data-v="kind|id|field"  a number recomputed from the payload and compared
  data-t="1"              free text that must be a payload string, a supplied translation or the omission note
  data-x="file|sha"       the source file name / sha256 prefix (compared with the embedded provenance)
"""
from __future__ import annotations

import html
from typing import List, Optional

from ja_report_text import TextPolicy, approval, difficulty, fmt, label, safe_issue_url, short_ref


def e(text) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def v(key: str, value, cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<span{c} data-v="{e(key)}">{e(fmt(value))}</span>'


def t(text) -> str:
    return f'<span data-t="1">{e(text)}</span>' if text else ""


def x(kind: str, text) -> str:
    return f'<span data-x="{kind}">{e(text)}</span>'


def ref_text(ref: str) -> str:
    return t(short_ref(ref))


def link(url, ref: str) -> str:
    safe = safe_issue_url(url)
    return f'<a href="{e(safe)}" rel="noreferrer">{ref_text(ref)}</a>' if safe else ref_text(ref)


def table(headers: List[str], rows: List[List[str]], row_attrs: Optional[List[str]] = None,
          raw_head: Optional[str] = None) -> str:
    """A table in a horizontally scrollable wrapper; row_attrs are pre-escaped attribute strings."""
    head = raw_head or "".join(f"<th>{e(h)}</th>" for h in headers)
    attrs = row_attrs or [""] * len(rows)
    body = "".join(f"<tr{a}>" + "".join(r) + "</tr>" for a, r in zip(attrs, rows))
    return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def td(content: str, num: bool = False) -> str:
    return f'<td class="n">{content}</td>' if num else f"<td>{content}</td>"


# Scores as SWP only: the axes (Scope / Complexity) stay in the embedded payload and the 照合表.
REP_HEADERS = ["SWP", "issue", "タイトル", "難易度", "選定理由", "スキルの評価（SWP）", "担当者の確定（SWP）", "調整の理由"]


def rep_rows(payload: dict, L: dict, T: TextPolicy) -> List[List[str]]:
    by_ref = {i["issueRef"]: i for i in payload.get("issues", [])}
    rows = []
    for r in payload.get("representatives") or []:
        ref = r["issueRef"]
        i = by_ref.get(ref) or {"issueRef": ref}
        a = approval(payload, ref)
        confirmed = ("—" if a["scope"] is None and a["complexity"] is None else v(f"rep|{ref}|final", i.get("finalSWP")))
        rows.append([td(v(f"rep|{ref}|chip", i.get("finalSWP"), "chip"), True), td(link(i.get("url"), ref)),
                     td(t(T(i.get("title")))), td(e(difficulty(L, i.get("finalSWP")))),
                     td(e("、".join(label(L, "selectionReason", s) for s in r.get("selectionReasons") or []))),
                     td(v(f"rep|{ref}|initial", i.get("initialSWP")), True), td(confirmed, True),
                     td(t(T(a["reason"])) or "—")])
    return rows
