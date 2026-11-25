# Recommendation Instance Identity Propagation Design

## 1. Purpose

`docs/audit/recommendation-metric-funnel-contract.md`（PR #2430）は、Recommendation
funnelをCONDITIONAL GOと判定した。Impression→Clickはjoin可能だが、Detail以降は
Authority/provenanceを保持してもRecommendation instance identityが一貫しない、
というのが核心の結論である。

本書は、その結論を受けて、

```text
Impression → Click → Detail → Route/Save → Visit → Reflection
```

までRecommendation instance identityを保持できる**最小Contract**を設計する。

本書はdesign auditのみである。production code、event schema、writer、DB schema、
Ranking、UIは一切変更しない。基準HEADは`develop`の
`2b027c0bbf1ec8a35e934e6d48d421673c241b09`（PR #2430マージ直後）。

## 2. Existing Funnel Contract（PR #2430からの要約）

PR #2430で確定した事実のみを引き継ぐ（詳細はPR #2430を正本とし、本書では再定義
しない）。

- Canonical funnel: `impression -> click -> detail view -> route/save -> visit ->
  reflection`。
- Impression/ClickのCanonical measurement storeはPostHog（Web/Mobile）。Backendに
  対応するimpression writerはない。
- Impression→Clickは`resultSetId + shrineId + rank`でjoin可能。
- Click→Detail以降はAuthority/grounding値は伝播するが、instance identityが揃わず
  strict joinできない。
- Dashboard判定はCONDITIONAL GO（rendered CTR / Primary Authority別CTR / fallback
  別CTRのみGO。viewable CTR、strict sequential funnel、Recommendation instance単位の
  Authority別Detail/Visit/Reflection conversionはNO-GO）。

## 3. Current Identity Inventory

### 3.1 Frontend合成`resultSetId`

共有helper `packages/shared/recommendationAnalyticsProvenance.ts:80-88`:

```ts
export function buildRecommendationResultSetId(threadId, recommendations): string {
  const signature = recommendations
    .map((item, index) => `${index + 1}:${item.shrineId ?? "unknown"}`)
    .join("|");
  return `${threadId ?? "unknown"}:${signature || "empty"}`;
}
```

- Web: 実threadIdを渡す（`ConciergeSectionsRenderer.tsx:305,375-377`）。
- Mobile: 常にリテラル`null`を渡す（`apps/mobile/app/concierge/index.tsx:679-682,
  833-836`）。したがってMobileの`resultSetId`は常に`unknown:`prefixになる。
  Mobile concierge画面はAPI responseからthreadIdを一切保持していない（grep
  で`thread_id`/`threadId`/`.thread`参照なし）。
- 同じordered shrine IDsが再度返ると同一IDになり、別generationを区別できない
  （PR #2430と一致）。

### 3.2 Backendの未活用ID: `rid`

`backend/temples/api_views_concierge.py:507`:

```python
rid = uuid.uuid4().hex[:8]
```

`/api/concierge/chat/`のPOSTごとに1つ生成される。現状は約15箇所のserver-side
logging（`rid=%s`）にのみ使われる。

成功パス（`api_views_concierge.py:1010-1026`）で
`debug={"rid": rid, "before": ..., "after": ..., "applied": ..., "flow": ..., "mode":
...}`が`_build_chat_response(..., debug=debug, ...)`へ渡る。`_build_chat_response()`
（320-368行）は`body["_debug"] = debug`（361-362行）をセットする。これは`data.pop
("_debug", None)`（340行、`recs`自体が内部で持つ別の`_debug`をpopする処理）とは
別物であり、**popされない**。`Response(body, status=...)`（1035行）は`body`を
そのまま返す。

**確認事項: `rid`は現在すでにclientへ到達している**（`response.body._debug.rid`、
quota上限到達時の早期returnを除く全成功応答）。frontendのどこからも読まれていない
（PR #2419のfield trace結果と整合: `_`-prefixのbackend内部fieldは読まれていない）。

制約: 8 hex文字 = 32bit。厳密な一意性保証ではないが、本アプリの想定規模での
join用途には十分。暗号学的な一意性としては扱わないことをRiskとして明記する
（§14）。

### 3.3 `rid`は現状threadへ永続化されない

`api_views_concierge.py:895-916`: `thread_recommendations = recs.get
("recommendations") or []`; `append_chat(..., recommendations=
thread_recommendations, recommendations_v2=thread_recommendations_v2)`は
`ConciergeThread.recommendations` / `.recommendations_v2`（既存JSONField）へ
recommendation item一覧（各shrineのrec dict）を永続化する。

`rid`はview層の変数であり、`build_chat_recommendations()`が返す`recs`辞書の
一部ではない。したがって**現状`rid`はthread snapshotへ含まれない**。後日
thread snapshotを読み返すページ（shrine detail等）は、どの`rid`がその
snapshotを生成したか復元できない。

### 3.4 未配線だがすでに存在するDB schema

`backend/temples/models_concierge_analytics.py`:

```python
class ConciergeRecommendationLog(models.Model):
    id = ...  # auto PK
    thread = models.ForeignKey("temples.ConciergeThread", ...)
    query, need_tags, flow, llm_enabled, llm_used
    recommendations = models.JSONField(...)  # snapshot
    result_state = models.JSONField(...)
    lat, lng, radius_m
    created_at

class ConciergeRecommendationClickLog(models.Model):
    recommendation_log = models.ForeignKey("temples.ConciergeRecommendationLog", ...)
    user, thread
    shrine_id, place_id, rank
    created_at
```

`ConciergeRecommendationLog.id`は、Option Cが求める「backend発行のimmutableな
per-generation ID」の形そのものであり、**すでにmigration済み**である。
`ConciergeRecommendationClickLog`も`recommendation_log`FK + `shrine_id/place_id/
rank`を持つ。

PR #2430 §2/§10-10で確認済みの通り、この2モデルには**production writerが
存在しない**（`.objects.create(...)`の呼び出し箇所がコード中に見つからない）。
つまりDB側のrecommendation-instance identity schemaはすでに存在し、Option Dは
新規migrationを要求せずとも「writerを配線する」だけで到達できる可能性がある
（本書はwriter追加を禁止事項としているため実装しないが、コスト評価として
重要な事実）。

### 3.5 Downstream domain modelsのidentity granularity

`backend/temples/models.py`:

| Model | thread FK | metadata JSONField | rank/resultSetId専用field |
|---|---|---|---|
| `Favorite`（576-606） | なし | なし | なし |
| `Visit`（691-712） | あり（703行、コメント"Recommendation Snapshotへの接続キー"） | なし | なし |
| `ShrineReflection`（716-745） | あり（733行） | なし（`history_theme`スナップショットfieldはある） | なし |
| `ShrineInteractionLog`（760-790） | あり（782行） | あり（789行） | なし（metadata内でのみ可能） |
| `ActionEvent`（804-845） | あり（828行） | あり（844行） | なし（metadata内でのみ可能） |

`ShrineReflection.history_theme`は「生成時点のcontextをsnapshotとして持つ」という
既存前例であり、Option B/Cの設計判断（新FKを作らずsnapshot fieldへ埋め込む）を
正当化する既存パターンである。

`Favorite`/`Visit`/`ShrineReflection`にはmetadata JSONFieldが無いため、Option B
（既存metadata利用）だけではこの3モデルへrecommendation-instance粒度のidentityを
持たせられない。`thread`粒度のidentityはすでにある（Visit/ShrineReflectionのみ、
Favoriteは無し）。

## 4. Impression Identity

- Web: `concierge_result_impression`イベントは`resultSetId`（実threadId由来）、
  `shrineId`、`recommendationRank`を持つ（`ConciergeSectionsRenderer.tsx:385-391`）。
- Mobile: 同型イベントだが`resultSetId`は`unknown:`prefix固定。
- Identity source: 完全にfrontend合成。Backend側に対応するimpression writerは
  ない（PR #2430と一致）。

## 5. Click Identity

- Web/Mobileとも`shrine_detail_transition`イベントに`resultSetId`、`shrineId`、
  `recommendationRank`を持つ（Web: `ConciergeSectionsRenderer.tsx:925-931`、
  Mobile: `apps/mobile/app/concierge/index.tsx:837-843`）。
- Impression→Clickはplatform内で`resultSetId + shrineId + rank`によりjoin可能
  （PR #2430の結論と一致、本書で再確認）。

## 6. Detail Identity

- Web `ShrineDetailViewTracker.tsx:18-45`: `threadId`/`tid` + Authority/grounding
  propertiesのみ。**`resultSetId`/rankは無い。**
- Mobile `apps/mobile/app/shrines/[id].tsx:404-413`: `resultSetId`/
  `recommendation_rank`は route params（`params.resultSetId`,
  `params.recommendationRank`）経由で**存在する場合がある**。ただしnative top-level
  identityではなく、navigationがそれらを運んだ場合のみ。
- Web detail pageの`_explanation_payload`/`recommendation_reason_v4`等provenance
  復元は、`ctx === "concierge" && tid`が揃った場合のみthread snapshotから行われる
  （`apps/web/src/app/shrines/[id]/page.tsx:309`、`normalizeCtx`は`ctx`を
  `"map"|"concierge"|null`に制限、52-54行）。**この条件がDeep Link Boundaryの
  既存実装である**（§7参照）。
- 例外（Risk、§14）: `ctx === "concierge" && !tid`（`tid`欠落）でも
  synthetic genericな`conciergeExplanationPayload`が注入される
  （`page.tsx:363-384`）。thread未検証のprovenance-shaped dataが漏れる余地。
- Mobileは`shrine?.reasonFacts`へのfallbackを持つが、backendの
  `ShrineDetailSerializer`（`backend/temples/api/serializers/shrine.py:199`）が
  `reason_facts`を含まないため、このfallbackは現状inert（潜在的だが未発火）。

## 7. Route / Save Identity

- Web `GoogleMapRouteLink.tsx`（route open）、`ShrineSaveButton.tsx:18,63,76`
  （save）: いずれも`tid`（threadId）+ `shrineId` + provenance flagsのみ。
  **`resultSetId`/rankは両方とも無い。**
- Mobile `trackRouteOpen`（`apps/mobile/lib/searchAnalytics.ts:52-63`）:
  `shrineId` + provenance flagsのみ。`threadId`すら持たない。
- 結論: Route/SaveではWebは`threadId`粒度、Mobileは**identityなし**まで
  劣化する。

## 8. Visit Identity

- Analytics: Web/Mobileとも`visit_done`イベントを送るが、Mobile側
  （`apps/mobile/app/shrines/[id].tsx:463-469`）はthreadId/resultSetId/rankを
  一切持たない。Webは`tid`のみ。
- DB persistence: `Visit.thread`（FK）は存在するが、Mobile側のvisit作成API呼び出し
  `apps/mobile/lib/visits.ts:33-38`（`createVisitByShrineId`）は
  `{shrine_id, visited_at}`のみをPOSTしており、**backendがthread_idを受け付ける
  余地があってもMobileは送っていない**（PR #2430 §8 Gap 4と一致）。
- 結論: WebのみVisitに`thread`粒度のidentityが付く可能性がある。
  Recommendation-instance粒度のidentityはWeb/Mobileどちらにもない。

## 9. Reflection Identity

- Visitと同型のパターン。`ShrineReflection.thread` FKはあるが、Mobile側からは
  populateされない（Mobile reflectionフロー`apps/mobile/app/shrines/[id].tsx:
  498-502,517-523`にthreadId/resultSetId送信なし）。`history_theme`
  スナップショットのみ生成時点contextとして残る。

## 10. Identity Loss Points（統合）

| Stage遷移 | 保持されるもの | 失われるもの |
|---|---|---|
| Impression -> Click | `resultSetId + shrineId + rank`（platform内） | なし（この区間はjoin可能） |
| Click -> Detail | Web: `threadId`のみ。Mobile: route params経由でresultSetId/rankが**時々**残るが保証なし | `resultSetId`/`rank`のnative保証（両platform）。Mobileの`threadId`（元々ない） |
| Detail -> Route/Save | Web: `threadId`のみ。Mobile: なし | `resultSetId`/`rank`（両platform）。Mobileの`threadId` |
| Route/Save -> Visit | Web: `threadId`（analytics）。DB `Visit.thread`はWebのみ理論上到達可能だがMobile APIが送らない | `resultSetId`/`rank`（両platform）。Mobile analytics/DBのidentity全て |
| Visit -> Reflection | Visitと同型 | 同上 |

一貫して失われるのは**「同一threadで複数回生成されたRecommendationのうち、
どのgenerationが今回のDetail/Route/Save/Visit/Reflectionを引き起こしたか」**
という、rank以下の粒度（=recommendation instance identity）である。`threadId`
（Webのみ）は「どの相談から来たか」までは保持するが、「どのrender/generation
から来たか」は保持しない。

### Deep Link Boundary

#### 定義

「Recommendation経由のdetail/route/save/visit」と「直接開いたdetail/route/save/
visit」を区別する条件を、以下のように定義する。

**あるdetail view（以降のroute/save/visit/reflectionも同様）がRecommendation
funnel numeratorに算入されるための条件:**

1. ページ遷移が`ctx=concierge`クエリパラメータを伴っていること（Webの既存実装
   `page.tsx:309`が示す通り、これは既にproduction code上の実際の条件である）。
2. `threadId`（`tid`）が存在し、かつBackend上に実在する`ConciergeThread`と一致
   すること（`getConciergeThreadServer(String(tid))`が成功すること）。
3. 条件1のみで条件2を満たさない場合（`ctx=concierge && !tid`）は、**numeratorへ
   算入しない** -- 現状Webはこのケースでsynthetic genericなexplanation payload
   を注入してしまうため（§6, Risk）、これをDeep Link Boundaryの正式なcontractとして
   明文化し、将来の実装修正（本書の範囲外）でこの漏れを閉じることをFollow-up
   候補とする（§15）。
4. Mobileは現状この境界を持たない（route paramsが無ければfallbackする経路が
   inertとはいえ構造的に存在する）。Mobileも同じ2条件（`ctx`相当の明示的
   navigation source + 実在するthread検証）を持つことをMinimal Contractの
   前提条件とする。

### Route/Save/Visitへの適用

Route open/Save/Visit/Reflectionは、detail viewよりさらに`resultSetId`/`rank`は
おろか`threadId`さえ持たないことが多い（§7-9）。したがって、これらのイベントを
Recommendation funnel numeratorに算入する条件は、**そのイベントの発生元となった
detail viewセッションが上記のDeep Link Boundary条件を満たしていたこと**を
（Recommendation instance identityの伝播を通じて）遡って確認できることに置く。
これは§12 Recommended Minimal Contractで具体化する。

## 11. Options A-D Comparison

評価順序: 1. schema変更なし 2. 既存metadata利用 3. 新しいevent field
4. DB migration。

### A. Existing fields only（resultSetId + shrineId + rank + threadId + metadataの延長利用）

- Impression->Clickはすでにこれで成立している（§4-5）。
- Click->Detail以降は、`resultSetId`/`rank`が構造的に存在しない（Web
  ShrineDetailViewTracker、GoogleMapRouteLink、ShrineSaveButtonのいずれも
  この2 fieldを送っていない。Mobileも同様、送るのはroute paramsが偶然運んだ
  場合のみ）。
- **判定: Existing fieldsだけではDetail以降のstrict funnelは成立しない。**
  `threadId`はWebのみ、`resultSetId`/`rank`は構造的に非対応であり、コード変更
  無しに新たな値を捻出することはできない。

### B. Metadata propagation（既存metadataへrecommendation contextを伝播）

- Analytics event（PostHog）は全てschema-freeなproperty bagであるため、
  新しいproperty（例: `recommendationInstanceId`）を追加するのは**backend
  schema変更ゼロ**で可能。
- `ShrineInteractionLog.metadata` / `ActionEvent.metadata`（既存JSONField）へも
  同様に新keyを追加可能（migration不要）。
- `Favorite` / `Visit` / `ShrineReflection`にはmetadata JSONFieldが無いため、
  これら3つのDB persistence recordへrecommendation-instance粒度のidentityを
  持たせることは、Option Bの範囲では**できない**（`thread`粒度までは既存の
  ままで到達可能）。
- **判定: Analytics event全体とShrineInteractionLog/ActionEventのDB
  persistenceについてはOption Bで完全にstrict funnelを閉じられる。
  Favorite/Visit/ShrineReflectionのDB persistenceはthread粒度までしか
  到達しない。**

### C. `recommendationInstanceId`（Recommendation item単位のimmutable ID新設）

- 新しいIDを"新設"する必要は無い。§3.2で確認した通り、Backendにはすでに
  `rid`（per-request UUID hex、8文字）が存在し、成功応答へ`_debug.rid`として
  すでに到達している。
- 最小実装イメージ（本書は設計のみ、実装しない）: `rid`を`recs`辞書へ含め、
  `build_chat_recommendations()`が返す各recommendation item（`rec`）へ
  `rec["recommendation_instance_id"] = rid`として埋め込む。これは新しい
  resolverでもranking変更でもなく、既存生成値を既存item構造へ複製するだけ。
- これにより、`ConciergeThread.recommendations`（既存JSONField、§3.3で
  すでに永続化経路があることを確認済み）へ自動的に含まれるようになり、
  thread snapshotを読み返すDetail pageからも復元可能になる。
- Frontendは、impression時点でこの値をcaptureし、以降のclick/detail/route/
  save/visit/reflectionの各analytics call・API POST bodyへ運ぶだけでよい
  （frontend側の変更は必要、backend schemaは無傷）。
- **判定: Option Bで閉じられない「同一thread内での複数generation区別」
  問題を解決できる。Backend側は新規resolver/schema変更なしで実現可能
  （既存`rid`の再利用+既存JSONFieldへの伝播）。Frontend側の変更（各
  analytics call/API呼び出しへのfield追加）は必要。**

### D. DB persistence（Visit/Reflection等へRecommendation identityを永続化）

- `Favorite`/`Visit`/`ShrineReflection`へrecommendation-instance粒度の
  identityを持たせるには、migrationが必要（metadata JSONField追加、または
  `ConciergeRecommendationLog`へのFK追加）。
- §3.4で確認した通り、`ConciergeRecommendationLog`/`ConciergeRecommendationClickLog`
  はすでにmigration済みで未配線。これらへwriterを配線するだけならmigrationは
  不要だが、Click以降（Detail/Route/Save/Visit/Reflection）まで到達させる
  にはさらなるFK/writerの追加が要る。
- **判定: 優先順位上最下位。本書は「新規migrationなしで達成できる範囲」を
  Minimal Contractとするため、Option Dは今回実装しない。Follow-up候補
  として記録する（§15）。**

## 12. Recommended Minimal Contract

優先順位（1が最優先）に従い、以下を最小Contractとして推奨する。

1. **Option B（Analytics event + ShrineInteractionLog/ActionEvent metadata）
   をまず全面適用する。** これはbackend schema変更ゼロで、Detail/Route-Open
   analyticsとそのDB学習記録の識別度を大きく改善する。
2. **Option C（既存`rid`の再利用によるrecommendationInstanceId伝播）を
   Impression時点からVisit/Reflectionまで一貫して適用する。** Backend側は
   `rid`を`recs`へ含めてrecommendation itemへ複製するのみ（新規resolver・
   ranking変更・schema変更なし）。Frontendは各段階のanalytics call/API
   POST bodyへこの値を運ぶ。
3. **Option A（既存field）はImpression->Click間で現状のまま維持する。**
   `resultSetId + shrineId + rank`のjoinはすでに機能しており変更不要。
4. **Option D（DB persistence、Favorite/Visit/ShrineReflectionへの
   recommendation-instance粒度永続化）は実装しない。** migrationを要する
   ため、母艦判断（§16 Mother Ship Decision Points）に委ねる。

この組み合わせで、Analytics側（PostHog）はImpression -> Reflectionまで一貫した
`recommendationInstanceId`によるstrict joinが可能になる。DB persistence側は
`ShrineInteractionLog`/`ActionEvent`のみ到達し、`Favorite`/`Visit`/
`ShrineReflection`は`thread`粒度に留まる（Webのみ、Mobileは現状のギャップ解消
が別途必要 -- §15）。

Deep Link Boundary（§10）は、Recommendation経由の判定条件として
`ctx=concierge && 実在するthreadId`を正式contractとし、この条件を満たさない
detail view由来のdownstream eventはfunnel numeratorから除外する。
`recommendationInstanceId`が伝播している場合、それ自体がこの条件の代替検証
（IDが存在する = Recommendation経由であることの証跡）としても機能する。

## 13. Metric Enablement

Minimal Contract（§12）適用後に算出可能になる条件を明記する。

| Metric | 適用後の状態 | 条件 |
|---|---|---|
| strict Recommendation->Detail rate | **Analytics上でGO** | `recommendationInstanceId`が一致するimpression/click/detail viewをdistinctにjoin。DB学習記録は対象外 |
| strict Recommendation->Route rate | **Analytics上でGO** | 同上。route open PostHogへ`recommendationInstanceId`が伝播していることが前提 |
| strict Recommendation->Save rate | **Analytics上でGO（`favorite_click nextFav=true`のみ）** | Save analyticsへの伝播が前提。DB `Favorite`はthreadすら持たないため、DB側でのstrict集計は不可のまま |
| strict Recommendation->Visit conversion | **Analytics上でGO（Web）、Mobile要修正** | Mobile analyticsへの伝播 + Mobile visit作成APIへのthread_id送信（現状送っていない、§8）の両方が必要 |
| strict Recommendation->Reflection conversion | **Analytics上でGO（Web）、Mobile要修正** | Visitと同型の前提条件 |
| Primary Authority別Visit conversion | **Analytics上でGO** | `primaryReasonSource`（既存、PR #2429で整備済み）と`recommendationInstanceId`を同一eventへ持たせてgroup by |

いずれも「DB上のLearning record（Favorite/Visit/ShrineReflection）を分母・
分子にしたstrict conversion」はOption Dなしでは成立しない。PostHog analytics
上のstrict conversionのみがMinimal Contractで到達可能な範囲である。

## 14. Risks

1. `rid`は32bit衝突耐性であり、暗号学的な一意性保証ではない。高頻度利用時の
   衝突確率は本アプリの想定規模では無視できる水準だが、正式な一意性保証が
   必要になった場合は将来的にUUID4フル桁への変更（migration不要、view層の
   1行変更）を検討する。
2. `ctx=concierge && !tid`のケースでWebがsynthetic genericなexplanation
   payloadを注入する既存の挙動（§6, §10）は、Deep Link Boundaryの正式contract
   化後もコード修正が伴わなければ残存する。本書は設計のみのため、この修正は
   Follow-up PR候補とする。
3. Mobile visit作成APIが`thread_id`を送らない実装（§8）は、`recommendationInstanceId`
   propagationを追加しても、それとは独立に修正が必要な既存ギャップである。
4. Analytics delivery自体がbest-effort（PR #2430 §5と同じ制約）であるため、
   `recommendationInstanceId`を伝播してもevent配信そのものの欠落は解消しない。
5. Web/Mobileでcamel/snake_caseの命名不統一（PR #2430 §3/§8 Gap 2）は、新しい
   `recommendationInstanceId` propertyにも同じ問題が及ぶ可能性がある。命名は
   既存の`primaryReasonSource`等と同じcamelCase規約に統一することを実装時の
   前提とする。

## 15. Follow-up PR Candidates

production変更案は本監査の範囲外。母艦判断が必要な実装候補のみ記録する。

1. `rid`を`recs`へ含め、各recommendation itemへ`recommendation_instance_id`
   として複製する（backend、schema変更なし）。
2. Web/Mobileの各analytics call（impression/click/detail/route/save/visit/
   reflection）へ`recommendationInstanceId`を伝播する（frontend、schema
   変更なし）。
3. `ShrineInteractionLog.metadata`/`ActionEvent.metadata`へ
   `recommendation_instance_id`を含める（backend API、schema変更なし）。
4. Mobile visit/reflection作成APIへ`thread_id`（および将来的に
   `recommendation_instance_id`）を送るようMobile側を修正する。
5. Web `ctx=concierge && !tid`のsynthetic explanation payload注入を、Deep
   Link Boundary contractに合わせてnullへ倒す修正。
6. `ConciergeRecommendationLog`/`ConciergeRecommendationClickLog`へ
   production writerを配線するか、writer不在のまま削除するかの判断（PR #2430
   §12-6と同じ論点、本書のOption D評価でも再確認）。

## 16. Mother Ship Decision Points

1. `recommendationInstanceId`として既存`rid`を再利用するか、より強い一意性
   保証（フルUUID4等）を持つ新規値に置き換えるか。
2. Deep Link Boundary（`ctx=concierge && 実在するthreadId`）を正式契約として
   ドキュメント化し、Web/Mobile両方でこの条件を強制するか。
3. Favorite/Visit/ShrineReflectionへrecommendation-instance粒度のidentityを
   持たせるDB migration（Option D）に着手するか、`thread`粒度で妥協するか。
4. `ConciergeRecommendationLog`/`ConciergeRecommendationClickLog`を配線する
   か、legacy宣言のうえ削除するか（PR #2430からの継続論点）。
5. Mobile側のidentity gap（threadId未保持、visit/reflection APIへのthread_id
   未送信）を、本書のrecommendationInstanceId propagationと同時に解消する
   別トラックのPRとして走らせるか。
