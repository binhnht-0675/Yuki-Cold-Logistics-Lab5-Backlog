# change-set の形式（`change-set/1`）

```json
{
  "schema": "change-set/1",
  "source": {"kind": "estimate-swp | sprint-plan | revert | manual", "createdAt": "…",
             "file": "元ファイル名", "sha256": "元 HTML の sha256（estimate-swp のみ）", "hourRule": {…},
             "review": {"calibrationStatus": "accepted", "reviewedBy": "名前", "reviewedAt": "YYYY-MM-DD"},
             "fromLog": "戻し元のログ名（revert のみ）"},
  "blockingErrors": ["build が見つけた停止理由（空なら書き込める）"],
  "changes": [
    {"key": "E01-I01-S01",
     "fields": {"SWP": 5, "見積時間(h)": 7.5, "Status": "完了", "スプリント": "スプリント 1"},
     "close": true, "reopen": false,
     "addLabels": ["持ち越し"], "removeLabels": [],
     "comment": "（模擬）…",
     "derived": "payload | sum-of-children",
     "children": ["親の行のみ: 子のキー"]}
  ]
}
```

| 項目 | 意味 |
|---|---|
| `key` | バックログの安定キー。`state/key-map.json` とスナップショットで issue / Project アイテムに対応付ける。重複不可 |
| `fields` | フィールド名 → 新しい値。名前は Project の表示名そのまま（`field-map.json` にあること）。数値は数、単一選択は選択肢名、イテレーションはイテレーション名。`null` は値を消す |
| `close` / `reopen` | issue の状態変更（同時指定は不可）。クローズ理由は completed |
| `addLabels` / `removeLabels` | issue ラベルの追加・削除 |
| `comment` | issue へのコメント（同一内容は 1 回だけ） |
| `ifCurrent` | `revert-from-log` が作る。フィールド名 → この実行が最後に書いた値。結果の記録（done / pending / failed）にかかわらず、現在の値がこれと同じときだけ戻す（後の実行の値を上書きしない） |
| `ifCurrentState` | `revert-from-log` が作る。この実行が残した issue の状態（`OPEN` / `CLOSED`）。現在の状態が違えば戻さない |
| `deleteComments` | `revert-from-log` が作る。`[{"id": "コメント id（なければ空）", "sha8": "本文の sha256 先頭 8 文字"}]`。apply は issue のコメントを読み、id がもうなければ「同じ」、id がなければ sha8 で探して 1 件なら削除・0 件なら「同じ」・2 件以上ならエラー（手で削除） |
| `derived` | 参考情報（書き込みには使わない）。親の値が子の合計であることを示す |
| `children` | 親の行の子のキー。apply は数値フィールドごとに「親 = change-set 内の子の合計」を確認し、違えば書かない |
| `source.review` | 見積もり由来のとき必須。`calibrationStatus` が accepted / calibrated、`reviewedBy`・`reviewedAt` あり。見積もり由来かどうかは `source.kind` ではなく中身（`source.sha256` / `hourRule` / `review`、行の `derived` / `children`）で決める |
| `source.kind` | 見積もり由来の中身なら `estimate-swp` 以外は不可。SWP / 見積時間を書く change-set で見積もり由来の印がないものは `manual` だけ（書き込み後の Project で親 = 子を検査）。印をすべて消した `manual` はレビューの検査を通らずに書ける（意図して残している道。WARN を表示し、ログの `#run` 行に `kind=manual`）。SWP / 見積時間を書く `revert` は `revert-from-log` がその場で作ったものだけ（ほかの項目だけの `revert` は手で作っても通る） |
| `blockingErrors` | 1 件でもあれば `apply` / `revert-from-log` は exit 2（書き込み 0 件）。`diff` は WARN 表示のみ |

差分表の列: キー / # / 項目（フィールド名、`state`、`labels+`、`labels-`、`comment`、`comment-` = コメント削除）/ 旧 / 新 / 判定（変更・同じ・エラー。`--snapshot` だけの diff ではコメント削除と、ログに投稿済みの記録がないコメント投稿を「変更（GitHub のコメントで確認）」、ログに投稿済みの記録があるコメント投稿を「ログでは投稿済み（apply は GitHub のコメントで確認）」と表示。投稿するかは apply が issue の今のコメントで決める）。

ログ（CSV）は実行ごとに 1 ファイル（既定 `state/write-logs/<change-set 名>-<changes の sha8>.csv`、`--log` で指定可）。
列: timestamp, skill, command, key, number, field, old, new, exit_code, status, op, ref。
1 書き込み = 書く前の `status = pending` の行 + 書いた後の `done`（exit_code 0）または `failed`（exit_code 付き）の行。
2 行は同じ `op`（操作 id）で対応する。`ref` はコメントの id（投稿・削除）。`pending` だけで終わっている操作は、
書き込みの途中でプロセスが落ちたもの。9 列の旧形式のログも読める（status は exit_code から決める）。
`field = #run` の行は書き込みではなく実行の記録（old = change-set 名、new = 種類・レビュー者・sha256）。変わる行がある `--apply` の実行ごとに、書き込みの前に 1 行足す（再実行すると同じログに 2 行目以降が入る）。
`revert-from-log` は渡されたログ 1 つの（key, field。ラベルは key, field, ラベル名）ごとに最初の行の `old` を新しい値にし、
最後の行の `new` を `ifCurrent` / `ifCurrentState` に入れ、投稿したコメントを
`deleteComments` にした change-set を作り、`--change-set` のパスに書き出す（既存のファイルは、同じログから作った戻し用のときだけ上書き。ほかは `--force` がなければ exit 2）（`pending` / `failed` の行も含む。届いたかどうかは apply が GitHub の現在の値と
比べて決める。`#run` 行は対象外。`comment-`（削除したコメント）は元に戻せないので WARN）。
