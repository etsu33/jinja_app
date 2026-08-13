# Recommendation Strict Funnel Readiness Recheck

## 1. Purpose

PR #2430（`docs/audit/recommendation-metric-funnel-contract.md`）は、PR #2429マージ直後のRecommendation
funnelをCONDITIONAL GOと判定した。核心の結論は「Impression→Clickはjoin可能だが、Detail以降は
Authority/provenanceを保持してもRecommendation instance identityが一貫しない」というものだった。

PR #2431（`docs/audit/recommendation-instance-identity-propagation.md`）はこの結論を受けて、既存Backend
`rid`を`recommendationInstanceId`として再利用するMinimal Contract（Option B + Option C）を設計した。
PR #2432はこの設計を実装し、`develop`へマージ済みである。

本書は、PR #2432マージ後のcurrent production behaviorを対象に、Recommendation instance単位のStrict
Funnelがどこまで成立するようになったかを再監査する。「eventにIDが存在する」ことと「strict funnelが
成立する」ことは同義ではないという前提に立ち、実装済みcodeを読んでidentity propagationの経路・欠落を
逐次確認した。

本監査はread-onlyである。基準HEADは`develop`の`edc5083116b715b8ea2eb5ed6139034db1fc1d26`（PR #2432
マージ直後）。production code、event schema、DB schema、writer、Ranking、Candidate filtering、Signal
Authority、Reason生成、Action Grounding、UIは一切変更しない。

## 2. Previous Contract

### PR #2430の結論（再掲）

- Canonical funnel: `impression -> click -> detail view -> route/save -> visit -> reflection`。
- Impression→Clickは`resultSetId + shrineId + rank`でjoin可能（platform内）。
- Click→Detail以降はAuthority/grounding値は伝播するが、instance identityが揃わずstrict joinできない。
- Dashboard判定: rendered CTR / Primary Authority別CTR / fallback別CTRのみGO。viewable CTR、strict
  sequential funnel、Recommendation instance単位のAuthority別Detail/Visit/Reflection conversionは
  NO-GO。

### PR #2431の設計（再掲）

- 既存Backend `rid`（`api_views_concierge.py`の`rid = uuid.uuid4().hex[:8]`、per-request生成）を
  `recommendationInstanceId`として再利用する。
- Option B: 既存analytics event / 既存`metadata` JSONField（`ShrineInteractionLog`、`ActionEvent`）へ
  伝播。
- Option C: `rid`を各recommendation itemへ`recommendation_instance_id`として複製し、`ConciergeThread.
  recommendations`（既存JSONField snapshot）経由でDetail以降からも復元可能にする。
- Option D（Favorite/Visit/ShrineReflectionへのDB persistence）は実装しない。

### PR #2432の実装（再掲、本書の監査対象そのもの）

Backend側は`api_views_concierge.py:857-863`で`rid`を`recommendations`/`recommendations_v2`の各item
へ`recommendation_instance_id`として複製するのみ（新規resolver・ranking変更・schema変更なし）。
Frontend/Mobile側はこの値を`recommendationInstanceId`としてImpression〜Reflectionまでの各analytics
call・API metadataへ伝播した。詳細は本書§6-11で個別に検証する。

### 訂正: `ConciergeRecommendationLog`のwriter有無

PR #2431文書§3.4は「`ConciergeRecommendationLog`/`ConciergeRecommendationClickLog`のいずれにも
production writerが存在しない」と記載しているが、これはstale findingである。

実際には`backend/temples/services/concierge_observability.py:145`の`ConciergeRecommendationLog.
objects.create(...)`（`save_concierge_recommendation_log()`内）が、`api_views_concierge.py:960`から
チャット成功パスの度に呼び出されており、**`ConciergeRecommendationLog`には既にproduction writerが
存在する**（PR #1706「Score v3 dashboard APIを追加」時点から存在。今回のPR #2432以前から存在し、
PR #2432はこのwriterを変更していない）。

`ConciergeRecommendationClickLog`にのみproduction writerが存在しないことは正しい（`grep`で
`.objects.create(...)`呼び出しがproductionコード中に見つからない。テストコード中のみ存在）。

この訂正は本書の各所（特に§10, §13）の判断に影響する。writer自体は今回変更しない。

## 3. Identity Definitions

現行実装から、各IDの役割を確定する。

### `resultSetId`

Recommendation **result set**単位の識別子。`packages/shared/recommendationAnalyticsProvenance.ts:80-88`
の`buildRecommendationResultSetId(threadId, recommendations)`がFrontend側で合成する
`${threadId ?? "unknown"}:${index+1}:${shrineId}|...`形式の文字列。

- **Backend発行ではない。** 同一thread・同一shrine ID順序であれば、別のrecommendation generation
  でも同じ`resultSetId`になる（PR #2430 §6, §10-2で既に指摘済み。本監査でも未解消のまま残存を確認、
  §6・§13参照）。
- Web: `threadId`をprefixに持つ（`ConciergeSectionsRenderer.tsx:377`、`tid`経由）。
- Mobile: 常に`unknown`prefix（`apps/mobile/app/concierge/index.tsx:689-691`、`buildRecommendation
  ResultSetId(null, ...)`と`null`固定で呼ばれる）。

### `recommendationInstanceId`

Backend `rid`をsourceとする、**1回のRecommendation request（1回の`/api/concierge/chat/`成功応答）**
に対応するimmutableな識別子（`backend/temples/api_views_concierge.py:507,857-863`）。

- Frontend/Mobileは生成・推測・再構成しない。`packages/shared/recommendationAnalyticsProvenance.ts`
  の`normalizeRecommendationInstanceId()`は前後空白除去のみを行うpure passthroughであり、値を合成
  しない（空/非string/null/undefinedは全て`null`へfallback、合成しない）。
- `resultSetId`と異なり、同一thread内で同じshrine順序が再度返っても**別の値**になる（`rid`は
  `uuid.uuid4().hex[:8]`から毎リクエスト新規生成されるため）。この点で`resultSetId`が持てなかった
  「同一thread内での複数generation区別」をidentity面では解決している。ただしevent発火経路には
  未解決のdedup問題が残る（§6参照）。

### `threadId`

Consultation **conversation**単位の識別子（`ConciergeThread.id`）。1つのthreadは複数回のchat turn
（＝複数回のrecommendation generation、複数の`recommendationInstanceId`）を持ち得る。`ConciergeThread.
recommendations`は最新turnのsnapshotで**上書き**される（`backend/temples/services/concierge_history.
py:408-412`、`ConciergeThread.objects.filter(pk=thread.pk).update(recommendations=recommendations,
...)`）。これはappend/蓄積ではない。この上書きの性質は§10-11のVisit/Reflection joinability判定に
直接影響する。

### `shrineId`

Shrine entityの識別子。Recommendation instance identityとは無関係。同一shrineが複数のrecommendation
instanceで異なるrankとして繰り返し登場し得る。

### `rank`

Result set内のposition（1-indexed）。identityそのものではない。同一rankでも別generationでは別shrine
になり得るし、同一shrineでも別generationでは別rankになり得る。

### 責務の重複確認

`resultSetId`・`recommendationInstanceId`・`threadId`は意味的に重複しない（result set構成の
fingerprint／1回のBackend request／conversation全体、という異なる粒度）。ただし`resultSetId`の
frontend合成方式そのものが、`recommendationInstanceId`が担うはずの「同一generationの識別」を部分的に
侵食している箇所が実装に残っている（§6, §13）。Web/Mobileのsemantic contractは`recommendationInstanceId`
自体については一致している（同一shared helperを使用、§9参照）が、`resultSetId`の構成（thread prefix
有無）はWeb/Mobileで異なったまま（PR #2430 §8 Gap 1と同じ、本PR範囲外のため未解消）。

## 4. Web Funnel Matrix

| Stage | Identity carried | Dedup / gap | Classification |
|---|---|---|---|
| Impression→Click | `recommendationInstanceId` + `resultSetId` + `shrineId` + `rank`（両event一致） | Impression側dedup keyが`resultSetId`ベースで`recommendationInstanceId`を含まない（§6） | **Strict Joinable（重複generation時を除く）** |
| Click→Detail | Detailは`selectedRecommendation.recommendation_instance_id`をthread snapshotから復元。Click event自体のvalueとは別経路で独立に取得 | Direct detail / `ctx=concierge && !tid`ではnull（意図通り）。PR #2432以前に作成されたthread snapshotはfield自体が無くnull（§7） | **Strict Joinable（Concierge経由・cutover後snapshot限定）** |
| Detail→Route | `ShrineDetailViewTracker`と`GoogleMapRouteLink`が同一`recommendationInstanceId`propを共有 | props drilling経由のため一致は構造的に保証。Authority provenanceも同時伝播 | **Strict Joinable** |
| Detail→Save | Detail page配下の`ShrineSaveButton`（`shrines/[id]/page.tsx`経由）はStrict。ただし`ConciergeSectionsRenderer.tsx:1017-1023`のhero card直下`ShrineSaveButton`はDetailを経由せず`recommendationInstanceId`未伝播（§9） | 経路が2つあり、片方は完全に欠落 | **Partial（Detail経由のみStrict、Concierge結果画面直接保存はNot Joinable）** |
| Recommendation→Visit | `visit_done` analyticsは`recommendationInstanceId`保持。`Visit` DBは`thread` FKのみ（field追加なし） | DB側はthread FK経由でも、その thread の最新turn以外は復元不可（§10） | **Analytics: Strict Joinable / DB: Not Joinable（Directly）、Reconstructable only for last-turn（Conditionally）** |
| Recommendation→Reflection | `reflection_prompt_view`/`reflection_saved`は`recommendationInstanceId`保持。`ShrineReflection` DBは`thread` FKのみ | Visitと同型の制約 | **Analytics: Strict Joinable / DB: 同上** |

## 5. Mobile Funnel Matrix

| Stage | Identity carried | Dedup / gap | Classification |
|---|---|---|---|
| Impression→Click | `recommendationInstanceId` + `resultSetId`(`unknown:`固定prefix) + `shrineId` + `rank` | Impression側dedupが`trackedResultSetRef`という単一ref比較で、result set全体のsignatureが変わらない限り再発火しない。threadIdがsignatureに含まれないためWeb以上に衝突域が広い（§6） | **Strict Joinable（重複generation・重複threadで同一shrine構成の場合を除く）** |
| Click→Detail | `router.push`のroute paramsで`recommendationInstanceId`を明示的に運ぶ（`concierge/index.tsx:871`） | route paramsが欠落する経路（直接detail起動）ではnull。空文字`""`はnormalizeで`null`へ収束するため往復安全 | **Strict Joinable（Concierge-origin navigationのみ）** |
| Detail→Route | `contextRecommendationInstanceId`をmetadata・`trackRouteOpen`双方へ伝播（`shrines/[id].tsx:615,624`） | 一致は構造的に保証 | **Strict Joinable** |
| Detail→Save | `onToggleFav`の`track("favorite_click", ...)`へ`contextRecommendationInstanceId`伝播（`shrines/[id].tsx:480`）。`createFavoriteByShrineId`（DB書き込み）へは伝播しない（意図通り、Option D非実装） | Concierge結果画面には保存操作自体が存在しない（Webのようなbypass経路がない） | **Analytics: Strict Joinable / DB: Not Joinable** |
| Recommendation→Visit | `trackVisitDone`へ伝播（`shrines/[id].tsx:515`）。`createVisitByShrineId`はshrine_id/visited_atのみPOST、thread_idすら送らない（PR #2430 §8 Gap 4のまま未解消、本PR範囲外） | DB側はWebと異なりthread FKすら得られないため、間接復元の余地もない | **Analytics: Strict Joinable / DB: Not Joinable（Webより厳格に不可）** |
| Recommendation→Reflection | `trackReflectionPromptView`/`trackReflectionSaved`/`trackReflectionToConsultationClick`へ伝播（`shrines/[id].tsx:537,567,596`）。DB書き込みは`shrineId`/`answer`等のみ | 同上 | **Analytics: Strict Joinable / DB: Not Joinable** |

Mobile固有の副次的経路として、Concierge結果画面のAction Suggestion CTA（`handleActionEvent`、
`concierge/index.tsx:815-838`）は`ActionEvent.metadata`へ`recommendation_instance_id`を格納する
（`concierge/index.tsx:837`）。ただしこれは通常のRoute/Save funnelとは別のAction Suggestion専用
funnelであり（PR #2430 §2の既存整理どおり）、canonical `route_open`/`favorite_click` PostHog eventは
このpathからは送信されない。DB側でこのpathだけはstrict joinable（Option Bの範囲内）だが、Web/Mobile
共通のDetail→Route/Save funnelには合流しない。

## 6. Impression → Click

### 一致の確認

Web: `resultImpressions`配列が各itemへ`recommendationInstanceId: item.recommendationInstanceId ??
null`を持ち（`ConciergeSectionsRenderer.tsx:371`）、`concierge_result_impression`イベント
（`:395`）とhero/compact双方の`shrine_detail_transition`イベント（`:941`, `:1120`）が同じ
`item.recommendationInstanceId`/`heroItem.recommendationInstanceId`を送る。sourceは同一の
`buildPayloadFromUnified()`正規化結果であり、値は構造的に一致する。

Mobile: `toRecommendationCard()`が`item.recommendation_instance_id ?? item.recommendationInstanceId`
を`normalizeRecommendationInstanceId()`で正規化し`card.recommendationInstanceId`へ格納
（`concierge/index.tsx:365-390`）。impression（`:703`）・click（`:855`）ともこの同じ`card`由来の値を
送る。

### Rerenderでの不変性

`recommendationInstanceId`はBackend responseから一度読み取られた不変値であり、Reactの再render・
再normalize（`buildPayloadFromUnified()`の再実行）では値が変化しない。これはpure functionによる
決定的なmapping（`item.recommendation_instance_id`という単一sourceからの読み取りのみ）であるため、
rerenderで生成し直されることはない（実装上、生成という概念自体が存在せず、常にBackend値の
transcriptionのみ）。

### Duplicate impression / dedup key問題（重要な残存Gap）

**「eventにIDが存在する」ことと「strict funnelが成立する」ことの差**が最も明確に現れる箇所である。

Web (`ConciergeSectionsRenderer.tsx:380-401`):

```ts
const impressionKey = `${resultSetId}:concierge_result_impression:${item.shrineId}:${item.position}:${item.rank}`;
if (trackedImpressionKeysRef.current.has(impressionKey)) return;
```

dedup keyは`resultSetId`（`recommendationInstanceId`ではない）を含む。同一thread内で、同じshrine
IDsが同じ順序で再度返るrecommendation regeneration（同じ質問の再送信、条件を変えない再生成等）が
発生すると、`resultSetId`は§3で述べた通り**新旧generationで同一値**になる。結果、`impressionKey`も
同一になり、`trackedImpressionKeysRef`により**新しいgenerationのimpression eventは再発火しない**。

一方、そのregeneration後にユーザーがclickした場合、`shrine_detail_transition`は`heroItem.
recommendationInstanceId`（＝**新しい**rid由来の値）を正しく送信する。結果として、この新しい
`recommendationInstanceId`を持つclick eventに対応する`concierge_result_impression`eventが存在しない
という**孤立click**が発生し得る。

Mobile (`concierge/index.tsx:687-706`)はさらに粗い単位のdedupを持つ:

```ts
const resultSetId = buildRecommendationResultSetId(null, results.map(...));
if (trackedResultSetRef.current === resultSetId) return;
trackedResultSetRef.current = resultSetId;
```

`threadId`が常に`null`（`unknown`prefix固定）であるため、Web以上に衝突域が広い。**同一thread内の
regenerationだけでなく、別thread（別consultation）でも同じtop-N shrine構成が返れば**、Impressionの
再発火が抑止される。ConciergeScreenコンポーネントがunmountされない限り（画面遷移せず同一セッション
内で複数回問い合わせる限り）この`useRef`は保持され続けるため、実運用で発生し得る。

**結論**: `recommendationInstanceId`自体はImpression/Click双方のeventで正しく一致する値を持つが、
client側のimpression発火自体がresultSetIdベースのdedupで抑制され得るため、**「同一threadまたは同一
上位shrine構成でのrecommendation再生成」というシナリオに限り、Click eventに対応するImpression event
が欠落し得る**。これはevent schemaの変更なしに（dedup keyへ`recommendationInstanceId`を含めることで）
解消可能だが、本監査はproduction code変更を行わないため、Follow-up候補として記録する（§16）。

## 7. Click → Detail

### Web: thread snapshot経由の復元

`shrines/[id]/page.tsx:312-322`は`ctx === "concierge" && tid`の場合のみ`getConciergeThreadServer(tid)`
でthreadを取得し、`thread.recommendations`から`Number(r.shrine_id ?? r.id) === numericId`で一致する
itemを`selectedRecommendation`として選ぶ。`recommendationInstanceId`は`:432-434`で
`normalizeRecommendationInstanceId(selectedRecommendation?.recommendation_instance_id)`として読み取ら
れる。

これはPR #2431設計どおり、Click event自体が運ぶ値ではなく、**Detail pageがBackendのthread snapshotを
再取得して独立に復元する**方式である。Click eventの`recommendationInstanceId`とDetail pageが復元する
`recommendationInstanceId`は、両者とも同じBackend response（同一`rid`）に由来するため、正常系では
一致する。

### Direct detail access（identityなしを許容）

`ctx === "concierge" && tid`条件を満たさない場合（`ctx`なし、または`ctx=concierge`だが`tid`欠落）、
`selectedRecommendation`は`null`のままであり（`:309`の初期値のまま変化しない）、`recommendationInstanceId`
は`null`になる。フロントエンドはこの値を合成しない。§10（PR #2431文書§10）で定義されたDeep Link
Boundaryの契約どおりである。

### 新たに確認した残存Gap: pre-cutover thread snapshot

PR #2432マージ以前に生成された`ConciergeThread.recommendations`スナップショットには、そもそも
`recommendation_instance_id` keyが存在しない（当時のBackendコードがこのfieldを書き込んでいないため）。
このようなthreadへ`ctx=concierge && tid`で正しく到達した場合でも、`selectedRecommendation?.
recommendation_instance_id`は`undefined`であり、`recommendationInstanceId`は`null`になる。

これは「Direct detail access」と**observationally区別できない**（どちらも`recommendationInstanceId
=== null`）。運用上は許容範囲内（cutover後は自然に解消する一時的な状態）だが、「`null`＝Direct
access」と単純に解釈するダッシュボード設計は誤りである、という点をResidual Gap（§14）として明記する。

### Mobile: route params経由

`concierge/index.tsx:871`で`router.push`の`params.recommendationInstanceId`へ`card.
recommendationInstanceId ?? ""`をセットし、`shrines/[id].tsx:231-235`の`contextRecommendationInstanceId`
がそれを`normalizeRecommendationInstanceId()`で読み戻す（空文字は`null`へ収束、往復安全）。

Web同様、Concierge-origin navigation（route paramsを伴う遷移）を経ない場合は`recommendationInstanceId`
は存在しない。PR #2431 §10-10で要求された「Mobileも同じ2条件（明示的navigation source + 実在する
thread検証）を持つ」という要件について、Mobileはroute paramsの有無のみで判定しており、Webのような
「Backend上に実在するthreadを検証する」ステップは持たない（route paramsに含まれる文字列をそのまま
信頼する）。これはPR #2431の範囲外の既存Gapであり、本PRで変更していない。

### Click → Detail 判定

**Strict Joinable**（Concierge経由・cutover後snapshot限定）。Direct detail accessとpre-cutover
threadはともに`null`になり判別不能という限定条件付き。

## 8. Detail → Route

Web: `ShrineDetailViewTracker`と`GoogleMapRouteLink`はいずれも`shrines/[id]/page.tsx`から同一の
`recommendationInstanceId`変数をpropとして受け取る（`page.tsx:462,474`）。Authority provenance
（`analyticsProvenance`）も同じ変数から同時に渡る。両event（`shrine_detail_view`の
`trackSearchEvent`呼び出しと`route_open`の`trackSearchEvent`呼び出し）は同一値を送信することが
props drillingの構造上保証される。

Mobile: `shrines/[id].tsx`の`contextRecommendationInstanceId`が detail-view metadata（`:422`）と
route-open metadata・`trackRouteOpen`呼び出し（`:615,624`）の双方へ渡る。同じ`useMemo`由来の単一値の
ため一致する。

**Detail → Route 判定: Strict Joinable**（Web/Mobileとも）。Authority provenance
（primaryReasonSource / isFallbackRecommendation / actionSource / actionSourceKeys）も同一eventへ
同時に含まれるため、Primary Authority別のRoute conversionをinstance粒度で算出できる基盤が揃った
（§12で再判定）。

## 9. Detail → Save

### Detail page経由（Strict）

Web `shrines/[id]/page.tsx:499`は`ShrineSaveButton`へ`recommendationInstanceId`を渡し、
`ShrineSaveButton.tsx:70,80`の`favorite_click`/`shrine_decision` track呼び出しへ含める。

Mobile `shrines/[id].tsx:480`の`onToggleFav`内`track("favorite_click", ...)`へ
`contextRecommendationInstanceId`を含める。

いずれもAnalytics eventレベルではStrict Joinable。

### Analytics vs DB persistenceの分離

`Favorite`モデル（`backend/temples/models.py:576-606`）は`user`/`shrine`/`place_id`/`created_at`
のみで、`thread`すら持たない。metadata JSONFieldも存在しない。Analytics側でrecommendation
instance identityを持てても、**DB `Favorite`レコード単体では常にNot Joinable**（これはPR #2430
§7・PR #2431 §3.5の既存確認と一致し、本PRでも変化なし。Option D未実装のため意図通り）。

### 新たに確認した残存Gap: Concierge結果画面からのDetail非経由Save（Webのみ）

`ConciergeSectionsRenderer.tsx:1017-1023`はhero item用に`<ShrineSaveButton>`をDetail pageを経由
せず**直接**レンダリングしている。

```tsx
<ShrineSaveButton
  shrineId={heroItem.shrineId}
  ctx="concierge"
  tid={tid}
  nextPath={heroItem.detailHref}
  variant="subtle"
/>
```

このインスタンスには`recommendationInstanceId`propが渡されていない（`analyticsProvenance`propも
同様に渡されていない。これはPR #2429時点から存在する既存Gapであり、PR #2432はこの箇所を変更して
いない）。したがって、ユーザーがConcierge結果画面から**Detail pageを経由せずに直接保存**した場合、
その`favorite_click`/`shrine_decision` eventには`recommendationInstanceId`が一切含まれない
（propが渡されないため`ShrineSaveButton`のdefault値`null`のまま送信される）。

このコンポーネントファイル冒頭のコメント（`ConciergeSectionsRenderer.tsx:59-66`「Conciergeでは
favorite操作を提供しない」）は、実際のコード（hero itemに対する`ShrineSaveButton`の存在）と矛盾
しており、コメントが実装を反映していない状態にある（本監査はこの矛盾を指摘するのみで、UI/コメント
修正は行わない）。

Mobile側にはConcierge結果画面上の直接save操作自体が存在しない（favorite関連のimport/呼び出しが
`concierge/index.tsx`に見つからない）ため、この特定のGapはWeb固有である。

### Detail → Save 判定

**Partial**。
- Detail page経由のSave: Analytics Strict Joinable / DB Not Joinable。
- Concierge結果画面直接Save（Webのみ存在する経路）: Analytics Not Joinable（identity自体が
  送信されない）/ DB Not Joinable。

「Detail→Save」という前提そのものが、Web上のSaveという行動の一部しかカバーしていないことに注意
（§14 Residual Gapへ計上）。

## 10. Recommendation → Visit

### Analytics

Web `ShrineDetailArticle.tsx:749`の`trackSearchEvent("visit_done", { ..., recommendationInstanceId,
...})`、Mobile `shrines/[id].tsx:515`の`trackVisitDone({ ..., recommendationInstanceId:
contextRecommendationInstanceId })`。いずれもDetail pageで解決された値をそのまま使うため、Analytics
イベント単体ではStrict Joinable。

### DB persistence

`Visit`モデル（`backend/temples/models.py:691-712`）は`thread`（`ConciergeThread`への`SET_NULL` FK）
を持つが、`recommendation_instance_id`もmetadataも持たない（Option D未実装につき意図通り）。

Web `addVisit(shrineId, tid)`（`apps/web/src/lib/api/visits.ts:17-25`）は`thread_id`を送信するため、
`Visit.thread`は設定される。Mobile `createVisitByShrineId`（`apps/mobile/lib/visits.ts:32-46`）は
`shrine_id`/`visited_at`のみPOSTし、`thread_id`を一切送らない（PR #2430 §8 Gap 4のまま、本PR範囲
外につき未解消）。

### 新たに確認した残存Gap: thread snapshotの上書き特性による間接復元の限界

`Visit.thread`が設定されていれば（Webのみ）、理論上は`Visit.thread → ConciergeThread.recommendations
→ shrine_idが一致するitemのrecommendation_instance_id`という間接joinを事後的に構築できる。

しかし`append_chat()`（`backend/temples/services/concierge_history.py:408-412`）は`ConciergeThread.
recommendations`を**毎chat turnで上書き**する（追記ではない）。同一threadで複数回のchat turn
（＝複数回のrecommendation generation）が発生した場合、`ConciergeThread.recommendations`は**常に
最新turnのsnapshotのみ**を保持する。

したがって、この間接復元が正しい値を返すのは「Visitが発生した時点のrecommendation generationが、
そのthreadにおける最後のchat turnである場合」に限られる。それより前のturnで表示・クリックされた
recommendationに対するVisitは、事後的にthread snapshotを見ても**別の（より新しい）
recommendation_instance_idしか得られず、誤ったjoin結果を生む**。この誤りは検出不能（snapshotは
上書きされており、古い値へのアクセス手段がない）。

### Recommendation → Visit 判定

- **Analytics: Strict Joinable**（Web/Mobileとも、Detail以降と同じ制約を継承）。
- **DB (Web): Not Joinable directly, Conditionally Reconstructable**（`Visit.thread`経由の間接復元は
  「そのthreadの最後のchat turnであった場合」のみ正しい。一般にはNot Joinableとして扱うべき）。
- **DB (Mobile): Not Joinable**（`thread_id`自体を送っていないため、間接復元の余地もない）。

## 11. Recommendation → Reflection

### Analytics

Web `ShrineReflectionPrompt.tsx:58,93`の`reflection_prompt_view`/`reflection_saved`、Mobile
`shrines/[id].tsx:537,567,596`の`trackReflectionPromptView`/`trackReflectionSaved`/
`trackReflectionToConsultationClick`。いずれも`recommendationInstanceId`/`contextRecommendationInstanceId`
を含む。Analytics単体ではStrict Joinable。

### DB persistence

`ShrineReflection`モデル（`backend/temples/models.py:716-748`）も`Visit`と同型で`thread` FKのみ
（Option D未実装につき`recommendation_instance_id`もmetadataも持たない）。`history_theme`は生成時点
のsnapshot値として保存されるが（既存前例、PR #2431文書§3.5で言及済み）、recommendation instance
identityそのものではない。

Web `ShrineReflectionPrompt.tsx`の`createShrineReflection`呼び出しは`thread_id`（数値変換できる
場合のみ）を送るため、`ShrineReflection.thread`はWebでは設定され得る。Mobile
`createShrineReflection`（`apps/mobile/lib/reflections.ts`）はthread_idを送らない。

### Recommendation → Visit → Reflectionの再構成可能性

Reflectionは通常Visit成立後に行われるUIフロー（`visited`state依存、`ShrineDetailArticle.tsx`/
`shrines/[id].tsx`の実装を参照）である。したがってVisitと同じ「thread snapshot上書き」制約を継承
する。Visit→Reflectionの間の時間経過中に同一threadで新たなchat turnが発生すれば、Reflection時点で
thread snapshotから復元できる`recommendation_instance_id`はVisit時点のものと既に食い違っている
可能性がある。

### Recommendation → Reflection 判定

- **Analytics: Strict Joinable**（Web/Mobileとも）。
- **DB (Web): Not Joinable directly, Conditionally Reconstructable**（Visitと同じ制約。加えて
  Visit→Reflectionの間の追加chat turnでさらに劣化し得る）。
- **DB (Mobile): Not Joinable**（thread FK自体が設定されない）。

## 12. Authority Conversion Matrix

PR #2429で伝播した`primaryReasonSource`/`isFallbackRecommendation`/`actionSource`/`actionSourceKeys`
は、本PR #2432で追加された`recommendationInstanceId`と**常に同じevent payload内で同時に伝播する**
（§6-11の各箇所で確認したとおり、`recommendationAnalyticsProperties(analyticsProvenance)`の
spreadと`recommendationInstanceId`フィールドは同一のtrack呼び出し・同一のmetadataオブジェクト内に
共存する）。したがって、Instance identityがStrict Joinableな範囲では、Authority別のconversionも
同じ精度でStrictになる。

| Metric | 判定 | 根拠 |
|---|---|---|
| Primary Authority別Detail conversion | **Strict**（cutover後・Concierge経由に限る） | Impression〜Detailまでrecommendationインスタンス粒度でjoin可能（§6-7）。dedup欠落による孤立click分は集計から漏れる |
| Primary Authority別Route conversion | **Strict**（同上） | Detail→Routeは完全にStrict（§8） |
| Primary Authority別Save conversion | **Strict（Detail経由のみ）/ Descriptive only（Concierge結果画面直接保存を含む場合、Webのみ）** | §9のPartial判定を継承。Web集計時はSave経路の混在に注意 |
| Primary Authority別Visit conversion | **Strict（Analytics）/ Unavailable（DB, Backend Learning record単位では不可）** | §10。DB `Visit`はProvenanceを一切持たない |
| Primary Authority別Reflection conversion | **Strict（Analytics）/ Unavailable（DB）** | §11。DB `ShrineReflection`も同様 |

PR #2430時点では上記5metricすべてが「NO-GO for strict conversion」だったが、Analytics層に限れば
本PR #2432後は**Detail・Route・Save(Detail経由)・Visit・Reflectionの全てがStrictへ昇格した**。
DB (Backend Learning record) 層はOption D未実装のためVisit/Reflectionは引き続きUnavailableのまま
である。

## 13. Option D Necessity

Option D（Favorite/Visit/ShrineReflectionへのrecommendation-instance粒度DB persistence）を実装
しない前提で、実測に基づき必要性を評価する。

### Option Dなしで可能なこと

- PostHog（Analytics）上でのImpression→Reflectionまでのstrict recommendation-instance funnel
  （§6-11、pre-cutover thread・dedup欠落による孤立clickという限定条件つき）。
- Primary Authority別のDetail/Route/Save(Detail経由)/Visit/Reflection conversionをAnalytics上で
  算出すること（§12）。
- Web限定で、`Visit.thread`/`ShrineReflection.thread`経由の**thread粒度**（recommendation instance
  粒度ではない）でのLearning record集計。
- Mobile Action Suggestion CTA経由の行動（`ActionEvent`）について、DB上でも
  recommendation-instance粒度のjoinが可能（Option Bの範囲内、§5末尾）。ただしこれは通常の
  Detail→Route/Save funnelとは別のAction Suggestion専用funnelである。

### Option Dなしでは不可能なこと

- Backend DB（Learning record）上での、Favorite/Visit/ShrineReflectionを分母・分子にした
  recommendation-instance粒度のstrict conversion。
- 同一threadで複数回のrecommendation generationが発生した場合の、Visit/Reflectionが「どの
  generationに由来するか」をDB上で確実に特定すること（thread snapshotが上書きされるため、
  `Visit.thread`経由の間接復元は最後のturnにしか正しく機能しない、§10）。
- Mobile側のFavorite/Visit/ShrineReflectionについて、thread粒度ですら特定すること（Mobile API群が
  そもそもthread_idを送っていない。Favorite/Visit/ShrineReflectionいずれも該当。PR #2430 §8 Gap 4の
  まま）。
- Analytics delivery失敗時（best-effort配信、PR #2430 §5と同じ制約）の代替経路としてDBを使うこと。
  DBにidentityがないため、Analytics側の欠落をDB側で補完できない。

### Option Dで初めて可能になる分析

- Backend DB単体（PostHogに依存しない）での、Recommendation instance別Visit/Reflection conversion
  監査・再現。
- Analytics配信失敗があってもDB persistenceにより担保されるauditability（regulatory/compliance
  用途、社内監査等でPostHogを正本にできない場合）。
- 過去に遡った（thread上書き後の）任意時点のrecommendation instanceに対するVisit/Reflectionの
  正確な遡及集計（thread snapshotの上書き問題に依存しない）。

### migrationコストとの比較のための材料

- `Favorite`へのfield追加は新規migration1本（nullable FK or CharField、user/shrine単位の既存
  UniqueConstraintとの整合を要検討）。
- `Visit`/`ShrineReflection`は既に`thread` FKを持つため、`recommendation_instance_id`
  CharField追加は比較的小さいmigrationで済む（indexの要否は書き込み頻度次第）。
- Mobile側は追加でthread_id送信の実装（PR #2430 §8 Gap 4の解消）も同時に必要になる。これは
  Option Dのmigrationとは独立した既存gapであり、Option D着手時にセットで解消するかは母艦判断
  事項（§17）。
- `ConciergeRecommendationLog`には既にwriterが存在する（§2訂正）ため、そちらへ
  `recommendation_instance_id`を追加することは新規writerではなく既存writerへのfield追加で済む
  可能性がある。ただし`ConciergeRecommendationLog`はthread単位のsnapshot logであり、
  Favorite/Visit/ShrineReflectionという行動記録そのものにidentityを持たせる代替にはならない
  （観測ログと行動記録は別モデル）。

## 14. Residual Identity Gaps

本監査で新たに確認した、PR #2432後も残るidentity gapを一覧化する。

1. **Web Impression dedup keyが`resultSetId`ベースで`recommendationInstanceId`を含まない**
   （`ConciergeSectionsRenderer.tsx:382`）。同一thread内でのrecommendation regenerationにより、
   新しいgenerationのImpressionが発火せず、対応するClickが孤立し得る（§6）。
2. **Mobile Impression dedupがWebよりさらに粗い**（`concierge/index.tsx:693`、単一ref・
   threadIdがsignatureに含まれない）。別threadでの同一shrine構成でも抑止され得る（§6）。
3. **Pre-cutover thread snapshotはrecommendation_instance_idを持たない**。PR #2432マージ以前に
   生成されたthreadは、genuine Concierge経由でも`recommendationInstanceId === null`になり、
   Direct detail accessと区別できない（§7）。
4. **Webのみ、Concierge結果画面のhero card直下`ShrineSaveButton`がDetailを経由せずSaveできる
   経路であり、`recommendationInstanceId`（およびAuthority provenance全般、PR #2429由来の
   既存gap）が伝播していない**（`ConciergeSectionsRenderer.tsx:1017-1023`、§9）。
5. **thread snapshot（`ConciergeThread.recommendations`）は上書き専用**であり、Visit/Reflectionの
   DB `thread` FK経由の間接復元は「最後のchat turnである場合」にしか正しく機能しない（§10-11）。
6. **Mobile Favorite/Visit/ShrineReflection APIはthread_idを一切送らない**ため、Web以上に
   DB側でのidentity（thread粒度ですら）が欠落する（PR #2430 §8 Gap 4、本PR範囲外で未解消）。
7. **`rid`は8 hex文字＝32bitであり暗号学的な一意性保証ではない**（PR #2431文書§14 Risk 1で
   既知）。本アプリの想定規模では衝突確率は無視できる水準だが、正式な一意性保証が必要になった
   場合はUUID4フル桁への変更を要する（migration不要）。
8. **Web/Mobileの`resultSetId`構成差（thread prefix有無）は未解消**（PR #2430 §8 Gap 1）。
   `recommendationInstanceId`が導入されたことで実害は縮小したが、`resultSetId`自体をIDとして
   信頼するダッシュボード設計には引き続き注意が必要。
9. **Mobile Action Suggestion CTA経由の行動（`ActionEvent`）は、通常のDetail→Route/Save funnelとは
   合流しない別funnelのまま**。DBレベルでこの経路だけがrecommendation-instance粒度でjoin可能
   という非対称性が生じている（§5, §13）。

## 15. GO / CONDITIONAL GO / NO-GO

| Metric | 判定 |
|---|---|
| Rendered CTR | **GO**（PR #2430から変更なし、既に成立） |
| Strict Impression→Click | **CONDITIONAL GO**（`recommendationInstanceId`で一致するが、dedup欠落による孤立clickが一定割合発生し得る。§6, §14-1,2） |
| Strict Impression→Detail | **CONDITIONAL GO**（Concierge経由・cutover後snapshotに限る。孤立click分・pre-cutover null分は分母/分子から除外する運用が必要。§7, §14-3） |
| Strict Impression→Route | **CONDITIONAL GO**（Detail以降はStrictだが、上流のImpression→Click→Detailの限定条件を継承する。§8） |
| Strict Impression→Save | **CONDITIONAL GO（Detail経由のSaveに限る）**（Webのみ存在するConcierge結果画面直接Save経路はNot Joinableのため、Web全体のSave集計では経路を分離する必要がある。§9, §14-4） |
| Strict Impression→Visit | **CONDITIONAL GO（Analytics限定）/ NO-GO（DB/Backend Learning record単位）**（§10, §14-5,6） |
| Strict Impression→Reflection | **CONDITIONAL GO（Analytics限定）/ NO-GO（DB/Backend Learning record単位）**（§11, §14-5,6） |
| Primary Authority別Detail conversion | **CONDITIONAL GO**（§12の限定条件を継承） |
| Primary Authority別Visit conversion | **CONDITIONAL GO（Analytics）/ NO-GO（DB）**（§12） |
| Primary Authority別Reflection conversion | **CONDITIONAL GO（Analytics）/ NO-GO（DB）**（§12） |

### 総合判定: CONDITIONAL GO

PR #2430のCONDITIONAL GO（rendered CTR / Primary Authority別CTR / fallback別CTRのみ）から、本PR
#2432後は**Analytics（PostHog）層に限り、Impression→Reflectionまでのstrict recommendation-instance
funnelがCONDITIONAL GOへ拡大した**。「CONDITIONAL」の内実は、Backend `rid`不在（PR #2430時点の
根本原因）から、client側dedup実装・thread snapshot上書き・一部UI経路の伝播漏れという、より狭い
範囲の運用上の制約へ後退した。

Backend DB（Learning record: Favorite/Visit/ShrineReflection）を分母・分子にしたrecommendation
-instance粒度のstrict conversionは、Option D未実装のため引き続き**NO-GO**である。

Dashboardには少なくとも次のguardrailを追加で明記する（PR #2430 §11の既存guardrailに追加）。

1. `recommendationInstanceId`が`null`のeventは「Direct detail access」と「pre-cutover thread」の
   両方を含み得るため、単純に前者と解釈しない。
2. 同一thread内での短時間の再送信・regenerationが疑われるsessionは、Impression→Click strict
   funnelのdenominatorから慎重に扱う（孤立clickが生じ得るため）。
3. Web `favorite_click`/`shrine_decision`のsource別内訳（Detail経由 vs Concierge結果画面直接）を
   分けずに集計しない。
4. Visit/Reflectionのstrict funnelはAnalytics（PostHog）を正本とし、Backend DBのcountとは混ぜない
   （Backend DBはthread粒度、かつ上書きにより不正確になり得るため）。

## 16. Follow-up PR Candidates

production変更案は本監査の範囲外。母艦判断が必要な実装候補のみ記録する。

1. Web/Mobileのimpression dedup keyへ`recommendationInstanceId`（またはgenerationを示す等価な値）
   を含め、regeneration時のImpression取りこぼしを解消する（§6, §14-1,2）。
2. `ConciergeSectionsRenderer.tsx`のhero card直下`ShrineSaveButton`へ`recommendationInstanceId`
   （および`analyticsProvenance`）を伝播する（§9, §14-4）。
3. Mobile Favorite/Visit/ShrineReflection作成APIへ`thread_id`を送るようMobile側を修正する
   （PR #2430 §8 Gap 4、§14-6）。これはOption D着手の前提整備にもなる。
4. `resultSetId`の構成をWeb/Mobileで統一する（thread prefix有無を揃える）、または
   `resultSetId`をBackend発行IDへ置き換える（PR #2430 §12-2の継続論点）。
5. `ConciergeRecommendationClickLog`を配線するか、legacy宣言のうえ削除するかの判断（PR #2430
   §12-6、PR #2431 §15-6と同じ継続論点。§2の訂正によりRecommendationLog側は既にwiring済みである
   ことを踏まえて再検討する）。
6. PR #2431文書§3.4の「production writerなし」記載を、本書§2の訂正内容へ合わせて更新する
   （ドキュメント修正のみ、production変更ではない）。

## 17. Mother Ship Decision Points

1. Option D（Favorite/Visit/ShrineReflectionへのrecommendation-instance粒度DB persistence）に
   着手するか、Analytics層のCONDITIONAL GOで妥協するか（§13）。着手する場合、Mobile側の
   thread_id送信整備（Follow-up候補3）を同時に行うかどうか。
2. Impression dedup keyの修正（Follow-up候補1）を、strict funnel精度向上のために優先度高く
   扱うか。孤立clickの実際の発生率を計測してから判断するか。
3. `ConciergeSectionsRenderer.tsx`のConcierge結果画面直接Save経路（hero card`ShrineSaveButton`）
   を、identity伝播対象に含めるか、それとも「Conciergeではfavorite操作を提供しない」という
   既存コメントの意図に立ち返り、UI自体を見直すか（本監査はUI変更を提案しない。母艦判断事項）。
4. `resultSetId`のBackend ID化（Follow-up候補4）に着手するか。`recommendationInstanceId`導入後は
   優先度が下がった可能性があるため、再評価が必要。
5. `ConciergeRecommendationClickLog`のwiring/legacy化/削除の最終判断（既存継続論点、§16-5）。
6. PostHogをKPI正本、Backend DBをLearning正本として明示的に分離する運用ルールを正式化するか
   （PR #2430 §12-5の継続論点）。
