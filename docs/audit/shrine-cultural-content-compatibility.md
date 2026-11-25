# 文化解説 Story / History / Highlights と Knowledge Base の整合性監査

> Status: Audit / Historical（仕様の正本・実装許可ではない）
> 監査日: 2026-11-21 JST
> 対象: `origin/develop` commit `eabea1da312bc254cdf49bc2d388f5ec0a0cc2e1`
> Branch: `audit/shrine-cultural-content-compatibility`

## 1. 判定と監査境界

**別の実装PRへの勧告: STOP。** Story / History の材料を保存・公開する基盤は存在する。しかし、3部構成への分類規則、Highlightsの対象と歴史との対応、欠落時・disputed時の表示契約が未確定である。既存契約は非disputed Factの同一 `history_type` による表示整理のみを許可しており、3部構成への再分類をその許可から導くことはできない。先に母艦判断と小さな仕様追記を別PRで行う。

**GOにできる範囲:** 本監査のレビュー、および既存スキーマ・エンドポイントを変えない仕様追記案の検討。文化情報をPublic Detailの読み取り表示として追加することは技術的には可能と推論するが、これは実装着手の承認でも、全神社で3部構成が成立する証明でもない。

ラベルは以下の意味で使用する。

- **確認済み:** 対象commitのコード・テスト・文書に直接存在する構造／記述。
- **推論:** その構造から可能と考えられる利用方法。現行仕様や実装済み挙動とは区別する。
- **不明:** 本番データ・外部Source内容・母艦判断等を確認していない事項。

ソース、モデル、migration、serializer、API、prompt、推薦、テスト、データ、Google Sheetsは変更していない。唯一の成果物は本ファイル。元の作業ディレクトリには既存変更があったため、`/private/tmp/jinja-cultural-audit` の独立worktreeで監査した。元の変更は本PRへ含めない。

`docs/audit/README.md` の「更新ルール」は新audit全件のindex追加を要求していない。したがってindex更新の例外は不要であり、indexも変更しない。対象worktreeには適用対象の `AGENTS.md` はなかった。ルートの `architecture.md` / `roadmap.md` はなく、実在する正本は `docs/core/architecture.md` / `docs/core/roadmap.md`。

## 2. 調査した正本と責務

| 実在パス・行 | 監査上の意味 |
| --- | --- |
| `README.md:31`, `:65`, `:350` | Detailは神社理解、Conciergeは個人との意味接続。Web中心、Mobile新規開発保留。developへPR、CI green後のマージ |
| `docs/core/architecture.md:18`, `:49` | Backendが推薦・業務判定の正本、Detailは由緒・祭神等の表示 |
| `docs/core/roadmap.md:93` | 実装完了・Coverageに関する未着手記述（§7の乖離参照） |
| `docs/knowledge/README.md:15` | 正本一覧、Stored→Meaningの責務委譲、正本更新順序 |
| `docs/knowledge/shrine-profile-spec.md:148`, `:253`, `:345` | Stored / Derived / Runtime / Governance、FactとMeaning、出典要否 |
| `docs/knowledge/shrine-data-guide.md:55`, `:220`, `:279`, `:648` | 入力品質とeligibilityの分離、Actionの実在根拠、未確定の保存・運用事項 |
| `docs/knowledge/glossary.md:37`, `:67` | `history_theme` / `culture_translation` / `place_context` とReadinessの語義 |
| `docs/knowledge/shrine-knowledge-contract.md:302`, `:403`, `:653`, `:699`, `:836` | 歴史種別、Source、disputed、Presentation Grouping、分類・確認・confidenceの独立性 |
| `docs/knowledge/fact-source-citation-contract.md:19`, `:60`, `:88` | 文書単位SourceとFact単位locatorの分離。runtimeに接続しない追加provenance |
| `docs/knowledge/recommendation-eligibility-contract.md:7` | usable Deity OR History。Score、F5 qualificationとは別 |
| `docs/core/recommendation-readiness.md:1`, `:27` | Governance観測。Score、候補除外、Fact利用判定を担わない |
| `docs/core/recommendation-reason-contract.md:40`, `:66`, `:90` | Fact / Interpretation / Action。history_themeは一次事実でない。伝承は必ずhedge |
| `docs/core/recommendation-architecture.md:190`, `:435`, `:500` | 推薦パイプラインと現在境界。一部旧As-Is／将来記述が併存 |
| `docs/product/meaning-translation-mapping.md:30`, `:155` | 相談解釈からhistory_themeへ接続。文化史年表の抽出仕様ではない |
| `docs/product/shrine-detail-layer.md:15`, `:30`, `:69` | Public / Context / Personalの分離。由緒・基本説明はPremium化しない |
| `docs/product/action_suggestion_v4.md:22`, `:48`, `:70` | Actionは選定・順位を決めない。I/Oの意味、fallback・具体schemaは実装へ委譲 |
| `docs/product/shrine-detail-meaning-layer.md:107`, `:137`; `docs/product/shrine-detail-v3-design.md:190` | 歴史・土地性／象徴を個人向け解釈とどう分けるかの関連契約 |

## 3. 実装inventory（パス・symbol・行）

以下のパスはすべて対象commitで確認した。行番号はこのcommitに対するもの。

| 層 | 実装と関係 |
| --- | --- |
| 基本神社 | `backend/temples/models.py:239` `Shrine`。`address`、緯度経度、`sajin`、`description`、`history_theme`、M2M `goriyaku_tags`、OneToOne `place_ref`。`sajin` / `description` はlegacy自由文 |
| Source | 同 `:449` `ShrineKnowledgeSource`。source_type、title、publisher、url、bibliography、accessed_at、verified_at、verification_status、confidence、language、note |
| 祭神 | 同 `:497` `ShrineDeity`。FK Shrine（`deities`）、表示名／正規名／role／sort_order、M2M sources、確認状態・confidence・verified_at・note |
| 集合祭神 | 同 `:544` `ShrineDeityCollective`、`:646` `ShrineDeityCollectiveMembership`。集合ラベル・人数表現と個々の祭神への関係を分離。単独祭神名へflattenしない |
| 歴史 | 同 `:749` `ShrineHistory`。FK Shrine（`histories`）、history_type、title、content、period_text、event_date、sort_order、M2M sources、確認metadata |
| Fact内出典位置 | 同 `:802` `ShrineFactSourceCitation`。Source FKとHistoryまたはDeityの一方、locator_text。exactly-one／非空／一意制約。`:887` saveでfull_clean |
| 別系統Source Fact | 同 `:892` `ShrineSourceFact`。公式祈祷・現行案内の原文表現用で、一般的な建築・歴史モデルではない。Detail serializerには未接続。Channel Bでの利用を文化解説へ転用しない |
| 意味根拠foundation | 同 `:954` `HistoryThemeAssignment`、`:1141` `EvidenceLink`。canonical_key・taxonomy_version・producer・mechanism・assigned_at、Stored Factへのedge。既存 `Shrine.history_theme` のread pathとは独立 |
| 特徴語 | `backend/temples/models_feature_words_en.py:18` `ShrineFeatureWordEn`。FK Shrine、word_id、語彙version、evidence_quote、source_url、source_type、checked_on、note。Google Sheetsのリポジトリ内コピーを入力とする別系統 |
| legacy神名辞書 | `backend/temples/models.py:1611` `Deity`。名前・alias・wiki_url。`ShrineDeity` のSource-backed祭神行と同一モデルではない |
| 基盤migration | `backend/temples/migrations/0093_shrine_knowledge_model_foundation.py:17` Source / History / Deity作成。NoGIS側は `backend/temples/migrations_nogis/0008_actionevent_conciergehistory_and_more.py:180`, `:199`, `:234`。同じ番号・同じlineageではない |
| 追加migration | 通常側 `0084_shrine_history_theme_shrine_idx_shrine_history_theme.py`、`0102_history_theme_assignment_foundation.py`、`0104_evidence_link_foundation.py`、`0116_shrine_deity_collective_foundation.py`、`0117_shrine_deity_collective_membership_foundation.py`、`0118_shrine_deity_collective_count_relation_constraint.py`、`0119_collective_runtime_activation_foundation.py`、`0121_shrine_fact_source_citation.py:15`、`0122_shrine_feature_word_en.py:14`（いずれも `backend/temples/migrations/`） |
| NoGISの対応追加 | `backend/temples/migrations_nogis/0007_shrine_history_theme_shrine_idx_shrine_history_theme.py`、`0009_historythemeassignment.py`、`0011_evidencelink.py`、`0015_shrine_deity_collective_foundation.py`、`0016_shrine_deity_collective_membership_foundation.py`、`0017_shrine_deity_collective_count_relation_constraint.py`、`0018_collective_runtime_activation_foundation.py`、`0020_shrine_fact_source_citation.py`、`0021_shrine_feature_word_en.py`。GIS適用・migration実行は今回未検証 |
| 入力・管理 | `backend/temples/services/knowledge_seed.py:1097` `parse_seed`、`:646` `_parse_citations`（schema 1.3）、`backend/temples/management/commands/import_shrine_knowledge.py` / `export_shrine_knowledge.py`。`backend/temples/admin.py:280`, `:296`, `:315` Source / Deity / History Admin。今回import・更新は未実行 |
| Serializer | `backend/temples/api/serializers/shrine.py:28` Source、`:59` Deity、`:85` History、`:133` Collective、`:199` List、`:228` Detail、`:318` Write |
| Detail View | `backend/temples/api/views/shrine.py:289` serializer選択、`:302` queryset、`:333` Source prefetch、`:362` retrieveでadmitted collective contextを供給 |
| API route | `backend/temples/api/urls.py:121` list、`:122` detail、`:123` data alias、`:124` meaning、`:125` feature-words-en。新規endpoint不要という可能性はこの既存経路に限定 |
| Gate / selector | `backend/temples/services/evidence_gate.py:53` `decide_fact_usability`、`:152` `decide_detail_display_state`。`backend/temples/services/shrine_knowledge_selector.py:36`, `:88` 祭神／歴史の推薦用取得 |
| 推薦・Action | `backend/temples/services/concierge_chat_candidates.py:51` `is_recommendation_eligible`、`backend/temples/services/concierge_chat.py:475` candidate profile、`backend/temples/services/recommendation_reason_v4.py:212` Fact構成、`backend/temples/services/action_suggestion_builder.py` 行動生成 |
| 意味出力 | `backend/temples/services/shrine_culture_translation.py:15`, `:38` dataclassと手編辞書、`backend/temples/services/shrine_meaning_composer.py:639`, `:838` 生成とsource、`backend/temples/api/views/shrine_meaning.py:29` View、`backend/temples/services/shrine_meaning_access.py:38` premium項目削除 |
| 観測 | `backend/temples/services/knowledge_coverage_report.py:1`、`backend/temples/management/commands/knowledge_coverage_report.py:130` read-only集計。既定のDB行集合はcanonical identity集合ではない（service `:46`）。今回DB Coverageは取得しない |

## 4. Story / History / Highlights: field → Source → API 対応

3部構成は本監査で評価する提案であり、既存canonical分類ではない。

| 対象 | 保存されている材料 | Sourceと確認 | 既存API出力／限界 | 評価 |
| --- | --- | --- | --- | --- |
| Story: 祭神 | `ShrineDeity.display_name`, canonical_name, role。集合はCollective / Membership | FactごとのM2M sources、確認状態・confidence | `GET /api/shrines/{id}/` の `deities[]`。集合は `deity_collectives[]`、admission済みのみ。集合serializerはsourcesを出さない（`shrine.py:113`） | **確認済み:** 名称・役割は扱える。神話上の人物関係／神話本文／祭神と特定Historyのedgeはない |
| Story: 起源伝承 | History `official_origin`, `tradition`（創建を含む場合も人手分類が必要）、title/content | Fact→sources→Source.url。FactのlocatorはCitationに別保存 | `histories[].history_type/title/content/period_text/event_date/sources`。Contentはそのまま。伝承の本文文体をDetailで自動修正しない | **推論:** 型を残した個別列挙は可能。公式由緒は伝承混在の可能性があり、史実へ自動昇格不可 |
| History: 年代付き出来事 | History `founding`, `historical_event`、event_date（確定日）、period_text（幅・推定年代） | 上と同じ | 同 `histories[]`。モデル順はsort_order, idで、日付順ではない（models.py:787）。推薦selectorはevent_dateを返さない（selector `:106`） | **確認済み:** 正確な日付と期間表現の併存可。年だけを架空の月日に補完不可。年表UI／重複時代整理は現行契約外 |
| History: 地域文脈 | History `regional_context` のcontent。住所は `Shrine.address` | HistoryのSourceは追跡可。住所には同じSource relationがない | 詳細 `histories[]` と `address/location/latitude/longitude`。推薦 `fact.place_context` は住所由来（concierge_chat.py:527） | **確認済み:** 地域史はHistoryへ格納可能。住所だけで土地の歴史・地形・文化を証明できない |
| Highlights: 建築・文化的特徴 | History本文へ既存6分類の範囲で記述可能。別系統に `ShrineFeatureWordEn` の特徴語・引用 | HistoryはM2M Source。特徴語はsource_url / checked_on（verification_statusやFact confidenceは持たない） | `/feature-words-en/` のitemsはword_id, label_en, category, slot, source_url, checked_on。引用本文・note・source_typeは返さない | **部分互換:** 既存特徴語の表示は可能。建物名・建築年代・文化財指定・現在観察可能性を個別対象として返す構造ではない |
| Highlights: 歴史との結び付き | 本文内で説明可能でも、建物／特徴→History IDの専用relationがない | 各FactのSourceは独立。共通Sourceや同じShrineであることは関係の証拠にならない | 型付きの歴史リンクは出力されない。特徴語endpointはword_id重複を1件化し、複数根拠を全件公開しない（view `:51`） | **不明:** 実データに必要な説明が揃うか。自動関連付けは不可 |

### 概念項目の物理対応（取り違え防止）

| 概念 | storage → 公開／推薦出力 |
| --- | --- |
| `deity` | 詳細では `Shrine.deities` → `deities[]`。推薦ではusable selector → `knowledge_deities` → profile.deity → ReasonV4.fact.deity。推薦profileはKnowledge不在時legacy sajinへfallbackするが、Detailはfallbackしない（concierge_chat.py:517、serializer:238） |
| `shrine_history` | 詳細では `histories[]`。推薦はusable Historyの最小dictから主となる1件を選び、ReasonV4.fact.shrine_historyへ。全History・日付・出典の一覧APIではない |
| `place_context` | Shrineの同名fieldはない。詳細のaddress/locationと、推薦の住所alias。地域史本文は別のregional_context。地理的住所をSource-backed文化解説へ再解釈しない |
| `shrine_feature` | Shrineの同名field／一般的な特徴一覧serializerはない。Action Layerの概念。英語特徴語モデルは関連する部分基盤だが同じ契約ではない |
| `source_url` | Knowledgeは `ShrineKnowledgeSource.url` → nested sources[].url。Shrine本体の同名fieldではない。英語特徴語だけは物理field `source_url` → items[].source_url |
| `verified_at` | Source・Deity・History・Collective等に保存。Knowledge serializersの公開fieldには含まれない。APIで返るのはverification_statusとconfidence。英語特徴語のchecked_onは別のDateFieldであり、同じレビュー状態を意味しない |
| Source内位置・offline provenance | bibliography/accessed_at/language/noteとCitation.locator_textは保存可能だがDetail API非公開。URLが空の正当なoffline Sourceはtitle/publisher/type等のみ公開され、API単体では書誌・頁・観察noteへ到達できない |
| `history_theme` | `Shrine.history_theme` は保存済み意味タグ。Detail serializerに含まれず、meaning.source.historyTheme（composer:849）や推薦fact等へ。HistoryThemeAssignment/EvidenceLinkが存在してもlegacyタグの公開経路と自動連結しない |
| `culture_translation` | Shrine DB fieldではなく手編Python辞書（対象ID 17,14）→ composerのshrineMeaning/historyContext/Action等の解釈素材。Source ID、verified_at、Fact edgeを辞書が持たない。ReasonV4 `_build_fact` は一次Factから除外（`:224`）。文化史の根拠APIとして転用しない |

## 5. 事実・伝承・解釈・観察とreview state

**確認済み:** Historyの6型は `official_origin / founding / historical_event / tradition / regional_context / editorial_summary`。伝承と編集要約を別行で保持できる。`official_origin` は公式Sourceだから史実という意味ではない。`founding` も史実確定の保証ではない（Knowledge契約 `:836`）。異なる由来・説は行を分け、本文を合成しない。

FactとSourceは独立に `draft / unverified / source_confirmed / reviewed / disputed / outdated / rejected` を保持し、confidenceは `low / medium / high / 空`。`clean()` はsource_confirmed/reviewed時のverified_atを要求する（models.py:436）。通常のDeity/History/Sourceのsaveで常にfull_cleanされるわけではないため、モデル検証・Admin・importerの役割とDB制約を同一視しない。GateはstatusとSource relationのみを読み、日付・URL到達性・Source本文の一致・history_type・confidenceを独立に再検証しない。

DetailはFactがsource_confirmed/reviewed、かつready Sourceが1件以上ならfull。disputedかつready Sourceありなら個別表示。その他は非公開。Source配列はready Sourceに限る。Recommendationはdisputedを常に除外する。Fact confidenceはReasonの表現強度へ接続するが、Detail表示可否はconfidenceを参照しない。low confidenceでもDetailに返ることと、Recommendation Reasonで抑制されることは矛盾ではなく経路差である（evidence_gate.py:53, :152、recommendation_reason_v4.py:234）。

**観察:** Source.source_type=`user_observation` は存在し、Source.noteやbibliographyでoffline記録を識別できる（Knowledge契約 `:515`）。ただしHistoryにはvisitor_note型や観察対象・観察日時の専用fieldがなく、Sourceのaccessed_at/verified_atを「観察日」と読み替えられない。APIはsource_typeを返すので出典種別は判別できるが、観察note自体は返さない。Visit.note（serializer `shrine.py:311`）や個人Reflectionを、そのまま公開・確認済み文化Factとみなす契約もない。

**不足:** Fact単位review状態はあるが、3部構成全体の編集完了、翻訳レビュー、対象建物の現在の観察可否、再確認期限、承認担当者、反対Sourceとの明示的supports/contradicts関係はこのAPI契約にない。Source内locatorはあるが、それ自体は賛否・矛盾のedgeではない。未確認・非公開・未登録はAPI上の空配列だけでは区別できない。これを「伝承なし」「歴史なし」「見どころなし」と断定してはならない。

## 6. Recommendation / Actionとの共存

**確認済みの分離:** `is_recommendation_eligible` はusable Deity OR Historyの有無のみ。ReadinessはGovernance。ReasonV4のFact / Interpretation / ActionはStory / History / Highlightsとは別の3分割。`culture_translation` はprimary ranking reasonから除外（concierge_chat_ranking.py:851）。Actionのgrounding/fallbackは既存builderが担う。文化セクションを埋めるためにこれらを変更する必要性は確認されない。

**推論として可能な最小境界:** 既存の詳細GET（必要なら既存英語特徴語GET）を消費し、公開された個別Factのid・型・本文・出典・statusを保持する読み取り表示なら、Score / candidate eligibility / Readiness / endpoint / Action schemaを変えずに共存できる。ただし「3部すべてに必ず本文を生成する」要求は満たせない。Presentation Grouping契約の許可を3つの新カテゴリへ無断拡張しない。

以下は別物であり自動流用しない。

- `meaning.generated.historyContext` / deitySymbolContextは生成された意味文であり、`histories[]` / `deities[]` の代わりではない。composerはlegacyや手編辞書を読む。
- Meaning APIはplanでhistoryContext等を削る（shrine_meaning_access.py:38）。Publicな由緒がPremium契約に変わったことを意味しない。文化本文をこの生成枠に載せるかは母艦判断が必要。
- 英語特徴語の既存 `Story` categoryは `history_culture` slotへ、Sight/Craft/Feelは `scenery_experience` へ振り分ける（view:31）。提案されたStory/History/Highlightsと同名・同義ではない。既存slotやSheetsの語彙を今回再定義しない。
- 文化Factを後日追加・reviewすると、同じ既存Gateでも候補適格性が変わり得る。表示のみのPRと、Knowledge投入PRは別の評価を要する。本監査ではデータを書かない。

## 7. 文書と実装・契約間の乖離

| ID | 根拠と食い違い | 監査上の扱い |
| --- | --- | --- |
| D1 | profile-spec:257はhistory_themeを「由緒から抽出」、glossary:47は「歴史文章から自動抽出される値ではない」。mapping文書は相談状態からの意味変換も定義。実装は保存タグ・相談変換・手編辞書の複数経路 | 単純な歴史要約として扱う契約はない。Shrine固定タグと相談runtime themeの語義を別PRで明確化する候補。ここで勝手に片方を採用しない |
| D2 | glossary:69はReadinessを「推薦可能かどうかを示す品質段階」、readiness正本:1, :27はGovernanceのみ、旧LevelはSuperseded。実装のcandidate gateはconcierge_chat_candidates.py:51 | glossaryの整合追記候補。文化セクション有無から新Readinessを作らない |
| D3 | data-guide:654はSourceの本体／別モデル保存を未決定と記載。一方models.py:449, :512, :773とmigration0093で別モデル＋M2Mが実在 | deity/historyについては解決済み構造がある。住所等すべてのprovenanceが解決済みとは言わない。未決定の対象を限定する追記候補 |
| D4 | roadmap:97-98はPilot拡大／105件rollout／Coverage集計を未着手とする。しかし26個のKnowledge seed JSON、batchテスト、knowledge_coverage_report command/service/testsが存在 | 実装・artifactの存在は確認済み。本番投入件数・全Coverage・rollout完了は未確認。古い数値を現在値へ転用しない。roadmapは今回変更しない |
| D5 | profile-spec:11-13の100%/0%/93%は旧観測（後段の時点注記あり）。住所はmodels.py:245でblank許容、APIで出典も確認日も付かない | 「常に信頼できる」「現在100%」とは確認できない。最新DB測定なしに更新・流用不可 |
| D6 | Knowledge契約:150, :152の旧As-Isは `shrine_public.py` / ShrinePublicSerializerへの経路とsajin公開不可を記載。現在そのファイル・symbolはbackendに見つからず、meaning composer:847-849はsource.sajin/descriptionを出力 | 時点記録を現行全API経路へ一般化できない。Detail serializerがlegacyを返さない事実は現在も維持 |
| D7 | recommendation-architecture:500はEvidence Gateを将来未実装とする旧節。一方同文書:190およびevidence_gate.py:53, :152、Knowledge契約のCurrent追記では実装済み | 旧設計と現在境界の併記。今回黙って解消せず、現在コードの関数を根拠に判定 |
| D8 | Public由緒の非Premium契約（shrine-detail-layer:69）に対し、MeaningのhistoryContextはPremium shapingされる | 現時点で同じデータの誤課金とまでは断定しない。生成解釈と公開Factの用途差がある。3部構成をMeaning枠へ載せる判断は保留 |
| D9 | profileのsource_url / verified_at / shrine_feature / place_contextは概念項目。Shrine本体に同名fieldなし。一方英語特徴語にはsource_urlあり、Knowledge URLはurl | 概念→物理→公開field対応が不足。名前一致で存在／公開を推定しない。§4の対応表を仕様へ最小限参照する候補 |

## 8. テストinventoryと保証範囲

テストの存在・assert内容の静的確認と、今回の実行成功を分離する。以下を変更していない。

| テストパス（`backend/temples/tests/` 起点）・symbol行 | 確認対象 |
| --- | --- |
| `test_models_shrine_knowledge.py:92`, `:170`, `:192`, `:253` | verified_at検証、確定日と推定期間の分離、Source共有。`:276`以降は集合祭神・membership制約 |
| `serializers/test_shrine_knowledge_serializers.py:49`, `:81`, `:121`, `:136`, `:155` | full/disputed、legacyへfallbackしない、Source nesting、ListにKnowledgeなし |
| `api/test_shrine_detail_knowledge_api.py:62`, `:113`, `:177`, `:234`, `:317` | API filtering、N+1、Sourceなし非公開、disputed、複数行独立列挙 |
| `api/test_shrine_detail_deity_collectives_api.py`; `serializers/test_shrine_deity_collective_serializers.py` | 集合祭神の別表現・admission経路 |
| `services/test_shrine_knowledge_selector.py`; `services/test_evidence_gate.py`; `services/test_evidence_gate_detail_display_state.py:20` | 推薦selectorとstatus / SourceのGate、Detailとの差 |
| `test_fact_source_citation.py:375`, `:481`, `:673`, `:708` | migration論理一致、validate-only/dry-run、citation追加でeligibility不変、Gateでcitation未参照 |
| `services/test_shared_recommendation_eligibility.py`; `services/test_culture_translation_primary_attribution_guard.py:66` | candidate gate分離、文化解釈でrank/primary authorityを変えない |
| `services/test_action_suggestion_grounding_alignment.py:51`, `:89`, `:106` | 行動の根拠・generic safe fallback・culture interpretation provenance |
| `api/test_shrine_feature_words_en.py`; `services/test_shrine_feature_matches_en.py` | 英語特徴語APIとmatch観測 |
| `test_knowledge_coverage_report_command.py`; `services/test_knowledge_coverage_report.py` | 既存Coverage観測ツール |

**不足:** この3部構成専用の完全性・分類・空状態・重複・建物と歴史の関連付け・offline出典・翻訳レビュー・disputedの配置を検証するテスト契約は確認できない。既存serializerテストは3部構成の文化的妥当性や本番データ充足を保証しない。

## 9. 最小の潜在的追加（今回未実施）

優先するのはschema拡張ではなく、母艦判断後の短い仕様差分である。

1. **Glossary:** Story / History / Highlightsの表示上の意味を定義し、既存英語category Story、Fact / Interpretation / Actionと区別。D1/D2の語義競合を明示的に裁定する。
2. **Profile / Knowledge契約:** §4の概念→物理→APIの対応を参照できる追記。既存canonical history_typeから新表示見出しへの対応、複数該当・非該当・disputed・editorial_summaryの処遇を決める。既存Groupingの制約を変えるなら明示する。
3. **Data guide:** 伝承と史実の文体、年代不明、対象建物の実在と歴史関係を確認する根拠、offline Source識別、観察と確認日の違い、未確認項目の扱いを短く追記。verified_atの公開を要求するかは別判断とする。
4. **Detail Product仕様:** Public情報としての配置、未入力時の省略／準備中、Fact単位Source/status保持、Meaning解釈との分離、既存APIだけで提供する限定範囲を定める。英語特徴語の語彙／Sheets／slot契約はそのまま参照する。
5. **別実装PRに必要な受入条件案:** 契約が決まった範囲だけを表示。本文や出典を合成しない、伝承を史実化しない、disputedは独立表示、空を不存在へ翻訳しない、Score/Action/eligibility/snapshot/endpoints不変を既存回帰と表示テストで確認する。

建物オブジェクトや専用relation、追加field、追加endpointは今回提案の必須解としない。既存出力で要件を限定できなければ、その要求をSTOP条件として母艦へ戻す。Source確認日・locatorの公開は現在のAPIでは満たせないため、要求する場合は「既存APIのみ」という境界とのトレードオフを別途扱う。

Knowledge READMEの更新順はprofile→knowledge contract→data guide→glossary、glossary冒頭は新概念を各仕様追加前に定義する指示がある。追加順序自体にも解釈差があるため、後続仕様PRでまとめて整合を取り、今回一方へ無断統一しない。

## 10. 未解決のMother Ship判断・不明事項

- 3部は常設・必須か、材料がある神社だけの任意表示か。Highlightsに英語特徴語のみを許すか、建物名と歴史リンクまで要求するか。
- Storyにofficial_origin/founding/traditionをどう分けるか。Historyとの重複を許すか。既存canonical型以外の見出しを許す契約範囲。
- disputedの独立列挙、editorial_summary、user_observation、low confidenceの説明・ラベル・配置。
- Public文化FactとMeaning / Premium解釈の境界、画面順、言語・翻訳reviewと空状態。Web中心の現行範囲で扱うか。
- 公開Sourceに必要な粒度はURLまでか、verified_at・bibliography・locator・全根拠が必要か。現在APIとの差を許容するか。
- 入力・レビュー責任者、再確認周期、競合Sourceの裁定担当と承認手順。
- 本番DBの最新件数、対象神社ごとの利用可能なFact、出典の到達性と内容一致、現在の建物の観察可否、翻訳品質は**不明**。既存seedの存在は本番投入の証明ではない。Google Sheetsは参照も変更もしていない。

GOへの再判定には上記の必要判断、対象を限定した最新read-onlyデータQA、専用表示の受入仕様、および隔離テストDBでの回帰成功が必要。今回の監査結果から実装・データ投入・本番公開を承認しない。

## 11. 検証記録

### Gitと対象snapshot

実行ディレクトリは最初のstatus/fetchのみ元workspace、以降は独立worktree。

```sh
git status --short --branch
git fetch origin develop
git worktree add -b audit/shrine-cultural-content-compatibility /private/tmp/jinja-cultural-audit origin/develop
git rev-parse HEAD
```

元workspaceには `eas.json` 等の既存変更があった。最初のfetchは `.git/FETCH_HEAD: Operation not permitted` で終了255。必要なGit権限の再実行は成功し、上記対象commitへworktree作成済み。source treeは変更していない。

### テスト実行（未成功・環境ブロック）

```sh
PYTHONDONTWRITEBYTECODE=1 USE_SQLITE=0 USE_GIS=0 DISABLE_GIS_FOR_TESTS=1 DATABASE_URL=postgres://audit:audit@127.0.0.1:1/cultural_audit DB_NAME=cultural_audit DJANGO_SECRET_KEY=audit-only-not-deployed /Users/morietsu/Desktop/jinja_app/.venv/bin/python -m pytest -c backend/pytest.ini -p no:cacheprovider --override-ini=addopts='' backend/temples/tests/services/test_evidence_gate.py backend/temples/tests/services/test_evidence_gate_detail_display_state.py backend/temples/tests/services/test_action_suggestion_grounding_alignment.py backend/temples/tests/services/test_culture_translation_primary_attribution_guard.py
```

終了3。pytest-rerunfailuresのローカルsocket bindでPermissionError。上の同一commandへ `-p no:rerunfailures` を追加して再実行すると、41件collect、41件setup error、終了1。隔離した到達不能なテスト用DB接続先でPostgreSQLへ接続できなかった。実データDBへの意図しない接続を避けるためこの接続先を明示した。`backend/temples/tests/conftest.py:120`, `:274` のautouse fixtureはdbに依存する。settings.py:153はpytestのSQLite実行を禁止しているため、SQLiteへの置換やfixture改変で成功扱いにはしない。モデル／serializer／APIのDB実行、PostGIS migration、最新DB Coverageは未検証。DB書き込み・migration適用には至っていない。

### 非実行型の構文・artifact検査

以下をそのまま実行（Python import、Django起動、DBアクセスなし）。

```sh
python3 - <<'PY'
import ast, json
from pathlib import Path
paths = [Path('backend/temples/models.py'),Path('backend/temples/models_feature_words_en.py')]
paths += list(Path('backend/temples/api/serializers').glob('shrine*.py'))
paths += list(Path('backend/temples/api/views').glob('shrine*.py'))
paths += [Path('backend/temples/services') / x for x in ['evidence_gate.py','shrine_knowledge_selector.py','concierge_chat_candidates.py','recommendation_reason_v4.py','action_suggestion_builder.py','shrine_culture_translation.py','shrine_meaning_composer.py','knowledge_seed.py']]
for p in paths: ast.parse(p.read_text(), filename=str(p))
seeds=sorted(Path('backend/temples/data/knowledge_seeds').glob('*.json'))
for p in seeds: json.loads(p.read_text())
print(f'AST parsed: {len(paths)} Python files; JSON decoded: {len(seeds)} knowledge seed files; no imports or DB access')
p=Path('backend/temples/models.py'); tree=ast.parse(p.read_text()); shrine=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Shrine')
fields={t.id for n in shrine.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
for x in ['sajin','description','history_theme','place_context','shrine_feature','source_url','verified_at','culture_translation']:
 print(f'Shrine declared {x}: {x in fields}')
PY
```

成功: Python 19ファイルをAST parse、Knowledge seed JSON 26ファイルをdecode。同名Shrine fieldはsajin/description/history_themeのみTrue、残り5項目はFalse。これはschema構造／JSON構文検査であり、seed semantic validation・import結果・本番Coverageの測定ではない。

### 差分制約

参照検証では本書から正規表現で抽出した39件の明示的なpath:lineについて、ファイル実在・行番号範囲を確認し、エラー0件。`git diff --check` は成功。`git status --short` は本ファイルのuntracked追加のみ。ステージ後の `git diff --cached --check` と `git diff --cached --name-only`、commit後の `git diff --name-only origin/develop...HEAD` / `git status --short` も提出時に確認し、結果をPRへ記録する。許可対象は本ファイル1件のみ。
