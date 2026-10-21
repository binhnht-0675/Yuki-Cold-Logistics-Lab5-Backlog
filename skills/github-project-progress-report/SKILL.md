---
name: github-project-progress-report
description: GitHub Project を読み取り専用でスナップショット（JSON）に落とし、日本語の集計表（ステータス別の issue 数・SWP 合計、エピック別、担当（仮）別、模擬バーンダウン）を Markdown か JSON で出す。GitHub には一切書き込まない。進捗報告書・スプリント報告・「Project の今の状態を表にして」「バーンダウンを作って」「件数と SWP を数えて」と言われたら、このスキルを使うこと。報告書の数字は手で数えず、必ずこのスキルの出力から転記する。
metadata:
  version: "0.3.0"
---

# github-project-progress-report

Project の実データから報告用の表を作る。**書き込みはしない**ので、いつ何度実行してもよい。
数字の出どころを 1 つ（スナップショット）に固定するのが目的。報告書の表は手で直さず、再生成する。

## コマンド
スクリプト: `scripts/progress-report.py`

| コマンド | GitHub | 内容 |
|---|---|---|
| `snapshot` | 読み取りのみ | `--repo` の issue のアイテム（issue 番号・タイトル・状態・親・ラベル・フィールド値）を `--snapshot` に保存。本文は保存しない。件数・キーの確認に通ったときだけ保存する |
| `tables` | 接続しない | スナップショットから表を作る。`--format md`（既定）/ `json`、`--out` でファイル出力。親 = 子の合計も確認する |

例:
```
python3 scripts/progress-report.py snapshot --owner <owner> --project <番号> --repo <owner/name> \
  --key-map state/key-map.json --expect-items <件数> --snapshot snapshots/project-now.json
python3 scripts/progress-report.py tables --snapshot snapshots/project-now.json \
  --iteration "スプリント 1" --plan-snapshot snapshots/project-plan.json --sprint-days sprint/sprint-days.json --strict
```
`--key-map` は `github-project-backlog-push` が作るキー → #番号 の対応表（なくても動くが、キー列が空になる）。

## スナップショットの確認（正式な数字にするための条件）
- `--repo` を付けると、そのリポジトリ（`owner/name`、大文字小文字は区別しない）の issue だけを残す。
  ほかのリポジトリの issue は除外して件数を WARN に出す。キーは「リポジトリ#番号」でだけ対応付けるので、
  別リポジトリの #1 が自分の #1 のキーを取ることはない。
- `--repo` なしで Project に複数リポジトリの issue があれば exit 1（どれを数えるか決められないため）。
- `--expect-items N`: 件数が N でなければ exit 2。GitHub の Project のアイテム一覧は、API で追加した直後には全件が出ないことがある（2026-10-20 の試行: 15 件を追加した直後は 1 件、約 15 分後に 9 件。作成順に少しずつ出る）。追加の直後はこの件数確認で止まるので、時間をおいて再実行する（足りない一覧から表を作らない）。
- key-map があるとき: key-map にない issue、Project にない key-map のキーが 1 つでもあれば exit 2。
- exit 2 のときはスナップショットを**保存しない**（報告書の数字に使わせないため）。

## 数え方（重要）
- 既定では**末端の issue（子を持たないもの）だけ**を数える。親（エピック・ストーリー）の SWP は子の合計なので、
  一緒に数えると二重計上になるため。親も数えたいときだけ `--include-parents`。
- `--iteration` を付けると、イテレーション欄がその値の issue だけを対象にする。表の上に「集計範囲」を必ず書く。
- 途中で別のイテレーションへ移った issue（持ち越し）も計画の合計に入れたいときは `--plan-snapshot`
  （スプリント開始時に撮ったスナップショット）を付ける。対象 = 計画時点でそのイテレーションにあった issue +
  現在そのイテレーションにある issue。移動した件数を「集計範囲」に書き、ステータス・エピック・担当・バーンダウンの
  合計はすべてこの同じ集合から出す（途中で追加した issue がなければ「完了 + 残り = 計画の合計」。追加した issue も現在
  そのイテレーションにあれば集合に入る）。
- SWP が空の issue は 0 として合計し、表の下に件数を注記する。
- 各ステータス行の備考に、その行のクローズ済みの件数を出す（完了以外の行に出たら Status と issue の状態がずれている）。
- **Status と issue の状態（open / closed）のずれ**: 数える issue のうち、Status が「完了」なのに未クローズ、または
  クローズ済みなのに Status が「完了」でないものがあれば、ステータス別の表の下に「注意:」の行と、その issue の一覧
  （キー・#・Status・状態・ずれ）を出す（JSON では `statusStateMismatch`）。ステータス別の表は Status で、バーンダウンは
  「Status 完了 または クローズ済み」で数えるので、ずれがあると両者の数字が合わない。既定は表を出して exit 0
  （標準エラーに WARN）。`--strict` を付けると表を出したうえで exit 5。報告書に使う前に issue を閉じる / Status を直す。

表の列と意味は `references/output-table-columns.md`。

## 親 = 子の合計の確認
`tables` は毎回、スナップショット全体（イテレーションで絞らない）の親それぞれについて、SWP と見積時間(h) が
直下の子の合計と一致するかを確認し、「親 = 子の合計の確認」の節に結果を出す。
- 一致: 「親 N 件、すべて一致」。親も子もすべて空の項目は確認の対象外（見積もり前）。
- 不一致・子に未設定あり・親が未設定: 不一致の表を出し、表を出力したうえで **exit 4**。
  この状態の数字は報告書に使わず、`github-project-field-writer` で直してから撮り直す。

## バーンダウン（模擬）
`--sprint-days` の JSON の `days`（YYYY-MM-DD の昇順）が横軸。各日の終わりの残 SWP と理想線（総量を日数で均等に減らす）を出す。
完了日の出どころは表の下に必ず書く（`完了日の出どころ: …`）。
- `completed` がないとき: Project の `closedAt` を `--tz`（既定 +09:00）の日付にして使う。初日より前にクローズした issue は
  初日から消化済み、最終日より後にクローズした issue は未消化として数える（`days` がイテレーションの期間と合うかは確認しない）。
- `completed`（キーまたは `#番号` → 完了日）があるとき: 1 日でまとめて状態を更新した模擬スプリントでは
  `closedAt` が全部同じ日になるため、計画ファイルの日付を使う。ただし Project と照合し、次のどれかなら exit 2:
  日付が YYYY-MM-DD でない・`days` にない、対象外のキー、Project で完了していない（Status ≠ 完了 かつ未クローズ）のに完了日がある、
  Project で完了済みなのに完了日がない。
表題は必ず「（模擬）」とし、報告書でもこの理由を説明すること。

## 使いどころ
- Project への一括登録の後: 件数・親子・初期値の照合（`github-project-backlog-push` の結果確認）。
- 見積もり書き込みの後: SWP・見積時間の合計と、親 = 子の合計の確認節（exit 4 でないこと）。
- スプリント模擬の後: 進捗報告書のステータス表とバーンダウン。

## 終了コード
| コード | 意味 |
|---|---|
| 0 | 正常 |
| 1 | GitHub の読み取り失敗（レート制限が続いて止まった場合も 75 ではなく 1）、`--repo` なしで複数リポジトリ。`--snapshot`・`--plan-snapshot`・`--sprint-days` のファイルがないなどの想定外の例外も 1（`ERROR` 行ではなく Python のトレースバックが出る） |
| 2 | 引数の誤り、スナップショットの件数・キーの不一致（保存しない）、sprint-days が Project と合わない |
| 4 | 表は出力済みだが、親 = 子の合計が一致しない行がある |
| 5 | `--strict` のときだけ: 表は出力済みだが、Status と issue の状態（open / closed）がずれた issue がある（4 にも当たるときは 4） |

## テスト
`python3 -m unittest discover -s tests`。架空のサンプル: `assets/example-snapshot.json`、`assets/example-sprint-days.json`。
