> **Status: Audit / Historical（Shrine Detail Premium Presentation Boundary Audit、時点記録）**
>
> 本ドキュメントは、KAMI MUSUBI Web版のShrine Detailについて、既に存在する機能・情報をFree/Premiumユーザーへ「どう見せるか」「どう伝えるか」「どこまで渡すか」をMother Shipが判断できるEvidenceを整理した記録である。`docs/audit/test-release-premium-boundary-audit.md`（PR #2617）・`docs/audit/premium-personalization-deep-search-audit.md`（PR #2619）・`docs/audit/shrine-detail-premium-information-architecture-audit.md`（PR #2622、Shrine Detail IA Audit）の続編であり、いずれも上書きしない。
>
> 対象コミット: `origin/develop` HEAD `20d3dcc8`（PR #2619〜#2621マージ後）。作業branch: `claude/kami-musubi-premium-audit-8roagp`（PR #2622がまだ未マージのため、同branchへ本監査文書を追加commitする形で継続。branch/PRの扱いはSection「PR運用に関する補足」参照）。
>
> **本監査はProduct Decisionを行わない。** Decision A-1a/A-1b/A-1cのいずれも選択せず、`Codex Recommendation: NONE`と明記する。UX/User Value/Conversionについてコードのみから判断できない内容はFACTとして書かない。
>
> **分類ルール**: FACT（コード/テスト/契約から直接確認）・INFERENCE（複数FACTからの推論）・UNRESOLVED（追加調査またはMother Ship判断が必要）。既存Audit文書と現行コードが矛盾する場合は`AUDIT_STALE`として明記し、現行実装を優先する。
>
> Web版のみを対象とする（Mobile対象外）。UI/Component/Route/Copy/Premium CTA/Recommendation Ranking/Score/Signal Extraction/InterpretationProfile/Recommendation Reason/Premium Gate/Backend API/Serializer/Authentication/Billing/Subscription/Quota/Favorite/Reflection/Record/Analytics/DB/Schema/Migration/Test/Mobileのいずれも変更していない。発見した既存バグも修正していない。

# KAMI MUSUBI — Shrine Detail Premium Presentation Boundary Audit

## Executive Summary

1. **前提（Decision A = HYBRID）は動かさない**。Freeで十分なRecommendation体験を提供し、Premiumは「回数」ではなく「より深く理解すること」を主価値とする。本監査はこの前提の下で、現行UIが実際に何を・どこまで・どう伝えているかを整理する。
2. **Free ValueはFULL_VALUE〜PARTIAL_VALUEの混在状態にある（FACT）**。Concierge主導線の推薦自体（相談→3件の候補→基本Reason→Shrine Detail Fact section→Route）はFreeで完全に完結する（`test-release-premium-boundary-audit.md`で既に確認済みのCOMPLETE判定を再確認）。一方、Shrine Detail内の①〜④ブロック（`personal_meaning`カード）はPremium限定のTEASERであり、その中身は前回Audit（`shrine-detail-premium-information-architecture-audit.md`）が発見した通り、経路によって個人化されていたりされていなかったりする。
3. **Basic ReasonとDeep Reasonの境界は、現行コード上「単一Signal起因」対「複数Signal合成」という形で実質的に既に存在する（FACT+INFERENCE）**。`score_need`（単一need_tag一致）はBasic Reason相当、`score_v3`の合成（`behavior_signal`+`profile_signal`+`direction_signal`+`history_signal`+`distance_signal`の加重和）はDeep Reason相当の構造を持つが、**`score_v3`はshadow計算のみで実際のRanking（`score_total_ranked`）には使われていない**（`premium-personalization-deep-search-audit.md`で確認済みFACTの再掲・再確認）。Deep Reasonを「見せる」ための材料はBackend内に断片的に存在するが、Premium/Free差として意図的に構成されたものではない。
4. **Personal RecordのうちVisit/Reflectionは、実際にRecommendationへ再利用されている（FACT、新規確認）**——`behavior_signal`（`calculate_shrine_behavior_signal_breakdown`）は`visit_signal`+`reflection_signal`を合成し、weight 0.1で`score_total_ranked_base`へ加算される。**Favoriteは一切Rankingに再利用されていない**（`concierge_chat_ranking.py`に"favorite"の参照が0件）。この差はPremium Personalizationの「Personal Record」要件を検討する上で重要な既存の技術的非対称性である。
5. **Premium Presentation Patternとして、現行UIは実質的にPattern B（TEASER_GATE）とPattern E（SEPARATE_EXPERIENCE、CTA遷移のみ）の萌芽形を併せ持つが、いずれも部分的。** Pattern A（HARD_GATE、完全非表示）・Pattern C（VALUE_PREVIEW、価値の種類だけ説明）・Pattern D（INLINE_EXPANSION、同一セクション内でFree→Premiumへ地続きに拡張）は現行コードに存在しない（NOT_IMPLEMENTED）。
6. **Premium Communication Surfaceは、Concierge結果画面とShrine Detail内の複数箇所に分散して存在するが、一貫した「Premiumで何が得られるか」の説明（Value Preview）は存在しない**——CTAは主に「アップグレードボタン」のみで、価値の中身を事前に説明する機構はコード上確認できない（NOT_IMPLEMENTED、Phase 9参照）。
7. Free Value Boundary候補（Boundary A/B/C/D）とPremium Presentation Pattern（5案）を技術的Evidenceのみで比較し（Phase 7-8）、Mother Ship Decision Input（Decision A-1a/A-1b/A-1c）を整理した（Phase 12）。**いずれも選択していない。**

---

## Phase 0 — Baseline

| 確認項目 | 結果 | Evidence |
| --- | --- | --- |
| 最新develop | Y（`20d3dcc8`、PR #2619〜#2621マージ後） | `git log --oneline -5 origin/develop` |
| PR #2619マージ済み | Y | 同上（`3b4b3734`としてsquash merge） |
| current branch | `claude/kami-musubi-premium-audit-8roagp` | `git branch --show-current` |
| commit SHA（作業ブランチ分岐元） | `607de72b`（PR #2620時点、直後に本監査シリーズのPR #2622を同branchへ追加commit） | `git log` |
| working tree | clean（本監査開始時点） | `git status` |
| unrelated changes | なし | 同上 |
| duplicate Audit/PR | 重複ファイル名なし（`docs/audit/shrine-detail-premium-presentation-boundary-audit.md`は新規） | ローカルglob確認 |

**PR運用に関する補足（FACT、透明性のため明記）**: 本監査の直前に作成した`docs/audit/shrine-detail-premium-information-architecture-audit.md`（PR #2622）はまだ`develop`へマージされていない。セッションの運用規則上、作業branchは1つに固定されており（`claude/kami-musubi-premium-audit-8roagp`）、そのPRが未マージの間に新しいbranchへ分岐するとPR #2622の履歴を破壊するリスクがあるため、本監査は同一branchへ追加commitする形を取った。PR自体は、本監査完了後にPR #2622のタイトル・本文を2つの監査文書を含む内容へ更新するか、あるいはGitHubの制約上別branchでの新規PRが必要な場合はその時点で判断する。**この運用上の判断はProduct Decisionではなく、git実務上の制約に基づくものである。**

---

## Phase 1 — Current Section Inventory

`docs/audit/shrine-detail-premium-information-architecture-audit.md`（PR #2622）のPhase 3 Section Inventoryで確定済みの内容を、本監査の目的（表示のされ方）に合わせて再構成する。**新規のコード照合は行わず、直前の監査ですでに検証済みのFACTをそのまま引用する**（矛盾がないため`AUDIT_STALE`該当なし）。

| Section | Runtime表示 | Entry Path | Data Source | Personalized | Login依存 | Premium依存 | Evidence |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| Hero title/address | Y | 全経路共通 | shrine素フィールド | N | N | N | `ShrineDetailArticle.tsx:651,653` |
| Hero意味コピー | Y | 全経路 | `buildHeroMeaningCopy()` | 条件付き（concierge限定で真の個人化） | N | Y | `buildShrineDetailModel.ts:1254-1297` |
| 方位補足コピー | Y（存在時） | ctx非依存 | `shrineMeaningPayloadV2.generated.directionSupportCopy` | N | N | N | `buildShrineDetailModel.ts:1701` |
| 参拝後state-delta（「前回との違い」） | Y（visited/reflected時） | ctx=concierge限定で非null | `page.tsx:352-364 compareState()` | Y | Y | **Y（真のgate）** | `ShrineDetailArticle.tsx:288-375,459-461` |
| ①〜④ブロック（`personal_meaning`） | Y（Premium時） | **多数派経路ではctx非依存に表示**（前回監査AUDIT_STALE訂正済み） | `buildMeaningSectionsFromPayloadV2()`（ctx非依存）or 真の個人化経路（ctx=concierge+構造化thread限定） | **条件付き**（多数派は非個人化コピー） | N | Y（teaser/visible） | `buildShrineDetailModel.ts:84-173,1625-1694` |
| ⑤補足（ご利益・象徴・相性） | Y（常時） | 相性タグのみ相談依存 | `buildSupplementSection()` | HYBRID | N | N（実効的にゲートされない） | `buildShrineDetailModel.ts:1072-1101` |
| 御祭神/由緒・歴史（Fact section） | Y | 全経路 | `buildShrineFactSection(shrine)` | N | N | N（明示的に対象外） | `ShrineDetailArticle.tsx:687-689` |
| Deep Dive Q&A | Y | 全経路 | `deep_dive_answer.py` | N | N | N | `deep_dive.py:76-108` |
| Save/お気に入り | Y | 全経路 | `useFavorite()` | N | Y | N | `ShrineSaveButton.tsx:44-48,92-98` |
| 参拝記録 | Y | 全経路 | `addVisit()` | N | Y | N | `ShrineDetailArticle.tsx:748-788` |
| 参拝後の振り返り | Y（訪問記録後） | 全経路 | `createShrineReflection()` | Y | Y | N | `ShrineReflectionPrompt.tsx:19,54-67` |
| 御朱印（公開ギャラリー） | **N（dead code）** | N/A | `PublicGoshuinSection` | N/A | N/A | N/A | `ShrineDetailArticle.tsx:388,414,795-806`（前回監査で確認済みAUDIT_STALE） |
| 経路案内 | Y（lat/lng存在時） | 全経路 | `gmapsDirUrl()` | N | N | N | `page.tsx:268` |
| Recommendation meta | **N（dead code）** | N/A | 計算のみ | N/A | N/A | N/A | `RecommendationMetaSection.tsx:14`（import元0件） |

---

## Phase 2 — Section Responsibility分類

| Section | Responsibility | Current Behavior | Evidence |
| --- | --- | --- | --- |
| Hero title/address, Hero画像, 御祭神/由緒・歴史, ⑤ご利益/象徴, Deep Dive Q&A | **SHRINE_FACT** | すべて神社固有データのみに基づき、consultation/user入力を一切受け取らない | `ShrineDetailArticle.tsx:687-689`; `deep_dive.py:88-97`（request契約に`shrine_id`+`question`のみ） |
| ②ブロック（`ShrineReasonSection`, kind:"reason"） | **BASIC_RECOMMENDATION**（ただし専用UIはdead code） | `matched_need_tags`/`_primary_reason_label`という単一〜少数Signal起因のreasonテンプレートを表示する構造を持つが、専用の描画面（`RecommendationMetaSection`）は未使用 | `concierge_chat_ranking.py:1865-1948`（Backend側reason生成）; `RecommendationMetaSection.tsx:14` |
| ①〜④ブロック（真の個人化経路、`recommendation_reason_v4_detail`由来） | **DEEP_RECOMMENDATION（到達時のみ）** | `ctx==="concierge"`+構造化thread時、相談要約・複数要素の統合的なnarrativeを提供 | `buildShrineDetailModel.ts:1625-1694` |
| ①〜④ブロック（payloadV2経路、多数派） | **SHRINE_FACT寄りのコンテンツをPERSONAL_MEANINGラベルで提示（ミスマッチ、前回監査で確認済み）** | `compose_shrine_meaning_payload()`はshrine行のみを引数に取り、consultation/user情報を受け取らない | `shrine_meaning_composer.py:858-868` |
| Hero意味コピー | **HYBRID**（PERSONAL_MEANINGの骨格にSHRINE_FACTのfallback） | concierge優先、失敗時は`HERO_MEANING_BY_TAG`（history-theme由来の汎用コピー）へfallback | `buildShrineDetailModel.ts:1254-1297` |
| 参拝後state-delta | **PERSONAL_MEANING** | ユーザー自身の2スレッド間比較 | `page.tsx:352-364` |
| ⑤補足の「相性・補助情報」タグ | **PERSONAL_MEANING（部分）** | `conciergeBreakdown`由来（ctx=concierge限定で非空） | `buildShrineDetailModel.ts:1429-1432` |
| 経路案内、参拝記録ボタン | **VISIT** | Route/Access/現地行動 | `page.tsx:268`; `ShrineDetailArticle.tsx:748-788` |
| Save/お気に入り、振り返り、（dead: 御朱印ギャラリー） | **RECORD** | Favorite/Reflection/Visit Historyの記録行為 | `ShrineSaveButton.tsx`; `ShrineReflectionPrompt.tsx` |
| 参拝後お礼コピー | **UNKNOWN寄りのINCIDENTAL**（静的文言、明確などの分類にも強く該当しない） | `actionState`が`visited`/`reflected`の時のみ表示される固定文字列 | `ShrineDetailArticle.tsx:664-672` |

---

## Phase 3 — Current Value Delivery Audit

「FreeでもRecommendation Engineを十分体験できる」というDecision Aの前提と、現行表示の整合性を確認する。**「十分」のProduct基準は決めない**——現在何が実際に渡っているかのみを記録する。

| 対象 | 分類 | Evidence |
| --- | --- | --- |
| Concierge相談入力・自由文・誕生日・goriyaku・参拝条件 | **FULL_VALUE** | 入力自体に一切の制限・差別化がない（`test-release-premium-boundary-audit.md`で既に確認済み） |
| Recommendation実行（1日あたり） | **PARTIAL_VALUE（回数の意味で）** | 匿名3回/Free 5回（環境変数既定）/Premium無制限。機能・品質の差ではなく回数のみ | `test-release-premium-boundary-audit.md` Section 3（既存FACT） |
| Recommendation候補件数（主導線） | **FULL_VALUE（Free/Premium同一）** | 3件固定、差なし | 同上 |
| Recommendation Reason（基本文） | **FULL_VALUE** | `shrine_meaning`/`consultation_summary`はFreeでも全文表示（"partial"ラベルだが実装上切り詰めなし） | 同上（Concierge結果画面側） |
| Reasonの「今の自分への問い」（action_meaning、Concierge結果画面） | **TEASER** | Freeはteaserテキストへ差し替え | 同上 |
| Shrine Detail: Fact section（御祭神/由緒等） | **FULL_VALUE** | Plan問わず全文 | `ShrineDetailArticle.tsx:687-689` |
| Shrine Detail: ①〜④ブロック（`personal_meaning`） | **TEASER（Free/匿名）／PREMIUM（表示されるが中身が経路依存、Phase 2参照）** | `personalMeaningVisibility` | `ShrineDetailArticle.tsx:677-683` |
| Shrine Detail: 参拝後state-delta | **TEASER（Free）／PREMIUM** | `isPremiumActive`直接判定 | `ShrineDetailArticle.tsx:288-375` |
| Shrine Detail: Deep Dive Q&A | **FULL_VALUE** | `AllowAny`、無制限 | `deep_dive.py:76-108` |
| Shrine Detail: Save/参拝記録/振り返り | **LOGIN_REQUIRED**（Premiumではない） | `IsAuthenticated`のみ | `favorites/views.py:16`等 |
| Shrine Detail: Route/経路案内 | **FULL_VALUE** | 無制限 | `page.tsx:268` |
| Shrine Detailの`context_reason`カード | **FULL_VALUE（ただし意図せず、DEAD_POLICYの副作用）** | Free配列に`kind:"reason"`が構造的に入らないため、"partial"ラベルにもかかわらず実質全文が出る | `shrine-detail-premium-information-architecture-audit.md` Phase 4（既存FACT再掲） |

**Decision Aとの整合確認（FACT+INFERENCE）**: Concierge主導線の相談→推薦→基本Reason→Shrine Detail Fact section→Routeという一連の流れは、上表の通りFreeで完全に`FULL_VALUE`または`FULL_VALUE`寄りである。これは「FreeでもRecommendation Engineを十分体験できる」という確定済みDecision Aの前提と**矛盾しない**（INFERENCE：ただし「十分」の評価基準自体はProduct判断であり、本監査はこれを判定しない）。一方、Shrine Detail内のPersonalized/Record系（①〜④、state-delta）はTEASER状態であり、これはDecision Aが定める「PremiumはPersonalization Depthを拡張する」という設計方針とも矛盾しない（FACT: 現状Freeの基本体験を損なわずにPremiumだけ追加要素を持つ構造になっている）。

---

## Phase 4 — Basic Reason / Deep Reason Audit

| Reason要素 | 現行実装 | Free表示 | Premium表示 | Personalization Depth | Ranking依存 | Future候補 | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `score_need`（単一/少数need_tag一致） | 実装済み、Rankingの主要因子 | Y（そのままreasonテンプレートに反映） | Y（差なし） | 低（単一Signal） | **Y（`score_total_ranked`の直接構成要素）** | — | `concierge_chat_ranking.py:1099-1213,1351-1358` |
| `history_theme_candidate_boost` | 実装済み | Y | Y（差なし） | 低〜中 | Y | — | `concierge_chat_ranking.py:1215-1219,1408-1411` |
| `astro_bonus`（西洋占星術element） | 実装済み、Compat Mode時のみ有効 | Y（Compat Mode利用時） | Y（差なし） | 中 | Y | — | `concierge_chat_ranking.py:1226-1239` |
| `profile_signal`（五行マッチ） | 実装済み、max+0.03 | Y | Y（差なし） | 中 | Y | — | `concierge_chat_ranking.py:326-371,1354` |
| `direction_signal`（方位） | 実装済み、max+0.02 | Y（Concierge Reasonの補助カードとして表示。主理由文には混入禁止契約あり） | Y（差なし） | 中 | Y | — | `concierge_chat_ranking.py:291-323,1348-1356`; `recommendation-reason-contract.md:246-256`（方位主理由混入禁止契約） |
| `behavior_signal`（Visit/Reflection履歴由来、weight 0.1） | 実装済み | Y（履歴があれば誰でも反映、Plan不問） | Y（差なし） | 中（ユーザー自身の過去行動を反映するという意味では個人的だが、Free/Premiumの差ではない） | **Y（`score_total_ranked_base`へ加算）** | — | `concierge_chat_ranking.py:1288-1308` |
| `InterpretationProfile`（8次元の深い解釈） | **実装済みだがdebug-onlyで破棄**（既存Audit`premium-personalization-deep-search-audit.md`のFACT） | N（誰にも表示されない） | N（同左） | 高（未使用） | **N（Rankingに未接続）** | **Y——Deep Reason/Deep Interpretationの最有力候補（既存の休眠信号を接続するだけで実現可能、新規Engine不要）** | `consultation_interpreter.py:260-297`（既存Audit引用、`api_views_concierge.py:340`で破棄） |
| `score_v3`（shadow合成スコア: behavior+profile+direction+history+distance の加重和） | **実装済みだがshadow計算のみ、実Rankingには未使用** | N | N | 高（構造上は複数Signal統合だが未使用） | **N（`score_total_ranked`には反映されない、`SCORE_V3_MODE`環境変数ゲート）** | Y——複数Signal統合というDeep Recommendationの構造的雛形として既に存在 | `concierge_chat_ranking.py:62-146`（既存Audit引用の再確認） |
| `recommendation_reason_v4_detail`（Shrine Detail①〜④の真の個人化経路） | 実装済み、ただし`ctx==="concierge"`+構造化thread限定 | N（そもそもこの経路自体が到達困難） | Y（到達時のみ） | 高 | N/A（Reason生成であり、Ranking自体には影響しない） | 到達経路を拡張すれば既存のDeep Reason UIとして機能しうる | `buildShrineDetailModel.ts:1625-1694`（前回監査の再掲） |
| Multi-intent構造化解析、cross-session文脈 | **NOT_IMPLEMENTED**（既存Audit確認済み、grep 0件） | N/A | N/A | N/A | N/A | Y（ただしNEW_ENGINE_CAPABILITY、実装コスト大） | `premium-personalization-deep-search-audit.md` Phase 4.3（既存FACT） |

**Basic Reason / Deep Reasonの現行境界（INFERENCE）**: 「単一Signal起因のreason」（`score_need`単体）と「複数Signal統合のreason」（`score_v3`, `InterpretationProfile`, `recommendation_reason_v4_detail`）という区別は、Rankingスコアの構造上すでに存在する。しかし**この区別は現状Free/Premiumの境界として設計されたものではなく**、単に「使われている信号（score_needベース）」と「計算されているが未使用/未接続の信号（score_v3, InterpretationProfile）」という実装上の状態の違いに過ぎない。Deep ReasonをPremium差別化として構成する場合、技術的には「既存の休眠信号をPremiumのみ接続する」という最小実装パスが存在する（BACKEND_POLICYレベル、既存Audit確認済み）。

---

## Phase 5 — Personal Meaning Audit

| Personal Meaning Section | Current Free | Current Premium | Backend Gate | Frontend Gate | Entry Path依存 | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Hero意味コピー | 汎用固定文（「今のあなたと静かに重なる神社です。」） | `heroMeaningCopy`（concierge経由時は真の個人化、それ以外は`HERO_MEANING_BY_TAG`という汎用fallback） | **なし** | `isPremiumActive`生boolean三項演算（`cardVisibility.ts`非経由） | Y（真の個人化はconcierge限定） | `ShrineDetailArticle.tsx:650-654`; `buildShrineDetailModel.ts:1254-1297` |
| ①〜④ブロック（`personal_meaning`カード） | `PremiumUpgradePrompt`（teaser時、完全なCTA差し替え） | payloadV2経路（多数派、非個人化神社一般コピー）or 真の個人化経路（concierge+構造化thread限定） | **なし**（`GET /api/shrines/{id}/meaning/`は`AllowAny`で全文無条件返却） | `personalMeaningVisibility`（`getVisibilityForCard`経由、機構自体は正常動作） | **多数派経路は非依存、真の個人化のみconcierge限定** | `ShrineDetailArticle.tsx:456,677-683`; `shrine_meaning.py:10-29` |
| 参拝後state-delta（「前回との違い」） | teaser CTA（`isPremiumActive`が偽の場合強制的にteaser） | 完全なnarrative（2スレッド比較） | なし | 生boolean判定（`isPremiumActive`直接、cardVisibilityの宣言値`hidden`とは別の実装） | Y（`ctx==="concierge"`限定でのみデータが非null） | `ShrineDetailArticle.tsx:288-375,459-461` |
| ⑤補足「相性・補助情報」タグ | 常時全文（Premiumゲートなし） | 差なし | なし | **DEAD_POLICY**（`contextReasonVisibility`が参照されない） | 相性タグ自体がconcierge限定で非空 | `buildShrineDetailModel.ts:1429-1432` |
| Concierge結果画面「今の自分への問い」（action_meaning、参考: Shrine Detail外だがPersonal Meaning系の一種） | teaserテキストへ差し替え | 実際の問いかけ文 | なし | `cardVisibility.ts`経由、正常動作 | N/A（Concierge主導線内、ctx分岐なし） | `test-release-premium-boundary-audit.md` Section 3（既存FACT） |

---

## Phase 6 — Personal Record Audit

| Record Feature | Current State | Login | Premium | Persistent | Recommendation再利用 | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Favorite | bookmark（discovery aid的） | **Y（IsAuthenticated）** | N | Y（DBモデル） | **NOT_CONNECTED**（`concierge_chat_ranking.py`に"favorite"の参照0件、本監査で新規確認） | `ShrineSaveButton.tsx:44-48`; `backend/favorites/views.py:16` |
| Visit（参拝記録） | personal history | **Y** | N | Y | **Y——`behavior_signal`の`visit_signal`成分として実際にRankingへ加算される**（weight 0.1、`score_total_ranked_base`の構成要素） | `concierge_chat_ranking.py:1288-1308` |
| Reflection（振り返り） | reflection | **Y** | N | Y | **Y——`behavior_signal`の`reflection_signal`成分として同様に加算** | `concierge_chat_ranking.py:1288-1308` |
| Previous Comparison（state-delta） | continuity（過去の自分との比較） | Y（訪問記録が前提） | **Y（真のPremium gate）** | N（都度2スレッドを比較計算、専用の永続データではない） | **NOT_CONNECTED**（Rankingへは影響しない、表示専用の比較計算） | `page.tsx:352-364`; `ShrineDetailArticle.tsx:288-375` |
| 御朱印公開ギャラリー | premium personalization inputではない（公開UGC） | N（`AllowAny`） | N | Y | **NOT_CONNECTED**（かつ本番描画自体がdead code、Phase 1参照） | `goshuin_feed.py:9` |
| `Light Behavior Profile`（`calculate_light_behavior_profile_breakdown`） | discovery aid寄り（visit/reflectionを除いた軽量シグナルのみ） | N/A（Backend内部計算） | N | N/A | **Y（既存の`behavior_profile`としてResponseに含まれる、Ranking自体には別途light版が使われる箇所あり）** | `concierge_chat_ranking.py:1336` |

**Personal Recordの技術的非対称性（FACT、Phase 6の中心的発見）**: Visit・Reflectionは実際にRecommendation Rankingへ再利用されている（`behavior_signal`）一方、Favoriteは一切再利用されていない。これは「Personal Recordを活用したPersonalized Recommendation」というHYBRID要件（既存Audit`shrine-detail-premium-information-architecture-audit.md` Phase 6参照）にとって、**Favoriteという最も気軽な記録行為が現状Recommendationの改善に一切寄与していない**、という具体的なギャップである（INFERENCE：この非対称性が意図的な設計判断か実装上の見落としかはコードから判別できない、UNRESOLVED）。

---

## Phase 7 — Premium Presentation Pattern比較

Product Recommendationは行わない。5つのPatternを現行コードとの適合度のみで評価する。

| Dimension | HARD_GATE | TEASER_GATE | VALUE_PREVIEW | INLINE_EXPANSION | SEPARATE_EXPERIENCE |
| --- | --- | --- | --- | --- | --- |
| Existing UI Reuse | MEDIUM（`PremiumUpgradePrompt`は実質HARD_GATE的な「完全非表示+CTA」動作をしている） | **HIGH（`personal_meaning`/`previous_comparison`が既にこの形で機能中）** | NONE（価値の種類を事前説明する機構は現行コードに存在しない） | NONE（同一セクション内でFree部分→Premium部分へ地続きに拡張する実装は未発見） | MEDIUM（`PremiumUpgradePrompt`が`/billing/upgrade`という別Routeへのリンクは持つが、これは汎用アップグレードページであり「ユーザー×神社」の別Personalized Experienceではない） |
| New Component | LOW（既存`PremiumUpgradePrompt`をそのまま使える） | LOW（既存機構をそのまま使える） | HIGH（価値説明用の新規コンポーネントが必要） | HIGH（Free/Premiumをシームレスに繋ぐ新規レイアウトが必要） | HIGH（新規Route/Page一式、既存Audit`shrine-detail-premium-information-architecture-audit.md` Phase 11で詳細評価済み） |
| State Complexity | LOW | LOW | LOW〜MEDIUM | MEDIUM（部分描画の状態管理が必要） | LOW（既存`mypage/history/[tid]`パターン踏襲可能、既存Audit確認済み） |
| Entitlement Need | Y（現状Frontendのみ） | Y（現状Frontendのみ） | N（価値の説明自体はコンテンツを渡さないため、entitlement判定は軽量で済む可能性） | Y（Free/Premium境界をコンテンツ内部に持つため、より精密なentitlement判定が必要になりうる） | Y（新規Routeで最初から組み込み可能） |
| Backend Enforcement | **現状NONE（全Pattern共通の既知ギャップ）** | **現状NONE（同左）** | 該当性低（コンテンツ自体を渡さないため、Enforcementの必要性自体が他Patternより低い可能性——ただしこれはINFERENCE） | **現状NONE、かつ最も実装が複雑になりうる（部分的にどこまでが「Free範囲」かの精密な線引きが必要）** | **現状NONE（新規Viewでの新設が前提、既存Audit確認済み）** |
| Analytics Impact | LOW（既存`premium_preview_click`等をそのまま利用可能） | LOW（既存`card_teaser_view`/`card_partial_view`をそのまま利用可能） | MEDIUM（新規の「価値説明を見た」イベントが必要になりうる） | MEDIUM〜HIGH（部分描画のどこまで見たかを計測する新規設計が必要になりうる） | MEDIUM〜HIGH（既存Audit確認済み、新Routeへのfunnel契約拡張が必要） |
| Routing Impact | NONE | NONE | NONE | NONE | **HIGH**（既存Audit確認済み） |
| Test Impact | LOW（既存テストの延長） | LOW（既存テストの延長） | MEDIUM（新規テストが必要） | MEDIUM〜HIGH（既存の最密結合テストファイルへの影響、既存Audit確認済み） | MEDIUM（新規スイート一式、既存Shrine Detailテストへの影響は小さい、既存Audit確認済み） |
| Current Architecture Fit | **HIGH（`PremiumUpgradePrompt`が既にこの形に近い）** | **HIGH（既に機能中）** | LOW（現行コードに萌芽なし） | LOW（現行コードに萌芽なし） | MEDIUM（既存Audit確認済みPrecedentあり） |

---

## Phase 8 — Free Value Boundary Candidates

「選択肢」でありProduct Decisionではない。

| Boundary | Freeで見えるSection | PremiumになるSection | Login Required | Existing implementation | Required changes | Backend enforcement | Analytics | Technical Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Boundary A**（`SHRINE_FACT`まで） | Hero, Fact section, Deep Dive Q&A, ⑤ご利益/象徴（相性タグ除く） | ①〜④ブロック全体、Hero意味コピーの個人化版、state-delta、⑤の相性タグ | 変更なし（Save/参拝/振り返りは既存通りLogin） | **既にこの境界に近い状態が実質的に存在**（①〜④とstate-deltaは既にPremium、⑤の相性タグのみ実効ゲートなしで漏れている） | ⑤補足の相性タグに対する実際のゲート追加（現状DEAD_POLICY） | 新設が必要（全Boundary共通） | 既存イベントの再利用で概ね対応可能 | LOW（現状に最も近いため変更量最小） |
| **Boundary B**（`SHRINE_FACT + BASIC_RECOMMENDATION`まで） | Boundary Aの内容 + ②ブロック（基本reason、単一Signal起因） | ①③④ブロック（複数Signal統合部分）、state-delta | 変更なし | `RecommendationMetaSection`がdead codeのため、BASIC_RECOMMENDATION専用の表示面を機能させる必要がある | `RecommendationMetaSection`の有効化、またはそれに相当する新規実装 | 新設が必要 | 既存＋新規（BASIC_RECOMMENDATION専用イベント） | MEDIUM（dead codeの復活または代替実装が必要） |
| **Boundary C**（`SHRINE_FACT + BASIC_RECOMMENDATION + VISIT`まで） | Boundary Bの内容 + 経路案内・参拝記録ボタン（表示のみ、記録自体は既存通りLogin） | 同上 | 変更なし | VISIT自体は既にPlan非依存で全公開のため、実質的にBoundary Bと同じ着地になる | Boundary Bと同じ | 新設が必要 | Boundary Bと同じ | Boundary Bと同水準（VISITは既に無ゲートのため追加コストはほぼ無い） |
| **Boundary D**（現行構造上の追加候補: `+ RECORD（Favorite/Visit/Reflectionの記録行為自体）`） | Boundary Cの内容 + Favorite/Visit/Reflection**記録行為** | ①③④・state-delta・⑤相性タグ（Boundary Aと同一） | 変更なし（記録行為自体は既にLogin Requiredであり、これをPremiumへ格上げしない場合の境界） | **これも実質的に現状そのまま**（RECORDはPremiumではなくLogin Requiredとして既に実装されている） | なし（現状維持） | 新設が必要（Personal Meaning部分のみ） | 既存の再利用で対応可能 | LOWEST（実質的に現状と同一） |

**Boundary間の実質的な差の小ささについて（INFERENCE）**: Boundary A・C・Dは、現行実装の実態（RECORD/VISITが既にLogin RequiredのままPremium化されていない）を踏まえると、実質的にほぼ同じ着地点になる。真に技術的な選択の分かれ目は**Boundary B**（②ブロック=BASIC_RECOMMENDATIONを明示的にFreeへ含めるかどうか、および現状dead codeの`RecommendationMetaSection`をどう扱うか）にある。

---

## Phase 9 — Premium Communication Surfaces（「どう伝えるか」）

| Surface | Current CTA | Premium説明 | Context保持 | Userが価値を理解できるEvidence | Analytics | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Concierge結果画面（quota上限到達時） | Y（`/billing/upgrade`リンク、`isUiPaywall`条件時に2箇所で描画） | **UNRESOLVED**（コードからCTA周辺の説明文の有無・具体性を本監査では文言まで精査していない） | Y（同一画面内） | UNRESOLVED（UI文言の理解しやすさはコードから直接確認できない） | **MISSING**（Paywall表示イベント自体が存在しないことは既存Audit`test-release-premium-boundary-audit.md` Section 10で確認済み） | `ConciergeClientFull.tsx:962,1872,1891,1960,1979` |
| Concierge結果画面（`personal_meaning`相当、action_meaning teaser） | Y（`premium_preview_click`イベント付きCTA） | UNRESOLVED（teaserテキスト自体は個人化の"種類"を示唆する可能性があるが、体系的なValue Preview機構ではない） | Y | UNRESOLVED | **EXISTING**（`premium_preview_click`、`card_teaser_view`） | `ConciergeSectionsRenderer.tsx:140`（既存Audit引用） |
| Shrine Detail Hero直下（Hero意味コピー差し替え） | **N（CTA付随なし、無言の差し替え）** | N | N/A | N（そもそもCTAがないため「価値を理解して行動する」導線自体がない） | UNRESOLVED（専用イベントの有無を本監査では未確認） | `ShrineDetailArticle.tsx:650-654` |
| Shrine Detail ①〜④ブロック直前（`PremiumUpgradePrompt`） | **Y（ゲスト/ログイン済みFreeを`useAuth()`で区別、正しいリンク先）** | UNRESOLVED（コード上のコピー文言の説明力は本監査では評価しない） | Y（`ctx`/`tid`/`historyTheme`を保持） | UNRESOLVED | **EXISTING**（`premium_preview_click`） | `ShrineDetailArticle.tsx:172-220` |
| Shrine Detail state-delta直前（インラインCTA） | **Y**（`/billing/upgrade?source=shrine_detail_state_delta&funnelStep=comparison_preview`という具体的なfunnelパラメータ付き） | UNRESOLVED | Y | UNRESOLVED | **EXISTING**（`comparison_preview`イベントが`monetization-funnel.md`に定義済み、既存Audit引用） | `ShrineDetailArticle.tsx:301-312` |
| Record系（Favorite/Visit/Reflection） | **N（Premium CTA無し、そもそもRECORDはPremium非依存）** | N/A | N/A | N/A | N/A | Phase 6参照 |
| Premium page自体（`/billing/upgrade`） | N/A（遷移先そのもの） | UNRESOLVED（本監査ではこのページ自体の中身を精査していない） | N/A | UNRESOLVED | UNRESOLVED | 未調査（範囲外） |

**Value Preview機構の不在（FACT）**: 上表の通り、現行UIにはPremiumで「何が得られるか」を、実際のコンテンツを渡す前に体系的に説明する専用コンポーネント（Pattern Cに相当するもの）が存在しない。CTAは存在するが、その多くは「アップグレードボタン」そのものであり、価値の中身の事前説明とは別物である。

---

## Phase 10 — Existing UI vs Required Premium Story

**Free Story**: 「今のあなたに合う神社を見つける」
**Premium Story**: 「あなたの状況をより深く理解して、より自分に合ったご縁を探す」

| 確認項目 | 分類 | 根拠 |
| --- | --- | --- |
| Recommendation画面で伝えられるか（Free Story） | **SUPPORTED** | 相談→3件の推薦→基本Reasonという一連の流れが完全にFreeで機能する（`test-release-premium-boundary-audit.md`のCOMPLETE判定を再確認） |
| Recommendation画面で伝えられるか（Premium Story） | **PARTIAL** | `action_meaning`のteaser・`premium_preview`カードは存在するが、Phase 9の通り「価値を事前に理解できるか」はUNRESOLVED（Value Preview機構が無いため、体系的にPremium Storyを伝える設計にはなっていない） |
| Detailで伝えられるか（Free Story） | **SUPPORTED** | Fact section・Deep Dive Q&A・Route等がすべてFreeで完結 |
| Detailで伝えられるか（Premium Story） | **PARTIAL、かつ経路依存（重要な留保）** | `ctx==="concierge"`経由なら真の個人化コンテンツが表示されうるが、Direct Navigation/`ctx=map`/`ctx=compass`経由では「Premiumのはずが実は個人化されていない」コンテンツが出るため（前回監査のAUDIT_STALE訂正）、Premium Storyの一貫性が経路によって崩れる |
| Personal Meaningで伝えられるか | **PARTIAL**（Phase 5参照、同上の経路依存問題） | `buildShrineDetailModel.ts:1625-1694` |
| Recordまで接続できるか | **PARTIAL** | Visit/ReflectionはRankingへ再利用される（Phase 6）ため「記録がRecommendationを深める」というStoryの技術的裏付けはあるが、**この接続自体がUIやCopy上でユーザーに説明されているかは本監査では確認できない**（UNRESOLVED、UI文言の評価は範囲外） |
| Surface間でストーリーが途切れるか | **PARTIAL（途切れる、FACT+INFERENCE）** | Concierge結果画面のPersonal Meaning teaser、Shrine Detailの①〜④、state-deltaはそれぞれ独立したCTA機構であり、一貫した「あなたの状況をより深く理解する」という単一のnarrativeとして統合的に設計されている形跡はコード上確認できない（各CTAが個別に存在するのみ） |
| Direct Navigationユーザーでも成立するか | **NOT_SUPPORTED（Premium Storyとしては）** | Direct Navigation経由ではconcierge文脈が存在しないため、①〜④ブロックの真の個人化コンテンツへ到達する経路自体がない（Phase 1・前回監査のAUDIT_STALE訂正）。Free Storyとしては成立する（Fact section等は完全に機能） |

---

## Phase 11 — Missing Presentation Capability

新規仕様は発明しない。必要性をEvidenceから確定できないものは`POSSIBLE_REQUIREMENT`とする。

| Missing Capability | 分類 | Evidence/根拠 |
| --- | --- | --- |
| Free/Premium Reason差の一貫した表示（BASIC_RECOMMENDATION専用UI） | **POSSIBLE_REQUIREMENT** | `RecommendationMetaSection`がdead codeのため、②ブロック相当の専用表示面が機能していない（Phase 2, 8） |
| Deep Interpretation表示 | **POSSIBLE_REQUIREMENT** | `InterpretationProfile`が計算済みだが誰にも表示されない（Phase 4） |
| Premium Value Preview（Pattern C相当） | **POSSIBLE_REQUIREMENT** | 現行コードに該当機構が一切存在しない（Phase 7, 9） |
| entitlement-aware API | **POSSIBLE_REQUIREMENT（既存2 Auditで繰り返し確認された既知ギャップ）** | `GET /api/shrines/{id}/meaning/`等すべて`AllowAny`、Backend側plan判定なし | 
| Premium CTAの体系的配置 | **POSSIBLE_REQUIREMENT**（既存CTAはあるが、Phase 9の通り分散的） | — |
| context persistence（Direct Navigation等での個人化データ供給） | **POSSIBLE_REQUIREMENT** | Phase 1・10で確認した経路依存問題への対処として考えられるが、具体的な設計は本監査では発明しない |
| Personal Record connection（Favoriteのランキングへの接続） | **POSSIBLE_REQUIREMENT** | Visit/Reflectionは既に接続済みだがFavoriteは未接続という非対称性が存在（Phase 6） |
| entry path normalization（Compassの`tid`欠如問題） | **POSSIBLE_REQUIREMENT** | Compass経由は`tid`を運ばないため、個人化データの供給元が原理的に存在しない（前回監査Phase 1で確認済み） |

---

## Phase 12 — Mother Ship Decision Input

選択肢は固定。各Decisionについて指定項目のみ記載する。Winner/推奨案/順位は付けない。

### Decision A-1a: Free Value Boundary

**候補**: `SHRINE_FACT` / `SHRINE_FACT + BASIC_RECOMMENDATION` / `SHRINE_FACT + BASIC_RECOMMENDATION + VISIT` / その他（Boundary D等）

- **Current FACT**: 現行実装は実質的にBoundary A・C・Dに近い状態にある（RECORD/VISITは既にLogin Requiredのまま無ゲート、①〜④とstate-deltaは既にPremium）。Boundary B（BASIC_RECOMMENDATIONを明示的にFreeへ含めるか）のみが実装上の分岐点になる（Phase 8）。
- **Existing Capability**: Fact section・Route・Save/Visit/Reflectionはすべて既にFree/Login-Requiredとして機能済み。
- **Required Change**: Boundary B採用時は`RecommendationMetaSection`の有効化または代替実装。全Boundary共通でBackend entitlement enforcementの新設。
- **Missing Capability**: BASIC_RECOMMENDATION専用の安定した表示面（現状dead code）。
- **Technical Risk**: Boundary A/C/Dは現状維持に近くLOW、Boundary BはMEDIUM（dead code復活の設計判断が必要）。
- **Test Release Impact**: Boundary A/C/DはLOW、BはMEDIUM（Phase 8）。
- **Unresolved**: Boundary間の「Product上の意味の違い」自体はMother Ship判断であり、本監査は技術的差分のみを提示している。

**Codex Recommendation: NONE**

### Decision A-1b: Premium Presentation Pattern

**候補**: `HARD_GATE` / `TEASER_GATE` / `VALUE_PREVIEW` / `INLINE_EXPANSION` / `SEPARATE_EXPERIENCE`

- **Current FACT**: TEASER_GATEは既に`personal_meaning`/`previous_comparison`で機能中（Phase 7）。HARD_GATEは`PremiumUpgradePrompt`が実質的に近い形（完全差し替え）で存在。VALUE_PREVIEW・INLINE_EXPANSIONはNOT_IMPLEMENTED。SEPARATE_EXPERIENCEはCTAとしての遷移のみ存在（`/billing/upgrade`という汎用ページへの遷移、「ユーザー×神社」の別Personalized Experienceではない）。
- **Existing Capability**: TEASER_GATE・HARD_GATE系はHIGH（Phase 7 Matrix）。
- **Required Change**: VALUE_PREVIEW・INLINE_EXPANSIONは新規Component一式が必要。SEPARATE_EXPERIENCEは既存Audit（`shrine-detail-premium-information-architecture-audit.md`）のOption C評価を参照。
- **Missing Capability**: 全Pattern共通でBackend entitlement enforcement皆無（Phase 7）。
- **Technical Risk**: TEASER_GATE/HARD_GATEはLOW（既存拡張）、VALUE_PREVIEWはLOW〜MEDIUM、INLINE_EXPANSIONはMEDIUM〜HIGH（Free/Premium境界をコンテンツ内部に持つ精密さが必要）、SEPARATE_EXPERIENCEはMEDIUM（既存Precedentあり）。
- **Test Release Impact**: Phase 7 Matrix参照。
- **Unresolved**: 複数Pattern組み合わせ（例: TEASER_GATE+VALUE_PREVIEW）の是非は本監査では評価していない。

**Codex Recommendation: NONE**

### Decision A-1c: Premium Experience Architecture

**候補**: `SAME_PAGE` / `RESTRUCTURED_DETAIL` / `SEPARATE_PREMIUM_EXPERIENCE`

- **Current FACT/Existing Capability/Required Change/Missing Capability/Technical Risk/Test Release Impact**: `docs/audit/shrine-detail-premium-information-architecture-audit.md` Phase 7-12で詳細評価済み（本監査はこれを重複記載しない）。
- **本監査からの追加知見**: どのArchitectureを選んでも、Phase 9で確認した「Value Preview機構の不在」「CTAの分散」「経路依存の個人化データ供給ギャップ」（Phase 1, 10）という**Presentation層の課題は独立して解決が必要**——Architecture選択だけでは自動的に解決しない。
- **Unresolved**: Architecture選択とPresentation Pattern選択（Decision A-1b）の組み合わせ次第で、実装コストが大きく変動する（例: SEPARATE_PREMIUM_EXPERIENCE + VALUE_PREVIEWは、既存Precedentの再利用度が下がる可能性がある）が、本監査はこの相互作用を体系的に評価していない。

**Codex Recommendation: NONE**

---

## Unresolved（Decision外の補足、Phase横断で再掲）

1. Concierge結果画面・Shrine Detail各所のCTA周辺コピー文言が実際に「Premiumで何が得られるか」をユーザーに理解させられるかは、UXレビュー無しにコードのみからは判定できない（Phase 9で全箇所UNRESOLVEDと明記）。
2. Favoriteがランキングへ再利用されていない（Phase 6）ことが意図的設計か見落としかは判別不能。
3. `/billing/upgrade`ページ自体の中身（Value Preview相当の説明が既にそこにあるかどうか）は本監査の調査範囲外。
4. Boundary間・Pattern間・Architecture間の相互作用（組み合わせた場合の実装コスト変化）は体系的に評価していない。
5. Personal Meaning/Personal Recordの経路依存問題（Phase 1, 5, 10）への対処方法は、Presentation Pattern選択（Decision A-1b）とArchitecture選択（Decision A-1c）の両方に影響されるため、いずれか一方だけでは解決しない可能性がある（INFERENCE）。

---

## Evidence / Files 参照一覧

### Frontend（Web）

- `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`, `RecommendationMetaSection.tsx`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`
- `apps/web/src/lib/premium/cardVisibility.ts`, `accessLevel.ts`
- `apps/web/src/app/concierge/ConciergeClientFull.tsx`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/components/shrine/ShrineSaveButton.tsx`

### Backend

- `backend/temples/services/concierge_chat_ranking.py`（`behavior_signal`, `score_v3`, `score_need`等の各Signal定義箇所）
- `backend/temples/services/consultation_interpreter.py`（`InterpretationProfile`）
- `backend/temples/services/shrine_meaning_composer.py`
- `backend/temples/api/views/shrine_meaning.py`, `deep_dive.py`
- `backend/favorites/views.py`

### 参照した既存文書（重複作成を避けるため確認済み、上書きしない）

- `docs/audit/test-release-premium-boundary-audit.md`（PR #2617）
- `docs/audit/premium-personalization-deep-search-audit.md`（PR #2619）
- `docs/audit/shrine-detail-premium-information-architecture-audit.md`（PR #2622）

---

## 責務境界

本書は「Shrine Detail（および関連するConcierge結果画面のCTA）が、既存の機能・情報をFree/Premiumへどう見せているかのEvidence整理」のみを責務とする。以下は対象外であり、実施していない。

- UI・Component・Route・Copy・Premium CTA・Recommendation Ranking・Score・Signal Extraction・InterpretationProfile・Recommendation Reason・Premium Gate・Backend API・Serializer・Authentication・Billing・Subscription・Quota・Favorite・Reflection・Record・Analytics・DB・Schema・Migration・Test・Mobileの変更
- 新規Premium UI実装、Paywall実装、Detail再構成、別Premium Page作成、Backend enforcement修正、既存bug修正、unrelated refactor
- Product Decision（Decision A-1a/A-1b/A-1cの代理決定、Decision B以降の決定を含む）

発見した問題（Value Preview機構の不在、Favorite⇔Rankingの非対称性、経路依存のPersonal Meaning等）はすべて修正せずAuditへ記録するに留めた。

## 更新ルール

- 本書は時点記録（Historical）であり、以降の実装変更によって内容は陳腐化しうる。継続的な更新は行わない。
- Decision A-1a/A-1b/A-1cが確定した場合、その決定は別途Product文書で記録し、本書へ遡及反映はしない。
