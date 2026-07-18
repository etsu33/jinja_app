# Product Document Responsibility Audit

## 1. 目的

Product文書の責務、分類、重複および委譲関係を確認し、現行仕様を安全に参照できる文書構造を確定する。

本監査は、Product文書の現行仕様そのものを再定義するものではない。

各文書について、現行分類、責務、重複、物理実装との混在および後続修正方針を記録する。

---

## 2. 対象範囲

- `docs/product/`直下のMarkdown文書35件
- `docs/product/README.md`
- 関連するCore・Knowledge・Analytics・Audit文書
- 責務と実装状況の確認に必要な範囲の実装コードおよびテスト

---

## 3. 監査時点

- 対象ブランチ：`audit/product-document-responsibility`
- 基準ブランチ：`develop`
- develop基準Commit：`a98c3ed026b60edc2e367db3d10787c0773e3f21`
- 監査日：2026年7月16日
- 参照した実装状態：監査開始時点のdevelopへマージ済み実装および文書

本監査後に変更された実装・文書については、後続PRまたは別監査で再確認する。

---

## 4. 現状サマリー

### 文書数

| 項目 | 件数 |
|---|---:|
| Markdown文書 | 35 |
| Active | 16 |
| Reference | 15 |
| Archive | 2 |
| Statusなし | 2 |

Statusなしの文書は以下である。

- `docs/product/README.md`
- `docs/product/product-document-audit.md`

### 参照状況

- `docs/product/README.md`への掲載漏れ：0件
- READMEに記載されたProduct文書の参照切れ：0件
- Product直下に存在するがREADMEへ未掲載の文書：0件

### 初期確認で抽出した論点

- 参照元が監査文書に限られるReference文書がある
- Product文書内にAnalytics Event、PayloadおよびKPIが混在している
- Product文書内にDjango Model、TypeScript型および実装ファイル名が混在している
- Active文書間で責務が重複している可能性がある
- 将来構想と現行実装が同一文書内に混在しているものがある

---

## 5. 判定基準

### Active

以下を満たす文書をActiveとする。

- 現行の体験・機能・分類・契約判断に使用する
- 独立した責務を持つ
- 実装または現在の設計方針と整合している
- 更新条件が明確である
- 単独で現行判断の基準として参照できる

### Reference

以下に該当する文書をReferenceとする。

- Active文書を補助する
- UI案、設計背景、分析案または将来構想を扱う
- 現行仕様を理解する補足情報を持つ
- 単独では現行仕様判断に使用しない

### Archive

以下に該当する文書をArchiveとする。

- 過去の設計判断として履歴価値がある
- 現行仕様には使用しない
- 現行正本への委譲先が明確である
- 誤って現行仕様として参照されない状態にできる

### Delete

以下をすべて満たす文書をDelete候補とする。

- 独自情報がない
- 内容が他文書へ完全に統合されている
- 履歴として残す価値が低い
- 有効な参照元がない
- 削除後も現行仕様または設計判断を失わない

Deleteは本監査だけでは実行せず、参照元とGit履歴を確認した後続PRで確定する。

### 統合

以下に該当する文書を統合候補とする。

- 複数文書が同じ責務を管理している
- 同一の定義・分類・境界が重複している
- 分離した状態では更新不整合が起きる
- 一方へ情報を移した後、他方をReferenceまたはArchiveへ変更できる

### 保留

以下に該当する場合は判断保留とする。

- 現行実装との整合を確認できていない
- Product方針の判断が必要である
- Core・Knowledge・Analytics監査の結果に依存する
- 現在の参照元だけでは独自責務の有無を判断できない
- 統合または削除により情報を失う可能性がある

保留項目は、必要な追加確認と判断主体を明記する。

---

## 6. 責務境界

| 領域 | Productに残す | 委譲先 |
|---|---|---|
| 体験 | 画面目的、ユーザー導線、Free / Premium境界 | Product |
| システム構造 | Frontend / BFF / Backendの全体責務 | Core |
| 神社知識 | 神社プロフィール、用語、コピー、データ品質 | Knowledge |
| Analytics | Event名、Payload、KPI、Funnel、集計 | Analytics |
| 物理実装 | Model、Serializer、Route、関数名 | 実装コード・テスト |
| 調査履歴 | 実装状況、監査結果、移行判断 | Audit |

### ProductとCore

Productにはユーザー体験、機能目的、画面責務および体験上の境界を残す。

以下はCoreへ委譲する。

- システム全体構造
- Frontend / BFF / Backendの技術責務
- Runtime Snapshotの共通概念
- 認証アーキテクチャ
- 横断的なSource of Truth
- Recommendation全体の依存関係

### ProductとKnowledge

Productには、Knowledgeをどの体験で利用するかを残す。

以下はKnowledgeへ委譲する。

- 神社プロフィールの定義
- 神社データ品質
- 用語定義
- コピー原則
- 神社FactとMeaningの分類
- 出典および検証方針

### ProductとAnalytics

Productには、どのユーザー行動を観測する必要があるかという体験上の目的を残せる。

以下はAnalyticsへ委譲する。

- 正確なEvent名
- Payload
- 必須・任意Property
- Funnel定義
- KPI計算式
- PostHog送信状況
- Web / Mobile間のイベント差
- 集計方法

### 文書正本と実装正本

Product文書は、体験、機能目的、入力・出力の意味および責務境界を管理する。

以下は実装コードとテストを最終的な正本とする。

- Django Modelの正確なField
- Serializer
- API Endpoint
- TypeScript型
- 関数名
- Component名
- 保存処理
- 発火条件の物理実装
- 現行テストケース

---

## 7. ファイル別監査結果

ファイル別監査では、35件すべてについて以下を記録する。

### 全体体験

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `kami-musubi-experience-design.md` | Active | Active維持・整理対象 | 相談・推薦・参拝・振り返りを接続する最上位体験設計 | 実装優先順位、URL物理項目、Backend / Frontend責務が混在 | 最上位体験と画面目的を残し、実装順序はRoadmap、技術責務はCore、物理項目は実装へ委譲 |

### Concierge

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `concierge-first-final-spec.md` | Active | Active維持・整理対象 | Concierge Firstの主導線、Home Hero、Entry、Filter、Need / Compat境界 | 実装前表現、MVP実装順、Score v2入力、URL query詳細が混在 | 現行体験導線と画面責務を残し、Score詳細はAnalytics / Backend、実装順はRoadmapへ委譲 |
| `concierge-modes.md` | Active | Active維持 | Need / Compat / Route / Theme / Search Modeの役割と入力文脈 | 大きな責務混在は確認されない | Mode種類または責務変更時のみ更新する現行方針を維持 |
| `consultation-theme-taxonomy.md` | Active | Active維持・境界整理対象 | Home Hero / Concierge Entryで使う相談テーマ、表示文言、`theme_key` | `consultation_axis`、`need_tags`、`history_theme`対応表がBackend・Knowledge責務と重複する可能性 | UI分類と表示文言をProductに残し、解釈・推薦ロジックはBackend、意味分類はKnowledge監査後に委譲範囲を確定 |
| `recommendation-v4-interpreter-contract.md` | Active | Active維持・意味契約への整理完了 | Consultation Interpreterの出力項目と意味責務 | 実装ファイル名、Expected Keys、KPI、現行関数名が混在 | Fieldの意味契約を残し、物理構造・関数名・KPIは実装またはAnalyticsへ委譲 |
| `home-hero-final-wireframe.md` | Reference | Reference維持 | Home Heroの画面構成とUI補足 | Active文書と画面責務が一部重複 | UI補足に限定し、体験判断は`concierge-first-final-spec.md`へ委譲 |
| `concierge-entry-final-wireframe.md` | Reference | Reference維持 | Concierge Entryの画面構成とUI補足 | Active文書と画面責務が一部重複 | UI構成、表示要素、CTA補足に限定 |
| `concierge-filter-area.md` | Reference | Reference維持・整理対象 | Filterの画面構成と補助条件UI | Frontend / Backend責務とデータ接続詳細が一部混在 | UI責務を残し、解釈・判定はBackend正本へ委譲 |
| `need-mode-ui-flow.md` | Reference | Reference維持 | Need ModeのUI導線と表示責務 | `need_tags`、`matched_need_tags`、Backend責務がActive文書と重複 | UI表示・導線補足に限定し、Mode責務は`concierge-modes.md`へ委譲 |
| `compat-mode-ui-flow.md` | Reference | Reference維持 | Compat ModeのUI導線と補助情報表示 | 占術、方位、推薦接続の記述がMeaning / Direction文書と重複 | UI補足に限定し、Mode責務とMeaning変換へ委譲 |
| `concierge-card-architecture.md` | Reference | Reference維持・統合完了 | Concierge結果画面のCard Tree、Props、Renderer、Visibility State別の表示原則、Card別Visibility PolicyおよびSection Routing | PropsやRendererなど物理Frontend構造が中心で、実装との差分が生じやすかった。`card-visibility-renderer-split.md`とVisibility表示原則が重複していた | 設計背景として維持し、現行構造はFrontend実装・テストを正本とする。`card-visibility-renderer-split.md`のVisibility State別表示原則とCard別Visibility Policyを統合済み |
| `card-visibility-renderer-split.md` | Archive | 統合完了・Archive | Card VisibilityとRenderer責務分離 | `concierge-card-architecture.md`とCard表示・Renderer責務が重複していた。実装進捗チェックリストや次PR候補などPR計画の記載も混在していた | 独自のVisibility State別表示原則とCard別Visibility Policyを`concierge-card-architecture.md`へ統合し、本書はArchiveへ変更した |
| `concierge-first.md` | Archive | Archive維持 | Concierge First初期思想 | 現行仕様ではなく、正本への委譲も明確 | 現状維持 |
| `concierge-first-wireframe.md` | Archive | Archive維持 | Concierge First初期ワイヤーフレーム | 現行UI正本への委譲が明確 | 現状維持 |

### Meaning・Recommendation

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `history-theme-taxonomy.md` | Active | Active維持・Product上のカテゴリ正本として責務境界整理完了、移管判断は保留継続 | `history_theme`7カテゴリの名称、定義、行動テーマおよび概念境界 | カテゴリ定義、相談例、ご利益との関係はProduct体験仕様よりKnowledgeの用語・意味分類責務に近い。Product / Backend / Analyticsの責務説明も混在していた | Knowledge責務監査で移動先を確定し、Productには体験上の利用箇所のみ残す。移管完了まではActiveとして扱う |
| `meaning-translation-mapping.md` | Active | Active維持・責務整理完了 | 相談、意味変換、神社文脈、Action、Visit、Reflectionを接続するProduct上の変換関係 | Runtime実装状況、Backendファイル名、Score計算、Snapshot物理構造、Analytics指標、神社データ管理方針が混在していた | 体験上の変換関係と各機能への接続を残す。システム構造はCore、カテゴリ定義と神社付与基準はKnowledge、Scoreと実装詳細はBackend、Event・KPIはAnalyticsへ委譲 |
| `shrine-detail-layer.md` | Active | Active維持 | 神社詳細画面のPublic / Context / Personal Layerと画面責務 | 大きな責務混在は確認されないが、Meaning Layer補足文書およびv3設計と情報レイヤの説明が重複する | 神社詳細の情報レイヤ境界を管理する正本として維持し、詳細な画面構成や実装順序は補足文書・実装へ委譲 |
| `shrine-detail-meaning-layer.md` | Reference | 統合候補（統合保留） | 神社詳細におけるMeaning情報の表示順、主役情報、補強情報および表現原則 | `shrine-detail-layer.md`の情報レイヤ（Public / Context / Personal）とは異なる軸（情報レイヤー順、主役/補強情報、コピー例文）を持ち、単純な重複ではない。コピー例文とWikipedia化回避ガイドラインはKnowledge責務に近い。既存コード対応、今後の実装方針、TODOも混在する | `shrine-detail-layer.md`への統合は新規Product仕様の追加に相当するため本タスクでは実施しない。コピー生成原則に該当する部分はKnowledge責務監査での移管先確定を待つ。統合方針が確定するまでReferenceを維持する |
| `shrine-detail-v3-design.md` | Active | Reference化候補・整理対象 | Shrine Detail v3のUX再設計、画面構成および実装時の設計背景 | Current State、Proposed構造、将来のCardVisibilityPolicy、Analytics Event・KPI、Premium導線、実装境界が混在する。現行仕様の正本というより実装フェーズの設計記録に近い | 現行の画面責務は`shrine-detail-layer.md`へ統合し、v3移行時の設計背景としてReferenceへ変更する。AnalyticsはAnalytics文書へ委譲 |
| `direction-ranking-design.md` | Reference | Reference維持 | 方角・吉方位を推薦補助軸として扱う将来設計 | 本文のDirection Mode、Score構造および九星補助は現行実装と一致せず、参照元も監査文書のみ | 将来設計であることを明示したReferenceとして維持する。現行Ranking判断には使用せず、Backend実装・テストを正本とする |
| `visit-style-taxonomy.md` | Reference | Reference維持・境界整理対象 | Concierge Filterで使用する参拝スタイルの表示分類、内部タグおよびUI上の扱い | `extraCondition`変換、Backendへの接続、推薦加点ルールなど物理処理が混在する。一方でUI分類として独立した価値はある | UI表示分類と内部値対応を残し、自然文変換、スコア、重み、API契約はBackend実装へ委譲 |

### Action・Visit・Reflection

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `action_suggestion_v4.md` | Active | Active維持・Product責務整理完了、Analytics物理契約は委譲済み | Recommendation Reasonから次に取りやすい行動を生成するInput / Outputと生成ルール | `action_suggestion_reflection_preview_view`、`actionPromptType`などAnalytics Event・Payload契約が混在していた | Actionの意味、出力項目、生成原則をProductに残し、正確なEvent名・Payload・計測語彙はAnalyticsへ委譲 |
| `visit-reflection-flow.md` | Active | Active維持・体験責務への整理完了 | 参拝完了からReflection保存、次回相談までを接続する体験とVisit / Reflectionの意味責務 | Event名、TypeScript Payload型、Django Model全文、Index、採用Field、Mobile送信状況、PostHog集計、実装ファイル名が混在していた | 体験フロー、Visit / Reflectionの意味責務、Free / Premium境界を残す。Event・Payload・FunnelはAnalytics、Model・Field・Index・APIは実装とテストへ委譲 |
| `reflection-timeline-design.md` | Reference | Reference維持・対応不要 | 写真、御朱印、検索、比較、感情推移など、長期的な振り返り体験の構想 | 写真、御朱印、検索、感情推移、行動記録、Premium分析、KPIなど未実装または将来構想が現行仕様として混在していた。現行のTimeline体験責務はJourney Timelineへ統合済み | 現行のTimeline体験責務はJourney Timeline正本へ統合完了。本書は長期構想・設計思想を扱うReferenceとして維持する。統合候補文書の再確認でも追加の重複・独自情報は確認されず、対応不要と判断した |
| `journey-timeline-design.md` | Active | Active正本 | 相談・提案・参拝・振り返りを「ご縁の歩み」として時系列で接続する現行体験設計 | 従来は内容が簡略でReflection Timelineと責務が重複していたが、Event・State分離とVisit / Reflection接続方針を整理し、正本として統合完了 | Journey Timelineの現行体験仕様を管理する正本として維持する。正確なEvent構造・API・Serializer・表示処理はBackend・Mobile実装とテストを正本とする |

`reflection-funnel-dashboard.md`は`docs/analytics/reflection-funnel-dashboard.md`へ移管が完了したため、本表から除外した（対象範囲はdocs/product/直下の文書のため）。移管の詳細は9節を参照する。

### Premium・Billing

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `premium-experience.md` | Active | Active維持・統合完了 | Free / Premiumの体験価値、画面別の体験差、Premium対象、価格表現の原則、保存・履歴・比較の原則 | `pricing.md`および`monetization-flow-design.md`とPremium価値の説明が一部重複していた。料金・Billing判定・収益導線・Analyticsへの委譲先が明記されていなかった | Premium体験価値の正本として維持。責務境界節で料金・Billing判定・収益導線・Analyticsの委譲先を明記済み。`pricing.md`のPremium対象一覧および価格表現の原則を統合済み |
| `pricing.md` | Archive | 統合完了・Archive | Premiumの支払対象、Free / Premium境界および価格表現の原則 | 具体的な料金・請求周期・プランを管理しておらず、内容の大半が`premium-experience.md`と重複していた（Free/Premiumの役割、価格表現の原則テーブルなど）。参照元もAudit文書に限られていた | 独自内容（Premium対象にできる/しないものの一覧、価格表現の原則）を`premium-experience.md`へ統合し、本書はArchiveへ変更した |
| `billing-paywall.md` | Active | Active維持・大幅整理完了 | Billing状態、Premium優先、Free回数制限およびPaywall表示の判定原則 | API Endpoint、Response Field、未閉鎖のJavaScript判定コード、テスト要件が混在し、Markdownコードブロックも未閉鎖だった | 利用可否と判定原則をProductに残し、API Endpoint・Field・実装コード・テストケースはBackend / Frontend実装とテストへ委譲済み。コードブロック不整合も解消 |
| `monetization-flow-design.md` | Reference | Reference維持・Analytics委譲完了 | Premium提示タイミング、CTA方針、収益導線思想およびRetention設計背景 | Event名、Funnel、Revenue KPI、Context Propertyが現行仕様として本文に列挙され、未実装の将来拡張案との境界が曖昧だった | 収益導線の設計思想をReferenceとして維持。Event・Payload・KPI・Funnelは`docs/analytics/`配下へ委譲し、将来拡張は現行仕様に含まない旨を明記済み |

### Explore・投稿

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `explore-integration-design.md` | Reference | Reference維持 | Recommendationから神社一覧・比較・位置確認・詳細へ接続するExploreの役割と画面責務 | 大きな責務混在は確認されない。現行仕様の詳細ではなく、Exploreを検索・比較・位置確認へ限定する補足設計として整理されている | Referenceとして維持する。Recommendation、Meaning、神社詳細およびシステム構造は各正本へ委譲し、Exploreの役割または画面責務が変更された場合のみ更新する |
| `shrine-submission-flow.md` | Active | Active維持・大幅整理対象 | 検索で見つからない神社を投稿し、審査中状態を表示して公開マスターへ接続するユーザー体験 | URL、API Endpoint、HTTP Status、Serializer・View・Service責務、BFF実装方針、重複判定ロジック、実データ検証結果、未確認事項、将来拡張、神社データ利用条件が混在する | 投稿入口、投稿後復帰、審査中表示、公開までの体験責務をProductに残す。重複判定・Endpoint・Status・物理実装はBackend実装とテスト、神社プロフィール・タグ・推薦利用条件はKnowledge、確認済み・未確認・実データ検証結果はAuditへ委譲する |

### UI・補足設計

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `README.md` | Active | Active付与済み | Product文書群の入口、読む順番、分類および各文書の役割案内 | 文書自体にStatus表記がなく、監査結果確定後の分類変更が未反映であった | Product文書の入口としてActiveを付与済み。読む順番、正本、Reference、Archiveおよび役割説明はJourney Timeline正本化を反映して更新済み |
| `product-document-audit.md` | Statusなし | Reference付与・整理対象 | 過去のProduct文書分類、統合履歴および整理時の判断記録 | 現行READMEの分類根拠として参照されている一方、今回の責務監査と監査範囲が重複する。Statusがなく、どちらが最新監査か判断しにくい | 過去の分類監査としてReferenceを付与する。今回の`docs/audit/product-document-responsibility-audit.md`を責務監査の最新記録とし、役割境界を明記する |
| `mobile-bottom-navigation.md` | Reference | Reference維持 | Mobile下部ナビゲーションのタブ構成、配置理由およびUI設計補足 | UI構成の補足に限定されており大きな責務混在はないが、現行画面構造との差分が生じる可能性がある | Mobile UIの設計背景としてReferenceを維持し、現行のRoute、画面構成および挙動はMobile実装とテストを正本とする |

---

## 8. 重複・混在一覧

### Coreとの重複

初期確認では、以下の重複候補がある。

- Backend / Frontend責務
- Runtime Snapshot
- Recommendation Score
- 認証
- Source of Truth
- システム全体のデータフロー

### Knowledgeとの重複

初期確認では、以下の重複候補がある。

- `history_theme`の定義
- 神社プロフィール
- ご利益と意味の関係
- Fact / Meaningの区分
- コピー原則
- 神社データの利用可否

### Analyticsとの重複

初期確認では、以下の重複候補がある。

- Event名
- Payload型
- 必須Property
- KPI
- Funnel
- PostHog送信状況
- Web / Mobile間のEvent差
- 集計方法

### 実装詳細の混在

初期確認では、以下の混在候補がある。

- Django Model全文
- TypeScript型全文
- API Endpoint
- 実装ファイル名
- Component名
- テスト要件
- 現行の未実装状況

### 未実装案の混在

以下を現行仕様と分離する必要がある。

- 将来のPremium機能
- 未実装の検索・比較・分析機能
- 将来の価格・プラン構成
- 未接続のMobile導線
- 将来の共通Hook・共通型基盤
- 今後のMigrationおよび拡張案

---

## 9. 最終分類

### Active

- `README.md`
- `action_suggestion_v4.md`
- `billing-paywall.md`
- `concierge-first-final-spec.md`
- `concierge-modes.md`
- `consultation-theme-taxonomy.md`
- `history-theme-taxonomy.md`
- `journey-timeline-design.md`
- `kami-musubi-experience-design.md`
- `meaning-translation-mapping.md`
- `premium-experience.md`
- `recommendation-v4-interpreter-contract.md`
- `shrine-detail-layer.md`
- `shrine-detail-v3-design.md`
- `shrine-submission-flow.md`
- `visit-reflection-flow.md`

### Reference

- `compat-mode-ui-flow.md`
- `concierge-card-architecture.md`
- `concierge-entry-final-wireframe.md`
- `concierge-filter-area.md`
- `direction-ranking-design.md`
- `explore-integration-design.md`
- `home-hero-final-wireframe.md`
- `mobile-bottom-navigation.md`
- `monetization-flow-design.md`
- `need-mode-ui-flow.md`
- `product-document-audit.md`
- `reflection-timeline-design.md`
- `shrine-detail-meaning-layer.md`
- `visit-style-taxonomy.md`

### Archive

- `card-visibility-renderer-split.md`
- `concierge-first.md`
- `concierge-first-wireframe.md`
- `pricing.md`

### 統合候補

- `shrine-detail-meaning-layer.md`
  - `shrine-detail-layer.md`への統合は新規Product仕様の追加に相当するため保留。コピー生成原則に該当する部分はKnowledge文書への移管候補（Knowledge責務監査待ち）
- `history-theme-taxonomy.md`
  - Knowledge移管候補（責務境界整理は完了、移管判断は保留継続）

Timeline正本名称は「Journey Timeline」で確定した。`journey-timeline-design.md`をJourney Timelineの現行体験仕様の正本（Active）とし、`reflection-timeline-design.md`は長期構想・設計思想を扱うReferenceへ変更した。統合候補としての判断保留は解除済みである。

`reflection-funnel-dashboard.md`のAnalytics移管は完了した。`docs/analytics/reflection-funnel-dashboard.md`へ移動し、Product文書（35件）の対象から除外した。以後のProduct文書総数は34件として扱う。

`card-visibility-renderer-split.md`の統合は完了した。独自のVisibility State別表示原則とCard別Visibility Policyを`concierge-card-architecture.md`へ統合し、本書はArchiveへ変更した。

`pricing.md`の統合は完了した。独自のPremium対象一覧と価格表現の原則を`premium-experience.md`へ統合し、本書はArchiveへ変更した。

### Delete候補

現時点ではなし。

Archive済み文書（`card-visibility-renderer-split.md`、`pricing.md`）は、参照元の更新状況を確認したうえで、後続PRでDeleteを再判定する。

### 判断保留

- `history-theme-taxonomy.md`のKnowledge移管先
- `shrine-detail-meaning-layer.md`の統合方針（Product仕様追加を伴わない統合方法、またはKnowledge移管の要否）
---

## 10. docs/product/README.mdとの差分

Product Integration Candidate Cleanup（`pricing.md`・`card-visibility-renderer-split.md`・`shrine-detail-meaning-layer.md`・`reflection-timeline-design.md`の再確認）完了時点で、以下をREADME.mdへ反映済みである。

- **現在分類と監査判定が一致する文書**: 本監査で確定したActive16 / Reference14 / Archive4の分類は、すべてREADME.mdの「正本」「Reference」「Archive」各表と一致している
- **Status変更が必要な文書**: `pricing.md`と`card-visibility-renderer-split.md`をReferenceからArchiveへ変更し、README.mdのArchive表へ移動済み。両文書の役割欄には統合先（`premium-experience.md`／`concierge-card-architecture.md`）を明記した
- **README上の役割説明を修正する文書**: `premium-experience.md`の役割欄に「Premium対象および価格表現の原則」を追加、`concierge-card-architecture.md`の役割欄に「Visibility PolicyおよびRenderer責務の設計補足」を反映済み
- **読む順番を変更する文書**: なし（`pricing.md`・`card-visibility-renderer-split.md`はいずれも「読む順番」に含まれていなかったため影響なし）
- **Archive候補**: `pricing.md`・`card-visibility-renderer-split.md`の2件をArchiveへ変更済み。Delete判定は参照元更新状況を確認する後続PRへ持ち越す（8節参照）
- **統合後にREADMEから除外する文書**: なし。Archive化した2件もREADME上ではArchive表に残し、統合済みである旨を役割欄に明記する方針とした（Archive文書自体をREADMEから削除すると参照経路が失われるため）
- **統合を見送った文書**: `shrine-detail-meaning-layer.md`はReferenceのまま維持（統合には新規Product仕様の追加が伴うため見送り）。`reflection-timeline-design.md`は既存のJourney Timeline正本化（PR #2056）で対応済みのためReferenceのまま追加変更なし。いずれもREADME.mdの記載を変更する必要はなかった

---

## 11. 後続PR設計

### PR1: Product README・Status統一

Product README、Status表記および分類表示を監査結果へ合わせる。

### PR2: Concierge責務整理

Concierge体験、Mode、入力分類、UI補足および実装契約の責務を整理する。

### PR3: Meaning・Recommendation責務整理

Meaning Translation、Taxonomy、InterpreterおよびRecommendation関連文書の責務を整理する。

### PR4: Action・Visit・Reflection責務整理

Action、Visit、ReflectionおよびTimeline関連文書の責務を整理する。

### PR5: Premium・Billing責務整理

Premium価値、Pricing、PaywallおよびMonetization文書の責務を整理する。

### PR6: ProductからAnalytics契約を委譲

Event、Payload、KPI、Funnelおよび実装状況をAnalytics文書へ委譲する。

### PR7: Archive・Delete整理

統合完了後の旧文書について、Archive移動または削除を実行する。

---

## 12. 品質確認

- [x] 35文書すべてに監査判定がある（7節の各表に記録済み。`reflection-funnel-dashboard.md`のAnalytics移管後は34件を対象として扱う）
- [x] Active / Reference / Archive / Delete / 統合 / 保留の基準が明文化されている
- [x] Productと他領域の境界が整理されている
- [x] 後続PRの変更範囲が分離されている
- [x] READMEとの差分が明示されている（10節）
- [x] Markdownコードブロックが閉じている
- [x] Markdown参照切れがない
- [x] `git diff --check`が成功する
- [x] 意図しないファイル変更が含まれていない

---

## 13. 結論

Product直下のMarkdown文書35件について、現行分類、主責務、重複、委譲先および後続対応を確認した。

監査時点の最終分類は以下である（`reflection-funnel-dashboard.md`の`docs/analytics/`への移管、`pricing.md`の`premium-experience.md`への統合、`card-visibility-renderer-split.md`の`concierge-card-architecture.md`への統合を反映した件数）。

| 分類 | 件数 |
|---|---:|
| Active | 16 |
| Reference | 14 |
| Archive | 4 |
| 合計 | 34 |

監査により、Product文書には以下の責務混在が存在することを確認した。

- Coreが管理すべきシステム構造および技術責務
- Knowledgeが管理すべき意味分類、神社知識およびデータ品質
- Analyticsが管理すべきEvent、Payload、KPIおよびFunnel
- 実装コードとテストが管理すべきModel、Field、Endpointおよび物理挙動
- Auditが管理すべき検証結果、未確認事項および移行履歴

Product文書には、ユーザー体験、画面目的、機能上の意味、ユーザー導線およびFree / Premium境界を残す。

現時点でDeleteへ確定する文書はない。

統合・移管候補は、独自情報の移管、委譲先の確認、参照元更新および参照切れ確認を完了した後に、Reference、ArchiveまたはDeleteへ再分類する。

後続PRでは、委譲先を先に整備し、Product文書から情報を削除することで、正本が一時的に失われないようにする。

---

## 14. 再監査ログ（2026-07-18 再確認）

Product Integration Candidate Cleanup（9節「統合候補」「Delete候補」「判断保留」）で扱った4文書について、develop最新化後に内容を再確認した。本節は既存の分類判断を変更するものではなく、再確認結果と新規に発見した事項を記録する。

### 再確認結果

| 文書 | 現在分類 | 再確認結果 | 備考 |
|---|---|---|---|
| `card-visibility-renderer-split.md` | Archive | 判断維持 | 12行のポインタスタブへ整理済みで、独自情報は残っていない。`concierge-card-architecture.md`が全内容を保持していることを再確認した |
| `pricing.md` | Archive | 判断維持 | 12行のポインタスタブへ整理済み。`premium-experience.md`の「Premium対象」「価格表現の原則」節が独自情報を保持していることを再確認した |
| `shrine-detail-meaning-layer.md` | Reference | 判断維持・参照元確認 | `docs/README.md` / `docs/product/README.md` / `docs/audit/product-document-responsibility-audit.md` / `docs/audit/root-docs-classification-audit.md` / `docs/audit/archive-final-classification.md`の5箇所から参照されていることを確認した。統合には新規Product仕様の追加が伴うため、引き続き統合を見送る |
| `history-theme-taxonomy.md` | Active | 判断維持・新規課題発見 | Product / Backend / Analyticsの責務境界整理は完了済み（PR #2052）であることを確認した。Knowledge移管先は依然未確定。加えて、`docs/knowledge/glossary.md`の`history_theme`定義（「神社の歴史や由緒から抽出した意味テーマ」）が、本書の定義（相談内容から意味変換される、神社側の意味文脈として扱うが由緒から機械的に抽出されるものではない）と一致していないことを新たに確認した |

### Delete候補（`card-visibility-renderer-split.md` / `pricing.md`）の参照元全文検索

Delete判定に向けて、両文書への参照元を`docs/`配下で全文検索した。

- `card-visibility-renderer-split.md`: `docs/product/README.md`（Archive表としての意図的な掲載）以外に参照元なし
- `pricing.md`: `docs/product/README.md`（Archive表としての意図的な掲載）、`docs/product/shrine-detail-layer.md`・`docs/product/monetization-flow-design.md`（#2062で参照を`premium-experience.md`へ修正済み）以外に参照元なし

両文書とも、Archive表への意図的な掲載以外に現行の参照元は確認されなかった。ただし、統合先（`concierge-card-architecture.md` / `premium-experience.md`）が実装との整合を保っているかは本監査の範囲外であり、Delete実行の判断は本PRでは行わない。統合先が今後変更される可能性を考慮し、履歴保存の価値がある間はArchiveのまま維持する。

### `history-theme-taxonomy.md`のKnowledge移管先が未確定な理由

`history-theme-taxonomy.md`は`docs/`配下15箇所から参照されている（`docs/product/README.md`、`meaning-translation-mapping.md`、`visit-reflection-flow.md`、`consultation-theme-taxonomy.md`、複数のAudit文書等）。Knowledgeへ移管する場合、これら参照元の文脈（Product体験文書からの参照か、Knowledgeの用語定義としての参照か）を個別に判定した上で更新する必要があり、本PRの範囲である「監査結果の記録」を超える。移管の実行は、Knowledge Base側の受け入れ文書（`glossary.md`の定義修正を含む）が整備された後続PRで行う。

### 新規発見事項（後続PR候補として記録）

`docs/knowledge/glossary.md`の`history_theme`定義と`docs/product/history-theme-taxonomy.md`の定義に齟齬がある。glossary.mdは「神社の歴史や由緒から抽出した意味テーマ」としているが、history-theme-taxonomy.mdでは相談内容から意味変換されて生成される文脈（7カテゴリ）として定義しており、神社の由緒から機械的に抽出される値ではない。この齟齬はKnowledge Base監査（`docs/audit/knowledge-base-refactoring.md`等）または`history-theme-taxonomy.md`のKnowledge移管検討時に解消する。本PRでは記録のみ行い、いずれの文書も変更しない。

### 結論（再確認）

4文書とも分類変更なし。`docs/product/README.md`への追加変更は不要（9節時点の記載が引き続き正確）。Delete判定は継続保留、Knowledge移管は`glossary.md`定義齟齬の解消を前提条件として追加した上で継続保留とする。

---

## 15. history_theme定義の整合性監査（2026-07-18）

14節で発見した`docs/knowledge/glossary.md`と`docs/product/history-theme-taxonomy.md`の定義齟齬について、Product・Knowledge・Core・Analytics・Backend実装・テストを横断して監査し、最小範囲で修正した。

### 確認した文書・実装

- `docs/product/history-theme-taxonomy.md`
- `docs/knowledge/glossary.md`
- `docs/knowledge/shrine-profile-spec.md` / `shrine-data-guide.md` / `action-guide.md` / `reflection-guide.md` / `recommendation-copy-guide.md` / `recommendation-v4-copy-guideline.md`
- `docs/core/recommendation-reason-contract.md` / `meaning-layer-connection.md` / `architecture.md` / `meaning-layer.md` / `roadmap.md` / `recommendation-readiness.md`
- `docs/analytics/`配下18文書（`historyTheme`/`history_theme`言及箇所）
- `backend/temples/models.py`（`Shrine.history_theme` / `ShrineReflection.history_theme` / `ActionEvent.history_theme`）
- `backend/temples/services/meaning_translation.py`（`_resolve_history_theme` / `HISTORY_THEME_BY_DIRECTION` / `HISTORY_THEME_BY_NEED` / `HISTORY_THEME_BY_DECISION` / `REFLECTION_QUESTION_BY_HISTORY_THEME`）
- `backend/temples/services/journey_timeline.py` / `reflection_state_change.py`
- `backend/temples/management/commands/seed_history_theme.py`
- `backend/temples/tests/services/test_meaning_translation.py`

### 判明した事実：`history_theme`は2つの物理的な値を指す同一語彙である

同一の7カテゴリ語彙（守り/静寂/再出発/復興/勝負/学び/縁）を、実装上は責務が異なる2つの値で共有している。

| 値 | 生成タイミング | 生成元 | 実装箇所 |
|---|---|---|---|
| `Shrine.history_theme` | 神社プロフィール作成時（事前・静的） | 神社の由緒・歴史情報をもとに、編集者が手動でタグ付けする | `backend/temples/models.py:253`（help_text: 「神社の歴史文脈タグ」）、`backend/temples/management/commands/seed_history_theme.py`（神社IDごとの手動マッピング） |
| `translation_result.history_theme`（Product上の`history_theme` / `historyTheme`） | 相談ごと（実行時） | `direction_profile.direction` / `need_profile.primary_need_tag` / `need_profile.need_tags` / `decision_context.primary_decision` / `decision_context.decision_candidates`のいずれかから解決される。**`Shrine.history_theme`を直接参照しない** | `backend/temples/services/meaning_translation.py:112-140`（`_resolve_history_theme`）、テストで動作確認済み（`test_meaning_translation.py:32,64,97,117,185`） |

両者は同じ語彙・同じカテゴリ数（7）を共有するが、後者が前者を機械的に「抽出」するわけではない。`meaning-layer-connection.md:128-130`が示すとおり、`Shrine.history_theme`は`translation_result.history_theme`が解決できない場合のFallback先としてのみ接続される。

### 定義差の一覧

| 文書 | 定義文言 | 対応する物理的実体 | 評価 |
|---|---|---|---|
| `docs/product/history-theme-taxonomy.md` | 「相談内容→意味変換→history_theme→神社推薦」。神社側の意味文脈として扱う | `translation_result.history_theme`（Product上で実際に利用される値） | 実装と一致 |
| `docs/knowledge/glossary.md`（修正前） | 「神社の歴史や由緒から抽出した意味テーマ。」 | 曖昧。`Shrine.history_theme`のみを指しているように読めるが、Product/Analytics/Reflection/Journey Timelineが実際に利用する`history_theme`（`translation_result.history_theme`）はこの定義に該当しない | 実装と不一致 |
| `docs/knowledge/shrine-profile-spec.md:250` | 「由緒から抽出した意味テーマ」（Meaning Layer節、「①からの解釈」と明記） | `Shrine.history_theme`（神社プロフィール作成時の値）に限定して記述されている | 文脈上、実装と一致（`Shrine.history_theme`固有の説明として妥当） |
| `docs/analytics/`配下（`shrine-meaning-profile.md`、`consultation-axis-discovery.md`、`recommendation-output-quality-review.md`等） | 「神社側の意味テーマ」「User Stateではない」 | `translation_result.history_theme` | 実装と一致（history-theme-taxonomy.mdと同じ理解） |
| `docs/analytics/reflection-funnel-dashboard.md:167` | 「historyThemeのカテゴリ名称は`docs/product/history-theme-taxonomy.md`の定義に従う」 | - | history-theme-taxonomy.mdを正本として明示的に指定済み。不一致なし |

### 採用した現行定義

`docs/product/history-theme-taxonomy.md`の定義（相談内容から意味変換されて生成される、神社側の意味文脈を表す7カテゴリの語彙。ユーザーの性格・心理状態・将来を断定するために使用しない）を現行定義として採用した。理由は以下のとおり。

- Product / Analytics / Reflection / Journey Timelineが実際に参照する`history_theme`（`historyTheme`）は、実装上`translation_result.history_theme`であり、`_resolve_history_theme`が相談由来のprofileから解決している（`Shrine.history_theme`は未参照）
- `docs/analytics/reflection-funnel-dashboard.md`が既に`history-theme-taxonomy.md`をカテゴリ名称の正本として指定している
- `docs/analytics/shrine-meaning-profile.md`等、複数のAnalytics文書がhistory-theme-taxonomy.mdと同一の理解（神社側の意味文脈、User Stateではない）を採用している

カテゴリ名・カテゴリ数（7）は変更していない。全ドキュメント・Backend実装・テストで一致していることを確認済み。

### 表示名と内部値

`守り` / `静寂` / `再出発` / `復興` / `勝負` / `学び` / `縁`は、表示名と内部値（保存値）が同一である。別名の内部キー（英語スラグ等）は存在しない。`backend/temples/services/meaning_translation.py`のマッピング辞書、`test_meaning_translation.py`のアサーション、`backend/temples/models.py`のフィールド値は全て日本語カテゴリ名をそのまま使用している。

### 修正した文書

- `docs/knowledge/glossary.md`: `history_theme`の定義を「神社の歴史や由緒から抽出した意味テーマ。」から「相談内容を神社側の意味文脈（7カテゴリ）へ接続した意味テーマ。神社の歴史文章から自動抽出される値ではない。」へ修正した。`Shrine.history_theme`（静的・手動タグ付け）と`translation_result.history_theme`（実行時・相談由来）のいずれも「自動抽出」ではないため、この文言は両者と矛盾しない

### 修正しなかった文書と理由

| 文書 | 理由 |
|---|---|
| `docs/product/history-theme-taxonomy.md` | 実装と一致しており、変更不要（制約により変更対象外） |
| `docs/knowledge/shrine-profile-spec.md` | 「② Meaning Layer」節における`history_theme`の記述は`Shrine.history_theme`（神社プロフィール作成時の値）に文脈上限定されており、実装と矛盾しない |
| `docs/knowledge/shrine-data-guide.md` / `action-guide.md` / `reflection-guide.md` / `recommendation-copy-guide.md` / `recommendation-v4-copy-guideline.md` | いずれも`history_theme`をフィールド名・入力項目として列挙するのみで、定義文を持たない。齟齬なし |
| `docs/core/`配下 | `history_theme`を`translation_result`の出力項目、または`Shrine.history_theme`の入力項目として言及するのみで、独自の定義文を持たない。齟齬なし |
| `docs/analytics/`配下 | history-theme-taxonomy.mdと同一の理解（神社側の意味文脈）を採用しており、齟齬なし |
| `backend/temples/models.py`（`Shrine.history_theme`のhelp_text） | 実装コードのコメントであり、本PRの変更対象外（制約により実装コード不変更） |

### Backend実装で実際に生成・保存される値（新規発見・参考情報）

`_resolve_history_theme`が参照する3つの辞書（`HISTORY_THEME_BY_DIRECTION` / `HISTORY_THEME_BY_NEED` / `HISTORY_THEME_BY_DECISION`）には、`復興`のマッピングが存在しない。`復興`は`_resolve_history_theme_secondary`（`direction_profile.themes[1]`相当、Score v3の`history_score`専用）経由でのみ到達可能であり、`REFLECTION_QUESTION_BY_HISTORY_THEME`にも`復興`のキーは存在しない（`test_meaning_translation.py:65`で`history_theme_secondary == "復興"`として確認済み）。これはカテゴリ定義の不一致ではなく、実装の到達可能性に関する観察事項であり、本監査の「history_theme定義の整合性」という主題そのものには影響しない。実装変更は本PRの範囲外のため、後続の実装監査への申し送り事項として記録するに留める。

### Knowledge移管を行うために残る条件

（`history-theme-taxonomy.md`のKnowledge移管そのものは本PRで実行しない。以下は将来の移管判断のために整理した前提条件である。）

- `Shrine.history_theme`（静的・神社プロフィール属性）と`translation_result.history_theme`（実行時・相談由来）が同一語彙を共有し、責務が異なる2つの物理的実体であることを、移管先のKnowledge文書内で明示的に区別できる構成にする
- 移管する場合、`docs/knowledge/shrine-profile-spec.md`（`Shrine.history_theme`の責務）と重複しない形で、Product側の利用文脈（相談接続・7カテゴリの行動テーマ・ご利益との関係）を配置する
- `docs/product/history-theme-taxonomy.md`を参照する15箇所（14節参照）の参照文脈がProduct体験文書からの参照かKnowledge用語定義としての参照かを個別判定し、移管後の参照先を決定する

### 参照元更新が必要な範囲

本PRでは`docs/knowledge/glossary.md`の定義文言のみを修正し、参照元（`history-theme-taxonomy.md`を参照する15箇所、`glossary.md`を参照する箇所）の更新は行っていない。`glossary.md`の該当エントリを直接引用・転記している文書は確認されなかったため、今回の文言修正による参照先の更新は不要である。

### 結論

`history_theme`は、Product・Analytics・Reflection・Journey Timelineが実際に利用する値（`translation_result.history_theme`、`history-theme-taxonomy.md`の定義）と、Knowledge（`shrine-profile-spec.md`）が神社プロフィール属性として扱う値（`Shrine.history_theme`）の、責務が異なる2つの実体を同一語彙で共有している。この構造そのものは実装上の既存事実であり、変更しない。齟齬は`docs/knowledge/glossary.md`の一般定義エントリのみに存在し、「神社の歴史から抽出」という不正確な表現を「相談内容を神社側の意味文脈へ接続した意味テーマ」へ修正した。カテゴリ名（7種）、カテゴリ数、表示名と内部値の対応関係はすべて一致しており、変更していない。

---

## 16. 「復興」到達可能性の監査（2026-07-18）

15節で発見した`history_theme_secondary`の実装（`_resolve_history_theme_secondary`）について、「復興」カテゴリの到達経路・設計根拠・Product taxonomyとの整合を監査した。実装変更は行っていない。

### 確認した実装・テスト

- `backend/temples/services/consultation_interpreter.py`（`STATE_KEYWORDS` / `DIRECTION_BY_STATE` / `build_direction_profile`）
- `backend/temples/services/meaning_translation.py`（`HISTORY_THEME_BY_DIRECTION` / `HISTORY_THEME_BY_NEED` / `HISTORY_THEME_BY_DECISION` / `_resolve_history_theme` / `_resolve_history_theme_secondary` / `REFLECTION_QUESTION_BY_HISTORY_THEME`）
- `backend/temples/services/recommendation_score_components.py`（`calculate_history_score`）
- `backend/temples/services/concierge_chat_ranking.py`（`SCORE_V3_HISTORY_THEME_BY_AXIS` / `resolve_score_v3_history_signal`）
- `backend/temples/services/journey_timeline.py` / `reflection_state_change.py`（`history_theme_secondary`の非利用を確認）
- `docs/product/history-theme-taxonomy.md` / `docs/product/meaning-translation-mapping.md`
- `docs/audit/history-theme-contract-audit.md`（既存監査。Status: Reference、`meaning-translation-mapping.md`へ統合済みと明記）
- `backend/temples/tests/services/test_meaning_translation.py`（9件）/ `test_recommendation_score_components.py`（8件のうちhistory_score関連4件）/ `test_consultation_interpreter.py`（6件）
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`（`復興`の表示コピー定義箇所）

### HISTORY_THEME_BY_STATE（実装上の名称：`DIRECTION_BY_STATE`）

チェックリスト上の呼称`HISTORY_THEME_BY_STATE`に対応する実装は存在しない。実際の名称は`consultation_interpreter.py`の`DIRECTION_BY_STATE`であり、`state → (direction, (theme_primary, theme_secondary))`を返す。

```text
tired            → (rest,       (静寂, 復興))
anxious          → (stabilize,  (守り, 静寂))
uncertain        → (review,     (静寂, 再出発))
stuck            → (reset,      (再出発, 静寂))
ready_to_change  → (challenge,  (再出発, 勝負))
```

`state`自体は`STATE_KEYWORDS`（5状態: tired / anxious / uncertain / stuck / ready_to_change）のキーワード一致でのみ決定される。相談文中に該当キーワードがなければ`primary_state`は`None`となり、`DIRECTION_BY_STATE`から何も解決されない。

### HISTORY_THEME_BY_NEED / HISTORY_THEME_BY_DECISION

いずれも`meaning_translation.py`で確認済み（値: mental/rest→静寂、career→再出発、money→守り、love→縁、study→学び、courage→勝負／career_decision・rest_or_action→再出発、relationship_decision→縁、money_decision→守り）。**両辞書とも値に「復興」を一切含まない。**

### history_theme_secondaryの生成条件

`_resolve_history_theme_secondary(direction_profile)`は、`direction_profile.themes`が2要素以上のリストである場合のみ、`themes[1]`を返す。`themes`は`DIRECTION_BY_STATE`の該当stateにおけるタプル2番目の値であり、`direction`（primary解決に使う値）とは独立したデータソースである。

### 「復興」がprimaryへ到達する経路

**存在しない。** `HISTORY_THEME_BY_DIRECTION` / `HISTORY_THEME_BY_NEED` / `HISTORY_THEME_BY_DECISION`の3辞書の値を全て突き合わせても、値として「復興」を持つエントリは0件。`_resolve_history_theme`はこの3辞書のみを参照するため、`translation_result.history_theme`（primary）が「復興」になることはない。

「復興」が到達可能なのは以下の2経路のみ。

1. `Shrine.history_theme`（Stored、編集者による神社プロフィールへの手動タグ付け。`seed_history_theme.py`で確認）
2. `translation_result.history_theme_secondary`（Runtime、`state=tired`の場合のみ。5状態中「復興」を`themes`に含むのは`tired`のみ）

### 「復興」がsecondaryのみとなる設計根拠

`meaning_translation.py:143-158`の`_resolve_history_theme_secondary`docstringに明文化されている。要約すると、`consultation_interpreter.build_direction_profile()`は`DIRECTION_BY_STATE`経由で`themes`（primary/secondaryの2値）を既に計算していたが、`_resolve_history_theme()`のprimary解決は`HISTORY_THEME_BY_DIRECTION`（`direction`から引く単一値）のみを参照するため、`themes[1]`相当の値（「復興」等）は計算されているにもかかわらず捨てられていた。この設計根拠は`docs/audit/history-theme-contract-audit.md`（P0、対応済み）に詳細な経緯がある。同監査により`_resolve_history_theme_secondary()`が追加され、`calculate_history_score()`が主値一致(1.0)／副次一致(0.6)／不一致(0.35)／欠損(0.0)の4段階評価へ拡張された。Score v3は全関数が「shadow observation only」であり、本番のRecommendation Rankingには影響しない。

**この設計自体（secondaryを追加してScore v3で弱いシグナルとして利用する）は意図的かつ妥当である。** 「復興」をprimaryとして生成する経路を追加しなかったこと自体は、当時の監査（`history-theme-contract-audit.md`）のスコープが「計算済みだが捨てられていた値の救済」に限定されていたためであり、明確な悪意や見落としではない。

### Backendテストで「復興」の期待値を確認

- `test_meaning_translation.py::test_translate_meaning_resolves_secondary_history_theme_from_direction_profile_themes`: `themes=["静寂","復興"]`から`history_theme_secondary == "復興"`を検証（実行確認済み・PASSED）
- `test_recommendation_score_components.py::test_calculate_history_score_returns_mid_score_when_secondary_theme_matches`: `translation_result.history_theme_secondary="復興"`、`candidate_profile.history_theme="復興"`で`0.6`を検証（実行確認済み・PASSED）
- 「復興」がprimaryとなるケースを検証するテストは存在しない（到達経路が存在しないため、そもそも書けない）

### Product taxonomyとの整合

`history-theme-taxonomy.md`は7カテゴリ（守り/静寂/再出発/復興/勝負/学び/縁）を対等な正本カテゴリとして定義しており、この点はBackendの`Shrine.history_theme`（7カテゴリ全てが有効なタグ値）および`SCORE_V3_HISTORY_THEME_BY_AXIS`（全10 axisで7カテゴリ全てに重みを持つ）と整合している。

**新規発見（本監査で新たに確認）**: `docs/product/meaning-translation-mapping.md`「相談状態からhistory_themeへの変換」節（148-179行目）は、16通りの相談状態例（「不安が強い」「疲れている」「落ち込んでいる」「自信がない」等）とprimary/secondary history_themeの対応表を提示しており、うち2行（「落ち込んでいる」→復興/静寂、「自信がない」→復興/学び）は「復興」をprimaryとする例として記載されている。しかし実装（`STATE_KEYWORDS` / `DIRECTION_BY_STATE`）が認識する状態は5種類のみ（tired/anxious/uncertain/stuck/ready_to_change）であり、「落ち込んでいる」「自信がない」に対応する状態キーワードは存在しない。したがって、この文書が例示する16パターンのうち実装で到達可能なのは最大5パターンのみであり、「復興」をprimaryとする2パターンはいずれも現行実装では生成不可能である。

`docs/audit/history-theme-contract-audit.md`のP2指摘（「主テーマ・補助テーマの併存を許容すると書いているが単一値のみ返す」）は既に解消済みだが、本監査で発見した「16例中5例のみ実装済み、復興のprimary例2件は未実装」というギャップは、同監査でもmeaning-translation-mapping.mdの改訂作業でも指摘されていない新規事項である。

### Analytics・Reflection・Journeyでsecondaryが利用されるか

**利用されていない。** `history_theme_secondary`の参照箇所は`meaning_translation.py`（生成元）と`recommendation_score_components.py`（Score v3 shadow observationでの消費）のみ。`docs/analytics/`配下、`journey_timeline.py`、`reflection_state_change.py`、Frontend（`apps/web` / `apps/mobile`）のいずれにも`history_theme_secondary`への参照はない。Analytics payload・Reflection・Journey Timelineが扱う`historyTheme`は常にprimary値のみである。

### 現行挙動が仕様か欠損かを判定する

2層に分けて判定する。

1. **「復興」がsecondaryのみで到達し、primaryへは到達しないこと自体**: **仕様（意図的）と判定する。** `history-theme-contract-audit.md`のP0対応として明文化・テスト済みであり、Score v3のみが消費する設計として妥当である。追加対応は不要。
2. **`meaning-translation-mapping.md`が16例を提示しながら実装は5状態のみ対応していること（「復興」をprimaryとする2例が未実装であること）**: **記述が実装より先行した状態（ドキュメント上の欠損）と判定する。** `docs/audit/history-theme-contract-audit.md`のP2「実装より記述が先行」パターンと同種の問題であり、悪意や設計ミスではなく、ドキュメントが将来拡張の例示を含んでいたためと考えられる。ただし現状は「実装済み」と誤読される書き方になっており、読者（開発者・後続監査）が誤って「16状態すべて実装済み」と判断するリスクがある。

### 後続実装PR案

本PRでは実装・ドキュメント本文のいずれも変更しない。以下は将来のPR候補として記録する。

**候補A: `STATE_KEYWORDS` / `DIRECTION_BY_STATE`の拡張**

- `meaning-translation-mapping.md`が例示する「落ち込んでいる」「自信がない」等の状態キーワードを`STATE_KEYWORDS`へ追加し、対応する`DIRECTION_BY_STATE`エントリ（例: `depressed`等の新state → 復興をprimaryとするdirection）を設計する
- 「復興」をprimaryとして生成する初めての経路となるため、`REFLECTION_QUESTION_BY_HISTORY_THEME`に「復興」の質問文を追加する必要がある（現状欠落）
- 影響範囲: `consultation_interpreter.py`、`meaning_translation.py`、関連テスト。Recommendation RankingへのScore v3反映状況次第では、shadow observationの数値傾向にも影響しうる

**候補B: `meaning-translation-mapping.md`の記述精度向上**

- 「相談状態からhistory_themeへの変換」表に、実装済み5状態と例示のみ（未実装）の11状態を区別する注記を追加する
- 実装コード変更は不要なため、候補Aより低リスクかつ即着手可能

優先順位の判断・実施は本PRの範囲外とし、母艦へ差し戻す。
