# 埋め込みデータから読む項目

原本 HTML の `<script id="report-data" type="application/json">` の JSON（estimate-swp の
assessment contract、`schemaVersion` 2.0・`scoringModelVersion` swp-matrix-v2。違う版は render / check とも exit 1）のうち、日本語版で使うのは次の項目だけ。
issue の本文（`body`）は原本でも埋め込まれておらず、日本語版でも扱わない（あれば埋め込みデータから外す）。
Scope・Complexity（初期・確定・担当者の確定）は表示しない。埋め込みデータ（`check` で原本と照合）と照合表の代表 issue 表にだけある。

| 場所 | 項目 | 日本語版での使い方 |
|---|---|---|
| `run` | `generatedAt`, `processingLevel`, `calibrationStatus` | 見出しの情報欄（`sourceLabel` は組織名などを含みうるので出さず、固定の文にする。埋め込みデータでも同じ固定の文）。`check` は `calibrationStatus` が accepted / calibrated でなければ不合格 |
| `issues[]` | `issueRef`, `url`, `title`, `parentRef` | issue 一覧（親ごとにまとめ、親ごとの件数も照合）。URL は `https://github.com/<owner>/<repo>/issues/<n>` の形のときだけリンク |
| `issues[]` | `initialSWP`, `finalSWP` | SWP 列、詳細の点数（変わったときだけ初期 → 校正後）、代表 issue 表の「スキルの評価（SWP）」 |
| `issues[]` | `initialScope`, `initialComplexity`, `finalScope`, `finalComplexity` | 表示しない。埋め込みデータで原本と照合（`validate_payload` が SWP = 表の値を確かめる） |
| `issues[]` | `primaryDiscipline`, `workType`, `confidence`, `evidenceStatus` | ラベル表で日本語にして表示 |
| `issues[]` | `rationale`, `assumptions`, `gaps`, `splitRecommended`, `splitReason`, `calibration.status` | 詳細欄と、リスクと対応の表（自由記述は訳文で置き換える。訳のないものがあれば `check` は不合格） |
| `parents[]` | `issueRef`, `url`, `title`, `issueType`, `aggregationStatus`, `childRefs`, `finalSWP` | 親の集計表。SWP は `finalSWP` をそのまま出し、null なら「—」（`needs-breakdown` の親は通常 null）。`needs-breakdown` の親は要約に件数と番号を出す |
| `representatives[]` | `issueRef`, `selectionReasons` | 校正の表（代表 issue ごとにスキルの評価〈初期 SWP〉も表示） |
| `corrections[]` | `representative.issueRef`, `approvedScope`, `approvedComplexity`, `rationale` | 校正の表の「担当者の確定（SWP）」と「調整の理由」。ない場合は「—」。軸の値は照合表の代表 issue 表にだけ出す |
| `issues[].calibration` | `approvedScope`, `approvedComplexity` | `corrections[]` に代表の項目がないときの担当者の確定 |
| `calibrationRules[]` | 件数のみ | 校正の表の下 |
| `caveats[]` | 全文 | 注意事項（訳文で置き換える。訳のない自由記述があれば `check` は不合格） |
| `run` | `selection`（状態の規則・既存見積の確認・絞り込み・除外の件数）, `assessors`, `assessorAgreement` | 範囲の帯（`selection`）、評価 B の要約（一致 / 軽微な差 / 大きな差 / 区分違い）と、B が使えなかったときの理由 |
| `issues[]` | `labels`, `state` | 作業種別の内訳（Build / Test・QA / Bug・rework）、`team:*` ラベルがあるときだけ担当チームの負荷表、クローズの印 |
| `issues[]` | `existingEstimate` | 再見積のときの「既存の見積 → 新しい SWP」の比較表 |
| `issues[]` | `assessorCheck`（`agreement`, `witness.swp`, `witness.rationale`） | 差のある行の印、`A · B` の幅、詳細欄の評価 B の SWP と根拠（訳文）。B はどの合計にも入れない |
| `issues[]` | `provenance`, `functionRef`, `activityType` | 詳細欄（取得元・機能・作業） |
| `calibrationRules[]` | 分野・作業種別・帯の移動 | 校正の表の下に、分野・作業種別ごとの規則として表示 |

## 要約の数値の定義（検査でも同じ定義で再計算する）
- SWP 合計 = `issues[].finalSWP` の合計（親は含めない。二重計上になるため）
- issue 数 = `issues` の件数、親の数 = `parents` の件数
- 確信度別 = `confidence` が high / medium / low の件数
- 分割の提案 = `splitRecommended` が true の件数
- 分解が必要な親 = `aggregationStatus` が `needs-breakdown` の件数
- 作業種別ごと = `workType` ごとの件数と `finalSWP` の合計
- 親ごとの件数 = `parentRef` ごとの issue 数（親なしは `-`）
- 親の SWP（検査のみ）= 集計 `derived` の親について、`childRefs` の `finalSWP` の合計（子がない・子の `finalSWP` が null なら不合格）
- 注意事項の件数 = 自由記述を省略・訳文に置換した件数（同じ訳文で描画し直して数える）

## 日本語版に埋め込むデータ
- `<script id="report-data" type="application/json">`: 原本の埋め込みデータと同じ構造の全項目（原本スキルの契約 9 と
  "Embedded audit payload"）。変えるのは次の欄だけ: 自由記述（`scripts/ja_report_payload.py` の `FREE_TEXT_FIELDS`:
  `issues[].title / rationale / assumptions[] / gaps[] / splitReason / supportingEvidence[] / provenance.notes[] /
  assessorCheck.witness.rationale`、`parents[].title / provenance.notes[]`、`corrections[].rationale`、`caveats[]`）を
  表示と同じ規則で日本語に（訳文 > 日本語・識別子の原文 > 省略の文）、`run.sourceLabel` を出典欄と同じ固定の文に。
  `body` は入れない。数値・軸・列挙値・署名・ラベル・状態・URL・`run.sourceUrl`・ルール ID はそのまま。
  エスケープは原本スキルの `_safe_json` と同じ（`<` `>` `&` U+2028 U+2029）。
- `<script id="report-data-ja" type="application/json">`: 原本ファイル名、原本 HTML の sha256、埋め込みデータの sha256
  （原本の埋め込みデータをキー順に並べた JSON）、表示で省略・置換した自由記述の件数。
