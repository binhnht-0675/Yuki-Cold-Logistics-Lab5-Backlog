# 埋め込みデータから読む項目

原本 HTML の `<script id="report-data" type="application/json">` の JSON（estimate-swp の
assessment contract、`schemaVersion` 2.0・`scoringModelVersion` swp-matrix-v2。違う版は render / check とも exit 1）のうち、日本語版で使うのは次の項目だけ。
issue の本文（`body`）は原本でも埋め込まれておらず、日本語版でも扱わない。

| 場所 | 項目 | 日本語版での使い方 |
|---|---|---|
| `run` | `generatedAt`, `processingLevel`, `calibrationStatus` | 見出しの情報欄（`sourceLabel` は組織名などを含みうるので出さず、固定の文にする）。`check` は `calibrationStatus` が accepted / calibrated でなければ不合格 |
| `issues[]` | `issueRef`, `url`, `title`, `parentRef` | issue 一覧（親ごとにまとめ、親ごとの件数も照合）。URL は `https://github.com/<owner>/<repo>/issues/<n>` の形のときだけリンク |
| `issues[]` | `initialScope`, `initialComplexity`, `initialSWP` | 「スキルの評価（Scope × Complexity → SWP）」列 |
| `issues[]` | `finalScope`, `finalComplexity`, `finalSWP` | SWP 列と「確定（Scope × Complexity → SWP）」列 |
| `issues[]` | `primaryDiscipline`, `workType`, `confidence`, `evidenceStatus` | ラベル表で日本語にして表示 |
| `issues[]` | `rationale`, `assumptions`, `gaps`, `splitRecommended`, `splitReason`, `calibration.status` | 詳細欄（自由記述は訳／省略の規則に従う） |
| `parents[]` | `issueRef`, `url`, `title`, `issueType`, `aggregationStatus`, `childRefs`, `finalSWP` | 親の集計表。SWP は `finalSWP` をそのまま出し、null なら「—」（`needs-breakdown` の親は通常 null）。`needs-breakdown` の親は要約に件数と番号を出す |
| `representatives[]` | `issueRef`, `selectionReasons` | 校正の表（代表 issue ごとにスキルの評価も表示） |
| `corrections[]` | `representative.issueRef`, `approvedScope`, `approvedComplexity`, `rationale` | 校正の表の「担当者の確定（Scope × Complexity → SWP）」と「調整の理由」。ない場合は「—」 |
| `issues[].calibration` | `approvedScope`, `approvedComplexity` | `corrections[]` に代表の項目がないときの担当者の確定 |
| `calibrationRules[]` | 件数のみ | 校正の表の下 |
| `caveats[]` | 全文 | 注意事項（訳／省略の規則に従う） |

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
`<script id="report-data-ja" type="application/json">` に、原本ファイル名、原本 HTML の sha256、
埋め込みデータの sha256（キー順に並べた JSON）、省略・置換した自由記述の件数を入れる。数値そのものは入れない
（表示された数値は `data-v` の印から検査し、印のない数値は 0 であることを検査する）。
