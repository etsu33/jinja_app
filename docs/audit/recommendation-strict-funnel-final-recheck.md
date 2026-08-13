# Recommendation Strict Funnel Final Recheck

## 1. Purpose

PR #2433（`docs/audit/recommendation-strict-funnel-readiness.md`）は、PR #2432（Recommendation
Instance Identity Propagation）マージ直後のRecommendation funnelをCONDITIONAL GOと判定し、2件の
具体的な残存Gapを指摘した。

1. Web/MobileのImpression dedupが`recommendationInstanceId`ではなく`resultSetId`（Web）／単一
   batch-level ref（Mobile）を基準にしており、同一shrine構成でのrecommendation regenerationが
   新generationのImpressionを抑制し、対応するClickが孤立する（orphan click）。
2. Concierge結果画面のhero card直下`ShrineSaveButton`（Detailを経由しないSave経路）が
   `recommendationInstanceId`もAuthority provenanceも一切伝播していなかった。

PR #2434がGap 1を、PR #2435がGap 2を修正し、いずれも`develop`へマージ済みである。

本書は、この2件の修正後のcurrent production behaviorを対象に、Option D（Favorite/Visit/
ShrineReflectionへのDB persistence）なしでStrict Funnelがどこまで成立したかを最終確定する。

本監査はread-onlyである。基準HEADは`develop`の`d96bd2cdfd93bd2ffd14562dd0cfcf634dc6838d`（PR #2435
マージ直後）。production code、event schema、DB schema、writer、Ranking、UIは一切変更しない。

## 2. 修正の検証

### PR #2434（Impression dedup）の検証

`packages/shared/recommendationAnalyticsProvenance.ts:113-128`の`buildRecommendationImpressionDedupKey()`
が、Web（`ConciergeSectionsRenderer.tsx:383-389`）・Mobile（`concierge/index.tsx:703-708`）の両方から
**同一関数**として呼び出されている。dedup keyの構成は`recommendationInstanceId ?? resultSetId`を
instance boundaryとし、`shrineId`/`rank`（Webはさらに`position`）で項目を区別する。

新しいrecommendationInstanceId + 同一shrine構成での新規Impression発火、およびそのgenerationの
Clickとのjoinは、`ConciergeSectionsRenderer.impressionInstanceDedup.test.tsx`の4テスト
（同一instance+rerenderで1回、新instance+同一shrine構成で2回、generation Bのclickにgeneration
Bのimpressionが存在、malformed値でクラッシュしない）で固定されており、本監査時点で全てpassする
ことを確認した。

`recommendationInstanceId`は、Backend（`api_views_concierge.py`）が成功応答の`recommendations`/
`recommendations_v2`へ無条件に`rid`を複製するため、**Live chatレスポンス経由のImpressionでは
実運用上ほぼ常に存在する**。Impressionを発火させるのは`ConciergeClientFull.tsx`経由の
`ConciergeSectionsRenderer`のみであり（`ConsultationHistoryDetailView.tsx`等の履歴閲覧画面は
`ConciergeSectionsRenderer`を再利用せず、Impression eventを発火しない）、履歴閲覧によって
pre-cutoverな古いsnapshotから新規Impressionが発火する経路は存在しない。

例外として、匿名セッションの`sessionStorage`スナップショット復元機構
（`ConciergeClientFull.tsx:233-253`）を用いた場合、本PR適用前後をまたいだセッションでは
`recommendationInstanceId`欠落状態のpayloadが復元され得る。この場合もdedup自体はresultSetId
fallbackによりクラッシュせず機能し続けるが、その回だけ従来の衝突耐性のない挙動に戻る。実運用上
稀（deploy境界をまたいだ復元のみ）であり、fallback設計どおりの動作である。

### PR #2435（Result Save provenance）の検証

`ConciergeSectionsRenderer.tsx:1024-1032`の`<ShrineSaveButton>`（hero item直下）が
`recommendationInstanceId={heroItem.recommendationInstanceId ?? null}`と
`analyticsProvenance={heroItem.analyticsProvenance}`を渡すようになったことを確認した。Detail page側
（`shrines/[id]/page.tsx` → `ShrineSaveButton`）は元々同じ2 propを渡しており、両者は同一component・
同一prop名・同一意味論を共有する。

`ConciergeSectionsRenderer.resultSaveProvenance.test.tsx`の7テスト（Hero Saveでの
recommendationInstanceId保持、primaryReasonSource保持、fallback保持、identityなしのケースで
nullのまま送信、malformed値でクラッシュしない、Result SaveとDetail Saveのsemantic parity、
Compact由来recommendationがDetail Save到達時に同一idを保持）が全てpassすることを確認した。

Compact card（`ShrineCardCompact.tsx`）にはSave UI自体が存在しない（既存仕様。今回もUI追加は
行っていない）ため、Compact由来のrecommendationは常にDetail経由でのみSaveされる。Detail Saveは
PR #2432以来変更されておらず、Compact由来かHero由来かを区別せず`selectedRecommendation`を
shrine_idで特定するため、Compact由来のSaveも問題なくstrictである。

## 3. Strict Funnel再判定（Web/Mobile Matrix）

以下は「join key（`recommendationInstanceId`）が存在し、かつその値がevent間で正しく一致するか」
という技術的観点での再判定である。Analytics（PostHog等のevent layer）とBackend DB（Learning
record: `Favorite`/`Visit`/`ShrineReflection`/`ShrineInteractionLog`/`ActionEvent`）を分離する。

| Stage | Web Analytics | Web DB | Mobile Analytics | Mobile DB | 総合分類 |
|---|---|---|---|---|---|
| Impression→Click | Strict Joinable（PR #2434で解消。sessionStorage境界越え復元のみ例外） | N/A（Impression/ClickにDB writerなし、PR #2430から不変） | 同左 | N/A | **Strict Joinable** |
| Click→Detail | Strict Joinable（thread snapshot復元。pre-cutover/direct accessはnullで判別不能） | Strict Joinable（`ShrineInteractionLog(detail_view).metadata`、PR #2432から不変） | Strict Joinable（route params経由） | Strict Joinable（同上metadata） | **Strict Joinable**（Concierge経由・cutover後に限る） |
| Detail→Route | Strict Joinable | Strict Joinable（`ShrineInteractionLog(route_open).metadata`） | Strict Joinable | Strict Joinable | **Strict Joinable** |
| Result/Detail→Save | Strict Joinable（PR #2435でResult経路も解消。Hero/Detail双方） | Not Joinable（`Favorite`にfieldなし、Option D未実装、不変） | Strict Joinable（Detail経由のみ、Result直接Save UIなし） | Not Joinable（同上） | **Analytics: Strict Joinable / DB: Not Joinable** |
| Recommendation→Visit | Strict Joinable（`visit_done`） | Not Joinable直接／`Visit.thread`経由で条件付き復元可（そのthreadの最終turnである場合のみ、PR #2430§10知見のまま不変） | Strict Joinable（`trackVisitDone`） | Not Joinable（thread_idすら送信しない、不変） | **Analytics: Strict Joinable / DB: Not Joinable** |
| Recommendation→Reflection | Strict Joinable（`reflection_prompt_view`/`reflection_saved`） | 同上（`ShrineReflection.thread`経由の条件付き復元） | Strict Joinable | Not Joinable | **Analytics: Strict Joinable / DB: Not Joinable** |

前回監査（PR #2433）との差分は、Impression→ClickとResult/Detail→Saveの2行のみである。他の4行
（Click→Detail、Detail→Route、Visit、Reflection）はPR #2434/#2435がbackend・thread snapshot・
Visit/Reflection関連コードを一切変更していないため、判定は不変である（§9で個別に再確認済み）。

## 4. 必須確認事項

### Impression（PR #2434後）

`buildRecommendationImpressionDedupKey()`のtest「2. new instance + 同じ神社集合/rank:
Impressionが2回送信される」で、同一shrine_id・同一rankのまま`recommendationInstanceId`のみ
`"gen-a"`→`"gen-b"`と変わるケースを再現し、2回のImpression発火（うち2回目が`"gen-b"`）を確認した。
test「3. generation Bのclickにgeneration Bのimpressionが存在する」で、後続のClickが同じ
`"gen-b"`を持ち、対応するImpressionが実際に発火済みであることを確認した（§2で詳述）。

### Save（PR #2435後）

Result Hero Saveの`favorite_click` event payloadに`recommendationInstanceId`・
`primaryReasonSource`・`isFallbackRecommendation`が含まれることを確認した。これらのfield名・
意味はDetail Save（`shrines/[id]/page.tsx` → `ShrineSaveButton`、PR #2432由来）と完全に一致する
（同一component、同一prop、`recommendationAnalyticsProperties()`という同一関数からの出力を
spreadしているため、構造的に一致が保証される。§2で詳述）。

### Visit / Reflection

Analytics event（`visit_done`、`reflection_prompt_view`、`reflection_saved`）は
`recommendationInstanceId`を保持する（PR #2432由来、PR #2434/#2435では変更されていない）。

Backend DB（`Visit`、`ShrineReflection`）にはrecommendation instance粒度のfieldが存在しない
（Option D未実装）。`thread` FKは存在するが、`ConciergeThread.recommendations`が
chat turnごとに**上書き**される仕様（`concierge_history.py:408-412`、不変）のため、間接復元は
「そのthreadの最終turnである場合」にしか正しく機能しない。この制約はPR #2433で確認済みのまま、
PR #2434/#2435では一切変更されていない（backendファイルへの差分ゼロを確認済み、§9）。

## 5. Metric Recheck

| Metric | 判定 | 根拠 |
|---|---|---|
| Primary Authority別CTR | **Strict** | Impression→ClickがPR #2434でStrict化。resultSetId + shrineId + rank + recommendationInstanceIdの多重keyでjoin可能 |
| Primary Authority別Detail conversion | **Strict**（Concierge経由・cutover後に限る） | Impression→Click→Detailの全区間がrecommendationInstanceIdで一貫。pre-cutover/direct accessは`null`として明示的に除外可能（合成されないため誤集計しない） |
| Primary Authority別Route conversion | **Strict** | Detail→RouteはPR #2432からStrict、変更なし |
| Primary Authority別Save conversion | **Strict**（Analytics限定） | PR #2435でResult直接Save経路の欠落を解消。Hero/Detail両経路が同一意味論。DB (`Favorite`) 側は引き続きUnavailable |
| Primary Authority別Visit conversion | **Strict（Analytics）/ Unavailable（DB）** | Analytics側は不変でStrict。DB側はOption D未実装のため不変でUnavailable |
| Primary Authority別Reflection conversion | **Strict（Analytics）/ Unavailable（DB）** | 同上 |
| Action Grounding別conversion | **Descriptive only** | `recommendationInstanceId`はどのrecommendation generationかを特定できるが、「どのAction Suggestionが当該行動を引き起こしたか」という**causal attribution**問題は本Contract（identity propagation）のscope外であり、PR #2430時点の判定（association比較のみ可、causal conversionは不可）から不変。Detail画面のroute/save CTAは特定のAction Suggestion選択に紐付かず、常に「現在のprimary/secondary action」のprovenanceを転記するのみのため |

PR #2430時点で「NO-GO for strict conversion」だった6metric中5metric
（Detail/Route/Save/Visit/Reflection conversion）が、Analytics層に限り全て**Strict**へ到達した。
Action Grounding別conversionのみ、identity解決とは独立した別種の問題（causal attribution）により
Descriptive onlyのまま据え置かれる。

## 6. Option D再評価

Option D（`Favorite`/`Visit`/`ShrineReflection`へのrecommendation-instance粒度DB persistence）を
実装しない前提を維持し、PR #2434/#2435後の状況で改めて整理する。

### 1. Option DなしでのKPI可否

- 上記5metric（Primary Authority別Detail/Route/Save/Visit/Reflection conversion）はAnalytics
  （PostHog）層でStrictに算出可能。PostHogをKPI正本として運用すれば、Option Dなしで大半の
  Product KPIをカバーできる。
- Impression→Reflectionのstrict sequential funnelも、Analytics層のみでPR #2433時点より
  broadに（孤立click・Result Save欠落という具体的な穴が塞がれた状態で）算出可能。

### 2. Option Dなしで失う分析

- PostHogに依存しない、Backend DB単体でのrecommendation-instance粒度Visit/Reflection
  conversion監査・再現。
- 同一thread内の複数chat turnにまたがるVisit/Reflectionについて、DBの`thread` FK経由の
  間接復元が「最終turnのみ正しい」という制約を超えた、任意turn単位での正確なDB側追跡。
- Mobile側のDB persistence（Favorite/Visit/ShrineReflectionいずれも）でのthread粒度未満は
  もちろん、thread粒度自体（Mobile APIがthread_idを一切送っていない、PR #2430 §8 Gap 4、
  本Follow-up群の対象外で不変）。

### 3. Option Dで初めて可能になる監査・再現性

- PostHog配信のbest-effort性（PR #2430 §5、不変の制約）から独立した、Backend DB単体での
  recommendation-instance粒度Visit/Reflection conversionの正式な監査証跡。
- コンプライアンス・regulatory用途等、サードパーティanalyticsを正本にできない文脈での
  Recommendation→行動のinstance粒度trace。
- thread上書き問題に依存しない、任意時点への遡及的な正確なinstance粒度再計算。

### 4. migration / maintenanceコスト

- `Favorite`: 新規field追加（nullable FK or CharField）+ migration1本。既存
  `UniqueConstraint`（user×shrine、user×place_id）との整合確認が必要。
- `Visit`/`ShrineReflection`: 既に`thread` FKを持つため、`recommendation_instance_id`
  CharField追加は比較的小さいmigrationで済む。indexの要否は書き込み頻度次第。
- Mobile側は、Option D実装と同時に「thread_id送信すらしていない」既存Gap（PR #2430 §8
  Gap 4）を解消しない限り、Mobile側のOption D効果はゼロになる。これはOption Dのmigration
  そのものとは別のfrontend実装コストであり、着手判断時にセットで検討する必要がある。
- `ConciergeRecommendationLog`には既存writerがある（PR #2431文書の訂正、PR #2433で明記済み）
  ため、そちらへのfield追加は新規writer不要で済む可能性があるが、これは行動記録
  （Favorite/Visit/ShrineReflection）そのものへのidentity付与の代替にはならない
  （観測ログと行動記録は別モデル、PR #2433§13で既出）。

## 7. Residual Gaps（PR #2433からの差分）

### 解消したGap

1. Web/Mobile Impression dedupの`resultSetId`/batch-level ref依存 → PR #2434で解消。
2. Concierge結果画面hero card直下`ShrineSaveButton`のprovenance欠落 → PR #2435で解消。

### 解消していないGap（PR #2433から不変、今回のscope外）

3. Pre-cutover thread snapshotは`recommendation_instance_id`を持たず、Direct detail access
   と区別できない（§3参照、backend未変更のため不変）。
4. `ConciergeThread.recommendations`の上書き仕様により、Visit/Reflectionの`thread` FK経由の
   間接復元は「最終turンのみ」正しい（§4, §6参照、不変）。
5. Mobile Favorite/Visit/ShrineReflection APIはthread_idを一切送らない（PR #2430 §8 Gap 4、
   不変）。
6. `rid`は8 hex文字＝32bitで暗号学的な一意性保証ではない（PR #2431 §14 Risk 1、不変）。
7. Web/Mobileの`resultSetId`構成差（thread prefix有無）は未解消（PR #2430 §8 Gap 1、
   `recommendationInstanceId`導入・dedup修正により実害はさらに縮小したが、`resultSetId`自体は
   引き続きBackend発行IDではない）。
8. Mobile Action Suggestion CTA経由の行動（`ActionEvent`）は、通常のDetail→Route/Save funnelと
   合流しない別funnelのまま（PR #2433 §14-9、不変）。
9. Action Grounding別conversionのcausal attribution問題（§5参照、identity解決とは独立した
   別種の問題であり、本Contractのscope外）。

これらはいずれも本書のscope（Impression dedup、Result Save provenance）とは独立した既存Gapで
あり、production code変更を伴わない本監査では変更していない。

## 8. 最終判断

### Analytics Strict Funnel: **GO**

Impression→Reflectionの全区間で、`recommendationInstanceId`によるstrict joinがConcierge経由・
cutover後の生成に対して成立する。PR #2433で指摘された2つの具体的な欠陥（孤立Impression/Click、
Result Save provenance欠落）はいずれも解消され、新たな阻害要因は本監査で見つからなかった。

GO判定に伴うguardrail（PR #2430 §11、PR #2433 §15の既存guardrailを維持・統合）:

1. `recommendationInstanceId`が`null`のeventは「Direct detail access」と「pre-cutover
   thread」の両方を含み得るため、単純に前者と解釈しない。
2. Save集計時、Result Hero Save（Concierge結果画面直接）とDetail Saveを経路別に分離せず
   合算する場合は、両者が同じsemanticのfieldを送ることを前提としてよい（PR #2435で保証）。
3. Visit/Reflectionのstrict funnelはAnalytics（PostHog）を正本とし、Backend DBのcountとは
   混ぜない。
4. Action Grounding別の比較はassociationでありcausal attributionではないと明示する。
5. Analytics deliveryはbest-effortであり、event配信そのものの欠落はidentity解決では解消
   されない。

### Backend DB Strict Funnel: **NO-GO**

`Favorite`/`Visit`/`ShrineReflection`をrecommendation-instance粒度で分母・分子にしたstrict
conversionは、Option D未実装のため引き続き成立しない。PR #2434/#2435はいずれもbackend/DBを
変更していないため、この判定はPR #2430・PR #2433から不変である。

### Product KPI Readiness: **CONDITIONAL GO**

Primary Authority別のDetail/Route/Save/Visit/Reflection conversion（5metric、§5）は、Analytics
層に限定する前提でProduct KPIとして採用可能。ただし以下を条件とする。

- KPIダッシュボードはPostHog（Analytics）を正本とし、Backend DB集計と混在させない
  （Backend DB Strict FunnelがNO-GOのため）。
- Action Grounding別のconversion／CVR比較は、causal（「Action Suggestionが行動を引き起こした」）
  ではなくdescriptive/associationとして提示する。
- コンプライアンス・監査等、PostHog単独を正本にできない用途には現状使用しない
  （Option D着手まで待つ、§6参照）。
- §8のguardrail 1-5を全てダッシュボード設計へ反映する。

## 9. 検証記録

- `git diff --stat`（PR #2433コミット490d2f0c以降）で`backend/`配下の差分がゼロであることを
  確認した（PR #2434/#2435はいずれもfrontend/shared packageのみを変更）。
- `ConciergeSectionsRenderer.impressionInstanceDedup.test.tsx`（4 tests）、
  `ConciergeSectionsRenderer.resultSaveProvenance.test.tsx`（7 tests）、
  `ConciergeSectionsRenderer.recommendationInstanceId.test.tsx`（既存3 tests）が全てpassする
  ことを確認した（web, 14 tests）。
- `recommendationAnalyticsProvenance.test.ts`（mobile, 14 tests）が全てpassすることを確認した。
- production diff 0（本監査はdocsファイルの追加のみ）。
