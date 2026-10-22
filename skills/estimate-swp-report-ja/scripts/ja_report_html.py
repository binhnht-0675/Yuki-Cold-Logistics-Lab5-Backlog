"""Render a self-contained Japanese HTML report from an estimate-swp payload (no network).

Every number shown carries data-v="kind|id|field" so the checker can compare it with the payload;
free text carries data-t and the provenance carries data-x (see ja_report_html_parts.py). The blocks
follow the source skill's report contract (references/html-report.md, "Required content" 1-9); the only
script is the fixed display script of ja_report_interaction.py (filters, sort, hours view). Scope and
Complexity are never shown (only inside the collapsed technical block, without per-issue values); the full
payload, with its free text in Japanese, is embedded as <script id="report-data"> (ja_report_payload.py).
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List

from ja_report_assessor_blocks import caveats_html as assessor_caveats, summary_html as agreement_summary
from ja_report_calibration_blocks import calibration_html
from ja_report_decision_blocks import hours_html, risks_html, team_html
from ja_report_html_parts import e, link, ref_text, t, table, td, v, x
from ja_report_interaction import CSS as INTERACTION_CSS, ISSUE_HEAD, SCRIPT, controls_html
from ja_report_issue_rows import issue_rows
from ja_report_axis_guard import TECH_DETAILS_ID
from ja_report_metrics import NO_PARENT, metrics
from ja_report_payload import SOURCE_NEUTRAL, payload_block, safe_json
from ja_report_summary_blocks import TECH, composition_html, diff_html, distribution_html, scope_html, summary_html
from ja_report_text import TextPolicy, canonical_sha256, label

CSS = """body{font-family:system-ui,'Hiragino Sans','Noto Sans JP',sans-serif;margin:0 auto;max-width:1100px;
padding:16px;color:#1f2328;background:#fff;line-height:1.6}h1{font-size:1.5rem}h2{font-size:1.2rem;
border-bottom:1px solid #d0d7de;margin-top:2rem}table{border-collapse:collapse;width:100%;margin:.5rem 0}
th,td{border:1px solid #d0d7de;padding:4px 8px;text-align:left;vertical-align:top}td.n{text-align:right}
.chip{display:inline-block;min-width:2.2em;text-align:center;border-radius:1em;background:#ddf4ff;font-weight:bold}
.meta{color:#57606a;font-size:.9rem}.warn{color:#9a6700}details{margin:.3rem 0}
@media print{details{display:block}}@media (prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}
.chip{background:#1f3a5f}th,td{border-color:#30363d}}""" + INTERACTION_CSS

METHOD = ("SWP（Standard Work Point）は、固定の基準表で付ける作業量の標準の点数です。"
          "同じ内容の issue には同じ点数が付き、点数が大きいほど作業が重くなります。エピック・ストーリーなどの親は、子の SWP の合計です。"
          "難易度の目安: 1–2 とても易しい、3–5 易しい、6–12 普通、13–25 難しい、26 以上 とても難しい。"
          "時間への換算は参考値で、約束ではありません。")
LOW_LEVEL_CAVEAT = ("処理レベル「低」: issue の内容だけで評価し、コードベースや専門家への確認はしていない。下書き・仕分け用。")
# run.sourceLabel is never shown (nor embedded): it may name an organization or a private Project.
# Fixed text whose digits are not data (explicit exclusions of the bare-number check).
FIXED_TEXTS = [METHOD, TECH, "sha256"]


def group_issues(payload: dict) -> Dict[str, List[dict]]:
    """Issues by parent ref (parents in payload order, then NO_PARENT); shared with the checker."""
    return OrderedDict((ref, rows) for ref, (rows, _sub) in metrics(payload)["groups"].items())


def _issue_section(payload: dict, L: dict, T: TextPolicy) -> str:
    issues, parents = payload.get("issues", []), payload.get("parents", [])
    titles = {p["issueRef"]: T(p.get("title")) for p in parents}
    out = ['<section id="issues"><h2>issue 一覧</h2><p>SWP は校正後の最終値です。校正で点数が変わった issue は、'
           "詳細に初期値も出します。JavaScript が使えるときは、検索・絞り込み・SWP での並べ替えができます。</p>"]
    if not issues:
        out.append("<p>対象の issue はありません。</p>")
    else:
        out.append(controls_html(issues, L))
    for ref, (members, subtotal) in metrics(payload)["groups"].items():
        if not members:
            continue
        head = f"{ref_text(ref)} {t(titles.get(ref, ''))}" if ref != NO_PARENT else "親のない issue"
        rows, attrs = issue_rows(members, L, T)
        out.append(f'<details class="group" open><summary>{head}（{v(f"group|{ref}|count", len(members))} 件 ・ 小計 '
                   f'{v(f"group|{ref}|swp", subtotal)} SWP）</summary>' + table([], rows, attrs, ISSUE_HEAD) + "</details>")
    return "".join(out) + "</section>"


def _parents_section(payload: dict, L: dict, T: TextPolicy) -> str:
    rows = [[td(link(p.get("url"), p["issueRef"])), td(t(T(p.get("title")))),
             td(e(label(L, "issueType", p.get("issueType")))), td(e(label(L, "aggregationStatus", p.get("aggregationStatus")))),
             td("、".join(ref_text(c) for c in p.get("childRefs") or []) or "—"),
             td(v(f"parent|{p['issueRef']}|children", len(p.get("childRefs") or [])), True),
             td(v(f"parent|{p['issueRef']}|initial", p.get("initialSWP")), True),
             td(v(f"parent|{p['issueRef']}|final", p.get("finalSWP")), True)] for p in payload.get("parents", [])]
    return ('<section id="parents"><h2>親（エピック・ストーリー）の集計</h2><p>親の SWP は子の SWP の合計で、直接は評価しない。'
            "「分解が必要」の親は点数を出さず、合計にも入れない。</p>"
            + table(["親", "タイトル", "種別", "集計", "子", "子の数", "初期 SWP", "SWP"], rows) + "</section>")


def render(payload: dict, L: dict, T: TextPolicy, source_name: str, source_sha: str) -> str:
    run, issues = payload.get("run") or {}, payload.get("issues", [])
    by_type: Dict[str, List[dict]] = OrderedDict()
    for i in issues:
        by_type.setdefault(i.get("workType"), []).append(i)
    out = [f"<h1>見積もりレポート（SWP）日本語版</h1><p class=\"meta\">出典: {e(SOURCE_NEUTRAL)}"
           f" ・ 原本の生成日時: {t(run.get('generatedAt'))} ・ 処理レベル: {e(label(L, 'processingLevel', run.get('processingLevel', 'medium')))}"
           f" ・ 校正: {e(label(L, 'runCalibration', run.get('calibrationStatus')))}<br>原本: {x('file', source_name)}"
           f"（sha256 {x('sha', source_sha[:16])}…）</p>", scope_html(payload, L),
           '<section id="summary">', "<h2>要約</h2>", summary_html(payload, L), agreement_summary(payload),
           composition_html(payload), "<h3>作業種別ごとの小計</h3>" + table(["作業種別", "件数", "SWP"], [
               [td(e(label(L, "workType", wt))), td(v(f"wt|{wt}|count", len(g)), True),
                td(v(f"wt|{wt}|swp", sum(i.get("finalSWP") or 0 for i in g)), True)] for wt, g in by_type.items()]),
           distribution_html(payload), diff_html(payload, L, T), "</section>",
           f'<section id="methodology"><h2>算定方法</h2><p>{e(METHOD)}</p><details id="{TECH_DETAILS_ID}"><summary>技術的な詳細（点数の求め方）'
           f"</summary><p>{e(TECH)}</p></details></section>",
           team_html(payload), risks_html(payload, L, T), hours_html(payload),
           _issue_section(payload, L, T), _parents_section(payload, L, T), calibration_html(payload, L, T)]
    caveats = [t(T(c)) for c in payload.get("caveats") or []]
    caveats += [e(LOW_LEVEL_CAVEAT)] if run.get("processingLevel") == "low" else []
    caveats += assessor_caveats(payload, L)
    out += ['<section id="caveats"><h2>注意事項</h2><ul>' + "".join(f"<li>{c}</li>" for c in caveats)
            + f"<li>訳のない記述 {v('note|omitted|count', T.omitted)} 件は省略、"
            + f"{v('note|translated|count', T.translated)} 件は日本語訳に置換しました（原本 HTML に原文あり）。</li>"
            + "<li>数値の照合結果は照合表（estimate-swp-verification-ja.md）を参照してください。</li></ul></section>"]
    data = {"sourceFile": source_name, "sourceSha256": source_sha, "sourcePayloadSha256": canonical_sha256(payload),
            "omittedTexts": T.omitted, "translatedTexts": T.translated}
    embedded = safe_json(data)
    return ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>見積もりレポート（SWP）日本語版</title><style>{CSS}</style></head><body>"
            + "\n".join(part for part in out if part)
            + f'\n<script id="report-data-ja" type="application/json">{embedded}</script>\n'
            + payload_block(payload, T.translations) + "\n"
            + f"<script>{SCRIPT}</script>\n</body></html>\n")
