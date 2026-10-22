"""Issue rows and their expandable detail (contract: "Each issue row exposes at least ...").

Row: final SWP chip | issue | title + flags (split / closed / contested + A · B spread) + detail |
discipline | work type | confidence. No axis column: Scope / Complexity live only in the embedded payload
(source contract; ja_report_axis_guard checks it). Detail: score audit in plain words
(final SWP + difficulty; initial -> final only when the score changed), rationale, assumptions, gaps,
split reason, function / activity, provenance, calibration status, evidence status, assessor B.
"""
from __future__ import annotations

from typing import List, Tuple

from ja_report_assessor_blocks import badge_html, detail_html, spread_html
from ja_report_html_parts import e, link, ref_text, t, td, v
from ja_report_interaction import row_attrs
from ja_report_text import TextPolicy, difficulty, label, short_ref


def _score_audit(i: dict, L: dict) -> str:
    ref, level = i["issueRef"], e(difficulty(L, i.get("finalSWP")))
    final = v(f"issue|{ref}|dfinal", i.get("finalSWP"))
    if i.get("initialSWP") != i.get("finalSWP"):
        return f"点数: 初期 {v(f'issue|{ref}|dinitial', i.get('initialSWP'))} SWP → 校正後 {final} SWP（{level}）"
    return f"点数: {final} SWP（{level}）"


def _provenance(i: dict, L: dict) -> str:
    prov = i.get("provenance") or {}
    fields = "、".join(e(label(L, "provenanceField", f)) for f in prov.get("fields") or []) or "—"
    return (f"<p>取得: {e(label(L, 'retrievedVia', prov.get('retrievedVia')))} ・ "
            f"取得状況: {e(label(L, 'detailStatus', prov.get('detailStatus')))} ・ 取得した項目: {fields}</p>")


def issue_detail(i: dict, L: dict, T: TextPolicy) -> str:
    cal = i.get("calibration") or {}
    function = ref_text(i["functionRef"]) if i.get("functionRef") else "—"
    parts = [f"<p>{_score_audit(i, L)}"
             + f" ・ 根拠の種類: {e(label(L, 'evidenceStatus', i.get('evidenceStatus')))}"
             + f" ・ 校正: {e(label(L, 'issueCalibration', cal.get('status')))}</p>",
             f"<p>根拠: {t(T(i.get('rationale')))}</p>"]
    for name, key in (("前提", "assumptions"), ("不明点", "gaps")):
        items = [T(s) for s in i.get(key) or []]
        if items:
            parts.append(f"<p>{name}:</p><ul>" + "".join(f"<li>{t(s)}</li>" for s in items) + "</ul>")
    if i.get("splitRecommended"):
        parts.append(f'<p class="warn">分割の提案: {t(T(i.get("splitReason")))}</p>')
    parts.append(f"<p>機能: {function} ・ 作業: {e(label(L, 'activityType', i.get('activityType')))}</p>")
    parts.append(_provenance(i, L))
    parts.append(detail_html(i, L, T))
    return "<details><summary>詳細</summary>" + "".join(parts) + "</details>"


def issue_rows(issues: List[dict], L: dict, T: TextPolicy) -> Tuple[List[List[str]], List[str]]:
    """(cells per row, row attribute strings) for one issue group."""
    rows, attrs = [], []
    for i in issues:
        ref = i["issueRef"]
        title = T(i.get("title"))
        flags = ' <span class="warn">（分割提案）</span>' if i.get("splitRecommended") else ""
        flags += ' <span class="warn">（クローズ）</span>' if i.get("state") == "closed" else ""
        flags += badge_html(i) + spread_html(i)
        rows.append([td(v(f"issue|{ref}|final", i.get("finalSWP"), "chip"), True),
                     td(link(i.get("url"), ref)),
                     td(t(title) + flags + issue_detail(i, L, T)),
                     td(e(label(L, "discipline", i.get("primaryDiscipline")))),
                     td(e(label(L, "workType", i.get("workType")))),
                     td(e(label(L, "confidence", i.get("confidence"))))])
        attrs.append(row_attrs(i, short_ref(ref), title))
    return rows, attrs
