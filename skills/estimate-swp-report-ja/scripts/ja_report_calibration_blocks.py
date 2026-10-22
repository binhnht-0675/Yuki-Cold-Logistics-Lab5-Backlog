"""Calibration section (contract items 5 and 6): opening sentence in user terms, representatives table
(SWP chip, issue, title, difficulty level, selection reason in Japanese), user corrections as score
movements with their reach, applied rules per discipline / work-type group with band steps, and the
changed-row count. The approved SWP of a correction uses the source derive_swp (ja_report_metrics)."""
from __future__ import annotations

from typing import List

from ja_report_html_parts import REP_HEADERS, e, ref_text, rep_rows, t, table, v
from ja_report_metrics import approved_swp, metrics
from ja_report_text import TextPolicy, difficulty, label

OPENING = ("システムが全体を代表する issue を最大五件選び、担当者がそれぞれの難しさを五段階の難易度（とても易しい〜とても難しい）"
           "で確かめます。似た issue の点数は、その確認に合わせて調整されます。担当者の確定がない場合と、埋め込みデータに理由が"
           "ない場合は「—」です。")


def _sign(n) -> str:
    return "+" if isinstance(n, (int, float)) and n > 0 else ""


def correction_lines(payload: dict, L: dict, T: TextPolicy) -> List[str]:
    issues = {i["issueRef"]: i for i in payload.get("issues", [])}
    out = []
    for n, c in enumerate(payload.get("corrections") or []):
        ref = (c.get("representative") or {}).get("issueRef") or ""
        approved = approved_swp(c.get("approvedScope"), c.get("approvedComplexity"))
        reach = "この issue だけ" if c.get("issueSpecific") else "似た issue にも適用"
        reason = t(T(c.get("rationale")))
        out.append(f"{ref_text(ref)}: 初期 {v(f'corr|{n}|initial', (issues.get(ref) or {}).get('initialSWP'))} SWP → "
                   f"確定 {v(f'corr|{n}|approved', approved)} SWP（{e(difficulty(L, approved))}）・ {reach}"
                   + (f" ・ 理由: {reason}" if reason else ""))
    return out


def rule_lines(payload: dict, L: dict) -> List[str]:
    out = []
    for n, r in enumerate(payload.get("calibrationRules") or []):
        stratum = r.get("stratum") or {}
        scope, cx = r.get("scopeBandDelta"), r.get("complexityBandDelta")
        out.append(f"分野 {e(label(L, 'discipline', stratum.get('primaryDiscipline')))} ・ 作業種別 "
                   f"{e(label(L, 'workType', stratum.get('workType')))}: 範囲 {_sign(scope)}{v(f'rule|{n}|scope', scope)} 段、"
                   f"複雑さ {_sign(cx)}{v(f'rule|{n}|complexity', cx)} 段 — 代表 "
                   + "、".join(ref_text(x) for x in r.get("representativeRefs") or []))
    return out


def _list(items: List[str]) -> str:
    return "<ul>" + ("".join(f"<li>{x}</li>" for x in items) or "<li>なし</li>") + "</ul>"


def calibration_html(payload: dict, L: dict, T: TextPolicy) -> str:
    run = payload.get("run") or {}
    reps = payload.get("representatives") or []
    return ('<section id="calibration"><h2>校正（代表 issue の確認）</h2>'
            f"<p>{e(OPENING)}</p>"
            f"<p>状態: {e(label(L, 'runCalibration', run.get('calibrationStatus')))} ・ 校正で点数が変わった issue "
            f"{v('sum|count|changed', metrics(payload)['changed'])} 件 ・ 代表 issue {v('sum|count|reps', len(reps))} 件</p>"
            + (table(REP_HEADERS, rep_rows(payload, L, T)) if reps else "<p>代表 issue はありません（対象の issue なし）。</p>")
            + "<h3>担当者の修正（点数の動き）</h3>" + _list(correction_lines(payload, L, T))
            + "<h3>適用したルール（分野・作業種別ごと）</h3>" + _list(rule_lines(payload, L))
            + f"<p>修正 {v('sum|count|corrections', len(payload.get('corrections') or []))} 件 ・ "
            f"適用ルール {v('sum|count|rules', len(payload.get('calibrationRules') or []))} 件</p></section>")
