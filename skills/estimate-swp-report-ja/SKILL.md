---
name: estimate-swp-report-ja
description: tkm:estimate-swp が出力した HTML レポート（ベトナム語表示）に埋め込まれた検証済みデータから、同じ数値の日本語版 HTML を作る。issue ごとにスキルの評価（Scope × Complexity → SWP）と確定値、代表 issue には担当者の確定と調整の理由も並べる。lang="ja"・ベトナム語の文字 0・印の付いた数値がすべて埋め込みデータと一致・印のない数値 0・校正済み（accepted / calibrated）を検査して、照合表（estimate-swp-verification-ja.md）を出す。原本 HTML は読むだけで変更・削除しない。「SWP レポートを日本語にして」「見積もりレポートの日本語版」「照合表を作って」と言われたら、このスキルを使うこと。
metadata:
  version: "0.4.0"
---

# estimate-swp-report-ja

estimate-swp のレポートは表示がベトナム語固定（`<html lang="vi">`）で、言語の切り替えがない。
このスキルは**同じデータ**から日本語版を作り直し、数値が 1 つも変わっていないことを機械で確かめる。
翻訳ではなく再描画なので、数値・issue・親子関係は必ず原本の埋め込みデータ
（`<script id="report-data" type="application/json">`、`schemaVersion` 2.0 / `swp-matrix-v2` のみ対応）から取る。
原本の描画コードは使わない（自作）。

> **未検証（UNPROVEN）**: 実際の tkm:estimate-swp が出力した HTML での動作は、まだ確認していない。
> テストは架空のレポート（`../_shared/tests/fixtures/`）とその書き換え版だけ。実データでの初回実行
> （計画のフェーズ 07）で確かめるまで、`RESULT PASS` は「架空データで合格」の意味に限る。
>
> **校正前のレポートは不合格**: `check` は `run.calibrationStatus` が `accepted` / `calibrated`（代表 issue のレビュー済み。
> `github-project-field-writer` が見積もりの書き込みに求める条件と同じ）でなければ不合格にする。提出版は校正を終えた原本から作る。
> `render` は校正の状態に関係なく日本語版を作る（レビュー中の確認用）。

## 日本語版に出す表
- 要約・作業種別ごとの小計・親の集計（従来どおり）
- issue 一覧: SWP、タイトル、**スキルの評価（Scope × Complexity → SWP）**、**確定（Scope × Complexity → SWP）**、分野、作業種別、確信度
- 校正（代表 issue の確認）: issue、タイトル、選定理由、スキルの評価、**担当者の確定（Scope × Complexity → SWP）**、**調整の理由**。
  担当者の確定は `corrections[]`（なければ issue の `calibration.approvedScope / approvedComplexity`）、理由は `corrections[].rationale`。
  埋め込みデータにない場合は「—」と表示し、照合表の代表 issue 表にも「—（埋め込みデータに理由なし）」と書く。

## コマンド
スクリプト: `scripts/render-estimate-report-ja.py`

1. 日本語版を作る
   ```
   python3 scripts/render-estimate-report-ja.py render --html <原本.html> --out reports/<名前>-ja.html [--repo owner/name]
   ```
   - 既存ファイルは上書きしない（`--force` で上書き）。`--out` に原本と同じパスは指定できない。
   - 書き出す前に、読み手に見える文字列（本文・リンク先・埋め込みデータ）を `../_shared/content_guard.py` で検査する
     （ベトナム語・制御文字・内部パス・秘密情報・メール・公開しない用語・社内 URL / 社名・`--repo` 以外のリポジトリの
     GitHub URL）。1 件でも当たれば書き出さずに exit 3。該当する自由記述は `--translations` で置き換える。
     `--repo` を省略したときは、`issueRef` のリポジトリが 1 つならそれを許す。
   - 出典欄に `run.sourceLabel` は出さない（組織名・非公開の Project 名を含みうるため）。固定の文
     「estimate-swp の評価結果（対象の名前は公開版に載せない。原本 HTML の sha256 で照合）」を出す。
   - JavaScript・外部読み込みなし。表示する数値には照合用の印（`data-v`）、自由記述には `data-t`、
     出所欄（原本のファイル名・sha256 の先頭）には `data-x` を付ける。
2. 検査して照合表を作る
   ```
   python3 scripts/render-estimate-report-ja.py check --html <原本.html> --ja reports/<名前>-ja.html \
     --verification-md reports/estimate-swp-verification-ja.md --source-skill "tkm:estimate-swp <版>" [--repo owner/name]
   ```
   検査項目（1 つでも不合格なら exit 1）:
   - `<html lang="ja">` である
   - ベトナム語の文字（声調記号付きの母音とストローク付きの d。合成済み・分解済み〈NFD〉のどちらも数える）が 0
   - `data-v` の印が付いた数値すべてが、原本の埋め込みデータから再計算した値と一致
   - 表示される本文（タグ・属性・`<style>`・`<script>` を除く）で、印のない数値が 0。例外は次のものだけ: 固定文（算定方法の難易度の目安、語「sha256」）、
     埋め込みデータの文字列か訳文と完全一致する自由記述（`data-t`）、出所欄（`data-x`、原本と照合）
   - 網羅: すべての表の数値の欄（全 issue の SWP と「確定」欄の SWP・初期 / 確定の Scope / Complexity、全親の SWP と子の数、
     合計・確信度別・分割の提案・分解が必要な親・修正数・ルール数、作業種別、代表、親ごとの件数、注意事項の件数）が表示されている。
     必要なキーは、埋め込みデータから決めた一覧と、埋め込みデータから描き直した版の `data-v` の全キーの和
   - 印の並び: 日本語版の印（`data-v` のキーと数値、`data-t` の文、`data-x` の出所）の順番と中身が、同じ訳文で
     埋め込みデータから描き直した版と完全に一致する（数値の欄を `data-t` の文に置き換える・欄を消す・欄を足す、はすべて不合格）
   - 訳文（`--translations` を渡したとき）: 原文が埋め込みデータの文字列であり、訳文の数値（NFKC 後の算用数字）が
     原文の数値と同じ（順番は問わない）
   - 内容検査: 日本語版の本文・リンク先・埋め込みデータに、公開リポジトリに出せない内容がない（render と同じ規則）
   - 親の SWP = 子の SWP の合計（集計 `derived` の親だけ。`needs-breakdown` などほかの親は検査しない）。
     子が埋め込みデータにない、または子の SWP が空なら不合格（0 として数えない）。代表の担当者確定 = 最終の Scope × Complexity
   - 出所: 日本語版に記録した原本 HTML の sha256 と、埋め込みデータの sha256 が一致
   - スクリプト・外部読み込み・イベント属性がない（リンクは `https://github.com/` で始まるものだけ。render は issue の URL だけを出す）
   - 日本語版に表示する列挙値すべて（分野・作業種別・確信度・根拠の種類・issue の校正・代表の選定理由・処理レベル・
     レポートの校正・親の種別・親の集計）が `references/label-map-ja.json` にある（未登録の値は原文のまま表示されるので不合格）。
     表示しない `state` は対象外
   - 校正済み: `run.calibrationStatus` が `accepted` / `calibrated`（`pending`・`skipped`・空は不合格）
   照合表には上記の結果、検査範囲の説明、代表 issue 表、原本と日本語版の sha256、原本を作ったスキルの版、
   本スキルの版、実行コマンドを書く。数値の照合表の左列は「埋め込みデータから再計算」した値。
   照合表も書き出す前に内容検査を通す。当たれば照合表は書き出さず、不合格（exit 1）。
   実行コマンド欄では、ファイルを指す引数（`--html` `--ja` `--out` `--verification-md` `--translations` と絶対パス）を
   すべてファイル名だけにする（作業フォルダの構成がわかる相対パスやローカルのユーザー名を出さない）。

## 自由記述（根拠・前提・不明点・注意事項・調整の理由）の扱い
estimate-swp の根拠などは評価したエージェントの言語（多くはベトナム語）で書かれている。順番に:
1. `--translations` の JSON（`{"原文": "日本語訳"}`）に完全一致する原文があれば、その訳を使う。
2. ベトナム語の文字を含まない原文はそのまま使う。
3. それ以外は「（原文がベトナム語のため省略。原本 HTML を参照）」と表示し、件数を注意事項に書く。
訳を使ったときは `check` にも同じ `--translations` を渡す（訳文を照合するため）。
訳文にベトナム語の文字がある → render・check とも exit 2（check は検査の前に止まる）。原文が埋め込みデータにない・訳文の数値が
原文の数値と違う → render は exit 2、check は不合格（exit 1）
（原文が数を語で書いていれば〈「一つ・二つ」にあたる語〉、訳文も「ひとつ・ふたつ」のように語で書く。数字を足さない）。
数値・列挙値は訳の対象外で、必ず埋め込みデータとラベル表から出す。

## 提出物の置き方
- 原本 HTML（ベトナム語表示）は公開・提出するリポジトリに置かない。非公開の場所（例: `.gitignore` 済みの
  `private/` フォルダ）に保管し、照合表の sha256 でたどれるようにする。
- 提出するのは日本語版 HTML と照合表だけ。両方を同じ `reports/` に置く。
- 照合表のコマンド欄ではファイルの引数をファイル名に縮める（ローカルのユーザー名・作業フォルダの構成を出さないため）。

## 終了コード
| コード | 意味 |
|---|---|
| 0 | 正常（check は全項目合格） |
| 1 | check の不合格（校正前のレポートを含む）、照合表が内容検査に当たった、埋め込みデータの読み込みエラー |
| 2 | 引数の誤り、訳文の誤り（render: ベトナム語・埋め込みデータにない原文・数値の違い。check: 訳文のベトナム語） |
| 3 | render が内容検査で停止（日本語版 HTML は書き出していない） |

読む項目の一覧は `references/payload-fields.md`。

## テスト
`python3 -m unittest discover -s tests`（架空のレポート `../_shared/tests/fixtures/example-estimate-swp-original.html` と、
テスト内でその埋め込みデータを書き換えた版を使う）。
