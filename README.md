# Yuki Cold Logistics 開発バックログ

- 学生情報: 受講者番号 B120675
- 対象: Product B（Yuki Cold Logistics、冷蔵・冷凍食品物流）
- 内容: 設計書（詳細設計）をもとに、GitHub Project 上へ epic / story / task（sub-issue）の形で開発のバックログを展開した提出用リポジトリです。

## 1. 概要

- 元にした設計書: 2026-10-12 に提出した詳細設計の版（以下「設計書」）から、バックログを分割した。
- PREMISE（前提）: 設計書からの変更あり。仕様の追加・削除・修正 31 行（P-S）、追加した仮定 31 行（P-A）、確定した方針 6 行（P-D）。詳細は [PREMISE.md](PREMISE.md) を参照。
- エピック数: 15 本（[#1](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/1) E09 と、[#16](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/16)〜[#29](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/29) の [#16](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/16) E01〜[#23](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/23) E08・[#24](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/24) E10〜[#29](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/29) E15）。配下は story 86 本、task（sub-issue）406 本、合計 507 件の issue。
- 規模: SWP 評価の合計は 1,645 SWP（task 406 件の合計。story・epic は配下の合計）。工数への換算は [estimate.md](estimate.md) に書いた（合計 6,222 時間 = 777.8 人日）。換算後に 16 時間を超える task 160 件は、スプリントに入れる前のリファインメントで、分けることを優先して見直す。
- 模擬スプリント: GitHub Project のイテレーション「スプリント 1」（2026-11-02〜2026-11-15、2 週間）を模擬実行し、結果を Project の Status・イテレーション・クローズ状態に反映した。対象 31 件・計画 63 SWP のうち、完了 24 件・42 SWP、スプリント 2 への持ち越し 7 件。結果は [progress-report.md](progress-report.md) に書いた。

## 2. リンク

- リポジトリ: https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog
- GitHub Project: https://github.com/users/binhnht-0675/projects/1
- SWP 評価の HTML レポート（日本語）: [reports/estimate-swp-yuki-cold-logistics-261023-1158-ja.html](reports/estimate-swp-yuki-cold-logistics-261023-1158-ja.html)
- HTML レポートの照合表（数値が元データと一致することの確認）: [reports/estimate-swp-verification-ja-261023.md](reports/estimate-swp-verification-ja-261023.md)
- 追加評価（2026-10-24、最終レビューを受けた 17 件）の HTML レポート（日本語）: [reports/estimate-swp-yuki-cold-logistics-261024-lot17-ja.html](reports/estimate-swp-yuki-cold-logistics-261024-lot17-ja.html)、照合表 [reports/estimate-swp-verification-ja-261024-lot17.md](reports/estimate-swp-verification-ja-261024-lot17.md)
- 時間の換算の参考に使った試作版の SWP 評価（日本語）: [reports/estimate-swp-prototype-reference-261023-1931-ja.html](reports/estimate-swp-prototype-reference-261023-1931-ja.html)、照合表 [reports/estimate-swp-prototype-reference-verification-ja-261023.md](reports/estimate-swp-prototype-reference-verification-ja-261023.md)
- 公開の確認: リポジトリと Project は、ログインしていないシークレット（プライベート）ウィンドウで開き、誰でも閲覧できることを 2026-10-24 に確認した。

## 3. リポジトリの構成

| ファイル・ディレクトリ | 内容 |
|---|---|
| `README.md` | 本ファイル。概要・リンク・構成・設計書とエピックの対応 |
| `PREMISE.md` | 設計書からの変更点と、追加した仮定・確定した方針 |
| `task-breakdown.md` | 分割の原則、設計書から issue への対応、2024 年運転時間規制の別立て、仕様の抜け・矛盾と扱い |
| `estimate.md` | SWP による規模評価、サンプル issue の確認、工数への換算、エピック別合計、提案時の見積との比較 |
| `progress-report.md` | 模擬スプリントの進捗（状態別の件数・バーンダウン・遅れのリスク） |
| `AI-report.md` | 使った AI・スキル・プロンプト、人によるレビュー、効果と改善点、作業時間 |
| `reports/` | SWP 評価の HTML レポート（日本語、本体・追加評価（17 件）・試作版の参考）、照合表、16 時間を超える task の一覧、バーンダウンの画像（模擬） |
| `skills/` | 作業に使った自作スキル 4 本（バックログ登録、フィールド書き込み、進捗の集計、レポートの日本語化）と共通部品。スキル 1・3 は使う前に人が確認し承認した（2026-10-20）。スキル 2・4 は同日に条件付きで承認し、実データで動かしたときに条件を確かめてから使った（スキル 4: 10-21〜23、スキル 2: 10-23） |
| `design-updates/` | 設計の更新。ワイヤーフレーム 8 画面の作り直し、HACCP の義務の水準の補足、パージ削除の関門のトリガー一覧 |
| `.gitignore` | リポジトリに含めないファイルの指定 |

## 4. 設計書とエピックの対応

| Spec（設計書の分冊・対象 FT） | Epic（#番号 — 名前） | 備考 |
|---|---|---|
| authentication/ 分冊、_common/adr/ADR-003 ／ FT-103・FT-112〜FT-114（4 件） | [#16](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/16) E01 — 認証・権限 | 試作版のメール・パスワード認証（模擬）を企業 SSO へ置き換えるのが中心。 |
| inbound-inventory/ 分冊、_common/architecture-overview.md ／ FT-001〜FT-024・FT-124・FT-125（26 件） | [#17](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/17) E02 — 入荷・在庫 | P-S01 により、検品から自動で作る逸脱ケースの記録項目を本番化の対象に数える。 |
| order-allocation/ 分冊 ／ FT-025〜FT-035・FT-122（12 件） | [#18](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/18) E03 — 受注・引当 | 引当ロジックの設計（ALLOCATE_LOTS）を含む。 |
| outbound-picking/ 分冊 ／ FT-036〜FT-041（6 件） | [#19](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/19) E04 — 出荷（ピッキング・積込） | ピッキングと積込の状態遷移を含む。 |
| route-delivery/ 分冊（運転時間の部分を除く） ／ FT-042〜FT-048・FT-053・FT-054・FT-057・FT-058・FT-060・FT-101（13 件） | [#20](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/20) E05 — 配送（ルート・運行・POD） | 運転時間の規制に関わる FT は [#25](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/25)（E11） に分けた。 |
| temperature-haccp/ 分冊、_common/adr/ADR-005 ／ FT-061〜FT-079・FT-123（20 件） | [#21](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/21) E06 — 温度管理・HACCP | HACCP の義務の水準は PREMISE P-S22、SCR-25 の既定のタブは P-A30。設計の更新は design-updates/ を参照。 |
| traceability-recall/ 分冊、_common/adr/ADR-005 ／ FT-080〜FT-086・FT-118（8 件） | [#22](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/22) E07 — トレーサビリティ・リコール | 回収の処理はロック順を ADR-005 に合わせる。 |
| master-data/ 分冊、system-design/database-design/master-data ／ FT-094〜FT-097・FT-119〜FT-121（7 件） | [#23](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/23) E08 — マスターデータ・納品期限契約 | 納品期限契約の版管理を含む。 |
| claims-returns/ 分冊 ／ FT-049〜FT-052（4 件） | [#1](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/1) E09 — クレーム・返品 | 最初に試験的に登録したエピックのため、番号が #1 になっている。 |
| reporting-audit/ 分冊、system-design/database-design/reporting-audit ／ FT-087〜FT-093・FT-115〜FT-117（10 件） | [#24](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/24) E10 — レポート・監査・保持 | 保持・法的保留・パージの削除の関門（42 表）を含む。 |
| _common/adr/ADR-002、route-delivery/ 分冊（SCR-19・SCR-16 の運転時間の部分） ／ FT-055・FT-056・FT-059・FT-102（4 件） | [#25](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/25) E11 — 2024年運転時間規制（専用） | 2024 年からの運転時間の上限は専用エピックに分け、他の配送の issue と混ぜない（理由は task-breakdown §3）。 |
| _common/architecture-overview.md、change-requests/ 変更要求（技術スタック） ／ FT なし（本番の基盤） | [#26](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/26) E12 — 基盤・環境・リリース | 環境・リリース・CI など、特定の機能に属さない基盤の作業。 |
| _common/external-integration-design.md、_common/adr/ADR-007 ／ FT-098〜FT-100・FT-104（4 件） | [#27](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/27) E13 — 外部連携 | 外部連携は非同期方式で統一する。 |
| _common/data-migration-design.md、change-requests/ 変更要求 ／ FT-105〜FT-111（7 件） | [#28](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/28) E14 — データ移行・切替 | 移行と切替。 |
| change-requests/ 変更要求（NFR の対応表）、_common/common-spec.md ／ FT なし（非機能・横断） | [#29](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/29) E15 — 非機能・横断 UI | 日時と温度の JST 表示など、画面をまたぐ共通事項。 |

FT（機能）は合計 125 件で、[#26](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/26)（E12） と [#29](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/29)（E15） を除く 13 本のエピックに分けた。[#26](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/26)（E12） と [#29](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/29)（E15） は特定の機能に属さない基盤・非機能の作業である。

## 5. 設計の更新

設計書から変えた設計は、リポジトリ内の `design-updates/` に置いた。PREMISE.md の該当行（P-S21 / P-S22 ほか）から参照している。

- [design-updates/wireframe-changes.ja.md](design-updates/wireframe-changes.ja.md): ワイヤーフレーム 8 画面の作り直しと、画面仕様との食い違い
- [design-updates/haccp-obligation-level-addendum.ja.md](design-updates/haccp-obligation-level-addendum.ja.md): HACCP の義務の水準の補足（PREMISE P-S22）
- [design-updates/purge-delete-gate-trigger-inventory.ja.md](design-updates/purge-delete-gate-trigger-inventory.ja.md): パージ削除の関門に関わるトリガーの一覧
