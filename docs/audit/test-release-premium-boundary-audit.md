> **Status: Audit / Historical（Web Test Release Premium Boundary Audit、時点記録）**
>
> 本ドキュメントは、KAMI MUSUBI **Web版**のテストリリース前に、現行repo（`develop` HEAD `6e69fef`、PR #2615時点）における Concierge Free/Premium境界・Compass実装状態・Concierge/Compass責務重複を、コード直読で証拠付けした監査記録である。作業は`claude/kami-musubi-premium-audit-8roagp`ブランチで実施した。
>
> **今回のTest Release対象はKAMI MUSUBI Web版のみとする。** Mobile版はRelease Readiness判定・Premium境界設計・実装対象から明示的に除外する。MobileにCompassが未実装であるという事実は記録するが、Mobile対応案・Mobile実装タスク・Mobile Premium Gate・Mobile Release Readinessの設計・実装は行わない。
>
> **Compassの現在地（前提として固定）**: Web版Compassは実装済み・現在はPremium Gateなし・現在のCompass機能はFreeで利用可能・CompassのFree/Premium境界はまだProduct Decisionとして確定していない。**「Compassが未完成なのでComing Soonにする」ことは前提としない。** Coming Soonは決定事項ではなく、Mother Ship Decision候補としてのみ記録する（Decision I）。
>
> **禁止事項の遵守**: 本監査はFree/Premium境界の変更、Premium機能の追加・削除、Compassの実装、Coming Soon UIの実装、Billingロジックの変更、Recommendation Ranking/Score/Direction Logic/Compass Logicの変更、Analytics Event/Payloadの追加・変更、API Response Schemaの変更、Mobile実装、Product仕様の推測更新、Release Scopeの自動決定のいずれも行っていない。コード変更は一切含まない（本PRはdocsのみ）。
>
> **分類ルール**: すべての実質的な主張は **FACT**（コードまたは既存正本文書で直接確認済み）・**INFERENCE**（複数のFACTから本監査が導いた推論）・**UNRESOLVED**（コードからは判定できず、Product判断または追加調査が必要）のいずれかで明示する。Mother Ship Decision ItemsについてはCodex自身は選択を行わない（各Decisionの末尾に`Codex Recommendation: NONE`を明記する）。
>
> 本監査は5つの並列コード調査（Concierge Free/Premium境界・Compass実装状態・Billing Architecture・Analytics現状・Concierge/Compass Signal重複）の結果を、上記の追加要件に沿って再分類・再構成したものである。個別調査はいずれも`develop`最新コミット（`6e69fef`、#2615）を対象に実施した。

# KAMI MUSUBI — Web Test Release Premium Boundary Audit

## 1. Executive Summary

1. **Conciergeは現在どこまでFreeで成立しているか**: `相談入力 → Recommendation → Recommendation Reason → Shrine Detail → Route`まで、匿名ユーザーでも完全に到達可能（Section 5、判定COMPLETE）。ログイン必須なのはFavorite保存・Reflection投稿・相談履歴一覧のみで、相談・推薦自体はログイン不要（`AllowAny`）。
2. **Concierge Premiumは現在何を販売している構造か**: 実質的な差は「1日あたりの利用回数（USAGE_LIMIT）」と「Reasonの一部サブフィールド（今の自分への問い）の深掘り（PERSONALIZATION）」「訪問後の前回比較カード（CONTINUITY）」の3種のみ。主導線（`/concierge/chat/`）の推薦件数はFree/Premium同一（3件固定）であり、既存の別監査文書が記録した「3 vs 6」という件数差は、**別ページ`/plan`にのみ存在**することが本監査で判明した（Section 4、Decision Aの前提FACT）。
3. **Compassは現在どこまでFreeで成立しているか**: `Compass Entry → Input(purpose/origin/birthdate) → Result(方向+参拝候補) → Shrine Detail → Route`まで、匿名ユーザーでも完全に到達可能（Section 8、判定COMPLETE）。Premium Gateは存在しない（`AllowAny`、意図的な設計）。
4. **ConciergeとCompassに実装上の重大な責務重複があるか**: **SHARED_LOGIC（計算モジュール共有）は存在するが、SHARED_OUTPUT/DISTINCT_EXPERIENCEの観点では実装上明確に区別されている。** 九星計算（`kyusei.py`）・方位計算（`direction_reference.py`）・Recommendationエンジン（`build_chat_candidates`等）はConcierge/Compass双方から呼び出される共有ロジックだが、ユーザーが体験する起点・入力形式・主要な問い（「なぜこの神社か相談とつながるか」 vs 「今月どちらへ向かうか」）はコード・UI上明確に異なる（Section 9）。「重複」ではなく既存契約が定義する意図的な計算モジュール再利用（Signal Reuse）である。
5. **現行Billing ArchitectureをCompassにも利用できるか**: 技術的にはYES（REUSABLE）。`is_premium_for_user()`・`resolve_plan_context()`・`check_quota()`はplan/feature非依存の汎用実装であり、Compass Viewへ追加の呼び出しを配線すれば動作する。ただし現状`QUOTA_POLICY`辞書・`CardId`共用体のいずれにもCompass用エントリはなく、DRFのPermission Class形式の宣言的Gateも存在しない（すべてView内ad-hoc呼び出し）（Section 10）。
6. **Web Test Releaseを妨げる技術的Blocker（P0）はあるか**: 本監査では**発見していない**。Concierge主導線・Compass主導線とも技術的に安定動作し、テストは通過している（Section 8-11のEvidence参照）。ただしAnalyticsの一部欠落（Concierge開始・Recommendation request・Paywallイベントの不在）と、Favorite件数上限ポリシーの未enforcementは、P0ではないがRelease前に把握しておくべき既知のギャップとして記録する（Section 12 Unresolved）。
7. **Release前にMother Ship判断が必要な項目は何か**: Section 13にDecision A〜Iとして9件を整理した（選択は行わない）。特に重要なのは、Concierge主導線の推薦件数差の扱い（Decision A/B）、CompassをTest Release時も全Free公開のままとするか（Decision C/D）、CompassのPremium候補をどのカテゴリから構成するか（Decision E）である。

---

## 2. 前提: 調査方法と対象範囲

- 対象commit: `origin/develop` HEAD `6e69fef`（PR #2615マージ後）。作業ブランチ`claude/kami-musubi-premium-audit-8roagp`はこのコミットから分岐（Phase 0でclean working tree・重複branch/PR無しを確認済み）。
- 5並列のコード調査エージェント（Concierge Free/Premium境界・Compass実装状態・Billing Architecture・Analytics現状・Concierge/Compass Signal重複）が、それぞれ独立にgrep・ファイル直読・テスト直読を実施した。本書はその結果を、追加指示（本書冒頭の前提）が要求する分類軸へ再構成したものである。**新たなコード調査はSection内の個別確認箇所（Route Attribution等）を除き実施していない。**
- **本監査の対象はWeb（`apps/web`）のみ**。`apps/mobile`はCompassが存在しない事実の記録（Section 6）にのみ言及し、それ以外のMobile関連調査・設計・実装は行っていない。
- 既存`docs/audit/`・`docs/product/`・`docs/core/`・`docs/analytics/`配下の正本/監査文書は、Section 15に列挙した範囲で参照したが、**すべての実装状態claimは本監査が独自にコードを再確認した上で記載している**。文書の記述と現行コードが乖離している箇所はその旨を明記する。

---

## 3. Concierge Free Inventory

対象はConcierge主導線 `POST /api/concierge/chat/`（`ConciergeChatView`、`backend/temples/api_views_concierge.py:474`）。Frontend入口は`apps/web/src/app/concierge/page.tsx` → `ConciergeClientFull.tsx`。

| Feature | Free利用 | Premium利用 | 制御場所 | Backend enforcement | Frontend gating | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Concierge入力（エンドポイント到達） | Y（匿名可） | Y | Backend | `permission_classes = [AllowAny]` | なし | `backend/temples/api_views_concierge.py:493` |
| 相談テーマ選択 | Y | Y | — | なし | なし | `concierge_input_contract.py:91-152`（Level 1 Consultation） |
| 自由入力（`query`/`message`） | Y | Y | — | なし | なし | `concierge_input_contract.py:183` |
| 誕生日入力（任意項目） | Y | Y | — | なし（入力受理は無制限、値はRanking/Reasonの補助シグナル） | なし | `concierge_input_contract.py:22,169`; `api_views_concierge.py:560-572` |
| ご利益（goriyaku）タグ | Y | Y | — | なし | なし | `concierge_input_contract.py:22-24` |
| 参拝条件（`extra_condition`/`visit_preferences`） | Y | Y | — | なし | なし | `concierge_input_contract.py:25-32,222` |
| Recommendation実行 | Y（1日あたり回数制限あり） | Y（無制限） | Backend（先頭でquota判定） | `resolve_plan_context()`→`check_quota(plan_context,"concierge")`、不可の場合は候補生成前に空配列+`LIMIT_MSG`を返す | サーバー応答の`stop_reason`/`limitReached`を表示するのみ | `api_views_concierge.py:645-668,1005`; 限度値: 匿名=3、Free=環境変数`CONCIERGE_DAILY_FREE_LIMIT`（既定5、`quota_policy.py`既定値3を上書き）、Premium=無制限（`quota_policy.py:7-26`, `quota_service.py:196-198`, `settings.py:16`） |
| Recommendation件数（主導線） | 3件（Free/Premium/匿名すべて同一） | 3件（差なし） | Backend | `_trim_to_top3_and_fill_message()`が無条件に`[:3]`（plan引数を受け取らない） | — | `concierge_chat_presentation.py:116-124`; 呼び出し元`concierge_chat.py:930`（`build_chat_recommendations()`にplan引数なし） |
| Recommendation Reason（本文） | ほぼ全文表示（"partial"ラベルだが実装上は切り詰めなし） | 全文 | Frontend表示ポリシー | なし | `cardVisibility.ts:78-107`の`shrine_meaning`/`consultation_summary`はFree="partial"だが、`ConciergeSectionsRenderer.tsx:1065-1096`は`!== "hidden"`のみ判定し全文レンダリング | 上記file:line |
| Reasonの一部サブフィールド（「今の自分への問い」=action_meaning） | N（teaserテキストに差し替え） | Y | Frontend | なし | `cardVisibility.ts`: Free="teaser"、Premium="visible"。`ConciergeSectionsRenderer.tsx:1083-1085`が固定テキストへ差し替え | 上記file:line |
| 神社詳細への遷移 | Y | Y | — | Shrine Detail系Viewはすべて`AllowAny` | なし | `detailHref.ts:32-57`; `backend/temples/api/views/shrine.py:112,161,212,345` |
| Route/Mapへの遷移 | Y | Y | — | なし | なし | `GoogleMapRouteLink.tsx:25-105` |
| Favorite（保存） | ログイン必須（Premium不問） | Y | Backend | `IsAuthenticated`のみ。件数上限ポリシー（Free=10）は`quota_policy.py`に定義済みだが未配線 | 未ログイン時はログイン誘導のみ | `api_views.py:21-77`; `api/views/favorite.py:23-98`; ポリシー`quota_policy.py:10,16,22` |
| Reflection/Action投稿 | ログイン必須（Premium不問） | Y | Backend | `IsAuthenticated`のみ | 訪問履歴の有無のみで表示 | `api/views/reflection.py:10-56`; `ShrineDetailArticle.tsx:730-740` |
| Reflection「前回との違い」比較カード | N（Premium限定） | Y | Frontend | Backend側専用エンドポイントの権限実装は未確認（UNRESOLVED） | `isPremiumActive`分岐 | `ShrineDetailArticle.tsx:288-313`; `PremiumStateDeltaCard.tsx:25,58-81` |

**Login必須条件（機能横断、FACT）**:

| ログイン不要（AllowAny） | ログイン必須（IsAuthenticated） |
| --- | --- |
| Concierge chat（`api_views_concierge.py:493`）、legacy/compat variants（`:1112,1144`）、Concierge plan（`:1112`）、Concierge thread単体（`:1144`） | Favorite（`api_views.py:27`, `api/views/favorite.py:24,51,85`）、Reflection作成/一覧（`api/views/reflection.py:11,48`）、Visit作成/一覧（`api/views/visit.py:13,60`）、Concierge相談履歴一覧（`api/views/concierge.py:59`）、神社投稿（`shrine_submission.py:21`） |
| Shrine詳細/検索系View（`shrine.py:112,161,212,345`, `shrine_public.py:8`, `shrine_meaning.py:13`） | — |

---

## 4. Concierge Premium Inventory と最終分類

Premiumで解放される、または差が生じる機能を、追加指示が定義する分類軸（FREE_CORE / PERSONALIZATION / CONTINUITY / CROSS_FEATURE / USAGE_LIMIT / FEATURE_LOCK / UNCLEAR）で整理する。良し悪しは判断しない。

| Concierge機能 | 分類 | 理由 | Backend/Frontend enforcement | Evidence |
| --- | --- | --- | --- | --- |
| 相談テーマ選択・自由入力・誕生日・goriyaku・参拝条件の入力受理 | **FREE_CORE** | Conciergeという体験（相談→推薦）を成立させるために必須。すべてFreeで無制限に受理される | なし | Section 3 |
| Recommendation基本実行と基本Reason文（shrine_meaning/consultation_summary） | **FREE_CORE** | Freeでも"なぜこの神社か"の主理由が全文表示される（切り詰めなし、Section 3） | Frontendラベルは"partial"だが実装上は全文 | `ConciergeSectionsRenderer.tsx:1065-1096` |
| Shrine Detail・Route遷移 | **FREE_CORE** | Concierge結果からの主要な行動導線として、ログイン・Premium不問で到達可能 | なし | Section 3 |
| Concierge日次利用回数（匿名3回・Free 5回 vs Premium無制限） | **USAGE_LIMIT** | 同一機能（Concierge実行）の回数のみを制限。機能・品質自体に差はない | Backend（`check_quota`） | `api_views_concierge.py:645-668` |
| `/concierge/plan`ページの表示件数（Free 3 vs Premium 6） | **USAGE_LIMIT**（ただし主導線とは別ページ） | `recommend_limit_for_user()`が件数のみ変える。Ranking結果自体は同一 | Backend | `concierge_plan.py:549,583`; `billing_state.py:147-148` |
| Concierge主導線（`/concierge/chat/`）の推薦件数 | **該当なし（現行差なし）** | 3件固定でFree/Premium差が存在しない。USAGE_LIMIT候補として設計されていた形跡はあるが現状は機能していない | — | `concierge_chat_presentation.py:116-124` |
| Reasonの「今の自分への問い」（action_meaning）teaser解除 | **PERSONALIZATION** | 同一推薦に対し、より内省的な問いかけを追加提示。推薦の正しさ自体は変えない | Frontend | `ConciergeSectionsRenderer.tsx:1083-1085` |
| Reflection「前回との違い」state delta比較カード | **CONTINUITY**（かつ**CROSS_FEATURE**の性質も持つ：Visit/Reflection履歴とShrine Detail/Concierge threadを横断） | 過去の自分（前回訪問・前回相談）との比較という継続利用価値。Shrine Detail・Visit・Reflection・Conciergeスレッドを横断して初めて成立する | Frontend確認済み、Backend側専用エンドポイントの権限実装はUNRESOLVED | `ShrineDetailArticle.tsx:288-313`; `PremiumStateDeltaCard.tsx:25,58-81` |
| Favorite件数上限（Free=10ポリシー） | **USAGE_LIMIT（未稼働）** | ポリシー定義はあるが、Favorite関連の全Viewから呼び出されておらず現状は無制限。「現行なし」に等しい | ポリシー定義のみ、呼び出し箇所なし | `quota_policy.py:10,16,22`; Section 3 |
| FEATURE_LOCK該当機能 | **（該当なし）** | Concierge主導線には、Freeで完全に利用不可能な独立機能は確認できなかった。すべてUSAGE_LIMITまたはPERSONALIZATION/CONTINUITYの度合いの差として実装されている | — | Section 3全体 |
| Staffユーザーの自動Premium化 | **UNCLEAR**（製品境界ではなく運用/開発上のバイパスの可能性が高いが、コードからは意図を断定できない） | `is_staff`ユーザーは無条件でPremium相当になる。QA/運用目的のバイパスなのか、製品境界として意図されたものなのか、コードのみからは判別不能 | `billing_state.py:144-149` | — |

---

## 5. Web Free Concierge Journey確認

**判定: COMPLETE**

`相談入力 → Recommendation → Recommendation Reason → Shrine Detail → Route` は、匿名ユーザーであっても技術的に完全に到達可能。

| 確認項目 | 結果 | Evidence |
| --- | --- | --- |
| Premium CTAで途中遮断されないか | 遮断なし。全APIが`AllowAny`またはUI上ノーゲート | Section 3 |
| Recommendation結果が過度に制限されていないか | 3件はFree/Premium共通。Freeが意図的に劣化させられている形跡はない | `concierge_chat_presentation.py:116-124` |
| Recommendation ReasonがFreeでも表示されるか | 主要な理由文はFreeでも全文表示。teaser化は1サブフィールドのみ | `ConciergeSectionsRenderer.tsx:1065-1096` |
| Shrine Detailへ進めるか | 進める（全`AllowAny`） | `shrine.py:112,161,212,345` |
| Routeへ進めるか | 進める（ログイン/Premium判定なし） | `GoogleMapRouteLink.tsx:25-105` |
| Login/Billing Stateによる予期しない遮断がないか | 主導線には確認されず。Favorite/Reflection**投稿**のみログイン必須だが、これはJourney本体の外側の操作 | Section 3 |

**注**: 1日あたりの利用回数上限に達した場合、以降の実行はブロックされるが、これは「1回分のJourneyの完結性」を損なうものではなく「繰り返し利用」の制限である。

---

## 6. Compass実装状態

対象: `apps/web/`（Web版のみ）、参考として`apps/mobile/`の不在事実のみ記録。

### UI

| Item | Status | Evidence |
| --- | --- | --- |
| `/compass`ページ（Web） | IMPLEMENTED | `apps/web/src/app/compass/page.tsx:1-10` |
| CompassClient（purpose/origin/birthdate入力、5種のfail-safe結果状態） | IMPLEMENTED | `apps/web/src/features/compass/CompassClient.tsx:85-358` |
| Purpose選択・Origin要約・方向ビジュアル・参拝候補セクション | IMPLEMENTED（各テスト有） | `apps/web/src/features/compass/components/*` |
| Home画面からのCTA導線 | IMPLEMENTED | `HomeCompassSection.tsx:23-42`; `HomeMainClient.tsx:14-28` |
| グローバルナビ（ハンバーガーメニュー）への導線 | NOT_IMPLEMENTED | `HamburgerMenu.tsx`にCompass参照なし |
| E2Eテスト | IMPLEMENTED | `apps/web/e2e/05_direction_flow.spec.ts`（352行） |
| Coming Soon/無効化プレースホルダー | NOT_IMPLEMENTED（Compassは既に本番稼働中であり、現状Coming Soon状態ではない） | grep 0件 |
| （参考、対象外）Mobileアプリの`/compass`ルート | NOT_IMPLEMENTED（記録のみ、対応は本監査スコープ外） | `apps/mobile/app`にcompassディレクトリなし |

### Backend

| Item | Status | Evidence |
| --- | --- | --- |
| `POST /compass/recommendations/` | IMPLEMENTED | `backend/temples/api_views_compass.py:36-97` |
| Web BFFプロキシ | IMPLEMENTED（テスト有） | `apps/web/src/app/api/compass/recommendations/route.ts:1-15` |
| Compass Runtime Authority（年盤∩月盤、Monthly Fallback） | IMPLEMENTED（テスト有） | `backend/temples/services/compass_runtime.py:70-131` |
| Compass Direction Candidate Filter | IMPLEMENTED（テスト有） | `backend/temples/services/compass_direction_filter.py:29-92` |
| Compass Recommendation Orchestrator（既存Recommendationへの統合） | IMPLEMENTED（テスト有、851行） | `backend/temples/services/compass_recommendation_orchestrator.py:1-334,49-51` |
| Premium/quotaゲート | NOT_IMPLEMENTED（意図的な設計判断） | `api_views_compass.py:39-45`（docstringで明示、`permission_classes=[AllowAny]`） |

### Data

| Item | Status | Evidence |
| --- | --- | --- |
| ユーザー`birthday`フィールド（永続化） | IMPLEMENTED（ただしCompassは`UserProfile.birthday`を読まず、毎回手入力） | `backend/users/models.py:15-17`; `CompassClient.tsx:28,62,75` |
| Compass計算結果のDB永続化 | NOT_IMPLEMENTED（意図的、ステートレス設計） | Migration該当なし。`compass-mvp-runtime-contract.md` §7 |
| Runtime-onlyな導出データ（`CompassDirectionRuntime`） | IMPLEMENTED（都度計算、非永続） | `compass_runtime.py:102-125` |

### Premium

| Item | Status | Evidence |
| --- | --- | --- |
| Compass専用Billing Gate/Entitlement | NOT_IMPLEMENTED（明示的なProduct Decision、既存監査で確認済み） | `api_views_compass.py:39-45`; `docs/audit/compass-free-premium-boundary.md` |

### Analytics

| Item | Status | Evidence |
| --- | --- | --- |
| `compass_entry`/`compass_result`/`home_compass_entry_click` | IMPLEMENTED | `CompassClient.tsx:102-104,120-131`; `HomeCompassSection.tsx:34` |
| Recommendation attribution（`card_view`/`shrine_detail_transition`/`shrine_detail_view`、`source=compass`） | IMPLEMENTED | `docs/analytics/compass-analytics-contract.md`; `CompassRecommendationsSection.tsx` |
| Route Attribution（`route_open`が`ctx=compass`を引き継ぐか） | IMPLEMENTED（一度Gapとして発見され修正済み） | `docs/audit/compass-route-attribution-contract.md`がGapを特定 → `GoogleMapRouteLink.tsx:16,29,71,91`が`ctx`propを受理・伝播（コミット履歴上、直後に`fix: Compass起点のルート計測コンテキストを引き継ぐ (#2525)`が対応） |
| Favorite/Visit/Reflectionへのsource伝播 | IMPLEMENTED（ただしSESSION/NAVIGATION ATTRIBUTIONのみ、DB永続化なし） | `docs/analytics/compass-analytics-contract.md`「Action source propagation」節 |

---

## 7. Compass Premium候補分類

現行Compass機能を確認し、Premium化の**候補になり得る**機能・価値を分類する。**どれをPremiumにするかは決定しない。** 実装が存在しないものは将来案と混在させずNOT_IMPLEMENTEDと明記する。

### FREE_CORE

Compassという体験を成立させるために必要な基本機能（現状すべてFreeで提供、Gateなし）。

| 機能 | Evidence |
| --- | --- |
| Purpose（目的）選択 | `CompassPurposeSelector.tsx` |
| Origin（出発地点）選択 | `CompassOriginSummary.tsx` |
| Birthdate入力 | `CompassClient.tsx:28,62,75` |
| 方向結果（referenceDirections）表示 | `CompassDirectionVisual.tsx`; `compass_runtime.py:102-125` |
| 参拝候補（Recommendation統合結果）表示 | `CompassRecommendationsSection.tsx`; `compass_recommendation_orchestrator.py` |
| Shrine Detailへの遷移 | `buildShrineHref()`（`compass-route-attribution-contract.md`） |

### PERSONALIZATION

ユーザー固有情報によって価値が深くなる、実在するSignal（現状すべてFreeで提供）。

| Signal | 実装状況 | Evidence |
| --- | --- | --- |
| birthdate（九星・方位計算の個人化入力） | IMPLEMENTED | `compass_runtime.py:22-23,41-44`; `kyusei.py` |
| purpose（候補神社の絞り込み） | IMPLEMENTED | `compass_recommendation_orchestrator.py` |
| individual compatibility（相性説明の深掘り） | NOT_IMPLEMENTED（Compass自体には相性説明レイヤーが存在しない。Concierge側のCompat Modeとは別物） | `docs/audit/compass-free-premium-boundary.md` Model B「no deeper Compass content exists to gate」 |
| consultation context（相談履歴を踏まえた文脈） | NOT_IMPLEMENTED（Compassは相談自由文を持たず、Concierge履歴とも接続されていない） | `CompassClient.tsx`にfree-text入力欄なし |

### CONTINUITY

単発利用ではなく継続利用によって価値が増える機能。

| 機能 | 実装状況 | Evidence |
| --- | --- | --- |
| Compass History（過去のCompass結果の保存・一覧） | **NOT_IMPLEMENTED** | Compassはステートレス。DB永続化なし（`compass-mvp-runtime-contract.md` §7） |
| Saved state（保存された方向・候補） | **NOT_IMPLEMENTED** | 同上 |
| Previous directions（過去の方向との比較） | **NOT_IMPLEMENTED** | 同上 |
| Daily/monthly transition（月次推移の表示） | **NOT_IMPLEMENTED**（月選択UIが存在せず、常に「今月」のみ計算） | `docs/audit/compass-premium-personal-continuity.md` §2「no month-selection UI」 |
| Revisit experience（再訪を前提とした導線） | **NOT_IMPLEMENTED** | 同上 |

### CROSS_FEATURE

Compass単体ではなく、他機能と接続することで価値が増えるもの。

| 接続 | 実装状況 | Evidence |
| --- | --- | --- |
| Compass → Shrine Detail | **IMPLEMENTED**（実際のページ遷移、`ctx=compass`付き） | `buildShrineHref()`; `compass-route-attribution-contract.md` |
| Compass → Route/Map | **IMPLEMENTED**（`route_open`が`ctx=compass`を引き継ぐ） | `GoogleMapRouteLink.tsx:16,29,71,91` |
| Compass → Favorite/Visit/Reflection | **PARTIAL（Analytics上のsource属性のみ、データとしての接続は未実装）** | `docs/analytics/compass-analytics-contract.md`「同一page render範囲でのみsource=compassを伝播、DB永続化なし」；`Favorite`モデルに`source`/`thread`等のprovenanceフィールドは存在しない（`docs/audit/compass-premium-personal-continuity.md` §2） |
| Compass → Concierge（相談文脈の引き継ぎ、または逆方向） | **NOT_IMPLEMENTED** | 双方向とも接続なし。Compassは独立オーケストレーション層として実装されている（`compass_recommendation_orchestrator.py`は`ConciergeChatView`を経由しない） |

### USAGE_LIMIT

同一Compass機能について回数・日次・月次上限で差を付ける可能性がある箇所。

**現行なし。** Compassには`quota_policy.py`上のエントリが存在せず（`"compass"`キー未定義）、`check_quota`/`consume_quota`の呼び出しも`api_views_compass.py`から一切行われていない（`AllowAny`、無制限）。

### UNRESOLVED

現行実装・文書からPremium候補か判断できないもの。

- 現状Freeで提供されているPERSONALIZATION Signal（birthdate/purposeの個人化度合い）が、将来Premium差別化の軸になり得るかどうかは、Product判断であり実装からは判定できない。
- CROSS_FEATURE（Compass→Favorite/Visit/Reflectionの永続的接続）を実装した場合、それ自体をPremium価値にするかFree範囲に含めるかは未決定（Product判断）。

---

## 8. Web Free Compass Journey確認

**判定: COMPLETE**

`Compass Entry → Input/Runtime Condition → Result → Related Shrine/Map/Route` は、実装済みの主要Flowとしてコード・テスト・UIから特定でき、匿名ユーザーでも完全に到達可能。存在しないStep（例: 月選択、履歴閲覧）は追加していない。

| Step | 実装状況 | 到達可否 | Evidence |
| --- | --- | --- | --- |
| Compass Entry（Home CTA または直接URL） | IMPLEMENTED | Y（ログイン不要） | `HomeCompassSection.tsx:34`; `apps/web/src/app/compass/page.tsx` |
| Input/Runtime Condition（purpose/origin/birthdate入力） | IMPLEMENTED | Y | `CompassClient.tsx:85-358` |
| Result（方向+参拝候補） | IMPLEMENTED | Y（`AllowAny`、無制限） | `api_views_compass.py:36-97,39-45` |
| Related Shrine（Shrine Detail遷移） | IMPLEMENTED | Y | `buildShrineHref()` |
| Route/Map | IMPLEMENTED | Y（Shrine Detail経由、既存`GoogleMapRouteLink`を再利用） | `GoogleMapRouteLink.tsx:25-105` |
| （存在しないStep）Revisit/History閲覧 | NOT_IMPLEMENTED | — | Section 7 CONTINUITY参照 |

---

## 9. Concierge / Compass 責務監査の最終整理

追加指示が定義する4分類（SHARED_SIGNAL / SHARED_LOGIC / SHARED_OUTPUT / DISTINCT_EXPERIENCE）で整理する。Product評価ではなく、実装上の責務境界のFACT収集である。

| 対象 | 分類 | 内容 | Evidence |
| --- | --- | --- | --- |
| birthdate | **SHARED_SIGNAL** | 同一の生年月日という入力を、Concierge・Compass双方が受け取る（ただし別々のUIで別々に入力される。プロフィールからの共有はされていない） | `concierge_input_contract.py:21`; `CompassClient.tsx:28,62,75` |
| 九星計算（`kyusei.py`） | **SHARED_LOGIC** | `annual_lucky_directions()`/`planned_visit_lucky_directions()`/`monthly_lucky_directions()`は、Concierge Chat View（`api_views_concierge.py:561-572`）とCompass Runtime（`compass_runtime.py:22-23,41-44`）の両方から直接呼び出される、同一の計算モジュール | 両file:line |
| 方位計算（`direction_reference.py`） | **SHARED_LOGIC** | `build_direction_reference()`/bearing計算が両方で使用される | `direction_reference.py:96-118`; `compass_runtime.py` |
| Recommendationエンジン（`build_chat_candidates`/`_attach_breakdown`/`build_chat_recommendations`） | **SHARED_LOGIC** | Compass Orchestratorは`ConciergeChatView`を経由せず、これらの関数を直接呼び出して独自の候補集合を構築する（Concierge Chat Viewも同じ関数群を使用） | `compass_recommendation_orchestrator.py:49-51` |
| 五行/西洋占星術スコアリング（`astrology.py`, `astro_bonus`） | **Concierge限定（SHARED_LOGICではない）** | Concierge Rankingのみが使用（`concierge_chat_ranking.py:1226-1239,326-371`）。Compassのコードからはこれらの関数への参照が確認できず、Compassは方位のみを扱い五行/西洋占星術は使用しない | Compass側grep 0件 |
| 「なぜこの神社か」の出力内容（Recommendation Reason/神社固有の理由文） | **SHARED_OUTPUT（部分的）** | 両者ともRecommendation Authority + Shrine Knowledge Authorityの合成結果を表示する。Compass結果画面の神社候補カードはConcierge側と同一の`ShrineCardCompact`コンポーネントを再利用しており、ユーザーが読む「神社ごとの理由文」の生成ロジックも共有 | `docs/audit/compass-full-experience-qa.md` §4,§8 |
| 「なぜこの方向か」（Compass）vs「相談とどうつながるか」（Concierge） | **DISTINCT_EXPERIENCE** | Compassの方向説明はConcierge側に存在しない独自コンテンツ。Concierge側の相談解釈（`consultation_interpreter.py`）もCompassには存在しない | Section 9下記のAuthority確認参照 |
| Concierge全体の体験成立性 | **DISTINCT_EXPERIENCE（FACT確認済み）** | 現行実装上、「相談・願い・条件から神社をRecommendationする体験」として成立している。自由文入力・goriyakuタグ・visit_preferencesを起点とし、`consultation_axis`/`need_tag`をRanking・Reasonへ反映する一連の実装が確認できる | `concierge_input_contract.py`; `concierge_chat_ranking.py`; Section 3 |
| Compass全体の体験成立性 | **DISTINCT_EXPERIENCE（FACT確認済み）** | 現行実装上、「方向・場所・現在条件（今月）を起点とした体験」として成立している。自由文入力欄が存在せず、purpose選択チップ+origin+birthdateのみで完結する構造がUI・Backendともに一貫している | `CompassClient.tsx`（自由文入力欄なし）; `compass-full-experience-qa.md` §3「PRODUCT BOUNDARY CLEAR」 |
| 入力形式の区別 | **DISTINCT_EXPERIENCE** | Conciergeは自由文中心、Compassはチップ選択+構造化入力のみ（自由文欄が存在しない設計自体がUIレベルで確認できる） | `compass-full-experience-qa.md` §3 |

**結論（FACT、Product評価ではない）**: ConciergeとCompassは、計算の土台（九星・方位・Recommendationエンジン）を**SHARED_LOGIC**として共有しているが、五行/西洋占星術スコアリングはConcierge限定であり、ユーザーが体験する起点・入力形式・主要な問いは実装上**DISTINCT_EXPERIENCE**として区別されている。これは既存契約文書（`docs/product/compass-product-contract.md` Section 1「Signal Reuse（許可）とAuthority Reuse（禁止）を明確に区別する」）が定義する設計方針と一致する、コードレベルでの再確認である。

---

## 10. 現行Billing Architecture確認

### アーキテクチャ図（FACT、file:line付き）

```
User
  → Frontend Component/Hook
      apps/web/src/features/billing/hooks/useBilling.ts:22
        → apps/web/src/lib/api/billing.ts:19-25（fetch "/api/billings/status/"）
  → BFF（Next.js Route Handler、同一オリジン）
      apps/web/src/app/api/billings/status/route.ts:17-44
        - 開発時Stub: NODE_ENV!=="production" && NEXT_PUBLIC_FORCE_BILLING_PLAN==="premium" なら
          Backend呼び出しをスキップしPremium固定応答（:18-27）
        - 通常時: bffFetchWithAuthFromReq() → apps/web/src/lib/server/bffFetch.ts:89-207
  → Backend Billing State（Django/DRF）
      backend/temples/api/urls.py:145 → BillingStatusView（backend/temples/api/views/billing.py:48-69）
        → get_billing_status(user) → backend/temples/services/billing_state.py:37-82
        - BILLING_PROVIDER=stub の場合、DBを無視し環境変数BILLING_STUB_PLAN/BILLING_STUB_ACTIVEを信頼（:55-56,84-121）
        - stripe/revenuecatの場合、UserProfile（backend/users/models.py:5-36）を参照
  → Feature Gate
      backend/temples/services/plan_service.py:14-50（resolve_plan_context）
        → billing_state.py:130-144（is_premium_for_user）
      backend/temples/services/quota_policy.py:7-48（QUOTA_POLICY辞書、plan×feature）
      backend/temples/services/quota_service.py:175-286（check_quota/consume_quota、FeatureUsageテーブル）
  → 呼び出し元（例: Concierge） backend/temples/api_views_concierge.py:645-668
```

**重要な構造的事実**: DRFの`IsPremium`のようなPermission Class、または`@requires_premium`のようなデコレータは**リポジトリ全体で存在しない**（grep 0件）。GatingはすべてView内でのad-hocな`resolve_plan_context()`→`check_quota()`呼び出しとして実装されている。

### Checkout/Webhookフロー（FACT）

- Checkout開始: `apps/web/src/app/api/billings/checkout/route.ts:8-30` → Backend `BillingCheckoutView`（`billing.py:93-116`）→ `create_checkout_session()`（`billing_checkout.py:41-83`）。
- Webhook: `BillingStripeWebhookView`（`billing.py:119-146`）。署名検証は`stripe_webhook.py:59-87`。`checkout.session.completed`→`UserProfile`更新（`:257-294`）、`customer.subscription.*`→ステータス/期限更新（`:297-415`）。
- Success/Cancel後の再取得: マウント時に`useBilling()`を1回自動実行するのみ（`success/page.tsx:63`）。自動ポーリング/クエリ無効化なし（React Query/SWR未使用）。

### Compass再利用可能性（技術的事実のみ）

| コンポーネント | File:Line | 分類 |
| --- | --- | --- |
| `UserProfile`モデル（正本） | `backend/users/models.py:5-36` | REUSABLE |
| `is_subscription_active()` | `backend/users/services/billing.py:12-28` | REUSABLE |
| `get_billing_status()` | `billing_state.py:37-121` | REUSABLE |
| `is_premium_for_user()`/`is_premium_for_request()` | `billing_state.py:125-144` | REUSABLE |
| `resolve_plan_context()` | `plan_service.py:14-50` | REUSABLE |
| `QUOTA_POLICY`辞書 + `get_feature_policy()` | `quota_policy.py:7-48` | PARTIAL（機構は汎用だが`"compass"`キーは未定義） |
| `check_quota()`/`consume_quota()`/`FeatureUsage` | `quota_service.py:175-286` | REUSABLE（feature文字列を追加すれば動作） |
| `BillingStatusView`/`BillingCheckoutView`/`BillingStripeWebhookView` | `billing.py:48-146` | REUSABLE |
| `CompassRecommendationsView` | `api_views_compass.py:36-94` | 未配線（`plan_context`/`quota`のimportなし、`AllowAny`固定） |
| DRF Permission Class（`IsPremium`等） | 該当なし | 存在しないため再利用不可（新規実装が必要） |
| `useBilling()`フック、BFF billing routes | `useBilling.ts:11-41`, `route.ts`各種 | REUSABLE |
| `resolveAccessLevel()`/`CARD_VISIBILITY_POLICIES` | `accessLevel.ts:8-21`, `cardVisibility.ts:30-186` | PARTIAL（`CardId`共用体にCompass用IDが無い、UI表示制御のみ） |
| Env stub（`NEXT_PUBLIC_FORCE_BILLING_PLAN`、`BILLING_STUB_PLAN`/`BILLING_STUB_ACTIVE`） | 各種route.ts、`billing_state.py:26-34,84-121` | REUSABLE（test専用） |

**テストによる裏付け**: `backend/temples/tests/api/test_billing_status_contract.py:14-80`、`test_billing_checkout_contract.py`、`test_billing_webhook_contract.py`、`test_concierge_recommend_limit_contract.py`。`test_compass_recommendations_api.py`にはpremium/billing/quotaへの参照が一切なし。

---

## 11. Analytics Coverage（Concierge / Compass別）

### Concierge

| Event | 分類 | Event名/型 | 発火箇所 |
| --- | --- | --- | --- |
| entry/start | **MISSING** | — | `/concierge`表示や送信前の開始イベントは存在しない。近縁の`consultation_theme_click`（`ConciergeClientFull.tsx:1483`）はチップ選択イベントで代替不可 |
| input（入力完了） | **PARTIAL** | `direction_condition_submitted`（direction-domain eventの流用） | `ConciergeClientFull.tsx:1747`（entry card送信のみ。follow-up送信・filter再送信・auto-submitの3箇所は無計装） |
| submit / recommendation request | **MISSING** | — | 独立Eventなし。`ConciergeRecommendationLog`はDB記録でありAnalytics Eventではない |
| recommendation success | **EXISTING** | `consultation_completed` | `ConciergeClientFull.tsx:1195` |
| result impression | **EXISTING** | `card_view`/`card_teaser_view`/`card_partial_view`、`concierge_result_impression` | `ConciergeSectionsRenderer.tsx:398`他多数 |
| shrine detail click | **EXISTING** | `shrine_detail_transition` | `ConciergeSectionsRenderer.tsx:980,1201` |
| route click | **EXISTING** | `route_open` | `GoogleMapRouteLink.tsx:65` |
| favorite | **EXISTING** | `favorite_click`（+`shrine_decision`） | `ShrineSaveButton.tsx:67,80` |
| premium CTA（impression/click） | **PARTIAL**（impressionはConcierge結果画面のみ、Shrine Detail側impressionイベントなし） | `card_teaser_view`(cardId=`premium_preview`) / `premium_preview_click` | `ConciergeSectionsRenderer.tsx:581-594,140`; `ShrineDetailArticle.tsx:202` |
| paywall | **MISSING** | — | `isUiPaywall`等のUI変数は存在するが、隣接するtrack呼び出しは0件 |

### Compass

| Event | 分類 | Event名/型 | 発火箇所 |
| --- | --- | --- | --- |
| entry | **EXISTING** | `compass_entry`、`home_compass_entry_click` | `CompassClient.tsx:102-104`; `HomeCompassSection.tsx:34` |
| input/interaction（purpose/origin変更ごとの個別Event） | **PARTIAL**（最終送信時の`compass_result`ペイロードにのみ`purpose`/`origin_mode`が含まれ、選択変更それ自体の中間Eventは存在しない） | `compass_result`のproperty | `CompassClient.tsx:120-131` |
| execution（送信） | **PARTIAL**（`compass_result`が成功/失敗状態を包含し、送信そのものを表す独立Eventはない） | `compass_result`（`result_state`） | `CompassClient.tsx:120-131` |
| result impression | **EXISTING** | `card_view`（`source=compass`） | `docs/analytics/compass-analytics-contract.md`; `CompassRecommendationsSection.tsx` |
| shrine click | **EXISTING** | `shrine_detail_transition`（`source=compass`） | 同上 |
| map/route click | **EXISTING**（`ctx=compass`伝播、一度Gapとして発見され修正済み） | `route_open`（`ctx`プロパティ） | `GoogleMapRouteLink.tsx:16,29,71,91`; `docs/audit/compass-route-attribution-contract.md` |
| revisit（次月以降の再訪測定） | **MISSING**（測定手段が存在しない。月選択UI自体が無く、匿名/Free横断での識別子連携もない） | — | `docs/audit/compass-premium-personal-continuity.md` §15「no `posthog.identify()` linkage」 |
| premium関連event | **MISSING（該当機能が存在しないため）** | — | Compass自体にPremium Gateが存在しないため、Premium CTA/Paywall相当のEventも存在しない |

**追加所見（FACT）**: `docs/analytics/analytics-card-events.md`はArchive済みで現状の正本ではない。`docs/audit/cross-platform-event-contract.md`はMobileの一部カバレッジについて既に陳腐化している（本監査ではMobileを対象外とするため参考情報として記録するのみ）。`premium_active`はWeb/Mobile両方で同名イベントだがPayload形状が非互換という既知の不整合が`docs/analytics/monetization-funnel.md`に記録されている（Mobile側は本監査スコープ外のため詳細調査せず）。

**新規Event追加は本監査では行っていない。** 上記MISSING/PARTIALはすべて現状の記録であり、追加提案はSection 13 Decision Hに委ねる。

---

## 12. Web Test Release Readiness Matrix

| Area | Current State | Free | Premium | Web Test Release Ready | Evidence | Decision Required |
| --- | --- | --- | --- | --- | --- | --- |
| Concierge Core | 稼働中、ログイン不要、AllowAny | 完全アクセス可 | 完全アクセス可 | **YES** | Section 3, 5 | なし |
| Concierge Recommendation | 主導線は3件固定（Premium差なし）。別ページ`/plan`のみ3 vs 6 | 3件 | 3件（主導線）/6件（`/plan`のみ） | **YES**（技術的には安定動作） | Section 3, 4 | Decision A |
| Concierge Reason | ほぼ全文表示、1サブフィールドのみteaser | ほぼ全文 | 全文+内省的な問い | **YES** | Section 3 | なし |
| Shrine Detail | 全公開、Personalized supplementのみPremium（Concierge起点のみ確認） | 基本情報全公開 | +Personalized supplement | **YES** | Section 3 | なし |
| Route / Map | 完全公開 | Y | Y | **YES** | Section 3, 5 | なし |
| Favorite | ログイン必須、件数上限ポリシー未enforcement | 無制限（実質） | 無制限 | **PARTIAL** | Section 3, 14(Unresolved) | Decision B |
| Compass Core | Web実装・テスト完了、AllowAny、Gateなし | 完全アクセス可（匿名含む） | 差なし（意図的） | **YES** | Section 6, 8 | Decision C/D |
| Compass Result | 方向+参拝候補、Fail-safe状態も網羅 | Y | Y（差なし） | **YES** | Section 6 | Decision C/D |
| Compass → Shrine connection | Shrine Detail/Route遷移とAttribution実装済み | Y | Y | **YES** | Section 6, 8, 11 | なし |
| Billing | Stripe連携済み、Stub провайдерでテスト可能、DRF Permission Class不在でad-hoc gating | — | — | **YES**（Concierge/Plan/Favorite（未配線分除く）は動作確認済み） | Section 10 | Decision F |
| Premium CTA | Concierge結果画面・Shrine Detail双方に存在、Analytics一部欠落 | 表示される | — | **PARTIAL** | Section 11 | Decision H |
| Concierge Analytics | 主要導線EXISTING、開始/送信/Paywallイベントは MISSING | — | — | **PARTIAL** | Section 11 | Decision H |
| Compass Analytics | Entry/Result/Attribution EXISTING、Revisit/Premium系はMISSING（該当機能なしのため） | — | — | **PARTIAL** | Section 11 | Decision H |

判定値の定義: YES=技術的にRelease可能、PARTIAL=動作するが既知のギャップがある、NO=Blockerあり（本監査では該当なし）、UNKNOWN=判定に必要な情報が不足。

---

## 13. Mother Ship Decision Items

以下はいずれも本監査が発見したFACTに基づく論点整理のみである。**選択・推奨は行わない**（各Decisionの末尾に明記）。

### Decision A

**Question**: Concierge主導線（`/concierge/chat/`）における推薦件数を、Free/Premiumで差別化するか。

**Current FACT**: 主導線は現在Free/Premium/匿名すべてで3件固定（`concierge_chat_presentation.py:116-124`）。件数差はUIに存在せず、別ページ`/plan`（`ConciergePlanView`）にのみ3 vs 6の差が実装されている（`concierge_plan.py:549,583`）。

**Options**:
- (a) 主導線に件数差を導入する（`/plan`と同じ`recommend_limit_for_user()`を`build_chat_recommendations()`へ配線する）
- (b) 主導線は3件固定のまま維持し、件数差は`/plan`ページ固有の設計として現状追認する
- (c) `/plan`ページ自体の位置づけ（廃止/主導線への統合/独立維持）を再検討する

**Technical Impact**: (a)は`build_chat_recommendations()`のシグネチャ変更（plan引数の追加）と関連テストの更新を要する。(b)/(c)はコード変更不要。

**Product Impact**: 現状のままでは、Concierge主導線を使うユーザーにとって「件数」はPremiumの理由にならない。既存文書（`docs/product/premium-experience.md`）はPremium価値を件数ではなく「理由の深掘り」「相性」「継続文脈」に置いているため、この状態自体が既存Product方針と矛盾するとは限らない。

**Evidence**: Section 3, 4, 12。

**Unresolved**: 既存の別監査文書（`docs/audit/compass-free-premium-boundary.md`）が「3 vs 6 shown」と記録した経緯（当時の実装が現在と異なっていたのか、監査が主導線と`/plan`を混同していたのか）は特定できていない。

**Codex Recommendation**: `NONE`

### Decision B

**Question**: Favorite件数上限ポリシー（Free=10）を実装するか、ポリシー定義自体を削除して「無制限」を正式な仕様として追認するか。

**Current FACT**: `quota_policy.py`にポリシー定義はあるが、Favorite関連の全View（`FavoriteViewSet`, `FavoriteToggleView`等）のいずれからも呼び出されていない。現状は事実上無制限。

**Options**:
- (a) ポリシー通りFree=10件の上限を実装する
- (b) 「保存機能はPremium限定にしない」という`premium-experience.md`の既存原則と整合させ、無制限のまま正式仕様化しポリシー定義を更新する
- (c) 現状維持（判断を保留し、次回監査まで持ち越す）

**Technical Impact**: (a)はFavorite系Viewへの`check_quota`/`consume_quota`呼び出し追加を要する（未実装）。(b)は`quota_policy.py`のドキュメント/コメント更新のみ。

**Product Impact**: テストリリース時のドキュメントとコードの不一致が、QA/サポート対応時の混乱要因になり得る。

**Evidence**: Section 3, 4, 14(Unresolved#1)。

**Unresolved**: 意図的な緩和（無制限へ移行済みだがポリシー定義の掃除漏れ）なのか、実装漏れなのか、コード上は判別不能。

**Codex Recommendation**: `NONE`

### Decision C

**Question**: CompassをWeb Test Release時も全Freeで公開するか。

**Current FACT**: Compassは現在完全にFree・Gateなし（`AllowAny`）で稼働中。既存監査2本（`compass-free-premium-boundary.md`、`compass-premium-personal-continuity.md`）はいずれも「現時点でゲートを追加すべき根拠がない（利用実績が存在しないため）」と結論しており、この結論はコミット履歴上、本監査時点（`#2485`以降`#2615`まで）変更されていない。

**Options**:
- (a) 現状（全Free公開）のままWeb Test Releaseへ進める
- (b) Test Release期間中に限定的なGate（Section 7のPremium候補いずれか）を新設する
- (c) Test Release自体からCompassを除外する

**Technical Impact**: (a)は追加実装不要。(b)は新規実装（本監査では実施しない）。(c)はHome導線の一時的な非表示等が必要（実装は本監査スコープ外）。

**Product Impact**: 利用実績が無い状態でGateを新設することは、既存2監査が明示的に回避を推奨してきた判断である。

**Evidence**: Section 6, 7, 8。

**Unresolved**: なし（既存監査の結論がFACTとして再確認できている）。

**Codex Recommendation**: `NONE`

### Decision D

**Question**: CompassにTest Release前からFree/Premium境界を設定するか。

**Current FACT**: Section 7で分類した通り、CONTINUITY・CROSS_FEATURE（永続的接続）はいずれもNOT_IMPLEMENTED。PERSONALIZATION Signal（birthdate/purpose）は実装済みだが現状Freeで提供されている。USAGE_LIMITは現行なし。

**Options**:
- (a) 境界を設定しない（Decision Cの(a)と整合）
- (b) PERSONALIZATION Signalの一部をPremium化する
- (c) CONTINUITY/CROSS_FEATURE機能を新規実装した上でそれをPremium化する（実装が前提となるため、Test Release前には間に合わない可能性が高い）

**Technical Impact**: (b)は`QUOTA_POLICY`への`"compass"`キー追加、`CompassRecommendationsView`への`plan_context`配線が必要（Section 10のREUSABLEコンポーネントで対応可能）。(c)は新規モデル・マイグレーションを要する大規模実装。

**Product Impact**: Section 7 FREE_COREの範囲をPremium化した場合、Compassという体験そのものが成立しなくなるリスクがある（既存監査Model Aの「Feature Gate」評価が同じ懸念を既に指摘済み）。

**Evidence**: Section 7, 10。

**Unresolved**: Section 7 UNRESOLVED参照。

**Codex Recommendation**: `NONE`

### Decision E

**Question**: CompassのPremium候補を、PERSONALIZATION / CONTINUITY / CROSS_FEATURE / USAGE_LIMITのどこから構成するか。

**Current FACT**: Section 7の通り、PERSONALIZATIONのみ実装済みで現状Free提供。CONTINUITY・CROSS_FEATURE（永続的接続）はNOT_IMPLEMENTED。USAGE_LIMITは現行なし。

**Options**: 各カテゴリの組み合わせ（単独/複合）。実装コストは CONTINUITY > CROSS_FEATURE（永続化含む場合）> USAGE_LIMIT ≈ PERSONALIZATION（配線のみ）の順に高い。

**Technical Impact**: Section 7の各カテゴリ表を参照。

**Product Impact**: 既存監査（`compass-premium-personal-continuity.md`）はCONTINUITY（Save→Connect→Reflect→Compare）を「最も一貫性のある将来候補」と評価しているが、これは実装前提の将来案であり、Test Release時点では未実装。

**Evidence**: Section 7、`docs/audit/compass-premium-personal-continuity.md`。

**Unresolved**: Section 7 UNRESOLVED参照。

**Codex Recommendation**: `NONE`

### Decision F

**Question**: ConciergeとCompassで共通のPremium entitlement機構（`is_premium_for_user()`等）を将来利用するか。

**Current FACT**: 技術的には`is_premium_for_user()`・`resolve_plan_context()`・`check_quota()`はplan/feature非依存の汎用実装であり、`"compass"`をfeature文字列として追加すれば再利用可能（REUSABLE、Section 10）。ただし`QUOTA_POLICY`辞書・`CardId`共用体のいずれにもCompass用エントリは存在しない。

**Options**: (a) 既存の`is_premium_for_user()`/`quota_service`をそのまま再利用する設計とする、(b) Compass専用の別entitlement機構を新設する、(c) 判断を保留する。

**Technical Impact**: (a)は既存機構への軽微な拡張（feature文字列追加、View内呼び出し追加）で対応可能。(b)は新規実装。

**Product Impact**: 将来Compassへ課金境界を追加する際の実装コスト・一貫性に影響。

**Evidence**: Section 10。

**Unresolved**: なし。

**Codex Recommendation**: `NONE`

### Decision G

**Question**: Concierge / Compassの共通Premium価値原則を定義するか。

**Current FACT**: 現行`docs/product/premium-experience.md`はConcierge/Shrine Detail/Reflectionを対象としており、Compassには明示的に触れていない（Section 12「Free/Premium」がPaywall配置・価格・Entitlementの決定を将来へ委譲）。Section 9で確認した通り、両者はSHARED_LOGICを持ちながらDISTINCT_EXPERIENCEとして実装されている。

**Options**: (a) Compassを`premium-experience.md`の既存原則（深掘り・継続性・比較）にそのまま合流させる、(b) Compass専用の価値原則文書を新設する、(c) Test Release後の観測結果を待ってから定義する。

**Technical Impact**: なし（Product文書の話）。

**Product Impact**: 原則が未定義のまま個別にPremium機能を追加すると、Concierge側の既存禁止表現（「地図が高機能になる」等）と類似したCompass訴求文言が生まれるリスクが既存監査で指摘されている（`docs/product/compass-product-contract.md` Section 12）。

**Evidence**: Section 9、`docs/product/premium-experience.md`、`docs/product/compass-product-contract.md` Section 12。

**Unresolved**: なし。

**Codex Recommendation**: `NONE`

### Decision H

**Question**: Web Test Releaseで最重要KPIとして何を採用するか。

**Current FACT**: Section 11の通り、Concierge開始・Recommendation request・PaywallイベントはMISSING。Compassのrevisit測定もMISSING（識別子連携なし）。既存の主要導線（impression/shrine detail/route/favorite/premium CTA click）はEXISTING。

**Options**: (a) Test Release前に不足Eventを追加実装する、(b) Test Release後の観測フェーズで段階的に追加する、(c) 現状のEvent群で十分と判断し追加しない。

**Technical Impact**: (a)は新規Analytics Event実装（本監査では実施していない、禁止事項）。

**Product Impact**: Test Release期間中に「どこで離脱したか」「Paywallがどれだけ見られたか」を計測できるかどうかに直結する。

**Evidence**: Section 11。

**Unresolved**: なし。

**Codex Recommendation**: `NONE`

### Decision I

**Question**: CompassをComing Soon/hiddenにする必要が本当にあるか。

**Current FACT**: Compassは既に本番相当の実装（Backend/Frontend/Analytics）を持ち、Coming Soon状態のコードは存在しない（Section 6）。Home導線・Analytics計装（`home_compass_entry_click`等）は既に稼働中。

**Options**: (a) Coming Soon化しない（現状の完全公開のまま）、(b) Test Release期間中のみ一時的にComing Soon相当の表示へ切り替える（新規実装が必要、本監査は実装しない）。

**Technical Impact**: (b)は既存のHome導線・Analytics計装を無効化または条件分岐する新規実装が必要。

**Product Impact**: (b)を選んだ場合、既に実装・テスト・計装済みの機能を意図的に隠すことになり、Decision C/Dとの整合を要する。

**Evidence**: Section 6。

**Unresolved**: なし。

**Codex Recommendation**: `NONE`

---

## 14. Unresolved Items（コードからは判定不能な項目、Decision外の補足）

1. **Favorite件数上限（Free=10）が実装上どこからも呼び出されていない理由**（Decision Bの前提FACT）。
2. **`goshuin_upload`クォータも同様に未配線**（Favoriteと同一パターン、深く調査していない）。
3. **匿名Concierge利用のrate-limitテストの整合性** — `backend/temples/tests/test_concierge_rate_limit.py:131-154`（`test_guest_user_is_not_rate_limited`）が、`limit==3`を返しつつ7回連続リクエストでも`limitReached is False`をアサートしている。原因は本監査のコード直読だけでは確定できなかった。
4. **Reflection「前回との違い」比較機能のBackend側権限実装** — Frontend側の`isPremiumActive`分岐は確認したが、対応するBackend専用エンドポイントの権限制御は本監査の調査範囲では特定できなかった。
5. **`docs/analytics/compass-posthog-query-contract.md`が定義するクエリが実際にPostHog側で構築されているか** — リポジトリ内にdashboard-as-codeが存在しないため確認不能。
6. **Staffユーザーの自動Premium化の意図**（Section 4のUNCLEAR項目）。

---

## 15. Evidence / Files / Tests

### Backend

- `backend/temples/api_views_concierge.py`（Concierge Chat View、quota連携、九星/方位呼び出し）
- `backend/temples/services/concierge_chat.py`, `concierge_chat_presentation.py`, `concierge_chat_ranking.py`, `concierge_explanation_payload.py`, `concierge_input_contract.py`
- `backend/temples/services/concierge_plan.py`（別ページ用、件数差あり）
- `backend/temples/services/billing_state.py`, `plan_service.py`, `quota_policy.py`, `quota_service.py`
- `backend/temples/api_views_compass.py`, `services/compass_runtime.py`, `compass_direction_filter.py`, `compass_recommendation_orchestrator.py`
- `backend/temples/domain/kyusei.py`, `services/direction_reference.py`, `domain/astrology.py`, `domain/fortune.py`
- `backend/temples/api/views/billing.py`, `services/billing_checkout.py`, `users/services/stripe_webhook.py`
- `backend/temples/api/views/favorite.py`, `reflection.py`, `visit.py`, `shrine.py`
- テスト: `backend/temples/tests/test_concierge_rate_limit.py`, `tests/api/test_billing_status_contract.py`, `test_compass_recommendations_api.py`, `tests/services/test_compass_runtime.py`, `test_compass_direction_filter.py`, `test_compass_recommendation_orchestrator.py`, `tests/services/test_kyusei_direction.py`, `test_direction_reference.py`, `test_concierge_eval_queries.py`

### Frontend（Web）

- `apps/web/src/app/concierge/ConciergeClientFull.tsx`, `features/concierge/components/ConciergeSectionsRenderer.tsx`, `PremiumStateDeltaCard.tsx`, `DirectionReferenceCard.tsx`
- `apps/web/src/app/compass/page.tsx`, `features/compass/CompassClient.tsx`他Compassコンポーネント群
- `apps/web/src/app/plan/PlanView.tsx`, `api/conciergePlan.ts`
- `apps/web/src/lib/premium/accessLevel.ts`, `cardVisibility.ts`
- `apps/web/src/lib/api/billing.ts`, `features/billing/hooks/useBilling.ts`, `app/api/billings/status/route.ts`, `app/api/billings/checkout/route.ts`
- `apps/web/src/lib/analytics/searchEvents.ts`, `cardEvents.ts`, `directionEvents.ts`, `track.ts`
- `apps/web/src/components/shrine/GoogleMapRouteLink.tsx`
- `apps/web/e2e/05_direction_flow.spec.ts`

### 参照した既存正本/監査文書（重複作成を避けるため確認済み）

- `docs/product/premium-experience.md`, `billing-paywall.md`, `pricing.md`（Archive）, `monetization-flow-design.md`
- `docs/product/compass-product-contract.md`, `compass-mvp-runtime-contract.md`, `compass-product-direction-decision.md`
- `docs/audit/compass-free-premium-boundary.md`（Phase 7）, `compass-premium-personal-continuity.md`（Phase 7続編）
- `docs/audit/concierge-compass-product-responsibility-contract.md`, `concierge-compass-meaning-action-authority-boundary.md`, `compass-contract-reconciliation-direction-audit-completion.md`
- `docs/audit/compass-full-experience-qa.md`, `compass-route-attribution-contract.md`
- `docs/analytics/compass-analytics-contract.md`, `compass-posthog-query-contract.md`, `monetization-funnel.md`
- `docs/audit/README.md`（audit配下の読み方契約）

---

## 責務境界

本書は「現行repoの事実の収集・分類（Web版のみ）」を責務とする。以下は本書の対象外であり、実施していない。

- Free/Premium境界の変更・決定
- Compassの実装・Coming Soon UIの実装
- Billingロジック・Recommendation Ranking/Score・Direction Logic/Compass Logic・Analytics Event/Payload・API Response Schemaの変更
- Mobile対応案・Mobile実装タスク・Mobile Premium Gate・Mobile Release Readinessの設計・実装
- Product仕様の推測による更新、Release Scopeの自動決定
- Section 13に列挙したDecision Itemsの選択

## 更新ルール

- 本書は時点記録（Historical）であり、以降の実装変更によって内容は陳腐化しうる。継続的な更新は行わない。
- Section 13のDecision Itemsが確定した場合、その決定は別途Product文書（`docs/product/premium-experience.md`等）またはPhase 7相当の新規監査で記録し、本書へ遡及反映はしない。
