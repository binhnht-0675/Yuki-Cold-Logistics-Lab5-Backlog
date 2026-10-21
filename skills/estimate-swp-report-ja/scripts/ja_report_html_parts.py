"""Cell / row builders for the JA report.

Markers the checker reads (ja_report_numbers.py):
  data-v="kind|id|field"  a number recomputed from the payload and compared
  data-t="1"              free text that must be a payload string, a supplied translation or the omission note
  data-x="file|sha"       the source file name / sha256 prefix (compared with the embedded provenance)
"""
from __future__ import annotations

import html
from typing import List

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


def table(headers: List[str], rows: List[List[str]]) -> str:
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def td(content: str, num: bool = False) -> str:
    return f'<td class="n">{content}</td>' if num else f"<td>{content}</td>"


def scs(prefix: str, scope, complexity, swp_key: str, swp) -> str:
    """'Scope × Complexity → SWP' with every number marked."""
    return f"{v(prefix + 'scope', scope)} × {v(prefix + 'complexity', complexity)} → {v(swp_key, swp)}"


def skill_cell(kind: str, i: dict) -> str:
    base = f"{kind}|{i['issueRef']}|"
    return scs(base + "i", i.get("initialScope"), i.get("initialComplexity"), base + "initial", i.get("initialSWP"))


def issue_detail(i: dict, L: dict, T: TextPolicy) -> str:
    cal = i.get("calibration") or {}
    parts = [f"<p>難易度: {e(difficulty(L, i.get('finalSWP')))}"
             + f" ・ 根拠の種類: {e(label(L, 'evidenceStatus', i.get('evidenceStatus')))}"
             + f" ・ 校正: {e(label(L, 'issueCalibration', cal.get('status')))}</p>",
             f"<p>根拠: {t(T(i.get('rationale')))}</p>"]
    for name, key in (("前提", "assumptions"), ("不明点", "gaps")):
        items = [T(s) for s in i.get(key) or []]
        if items:
            parts.append(f"<p>{name}:</p><ul>" + "".join(f"<li>{t(s)}</li>" for s in items) + "</ul>")
    if i.get("splitRecommended"):
        parts.append(f'<p class="warn">分割の提案: {t(T(i.get("splitReason")))}</p>')
    return "<details><summary>詳細</summary>" + "".join(parts) + "</details>"


ISSUE_HEADERS = ["SWP", "issue", "タイトル", "スキルの評価（Scope × Complexity → SWP）",
                 "確定（Scope × Complexity → SWP）", "分野", "作業種別", "確信度"]
REP_HEADERS = ["issue", "タイトル", "選定理由", "スキルの評価（Scope × Complexity → SWP）",
               "担当者の確定（Scope × Complexity → SWP）", "調整の理由"]


def issue_rows(issues: List[dict], L: dict, T: TextPolicy) -> List[List[str]]:
    rows = []
    for i in issues:
        ref = i["issueRef"]
        flag = ' <span class="warn">（分割提案）</span>' if i.get("splitRecommended") else ""
        final = scs(f"issue|{ref}|f", i.get("finalScope"), i.get("finalComplexity"), f"issue|{ref}|final2",
                    i.get("finalSWP"))
        rows.append([td(v(f"issue|{ref}|final", i.get("finalSWP"), "chip"), True),
                     td(link(i.get("url"), ref)),
                     td(t(T(i.get("title"))) + flag + issue_detail(i, L, T)),
                     td(skill_cell("issue", i)), td(final),
                     td(e(label(L, "discipline", i.get("primaryDiscipline")))),
                     td(e(label(L, "workType", i.get("workType")))),
                     td(e(label(L, "confidence", i.get("confidence"))))])
    return rows


def rep_rows(payload: dict, L: dict, T: TextPolicy) -> List[List[str]]:
    by_ref = {i["issueRef"]: i for i in payload.get("issues", [])}
    rows = []
    for r in payload.get("representatives") or []:
        ref = r["issueRef"]
        i = by_ref.get(ref) or {"issueRef": ref}
        a = approval(payload, ref)
        confirmed = ("—" if a["scope"] is None and a["complexity"] is None else
                     scs(f"rep|{ref}|a", a["scope"], a["complexity"], f"rep|{ref}|final", i.get("finalSWP")))
        rows.append([td(ref_text(ref)), td(t(T(i.get("title")))),
                     td(e("、".join(label(L, "selectionReason", s) for s in r.get("selectionReasons") or []))),
                     td(skill_cell("rep", i)), td(confirmed), td(t(T(a["reason"])) or "—")])
    return rows
