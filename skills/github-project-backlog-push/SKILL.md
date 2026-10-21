---
name: github-project-backlog-push
description: バックログ JSON（epic / story / task の木）から GitHub の issue を作成し、sub-issue で親子をつなぎ、GitHub Project に追加して初期フィールド（担当（仮）・Status）を設定する。既定は計画表示のみで、--apply を付けたときだけ書き込む。キー（<!-- backlog-key: … -->）で冪等なので、途中で止まっても同じコマンドの再実行で続きから進む。「バックログを GitHub に登録」「issue を一括作成」「sub-issue を張る」「Project に積む」と言われたら、件数が少なくてもこのスキルを使うこと。
metadata:
  version: "0.5.0"
---

# github-project-backlog-push

バックログファイルを GitHub の実物（issue・sub-issue・Project アイテム）に変換する。
数百件を一度に作るため、**計画 → 人の確認 → 実行** の順を崩さないことが一番大事。

## 前提
- `gh` にログイン済みで、対象リポジトリへの書き込み権限と `project` スコープがあること
  （スキルはトークンや環境変数を読まない。`gh auth status` の確認は人が行う）。
- Project のフィールド（`Status`、`担当（仮）` など）は先に作っておく。
- バックログの形式は `references/backlog-json-schema.md`。サンプルは `assets/example-backlog.json`（架空）。

## コマンド
スクリプト: `scripts/push-backlog.py`（作業ディレクトリに `state/` を作る。`--state-dir` で変更可）

| コマンド | 書き込み | 内容 |
|---|---|---|
| `plan`（既定） | なし・GitHub にも接続しない | 内容検査、field-map の検査（あれば）、作成予定の issue / sub-issue / Project 追加 / フィールド設定の件数、所要時間の目安、本文プレビュー（`--show-body キー`）、本文の書き出し（`--dump-bodies DIR`） |
| `fetch-field-map` | なし（読み取り） | Project のフィールド ID・選択肢 ID・イテレーション ID を `state/field-map.json` に保存 |
| `apply` | `--apply` 時のみ | 最初の書き込みの前に field-map を検査（下記）し、現状を読み取って足りない分だけ作成・接続・追加・設定。`--apply` なしは dry-run |
| `rebuild-key-map` | なし（読み取り） | リポジトリの全 issue を列挙し、キー → #番号 を `state/key-map.json` に再構築（重複キーは exit 1） |
| `update-body` | `--apply` 時のみ | 本文を再生成し、変わった issue だけ更新（依存キーを #番号 に置き換える用途）。改行コード（CRLF）の違いは差分とみなさない。`依存` 以外も違う issue は手で編集された可能性があるため WARN を出して飛ばす（上書きは `--force-body`、対象を絞るなら `--keys`）。`--max-writes` の対象 |
| `close-and-mark` | `--apply` 時のみ | `--keys` の issue をクローズ（not planned）し、`廃止` ラベルを付ける。削除はしない。**既にクローズ済みの issue は変えない**（WARN を出して飛ばす。完了でクローズした issue のクローズ理由を not planned に変えないため）。クローズ済みも not planned と `廃止` にするときだけ `--include-closed` を付ける。`廃止` が既に付いていれば付け直さない。`--max-writes` の対象 |

主なオプション: `--repo owner/name`、`--project 番号`、`--owner`、`--ref-style permalink|text`、
`--ref タグ`、`--specs-root 設計書ルート`、`--edition 版表示`、`--only-level epic,story,task`、
`--max-writes N`（1 回の書き込み上限。`apply`・`update-body`・`close-and-mark` の書き込みを数え、dry-run でも数える。到達で exit 10）、`--pace 秒`（既定 2.5）、`--max-writes-per-hour N`（直近 60 分の
書き込み上限。既定 450、到達で待機、0 で無効。実行をまたいで数える）、`--write-window ファイル`（直近 60 分の書き込み記録。
既定 `<state-dir>/write-window.json`）、`--ignore-broken-write-window`（記録が壊れていても 0 件から数えて続ける。既定は exit 1）、
`--retry-wait 秒`（既定 60）、`--max-retries N`（既定 5）、`--timeout 秒`（gh 1 回の制限時間。既定 120）。

## 手順
1. `fetch-field-map` で `state/field-map.json` を作る（読み取りのみ）。
2. `plan --repo <公開リポジトリ>` で「内容検査: OK」・件数・所要時間の目安・本文を確認し、人に見せる。内容検査で
   1 件でも止まったら（exit 3）バックログを直してからやり直す。field-map の検査に通らなければ exit 2。
   `WARN Project 名…` が出たら、GitHub の画面で Project 名を変えてから手順 1 をやり直す（スキルは Project 名を書かない）。
3. `apply`（`--apply` なし）で、実データに対する書き込み予定を確認する。
4. 人の承認後、`apply --apply --only-level epic` で最初のバッチを流し、GitHub 上で 1〜2 件を目視確認。
5. 問題なければ `--only-level story`、`--only-level task` と進める。`--max-writes` で区切ってもよい。
   数百件以上は数時間かかる（下記「レート制限と所要時間」）。途中で止まったら「冪等性と再開」の手順で続ける。
6. 最後に `rebuild-key-map` で件数・親子・Project 追加数を確認する。依存の #番号 化は `update-body`。

## field-map の検査（`apply` は最初の書き込みの前、`plan` は field-map があるとき）
次のどれかに当たれば、GitHub への書き込み 0 件のまま exit 2 で止まる（`apply` は GitHub に接続する前に検査し、
Project ID と下の「Project の今のフィールド」だけは読み取りの後・書き込みの前に照合する）。
- `state/field-map.json` がない（`fetch-field-map` を先に実行）。
- field-map の owner / Project 番号が `--owner` / `--project` と違う。読み取った Project の ID が field-map の `projectId` と違う。
- `--role-field`（既定 `担当（仮）`）・`--status-field`（既定 `Status`）が field-map にない、または単一選択でない。
- バックログの `assigneeRole` や `--initial-status` の値が選択肢にない。
- `apply` のみ: Project のフィールドを 1 回読み（`fetch-field-map` と同じ読み取り）、`--role-field` と `--status-field` の
  フィールド名・フィールド ID・型・選択肢（名前 → ID の組をすべて）が field-map と同じかを比べる。名前の変更・削除、
  選択肢の追加・削除・作り直し（ID が変わる）が 1 つでもあれば止まる（`fetch-field-map` をやり直す）。

## 内容検査（公開リポジトリへ出す前の遮断）
`plan`・`apply`・`update-body`・`close-and-mark` は、GitHub に接続する前に、送る可能性のある**すべての文字列**
（全 item のタイトル・生成後の本文・ラベル名・`担当（仮）`・Status 初期値・廃止ラベル。`--only-level` に関係なく全件）を
`../_shared/content_guard.py` で検査する。1 件でも該当すれば**最初の書き込みの前に**実行全体を止め、exit 3 を返す
（途中まで書くことはない）。

| 分類 | 止める内容 |
|---|---|
| 1 ベトナム語の文字 | 声調記号付きの文字（合成済み・結合文字のどちらも。短音記号だけの文字も含む） |
| 2 制御文字 | `\n`・`\t` 以外の制御文字、`\r`、Unicode の書式文字（ゼロ幅文字・ソフトハイフン・文字の向きを変える文字・タグ文字など一般カテゴリ Cf のすべて）、結合用書記素接合子、異体字セレクタ、ハングルの空白文字 |
| 3 内部パス | 計画フォルダ（plans）・試作フォルダ（prototype）の相対パス、ホームディレクトリの絶対パス（macOS・Linux・Windows、`~` で始まる形）、/private 配下の一時フォルダ、作業資料用のフォルダ名、env ファイル（`.example` などのひな形は可） |
| 4 秘密情報のパターン | Supabase の秘密鍵・個人アクセストークン、JWT、AWS のアクセスキー、PEM の秘密鍵、GitHub のトークン、Slack / Google の API キーの形、利用者名とパスワードを含む接続文字列、`password` / `passwd` の直後に `:` か `=` が続く値 |
| 5 メールアドレス | `noreply@`・`no-reply@` で始まるものと example ドメイン以外のアドレス |
| 6 公開しない固有の用語 | 公開物に出さない内部の用語（一覧は `content_guard_rules.py` の `RULES`） |
| 7 社内・要ログインの URL / 社名 | Google Docs / Drive などの URL、社内 SaaS の URL、gist、社名（表記ゆれ・全角・カタカナを含む）、`--repo` 以外のリポジトリを指す GitHub URL（`https://`・ポート番号・利用者名の有無や、REST API の `repos` 形式を問わない） |

- 各行は **NFKC で正規化し、見えない文字を取り除いた形**で検査する（全角文字やソフトハイフンを挟んで規則をすり抜けることはできない）。
  見えない文字そのものは分類 2 で止まる。表示する「行:桁」は元の文字列の位置。
- `--repo` に指定したリポジトリへの GitHub URL（`--ref-style permalink` の `参照`）は許可する（大文字小文字は区別しない）。
  許可するのは `https://github.com/<owner>/<repo>` の部分だけで、その後ろのパス・クエリは通常どおり検査する
  （例: 許可リポジトリでも計画フォルダへのパスやトークンを含むクエリは止まる。`..` でリポジトリの外へ出る URL も止まる）。
  `--repo` の owner の `github.com/users|orgs/<owner>/…` も許可する（Project の URL 用。後ろのパスは通常どおり検査）。`--repo` なしの `plan` では仮の `OWNER/REPO` が許可される。
- Project 名は書き込まないので止めないが、`plan` / `apply` は field-map の Project 名も検査し、該当すれば WARN を出す。
- 結果は 1 行 1 件で「分類・キー・項目（title / body / label …）・行:桁・本文の見出し（§）・規則名」を出す。
  4・5・7 は該当文字列を表示しない（長さだけ。ただし許可外リポジトリの GitHub URL は owner 名だけ表示する）。
- 検出できないもの: 声調記号のないベトナム語、資料からの長文の写し、パーセントエンコードされた文字、行をまたいで分けた語。
  長文の写しは `plan --dump-bodies DIR` で本文を書き出し、手元の漏えい検査ツールで別途確認する。規則は
  `../_shared/content_guard_rules.py` にある（変えたら `../_shared/tests/` のテストも直す）。

## キーと親子の検査（最初の書き込みの前）
- キーに使える文字は英数字と `.`・`_`・`-` だけ（本文のキー印から読み戻せる文字）。それ以外の文字（空白・スラッシュ・全角文字など）を
  含むキーがあれば、`plan`・`apply`・`update-body` は GitHub に接続する前に exit 2 で止まる（再実行で issue が重複するのを防ぐ）。
- `--dump-bodies DIR` は各キーの本文を `DIR/<キー>.md` に書く。`DIR` の外に出るファイル名になるキーがあれば 1 件も書かずに exit 2。
- `--only-level story` / `task` で、親が GitHub にまだない（かつ同じ実行で作らない）項目があれば、issue を作る前に exit 2 で止まる
  （`apply` は読み取りだけ済ませた時点。`plan` は手元の key-map で判定）。epic → story → task の順に流す。

## 冪等性と再開
- 各 issue の本文先頭に `<!-- backlog-key: キー -->` を入れる。実行のたびにリポジトリの全 issue
  （検索インデックスではなく GraphQL の一覧）からキー → #番号 を作り直すので、再実行で重複しない。
- キー印を信用するのは、**実行中のアカウント（GraphQL の viewer）が作成した issue だけ**。公開リポジトリでは誰でも issue を
  作れるため、ほかのアカウントが作った issue の印は WARN を出して無視する（重複キーで止められたり、他人の issue を
  バックログの issue として親子付け・Project 追加したりしない）。
- ただし無視するのは**実行中のアカウントがリポジトリの owner（`--repo` の owner 部分）のとき**だけ。owner でないアカウントで
  実行していて、ほかのアカウントが作ったキー印付きの issue が 1 件でもあれば、別のアカウントで実行している（バックログの
  issue は owner が作った）可能性が高く、無視すると全部作り直して重複するため、書き込みの前に exit 2 で止まる
  （「別のアカウントで実行しています」。`gh auth status` で owner のアカウントに切り替えて再実行）。`apply` のほか、
  issue の一覧を読む `rebuild-key-map`・`update-body`・`close-and-mark` も同じ。
- sub-issue は親が一致していれば何もしない。別の親が付いていれば変更せず WARN を出す。
- Project のワークフロー「Auto-add sub-issues to project」が有効だと、sub-issue にした直後に GitHub が子の issue を Project に追加する。このときスキルの追加は「Content already exists in this project」で断られるため、すでにあるアイテムの id を読んで追加済みとして続ける（2026-10-20 の実行で確認）。
- 初期フィールドは**空のときだけ**設定する（後で人が変えた Status などを上書きしない）。GitHub の Project のアイテム一覧は、API で追加した直後には全件が出ないことがある（2026-10-20 の試行: 15 件を追加した直後は 1 件、約 15 分後に 9 件。作成順に少しずつ出る）。そのため `apply` は、一覧に出ていないアイテムでも、実行のたびに GitHub から読み直した issue に Project のアイテム id があれば、その id で値を読み直し、空とみなして書き込まない（読めないアイテムがあれば書き込みの前にエラーで止まる）。
- **途中で止まったとき（exit 1 / 10 / 75、または手で止めた）**: 原因を確かめてから同じコマンドを再実行する。
  毎回 GitHub の現状を読み直すので、作成済みの issue・接続・追加・設定は飛ばして続きから進む。
  時間あたりの上限は書き込み記録（`state/write-window.json`）で実行をまたいで数えるので、再実行や `--only-level` ごとの
  実行でも直近 60 分の合計が上限を超えない（記録を消したり別の `--state-dir` で流したりすると数え直しになる）。

## レート制限と所要時間
GitHub には内容を作る要求（issue・sub-issue・コメントなど）の二次レート制限がある（GitHub の公開文書では 1 分あたり約 80 件、
1 時間あたり約 500 件。値は GitHub 側で変わりうるため、このスキルでは検証していない）。このスキルは次のように動く（`../_shared/gh_runner.py`）。
- 書き込みは既定 2.5 秒に 1 件（1 分 24 件）。さらに直近 60 分の書き込みが `--max-writes-per-hour`（既定 450、
  500 の手前。再試行も 1 件として数える）に達したら、空きが出るまで（上限を超える分の書き込みが 60 分前になるまで）**待機して続ける**
  （止まらない。待機時間と再開時刻を表示）。
- 直近 60 分の書き込み数は**実行をまたいで、また `github-project-field-writer` とも共通に**数える。書き込みのたびに時刻（epoch 秒）を
  `--write-window`（既定 `<state-dir>/write-window.json`）に記録する。書き込みの直前に直近 60 分の数を数え、空きがあればその時刻を保存する（一時ファイルに書いてから置き換え）。数えることと保存は 1 つの排他ロック（`fcntl`）の中で行うので、同じファイルを使う実行が同時に動いても、最後の 1 件の空きを両方が使うことはない（`fcntl` のない環境ではロックがないため、同時に実行しない）。
  60 分より古い記録は保存のたびに消す。2 つのスキルを同じ作業ディレクトリ・同じ `--state-dir`（既定 `state/`）で動かせば同じファイルを使う
  （別の `--state-dir` なら `--write-window` で同じファイルを指す）。記録が読めない・形式が違うときは数が分からないため、
  何も読み書きせずに exit 1 で止まる（直すか、60 分以上あけて `--ignore-broken-write-window`）。dry-run と `plan` はこのファイルを開かない。
  `state/` は公開リポジトリにコミットしない（`.gitignore` 済み）。
- レート制限（HTTP 429、本文に rate limit を含む HTTP 403、または HTTP 200 の本文や GraphQL の `errors` に "secondary rate limit"・
  "API rate limit exceeded"・`RATE_LIMITED`）は、`retry-after` があればその秒数、`x-ratelimit-remaining: 0` なら
  `x-ratelimit-reset` の時刻まで、どちらもなければ 60 秒（`--retry-wait`）待って再試行する。これらは応答ヘッダーから読む:
  `gh api` は毎回 `--include` を付けて呼び、出力の先頭のステータス行とヘッダー（最初の空行まで）を本文から切り離してから
  本文を読む（`../_shared/gh_include_response.py`）。`retry-after` と 60 秒の待ちは
  続くたびに倍にする（`x-ratelimit-reset` までの待ちは倍にしない）。再試行は最大 `--max-retries`（既定 5）回（最初の呼び出しと
  合わせて最大 6 回）。それでも続けば exit 75 で止まり、書き込み中なら CSV ログに `failed`・exit_code 75 の行が残る。時間をおいて再実行する。
- `gh` 1 回は `--timeout`（既定 120 秒）で打ち切る。読み取りのタイムアウト・HTTP 5xx・通信エラーは 5 秒から倍々で
  最大 `--max-retries` 回（最大 6 回の呼び出し）再試行する。書き込みは、送られていないことが確かな通信エラー（名前解決・接続失敗）だけ
  再試行し、結果が分からないもの（タイムアウト・5xx）は二重作成を避けるため再送せず exit 1 で止まる（再実行で続きから）。
- `plan` は所要時間の目安を出す: 書き込み合計を `--max-writes-per-hour` 件ずつの 60 分枠に分け、最後の枠は
  `--pace` 間隔で数える（レート制限の待ちと、書き込み記録にある直近 60 分の書き込みは含まない）。例: 書き込み 2,421 件・既定値なら約 5.1 時間。
  長時間になるので `--only-level` ごとに分けるか、`--max-writes` で区切って流してもよい。

## ログ
`state/push-log.csv`（timestamp, skill, command, key, number, field, old, new, exit_code, status, op, ref）。`apply`・`update-body`・`close-and-mark` とも、書き込みの前に `status = pending` の行（field は `issue-create`・`body`・`labels+`・`state` などの操作名）を書き、成功したら同じ `op` で `done` の行、`gh` が失敗したら同じ `op` で `failed` の行（exit_code は gh の終了コード。タイムアウトは 124、レート制限で止まったら 75）を足す。`pending` だけの行は書き込みの途中でプロセスが止まったもの（GitHub に届いたかは不明。再実行は GitHub の現状を読み直すので重複しない）。9 列の旧形式も読める。
本文やトークンは書かない。本文更新は sha256 の先頭 8 文字だけを記録する。`=`・`+`・`-`・`@` で始まる値は表計算ソフトで式として
動かないよう先頭に `'` を付けて書く（読み取り時に外すので、ほかのスキルからは元の値に見える）。

## 終了コード
| コード | 意味 |
|---|---|
| 0 | 正常（dry-run を含む） |
| 1 | 実行時エラー（gh の失敗、結果が不明な書き込み、一時的なエラーの再試行切れ、自分が作った issue どうしのキー重複など。再実行で続きから）。書き込み記録 `state/write-window.json` が読めない・形式が違う（`--apply` 時、何も読み書きする前に `ERROR` 行）。想定外の例外（`plan --show-body` に存在しないキー、`state/` に書けないなど）も 1（`ERROR` 行ではなく Python のトレースバックが出る） |
| 2 | 入力・オプションの誤り（バックログ検証・キーの文字、field-map の検査（Project の今のフィールドとの照合を含む）、親が未作成の `--only-level`、`--dump-bodies` の外への書き出し、owner でないアカウントでほかのアカウントのキー印付き issue がある。書き込み 0 件） |
| 3 | 内容検査で停止（書き込み 0 件） |
| 10 | `--max-writes` に到達（`apply`・`update-body`・`close-and-mark`。dry-run でも到達すれば 10。同じコマンドの再実行で続き） |
| 75 | レート制限が続いたため停止（時間をおいて再実行） |

## 本文の形式
見出しは `bodyJa` のキー名（`概要`・`対象機能（FT）`・`参照（詳細設計）`・`規模の手がかり`・
`完了の定義`（チェックボックス）・`依存`・`備考`）。末尾に「種別・層・担当（仮）・キー」の 1 行。
`--ref-style permalink` は `https://github.com/<repo>/blob/<ref>/<specs-root>/<path>` へのリンク、
`text` はファイル名＋節＋版表示（リンクなし。公開リポジトリから非公開リポジトリへリンクしない場合）。

## やらないこと
- issue の削除。Project・フィールド・ビューも作らない（人が GitHub の画面で作り、このスキルは `fetch-field-map` で ID を読むだけ）。
- 見積もり値（SWP・時間）の書き込み → `github-project-field-writer` を使う。

## 共通部品（`../_shared/`、3 つの GitHub スキルで共用）
- `gh_runner.py`: `gh` の呼び出し（タイムアウト付き、`--include` で応答ヘッダーも受け取る）、書き込み間隔と時間あたりの上限、レート制限・一時的なエラーの待機・再試行、停止（exit 75）。
- `gh_include_response.py`: `gh api --include` の出力をヘッダーと本文に分ける。
- `content_guard.py` / `content_guard_rules.py`: 公開前の内容検査（上記 7 分類、exit 3）と規則の表。
- `key_map.py`: キーの文字の規則、本文のキー印の読み取り、リポジトリ全 issue（実行中のアカウントが作ったもの）からのキー → #番号 の再構築、owner でないアカウントでの実行の停止。
- `project_fields.py`: フィールド ID の取得、1 アイテム 1 フィールドの書き込み、Project への追加。
- `project_snapshot.py`: Project 全アイテムの読み取り（本文なし）。
- `write_log.py`: 書き込みログ（CSV）。`estimate_swp_payload.py`: estimate-swp レポートの埋め込みデータ読み取り。
- `tests/fake-gh.py`: テスト用の偽 `gh`（小さな架空の GitHub を JSON で再現し、呼び出しを記録）。

このスキル内の補助: `scripts/backlog_field_map_preflight.py`（field-map の検査・Project の今のフィールドとの照合・Project 名の WARN）、
`scripts/backlog_run_estimate.py`（所要時間の目安）、`scripts/backlog_plan_apply_commands.py`（`plan` / `apply`）。

## テスト
`python3 -m unittest discover -s tests`（偽の `gh` = `../_shared/tests/fake-gh.py` を使い、実 GitHub には接続しない）。
共通部品自体のテストは `../_shared` で同じコマンド。
