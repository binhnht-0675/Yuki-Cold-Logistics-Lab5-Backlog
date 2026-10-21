---
name: github-project-field-writer
description: GitHub Project のフィールド（SWP・見積時間・Status・イテレーション）、issue のクローズ、ラベル、コメントを「変更セット（change-set）」として宣言し、旧 → 新の差分表を人が確認してから書き込む。estimate-swp の HTML レポートから SWP と時間（親 = 子の合計）を作る機能と、スプリント計画から Status / イテレーション / クローズ / 持ち越しラベルを作る機能を持つ。ログから元に戻せる。「SWP を Project に書いて」「見積時間を入れて」「スプリントの状態を反映して」「さっきの書き込みを戻して」と言われたら、このスキルを使うこと。
metadata:
  version: "0.6.0"
---

# github-project-field-writer

AI エージェントが Project に値を書くときの手順を固定するスキル。
**作る（build）→ 見せる（diff）→ 人が承認 → 書く（apply --apply）→ ログ → 必要なら戻す（revert-from-log）**。
値は必ず change-set ファイルを経由するので、何をどう変えるかが書き込み前に人の目に入る。

## コマンド
スクリプト: `scripts/write-fields.py`（`--state-dir` 既定 `state/`。`key-map.json`・`field-map.json` は
`github-project-backlog-push` が作ったものを使う。ログは**実行ごとに 1 ファイル**:
`state/write-logs/<change-set 名>-<内容の sha8>.csv`、`--log` で指定も可）

| コマンド | GitHub | 内容 |
|---|---|---|
| `build-from-estimate-swp` | 接続しない | `--html`（estimate-swp のレポート）の埋め込みデータから、末端は `finalSWP`、親は子の合計で change-set を作る。`--hour-rule` があれば時間も。`--reviewed-by` / `--reviewed-at` で代表 issue のレビュー者を記録 |
| `build-from-sprint-plan` | 接続しない | `--plan`（スプリント計画 JSON）から Status・イテレーション・クローズ・ラベル・コメントの change-set を作る |
| `diff`（既定） | `--snapshot` 指定時は接続しない／なければ読み取りのみ | 内容検査のあと、旧 → 新の表と集計（変更・同じ・エラー） |
| `apply` | `--apply` 時のみ書き込み | 停止条件（下記）を確認し、最新の値を読み直して差分を出し、変わる行だけ書く。`--apply` なしは dry-run |
| `revert-from-log` | `--apply` 時のみ書き込み | `--from-log` に渡した**1 回分の実行ログ**の各（キー, 項目）について最初の「旧」値に戻し、投稿したコメントは削除する change-set を作って `--change-set` のパスに書き出し、apply と同じ流れで反映。`--change-set` に既存のファイルがあれば、同じログから作った戻し用（再実行）のときだけ上書きし、それ以外（元の change-set など）は exit 2 で止まる（上書きするなら `--force`）。戻すのは GitHub の現在の値が**その実行の書いた値のまま**の項目だけ（後の実行の値は上書きしない）。ラベルは 1 つずつ全部扱う |

change-set の形式は `references/change-set-schema.md`、例は `assets/example-change-set.json`（架空。形式の説明用で、
`manual` の SWP 行は書き込み後の Project で親 = 子の合計を検査されるため、そのまま apply すると止まることがある）。

## 見積もりの書き込み（estimate-swp → Project）
1. `build-from-estimate-swp --html <レポート> --backlog <backlog.json> --hour-rule <hour-rule.json> --repo <owner/name>
   --reviewed-by <代表 issue をレビューした人> --reviewed-at <YYYY-MM-DD> --change-set cs.json`
   - 末端: SWP = レポートの `finalSWP`。時間 = 0.5 刻みの四捨五入（SWP × k × f）。
   - 親（epic / story）: SWP も時間も**子の合計**（GitHub は数値フィールドを親に集計しないため）。親の行には `children`（子のキー）を記録する。
   - レポートの元 HTML の sha256 と、`source.review`（`calibrationStatus`・`reviewedBy`・`reviewedAt`）を change-set に記録する。
     レポートの埋め込みデータにはレビュー者の名前がないため、名前と日付は引数で明示する。
   - 下の「apply の停止条件」に当たるものは WARN を出したうえで `blockingErrors` として change-set に記録する（build 自体は exit 0）。
2. `diff --change-set cs.json`（GitHub の最新値と比較）。人は全親行と、末端の数行を抜き取りで確認する。
3. 承認後 `apply --change-set cs.json --apply`。もう一度 `apply` しても「変更 0」になることを確認。
4. 照合は `github-project-progress-report` のスナップショットで行う。

`hour-rule.json`: `{"k": 時間/SWP, "f": 状況係数, "round": 0.5}`（k と f の根拠は別資料に書く）。

## apply の停止条件（書き込み 0 件で exit 2）
`apply` と `revert-from-log` は、GitHub を読む前に次を確認し、1 つでも当たれば何も書かない。`diff` は `blockingErrors` と見積もりの検査
（次の 3 項目）を WARN として表示するだけ。フィールド名・選択肢・イテレーションの誤り、キー重複、close と reopen の同時指定は `diff` でも exit 2。
- `blockingErrors` がある: バックログの末端（タスク）に SWP がない、子がそろわず親を出せない、
  レポートの親の合計やレポートが親に付けた値が子の合計と違う、レビュー記録がない。
- **見積もり由来かどうかは中身で決める**（印が残っている change-set は `source.kind` を書き換えただけでは外せない）。
  `source` に `sha256` / `hourRule` / `review` がある、または行に `derived` / `children` がある change-set は見積もり由来とみなし、次をすべて求める:
  `source.kind = estimate-swp`、元 HTML の `sha256`、`source.review` の
  `calibrationStatus` が `accepted` / `calibrated`（`pending`・`skipped` = 代表 issue のレビュー未完了は不可）、
  `reviewedBy` / `reviewedAt`（YYYY-MM-DD）。分割推奨（`splitRecommended`）の issue があるときは build 時に `blockingErrors` に入る。
- 見積もり由来の印がないのに SWP / 見積時間（`--swp-field` / `--hours-field`）を書く change-set は、`source.kind = manual`
  だけ許す（Project 上の親 = 子は下で検査）。**この manual の道は意図して残している**: 見積もりの change-set から印
  （`sha256`・`hourRule`・`review`・`derived`・`children`）をすべて消して `kind = manual` にすれば、代表 issue のレビュー
  （`calibrationStatus`・`reviewedBy`）を通らずに SWP / 見積時間を書ける。止めない代わりに、`diff` / `apply` は
  「WARN source.kind = manual（見積もり由来の印なし）: 代表 issue のレビュー記録を検査せずに …」を必ず表示し、
  ログの `#run` 行に `kind=manual` を残す。親 = 子の合計は書き込みの前に Project 上で検査し、合わなければ止める（下記）。
  見積もりの書き込みには使わず、レビュー後の少数の手直しだけに使う。印のない change-set で SWP / 見積時間を書くとき、
  `manual` 以外の kind（`sprint-plan` など）は不可。SWP / 見積時間を書く `revert` は `revert-from-log` がログから
  その場で作ったものだけ（手で作った `revert` で SWP / 見積時間を書く change-set を `apply` に渡すと exit 2。それ以外の項目だけの `revert` は通る）。
- `children` を持つ行の数値が、change-set 内の子の値の合計と違う（change-set を手で直した場合も検出する）。
- Status・イテレーションなどの値が `field-map.json` の選択肢 / イテレーションにない（最初の書き込みの前に全行を検査）。

さらに `apply` は、Project を読んで差分を出したあと、**最初の書き込みの前に全行を**検査し、次に当たれば 1 件も書かない（exit 2）:
- エラー行がある（Project にないキー＝ key-map が古い・Project に追加されていない issue）。
  末端が 1 件でも書けないなら、その親も含めて何も書かない。
- 書き込み後の Project で親 = 子の合計にならない: SWP / 見積時間が変わる issue の親と、値が変わる親について、
  スナップショットの親子関係（sub-issue）で子の値を合計して比べる。`manual` の change-set も対象
  （末端だけ直すと親が合わず止まる。親・祖先も同じ change-set で直す）。
`revert-from-log` は戻せるものを戻すため止めない: エラー行（Project にないキーなど）は飛ばし、親 = 子の不一致は WARN を出したうえで書き戻す。

## スプリント状態の反映
`build-from-sprint-plan --plan sprint.json --change-set cs.json` → `diff` → `apply --apply`。
計画 JSON の 1 行: `{"key", "status", "iteration", "close", "reopen", "addLabels", "removeLabels", "comment"}`。
コメントを投稿するかは、**GitHub の issue に今あるコメント**で決める（`diff`・`apply` はコメントの行がある issue のコメントを
読む。ログの記録だけでは決めない）: 同じ内容（本文の sha256 先頭 8 文字）がすでにあれば再投稿しない、なければ投稿する。
そのため `revert-from-log`（や手作業）で削除したあとに同じ change-set を `apply` し直すと、コメントはもう一度投稿される。
`diff --snapshot`（GitHub に接続しない）ではコメントを読めないので、ログの記録を「ログでは投稿済み」などと表示するだけ。
コメントは `revert-from-log` で削除できる: 投稿時に返ってきたコメント id をログに残し、戻すときはその id で削除する
（`diff` / `apply` はコメントの行があると INFO を出す）。削除したコメントは元に戻せない。
**手で削除が必要な場合**: id がログにない（投稿の直後にプロセスが落ちた、または `status` 列のない旧形式のログ）うえ、
同じ issue に同じ内容のコメントが 2 件以上あって、どれを消すか決められないとき。差分表にエラーとして出し、何も消さない。

## ログと戻し方
- 1 回の実行 = 1 つのログ。既定名は change-set のファイル名と内容から決まるので、同じ change-set の再実行
  （exit 75 のあとの続きなど）は同じログに追記され、別の change-set（見積もりの書き込みとスプリント模擬など）は別のログになる。
- `apply --apply`（`revert-from-log --apply` も）は、変わる行があれば書き込みの前に項目 `#run` の行を 1 行足す（書き込みではなく、
  change-set 名・種類・レビュー者・HTML の sha256 の記録）。exit 75 のあとの再実行では同じログに 2 行目の `#run` が入る。
- `revert-from-log --from-log <そのログ>` は、そのログの書き込みだけを戻す: フィールド値 → 旧値、クローズ ↔ 再オープン、
  追加したラベル → 削除、削除したラベル → 再追加、投稿したコメント → 削除（id で。id がなければ内容の sha8 で探す）。
  `revert-from-log` で削除したコメントをさらに戻すことはできない（WARN）。
- ログは先行書き込み（write-ahead）: 書き込みの**前に** `status = pending` の行（キー・issue 番号・項目・旧値・新値・
  操作 id）をディスクに書き、成功したら同じ操作 id で `done` の行（コメントはその id を `ref` に）、失敗したら
  `failed` の行（exit_code 付き）を足す。
- 書き込みとログの間でプロセスが落ちると `pending` の行だけが残る。`revert-from-log` はその行も戻す対象に含め、
  GitHub の現在の値（Project のフィールド・issue の状態とラベル・issue のコメント）と比べて決める:
  書き込みが届いていれば戻し、届いていなければ「同じ」として何もしない。ログだけから推測はしない。
  フィールドは結果の記録（done / pending / failed）にかかわらず、現在の値がその実行の最後に書いた値のときだけ戻す
  （`ifCurrent`。後の実行が書いた値は残し、差分表に「この実行の値ではないので戻さない」・WARN を出す）。
  issue の状態も同じ（`ifCurrentState`）。ラベルは 1 つずつ: 追加したラベルはまだ付いていれば外し、
  外したラベルはまだ付いていなければ付け直す。
- `status` 列のない旧形式のログ（9 列）も読める（exit_code 0 = done、それ以外 = failed とみなす）。
  そのログに追記するときは見出し行を新しい形式に書き換え、既存の行はそのまま残す。

## 内容検査（公開リポジトリへ出す前の遮断）
`diff`・`apply`・`revert-from-log` は、change-set の検証の直後、GitHub を読む前に、送る可能性のある**すべての文字列**
（コメント本文、`addLabels` のラベル名、文字列のフィールド値。数値は対象外。`removeLabels` は削除なので対象外）を
`../_shared/content_guard.py` で検査する。1 件でも該当すれば**最初の書き込みの前に**全体を止め、exit 3 を返す。
分類は 7 つ（1 ベトナム語の文字／2 制御文字／3 内部パス／4 秘密情報のパターン／5 メールアドレス（noreply・example
ドメインは可）／6 公開しない固有の用語／7 社内・要ログインの URL・社名・`--repo` 以外のリポジトリを指す GitHub URL）。
詳細な規則は `github-project-backlog-push` の SKILL.md「内容検査」と同じ。コメントに GitHub の URL を書くときは
`--repo` を付ける（`--repo` なしの `diff --snapshot` では GitHub URL はすべて許可外として止まる）。
4・5・7 の該当文字列は出力しない（長さだけ。ただし許可外リポジトリの GitHub URL は owner 名だけ表示する）。

## 安全のための決まり
- 書き込むのは「旧 ≠ 新」の行だけ（数値は 5 と 5.0 を同じとみなす）。再実行しても二重に書かない。
- change-set に Project にないフィールド・選択肢にない値がある、キーが重複している、close と reopen が同時、のどれかなら exit 2。
- スナップショットにない（Project に入っていない）キーはエラー行として表示し、`apply` は 1 件も書かずに exit 2。GitHub の Project のアイテム一覧は、API で追加した直後には全件が出ないことがある（2026-10-20 の試行: 15 件を追加した直後は 1 件、約 15 分後に 9 件。作成順に少しずつ出る）。issue を追加した直後はこの理由でも止まるため、スナップショットを取り直してから実行する。
- 書き込みは既定 2.5 秒に 1 件（`--pace`）、直近 60 分の書き込み（再試行を含む）が 450 件（`--max-writes-per-hour`、0 で無効）に
  達したら止まらずに待機して続ける。直近 60 分の数は実行をまたいで、`github-project-backlog-push` とも共通に数える
  （書き込み記録 `--write-window`、既定 `<state-dir>/write-window.json`。同じ作業ディレクトリ・同じ `--state-dir` なら同じファイル。
  別の `--state-dir` なら `--write-window` で同じファイルを指す。コミットしない）。書き込みの直前に直近 60 分の数を数え、空きがあればその時刻を保存する（一時ファイルに書いてから置き換え）。数えることと保存は 1 つの排他ロック（`fcntl`）の中で行うので、同じファイルを使う実行が同時に動いても、最後の 1 件の空きを両方が使うことはない（`fcntl` のない環境ではロックがないため、同時に実行しない）。記録が読めない・形式が違うときは何も読み書きせずに
  exit 1（直すか、60 分以上あけて `--ignore-broken-write-window`）。`--apply` を付けない実行（diff・dry-run）はこのファイルを開かない。`gh` 1 回は `--timeout`（既定 120 秒）で打ち切る。動きは `github-project-backlog-push` の
  「レート制限と所要時間」と同じ（`../_shared/gh_runner.py`）。`--max-writes`（1 回の書き込み上限）はない。
  例: 約 450 issue に SWP と時間を書く（約 900 件）と、少なくとも 1 回、約 60 分の待機が入る。
  レート制限の待ち時間（`retry-after`・`x-ratelimit-reset`）は `gh api --include` の応答ヘッダーから読む。
- レート制限（二次制限に加え、一次制限 "API rate limit exceeded"・GraphQL の `RATE_LIMITED` も）は待機・再試行する。再試行は最大 5 回
  （最初の呼び出しと合わせて最大 6 回）。続けば exit 75 で止まり、ログに `failed`・exit_code 75 の行が残る。再実行で続きから。
- トークン・環境変数は読まない。ログに本文は書かない（コメントは sha256 の先頭 8 文字と、投稿後のコメント id のみ）。
- コメントは `revert-from-log` で削除できるが、削除の前に他の人が読んでいる可能性はある。
  だからこそコメントは内容検査を通ったものだけを投稿する。

## 終了コード
| コード | 意味 |
|---|---|
| 0 | 正常（dry-run・diff を含む） |
| 1 | 実行時エラー（gh の失敗、スナップショット取得の失敗、`--apply` 時に書き込み記録 `state/write-window.json` が読めない・形式が違うなど）。`state/field-map.json` がない・ファイルが読めないなどの想定外の例外も 1（`ERROR` 行ではなく Python のトレースバックが出る。先に `github-project-backlog-push fetch-field-map`） |
| 2 | 入力・オプションの誤り（change-set の検証、必須オプションの不足、`revert-from-log` の `--change-set` が既存の別ファイル）、apply の停止条件に該当（書き込み 0 件） |
| 3 | 内容検査で停止（書き込み 0 件） |
| 75 | レート制限が続いたため停止（時間をおいて再実行。同値はスキップされる） |

## テスト
`python3 -m unittest discover -s tests`（偽の `gh`。見積もりの入力は `../_shared/tests/fixtures/` の架空レポート）。
