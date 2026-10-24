# 換算後に 16 時間を超える task（160 件）

時間 = SWP × 3.80（1 SWP あたりの時間。直接見積もった 10 件の task から較正した値。estimate.md 第 3 節）。上限の判定は丸める前の時間で行う。Project には 0.5 時間刻みに丸めた値を記録する。この換算では 5 SWP 以上の task がすべて対象になる。
- 6 SWP 以上の 75 件は、感度のどの置き方（estimate.md 第 3 節）でも 16 時間を超える。
- 5 SWP の 85 件は境目にある。1 SWP あたりの時間を、6 件を別のレビュー担当（AI のセッション）が独立に見積もった値（3.10 時間）にすると、16 時間以下になる。
- 時間の見積は AI 利用の前提を置いていない。提案時と同じ AI の効果（×0.8）を掛けると 1 SWP あたり 3.04 時間で、上限を超えるのは 6 SWP 以上の 75 件になる。Project に記録する時間と、この一覧の判定には ×0.8 を掛けない。
- 直接の見積もりが規則から大きく離れる、または 16 時間を超える task は、リファインメントで見積もり直す: [#148](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/148)、[#472](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/472)、[#6](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/6)。#6 と #472 は直接の見積もりが 24 時間で、規則では 16 時間以下でも上限を超える。

どの task もまだ分割していない。スプリントに入れる前のリファインメントで、分けることを優先して見直す。分けない task は、見直したうえで task ごとに理由を書く（この表にはまだ理由を書かない）。

| issue | キー | 層 | SWP | 換算（丸め前、時間） | Project の記録（時間） | タイトル |
|---|---|---|---|---|---|---|
| [#500](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/500) | E10-I04-S10 | DB | 16 | 60.80 | 61 | パージの削除の関門（D-RA-1: 対象 42 表の削除を承認済みのパージに限る） |
| [#239](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/239) | E05-I01-S03 | API | 10 | 38.00 | 38 | 出発確定 API の本番化（POST …/dispatch） |
| [#367](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/367) | E08-I02-S01 | DB | 10 | 38.00 | 38 | 版管理の DB（仕入先・ロケーション・機器の版表・既存の版表の maker-checker・温度ポリシーの適用範囲） |
| [#394](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/394) | E10-I02-S01 | DB | 10 | 38.00 | 38 | 監査エクスポートの DB（audit_export・作成関数・マニフェストの固定・検証関数・ワーカーの起動） |
| [#485](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/485) | E15-I03-S03 | テスト | 10 | 38.00 | 38 | 80同時ユーザーの負荷試験の実施と結果報告 |
| [#497](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/497) | E15-I08-S03 | ドキュメント | 10 | 38.00 | 38 | API 契約の一元化（API 設計書を正とし、画面補遺と API 一覧（設計）は番号とリンクだけにする） |
| [#507](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/507) | E13-I05-S06 | API | 10 | 38.00 | 38 | 取込ワーカーの Route Handler（`POST /api/internal/worker/ingest`）（.sha256 と見出しの検査・塊ごとの RPC の呼出し・再試行と dead） |
| [#330](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/330) | E06-I09-S01 | DB | 9 | 34.20 | 34 | リーディング評価・アラーム生成・影響ロットの隔離の本番化（有効な版の選択・グループ化・重大度・確認期限） |
| [#349](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/349) | E07-I04-S04 | API | 9 | 34.20 | 34 | API-057 POST 範囲の確定（3 つの脚の写し・自動隔離・安全網） |
| [#409](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/409) | E10-I04-S09 | API | 9 | 34.20 | 34 | API-D-103 POST パージの承認と実行（保留の再確認・1,000 行ずつの削除） |
| [#14](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/14) | E09-I02-S05 | テスト | 8 | 30.40 | 30.5 | SCR-18 のテスト（状況の遷移・証拠の版・返品と処分の独立・回収との二重計上・E2E） |
| [#443](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/443) | E12-I01-S01 | インフラ | 8 | 30.40 | 30.5 | Supabase プロジェクトの作成（stg / UAT / prod）とシークレットの配置規約 |
| [#489](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/489) | E15-I05-S03 | テスト | 8 | 30.40 | 30.5 | WCAG 2.2 AA の検証（主要画面・自動検査と手動） |
| [#10](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/10) | E09-I02-S07 | API | 6 | 22.80 | 23 | API-D-048 POST 返品の受領と検品（隔離ロットの作成） |
| [#116](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/116) | E01-I01-S04 | API | 6 | 22.80 | 23 | SSO の開始 API とコールバック API（GET /api/auth/sso/start・callback） |
| [#123](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/123) | E01-I02-S05 | API | 6 | 22.80 | 23 | API-D-072 POST アカウントのロック・ロック解除 |
| [#150](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/150) | E02-I11-S02 | API | 6 | 22.80 | 23 | 検品確定 API の本番化（数量・理由・状態） |
| [#154](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/154) | E02-I11-S06 | テスト | 6 | 22.80 | 23 | SCR-02 数量・ロット作成の結合・E2E テスト |
| [#156](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/156) | E02-I12-S02 | API | 6 | 22.80 | 23 | 差異承認待ち一覧と承認・差戻し API（GET variance-pending・POST variance-decision） |
| [#161](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/161) | E02-I03-S04 | DB | 6 | 22.80 | 23 | 在庫移動のブロック RPC（負の在庫・温度帯逸脱）と inventory_movement の列追加 |
| [#170](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/170) | E02-I05-S04 | API | 6 | 22.80 | 23 | 棚入れ確定 API の本番化と提案外選択の契約変更（POST /api/putaway・putaway_confirm の引数追加） |
| [#195](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/195) | E02-I10-S03 | API | 6 | 22.80 | 23 | ロット状態判定 API の本番化（POST …/status） |
| [#207](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/207) | E03-I03-S01 | DB | 6 | 22.80 | 23 | 引当 RPC の判定と割当の本番化（納品期限規則・日付逆転・FEFO） |
| [#211](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/211) | E03-I04-S01 | API | 6 | 22.80 | 23 | 引当実行 API の本番化（POST …/allocate） |
| [#212](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/212) | E03-I04-S02 | DB | 6 | 22.80 | 23 | 引当の原子性とロック順（SKU → 受注 → 顧客×SKU → ロット） |
| [#222](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/222) | E04-I01-S03 | API | 6 | 22.80 | 23 | ピッキング・積込の作業一覧 API とピック API の本番化 |
| [#231](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/231) | E04-I02-S04 | DB | 6 | 22.80 | 23 | 出荷前確認の判定 RPC（温度・封印・逸脱・全隔離）の本番化 |
| [#234](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/234) | E04-I03-S02 | API | 6 | 22.80 | 23 | ピッキングのグループ一覧 API と並び保存 API（GET pick-groups・PUT pick-order） |
| [#243](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/243) | E05-I02-S03 | API | 6 | 22.80 | 23 | 配送詳細・受領記録 API の本番化（GET と POST pod） |
| [#247](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/247) | E05-I05-S01 | UI | 6 | 22.80 | 23 | 端末内の暗号化キュー（PWA）の実装 |
| [#267](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/267) | E05-I03-S06 | DB | 6 | 22.80 | 23 | ルート作成 RPC の受注の絞り込み（引当・納品日・温度帯・地図の地点）の本番化と地図の表の列追加 |
| [#271](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/271) | E05-I07-S01 | DB | 6 | 22.80 | 23 | 公開した版の凍結と、版・配送・未割当理由のマイグレーション（route_version・delivery・route_unassigned） |
| [#273](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/273) | E05-I07-S03 | API | 6 | 22.80 | 23 | ルート取消 API（POST …/cancel） |
| [#283](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/283) | E06-I01-S02 | API | 6 | 22.80 | 23 | API-042 POST /api/temperature/imports の本番化（解析・RPC 引数・サービスロール呼び出し） |
| [#285](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/285) | E06-I01-S04 | DB | 6 | 22.80 | 23 | 取込 RPC・アラーム生成クエリの本番相当データ量での計画確認とインデックス |
| [#287](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/287) | E06-I01-S08 | テスト | 6 | 22.80 | 23 | 温度取込まわりの同時実行テスト（取込 × 引当・同一ファイル・取込 × 予定枠の同期・同期 × クローズ） |
| [#298](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/298) | E06-I03-S05 | API | 6 | 22.80 | 23 | API-049 POST ロットの判定（解除・廃棄） |
| [#305](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/305) | E06-I04-S03 | DB | 6 | 22.80 | 23 | ロガー予定枠の同期の本番化（15 分の格子・待ち 30 時間・同期済みの印） |
| [#313](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/313) | E06-I06-S05 | DB | 6 | 22.80 | 23 | 5 分ごとの判定期限ジョブと通知の依頼（出箱への書き込み） |
| [#322](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/322) | E06-I07-S04 | テスト | 6 | 22.80 | 23 | リズム拡張のテスト（リズム別の枠・期限・不足に戻す・ロガー枠の回帰） |
| [#323](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/323) | E06-I07-S08 | ドキュメント | 6 | 22.80 | 23 | HACCP 義務の水準（法令上の義務と Yuki の方針の区別、小規模事業者等向けの衛生管理の適用条件）を設計補遺に反映する |
| [#334](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/334) | E07-I01-S03 | DB | 6 | 22.80 | 23 | トレース検索 RPC（3 レーン・家系の根・終点・切り詰め）の本番化と最大規模の性能確認 |
| [#341](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/341) | E07-I03-S05 | DB | 6 | 22.80 | 23 | 社内管理レーンのトレース検索と範囲確定の RPC 変更 |
| [#355](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/355) | E07-I04-S11 | テスト | 6 | 22.80 | 23 | 回収の同時実行テスト（2 セッション・4 つの組み合わせ・ロック順） |
| [#356](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/356) | E07-I04-S12 | テスト | 6 | 22.80 | 23 | 回収の E2E テスト（起票からクローズまで・クローズを止める 4 項目・確認の対話・PC と 390px・本番は読み取りだけ） |
| [#362](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/362) | E07-I05-S06 | API | 6 | 22.80 | 23 | API-D-147 POST 通知の送付（宛先ごとの出箱・ケースを通知済みに） |
| [#371](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/371) | E08-I02-S04 | API | 6 | 22.80 | 23 | API-D-149 POST マスターの新規提案 |
| [#374](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/374) | E08-I02-S12 | API | 6 | 22.80 | 23 | API-D-152 POST 承認・差戻し（旧い版の終了日・現在の表への反映） |
| [#383](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/383) | E08-I03-S07 | API | 6 | 22.80 | 23 | API-D-067 POST 契約の版の承認・差戻し |
| [#388](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/388) | E10-I01-S01 | DB | 6 | 22.80 | 23 | レポートの付与表・カタログ・部門の範囲の関数とレポート 1〜6（在庫・期限・隔離・HACCP・逸脱・アラーム SLA） |
| [#392](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/392) | E10-I01-S05 | テスト | 6 | 22.80 | 23 | SCR-28 のテスト（12 種類の部門範囲・付与・CSV の一致・期間の半開区間・E2E） |
| [#395](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/395) | E10-I02-S02 | API | 6 | 22.80 | 23 | API-D-084 POST 証拠パッケージの作成とワーカー |
| [#401](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/401) | E10-I02-S05 | テスト | 6 | 22.80 | 23 | SCR-29 のテスト（マニフェストの安定・再作成の一致・不一致の拒否・ロック・E2E） |
| [#402](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/402) | E10-I03-S01 | API | 6 | 22.80 | 23 | API-D-093 / 094 GET 監査イベントの一覧と詳細（追記専用の確認・索引） |
| [#404](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/404) | E10-I04-S01 | DB | 6 | 22.80 | 23 | 保持・法的保留・パージの DB（retention_action・保持スケジュール 10 種別・日次の件数） |
| [#411](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/411) | E10-I04-S05 | テスト | 6 | 22.80 | 23 | SCR-36 のテスト（保留中の削除ブロック・承認者の分離・パージの冪等・E2E） |
| [#417](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/417) | E11-I01-S07 | API | 6 | 22.80 | 23 | 運転時間チェック API（API-033）と結果記録 RPC の本番化 |
| [#422](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/422) | E11-I02-S03 | API | 6 | 22.80 | 23 | publish_route の照合条件を本番 DB で実装・確認 |
| [#446](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/446) | E12-I02-S02 | インフラ | 6 | 22.80 | 23 | stg 適用 → 承認 → 本番適用のリリースワークフロー（PITR 時点の記録） |
| [#458](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/458) | E13-I01-S02 | API | 6 | 22.80 | 23 | 毎日 02:30 JST の取得ジョブ（pull モード）と着地 |
| [#459](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/459) | E13-I01-S03 | API | 6 | 22.80 | 23 | orders CSV の列検査と受注の適用（API-015 の規則を再利用） |
| [#460](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/460) | E13-I01-S05 | API | 6 | 22.80 | 23 | inventory-result の出力 CSV と SFTP への配置 |
| [#463](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/463) | E13-I03-S02 | DB | 6 | 22.80 | 23 | 取込 RPC の取込元の種別への対応（source・uploaded_by）と、元ファイル・SHA-256 の3年保持 |
| [#465](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/465) | E13-I04-S02 | API | 6 | 22.80 | 23 | 出箱の取り出しと SMTP 送信ワーカー（587・STARTTLS・認証） |
| [#466](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/466) | E13-I05-S01 | DB | 6 | 22.80 | 23 | integration_file・integration_staging_row の作成と lease による起動の取得・取り直し |
| [#467](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/467) | E13-I05-S04 | DB | 6 | 22.80 | 23 | 適用・確定の RPC（SKU ロックの昇順・塊の切り方） |
| [#483](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/483) | E14-I08-S02 | 移行 | 6 | 22.80 | 23 | 最終ロードの実行と照合 |
| [#484](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/484) | E14-I08-S03 | テスト | 6 | 22.80 | 23 | スモークテスト（6人のオーナーによる E2E の流れの確認） |
| [#490](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/490) | E15-I05-S01 | テスト | 6 | 22.80 | 23 | 権限と暗号化の点検（全 RPC・全表） |
| [#491](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/491) | E15-I06-S01 | UI | 6 | 22.80 | 23 | 日付表示の共通関数への統一と直接整形の禁止（YYYY/MM/DD） |
| [#492](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/492) | E15-I06-S02 | UI | 6 | 22.80 | 23 | 必須マークの共通部品と適用（受入検査・受注登録ほか） |
| [#496](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/496) | E15-I08-S02 | ドキュメント | 6 | 22.80 | 23 | 残り 27 画面のワイヤーフレームを照合の結果に合わせて直す |
| [#498](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/498) | E15-I08-S04 | ドキュメント | 6 | 22.80 | 23 | 作り直した 8 画面のワイヤーフレームを UI 担当がレビューし、各 UI タスクの参照を差し替える |
| [#503](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/503) | E08-I02-S15 | API | 6 | 22.80 | 23 | 端末マスターの失効の API と RPC（status を revoked に・続いているセッションを閉じる） |
| [#506](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/506) | E13-I05-S05 | DB | 6 | 22.80 | 23 | 読込の RPC（staging への塊ごとの投入・同じ行番号は入れ直さない・ファイル内の冪等キーの重複で拒否） |
| [#4](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/4) | E09-I01-S01 | DB | 5 | 19.00 | 19 | クレームの表と制約（claim・クレームの行・状況のイベント） |
| [#5](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/5) | E09-I02-S01 | DB | 5 | 19.00 | 19 | 証拠の版・保管イベント・処分の表と、ロット状態イベントの発生元の拡張 |
| [#12](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/12) | E09-I01-S06 | UI | 5 | 19.00 | 19 | SCR-18 一覧・受付・詳細・状況の進行・判定（A〜C 区画） |
| [#13](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/13) | E09-I02-S04 | UI | 5 | 19.00 | 19 | SCR-18 証拠の版・返品と保管・在庫処分（D〜F 区画） |
| [#115](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/115) | E01-I01-S02 | API | 5 | 19.00 | 19 | セッション情報 API と認証イベント記録 API の本番化（GET /api/me・POST /api/auth/events） |
| [#117](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/117) | E01-I01-S06 | テスト | 5 | 19.00 | 19 | SCR-33 結合・E2E テスト（SSO） |
| [#122](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/122) | E01-I02-S04 | API | 5 | 19.00 | 19 | アカウント作成 API（POST /api/admin/users） |
| [#124](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/124) | E01-I02-S08 | API | 5 | 19.00 | 19 | API-D-073 POST ロールの付与・取消 |
| [#134](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/134) | E01-I04-S02 | API | 5 | 19.00 | 19 | 第1層の MFA 検査（Route Handler 共通ガード） |
| [#135](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/135) | E01-I04-S03 | DB | 5 | 19.00 | 19 | 第2層の MFA 検査（assert_privileged_mfa と設定値） |
| [#147](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/147) | E02-I02-S03 | API | 5 | 19.00 | 19 | 入荷予定一覧 API と証拠アップロード API の本番化（GET appointments・POST /api/receiving/evidence） |
| [#148](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/148) | E02-I02-S05 | テスト | 5 | 19.00 | 19 | SCR-02 検品入力の結合・E2E テスト |
| [#152](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/152) | E02-I11-S04 | DB | 5 | 19.00 | 19 | 検品行の測定時刻（measured_at）列の追加と、自動隔離の逸脱記録への測定時刻・ゾーン・記録者の設定 |
| [#160](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/160) | E02-I03-S02 | API | 5 | 19.00 | 19 | 移動履歴と在庫移動記録の API（GET・POST /api/inventory/movements） |
| [#177](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/177) | E02-I07-S03 | API | 5 | 19.00 | 19 | 申請一覧・申請 API（GET と POST） |
| [#189](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/189) | E02-I09-S03 | API | 5 | 19.00 | 19 | 調整の一覧・提案 API（GET と POST） |
| [#193](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/193) | E02-I10-S01 | UI | 5 | 19.00 | 19 | SCR-10 一覧・詳細・判定の画面の本番化 |
| [#194](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/194) | E02-I10-S02 | API | 5 | 19.00 | 19 | ロットの詳細 API（API-011）と入荷の例外の一覧 API（API-008）の本番化（GET 2 本） |
| [#200](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/200) | E03-I01-S02 | API | 5 | 19.00 | 19 | 受注登録 API と注文フォーム選択肢 API の本番化（POST /api/orders・GET /api/orders/options） |
| [#203](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/203) | E03-I02-S01 | UI | 5 | 19.00 | 19 | SCR-12 結果画面の本番化（除外理由の表示・絞り込みの URL 保持） |
| [#210](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/210) | E03-I03-S05 | テスト | 5 | 19.00 | 19 | 期限規則・FEFO の統合テスト |
| [#218](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/218) | E03-I04-S07 | テスト | 5 | 19.00 | 19 | SCR-12 結合・E2E テスト（引当の同時実行・業務確認・取消） |
| [#220](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/220) | E04-I01-S01 | UI | 5 | 19.00 | 19 | ピッキング・積込のスキャン画面の本番化 |
| [#241](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/241) | E05-I02-S01 | UI | 5 | 19.00 | 19 | 配送一覧・記録フォームの画面の本番化 |
| [#242](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/242) | E05-I02-S02 | UI | 5 | 19.00 | 19 | 証拠取得の画面（写真・署名・位置・荷降ろし）の本番化 |
| [#253](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/253) | E05-I05-S06 | テスト | 5 | 19.00 | 19 | オフライン保存・同期の結合・E2E テスト |
| [#256](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/256) | E05-I06-S02 | API | 5 | 19.00 | 19 | 運転手の POD 修正 API と配送詳細の拡張 |
| [#258](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/258) | E05-I06-S04 | API | 5 | 19.00 | 19 | 承認・却下 API と修正一覧 API（POST と GET） |
| [#260](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/260) | E05-I06-S06 | UI | 5 | 19.00 | 19 | 職員向け「配送証拠の履歴」画面と承認操作（区画 G・H） |
| [#269](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/269) | E05-I03-S09 | テスト | 5 | 19.00 | 19 | SCR-19 ルート作成の結合・E2E テスト |
| [#275](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/275) | E05-I07-S06 | テスト | 5 | 19.00 | 19 | SCR-19 公開・変更・取消の結合・E2E テスト |
| [#282](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/282) | E06-I01-S07 | UI | 5 | 19.00 | 19 | SCR-21 取込結果パネルと取込履歴の本番化（行番号つきの却下行・予定枠の増減・起点未設定の警告） |
| [#288](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/288) | E06-I01-S06 | テスト | 5 | 19.00 | 19 | SCR-21 E2E テスト（成功・ハッシュ不一致・重複・形式エラー・上限超過）PC と 390px・本番は読み取りだけ |
| [#289](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/289) | E06-I02-S01 | UI | 5 | 19.00 | 19 | SCR-23 確認待ち一覧・詳細の本番化（残り時間表示・確認ボタン・ページ送り・ロットの業務コード表示） |
| [#290](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/290) | E06-I02-S02 | API | 5 | 19.00 | 19 | API-043 GET 確認待ち一覧 と API-046 POST アラームの確認 |
| [#295](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/295) | E06-I03-S03 | API | 5 | 19.00 | 19 | API-044・045 GET 逸脱ケースの一覧・詳細の本番化と判定期限・エスカレーション項目の追加（API-D-136） |
| [#302](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/302) | E06-I04-S01 | UI | 5 | 19.00 | 19 | SCR-25 予定枠の表とクローズ操作の本番化 |
| [#307](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/307) | E06-I04-S05 | テスト | 5 | 19.00 | 19 | SCR-25 E2E テスト（PC と 390px・取込 → 欠け → 補充 → クローズ・起点未設定）ステージングで実施 |
| [#317](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/317) | E06-I07-S05 | DB | 5 | 19.00 | 19 | 事象に結び付くリズムの同期関数（入荷・出荷の移動、アラームの確認、来訪者の退場） |
| [#318](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/318) | E06-I07-S06 | DB | 5 | 19.00 | 19 | 時刻で決まるリズムの同期関数（衛生のシフト、日次と月次のレビュー） |
| [#326](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/326) | E06-I08-S02 | API | 5 | 19.00 | 19 | API-D-139 POST 記録の入力（衛生・入場・退場・レビュー） |
| [#332](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/332) | E07-I01-S01 | UI | 5 | 19.00 | 19 | SCR-26 検索フォーム・結果（3 レーンの枠・家系・終点・切り詰め）の本番化と日付表記 YYYY/MM/DD の統一 |
| [#335](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/335) | E07-I01-S04 | テスト | 5 | 19.00 | 19 | トレース検索の単体・DB・E2E テスト（家系・切り詰め・個人情報の除外・回数制限・日付表記） |
| [#338](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/338) | E07-I02-S03 | UI | 5 | 19.00 | 19 | SCR-26・27 の検索の種類の追加（米の産地・社内ロット番号）と社内管理の枠・対象列の表示 |
| [#340](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/340) | E07-I03-S01 | DB | 5 | 19.00 | 19 | 社内管理レーンの表と制約（連動表・ロット作成トリガー・回収の CHECK 拡張） |
| [#346](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/346) | E07-I04-S02 | UI | 5 | 19.00 | 19 | SCR-27 行の編集・返品受入・廃棄確認の記録・照合・クローズ前の確認 4 項目 |
| [#354](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/354) | E07-I04-S07 | テスト | 5 | 19.00 | 19 | 回収の DB テスト（範囲確定の等式・照合の数値例・クローズ前の 4 項目・履歴の欠け） |
| [#358](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/358) | E07-I05-S01 | DB | 5 | 19.00 | 19 | 回収通知の DB（版の表・状態遷移・ケースの遷移） |
| [#363](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/363) | E07-I05-S04 | UI | 5 | 19.00 | 19 | SCR-27 通知パネル（作成・版の履歴・承認・送付・結果の表示） |
| [#364](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/364) | E07-I05-S05 | テスト | 5 | 19.00 | 19 | 回収通知のテスト（承認者の分離・期限・出箱・再送・状態遷移） |
| [#370](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/370) | E08-I02-S03 | API | 5 | 19.00 | 19 | API-D-148 / 153 / 154 GET マスターの一覧・承認待ち（差分つき）・版の履歴と利用状況 |
| [#376](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/376) | E08-I02-S06 | UI | 5 | 19.00 | 19 | SCR-31 種類のタブ・一覧・承認・版の履歴（E・H・J 区画） |
| [#377](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/377) | E08-I02-S07 | UI | 5 | 19.00 | 19 | SCR-31 提案フォーム（共通項目と 8 種類の欄・期限種別・温度ポリシー） |
| [#378](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/378) | E08-I02-S08 | テスト | 5 | 19.00 | 19 | マスター版管理の DB テスト（遷移・重複期間・承認者の分離・温度ポリシーの優先） |
| [#385](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/385) | E08-I03-S04 | UI | 5 | 19.00 | 19 | SCR-32 契約の一覧・変更の提案・承認・版の履歴（A〜D 区画） |
| [#387](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/387) | E08-I03-S06 | テスト | 5 | 19.00 | 19 | SCR-32 のテスト（ルール判定の版選択・自己承認・UNSET の保留・却下・E2E） |
| [#389](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/389) | E10-I01-S02 | DB | 5 | 19.00 | 19 | レポート 7〜12 の問い合わせ（受入差異・配送実績・POD 完全性・法令順守・リコール照合・変更履歴） |
| [#390](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/390) | E10-I01-S03 | API | 5 | 19.00 | 19 | API-D-080 / 081 / 082 GET レポートのカタログ・表示・CSV |
| [#391](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/391) | E10-I01-S04 | UI | 5 | 19.00 | 19 | SCR-28 レポートの選択・条件・結果の表・件数と合計・CSV 出力 |
| [#400](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/400) | E10-I02-S04 | UI | 5 | 19.00 | 19 | SCR-29 作成フォーム・作成済みの一覧・詳細と検証（A〜D 区画） |
| [#403](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/403) | E10-I03-S02 | UI | 5 | 19.00 | 19 | SCR-30 検索条件・イベントの表・詳細・「この条件でエクスポート」（E2E を含む） |
| [#410](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/410) | E10-I04-S04 | UI | 5 | 19.00 | 19 | SCR-36 保持スケジュール・法的保留・パージ・履歴のエクスポート（A〜D 区画） |
| [#414](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/414) | E11-I01-S03 | テスト | 5 | 19.00 | 19 | 拘束時間・平均運転時間・時間外・納品日・デポ営業時間の境界単体テスト |
| [#415](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/415) | E11-I01-S05 | API | 5 | 19.00 | 19 | 見積のない区間の到着予定計算を是正（0分扱いをやめる） |
| [#418](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/418) | E11-I01-S08 | ドキュメント | 5 | 19.00 | 19 | 休憩解釈の法令出典による再検証と規則セット改訂要否の判断 |
| [#419](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/419) | E11-I01-S09 | API | 5 | 19.00 | 19 | 判定関数の本番モジュール化（勤務の時系列・地図の見積・連続運転・休憩の取り方・休息期間 — 規則 5 種） |
| [#420](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/420) | E11-I01-S10 | API | 5 | 19.00 | 19 | 判定関数の本番モジュール化（拘束・運転時間の平均・年間の時間外・納品日・デポの営業時間 — 規則 8 種） |
| [#428](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/428) | E11-I03-S04 | API | 5 | 19.00 | 19 | 下書き保存 API（API-D-124）に休止の挿入・再計算を追加 |
| [#441](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/441) | E11-I06-S04 | インフラ | 5 | 19.00 | 19 | チェック用 service_role 鍵の環境別配置と漏えい防止検査 |
| [#447](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/447) | E12-I03-S02 | API | 5 | 19.00 | 19 | 相関 ID の全層引き継ぎと構造化ログの形式を統一 |
| [#450](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/450) | E12-I04-S02 | インフラ | 5 | 19.00 | 19 | Storage のファイルの複製・整合確認と、復旧手順書 |
| [#451](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/451) | E12-I05-S04 | DB | 5 | 19.00 | 19 | Storage バケットの非公開化・署名 URL の期限・パス規約 |
| [#454](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/454) | E12-I06-S01 | DB | 5 | 19.00 | 19 | pg_cron / pg_net の有効化とジョブ登録マイグレーション |
| [#456](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/456) | E12-I07-S01 | DB | 5 | 19.00 | 19 | 日本語の架空デモデータ（シード） |
| [#462](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/462) | E13-I02-S02 | DB | 5 | 19.00 | 19 | 検査段の冪等キー重複・スキーマ版の検査と、拒否の記録（理由・最初の行番号） |
| [#464](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/464) | E13-I04-S01 | DB | 5 | 19.00 | 19 | 出箱への書込みを業務 RPC に組み込む（同一トランザクション） |
| [#470](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/470) | E14-I02-S02 | 移行 | 5 | 19.00 | 19 | マスター（SKU・顧客・仕入先・拠点・機器）の変換 |
| [#478](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/478) | E14-I05-S02 | API | 5 | 19.00 | 19 | 注文の凍結と制御された手動キュー |
| [#486](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/486) | E15-I03-S04 | テスト | 5 | 19.00 | 19 | 3 年分のデータでのロット追跡の性能測定（NFR-PERF-02） |
| [#493](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/493) | E15-I06-S03 | UI | 5 | 19.00 | 19 | 390px 幅の共通レイアウト（操作ボタンの折返し・固定領域） |
| [#495](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/495) | E15-I08-S01 | テスト | 5 | 19.00 | 19 | ワイヤーフレームと画面仕様 §4.1 の自動照合（CI・設計書の変更ごと） |
| [#499](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/499) | E06-I03-S12 | テスト | 5 | 19.00 | 19 | 逸脱ケースの E2E（一連の流れ・クローズ禁止 3 条件・取込者本人・390px・本番は読み取りだけ） |
| [#502](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/502) | E08-I02-S14 | API | 5 | 19.00 | 19 | 端末マスターの登録の API と RPC（device_enrollment の作成・mdm_ref の形・handheld のみ・1 台 1 件） |
| [#504](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/504) | E13-I01-S07 | API | 5 | 19.00 | 19 | inbound CSV の行の検査（API-D-003 の規則・同じ参照コードの揃い・既存予約との重複） |
| [#505](https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues/505) | E13-I01-S08 | API | 5 | 19.00 | 19 | inbound の適用（予約と明細の作成・同じ参照コードの行のまとめ・塊の境目） |
