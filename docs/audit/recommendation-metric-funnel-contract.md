# Recommendation Metric / Funnel Contract Audit

## 1. Purpose

PR #2429 merge後のRecommendation event contractを対象に、イベントの存在ではなく、正しい分母・分子・Recommendation instance identity・Web/Mobileの意味一致を監査した。

本監査はread-onlyである。基準HEADは`develop`の`bd25827fed0002986745cff4bb8a354dd071d11b`。production code、event schema、writer、Ranking、Learning weight、UI、migrationは変更しない。

## 2. Canonical Funnel Definition

Recommendation funnelを次のように定義する。

```text
recommendation rendered impression
  -> recommendation detail-transition click
  -> detail page view
  -> route open / save
  -> visit persisted
  -> reflection persisted
```

- ImpressionとClickのcanonical measurement storeはWeb/Mobile analytics provider（現行PostHog provider）。Backend DBには対応するimpression writerがない。
- Detail/Routeはanalytics eventと`ShrineInteractionLog`の二重経路を持つ。
- Save/Visit/Reflectionはanalytics eventと各domain model（`Favorite` / `Visit` / `ShrineReflection`）の二重経路を持つ。
- `ActionEvent`はAction Suggestionのstart/complete用であり、通常のRecommendation Clickや全route/save/visitの代替ではない。
- `ConciergeRecommendationClickLog`はmodel/migrationのみでproduction writerがない。現行click measurementが成立しているため、本監査は新writer追加を前提にしない。

## 3. Event and Field Inventory

記号: `Y`=常に契約上存在、`C`=recommendation contextがある場合のみ、`N`=存在しない、`W/M`=Web/Mobile差分。

| Funnel stage | Canonical event / persistence | Writer | threadId | shrineId | rank | primaryReasonSource | fallback | actionSource | actionSourceKeys |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Impression | `concierge_result_impression` | Web `ConciergeSectionsRenderer`; Mobile `ConciergeScreen` | Web C / Mobile N | Y | Y | C | C | C | C |
| Recommendation Click | `shrine_detail_transition` | Web/Mobile recommendation card handler | Web C / Mobile N | Y | Y | C | C | C | C |
| Detail View analytics | `shrine_detail_view` | Web `ShrineDetailViewTracker`; Mobile `trackShrineDetailView` | Web C / Mobile N | Y | Web N / Mobile metadata `recommendation_rank` | C | C | C | C |
| Detail View learning record | `ShrineInteractionLog(detail_view)` | `/shrine-interactions/` | Web C / Mobile N | Y | Web N / Mobile metadataのみ | metadata C | metadata C | metadata C | metadata C |
| Route Open analytics | `route_open` | Web `GoogleMapRouteLink`; Mobile `trackRouteOpen` | Web C / Mobile N | Y | N | C | C | C | C |
| Route Open learning record | `ShrineInteractionLog(route_open)` | `/shrine-interactions/` | Web C / Mobile N | Y | Web N / Mobile metadataのみ | metadata C | metadata C | metadata C | metadata C |
| Save analytics | `favorite_click`（追加は`nextFav=true`）/ Webは`shrine_decision(action=save)`も送信 | Web/Mobile detail screen | Web C / Mobile N | Y | N | C | C | C | C |
| Save learning record | `Favorite` | favorites API | N | Y | N | N | N | N | N |
| Visit analytics | `visit_done` | Web/Mobile detail screen | Web C / Mobile N | Y | N | C | C | C | C |
| Visit learning record | `Visit(status=added)` | visit API | Web C / Mobile N | Y | N | N | N | N | N |
| Reflection analytics | `reflection_saved` | Web/Mobile reflection UI | Web C / Mobile N | Y | N | C | C | C | C |
| Reflection learning record | `ShrineReflection` | reflection API | Web C / Mobile N | Y | N | N | N | N | N |
| Action start/complete | `ActionEvent` DB（Mobileのみproduction caller） | Mobile recommendation Action CTA | N | C | metadata `rank` | metadata C | metadata C | metadata `action_source` | metadata `source_keys` |

### Field naming parity

PostHog系eventではPR #2429の共通helperにより`primaryReasonSource`、`isFallbackRecommendation`、`actionSource`、comma-separated `actionSourceKeys`の意味はWeb/Mobileで一致する。

ただしBackend JSON metadataでは命名が統一されていない。

- Web `ShrineInteractionLog.metadata`: camelCase properties
- Mobile detail/route metadata: provenanceはcamelCaseだがidentityは`recommendation_rank` / `result_set_id`
- Mobile `ActionEvent.metadata`: `primary_reason_source` / `is_fallback_recommendation` / `action_source` / `source_keys`

値のAuthority contractは一致するが、warehouse/dashboard側でevent family別のfield mappingなしにunionできない。

## 4. Impression Contract

### Actual trigger

Webは`ConciergeSectionsRenderer`がrecommendation sectionをrenderし、React `useEffect`が実行された時点で、section内の全registered itemについて送信する。Mobileも`results` stateが非空になりscreen effectが実行された時点で全itemを送信する。

したがって現行impressionの意味は次のとおり。

| Candidate definition | 該当 |
|---|---|
| 1. API responseに含まれた | 部分的。normalize後にregistered recommendationとして採用されたもの |
| 2. DOM/native view treeへrenderされた | **最も近い正本** |
| 3. viewportへ実際に表示された | **No** |

compact itemがfold下にあっても全件impressionになる。IntersectionObserver、Viewability callback、可視時間、visibility percentageは使用していない。またWebはregistered itemだけを対象とするため、raw API response全件を分母にするeventでもない。

### Denominator judgment

- 「rendered result CTR」の分母としては使用可能。
- 「viewable impression CTR」「実際に見た候補のCTR」の分母としては使用不可。
- rank別比較ではfold下のrankほど未視認impressionが多くなり得るため、rank effectとvisibility effectを分離できない。
- component instance内では`resultSetId + shrineId + position + rank`で重複送信を抑止するが、reload/remount/session跨ぎを一意化するBackend IDではない。

## 5. Click Contract

### Event separation

| Interaction | Event | Recommendation Clickに含めるか |
|---|---|---|
| Recommendation card/heroから詳細へ遷移 | `shrine_detail_transition` | **Yes (canonical)** |
| 詳細画面の表示成立 | `shrine_detail_view` | No。Click後の別段階 |
| Action Suggestion preview/CTA | `action_suggestion_*`, `ActionEvent` | No。Action funnel |
| 詳細画面のroute/save/visit CTA | 各downstream event | No |
| 一般一覧/地図のcard click | `shrine_card_click` | No。Recommendation result由来とは限らない |

### Canonical suitability

`shrine_detail_transition`はRecommendation cardのclick handlerでのみ送信され、`resultSetId`、`shrineId`、`recommendationRank`、Authority/grounding propertiesをimpressionと同じ形で持つ。よってRecommendation Clickのanalytics正本として利用できる。

制約:

- client analytics delivery failure時もnavigationは継続するため、clickはbest-effortである。
- actual navigation completionではなくclick intentを測る。
- `firstClick`はresult set内の最初のclickを示すが、通常CTRでは全clickまたはdistinct recommendation clickのどちらを用いるか明示が必要。
- `ConciergeRecommendationClickLog` writer不在はPostHog CTRを否定しない。ただしBackend snapshotとのFK joinはできない。

## 6. Recommendation Identity and Joinability

### Impression -> Click

**Joinable / metric-ready.** Web/Mobileとも`resultSetId + shrineId + recommendationRank`を共有し、Authority/grounding propertiesも同一helperから出る。

ただし`resultSetId`はBackend IDではなく`threadId-or-unknown + ordered shrine IDs`のFrontend合成値である。

- Webはthread IDをprefixに持つ。
- Mobileは常に`unknown` prefix。
- 同じordered shrine IDsが再度返ると同一IDになり、異なるrecommendation generationを区別できない。
- Web `recommendation_quality`はraw recommendations、renderer impressionはregistered itemsからIDを作るため、place recommendation混在時にsignatureが一致しない可能性がある。

CTR集計はevent時刻/sessionを併用し、`resultSetId`をglobal unique IDとして扱わない必要がある。

### Click -> Detail and beyond

**Not strictly joinable.** Authority valuesは伝播するがinstance identityが揃わない。

- Web detail/route/save/visit/reflectionは`threadId + shrineId`を持つが`resultSetId/rank`を持たない。
- Mobile detail Backend metadataだけが`result_set_id/recommendation_rank`を持つ。Mobile PostHog detail eventでは同値がsnake_caseで、route/save/visit/reflection PostHogにはidentityがない。
- Mobileは`threadId`を推薦responseから保持していない。
- 同一threadで同一shrineが複数回推薦された場合、Webの`threadId + shrineId`ではgenerationを区別できない。
- reload、戻る、再訪でdetail viewは複数発生し得るため、clickとの1:1対応ではない。

結論: Authority別のdownstream event countは観測可能だが、「同一Recommendation impressionを母集団にしたconversion」の厳密joinはできない。

## 7. Required Metric Assessment

| Metric | Judgment | Valid definition / blocker |
|---|---|---|
| Recommendation CTR | **GO (rendered CTR)** | `distinct shrine_detail_transition / distinct concierge_result_impression`を同じplatform、session/time window、`resultSetId+shrineId+rank`で集計。viewable CTRとは呼ばない |
| Primary Authority別CTR | **GO (rendered CTR)** | 両eventの`primaryReasonSource`をそのままgroup。unknown/nullを除外せず別bucketにする |
| fallback別CTR | **GO (rendered CTR)** | `isFallbackRecommendation`でgroup。nullはfalseへcoalesceしない |
| Authority別Detail View Rate | **NO-GO for strict conversion** | detailにAuthorityはあるが`resultSetId/rank`欠落。descriptive event ratioは可能だがRecommendation instance conversionではない |
| Route Open Rate | **CONDITIONAL** | 詳細到達者を分母にしたplatform/Authority別のdescriptive rateは可能。Recommendation impressionからのstrict conversionは不可 |
| Save Rate | **CONDITIONAL** | analyticsはprovenanceを持つ。追加率は`favorite_click nextFav=true`または`shrine_decision action=save`に限定。DB `Favorite`はprovenanceを持たない |
| Visit Conversion | **NO-GO for recommendation conversion** | analyticsにAuthorityはあるがinstance identity欠落。DB VisitはWebのみthreadを持ちMobileはnull、provenanceなし |
| Reflection Rate | **NO-GO for recommendation conversion** | analyticsにAuthorityはあるがinstance identity欠落。DB reflectionもMobile threadなし、provenanceなし |
| Action Grounding別行動率 | **NO-GO as causal Action conversion** | detail CTAの通常行動にもcurrent recommendationのAction provenanceが付くため、そのAction suggestionが行動を起こしたことを示さない |
| generic_safe vs grounded比較 | **CONDITIONAL as association only** | `actionSource=fallback` vs `actionSourceKeys` containing `ranked_history_theme`等のcohort比較は可能。ただしAction CTA由来の因果CVとは表現しない |

### Numerator/denominator rules

- CTR numeratorは`shrine_detail_transition`。`shrine_detail_view`や`shrine_card_click`を混ぜない。
- CTR denominatorは`concierge_result_impression`のdistinct recommendation instance。raw event count比はrerender/remount差を受けるため不可。
- Save numeratorは追加のみ。`favorite_click`全件にはremoveも含まれる。
- Route/Visit/Reflectionをdetail countで割る既存`build_score_v3_funnel_correlation_summary()`はuser/shrine/time範囲の相関値であり、sequential unique-user funnelではない。複数eventにより100%超過し得る（既存debug UIもreflectionについて明記）。
- `actionSourceKeys`はcomma-separated string。substringではなくsplit後のexact keyで分類する。
- `actionSource=fallback`はgeneric-safe/fallback provenanceを表すが、全Action taxonomyを完全に表す新enumではない。

## 8. Web / Mobile Semantic Parity

### Aligned

- impression/click event names
- `shrineId`, `recommendationRank`, Frontend合成`resultSetId`
- `primaryReasonSource`, `isFallbackRecommendation`, `actionSource`, `actionSourceKeys`の意味
- Impressionがviewportではなくrendered resultである点
- route/save/visit/reflectionのanalytics provenance

### Gaps

1. Web impression/result identityはthread IDを持つがMobileは`unknown`。
2. Web downstreamはcamelCase event fields、Mobile Backend metadataにはsnake_case identity/action fieldsが混在する。
3. Web detail pageはthread snapshotからprovenanceを復元する。Mobileはroute paramsのFact/previewを消費する。
4. Web Visit/Reflection persistenceはthread IDを送れる。Mobile APIsはthread IDを送らない。
5. Mobile ActionEvent production writerはあるがWeb ActionEvent production callerは確認できない。
6. Mobile route PostHogはprovenanceを持つが`resultSetId/rank`を持たず、Backend route metadataだけがそれらを持つ。

Web/Mobileを同じdashboardで集計する場合は`platform`で分離検証し、欠損fieldをfalse/zeroへ補完しないこと。

## 9. Learning Signal Boundary

Analytics emissionとRanking feedback persistenceは別経路である。

| Behavior | Analytics emission | Persistence used by ranking | Join/provenance consequence |
|---|---|---|---|
| detail_view | PostHog `shrine_detail_view` | `ShrineInteractionLog(detail_view)` | metadataにprovenanceはあるがRankingはuser+shrine+recencyだけを読む |
| route_open | PostHog `route_open` | `ShrineInteractionLog(route_open)` | 同上 |
| save | `favorite_click` / `shrine_decision` | `Favorite` | Favoriteにrecommendation provenanceなし |
| visit | `visit_done` | `Visit(status=added)` | Web threadのみ保持可能。Rankingはuser+shrine+recencyを読む |
| reflection | `reflection_saved` | `ShrineReflection` | Web threadのみ保持可能。Rankingはuser+shrine+recencyを読む |
| Action complete | Mobile `ActionEvent(action_completed)` | `ActionEvent` | action suggestion ID/metadataあり。Rankingはuser+shrine+recencyのcompletion signalを読む |

`calculate_shrine_behavior_signal_breakdown()`はdetail count×0.2、route count×0.6、save 1.5、visit 3.0、reflection 4.0、action completion 2.0をrecency付きで集約し、合計をcapする。これは既存Learning Signal behaviorであり、本監査はweightを変更しない。

重要な境界:

- Analytics側provenanceがRanking入力へ直接渡るわけではない。
- Ranking feedbackはAuthority/grounding別にweightを変えない。
- Backend domain recordsとPostHog eventはcanonical event IDを共有しないため、delivery差分をevent単位で照合できない。
- `behavior_funnel.py`はuser/shrine/time集計であり、Recommendation instance funnelではない。

## 10. Schema, Writer, and Identity Gaps

1. Impressionはviewport visibilityを測らない。
2. `resultSetId`はFrontend合成でgeneration nonce/backend recommendation log IDではない。
3. Mobile `resultSetId`はthread prefixが常に`unknown`。
4. Web qualityとimpressionでresult set構成対象が異なる可能性がある。
5. Web detail以降に`resultSetId/rank`がない。
6. Mobile route/save/visit/reflection PostHogに`resultSetId/rank/threadId`がない。
7. Backend domain recordsの大半にAuthority/Action groundingがない。InteractionLog metadataだけが例外。
8. Web/Mobile/ActionEvent metadataのcamelCase/snake_caseが統一されていない。
9. Recommendation Action起点と通常detail CTA起点を示す`actionSuggestionId`がroute/save/visitへ伝播しない。
10. `ConciergeRecommendationClickLog`はwriter不在だが、PostHog click contractは成立している。問題はwriter不在単独ではなくBackend snapshotとのcanonical join ID不在である。
11. analytics deliveryとDB persistenceの成功/失敗を結ぶevent IDがない。
12. anonymous impression/clickと認証後Learning recordを同一identityへ結べない。

## 11. Dashboard Decision

## CONDITIONAL GO

次の限定dashboard/KPI分析へは進める。

- rendered Recommendation CTR
- Primary Authority別rendered CTR
- fallback別rendered CTR
- platform別・Authority別downstream eventのdescriptive counts/rates
- generic-safe vs grounded cohortの**association comparison**

次は現contractではGOにしない。

- viewport/viewable CTR
- impressionからReflectionまでのstrict sequential funnel
- Recommendation instance単位のAuthority別Detail/Visit/Reflection conversion
- Action suggestionがroute/save/visitを引き起こしたとするGrounding別causal CV
- Web/Mobileをidentity normalizationなしで合算した単一KPI

Dashboardには少なくとも次のguardrailを明記する。

1. Impression labelを`rendered_recommendation_impression`相当として説明し、viewableと呼ばない。
2. CTRはimpression/clickの同一platform・同一event schema内だけで算出する。
3. null Authority/fallbackをunknown bucketとして保持する。
4. downstreamは`conversion`ではなく`observed action rate`と表示する。
5. Action grounding比較はassociationでありcausal attributionではないと表示する。
6. Backend behavior funnelとPostHog recommendation funnelを同じ分母のmetricとして混ぜない。

## 12. Follow-up Decision Points

production変更案は本監査の範囲外。母艦で判断が必要な論点のみ記録する。

1. Viewable impressionを新正本にするか、rendered impressionを正式KPI定義として維持するか。
2. Backend recommendation log IDまたはgeneration IDをcanonical `resultSetId`にするか。
3. Detail以降へinstance identityを伝播する範囲とretention/privacy contract。
4. Action起点行動だけを結ぶ`actionSuggestionId` propagationが必要か。
5. PostHogをKPI正本、Backend DBをLearning正本として明示的に分離するか、warehouseでevent-level reconciliationするか。
6. `ConciergeRecommendationClickLog`を配線、legacy宣言、削除のどれにするか。writer不在だけを理由に配線しない。
