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
| `recommendation-v4-interpreter-contract.md` | Active | Active維持・整理対象 | Consultation Interpreterの出力項目と意味責務 | 実装ファイル名、Expected Keys、KPI、現行関数名が混在 | Fieldの意味契約を残し、物理構造・関数名・KPIは実装またはAnalyticsへ委譲 |
| `home-hero-final-wireframe.md` | Reference | Reference維持 | Home Heroの画面構成とUI補足 | Active文書と画面責務が一部重複 | UI補足に限定し、体験判断は`concierge-first-final-spec.md`へ委譲 |
| `concierge-entry-final-wireframe.md` | Reference | Reference維持 | Concierge Entryの画面構成とUI補足 | Active文書と画面責務が一部重複 | UI構成、表示要素、CTA補足に限定 |
| `concierge-filter-area.md` | Reference | Reference維持・整理対象 | Filterの画面構成と補助条件UI | Frontend / Backend責務とデータ接続詳細が一部混在 | UI責務を残し、解釈・判定はBackend正本へ委譲 |
| `need-mode-ui-flow.md` | Reference | Reference維持 | Need ModeのUI導線と表示責務 | `need_tags`、`matched_need_tags`、Backend責務がActive文書と重複 | UI表示・導線補足に限定し、Mode責務は`concierge-modes.md`へ委譲 |
| `compat-mode-ui-flow.md` | Reference | Reference維持 | Compat ModeのUI導線と補助情報表示 | 占術、方位、推薦接続の記述がMeaning / Direction文書と重複 | UI補足に限定し、Mode責務とMeaning変換へ委譲 |
| `concierge-card-architecture.md` | Reference | Reference維持 | Concierge結果画面のCard Tree、Props、Renderer、Section Routing | PropsやRendererなど物理Frontend構造が中心で、実装との差分が生じやすい | 設計背景として維持し、現行構造はFrontend実装・テストを正本とする |
| `card-visibility-renderer-split.md` | Reference | 統合候補 | Card VisibilityとRenderer責務分離 | `concierge-card-architecture.md`とCard表示・Renderer責務が重複 | 独自情報を比較し、統合後にArchiveまたはDelete候補とする |
| `concierge-first.md` | Archive | Archive維持 | Concierge First初期思想 | 現行仕様ではなく、正本への委譲も明確 | 現状維持 |
| `concierge-first-wireframe.md` | Archive | Archive維持 | Concierge First初期ワイヤーフレーム | 現行UI正本への委譲が明確 | 現状維持 |

### Meaning・Recommendation

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `history-theme-taxonomy.md` | Active | Knowledge移管候補・Active維持 | `history_theme`7カテゴリの名称、定義、行動テーマおよび概念境界 | カテゴリ定義、相談例、ご利益との関係はProduct体験仕様よりKnowledgeの用語・意味分類責務に近い。Product / Backend / Analyticsの責務説明も混在する | Knowledge責務監査で移動先を確定し、Productには体験上の利用箇所のみ残す。移管完了まではActiveとして扱う |
| `meaning-translation-mapping.md` | Active | Active維持・大幅整理対象 | 相談、意味変換、神社文脈、Action、Visit、Reflectionを接続するProduct上の変換関係 | Runtime実装状況、Backendファイル名、Score計算、Snapshot物理構造、Analytics指標、神社データ管理方針が混在する | 体験上の変換関係と各機能への接続を残す。システム構造はCore、カテゴリ定義と神社付与基準はKnowledge、Scoreと実装詳細はBackend、Event・KPIはAnalyticsへ委譲 |
| `shrine-detail-layer.md` | Active | Active維持 | 神社詳細画面のPublic / Context / Personal Layerと画面責務 | 大きな責務混在は確認されないが、Meaning Layer補足文書およびv3設計と情報レイヤの説明が重複する | 神社詳細の情報レイヤ境界を管理する正本として維持し、詳細な画面構成や実装順序は補足文書・実装へ委譲 |
| `shrine-detail-meaning-layer.md` | Reference | 統合候補 | 神社詳細におけるMeaning情報の表示順、主役情報、補強情報および表現原則 | `shrine-detail-layer.md`の情報レイヤ、`shrine-detail-v3-design.md`の画面構造、Knowledgeのコピー原則と重複する。既存コード対応、今後の実装方針、TODOも混在する | 独自のMeaning表示原則を`shrine-detail-layer.md`またはKnowledge文書へ統合し、統合後はArchiveまたはDelete候補として再判定 |
| `shrine-detail-v3-design.md` | Active | Reference化候補・整理対象 | Shrine Detail v3のUX再設計、画面構成および実装時の設計背景 | Current State、Proposed構造、将来のCardVisibilityPolicy、Analytics Event・KPI、Premium導線、実装境界が混在する。現行仕様の正本というより実装フェーズの設計記録に近い | 現行の画面責務は`shrine-detail-layer.md`へ統合し、v3移行時の設計背景としてReferenceへ変更する。AnalyticsはAnalytics文書へ委譲 |
| `direction-ranking-design.md` | Reference | Reference維持 | 方角・吉方位を推薦補助軸として扱う将来設計 | 本文のDirection Mode、Score構造および九星補助は現行実装と一致せず、参照元も監査文書のみ | 将来設計であることを明示したReferenceとして維持する。現行Ranking判断には使用せず、Backend実装・テストを正本とする |
| `visit-style-taxonomy.md` | Reference | Reference維持・境界整理対象 | Concierge Filterで使用する参拝スタイルの表示分類、内部タグおよびUI上の扱い | `extraCondition`変換、Backendへの接続、推薦加点ルールなど物理処理が混在する。一方でUI分類として独立した価値はある | UI表示分類と内部値対応を残し、自然文変換、スコア、重み、API契約はBackend実装へ委譲 |

### Action・Visit・Reflection

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `action_suggestion_v4.md` | Active | Active維持・Analytics委譲対象 | Recommendation Reasonから次に取りやすい行動を生成するInput / Outputと生成ルール | `action_suggestion_reflection_preview_view`、`actionPromptType`などAnalytics Event・Payload契約が混在する | Actionの意味、出力項目、生成原則をProductに残し、正確なEvent名・Payload・計測語彙はAnalyticsへ委譲 |
| `visit-reflection-flow.md` | Active | Active維持・大幅整理対象 | 参拝完了からReflection保存、次回相談までを接続する体験とVisit / Reflectionの意味責務 | Event名、TypeScript Payload型、Django Model全文、Index、採用Field、Mobile送信状況、PostHog集計、実装ファイル名が混在する | 体験フロー、Visit / Reflectionの意味責務、Free / Premium境界を残す。Event・Payload・FunnelはAnalytics、Model・Field・Index・APIは実装とテストへ委譲 |
| `reflection-timeline-design.md` | Active | Reference化候補・統合対象 | 相談、参拝、振り返り、再相談を時間軸で接続する長期体験思想 | 写真、御朱印、検索、感情推移、行動記録、Premium分析、KPIなど未実装または将来構想が現行仕様として混在する。Journey Timeline実装との名称・責務差もある | 現行のTimeline体験責務をJourney Timeline正本へ統合し、本書は長期構想・設計思想を残すReferenceへ変更する |
| `journey-timeline-design.md` | Reference | Reference維持・統合候補 | EventとStateを分離したJourney Timelineの情報設計と移行方針 | 現行実装に近いが内容が簡略で、正確なEvent構造・表示・Visit / Reflection接続はBackend・Mobile実装とテストに委譲されている。Reflection Timelineと責務が重複する | Reflection Timelineの現行利用可能な情報を統合し、Journey Timelineの補足設計として維持する。物理仕様は実装とテストを正本とする |
| `reflection-funnel-dashboard.md` | Reference | Analytics移管候補・Reference維持 | VisitからReflection保存までのFunnel、KPIおよびPostHog Dashboard設計 | 内容の中心がEvent、KPI、Breakdown、Dashboard、観測期間およびSuccess Criteriaであり、ProductよりAnalytics責務に属する | `docs/analytics/`へ移管または同等文書へ統合する。移管完了まではReferenceとして維持し、Product README上の分類を後続PRで更新する |

### Premium・Billing

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `premium-experience.md` | Active | Active維持・責務明確化対象 | Free / Premiumの体験価値、画面別の体験差、保存・履歴・比較の原則 | `pricing.md`および`monetization-flow-design.md`とPremium価値の説明が一部重複する。現行仕様と将来の比較・分析機能も一部混在する | Premium体験価値の正本として維持し、料金・Billing判定・収益導線・Analyticsを各専用文書へ委譲する |
| `pricing.md` | Active | Reference化候補・統合候補 | Premiumの支払対象、Free / Premium境界および価格表現の原則 | 具体的な料金・請求周期・プランを管理しておらず、内容の多くが`premium-experience.md`と重複する。参照元もAudit文書に限られる | 独自の価格表現原則を`premium-experience.md`へ統合し、具体的な料金体系が確定するまではReferenceへ変更することを後続PRで判断する |
| `billing-paywall.md` | Active | Active維持・大幅整理対象 | Billing状態、Premium優先、Free回数制限およびPaywall表示の判定契約 | API Endpoint、Response Field、JavaScript判定コード、未実装の共通Hook、テスト要件が混在する。Markdownコードブロック構造も再確認が必要 | 利用可否と判定原則をProductに残し、正確なField・Endpoint・実装コード・テスト要件はBackend / Frontend実装とテストへ委譲する |
| `monetization-flow-design.md` | Reference | Reference維持・Analytics委譲対象 | Premium提示タイミング、CTA方針、収益導線思想およびRetention設計背景 | Event名、Funnel、Revenue KPI、Context Property、未実装機能、将来拡張が混在する。現行仕様と将来構想の境界が曖昧 | 収益導線の設計思想をReferenceとして維持する。Event・Payload・KPI・FunnelはAnalyticsへ委譲し、未実装案は将来構想として明示する |

### Explore・投稿

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `explore-integration-design.md` | Reference | Reference維持 | Recommendationから神社一覧・比較・位置確認・詳細へ接続するExploreの役割と画面責務 | 大きな責務混在は確認されない。現行仕様の詳細ではなく、Exploreを検索・比較・位置確認へ限定する補足設計として整理されている | Referenceとして維持する。Recommendation、Meaning、神社詳細およびシステム構造は各正本へ委譲し、Exploreの役割または画面責務が変更された場合のみ更新する |
| `shrine-submission-flow.md` | Active | Active維持・大幅整理対象 | 検索で見つからない神社を投稿し、審査中状態を表示して公開マスターへ接続するユーザー体験 | URL、API Endpoint、HTTP Status、Serializer・View・Service責務、BFF実装方針、重複判定ロジック、実データ検証結果、未確認事項、将来拡張、神社データ利用条件が混在する | 投稿入口、投稿後復帰、審査中表示、公開までの体験責務をProductに残す。重複判定・Endpoint・Status・物理実装はBackend実装とテスト、神社プロフィール・タグ・推薦利用条件はKnowledge、確認済み・未確認・実データ検証結果はAuditへ委譲する |

### UI・補足設計

| 文書 | 現在分類 | 監査判定 | 主責務 | 確認した問題 | 後続対応 |
|---|---|---|---|---|---|
| `README.md` | Statusなし | Active付与 | Product文書群の入口、読む順番、分類および各文書の役割案内 | 文書自体にStatus表記がなく、監査結果確定後の分類変更が未反映である | Product文書の入口としてActiveを付与し、監査確定後に読む順番、正本、Reference、Archiveおよび役割説明を更新する |
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
- `kami-musubi-experience-design.md`
- `meaning-translation-mapping.md`
- `premium-experience.md`
- `pricing.md`
- `recommendation-v4-interpreter-contract.md`
- `reflection-timeline-design.md`
- `shrine-detail-layer.md`
- `shrine-detail-v3-design.md`
- `shrine-submission-flow.md`
- `visit-reflection-flow.md`

### Reference

- `card-visibility-renderer-split.md`
- `compat-mode-ui-flow.md`
- `concierge-card-architecture.md`
- `concierge-entry-final-wireframe.md`
- `concierge-filter-area.md`
- `direction-ranking-design.md`
- `explore-integration-design.md`
- `home-hero-final-wireframe.md`
- `journey-timeline-design.md`
- `mobile-bottom-navigation.md`
- `monetization-flow-design.md`
- `need-mode-ui-flow.md`
- `product-document-audit.md`
- `reflection-funnel-dashboard.md`
- `shrine-detail-meaning-layer.md`
- `visit-style-taxonomy.md`

### Archive

- `concierge-first.md`
- `concierge-first-wireframe.md`

### 統合候補

- `card-visibility-renderer-split.md`
  - `concierge-card-architecture.md`への統合候補
- `shrine-detail-meaning-layer.md`
  - `shrine-detail-layer.md`またはKnowledge文書への統合候補
- `reflection-timeline-design.md`
  - Journey Timeline側への現行責務統合後、Reference化候補
- `journey-timeline-design.md`
  - Reflection Timelineとの整理・統合候補
- `pricing.md`
  - `premium-experience.md`への独自原則統合後、Reference化候補
- `history-theme-taxonomy.md`
  - Knowledge移管候補
- `reflection-funnel-dashboard.md`
  - Analytics移管候補

### Delete候補

現時点ではなし。

統合候補文書は、独自情報の移管と参照元更新を確認した後に、ArchiveまたはDeleteを再判定する。

### 判断保留

- `history-theme-taxonomy.md`のKnowledge移管先
- `reflection-timeline-design.md`と`journey-timeline-design.md`の正本名称
- `pricing.md`を独立文書として残すか
- `card-visibility-renderer-split.md`統合後のArchive / Delete
- `shrine-detail-meaning-layer.md`統合後のArchive / Delete
---

## 10. docs/product/README.mdとの差分

監査完了後に以下を記録する。

- 現在分類と監査判定が一致する文書
- Status変更が必要な文書
- README上の役割説明を修正する文書
- 読む順番を変更する文書
- ArchiveまたはDelete候補
- 統合後にREADMEから除外する文書

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

- [ ] 35文書すべてに監査判定がある
- [x] Active / Reference / Archive / Delete / 統合 / 保留の基準が明文化されている
- [x] Productと他領域の境界が整理されている
- [x] 後続PRの変更範囲が分離されている
- [ ] READMEとの差分が明示されている
- [ ] Markdownコードブロックが閉じている
- [ ] Markdown参照切れがない
- [ ] `git diff --check`が成功する
- [ ] 意図しないファイル変更が含まれていない

---

## 13. 結論

Product直下のMarkdown文書35件について、現行分類、主責務、重複、委譲先および後続対応を確認した。

監査時点の最終分類は以下である。

| 分類 | 件数 |
|---|---:|
| Active | 17 |
| Reference | 16 |
| Archive | 2 |
| 合計 | 35 |

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
