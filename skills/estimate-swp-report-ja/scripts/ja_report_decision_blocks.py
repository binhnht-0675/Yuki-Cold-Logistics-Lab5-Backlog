"""Decision-support blocks (contract item 3c): risk & action tables, team load, SWP-hours reference view.

Each risk row carries a concrete suggested action: a fixed Japanese sentence plus the recorded reason
(splitReason, the first gap, else the rationale) passed through the TextPolicy, so an untranslated
reason is omitted and fails `check`. The team table appears only when an issue has a team:* label.
The hours view shows the default rate (median hours/SWP from existing hour estimates, else 1); the
converted hours are written by the fixed script from the marked SWP values and never stored.
"""
from __future__ import annotations

from ja_report_html_parts import e, link, t, table, td, v
from ja_report_metrics import NO_TEAM, metrics
from ja_report_text import TextPolicy, label

RISK_HEAD = ["SWP", "issue", "タイトル", "対応の提案"]
SPLIT_ACTION = "独立した issue に分けてから、それぞれ見積もり直す。理由: "
LOW_ACTION = "チケットで次の点をはっきりさせる: "
BREAKDOWN_ACTION = "次の計画会議の前に、見積もれる子タスクに分解する。"
HOURS_ROWS = (("sum|total|swp", "全 issue の合計"), ("cat|planned|swp", "計画の合計"), ("cat|bug|swp", "不具合・手戻り"),
              ("sum|range|min", "不確かさの幅（最小）"), ("sum|range|max", "不確かさの幅（最大）"))


def _row(kind: str, item: dict, T: TextPolicy, action: str, swp=True):
    ref = item["issueRef"]
    cell = v(f"{kind}|{ref}|swp", item.get("finalSWP"), "chip") if swp else "—"
    return [td(cell, True), td(link(item.get("url"), ref)), td(t(T(item.get("title")))), td(action)]


def risks_html(payload: dict, L: dict, T: TextPolicy) -> str:
    issues, m = payload.get("issues", []), metrics(payload)
    splits = sorted((i for i in issues if i.get("splitRecommended")), key=lambda x: x["issueRef"])
    low = sorted((i for i in issues if i.get("confidence") == "low"), key=lambda x: (-x["finalSWP"], x["issueRef"]))
    needs = [p for p in payload.get("parents", []) if p.get("aggregationStatus") == "needs-breakdown"]
    if not (splits or low or needs):
        return ""
    out = ['<section id="risks"><h2>リスクと、見積もりを確定する前の対応</h2>']
    if splits:
        rows = [_row("rsplit", i, T, e(SPLIT_ACTION) + (t(T(i.get("splitReason"))) or "—")) for i in splits]
        out.append(f"<h3>分割の提案（{v('sum|split|count', len(splits))} 件、{v('sum|split|swp', m['split_swp'])} SWP）</h3>"
                   + table(RISK_HEAD, rows))
    if low:
        rows = [_row("rlow", i, T, e(LOW_ACTION) + t(T((i.get("gaps") or [i.get("rationale")])[0]))) for i in low]
        out.append(f"<h3>確信度「低」の issue（{v('sum|conf|low', len(low))} 件、{v('sum|low|swp', m['low_swp'])} SWP）</h3>"
                   + table(RISK_HEAD, rows))
    if needs:
        rows = []
        for p in needs:
            row = _row("rneeds", p, T, e(BREAKDOWN_ACTION), swp=False)
            row[2] = td(e(label(L, "issueType", p.get("issueType"))) + " " + t(T(p.get("title"))))
            rows.append(row)
        out.append(f"<h3>分解が必要な親（{v('sum|needs|count', len(needs))} 件。子タスクがまだない）</h3>"
                   + table(RISK_HEAD, rows))
    return "".join(out) + "</section>"


def team_html(payload: dict) -> str:
    teams = metrics(payload)["teams"]
    if not teams:
        return ""
    rows = []
    for name, (n, build, bug) in teams.items():
        shown = "（チーム未設定）" if name == NO_TEAM else t("team:" + name)  # an identifier, shown verbatim
        rows.append([td(shown), td(v(f"team|{name}|count", n), True), td(v(f"team|{name}|build", build), True),
                     td(v(f"team|{name}|bug", bug), True), td(v(f"team|{name}|total", build + bug), True)])
    out = '<section id="team"><h2>チーム別の負荷</h2>' + table(["チーム", "issue 数", "構築", "不具合・手戻り", "合計"], rows)
    if NO_TEAM in teams:
        out += (f"<p>{v(f'team|{NO_TEAM}|count', teams[NO_TEAM][0])} / {v('sum|count|issues', len(payload['issues']))}"
                " 件に team:* のラベルがない。ボードでチームのラベルを付けると、この表を実際の割り当てに使える。</p>")
    return out + "</section>"


def hours_html(payload: dict) -> str:
    m = metrics(payload)
    basis = (f"時間の見積もりがある issue {v('sum|hours|samples', m['samples'])} 件の「時間 ÷ SWP」の中央値"
             if m["samples"] else "時間の実績がないため既定値。チームで調整する")
    rows = [[td(e(name)), td(f'<output data-from="{e(key)}"></output>', True)] for key, name in HOURS_ROWS]
    return ('<section id="hours"><h2>時間への換算（参考値）</h2>'
            "<p>SWP を時間に換算した値は参考値で、約束ではありません。換算率は読む人が変えられ、どこにも保存しません。"
            f"既定の換算率: SWP ひとつあたり {v('sum|hours|rate', m['rate'])} 時間（{basis}）。</p>"
            "<noscript><p>JavaScript が無効なため、換算表は表示しません。</p></noscript>"
            '<div id="hours-view" hidden><label for="rate">換算率（時間 / SWP）</label> '
            f'<input id="rate" type="number" min="0.1" step="0.1" value="{e(m["rate"])}">'
            + table(["項目", "時間（参考値）"], rows) + "</div></section>")
