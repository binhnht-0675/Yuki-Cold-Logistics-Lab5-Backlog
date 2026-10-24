# estimate-swp 照合表（日本語版 HTML と原本 HTML）

- 判定: **合格**
- 原本 HTML: `estimate-swp-prototype-reference-261023-1931.html`（sha256 `c48d625eb8dce325ff2b563457a50aa37d1f2c16ac1519b818bd796c178d5144`。公開リポジトリには置かず、sha256 で照合）
- 日本語版 HTML: `estimate-swp-prototype-reference-261023-1931-ja.html`（sha256 `b63faa42cbda86b9ba0375e0dd3d2e6bd34a502295cb4a3976ec0d1b3e8515e2`）
- 埋め込みデータの sha256（正規化 JSON）: `18046c9de4897ae594e014907ded530170ff4bbcadc5b416d46b57d2dd77689f`
- 原本を作ったスキル: tkm:estimate-swp 2.1.0-beta.1
- 変換スキル: estimate-swp-report-ja 0.7.0
- 照合日時: 2026-10-23T19:31:43+07:00
- 実行したコマンド: `python3 scripts/render-estimate-report-ja.py check --html estimate-swp-prototype-reference-261023-1931.html --ja estimate-swp-prototype-reference-261023-1931-ja.html --verification-md estimate-swp-prototype-reference-verification-ja-261023.md --source-skill 'tkm:estimate-swp 2.1.0-beta.1' --repo binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog --translations translations.ja.json`
- 数値の検査範囲: data-v の印が付いた数値は、すべて原本の埋め込みデータから再計算した値と照合する。印のない数値は、表示される本文（タグ・属性・style・script を除く）で、固定文（算定方法の難易度の目安、語「sha256」）、照合済みの自由記述（data-t: 埋め込みデータの文字列か訳文と完全一致）、出所欄（data-x: 原本のファイル名・sha256 の先頭・照合表の名前）を除いて 0 個であることを検査する。

## 検査項目

| 検査 | 結果 | 詳細 |
|---|---|---|
| lang="ja" | 合格 |  |
| 照合表の名前 = 日本語版 HTML が案内する名前 | 合格 | HTML: estimate-swp-prototype-reference-verification-ja-261023.md / 照合表: estimate-swp-prototype-reference-verification-ja-261023.md |
| ベトナム語の文字（NFC / NFD とも） | 合格 | 0 文字 |
| 数値 = 埋め込みデータ（data-v の印の付いた数値） | 合格 | 照合 804 箇所、不一致 0 |
| 網羅（全表の数値の欄: issue・確定・親・合計・分割の提案・作業種別・代表・件数） | 合格 | 不足 0 |
| 印の並び = 埋め込みデータから描き直した版（数値の欄を自由記述で置き換えていない） | 合格 | 違い 0 |
| 訳文（原文が埋め込みデータにある・数値が原文と同じ） | 合格 | 不一致 0 |
| 訳のない自由記述 0（日本語でない記述は訳文で置き換え） | 合格 | 0 件・埋め込みデータ 0 件 |
| 表示部に Scope × Complexity の表記・軸の値がない（埋め込みデータと折りたたみの「技術的な詳細」を除く） | 合格 | 該当 0 |
| 内容検査（公開リポジトリに出せない内容がない） | 合格 | 該当 0 |
| 印のない数値 0（固定文・自由記述・出所欄を除く） | 合格 | 0 個 |
| 自由記述 = 埋め込みデータ／訳文 | 合格 | 不明 0 |
| 親 = 子の合計（集計 derived） | 合格 |  |
| 代表の担当者確定 = 最終の Scope × Complexity | 合格 |  |
| 出所（原本 sha256・データ sha256） | 合格 | 原本 一致 / データ 一致 |
| 外部読み込み・スクリプトなし（固定の表示用スクリプトだけ） | 合格 |  |
| 埋め込みデータ（全項目）が原本スキルの validate_payload に合格 | 合格 |  |
| 埋め込みデータの自由記述以外の全項目 = 原本の埋め込みデータ（Scope・Complexity・列挙値・署名を含む。issue 本文は入れない） | 合格 |  |
| 埋め込みデータの自由記述 = 訳文（訳文表の原文 → 訳。日本語の原文と識別子はそのまま。対象の名前は固定の文） | 合格 | 自由記述 846 箇所、不一致 0（訳文に置換 656・省略 0） |
| 埋め込みデータの issue・親 = 表示した行（件数・識別子） | 合格 | issue 174・親 12 |
| 埋め込みデータのエスケープ（< > & U+2028 U+2029）・issue 本文なし・ベトナム語の文字なし | 合格 | 未エスケープ 0 種・本文 0 件・ベトナム語 0 文字 |
| 列挙値の日本語化 | 合格 |  |
| 校正済み（calibrationStatus が accepted / calibrated） | 合格 | calibrationStatus = calibrated |

## 代表 issue（スキルの評価・担当者の確定・調整の理由）

| issue | スキルの評価（Scope × Complexity → SWP） | 担当者の確定（Scope × Complexity → SWP） | 調整の理由 |
|---|---|---|---|
| REF-01-T02 | 1 × 1 → 1 | 2 × 1 → 3 | （ベトナム語のため日本語版 HTML を参照） |
| REF-04-T19 | 2 × 1 → 3 | 2 × 1 → 3 | （ベトナム語のため日本語版 HTML を参照） |
| REF-10-T24 | 5 × 2 → 8 | 5 × 2 → 8 | （ベトナム語のため日本語版 HTML を参照） |
| REF-04-T22 | 5 × 2 → 8 | 5 × 2 → 8 | （ベトナム語のため日本語版 HTML を参照） |
| REF-01-T04 | 1 × 1 → 1 | 2 × 1 → 3 | （ベトナム語のため日本語版 HTML を参照） |

## 数値の照合（埋め込みデータから再計算 → 日本語版の表示）

| 項目 | 埋め込みデータから再計算 | 日本語版 | 一致 |
|---|---|---|---|
| 要約 SWP 合計 SWP | 515 | 515 | ○ |
| 要約 issue 数 | 174 | 174 | ○ |
| 要約 オープン | 174 | 174 | ○ |
| 要約 クローズ | 0 | 0 | ○ |
| 要約 親の数 | 12 | 12 | ○ |
| 区分 不具合・手戻り SWP | 10 | 10 | ○ |
| 要約 不確かさの幅 最小 | 463 | 463 | ○ |
| 要約 不確かさの幅 最大 | 584 | 584 | ○ |
| 要約 幅を付けた issue 数 | 63 | 63 | ○ |
| 要約 分解が必要な親 件数 | 0 | 0 | ○ |
| 要約 分割提案 件数 | 0 | 0 | ○ |
| 要約 分割提案 SWP | 0 | 0 | ○ |
| 要約 確信度 高 | 111 | 111 | ○ |
| 要約 確信度 中 | 63 | 63 | ○ |
| 要約 確信度 低 | 0 | 0 | ○ |
| 要約 確信度「低」 SWP | 0 | 0 | ○ |
| 要約 SWP 合計 SWP | 515 | 515 | ○ |
| 要約 不確かさの幅 最小 | 463 | 463 | ○ |
| 要約 不確かさの幅 最大 | 584 | 584 | ○ |
| 要約 オープン | 174 | 174 | ○ |
| 要約 クローズ | 0 | 0 | ○ |
| 要約 確信度 高 | 111 | 111 | ○ |
| 要約 確信度 中 | 63 | 63 | ○ |
| 要約 確信度 低 | 0 | 0 | ○ |
| 評価 A・B 二回評価した issue 件数 | 174 | 174 | ○ |
| 評価 A・B 一致 件数 | 53 | 53 | ○ |
| 評価 A・B 軽微な差 件数 | 77 | 77 | ○ |
| 評価 A・B 大きな差 件数 | 0 | 0 | ○ |
| 評価 A・B 区分違い 件数 | 44 | 44 | ○ |
| 区分 計画の合計 SWP | 505 | 505 | ○ |
| 区分 計画の合計 割合（%） | 98 | 98 | ○ |
| 区分 不具合・手戻り SWP | 10 | 10 | ○ |
| 区分 不具合・手戻り 割合（%） | 2 | 2 | ○ |
| 区分 構築 件数 | 142 | 142 | ○ |
| 区分 構築 SWP | 376 | 376 | ○ |
| 区分 テスト・品質確認 件数 | 30 | 30 | ○ |
| 区分 テスト・品質確認 SWP | 129 | 129 | ○ |
| 区分 計画の合計 件数 | 172 | 172 | ○ |
| 区分 計画の合計 SWP | 505 | 505 | ○ |
| 区分 不具合・手戻り 件数 | 2 | 2 | ○ |
| 区分 不具合・手戻り SWP | 10 | 10 | ○ |
| 区分 全 issue の合計 件数 | 174 | 174 | ○ |
| 区分 全 issue の合計 SWP | 515 | 515 | ○ |
| 作業種別 インフラ 件数 | 3 | 3 | ○ |
| 作業種別 インフラ SWP | 8 | 8 | ○ |
| 作業種別 機能開発 件数 | 134 | 134 | ○ |
| 作業種別 機能開発 SWP | 344 | 344 | ○ |
| 作業種別 テスト設計 件数 | 29 | 29 | ○ |
| 作業種別 テスト設計 SWP | 124 | 124 | ○ |
| 作業種別 デプロイ 件数 | 1 | 1 | ○ |
| 作業種別 デプロイ SWP | 6 | 6 | ○ |
| 作業種別 不具合修正 件数 | 2 | 2 | ○ |
| 作業種別 不具合修正 SWP | 10 | 10 | ○ |
| 作業種別 移行 件数 | 2 | 2 | ○ |
| 作業種別 移行 SWP | 12 | 12 | ○ |
| 作業種別 テスト実施 件数 | 1 | 1 | ○ |
| 作業種別 テスト実施 SWP | 5 | 5 | ○ |
| 作業種別 調査 件数 | 1 | 1 | ○ |
| 作業種別 調査 SWP | 4 | 4 | ○ |
| 作業種別 リファクタリング 件数 | 1 | 1 | ○ |
| 作業種別 リファクタリング SWP | 2 | 2 | ○ |
| SWP の分布 SWP 1 値 | 1 | 1 | ○ |
| SWP の分布 SWP 1 件数 | 52 | 52 | ○ |
| SWP の分布 SWP 2 値 | 2 | 2 | ○ |
| SWP の分布 SWP 2 件数 | 19 | 19 | ○ |
| SWP の分布 SWP 3 値 | 3 | 3 | ○ |
| SWP の分布 SWP 3 件数 | 44 | 44 | ○ |
| SWP の分布 SWP 4 値 | 4 | 4 | ○ |
| SWP の分布 SWP 4 件数 | 19 | 19 | ○ |
| SWP の分布 SWP 5 値 | 5 | 5 | ○ |
| SWP の分布 SWP 5 件数 | 27 | 27 | ○ |
| SWP の分布 SWP 6 値 | 6 | 6 | ○ |
| SWP の分布 SWP 6 件数 | 11 | 11 | ○ |
| SWP の分布 SWP 8 値 | 8 | 8 | ○ |
| SWP の分布 SWP 8 件数 | 2 | 2 | ○ |
| 要約 時間の換算率（既定） | 1 | 1 | ○ |
| 親ごとの件数 REF-01 | 6 | 6 | ○ |
| 親ごとの小計 REF-01 SWP | 17 | 17 | ○ |
| issue REF-01-T01 最終 SWP | 3 | 3 | ○ |
| issue REF-01-T01 詳細の SWP | 3 | 3 | ○ |
| issue REF-01-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-01-T02 最終 SWP | 3 | 3 | ○ |
| issue REF-01-T02 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-01-T02 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-01-T02 詳細の初期 SWP | 1 | 1 | ○ |
| issue REF-01-T02 詳細の SWP | 3 | 3 | ○ |
| issue REF-01-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-01-T03 最終 SWP | 4 | 4 | ○ |
| issue REF-01-T03 詳細の SWP | 4 | 4 | ○ |
| issue REF-01-T03 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-01-T04 最終 SWP | 3 | 3 | ○ |
| issue REF-01-T04 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-01-T04 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-01-T04 詳細の初期 SWP | 1 | 1 | ○ |
| issue REF-01-T04 詳細の SWP | 3 | 3 | ○ |
| issue REF-01-T04 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-01-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-01-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-01-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-01-T06 最終 SWP | 3 | 3 | ○ |
| issue REF-01-T06 詳細の SWP | 3 | 3 | ○ |
| issue REF-01-T06 評価 B の SWP（詳細） | 3 | 3 | ○ |
| 親ごとの件数 REF-02 | 9 | 9 | ○ |
| 親ごとの小計 REF-02 SWP | 35 | 35 | ○ |
| issue REF-02-T01 最終 SWP | 3 | 3 | ○ |
| issue REF-02-T01 詳細の SWP | 3 | 3 | ○ |
| issue REF-02-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-02-T02 最終 SWP | 5 | 5 | ○ |
| issue REF-02-T02 詳細の SWP | 5 | 5 | ○ |
| issue REF-02-T02 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-02-T03 最終 SWP | 5 | 5 | ○ |
| issue REF-02-T03 詳細の SWP | 5 | 5 | ○ |
| issue REF-02-T03 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-02-T04 最終 SWP | 4 | 4 | ○ |
| issue REF-02-T04 詳細の SWP | 4 | 4 | ○ |
| issue REF-02-T04 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-02-T05 最終 SWP | 4 | 4 | ○ |
| issue REF-02-T05 詳細の SWP | 4 | 4 | ○ |
| issue REF-02-T05 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-02-T06 最終 SWP | 5 | 5 | ○ |
| issue REF-02-T06 詳細の SWP | 5 | 5 | ○ |
| issue REF-02-T06 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-02-T07 最終 SWP | 3 | 3 | ○ |
| issue REF-02-T07 評価 A の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-02-T07 評価 B の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-02-T07 詳細の SWP | 3 | 3 | ○ |
| issue REF-02-T07 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-02-T08 最終 SWP | 5 | 5 | ○ |
| issue REF-02-T08 詳細の SWP | 5 | 5 | ○ |
| issue REF-02-T08 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-02-T09 最終 SWP | 1 | 1 | ○ |
| issue REF-02-T09 詳細の SWP | 1 | 1 | ○ |
| issue REF-02-T09 評価 B の SWP（詳細） | 1 | 1 | ○ |
| 親ごとの件数 REF-03 | 9 | 9 | ○ |
| 親ごとの小計 REF-03 SWP | 33 | 33 | ○ |
| issue REF-03-T01 最終 SWP | 3 | 3 | ○ |
| issue REF-03-T01 詳細の SWP | 3 | 3 | ○ |
| issue REF-03-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-03-T02 最終 SWP | 5 | 5 | ○ |
| issue REF-03-T02 詳細の SWP | 5 | 5 | ○ |
| issue REF-03-T02 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-03-T03 最終 SWP | 3 | 3 | ○ |
| issue REF-03-T03 詳細の SWP | 3 | 3 | ○ |
| issue REF-03-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-03-T04 最終 SWP | 1 | 1 | ○ |
| issue REF-03-T04 詳細の SWP | 1 | 1 | ○ |
| issue REF-03-T04 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-03-T05 最終 SWP | 4 | 4 | ○ |
| issue REF-03-T05 詳細の SWP | 4 | 4 | ○ |
| issue REF-03-T05 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-03-T06 最終 SWP | 2 | 2 | ○ |
| issue REF-03-T06 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-03-T06 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-03-T06 詳細の SWP | 2 | 2 | ○ |
| issue REF-03-T06 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-03-T07 最終 SWP | 6 | 6 | ○ |
| issue REF-03-T07 評価 A の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-03-T07 評価 B の SWP（差の表示） | 10 | 10 | ○ |
| issue REF-03-T07 詳細の SWP | 6 | 6 | ○ |
| issue REF-03-T07 評価 B の SWP（詳細） | 10 | 10 | ○ |
| issue REF-03-T08 最終 SWP | 4 | 4 | ○ |
| issue REF-03-T08 詳細の SWP | 4 | 4 | ○ |
| issue REF-03-T08 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-03-T09 最終 SWP | 5 | 5 | ○ |
| issue REF-03-T09 詳細の SWP | 5 | 5 | ○ |
| issue REF-03-T09 評価 B の SWP（詳細） | 5 | 5 | ○ |
| 親ごとの件数 REF-04 | 22 | 22 | ○ |
| 親ごとの小計 REF-04 SWP | 62 | 62 | ○ |
| issue REF-04-T01 最終 SWP | 5 | 5 | ○ |
| issue REF-04-T01 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-04-T01 評価 B の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-04-T01 詳細の SWP | 5 | 5 | ○ |
| issue REF-04-T01 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-04-T02 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T02 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T03 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T03 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T04 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T04 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T04 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T05 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T05 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T05 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T06 最終 SWP | 4 | 4 | ○ |
| issue REF-04-T06 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-04-T06 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-04-T06 詳細の SWP | 4 | 4 | ○ |
| issue REF-04-T06 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-04-T07 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T07 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T07 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T08 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T08 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-04-T08 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-04-T08 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T08 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T09 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T09 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T09 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T10 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T10 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T10 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T11 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T11 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T11 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T12 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T12 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T12 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T13 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T13 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-04-T13 評価 B の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-04-T13 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T13 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-04-T14 最終 SWP | 1 | 1 | ○ |
| issue REF-04-T14 詳細の SWP | 1 | 1 | ○ |
| issue REF-04-T14 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T15 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T15 評価 A の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-04-T15 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-04-T15 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T15 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T16 最終 SWP | 2 | 2 | ○ |
| issue REF-04-T16 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-04-T16 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-04-T16 詳細の SWP | 2 | 2 | ○ |
| issue REF-04-T16 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-04-T17 最終 SWP | 4 | 4 | ○ |
| issue REF-04-T17 詳細の SWP | 4 | 4 | ○ |
| issue REF-04-T17 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-04-T18 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T18 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T18 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T19 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T19 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T19 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T20 最終 SWP | 3 | 3 | ○ |
| issue REF-04-T20 詳細の SWP | 3 | 3 | ○ |
| issue REF-04-T20 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-04-T21 最終 SWP | 5 | 5 | ○ |
| issue REF-04-T21 詳細の SWP | 5 | 5 | ○ |
| issue REF-04-T21 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-04-T22 最終 SWP | 8 | 8 | ○ |
| issue REF-04-T22 詳細の SWP | 8 | 8 | ○ |
| issue REF-04-T22 評価 B の SWP（詳細） | 8 | 8 | ○ |
| 親ごとの件数 REF-05 | 18 | 18 | ○ |
| 親ごとの小計 REF-05 SWP | 43 | 43 | ○ |
| issue REF-05-T01 最終 SWP | 2 | 2 | ○ |
| issue REF-05-T01 詳細の SWP | 2 | 2 | ○ |
| issue REF-05-T01 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-05-T02 最終 SWP | 2 | 2 | ○ |
| issue REF-05-T02 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-05-T02 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-05-T02 詳細の SWP | 2 | 2 | ○ |
| issue REF-05-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-05-T03 最終 SWP | 2 | 2 | ○ |
| issue REF-05-T03 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-05-T03 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-05-T03 詳細の SWP | 2 | 2 | ○ |
| issue REF-05-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-05-T04 最終 SWP | 4 | 4 | ○ |
| issue REF-05-T04 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-05-T04 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-05-T04 詳細の SWP | 4 | 4 | ○ |
| issue REF-05-T04 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-05-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T06 最終 SWP | 4 | 4 | ○ |
| issue REF-05-T06 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-05-T06 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-05-T06 詳細の SWP | 4 | 4 | ○ |
| issue REF-05-T06 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-05-T07 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T07 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T07 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T08 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T08 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T08 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T09 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T09 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T09 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T10 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T10 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T10 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T11 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T11 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T11 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T12 最終 SWP | 2 | 2 | ○ |
| issue REF-05-T12 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-05-T12 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-05-T12 詳細の SWP | 2 | 2 | ○ |
| issue REF-05-T12 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T13 最終 SWP | 1 | 1 | ○ |
| issue REF-05-T13 詳細の SWP | 1 | 1 | ○ |
| issue REF-05-T13 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-05-T14 最終 SWP | 3 | 3 | ○ |
| issue REF-05-T14 詳細の SWP | 3 | 3 | ○ |
| issue REF-05-T14 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-05-T15 最終 SWP | 3 | 3 | ○ |
| issue REF-05-T15 詳細の SWP | 3 | 3 | ○ |
| issue REF-05-T15 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-05-T16 最終 SWP | 5 | 5 | ○ |
| issue REF-05-T16 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-05-T16 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-05-T16 詳細の SWP | 5 | 5 | ○ |
| issue REF-05-T16 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-05-T17 最終 SWP | 4 | 4 | ○ |
| issue REF-05-T17 詳細の SWP | 4 | 4 | ○ |
| issue REF-05-T17 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-05-T18 最終 SWP | 5 | 5 | ○ |
| issue REF-05-T18 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-05-T18 評価 B の SWP（差の表示） | 8 | 8 | ○ |
| issue REF-05-T18 詳細の SWP | 5 | 5 | ○ |
| issue REF-05-T18 評価 B の SWP（詳細） | 8 | 8 | ○ |
| 親ごとの件数 REF-06 | 13 | 13 | ○ |
| 親ごとの小計 REF-06 SWP | 42 | 42 | ○ |
| issue REF-06-T01 最終 SWP | 2 | 2 | ○ |
| issue REF-06-T01 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-06-T01 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-06-T01 詳細の SWP | 2 | 2 | ○ |
| issue REF-06-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-06-T02 最終 SWP | 2 | 2 | ○ |
| issue REF-06-T02 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-06-T02 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-06-T02 詳細の SWP | 2 | 2 | ○ |
| issue REF-06-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-06-T03 最終 SWP | 6 | 6 | ○ |
| issue REF-06-T03 詳細の SWP | 6 | 6 | ○ |
| issue REF-06-T03 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-06-T04 最終 SWP | 6 | 6 | ○ |
| issue REF-06-T04 詳細の SWP | 6 | 6 | ○ |
| issue REF-06-T04 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-06-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-06-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-06-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-06-T06 最終 SWP | 1 | 1 | ○ |
| issue REF-06-T06 詳細の SWP | 1 | 1 | ○ |
| issue REF-06-T06 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-06-T07 最終 SWP | 1 | 1 | ○ |
| issue REF-06-T07 詳細の SWP | 1 | 1 | ○ |
| issue REF-06-T07 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-06-T08 最終 SWP | 3 | 3 | ○ |
| issue REF-06-T08 評価 A の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-06-T08 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-06-T08 詳細の SWP | 3 | 3 | ○ |
| issue REF-06-T08 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-06-T09 最終 SWP | 3 | 3 | ○ |
| issue REF-06-T09 評価 A の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-06-T09 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-06-T09 詳細の SWP | 3 | 3 | ○ |
| issue REF-06-T09 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-06-T10 最終 SWP | 5 | 5 | ○ |
| issue REF-06-T10 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-06-T10 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-06-T10 詳細の SWP | 5 | 5 | ○ |
| issue REF-06-T10 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-06-T11 最終 SWP | 3 | 3 | ○ |
| issue REF-06-T11 詳細の SWP | 3 | 3 | ○ |
| issue REF-06-T11 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-06-T12 最終 SWP | 4 | 4 | ○ |
| issue REF-06-T12 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-06-T12 評価 B の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-06-T12 詳細の SWP | 4 | 4 | ○ |
| issue REF-06-T12 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-06-T13 最終 SWP | 5 | 5 | ○ |
| issue REF-06-T13 詳細の SWP | 5 | 5 | ○ |
| issue REF-06-T13 評価 B の SWP（詳細） | 5 | 5 | ○ |
| 親ごとの件数 REF-07 | 15 | 15 | ○ |
| 親ごとの小計 REF-07 SWP | 54 | 54 | ○ |
| issue REF-07-T01 最終 SWP | 6 | 6 | ○ |
| issue REF-07-T01 詳細の SWP | 6 | 6 | ○ |
| issue REF-07-T01 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-07-T02 最終 SWP | 5 | 5 | ○ |
| issue REF-07-T02 詳細の SWP | 5 | 5 | ○ |
| issue REF-07-T02 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-07-T03 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T03 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T04 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T04 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T04 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T05 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T05 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T05 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T06 最終 SWP | 1 | 1 | ○ |
| issue REF-07-T06 詳細の SWP | 1 | 1 | ○ |
| issue REF-07-T06 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-07-T07 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T07 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T07 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T08 最終 SWP | 1 | 1 | ○ |
| issue REF-07-T08 詳細の SWP | 1 | 1 | ○ |
| issue REF-07-T08 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-07-T09 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T09 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T09 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T10 最終 SWP | 4 | 4 | ○ |
| issue REF-07-T10 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-07-T10 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-07-T10 詳細の SWP | 4 | 4 | ○ |
| issue REF-07-T10 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T11 最終 SWP | 5 | 5 | ○ |
| issue REF-07-T11 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-07-T11 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-07-T11 詳細の SWP | 5 | 5 | ○ |
| issue REF-07-T11 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T12 最終 SWP | 5 | 5 | ○ |
| issue REF-07-T12 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-07-T12 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-07-T12 詳細の SWP | 5 | 5 | ○ |
| issue REF-07-T12 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T13 最終 SWP | 3 | 3 | ○ |
| issue REF-07-T13 詳細の SWP | 3 | 3 | ○ |
| issue REF-07-T13 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-07-T14 最終 SWP | 4 | 4 | ○ |
| issue REF-07-T14 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-07-T14 評価 B の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-07-T14 詳細の SWP | 4 | 4 | ○ |
| issue REF-07-T14 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-07-T15 最終 SWP | 5 | 5 | ○ |
| issue REF-07-T15 詳細の SWP | 5 | 5 | ○ |
| issue REF-07-T15 評価 B の SWP（詳細） | 5 | 5 | ○ |
| 親ごとの件数 REF-08 | 14 | 14 | ○ |
| 親ごとの小計 REF-08 SWP | 44 | 44 | ○ |
| issue REF-08-T01 最終 SWP | 3 | 3 | ○ |
| issue REF-08-T01 詳細の SWP | 3 | 3 | ○ |
| issue REF-08-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-08-T02 最終 SWP | 5 | 5 | ○ |
| issue REF-08-T02 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-08-T02 評価 B の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-08-T02 詳細の SWP | 5 | 5 | ○ |
| issue REF-08-T02 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-08-T03 最終 SWP | 3 | 3 | ○ |
| issue REF-08-T03 詳細の SWP | 3 | 3 | ○ |
| issue REF-08-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-08-T04 最終 SWP | 6 | 6 | ○ |
| issue REF-08-T04 評価 A の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-08-T04 評価 B の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-08-T04 詳細の SWP | 6 | 6 | ○ |
| issue REF-08-T04 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-08-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-08-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-08-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-08-T06 最終 SWP | 1 | 1 | ○ |
| issue REF-08-T06 詳細の SWP | 1 | 1 | ○ |
| issue REF-08-T06 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-08-T07 最終 SWP | 2 | 2 | ○ |
| issue REF-08-T07 詳細の SWP | 2 | 2 | ○ |
| issue REF-08-T07 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-08-T08 最終 SWP | 1 | 1 | ○ |
| issue REF-08-T08 詳細の SWP | 1 | 1 | ○ |
| issue REF-08-T08 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-08-T09 最終 SWP | 3 | 3 | ○ |
| issue REF-08-T09 詳細の SWP | 3 | 3 | ○ |
| issue REF-08-T09 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-08-T10 最終 SWP | 3 | 3 | ○ |
| issue REF-08-T10 評価 A の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-08-T10 評価 B の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-08-T10 詳細の SWP | 3 | 3 | ○ |
| issue REF-08-T10 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-08-T11 最終 SWP | 1 | 1 | ○ |
| issue REF-08-T11 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-08-T11 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-08-T11 詳細の SWP | 1 | 1 | ○ |
| issue REF-08-T11 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-08-T12 最終 SWP | 5 | 5 | ○ |
| issue REF-08-T12 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-08-T12 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-08-T12 詳細の SWP | 5 | 5 | ○ |
| issue REF-08-T12 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-08-T13 最終 SWP | 5 | 5 | ○ |
| issue REF-08-T13 詳細の SWP | 5 | 5 | ○ |
| issue REF-08-T13 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-08-T14 最終 SWP | 5 | 5 | ○ |
| issue REF-08-T14 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-08-T14 評価 B の SWP（差の表示） | 8 | 8 | ○ |
| issue REF-08-T14 詳細の SWP | 5 | 5 | ○ |
| issue REF-08-T14 評価 B の SWP（詳細） | 8 | 8 | ○ |
| 親ごとの件数 REF-09 | 29 | 29 | ○ |
| 親ごとの小計 REF-09 SWP | 64 | 64 | ○ |
| issue REF-09-T01 最終 SWP | 2 | 2 | ○ |
| issue REF-09-T01 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-09-T01 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-09-T01 詳細の SWP | 2 | 2 | ○ |
| issue REF-09-T01 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T02 最終 SWP | 4 | 4 | ○ |
| issue REF-09-T02 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-09-T02 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-09-T02 詳細の SWP | 4 | 4 | ○ |
| issue REF-09-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T03 最終 SWP | 6 | 6 | ○ |
| issue REF-09-T03 詳細の SWP | 6 | 6 | ○ |
| issue REF-09-T03 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-09-T04 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T04 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T04 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T06 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T06 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-09-T06 評価 B の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-09-T06 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T06 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-09-T07 最終 SWP | 2 | 2 | ○ |
| issue REF-09-T07 詳細の SWP | 2 | 2 | ○ |
| issue REF-09-T07 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-09-T08 最終 SWP | 3 | 3 | ○ |
| issue REF-09-T08 詳細の SWP | 3 | 3 | ○ |
| issue REF-09-T08 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T09 最終 SWP | 4 | 4 | ○ |
| issue REF-09-T09 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-09-T09 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-09-T09 詳細の SWP | 4 | 4 | ○ |
| issue REF-09-T09 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T10 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T10 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T10 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T11 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T11 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T11 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T12 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T12 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T12 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T13 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T13 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T13 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T14 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T14 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T14 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T15 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T15 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T15 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T16 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T16 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T16 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T17 最終 SWP | 2 | 2 | ○ |
| issue REF-09-T17 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-09-T17 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-09-T17 詳細の SWP | 2 | 2 | ○ |
| issue REF-09-T17 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T18 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T18 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T18 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T19 最終 SWP | 3 | 3 | ○ |
| issue REF-09-T19 詳細の SWP | 3 | 3 | ○ |
| issue REF-09-T19 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T20 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T20 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T20 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T21 最終 SWP | 3 | 3 | ○ |
| issue REF-09-T21 詳細の SWP | 3 | 3 | ○ |
| issue REF-09-T21 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T22 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T22 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T22 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-09-T23 最終 SWP | 3 | 3 | ○ |
| issue REF-09-T23 詳細の SWP | 3 | 3 | ○ |
| issue REF-09-T23 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T24 最終 SWP | 3 | 3 | ○ |
| issue REF-09-T24 詳細の SWP | 3 | 3 | ○ |
| issue REF-09-T24 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-09-T25 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T25 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-09-T25 評価 B の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-09-T25 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T25 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-09-T26 最終 SWP | 1 | 1 | ○ |
| issue REF-09-T26 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-09-T26 評価 B の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-09-T26 詳細の SWP | 1 | 1 | ○ |
| issue REF-09-T26 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-09-T27 最終 SWP | 5 | 5 | ○ |
| issue REF-09-T27 詳細の SWP | 5 | 5 | ○ |
| issue REF-09-T27 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-09-T28 最終 SWP | 4 | 4 | ○ |
| issue REF-09-T28 詳細の SWP | 4 | 4 | ○ |
| issue REF-09-T28 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-09-T29 最終 SWP | 5 | 5 | ○ |
| issue REF-09-T29 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-09-T29 評価 B の SWP（差の表示） | 8 | 8 | ○ |
| issue REF-09-T29 詳細の SWP | 5 | 5 | ○ |
| issue REF-09-T29 評価 B の SWP（詳細） | 8 | 8 | ○ |
| 親ごとの件数 REF-10 | 25 | 25 | ○ |
| 親ごとの小計 REF-10 SWP | 70 | 70 | ○ |
| issue REF-10-T01 最終 SWP | 6 | 6 | ○ |
| issue REF-10-T01 評価 A の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-10-T01 評価 B の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-10-T01 詳細の SWP | 6 | 6 | ○ |
| issue REF-10-T01 評価 B の SWP（詳細） | 4 | 4 | ○ |
| issue REF-10-T02 最終 SWP | 2 | 2 | ○ |
| issue REF-10-T02 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-10-T02 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-10-T02 詳細の SWP | 2 | 2 | ○ |
| issue REF-10-T02 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T03 最終 SWP | 6 | 6 | ○ |
| issue REF-10-T03 詳細の SWP | 6 | 6 | ○ |
| issue REF-10-T03 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-10-T04 最終 SWP | 2 | 2 | ○ |
| issue REF-10-T04 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-10-T04 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-10-T04 詳細の SWP | 2 | 2 | ○ |
| issue REF-10-T04 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T05 最終 SWP | 2 | 2 | ○ |
| issue REF-10-T05 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-10-T05 評価 B の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-10-T05 詳細の SWP | 2 | 2 | ○ |
| issue REF-10-T05 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T06 最終 SWP | 2 | 2 | ○ |
| issue REF-10-T06 詳細の SWP | 2 | 2 | ○ |
| issue REF-10-T06 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-10-T07 最終 SWP | 2 | 2 | ○ |
| issue REF-10-T07 詳細の SWP | 2 | 2 | ○ |
| issue REF-10-T07 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-10-T08 最終 SWP | 4 | 4 | ○ |
| issue REF-10-T08 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-10-T08 評価 B の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-10-T08 詳細の SWP | 4 | 4 | ○ |
| issue REF-10-T08 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-10-T09 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T09 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T09 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T10 最終 SWP | 3 | 3 | ○ |
| issue REF-10-T10 詳細の SWP | 3 | 3 | ○ |
| issue REF-10-T10 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-10-T11 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T11 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T11 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T12 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T12 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T12 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T13 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T13 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T13 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T14 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T14 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T14 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T15 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T15 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T15 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T16 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T16 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T16 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T17 最終 SWP | 3 | 3 | ○ |
| issue REF-10-T17 詳細の SWP | 3 | 3 | ○ |
| issue REF-10-T17 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-10-T18 最終 SWP | 3 | 3 | ○ |
| issue REF-10-T18 詳細の SWP | 3 | 3 | ○ |
| issue REF-10-T18 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-10-T19 最終 SWP | 5 | 5 | ○ |
| issue REF-10-T19 詳細の SWP | 5 | 5 | ○ |
| issue REF-10-T19 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-10-T20 最終 SWP | 3 | 3 | ○ |
| issue REF-10-T20 詳細の SWP | 3 | 3 | ○ |
| issue REF-10-T20 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-10-T21 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T21 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-10-T21 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-10-T21 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T21 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-10-T22 最終 SWP | 1 | 1 | ○ |
| issue REF-10-T22 詳細の SWP | 1 | 1 | ○ |
| issue REF-10-T22 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-10-T23 最終 SWP | 5 | 5 | ○ |
| issue REF-10-T23 詳細の SWP | 5 | 5 | ○ |
| issue REF-10-T23 評価 B の SWP（詳細） | 5 | 5 | ○ |
| issue REF-10-T24 最終 SWP | 8 | 8 | ○ |
| issue REF-10-T24 詳細の SWP | 8 | 8 | ○ |
| issue REF-10-T24 評価 B の SWP（詳細） | 8 | 8 | ○ |
| issue REF-10-T25 最終 SWP | 5 | 5 | ○ |
| issue REF-10-T25 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-10-T25 評価 B の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-10-T25 詳細の SWP | 5 | 5 | ○ |
| issue REF-10-T25 評価 B の SWP（詳細） | 4 | 4 | ○ |
| 親ごとの件数 REF-11 | 7 | 7 | ○ |
| 親ごとの小計 REF-11 SWP | 31 | 31 | ○ |
| issue REF-11-T01 最終 SWP | 6 | 6 | ○ |
| issue REF-11-T01 詳細の SWP | 6 | 6 | ○ |
| issue REF-11-T01 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-11-T02 最終 SWP | 3 | 3 | ○ |
| issue REF-11-T02 詳細の SWP | 3 | 3 | ○ |
| issue REF-11-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-11-T03 最終 SWP | 6 | 6 | ○ |
| issue REF-11-T03 評価 A の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-11-T03 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-11-T03 詳細の SWP | 6 | 6 | ○ |
| issue REF-11-T03 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-11-T04 最終 SWP | 4 | 4 | ○ |
| issue REF-11-T04 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-11-T04 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-11-T04 詳細の SWP | 4 | 4 | ○ |
| issue REF-11-T04 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-11-T05 最終 SWP | 5 | 5 | ○ |
| issue REF-11-T05 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-11-T05 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-11-T05 詳細の SWP | 5 | 5 | ○ |
| issue REF-11-T05 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-11-T06 最終 SWP | 3 | 3 | ○ |
| issue REF-11-T06 詳細の SWP | 3 | 3 | ○ |
| issue REF-11-T06 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-11-T07 最終 SWP | 4 | 4 | ○ |
| issue REF-11-T07 評価 A の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-11-T07 評価 B の SWP（差の表示） | 6 | 6 | ○ |
| issue REF-11-T07 詳細の SWP | 4 | 4 | ○ |
| issue REF-11-T07 評価 B の SWP（詳細） | 6 | 6 | ○ |
| 親ごとの件数 REF-12 | 7 | 7 | ○ |
| 親ごとの小計 REF-12 SWP | 20 | 20 | ○ |
| issue REF-12-T01 最終 SWP | 2 | 2 | ○ |
| issue REF-12-T01 詳細の SWP | 2 | 2 | ○ |
| issue REF-12-T01 評価 B の SWP（詳細） | 2 | 2 | ○ |
| issue REF-12-T02 最終 SWP | 3 | 3 | ○ |
| issue REF-12-T02 詳細の SWP | 3 | 3 | ○ |
| issue REF-12-T02 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-12-T03 最終 SWP | 1 | 1 | ○ |
| issue REF-12-T03 詳細の SWP | 1 | 1 | ○ |
| issue REF-12-T03 評価 B の SWP（詳細） | 1 | 1 | ○ |
| issue REF-12-T04 最終 SWP | 6 | 6 | ○ |
| issue REF-12-T04 詳細の SWP | 6 | 6 | ○ |
| issue REF-12-T04 評価 B の SWP（詳細） | 6 | 6 | ○ |
| issue REF-12-T05 最終 SWP | 1 | 1 | ○ |
| issue REF-12-T05 評価 A の SWP（差の表示） | 1 | 1 | ○ |
| issue REF-12-T05 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-12-T05 詳細の SWP | 1 | 1 | ○ |
| issue REF-12-T05 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-12-T06 最終 SWP | 2 | 2 | ○ |
| issue REF-12-T06 評価 A の SWP（差の表示） | 2 | 2 | ○ |
| issue REF-12-T06 評価 B の SWP（差の表示） | 3 | 3 | ○ |
| issue REF-12-T06 詳細の SWP | 2 | 2 | ○ |
| issue REF-12-T06 評価 B の SWP（詳細） | 3 | 3 | ○ |
| issue REF-12-T07 最終 SWP | 5 | 5 | ○ |
| issue REF-12-T07 評価 A の SWP（差の表示） | 5 | 5 | ○ |
| issue REF-12-T07 評価 B の SWP（差の表示） | 4 | 4 | ○ |
| issue REF-12-T07 詳細の SWP | 5 | 5 | ○ |
| issue REF-12-T07 評価 B の SWP（詳細） | 4 | 4 | ○ |
| 親 REF-01 子の数 | 6 | 6 | ○ |
| 親 REF-01 初期 SWP | 13 | 13 | ○ |
| 親 REF-01 最終 SWP | 17 | 17 | ○ |
| 親 REF-02 子の数 | 9 | 9 | ○ |
| 親 REF-02 初期 SWP | 35 | 35 | ○ |
| 親 REF-02 最終 SWP | 35 | 35 | ○ |
| 親 REF-03 子の数 | 9 | 9 | ○ |
| 親 REF-03 初期 SWP | 33 | 33 | ○ |
| 親 REF-03 最終 SWP | 33 | 33 | ○ |
| 親 REF-04 子の数 | 22 | 22 | ○ |
| 親 REF-04 初期 SWP | 62 | 62 | ○ |
| 親 REF-04 最終 SWP | 62 | 62 | ○ |
| 親 REF-05 子の数 | 18 | 18 | ○ |
| 親 REF-05 初期 SWP | 43 | 43 | ○ |
| 親 REF-05 最終 SWP | 43 | 43 | ○ |
| 親 REF-06 子の数 | 13 | 13 | ○ |
| 親 REF-06 初期 SWP | 42 | 42 | ○ |
| 親 REF-06 最終 SWP | 42 | 42 | ○ |
| 親 REF-07 子の数 | 15 | 15 | ○ |
| 親 REF-07 初期 SWP | 54 | 54 | ○ |
| 親 REF-07 最終 SWP | 54 | 54 | ○ |
| 親 REF-08 子の数 | 14 | 14 | ○ |
| 親 REF-08 初期 SWP | 44 | 44 | ○ |
| 親 REF-08 最終 SWP | 44 | 44 | ○ |
| 親 REF-09 子の数 | 29 | 29 | ○ |
| 親 REF-09 初期 SWP | 64 | 64 | ○ |
| 親 REF-09 最終 SWP | 64 | 64 | ○ |
| 親 REF-10 子の数 | 25 | 25 | ○ |
| 親 REF-10 初期 SWP | 70 | 70 | ○ |
| 親 REF-10 最終 SWP | 70 | 70 | ○ |
| 親 REF-11 子の数 | 7 | 7 | ○ |
| 親 REF-11 初期 SWP | 31 | 31 | ○ |
| 親 REF-11 最終 SWP | 31 | 31 | ○ |
| 親 REF-12 子の数 | 7 | 7 | ○ |
| 親 REF-12 初期 SWP | 20 | 20 | ○ |
| 親 REF-12 最終 SWP | 20 | 20 | ○ |
| 要約 点数が変わった issue 数 | 2 | 2 | ○ |
| 要約 代表 issue 数 | 5 | 5 | ○ |
| 代表 REF-01-T02 SWP | 3 | 3 | ○ |
| 代表 REF-01-T02 初期 SWP | 1 | 1 | ○ |
| 代表 REF-01-T02 最終 SWP | 3 | 3 | ○ |
| 代表 REF-04-T19 SWP | 3 | 3 | ○ |
| 代表 REF-04-T19 初期 SWP | 3 | 3 | ○ |
| 代表 REF-04-T19 最終 SWP | 3 | 3 | ○ |
| 代表 REF-10-T24 SWP | 8 | 8 | ○ |
| 代表 REF-10-T24 初期 SWP | 8 | 8 | ○ |
| 代表 REF-10-T24 最終 SWP | 8 | 8 | ○ |
| 代表 REF-04-T22 SWP | 8 | 8 | ○ |
| 代表 REF-04-T22 初期 SWP | 8 | 8 | ○ |
| 代表 REF-04-T22 最終 SWP | 8 | 8 | ○ |
| 代表 REF-01-T04 SWP | 3 | 3 | ○ |
| 代表 REF-01-T04 初期 SWP | 1 | 1 | ○ |
| 代表 REF-01-T04 最終 SWP | 3 | 3 | ○ |
| 校正の修正 1 件目 初期 SWP | 1 | 1 | ○ |
| 校正の修正 1 件目 確定 SWP | 3 | 3 | ○ |
| 校正の修正 2 件目 初期 SWP | 1 | 1 | ○ |
| 校正の修正 2 件目 確定 SWP | 3 | 3 | ○ |
| 校正の修正 3 件目 初期 SWP | 3 | 3 | ○ |
| 校正の修正 3 件目 確定 SWP | 3 | 3 | ○ |
| 校正の修正 4 件目 初期 SWP | 8 | 8 | ○ |
| 校正の修正 4 件目 確定 SWP | 8 | 8 | ○ |
| 校正の修正 5 件目 初期 SWP | 8 | 8 | ○ |
| 校正の修正 5 件目 確定 SWP | 8 | 8 | ○ |
| 要約 修正数 | 5 | 5 | ○ |
| 要約 ルール数 | 0 | 0 | ○ |
| 評価 A・B 人が見ていない分かれた issue 件数 | 116 | 116 | ○ |
| 注意事項 省略した記述 件数 | 0 | 0 | ○ |
| 注意事項 訳文に置換した記述 件数 | 475 | 475 | ○ |
