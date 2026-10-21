"""Render the tables result (see progress-report.py build()) as Japanese Markdown."""
from __future__ import annotations

from progress_tables import fmt, md_table


def _scope_lines(src: dict) -> list:
    head = (f"対象: Project「{src['title']}」" + (f"・イテレーション「{src['iteration']}」" if src["iteration"] else "")
            + f"・{'末端の issue のみ' if src['leafOnly'] else '親を含む'} {src['items']} 件")
    if src.get("repo"):
        head += f"（リポジトリ {src['repo']}）"
    lines = [head]
    if src["iteration"] and src.get("planSnapshot"):
        lines.append(f"集計範囲: 計画スナップショット（{src['planSnapshot']}）でこのイテレーションに入っていた issue と、"
                     f"現在このイテレーションにある issue。うち他のイテレーションへ移動 {src['movedOut']} 件も合計に含む。")
    elif src["iteration"]:
        lines.append("集計範囲: 現在このイテレーションにある issue だけ。他のイテレーションへ移った issue は合計に含まない"
                     "（計画の合計と照合するときは --plan-snapshot）。")
    else:
        lines.append("集計範囲: スナップショットの全 issue（イテレーションで絞らない）。")
    return lines


def _parent_check(pc: dict) -> list:
    out = ["### 親 = 子の合計の確認（スナップショット全体）"]
    if not pc["mismatches"]:
        out.append(f"親 {pc['checkedParents']} 件、すべて一致（SWP・見積時間）。")
        return out
    rows = [[m["key"], m["field"], "（空）" if m["parent"] is None else fmt(m["parent"]), fmt(m["childrenSum"]),
             m["note"]] for m in pc["mismatches"]]
    out.append(f"⚠ 不一致 {len(rows)} 行（終了コード 4）。この表の数字を報告に使う前に field-writer で直すこと。")
    out.append(md_table(["キー", "項目", "親の値", "子の合計", "備考"], rows))
    return out


def _status_state_note(rows: list) -> list:
    if not rows:
        return []
    table = md_table(["キー", "#", "Status", "状態", "ずれ"],
                     [[m["key"], str(m["number"]), m["status"] or "（未設定）", m["state"] or "-", m["problem"]] for m in rows])
    return [f"注意: Status と issue の状態（open / closed）が合わない issue が {len(rows)} 件あります。ステータス別の表は"
            " Status で、バーンダウンは「Status 完了 または クローズ済み」で数えるため、両者の数字がずれます。"
            "報告に使う前に issue を閉じる / Status を直してから撮り直すこと（--strict なら exit 5）。", table]


def to_markdown(r: dict) -> str:
    src = r["source"]
    parts = [f"<!-- 生成: github-project-progress-report / スナップショット {src['takenAt']} -->",
             "\n".join(_scope_lines(src))]
    st = r["status"]
    rows = [[s["status"], str(s["count"]), fmt(s["swp"]), s["note"]] for s in st]
    rows.append(["**合計**", str(sum(s["count"] for s in st)), fmt(sum(s["swp"] for s in st)), ""])
    parts += ["### ステータス別", md_table(["ステータス", "issue 数", "SWP 合計", "備考"], rows)]
    parts += _status_state_note(r.get("statusStateMismatch") or [])
    rows = [[e["epic"], str(e["count"]), str(e["done"]), fmt(e["swp"]), fmt(e["doneSwp"]), fmt(e["hours"])]
            for e in r["epics"]]
    parts += ["### エピック別", md_table(["エピック", "issue 数", "完了", "SWP 合計", "完了 SWP", "見積時間(h)"], rows)]
    rows = [[g["role"], str(g["count"]), fmt(g["swp"]), fmt(g["hours"])] for g in r["roles"]]
    parts += ["### 担当（仮）別", md_table(["担当（仮）", "issue 数", "SWP 合計", "見積時間(h)"], rows)]
    if "burndown" in r:
        rows = [[b["day"], fmt(b["ideal"]), fmt(b["remaining"]), fmt(b["doneToday"])] for b in r["burndown"]]
        parts += ["### バーンダウン（模擬）", md_table(["日付", "残 SWP（理想）", "残 SWP（模擬）", "当日完了 SWP"], rows),
                  f"完了日の出どころ: {r['burndownDateSource']}"]
    parts += _parent_check(r["parentCheck"])
    if r["missingSwp"]:
        parts.append(f"※ SWP 未設定の issue が {r['missingSwp']} 件あり、SWP 合計では 0 として数えています。")
    return "\n\n".join(parts) + "\n"
