"""Render a self-contained Japanese HTML report from an estimate-swp payload (no JS, no network).

Every number shown carries data-v="kind|id|field" so the checker can compare it with the payload;
free text carries data-t and the provenance carries data-x (see ja_report_html_parts.py).
"""
from __future__ import annotations

import json
from collections import OrderedDict
from typing import Dict, List

from ja_report_html_parts import (ISSUE_HEADERS, REP_HEADERS, e, issue_rows, link, ref_text, rep_rows, t, table,
                                  td, v, x)
from ja_report_text import TextPolicy, canonical_sha256, label

CSS = """body{font-family:system-ui,'Hiragino Sans','Noto Sans JP',sans-serif;margin:0 auto;max-width:1100px;
padding:16px;color:#1f2328;background:#fff;line-height:1.6}h1{font-size:1.5rem}h2{font-size:1.2rem;
border-bottom:1px solid #d0d7de;margin-top:2rem}table{border-collapse:collapse;width:100%;margin:.5rem 0}
th,td{border:1px solid #d0d7de;padding:4px 8px;text-align:left;vertical-align:top}td.n{text-align:right}
.chip{display:inline-block;min-width:2.2em;text-align:center;border-radius:1em;background:#ddf4ff;font-weight:bold}
.meta{color:#57606a;font-size:.9rem}.warn{color:#9a6700}details{margin:.3rem 0}
@media print{details{display:block}}@media (prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}
.chip{background:#1f3a5f}th,td{border-color:#30363d}}"""

METHOD = ("SWP（Standard Work Point）は、issue の「範囲（Scope）」と「複雑さ（Complexity）」を固定の表で組み合わせた"
          "作業量の指標です。同じ内容の issue には同じ点数が付きます。エピック・ストーリーなどの親は、子の SWP の合計です。"
          "難易度の目安: 1–2 とても易しい、3–5 易しい、6–12 普通、13–25 難しい、26 以上 とても難しい。")
# run.sourceLabel is never shown: it may name an organization or a private Project (public output).
SOURCE_NEUTRAL = "estimate-swp の評価結果（対象の名前は公開版に載せない。原本 HTML の sha256 で照合）"
# Fixed text whose digits are not data (explicit exclusions of the bare-number check).
FIXED_TEXTS = [METHOD, "sha256"]
NO_PARENT = "-"


def group_issues(payload: dict) -> Dict[str, List[dict]]:
    """Issues by parent ref (parents in payload order, then NO_PARENT); shared with the checker."""
    groups: Dict[str, List[dict]] = OrderedDict((p["issueRef"], []) for p in payload.get("parents", []))
    groups[NO_PARENT] = []
    for i in payload.get("issues", []):
        groups.setdefault(i.get("parentRef") or NO_PARENT, []).append(i)
    return groups


def render(payload: dict, L: dict, T: TextPolicy, source_name: str, source_sha: str) -> str:
    run, issues, parents = payload.get("run") or {}, payload.get("issues", []), payload.get("parents", [])
    total = sum(i.get("finalSWP") or 0 for i in issues)
    conf = {c: sum(1 for i in issues if i.get("confidence") == c) for c in ("high", "medium", "low")}
    needs = [p for p in parents if p.get("aggregationStatus") == "needs-breakdown"]
    splits = sum(1 for i in issues if i.get("splitRecommended"))
    out = [f"<h1>見積もりレポート（SWP）日本語版</h1><p class=\"meta\">出典: {e(SOURCE_NEUTRAL)}"
           f" ・ 原本の生成日時: {t(run.get('generatedAt'))} ・ 処理レベル: {e(label(L, 'processingLevel', run.get('processingLevel', 'medium')))}"
           f" ・ 校正: {e(label(L, 'runCalibration', run.get('calibrationStatus')))}<br>原本: {x('file', source_name)}"
           f"（sha256 {x('sha', source_sha[:16])}…）</p>",
           "<h2>要約</h2>",
           f"<p>SWP 合計 {v('sum|total|swp', total)}（issue {v('sum|count|issues', len(issues))} 件、"
           f"親 {v('sum|count|parents', len(parents))} 件）。確信度: 高 {v('sum|conf|high', conf['high'])} ・ "
           f"中 {v('sum|conf|medium', conf['medium'])} ・ 低 {v('sum|conf|low', conf['low'])}。"
           f"分割の提案 {v('sum|split|count', splits)} 件。分解が必要な親 {v('sum|needs|count', len(needs))} 件"
           + ("（合計に含まない: " + "、".join(ref_text(p["issueRef"]) for p in needs) + "）" if needs else "")
           + "。</p>", f"<h2>算定方法</h2><p>{e(METHOD)}</p>"]
    by_type: Dict[str, List[dict]] = OrderedDict()
    for i in issues:
        by_type.setdefault(i.get("workType"), []).append(i)
    out += ["<h2>作業種別ごとの小計</h2>", table(["作業種別", "件数", "SWP"], [
        [td(e(label(L, "workType", wt))), td(v(f"wt|{wt}|count", len(g)), True),
         td(v(f"wt|{wt}|swp", sum(i.get("finalSWP") or 0 for i in g)), True)] for wt, g in by_type.items()])]
    out += ["<h2>親（エピック・ストーリー）の集計</h2>", table(["親", "タイトル", "種別", "集計", "子の数", "SWP"], [
        [td(link(p.get("url"), p["issueRef"])), td(t(T(p.get("title")))),
         td(e(label(L, "issueType", p.get("issueType")))), td(e(label(L, "aggregationStatus", p.get("aggregationStatus")))),
         td(v(f"parent|{p['issueRef']}|children", len(p.get("childRefs") or [])), True),
         td(v(f"parent|{p['issueRef']}|final", p.get("finalSWP")), True)] for p in parents])]
    titles = {p["issueRef"]: T(p.get("title")) for p in parents}
    out.append("<h2>issue 一覧</h2><p>「スキルの評価」は estimate-swp が付けた初期値、「確定」は校正後の最終値です。</p>")
    for ref, members in group_issues(payload).items():
        if not members:
            continue
        head = f"{ref_text(ref)} {t(titles.get(ref, ''))}" if ref != NO_PARENT else "親なし"
        out.append(f"<details open><summary>{head}（{v(f'group|{ref}|count', len(members))} 件）</summary>"
                   + table(ISSUE_HEADERS, issue_rows(members, L, T)) + "</details>")
    out += ["<h2>校正（代表 issue の確認）</h2><p>代表として選んだ issue を担当者が確認し、似た issue に同じ修正を当てはめます。"
            "担当者の確定がない場合と、埋め込みデータに理由がない場合は「—」です。</p>",
            table(REP_HEADERS, rep_rows(payload, L, T)),
            f"<p>修正 {v('sum|count|corrections', len(payload.get('corrections') or []))} 件 ・ "
            f"適用ルール {v('sum|count|rules', len(payload.get('calibrationRules') or []))} 件</p>"]
    caveats = [T(c) for c in payload.get("caveats") or []]
    out += ["<h2>注意事項</h2><ul>" + "".join(f"<li>{t(c)}</li>" for c in caveats)
            + f"<li>ベトナム語の記述 {v('note|omitted|count', T.omitted)} 件は省略、"
            + f"{v('note|translated|count', T.translated)} 件は日本語訳に置換しました（原本 HTML に原文あり）。</li>"
            + "<li>数値の照合結果は照合表（estimate-swp-verification-ja.md）を参照してください。</li></ul>"]
    data = {"sourceFile": source_name, "sourceSha256": source_sha, "sourcePayloadSha256": canonical_sha256(payload),
            "omittedTexts": T.omitted, "translatedTexts": T.translated}
    embedded = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e")
    return ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>見積もりレポート（SWP）日本語版</title><style>{CSS}</style></head><body>"
            + "\n".join(out) + f'\n<script id="report-data-ja" type="application/json">{embedded}</script>\n</body></html>\n')
