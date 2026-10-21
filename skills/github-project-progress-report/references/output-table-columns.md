# 出力する表の列

すべて同じ「対象集合」から計算する（既定: 末端の issue。`--iteration` 指定時はそのイテレーションのみ、
`--plan-snapshot` もあれば計画時点でそのイテレーションにあった issue を加える）。表の上の「集計範囲」に範囲を書く。

## ステータス別
| 列 | 意味 |
|---|---|
| ステータス | Project の `Status`。順序は 未着手 → 進行中 → レビュー中 → 完了 → ブロック中 → その他。空は「（未設定）」 |
| issue 数 | その Status の issue 数 |
| SWP 合計 | `SWP` フィールドの合計（空は 0） |
| 備考 | クローズ済みの件数（ある場合） |
最終行は合計。未着手・進行中・完了は 0 件でも行を出す。

### 注意（Status と issue の状態のずれ。あるときだけ）
ステータス別の表の下に「注意: Status と issue の状態（open / closed）が合わない issue が N 件あります。…」の行と、次の表を出す:
| 列 | 意味 |
|---|---|
| キー / # | ずれた issue のキー（なければ #番号）と番号 |
| Status / 状態 | Project の `Status` と issue の `OPEN` / `CLOSED` |
| ずれ | 「Status 完了 だが未クローズ」または「クローズ済みだが Status ≠ 完了」 |
既定は exit 0（標準エラーに WARN）、`--strict` なら exit 5。

## エピック別
親をたどった最上位の issue（エピック）ごとに: issue 数、完了数（Status = 完了）、SWP 合計、完了 SWP、見積時間(h) 合計。

## 担当（仮）別
`担当（仮）` ごとに: issue 数、SWP 合計、見積時間(h) 合計。チームの負荷の偏りを見る用。

## バーンダウン（模擬）
| 列 | 意味 |
|---|---|
| 日付 | `sprint-days.json` の `days`（YYYY-MM-DD の昇順） |
| 残 SWP（理想） | 総 SWP × (日数 − 何日目) / 日数（その日の終わり、小数 1 桁） |
| 残 SWP（模擬） | 総 SWP − その日までに完了した SWP |
| 当日完了 SWP | その日に完了した issue の SWP 合計 |
表の下に「完了日の出どころ」（Project の closedAt か、Project と照合済みの sprint-days の completed）を書く。

## 親 = 子の合計の確認
スナップショット全体の親ごとに、SWP と見積時間(h) を直下の子の合計と比べる。不一致の行だけ表にする:
| 列 | 意味 |
|---|---|
| キー | 親のキー（なければ #番号） |
| 項目 | SWP または 見積時間(h) |
| 親の値 / 子の合計 | 比べた 2 つの値（空は「（空）」） |
| 備考 | 子に未設定あり / 親が未設定 |
不一致があれば exit 4。

## JSON 出力（`--format json`）
`{"source": {..., "repo", "planSnapshot", "movedOut"}, "status": [...], "epics": [...], "roles": [...], "missingSwp": n,
"parentCheck": {"checkedParents": n, "mismatches": [...]}, "statusStateMismatch": [{"key", "number", "status", "state", "problem"}],
"burndown": [...], "burndownDateSource": "..."}`。
報告書の表を生成・照合するスクリプトはこちらを読む。
