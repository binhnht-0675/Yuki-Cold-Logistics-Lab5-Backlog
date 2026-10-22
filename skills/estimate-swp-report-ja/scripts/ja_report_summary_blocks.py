"""Summary blocks (contract items 1, 2, 3a, 3b): estimate summary with the uncertainty range and its formula,
explicit exclusions, stat tiles, planned-vs-rework composition, category subtotals, the SWP distribution,
the scope banner and the existing-estimate diff. Numbers come from ja_report_metrics (source formulas)."""
from __future__ import annotations

from typing import List

from ja_report_html_parts import e, link, ref_text, t, table, td, v
from ja_report_metrics import COMPLEXITY_BANDS, COMPLEXITY_MULTIPLIERS, SCOPE_BANDS, VALID_SWP, metrics
from ja_report_text import TextPolicy, label

RANGE_FORMULA = ("確信度が「高」の issue は点数のまま、「中」「低」の issue は有効な SWP の値の並びでひと段階下げた合計"
                 "〜ひと段階上げた合計。")


def _join(values) -> str:
    return ", ".join(str(x) for x in values)


TECH = (f"SWP は、範囲（Scope）の段階（{_join(SCOPE_BANDS)}）に、複雑さ（Complexity）の段階（{_join(COMPLEXITY_BANDS)}）"
        f"ごとの係数（{_join(COMPLEXITY_MULTIPLIERS)}）を掛けて四捨五入した値を、固定の表から引きます。"
        f"有効な値: {_join(VALID_SWP)}。確信度と過去の実績は点数を変えません。issue ごとの範囲と複雑さは埋め込みデータにあります。")
CATEGORIES = (("build", "構築", "計画の合計に入る"), ("test", "テスト・品質確認", "計画の合計に入る"),
              ("planned", "計画の合計", "構築＋テスト・品質確認"),
              ("bug", "不具合・手戻り", "別の小計（計画の合計には入れない）"), ("all", "全 issue の合計", "直接評価した issue すべて"))


def summary_html(payload: dict, L: dict) -> str:
    m, issues, parents = metrics(payload), payload.get("issues", []), payload.get("parents", [])
    total = sum(i.get("finalSWP") or 0 for i in issues)
    conf = {c: sum(1 for i in issues if i.get("confidence") == c) for c in ("high", "medium", "low")}
    needs = [p for p in parents if p.get("aggregationStatus") == "needs-breakdown"]
    splits = sum(1 for i in issues if i.get("splitRecommended"))
    rng = m["range"]
    items = [f"SWP 合計 {v('sum|total|swp', total)}（issue {v('sum|count|issues', len(issues))} 件 ・ オープン "
             f"{v('sum|state|open', m['state']['open'])} ・ クローズ {v('sum|state|closed', m['state']['closed'])}、"
             f"親 {v('sum|count|parents', len(parents))} 件）。うち不具合・手戻り {v('cat|bug|swp', m['cat']['bug'][1])} SWP。",
             f"不確かさの幅: {v('sum|range|min', rng['min'])}〜{v('sum|range|max', rng['max'])} SWP"
             f"（幅を付けた issue {v('sum|range|uncertain', rng['uncertain'])} 件）。求め方: {e(RANGE_FORMULA)}",
             (f"分解が必要な親 {v('sum|needs|count', len(needs))} 件は合計に含まない: "
              + "、".join(ref_text(p["issueRef"]) for p in needs) + "。分解すると実際の作業量は増える。") if needs else
             f"合計から除いた親はない（分解が必要な親 {v('sum|needs|count', 0)} 件）。",
             f"分割の提案 {v('sum|split|count', splits)} 件（{v('sum|split|swp', m['split_swp'])} SWP）。"
             f"確信度: 高 {v('sum|conf|high', conf['high'])} ・ 中 {v('sum|conf|medium', conf['medium'])} ・ "
             f"低 {v('sum|conf|low', conf['low'])}（確信度「低」の合計 {v('sum|low|swp', m['low_swp'])} SWP。"
             "チケットの情報が足りず、点数がずれることがある）。"]
    if not issues:
        items.append("対象の issue はありません（選んだ範囲に該当なし）。")
    out = "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    if issues:
        out += ('<div class="tiles">'
                f"<div class=\"tile\"><b>{v('sum|total|swp', total)}</b>SWP 合計（幅 {v('sum|range|min', rng['min'])}〜"
                f"{v('sum|range|max', rng['max'])}）</div>"
                f"<div class=\"tile\"><b>{v('sum|state|open', m['state']['open'])} / {v('sum|state|closed', m['state']['closed'])}"
                "</b>オープン / クローズ</div>"
                f"<div class=\"tile\"><b>{v('sum|conf|high', conf['high'])} / {v('sum|conf|medium', conf['medium'])} / "
                f"{v('sum|conf|low', conf['low'])}</b>確信度 高 / 中 / 低</div></div>")
    return out


def composition_html(payload: dict) -> str:
    m = metrics(payload)
    cat, pct = m["cat"], m["pct"]
    out = ""
    if cat["all"][1]:
        out += ('<div class="compbar" role="img" aria-label="計画と不具合・手戻りの割合">'
                f'<span class="seg-plan" style="flex:{max(cat["planned"][1], 1)}">計画 {v("cat|planned|swp", cat["planned"][1])}'
                f'（{v("cat|planned|pct", pct["planned"])}%）</span><span class="seg-bug" style="flex:{max(cat["bug"][1], 1)}">'
                f'不具合・手戻り {v("cat|bug|swp", cat["bug"][1])}（{v("cat|bug|pct", pct["bug"])}%）</span></div>')
    rows = [[td(e(name)), td(v(f"cat|{key}|count", cat[key][0]), True), td(v(f"cat|{key}|swp", cat[key][1]), True),
             td(e(note))] for key, name, note in CATEGORIES]
    return out + "<h3>区分ごとの小計（計画と不具合・手戻り）</h3>" + table(["区分", "件数", "SWP", "備考"], rows)


def distribution_html(payload: dict) -> str:
    dist = metrics(payload)["dist"]
    if not dist:
        return ""
    peak = max(dist.values())
    rows = [[td(v(f"dist|{swp}|value", swp), True), td(v(f"dist|{swp}|count", n), True),
             td(f'<span class="bar" style="width:{round(n * 100 / peak)}%" aria-hidden="true"></span>')]
            for swp, n in dist.items()]
    return "<h3>SWP の分布（点数ごとの issue 数）</h3>" + table(["SWP", "件数", "棒"], rows)


def scope_html(payload: dict, L: dict) -> str:
    sel = (payload.get("run") or {}).get("selection")
    if not sel:
        return ""
    filters = sel.get("filters") or {}
    active = [f"{name} " + "、".join(t(x) for x in filters.get(key) or [])  # identifiers, shown verbatim
              for key, name in (("sprints", "スプリント"), ("milestones", "マイルストーン"), ("labels", "ラベル"))
              if filters.get(key)]
    excluded = [f"{e(label(L, 'excludedGate', gate))} {v(f'sel|{gate}|count', n)} 件"
                for gate, n in (sel.get("excluded") or {}).items()]
    items = [f"クローズ済みの issue: {'含める' if sel.get('includeClosed') else '含めない'} ・ 既存の見積もりがある issue: "
             f"{'見積もり直す' if sel.get('reestimateExisting') else '対象外'}",
             f"状態の判定: {e(label(L, 'statusRule', sel.get('statusRule')))}",
             f"既存の見積もりの確認: {e(label(L, 'estimateCheck', sel.get('existingEstimateCheck')))}",
             "絞り込み: " + (" ・ ".join(active) or "なし"), "除外した issue: " + (" ・ ".join(excluded) or "なし")]
    return '<section id="scope"><h2>対象の範囲</h2><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul></section>"


def diff_html(payload: dict, L: dict, T: TextPolicy) -> str:
    diff = metrics(payload)["diff"]
    if not diff:
        return ""
    rows: List[List[str]] = []
    for i in diff:
        ref, old = i["issueRef"], i["existingEstimate"]
        if old.get("standardWorkPoint") is not None:
            delta = i["finalSWP"] - old["standardWorkPoint"]
            old_cell, delta_cell = f"{v(f'diff|{ref}|old', old['standardWorkPoint'])} SWP", (
                ("+" if delta > 0 else "") + v(f"diff|{ref}|delta", delta))
        else:
            old_cell, delta_cell = f"{v(f'diff|{ref}|hours', old.get('estimatedHours'))} 時間", "—"
        rows.append([td(link(i.get("url"), ref)), td(t(T(i.get("title")))), td(old_cell, True),
                     td(v(f"diff|{ref}|new", i["finalSWP"], "chip"), True), td(delta_cell, True),
                     td(e(label(L, "estimateSource", old.get("source"))))])
    return (f"<h3>既存の見積もりとの比較（{v('sum|diff|count', len(diff))} 件）</h3><p>どちらの数を使うかは人が決める。"
            "時間の見積もりは SWP に直接換算しないため、差は単位が同じときだけ出す。</p>"
            + table(["issue", "タイトル", "既存の見積もり", "新しい SWP", "差", "出所"], rows))
