# Web・Mobile共通Analyticsイベント契約 — 監査 & Target設計

本ドキュメントは以下の4段階で構成する。

1. **Current State（事実）** — コード調査に基づく確認済みの現状(file:line付き)
2. **Issues（確認された問題）** — Current Stateから導かれる、優先度付きの問題点
3. **Target Funnel（目標）** — プロダクト全体を貫く一本道のイベント契約案(未実装・提案)
4. **Property Contract（今後）** — Target Funnelを支える共通Property契約案(未実装・提案)
5. **PostHog Dashboard Design** — Target Funnel/Property Contractを前提としたDashboard設計案(未実装・提案)

Current State以外(Issues以降)はすべて「事実」ではなく「提案」であり、実施の可否・優先順位・命名の最終決定は別途意思決定を要する。本ドキュメント自体は監査と設計案の提示のみを目的とし、実装コードへの変更は含まない。

## Scope

- 対象: `apps/web`(Next.js)、`apps/mobile`(Expo/React Native)、`backend`(Django)
- 目的: PostHog上でWeb/Mobileのユーザー行動を単一Funnelとして集計できるようにするための、既存イベント名・payload・送信経路の棚卸しと、共通Property契約・Target Funnel・Dashboard設計への橋渡し
- 調査対象ドメイン: `consultation` / `recommendation` / `shrine_detail` / `route_open` / `visit` / `reflection` / `premium`
- 非対象: コード変更、イベント名の改名実施、新規実装

---

# Phase 1: Current State（事実）

### 送信基盤の事実確認

| 項目 | Web | Mobile | Backend |
|---|---|---|---|
| Analytics SDK | `posthog-js`導入済み(`apps/web/src/lib/analytics/providers.ts`) | 導入済み(`posthog-react-native@^4.55.0`、`apps/mobile/lib/posthogAnalyticsProvider.ts`) | 未導入(`grep -rniE "posthog" backend/` 0件) |
| エントリポイント | `track()` — `apps/web/src/lib/analytics/track.ts:74` | `track()` — `apps/mobile/lib/analytics.ts:75` | なし |
| 本番でPostHogへ到達するか | する(`NODE_ENV==="production"`かつ`NEXT_PUBLIC_POSTHOG_KEY`設定時、`providers.ts:23-38`) | Preview/Production相当(`__DEV__===false`)かつ`EXPO_PUBLIC_POSTHOG_KEY`設定時は`PostHogAnalyticsProvider`へ切り替わる(`initAnalyticsProvider()` — `posthogAnalyticsProvider.ts:34`、`app/_layout.tsx:20-22`で起動時に1回呼び出し)。EAS Preview環境変数は設定済み(EAS Dashboard側の設定のためコードからは直接確認不可)。Apple Developer Program未加入のためiOS実機での受信確認は未実施 | 該当なし |
| session_id/sessionId除外 | **されない**。`track.ts:78-83`が全イベントに`analyticsSessionId`と`sessionId`(legacy互換)を**自動付与**してPostHogへ送信 | **される**。`analytics.ts:41`の`serializeAnalyticsPayload`が`session_id`/`sessionId`に加え`checkout_session_id`/`checkout_url`/`token`/`access_token`/`refresh_token`(camelCase含む、`analytics.ts:19-31`)を構造的に除外 | 該当なし |

**最重要の事実**: Mobile PostHog Providerは接続済み。`posthog-react-native`を利用した`PostHogAnalyticsProvider`(`apps/mobile/lib/posthogAnalyticsProvider.ts`)により、Preview/Production相当ではPostHogへイベント送信が可能になった。EAS Preview環境変数も設定済み。残る未確認事項はApple Developer Program加入後のiOS実機での受信確認のみである。

---

## Web Events

`apps/web/src/lib/analytics/`配下に5つの送信経路がある。`track.ts`経由(自動sessionId付与あり)と、`searchEvents.ts`/`cardEvents.ts`/`retentionEvents.ts`/`billing.ts`が`getAnalyticsProvider().track()`を直接呼ぶ経路(自動付与なし、個別にthreadId等を手動付与)に分かれる。

### consultation

| イベント名 | file:line | payload keys |
|---|---|---|
| `consultation_completed` | `ConciergeClientFull.tsx:1198` | threadId, mode, flow, hasBirthdate, recommendationCount, historyTheme, consultationAxis?, source |
| `filter_result` | `ConciergeClientFull.tsx:1211` | source, threadId, mode, recommendation_count(snake_case混在), is_zero_result, hasFilter |
| `consultation_theme_click` | `ConciergeClientFull.tsx:1486` | label, text(相談テーマの定型文コピー), source |
| `action_suggestion_preview_view` | `ConciergeTopRecommendationHero.tsx:120` | source, threadId, resultSetId, shrineId, recommendationRank, position, historyTheme, actionSuggestionVersion, primaryActionType, secondaryActionType, actionPromptType, actionSource, sourceKeys, summaryLine |
| `action_suggestion_reflection_preview_view` | `ConciergeTopRecommendationHero.tsx:123`（訂正: 初回監査時は`reflection_prompt_view`(concierge文脈)として誤記録していたが、実際のイベント名は別物） | 上記 + reflectionPromptSourceSeed |
| `concierge_result_impression` | `ConciergeSectionsRenderer.tsx:358` | source, threadId, resultSetId, shrineId, position, recommendationRank, mode, historyTheme, consultationAxis? |
| `shrine_detail_transition` | `ConciergeSectionsRenderer.tsx:847,983` | source, threadId, resultSetId, position, recommendationRank, shrineId, mode, flow, hasBirthdate, recommendationCount, historyTheme, consultationAxis?, firstClick |
| `recommendation_quality` | `features/concierge/hooks.ts:140` | source, threadId, shrineId, recommendationRank, accessLevel, shrine_data_rate等snake_caseメトリクス群 |
| `posthog_health_check` | `app/providers/ClientBootstrap.tsx:19` | source:"client_bootstrap"(プロダクトイベントではなく起動時のProvider自己診断) |

うち `card_view`/`card_cta_click`/`card_partial_view`/`card_teaser_view`/`save_prompt_view`/`save_prompt_click` は`cardEvents.ts`の`trackCardEvent()`経由(consultation/recommendation両ドメインに跨って`ConciergeSectionsRenderer.tsx`・`ConciergeClientFull.tsx`から多数呼び出し、約19箇所)。

**未使用(dead)として確認された宣言済みイベント名**: `shrine_search` / `map_search` / `action_suggestion_view` / `action_suggestion_click` / `action_started` / `action_completed` / `action_done` / `primary_action_click` / `secondary_action_click`(`searchEvents.ts`の型union上に存在するが呼び出し元0件)。うち`action_started`/`action_completed`はPostHog経路(`trackSearchEvent`)としては未使用だが、同名の`action_type`値がBackend `ActionEvent`モデル経由でMobile Conciergeから`POST /api/action-events/`へ送信・DB永続化されている、PostHogとは無関係の別系統として存在する(詳細: `docs/analytics/action-suggestion-funnel.md`)。

### recommendation

`cardEvents.ts`の`trackCardEvent()`経由で `shrine_hero` / `shrine_compact` / `other_shrines` / `shrine_meaning` / `action_meaning` / `recommendation_meta` / `previous_comparison` 等の`cardId`に対する`card_view`/`card_teaser_view`/`card_partial_view`(`ConciergeSectionsRenderer.tsx:508-700`付近)。

| イベント名 | file:line | payload keys |
|---|---|---|
| `shrine_decision` | `ConciergeClientFull.tsx:1522`, `ShrineSaveButton.tsx:65` | shrineId, action("route"/"save"/"map_search"), rank?, tid/ctx, consultationAxis? |
| `premium_preview_click` | `ConciergeSectionsRenderer.tsx:~185`, `ShrineDetailArticle.tsx:191` | cardId:"premium_preview", source, accessLevel, visibility:"teaser", ctaType, shrineId, historyTheme, threadId |

### shrine_detail

| イベント名 | file:line | payload keys |
|---|---|---|
| `shrine_detail_view` | `components/shrine/ShrineDetailViewTracker.tsx:22` | source, shrineId(num), threadId? |
| `shrine_card_click` | `components/shrines/ShrineCard.tsx:219` | source:"shrines", shrineId |
| `empty_state_view` | `app/shrines/page.tsx:136` | source:"shrines", query(検索文字列そのまま) |
| `add_shrine_click` | `app/shrines/page.tsx:188` | source, query(検索文字列そのまま), returnTo(URL) |
| `card_view`/`card_partial_view`(context_reason等) | `ShrineDetailArticle.tsx:134,511-560` | cardId, source:"shrine_detail", accessLevel, visibility, shrineId, historyTheme, payloadSource |

**Backendへの二重書き込み**: `ShrineDetailViewTracker.tsx:28`は同一の閲覧を`trackShrineInteraction({shrineId, actionType:"detail_view", ...})`としてBackend `shrine-interactions/` APIへも同時POSTしている(PostHog + 自社DBの二重記録)。

### route_open

| イベント名 | file:line | payload keys |
|---|---|---|
| `route_open` | `components/shrine/GoogleMapRouteLink.tsx:32` | source:"shrine_detail", routeTarget:"google_maps", shrineId, threadId, historyTheme, ctx |

同ファイル43行目で`trackShrineInteraction({actionType:"route_open", ...})`によるBackendへの二重書き込みも確認(shrine_detailと同じ二重記録パターン)。

### visit

| イベント名 | file:line | payload keys |
|---|---|---|
| `visit_done` | `components/shrine/detail/ShrineDetailArticle.tsx:724` | source:"shrine_detail", shrineId, threadId, historyTheme, ctx |

### reflection

| イベント名 | file:line | payload keys |
|---|---|---|
| `reflection_prompt_view` | `components/shrine/detail/ShrineReflectionPrompt.tsx:32` | source, shrineId, threadId, historyTheme, promptType, ctx |
| `reflection_saved` | `components/shrine/detail/ShrineReflectionPrompt.tsx:57` | source, shrineId, threadId, historyTheme, promptType, answerLength(num), **moodBefore**, **moodAfter**, ctx |
| `premium_history_comparison_view`/`_click` | `features/concierge/components/PremiumStateDeltaCard.tsx:33,70` | source, hasSummary, hasCombinationChange, combinationChanged, hasTransitionNarrative, transitionType, changedNeedTagCount, continuedNeedTagCount, daysSincePrevious, within7DaysSincePrevious, funnelStep |

**要注意事実**: `reflection_saved`の`moodBefore`/`moodAfter`は自由入力欄の値がそのままPostHogへ送信されている(バリデーション・列挙値化なし)。振り返り本文(`answer`)自体は`answerLength`(文字数)のみで本文は送っていないが、気分入力欄は未加工の自由記述であり、調査中で見つかった中で最も機微度が高いフィールド。

### premium(Web)

`billing.ts`の`trackBillingEvent()`は送信前に`session_id`/`sessionId`キーを明示的にstrip(`billing.ts:56`)する独自ガードを持つ(Web内で唯一sessionId除外を自前で行っているモジュール)。

| イベント名 | file:line | payload keys |
|---|---|---|
| `upgrade_click` | `app/billing/upgrade/page.tsx:67` | source, funnelStep, cardId, historyTheme |
| `checkout_started` | `app/billing/upgrade/page.tsx:87` | **checkoutSessionId**, source, funnelStep, cardId, historyTheme |
| `checkout_success` | `app/billing/success/page.tsx:73` | **checkoutSessionId**, source, funnelStep, cardId, historyTheme |
| `premium_active` | `app/billing/success/page.tsx:83` | **checkoutSessionId**, source, funnelStep, cardId, historyTheme(checkout_successと同一shape) |
| `premium_history_click` | `features/concierge/components/ThreadList.tsx:79`(`trackRetentionEvent`経由) | source:"thread_list", funnelStep:"history_comparison" |

**要注意事実(重大)**: `checkout_started`/`checkout_success`/`premium_active`の3イベントすべてが`checkoutSessionId`をpayloadに含めてPostHogへ送信している。これは本監査の除外対象リストにある`checkout_session_id`に該当し、現状のWeb実装はこの契約に違反している。

Web全体で確認できた「実際に呼び出されているイベント名」の総数: **34**(うち`posthog_health_check`を含む)。加えて宣言済みだが呼び出し元0件の「死んだ」イベント名が10件、`conciergeDecisionSummary.ts`が参照するが発火元が見当たらないイベント名が3件(`concierge_return_after_detail`, `concierge_result_click`, `concierge_premium_click`)存在する。

---

## Mobile Events

Mobileで`track()`が呼ばれているのは**premiumドメインのみ**。他の6ドメインは調査の結果、計測コードが一切存在しないことを確認した(スクリーン自体は存在するが`analytics`/`track`のimportがない)。

`PostHogAnalyticsProvider`(`apps/mobile/lib/posthogAnalyticsProvider.ts:13`)が実装済み。`initAnalyticsProvider()`(同ファイル:34)が`app/_layout.tsx:20-22`のアプリ起動時`useEffect`から一度だけ呼び出される。development時または`EXPO_PUBLIC_POSTHOG_KEY`未設定時は既定の`ConsoleAnalyticsProvider`へfallbackし、Preview/Production相当(`__DEV__===false`)かつkey設定時のみ`PostHogAnalyticsProvider`へ切り替わる。EAS Preview環境変数は設定済み(EAS Dashboard側の設定のためコードからは直接確認不可)。Apple Developer Program未加入のためiOS実機でのPostHog受信確認は未実施。

| イベント名 | track()呼び出し | wrapper呼び出し元 | payload keys |
|---|---|---|---|
| `premium_screen_view` | `lib/premiumAnalytics.ts:12` | `app/premium/index.tsx:102` | source:"mobile_premium", platform:"mobile" |
| `premium_status_view` | `lib/premiumAnalytics.ts:16-21` | `app/premium/index.tsx:117` | plan, isActive, provider, source |
| `premium_upgrade_click` | `lib/premiumAnalytics.ts:25` | `app/premium/index.tsx:171` | plan:"free"(固定), source |
| `premium_checkout_started` | `lib/premiumAnalytics.ts:29` | `app/premium/index.tsx:180` | source |
| `premium_checkout_failed` | `lib/premiumAnalytics.ts:33` | `app/premium/index.tsx:193,211` | source, failureType("unauthenticated"\|"invalid_response"\|"open_url_failed"\|"unknown") |
| `premium_checkout_returned` | `lib/premiumAnalytics.ts:39` | `app/premium/index.tsx:154` | source |
| `premium_active` | `lib/premiumAnalytics.ts:47-52` | `app/premium/index.tsx:118`(plan==="premium" && is_active===trueのみ発火) | plan:"premium"(固定), isActive:true(固定), provider, source |

全イベントが`SOURCE = "mobile_premium"`固定値を共有(`lib/premiumAnalytics.ts:7`)。`session_id`/`sessionId`/`checkout_session_id`/`checkout_url`/`token`/`access_token`/`refresh_token`(camelCase含む)は`analytics.ts:19-31`の`EXCLUDED_PAYLOAD_KEYS`によりserializerレベルで構造的に除外されている(payload組み立て側の実装ミスに依存しない)。

**計測ゼロを確認したドメイン(6件)**:

| ドメイン | 該当画面(未計装) |
|---|---|
| consultation | `app/concierge/index.tsx`, `app/consultation-history/index.tsx` |
| recommendation | 専用画面なし(Journey機能内に折り込まれている可能性、`lib/journey.ts`も未計装) |
| shrine_detail | `app/shrines/[id].tsx` |
| route_open | `app/shrines/[id].tsx:521-535`(`Linking.openURL`によるGoogle Maps遷移ロジックは存在するが未計装) |
| visit | `app/visit-history/index.tsx`, `app/records/index.tsx`, `lib/visits.ts` |
| reflection | `app/journey/index.tsx`, `app/reflection-history/index.tsx`, `lib/journey.ts`, `lib/reflections.ts` |

Mobileで確認できたイベント名の総数: **7**(すべてpremiumドメイン)。PostHogへの到達経路(Provider接続)は確立済みである。

---

## Backend Records

Backendにはanalytics SDKの統合は一切なく(`posthog`等の依存なし、確認済み)、以下はすべて「ビジネスレコード」としてのDjangoモデルであり、汎用的な`AnalyticsEvent`/`EventLog`テーブルは存在しない。PKはPlaceRef.place_idを除き全て`BigAutoField`(整数連番)。

| ドメイン | モデル | file:line | 相関用ID |
|---|---|---|---|
| consultation | `ConciergeThread` | `backend/temples/models.py:425` | `id`(int) ≒ Web/Mobileの`threadId` |
| consultation | `ConciergeMessage` | `backend/temples/models.py:469` | `thread`(FK) |
| recommendation | `ConciergeRecommendationLog` | `backend/temples/models_concierge_analytics.py:6` | `thread`(FK, nullable) |
| recommendation | `ConciergeRecommendationClickLog` | `backend/temples/models_concierge_analytics.py:42` | `shrine_id`(IntegerField、**実FKではない緩い参照**) |
| recommendation | `ConciergeHistory` / `ActionEvent` | `backend/temples/models.py:722` / `:602` | `shrine`(FK, nullable) |
| shrine_detail | `Shrine`(マスタ) | `backend/temples/models.py:221` | `id`(int) ≒ `shrineId` |
| shrine_detail / route_open | `ShrineInteractionLog`(1モデルで両ドメインを兼ねる。`action_type`が`detail_view`/`route_open`/`shrine_card_click`) | `backend/temples/models.py:558` | `shrine`(FK), `thread`(FK, nullable) |
| visit | `Visit` | `backend/temples/models.py:505` | `id`(int)、`shrine`(FK)、`user`(FK) |
| reflection | `ShrineReflection` | `backend/temples/models.py:522` | `shrine`(FK)、`user`(FK)。**`visit`へのFKが存在しない** |
| premium | `UserProfile`(専用Billingモデルなし) | `backend/users/models.py:5` | `plan`/`is_active`は非永続(リクエスト時に`billing_state.py:16-22`で計算されるdataclass) |

**premium/billingの機微フィールド(正確なフィールド名、除外対象)**: `UserProfile.stripe_customer_id`(`backend/users/models.py:17`)、`UserProfile.stripe_subscription_id`(同:18`)、`UserProfile.stripe_price_id`(同:19)。`CheckoutSession`(`session_id`, `checkout_url`)は永続化されないdataclass(`backend/temples/services/billing_checkout.py:14`)。

---

## Cross-platform Event Mapping

「同一のユーザー行動」を軸に、Web/Mobileのイベント名を対応付けた事実整理(=名前が違うだけで意味が対応するもの)。★は名前が同じだが意味・payloadが食い違う衝突箇所。

| ユーザー行動 | Webイベント名 | Mobileイベント名 | 対応状況 |
|---|---|---|---|
| Premium画面/ページ表示 | (該当なし) | `premium_screen_view` | Mobileのみ存在 |
| 現在のプラン状態表示 | (該当なし) | `premium_status_view` | Mobileのみ存在 |
| アップグレードボタン押下 | `upgrade_click` | `premium_upgrade_click` | 意味は対応、名前不一致 |
| Checkout開始 | `checkout_started` | `premium_checkout_started` | 意味は対応、名前不一致。**Webはpayloadに`checkoutSessionId`を含む(除外対象違反)** |
| Checkout成功/復帰 | `checkout_success` | `premium_checkout_returned` | **名前だけでなく意味が非対称**。Webは(Stripeのsuccess_url到達という)決済成功シグナル、Mobileは単なるAppState復帰検知であり決済成功を証明しない。同一視して集計すると誤ったFunnelになる |
| Checkout失敗 | (該当なし) | `premium_checkout_failed` | Mobileのみ存在 |
| Premium有効化確認 | `premium_active` ★ | `premium_active` ★ | **イベント名が完全一致しているがpayload形状が別物**(Web: checkoutSessionId/funnelStep/cardId/historyTheme、Mobile: plan/isActive/provider)。PostHog上でこの名前のイベントを見ると、由来がWebかMobileかでフィールドの意味が変わる |
| 神社詳細閲覧 | `shrine_detail_view` | (該当なし) | Webのみ存在 |
| ルートを開く | `route_open` | (該当なし) | Webのみ存在 |
| 参拝記録 | `visit_done` | (該当なし) | Webのみ存在 |
| 振り返り保存 | `reflection_saved` | (該当なし) | Webのみ存在 |
| 相談完了 | `consultation_completed` | (該当なし) | Webのみ存在 |
| 提案表示/クリック | `card_view`ファミリー / `shrine_decision` | (該当なし) | Webのみ存在 |

---

## Payload Mapping

premiumドメインを軸にした、フィールド単位の対応表(事実)。

| 意味 | Webフィールド名 | Mobileフィールド名 | 型 | 一致状況 |
|---|---|---|---|---|
| 発生源識別 | `source`(値は"shrine_detail"等、画面ごとに可変) | `source`(値は"mobile_premium"固定) | string | 名前は同じだが値の設計思想が違う(Web=画面文脈、Mobile=プラットフォーム固定値) |
| プラットフォーム識別 | フィールド自体が存在しない | `platform: "mobile"`(premium_screen_viewのみ) | string | **Webには相当するフィールドが一つも存在しない** |
| プラン状態 | (billing系イベントに独立フィールドなし) | `plan` | string("free"\|"premium") | Mobileのみ |
| 有効フラグ | (なし) | `isActive` | boolean | Mobileのみ。BackendのAPIは`is_active`(snake_case)だが、Mobileのwrapperが`isActive`へ変換して送信(`lib/premiumAnalytics.ts:18`) |
| プロバイダ | (なし) | `provider` | string | Mobileのみ |
| Checkoutセッション識別子 | `checkoutSessionId` | 明示的に除外(analytics.tsのserializerで構造的に不可能) | string | **Webは除外対象フィールドを送信中** |
| 神社ID | `shrineId`(camelCase, PostHogペイロード) / `shrine_id`(snake_case, Backend直POST時) | (未使用) | number | Web内で命名規則が不統一 |
| スレッドID | `threadId` | (未使用) | number | Webのみ使用中 |

---

## Missing Events

| ドメイン | 欠損箇所 | 備考 |
|---|---|---|
| consultation | Mobile全体 | 相談画面自体は存在するが計装なし |
| recommendation | Mobile全体 | 専用画面が見当たらない |
| shrine_detail | Mobile全体 | `app/shrines/[id].tsx`は存在するが未計装 |
| route_open | Mobile全体 | Google Maps遷移ロジックは実装済みだが未計装 |
| visit | Mobile全体 | 参拝記録画面・APIは存在するが未計装 |
| reflection | Mobile全体 | Journey/振り返り画面群は存在するが未計装 |
| premium: 画面表示(`_screen_view`相当) | Web | `/billing/upgrade`ページの表示自体をトラッキングするイベントが見当たらない |
| premium: 現在プラン表示(`_status_view`相当) | Web | 相当するイベントが見当たらない |
| premium: Checkout失敗 | Web | `premium_checkout_failed`に相当するWebイベントが見当たらない |
| reflectionとvisitの相関 | Backend | `ShrineReflection`に`visit`へのFKがなく、特定の参拝記録と振り返りイベントをID単位で突き合わせる手段がDB上に存在しない |

---

## Duplicate Events

| 内容 | 詳細 |
|---|---|
| `premium_active`の名前衝突 | Web/Mobile双方が同名イベントを異なるpayload形状で送信(Cross-platform Event Mapping参照)。PostHog上で名前ベースに集計すると誤集計になる |
| `shrine_detail_view`の二重記録 | Web: PostHogへの`track()`呼び出しと、Backend `shrine-interactions/`への`trackShrineInteraction()`POSTが同一クリックに対して両方発生(`ShrineDetailViewTracker.tsx:22,28`) |
| `route_open`の二重記録 | 同様にPostHog `track()` + Backend `shrine-interactions/`への二重POST(`GoogleMapRouteLink.tsx:32,43`) |
| `checkout_success`と`premium_active`の重複 | Webの`app/billing/success/page.tsx`内で、73行目と83行目が実質同一payload(checkoutSessionId/source/funnelStep/cardId/historyTheme)を持つ2つの別イベント名として発火している |
| Web宣言済みだが未使用のイベント名(13件) | `shrine_search`, `map_search`, `action_suggestion_view`, `action_suggestion_click`, `action_started`, `action_completed`, `action_done`, `primary_action_click`, `secondary_action_click`, `premium_preview_view`, `next_session`, `next_thread`, `comparison_preview` — 型定義上は存在するが呼び出し元0件。うち`action_started`/`action_completed`はPostHog経路としては未使用(Backend `ActionEvent`モデルの`action_type`値としては使用中、Web側からの送信元は0件) |
| 発火元不明の参照イベント名(3件) | `conciergeDecisionSummary.ts`が`concierge_return_after_detail`/`concierge_result_click`/`concierge_premium_click`を参照しているが、これらを発火するコードが見当たらない(集計ロジックが常にゼロを返している可能性) |

---

## Privacy / Excluded Fields

以下は本監査で指定された除外対象リストと、現状実装の突き合わせ結果(事実)。

| 除外対象フィールド | Web現状 | Mobile現状 | Backend現状 |
|---|---|---|---|
| access token / refresh token | 送信箇所は確認されなかった | serializerで構造的に除外済み(`analytics.ts:19-31`、`token`/`access_token`/`accessToken`/`refresh_token`/`refreshToken`) | 該当なし(SDK未統合) |
| session_id | 送信箇所は確認されなかった | serializerで構造的に除外(`analytics.ts:19-31,41`) | 該当なし |
| sessionId | **`track.ts:78-83`が全イベントへ自動付与し、production時にPostHogへ送信される**(唯一の重大な違反) | serializerで構造的に除外 | 該当なし |
| checkout_session_id / checkoutSessionId | **`checkout_started`/`checkout_success`/`premium_active`の3イベントで送信されている**(重大な違反) | serializerで構造的に除外済み(`analytics.ts:19-31`) | 該当なし |
| checkout_url | 送信箇所は確認されなかった | serializerで構造的に除外済み(`analytics.ts:19-31`、`checkoutUrl`も含む) | 該当なし |
| Stripe customer ID | 送信箇所は確認されなかった | 送信箇所は確認されなかった | `UserProfile.stripe_customer_id`はDB保存のみ、analyticsへの参照なし |
| Stripe subscription ID | 送信箇所は確認されなかった | 送信箇所は確認されなかった | `UserProfile.stripe_subscription_id`はDB保存のみ、analyticsへの参照なし |
| 相談本文 | `consultation_theme_click`の`text`は定型文コピー(自由記述ではない)。相談の自由入力自体を送るイベントは確認されなかった | 該当イベントなし | 該当なし |
| 振り返り本文 | `reflection_saved`は`answer`本文ではなく`answerLength`(文字数)のみ送信 | 該当イベントなし | 該当なし |
| メールアドレス / 氏名 / 生年月日 | 直接送信は確認されなかったが、`hasBirthdate`(生年月日の有無を示すbooleanフラグ)が`consultation_completed`/`shrine_detail_transition`で繰り返し送信されている(生年月日そのものではないが、隣接する属性の存在漏洩) | 該当イベントなし | 該当なし |

**追加で確認された機微フィールド(除外対象リストには明記されていないが要検討)**: `reflection_saved`の`moodBefore`/`moodAfter`は未加工の自由入力文字列であり、振り返り本文と同種の機微性を持つ可能性がある。

---

# Phase 1.5: Issues（確認された問題）

Current Stateの事実から導かれる問題点を優先度別に整理する。優先度・対応方針はすべて**提案**であり、実施の可否・順序は別途意思決定が必要。

## P0（データ汚染・プライバシー違反 — 即対応を推奨）

1. **`checkoutSessionId`の除外対象違反** — Webの`checkout_started`/`checkout_success`/`premium_active`が`checkoutSessionId`をPostHogへ送信している(`apps/web/src/app/billing/upgrade/page.tsx:87`, `apps/web/src/app/billing/success/page.tsx:73,83`)。除外対象リストの`checkout_session_id`に直接該当
2. **`premium_active`の名前衝突** — Web/Mobileが同名イベントを非互換なpayload形状で送信中。現状PostHog上でこのイベント名は集計不能な状態にある(Cross-platform Event Mapping参照)

## P1（設計の不整合・機微データの懸念）

3. **Webの`sessionId`自動付与** — `track.ts:78-83`が全イベントに`sessionId`を自動付与しPostHogへ送信している。既存の`docs/analytics/analytics-payload-audit.md`に設計意図の記載があり意図的な可能性があるため、削除の是非はプロダクト/プライバシー判断が必要
4. **`moodBefore`/`moodAfter`の自由記述漏洩** — `reflection_saved`(`ShrineReflectionPrompt.tsx:57`)が未加工の自由入力文字列をPostHogへ送信。列挙値化または除外を検討
5. **`platform`フィールドがWebに存在しない** — Mobileの`platform:"mobile"`に対応するフィールドがWeb側の全イベントに存在せず、PostHog上でプラットフォーム別Funnelを作れない
6. **Mobile Provider接続済み** — `posthog-react-native`により`PostHogAnalyticsProvider`(`apps/mobile/lib/posthogAnalyticsProvider.ts`)が実装され、Preview/Production相当では実際にPostHogへ到達するようになった。残課題はApple Developer Program加入後のiOS実機での受信確認のみ

## P2（データ整備・技術的負債）

7. **Mobile 6ドメインの計装欠如** — Provider統合(PostHog接続)は完了した。残る作業はconsultation/recommendation/shrine_detail/route_open/visit_done/reflection_savedをTarget Funnelの順序(Phase 2参照)で実装することである
8. **`shrineId`/`shrine_id`のcasing不統一** — Web内でPostHog payload(camelCase)とBackend直POST(snake_case)の命名規則が食い違っている
9. **未使用・発火元不明のイベント名** — 宣言済みだが呼び出し元0件のイベント名10件、発火元不明の参照イベント名3件、dead wrapperモジュール2件(`analytics/actionEvents.ts`, `api/actionEvents.ts`)
10. **`ShrineReflection`に`visit`へのFKがない** — 振り返りイベントと特定の参拝記録をID単位で相関する手段がDB上に存在しない(`backend/temples/models.py:522`)

## P3（ドキュメント化・将来検討）

11. **`shrine_detail_view`/`route_open`のPostHog+Backend二重記録** — 用途の違い(PostHog=プロダクト分析、ShrineInteractionLog=レコメンドスコアリング信号)を前提とした意図的な設計である可能性が高いが、明文化されていない

## 名前衝突・命名不一致への対応方針(Option A / Option B)

**Option A: イベント名を実装側で統一** — Web/Mobile両方のコードを変更し、同一行動には同一イベント名・同一payload形状を採用する。1イベント名=1意味が保証される一方、両アプリのコード変更と既存Dashboard/Insightの移行調整が必要。**`premium_active`の名前衝突はOption Bでは解決できず、この1件は実装側の改名が必須**と考えられる。

**Option B: PostHog集計側でマッピング** — コードは変更せず、PostHog側のActions/Insightで複数イベント名を1つの論理アクションとして束ねる。即座に着手可能でコード変更不要な反面、マッピング表の継続的な保守が必要で、payload形状が異なる名前衝突ケース(`premium_active`)には使えない。

**方向性の提案**: 全面的な名前統一(Option A)を今すぐ実施するのではなく、まずP0(`premium_active`衝突・`checkoutSessionId`漏洩)を個別PRで是正し、それ以外の名前不一致は当面Option Bで運用しつつ、Mobileの計測範囲拡大(P2 #7)のタイミングで下記のTarget Funnel/Property Contractに合わせて命名を揃えるのが現実的と考える。

---

# Resolved Since Initial Audit

初回監査後に解消済みの項目と、残る未完了項目の整理。

## 完了

- Mobile PostHog Provider接続(`apps/mobile/lib/posthogAnalyticsProvider.ts`)
- serializer除外キー拡張(`apps/mobile/lib/analytics.ts:19-31`)
- EAS Project作成(`apps/mobile/app.json`の`extra.eas.projectId`)
- Preview環境変数設定(EAS Dashboard側の設定のためコードからは直接確認不可)
- Bundle Identifier: `com.morietsu.kamimusubi`(`apps/mobile/app.json`)
- Mobile Premiumイベント送信基盤

## 未完了

- Apple Developer Program加入
- iOS Preview実機確認
- consultation
- recommendation
- shrine_detail
- route_open
- visit_done
- reflection_saved

---

# Phase 2: Target Funnel（目標）

これは**現状の実装一覧ではなく、目標とするイベント契約**である。プロダクト全体を「相談 → 提案 → 神社詳細 → ルート → 参拝 → 振り返り → Premium化」という一本道として捉え、Web/Mobile共通のイベント名で表現する。今後の実装は、この一本道を基準として追加・整理する。

```text
consultation_started
        ↓
recommendation_view
        ↓
shrine_detail
        ↓
route_open
        ↓
visit_done
        ↓
reflection_saved
        ↓
premium_upgrade_click
        ↓
premium_checkout_started
        ↓
premium_checkout_returned
        ↓
premium_active
```

## 現状との差分(Current State → Target)

| Target Funnelのイベント名 | Web現状 | Mobile現状 | 差分の性質 |
|---|---|---|---|
| `consultation_started` | `consultation_completed`(完了時点で発火、開始イベントはない) | 未実装 | Webは名前・発火タイミングとも異なる。改名+開始時点への発火タイミング変更が必要 |
| `recommendation_view` | `concierge_result_impression` / `card_view`ファミリーが相当 | 未実装 | Webは相当イベントが複数に分散しており、統合が必要 |
| `shrine_detail` | `shrine_detail_view` | 未実装 | Webは名前がほぼ一致(`_view`サフィックスの有無のみ) |
| `route_open` | `route_open`(一致) | 未実装 | Webは名前一致。Mobile新規実装が必要 |
| `visit_done` | `visit_done`(一致) | 未実装 | Webは名前一致。Mobile新規実装が必要 |
| `reflection_saved` | `reflection_saved`(一致) | 未実装 | Webは名前一致。Mobile新規実装が必要 |
| `premium_upgrade_click` | `upgrade_click` | `premium_upgrade_click`(一致) | Webは改名が必要 |
| `premium_checkout_started` | `checkout_started`(+除外対象違反の`checkoutSessionId`あり) | `premium_checkout_started`(一致) | Webは改名+privacy是正が必要 |
| `premium_checkout_returned` | `checkout_success`(意味が非対称、Issues #2参照) | `premium_checkout_returned`(一致) | 単純改名では不可。Web/Mobileで意味の擦り合わせが前提 |
| `premium_active` ★ | `premium_active`(名前は一致だがpayload非互換、Issues #2参照) | `premium_active`(一致) | P0で個別対応が必要な衝突箇所 |

Target Funnelは「新しいイベント名を思いつきで置く」のではなく、上表の通り**既存実装との対応関係を確認した上で**設計している。Web側は7イベント中5イベントで改名または統合が必要、Mobile側はpremium以外の6イベントすべてが新規実装となる。

---

# Phase 3: Property Contract（今後）

Cross-platform Analyticsの共通Property契約案。

| Property | Purpose | Web | Mobile | Backend | Target |
|----------|---------|-----|--------|----------|--------|
| platform | プラットフォーム識別 | 未実装 | 実装済み | - | Web / Mobile共通 |
| source | 画面・導線識別 | 実装済み | 実装済み | - | 共通命名 |
| threadId | 相談スレッド相関 | 実装済み | 未実装 | ConciergeThread.id | camelCase |
| shrineId | 神社相関 | 実装済み | 未実装 | Shrine.id | camelCase |
| historyTheme | 推薦文脈 | 実装済み | 未実装 | 派生値 | 共通Property候補 |
| provider | Billing Provider | 未実装 | 実装済み | UserProfile | Billingのみ |
| plan | Premium Plan | 未実装 | 実装済み | Billing State | Billingのみ |
| isActive | Premium状態 | 未実装 | 実装済み | Billing State | Billingのみ |

### 方針

Propertyはイベントごとに自由に増やすのではなく、Cross-platformで意味を統一する。

目的は

- Funnel分析
- Breakdown
- Dashboard

を共通化することである。

---

# Phase 4: PostHog Dashboard Design

### Primary Funnel

- consultation_started
- recommendation_view
- shrine_detail
- route_open
- visit_done
- reflection_saved
- premium_upgrade_click
- premium_checkout_started
- premium_checkout_returned
- premium_active

### Breakdown

以下を共通Propertyとして利用する。

- platform
- source
- historyTheme
- provider

### KPI

優先的に監視する指標。

- Consultation Completion Rate
- Recommendation → Detail CTR
- Detail → Route Open Rate
- Visit Completion Rate
- Reflection Completion Rate
- Premium Upgrade Rate
- Premium Activation Rate

### Monitoring

継続監視対象。

- Duplicate Event
- Missing Event
- Payload Contract Violation
- Event Name Drift
- Property Contract Drift

本ドキュメントは監査結果を保持しつつ、将来のAnalytics設計・Dashboard設計への橋渡しを目的とする。
