# A-6-0 Collective Deity Runtime Activation Surface Audit

## Status

- Status: AUDIT COMPLETE / RUNTIME UNCHANGED
- Recorded at: 2026-09-30
- Base branch: develop
- Audit branch: audit/collective-deity-runtime-activation-surface
- Change type: docs-only audit
- Runtime code change: NONE
- Production write: NONE
- Model / Migration change: NONE
- Recommendation behavior change: NONE

## 1. Purpose

A-5bでProductionへ投入済みのShrineDeityCollective / ShrineDeityCollectiveMembershipが、
現行Runtimeのどこから読まれているか、どこでは読まれていないか、どの接続が既存契約の
再利用で済むか、どの接続がMother Ship判断または別Model Gateを要するかを現行developから固定する。

本auditはRuntime activationそのものを行わない。

## 2. Current authority

A-1のNamed Collective Migration = Cは次の順序を固定している。

~~~text
Model Foundation
-> Source-backed backfill
-> Runtime activation
-> legacy collective cleanup
~~~

A-5b Pattern B Production backfillは別GateでCLOSED / PASS済みで、Production上の記録は以下。

~~~text
Collectives created = 6
Memberships created = 23
A5B_PRODUCTION_BACKFILL = PASS
A5B_PRODUCTION_CLOSURE = CLOSED
~~~

このA-6-0ではA-5b履歴・Production state・legacy ShrineDeityを変更しない。

## 3. Executive result

現行developでは、CollectiveはModel / Migration / Seed Import / Production Dataまでは存在するが、
Runtime consumerには接続されていない。

Repository横断検索でShrine.deity_collectivesのRuntime参照は確認できず、参照はmodel、migration、
model/import testsに限定される。

~~~text
MODEL / DB                    = ACTIVE
KNOWLEDGE SEED IMPORT         = ACTIVE
EVIDENCE GATE PRIMITIVE       = REUSE_CANDIDATE / NOT_CONNECTED
SHRINE DETAIL API             = INACTIVE
DETAIL PREFETCH               = INACTIVE
RECOMMENDATION SELECTOR       = INACTIVE
SHARED ELIGIBILITY            = CURRENT_FIXED / COLLECTIVE_EXCLUDED
RECOMMENDATION REASON         = INACTIVE
CONCIERGE                     = INACTIVE
COMPASS                       = INACTIVE
DEEP DIVE                     = INACTIVE
EVIDENCE FOUNDATION/LINK      = MODEL_CHANGE_REQUIRED
EVIDENCE TRANSPORT V1         = UNSUPPORTED
WEB DETAIL                    = INACTIVE
MOBILE DETAIL                 = INACTIVE
LEGACY COLLECTIVE CLEANUP     = BLOCKED_BY_RUNTIME_ACTIVATION
~~~

## 4. Surface matrix

| Surface | Current state | Evidence / current behavior | A-6 implication |
|---|---|---|---|
| ShrineDeityCollective model | ACTIVE | backend/temples/models.pyに実装。model docstring自身がRuntimeから読まれないと明記 | Runtime接続前提は満たす |
| Membership model | ACTIVE | 独自sourcesを持つ。Membership Evidence = B。Collective Sourceを自動継承しない | Runtime表示時もMembershipを独立Evidenceとして扱う必要 |
| Evidence Gate | REUSE_CANDIDATE | decide_fact_usability / decide_detail_display_stateはverification_status・confidence・Source statusのprimitive入力でModel型に依存しない | Collective/Membershipへ再利用可能性が高いが、専用selector/serializer testが必要 |
| Shrine Detail Serializer | INACTIVE | ShrineDetailSerializerはdeities / historiesのみ。Collective serializerもfieldも存在しない | separate payload contractが必要 |
| Detail View prefetch | INACTIVE | ShrineViewSet.retrieveはShrineDeity / ShrineHistoryのみprefetch | Collective/Membership有効化時はN+1を避けるprefetch設計が必要 |
| Recommendation selector | INACTIVE | shrine_knowledge_selectorはShrineDeity / ShrineHistoryのみimport・query | explicit Collective selectorが必要 |
| Shared Recommendation Eligibility | CURRENT_FIXED | is_recommendation_eligible = usable Deity OR usable History。Mother Ship Decision: KEEP CURRENT SHARED ELIGIBILITY | Collectiveを第3経路へ追加するなら新しいMother Ship decisionが必要 |
| Recommendation Reason | INACTIVE | concierge_chat._join_knowledge_deity_namesはknowledge_deitiesのみを読点結合。Reason V4のFact layerもdeity/shrine_history前提 | CollectiveをExplanationへ出すならpresentation contractが必要 |
| Concierge | INACTIVE | Candidate payloadはknowledge_deities / knowledge_historiesのみ | Shared Eligibility変更時は直接影響 |
| Compass current orchestrator | INACTIVE | build_chat_candidates_with_eligibility経由のShared Eligibilityを利用 | Shared Eligibility変更時は直接影響 |
| Compass Direction-only Core (#3032) | INACTIVE FOR COLLECTIVE | partition_recommendation_eligible_shrinesを使用し、payloadはknowledge_deities / knowledge_historiesのみ。HTTP cutoverは別PR | A-6は旧/current pathと新Coreの両方を監査対象に維持する必要 |
| Deep Dive | INACTIVE | _usable_deities / _usable_historiesのみ。question retrievalもDeity/History固定 | Collective-aware question/retrievalは別contractが必要 |
| EvidenceLink Foundation | UNSUPPORTED | EvidenceLink FKはshrine_history / shrine_deityの2択。SUPPORTED_FACT_MODELSもShrineHistory / ShrineDeityのみ | Serializer追加では済まずModel/Foundation変更が必要 |
| Evidence Transport v1 | UNSUPPORTED | NormalizedFactV1 payload unionはShrineHistory / ShrineDeityのみ | versioned transport設計だけでなくEvidenceLink/Foundation拡張が先に必要 |
| Web API types | INACTIVE | ShrineBaseはdeities? / histories?のみ。Collective型なし | Backend payload確定後にtype追加 |
| Web Fact ViewModel/UI | INACTIVE | buildShrineFactSection / ShrineFactSectionはDeity/Historyのみ | Collectiveをdeitiesへflattenしてはならない |
| Mobile API/ViewModel/UI | INACTIVE | buildShrineFactViewModel / ShrineKnowledgeFactSectionはDeity/Historyのみ | Backend payload確定後に独立表示責務を定義 |
| Legacy cleanup | NOT_ALLOWED_YET | Named Collective Migration = CでRuntime activation + QA後 | A-6完了前のlegacy ShrineDeity削除は禁止 |

## 5. Backend findings

### 5.1 Model boundary is intact

ShrineDeityCollectiveとShrineDeityCollectiveMembershipのmodel docstringは、
Serializer / selector / Recommendation eligibility / Deep Dive / Evidence Transportから
まだ読まれないModel Foundationであることを明示している。

この境界は現行コードでも維持されている。

### 5.2 Evidence Gate is structurally reusable

decide_fact_usability()は次だけを入力に取る。

~~~text
verification_status
confidence
source_verification_statuses
~~~

decide_detail_display_state()もModel型を要求しない。

Collective / Membershipはいずれもverification_status / confidence / sourcesを持つため、
新しいEvidence Authorityを作らず既存Gateを再利用できる構造である。

ただし現時点ではCollective/MembershipをGateへ渡すselector/serializerが存在しないため、
REUSE_CANDIDATEでありACTIVEではない。

Membership Evidence = Bにより、CollectiveがusableでもMembershipを自動usableにしてはならない。

### 5.3 Detail API is fully disconnected

backend/temples/api/serializers/shrine.py:

- importsはShrineDeity / ShrineHistory / ShrineKnowledgeSourceまで
- ShrineDetailSerializer fieldはdeities / historiesのみ
- get_deities / get_historiesのみ
- __all__にもCollective serializerなし

backend/temples/api/views/shrine.py:

- retrieve時prefetchはdeities / historiesのみ
- deity_collectives / membershipsのprefetchなし

よってProduction上の6 Collective / 23 MembershipはDetail API responseへ到達しない。

### 5.4 Recommendation is fully disconnected

shrine_knowledge_selector.pyはShrineDeity / ShrineHistoryだけをimportし、
fetch_fact_ready_knowledge_deities() / fetch_fact_ready_knowledge_histories()だけを持つ。

is_recommendation_eligible()のCurrent authorityは:

~~~text
usable Deity Fact >= 1
OR
usable History Fact >= 1
~~~

rule-conflict-resolution.mdでMother Ship Decision = KEEP CURRENT SHARED ELIGIBILITYとして
Current固定されている。

したがってCollectiveをRecommendation eligibilityへ追加することは、A-6配線の当然の帰結ではない。
明示的なMother Ship decisionなしに変更してはならない。

### 5.5 Recommendation Reason is not Collective-aware

concierge_chat.pyのReason入力はknowledge_deitiesを_join_knowledge_deity_names()で
display_nameの自然文へ変換し、knowledge_historiesからHistoryを選ぶ。

recommendation_reason_v4.pyのFact layerもdeity / shrine_historyを前提とする。

Collectiveを通常ShrineDeityとしてflattenすると、A-1の意味分離を破壊する。

### 5.6 Deep Dive is disconnected

deep_dive_retrieval.pyは:

~~~text
_usable_deities()  -> ShrineDeity
_usable_histories() -> ShrineHistory
~~~

のみを取得する。deity_who / deity_natureを含めCollective retrievalは存在しない。

## 6. Evidence Foundation / Transport finding

これはA-6-0で最も大きいblast-radius findingである。

Evidence Transportは単に新しいpayload serializerを追加すれば対応できる状態ではない。

backend/temples/models.py EvidenceLinkはFact relationとして:

~~~text
shrine_history
shrine_deity
~~~

だけを持つ。

backend/temples/domain/evidence_link.py:

~~~text
SUPPORTED_FACT_MODELS = {ShrineHistory, ShrineDeity}
~~~

backend/temples/services/evidence_foundation.pyもfact_fields / select_related / prefetchを
History / Deityの2種類へ固定している。

NormalizedFactV1のpayload unionもShrineHistory / ShrineDeityだけである。

したがってCollectiveをEvidence Transportへ追加する場合は少なくとも:

~~~text
EvidenceLink model contract
DB migration
Evidence Foundation snapshot
SUPPORTED_FACT_MODELS
normalized transport schema/version
transport serializer
integrity tests
~~~

の再設計が必要になる。

この変更を通常のDetail Runtime activation PRへ混ぜてはならない。

## 7. Frontend findings

### 7.1 Web

apps/web/src/lib/api/types.tsはShrineDeity / ShrineHistoryだけを定義し、
ShrineBaseもdeities? / histories?のみ。

buildShrineFactSection()はその2配列だけを『神社について』Fact Sectionへ変換する。

Collective / Membershipの型、ViewModel、UIは存在しない。

### 7.2 Mobile

MobileもbuildShrineFactViewModel()とShrineKnowledgeFactSectionがDeity / Historyだけを描画する。

apps/mobile/app/shrines/[id].tsxではShrineKnowledgeFactSectionを実際にrenderしている。

一方、同ファイルの型付近には『UIはまだこれらを描画しない』という古いcommentが残っており、
実装とcommentがずれている。

Classification:

~~~text
STALE_COMMENT_ONLY
runtime behavior impact = NONE
~~~

このcomment driftはA-6の仕様判断材料にはしない。

## 8. Compass current-state note

developにはPR #3032のDirection-only Monthly candidate coreが入っている。

新CoreはShared Eligibilityのauthorityを複製せずpartition_recommendation_eligible_shrines()へ委譲する。
その返却payloadもknowledge_deities / knowledge_historiesだけで、Collectiveは存在しない。

旧Monthly HTTP配線はまだ変更されていないため、recommendation-eligibility-contract.mdの旧Compass説明は
公開Runtimeについては直ちに矛盾しない。

ただしA-6でShared Eligibilityを変更する場合、旧orchestratorだけでなく新Direction-only Coreも
同じ影響範囲として扱う必要がある。

## 9. Mother Ship decisions required before implementation

### D1. Runtime activation scope

Collective Runtime Activationをどこまで含めるか。

候補scope:

~~~text
DETAIL_DISPLAY_ONLY
DETAIL_PLUS_RECOMMENDATION_EXPLANATION
DETAIL_PLUS_DEEP_DIVE
FULL_RUNTIME_INCLUDING_ELIGIBILITY
~~~

A-6-0は選択しない。

### D2. Detail API payload shape

A-1で『Collectiveをexisting deities arrayへsilent flattenしない』ことは固定済み。

未決:

~~~text
top-level deity_collectives
nested memberships
membershipを別fieldにするか
member_count / member_count_relation / member_list_statusをどこまで公開するか
~~~

### D3. Membership presentation

Membership Evidence = Bは固定済み。

CollectiveがfullでもMembershipがhiddenになりうる。
その場合の表示契約を決める必要がある。

### D4. Shared Recommendation Eligibility

CurrentはDeity OR Historyで固定されている。

Collectiveを:

~~~text
eligibilityに含めない
OR
usable Collectiveを第3経路として含める
~~~

の変更はMother Ship判断が必要。

### D5. Recommendation Reason

CollectiveをExplanation-only Factとして使用するか、Reasonから外すか。
通常Deity名称列へflattenすることは不可。

### D6. Deep Dive

Collective-aware question/retrievalをA-6に含めるか。

### D7. Evidence Foundation / Transport

CollectiveをEvidence Foundation / normalized transportへ対応させるか。

対応する場合は通常A-6 Runtime UIとは別Model/Foundation Gateとして扱う必要がある。

## 10. Candidate implementation split after Mother Ship decisions

これは優先順位の確定ではなく、blast radiusを混ぜないための分割候補である。

~~~text
A-6-1 Runtime Activation Contract
  - D1-D7のMother Ship decisionsを記録

A-6-2 Detail Backend Activation
  - Collective serializer
  - Membership representation
  - Evidence Gate reuse
  - prefetch
  - API contract tests

A-6-3 Web / Mobile Detail Presentation
  - API types
  - ViewModels
  - UI

A-6-4 Recommendation Integration
  - Mother Shipが承認した場合のみ
  - selector / eligibility / reason contract
  - Concierge + Compass両経路

A-6-5 Deep Dive Integration
  - Mother Shipが承認した場合のみ

Separate Evidence Foundation Gate
  - EvidenceLink / migration / transport
  - D7が承認された場合のみ

A-6 Runtime QA
  - regression / query / response / UI

Legacy Collective Cleanup Gate
  - Runtime activation + QA後のみ
~~~

## 11. Explicit non-goals of A-6-0

- Runtime code modification
- Production write
- serializer implementation
- selector implementation
- eligibility modification
- ranking / score change
- Recommendation reason change
- Deep Dive change
- EvidenceLink migration
- Evidence Transport schema change
- Web/Mobile UI change
- legacy ShrineDeity cleanup
- Model Risk release
- Candidate lifecycle change

## 12. Audit completion checklist

~~~markdown
- [x] Current develop inspected
- [x] A-1 Runtime boundary revalidated
- [x] A-5b Production closure revalidated
- [x] Collective / Membership model inspected
- [x] Evidence Gate inspected
- [x] Shrine Detail Serializer inspected
- [x] Detail prefetch inspected
- [x] Recommendation selector inspected
- [x] Shared Recommendation Eligibility inspected
- [x] Recommendation Reason path inspected
- [x] Concierge impact inspected
- [x] Current Compass orchestrator impact inspected
- [x] Direction-only Compass Core (#3032) inspected
- [x] Deep Dive retrieval inspected
- [x] Evidence Foundation / EvidenceLink inspected
- [x] Evidence Transport inspected
- [x] Web types / ViewModel / UI inspected
- [x] Mobile types / ViewModel / UI inspected
- [x] Mother Ship decisions extracted
- [x] Runtime implementation boundaries proposed without selecting policy
- [x] Runtime changes = 0
- [x] Production writes = 0
~~~

## 13. Final classification

~~~text
A6_0_RUNTIME_SURFACE_AUDIT = COMPLETE

COLLECTIVE_DATA_STATE = PRODUCTION_PRESENT
COLLECTIVE_RUNTIME_STATE = INACTIVE

EVIDENCE_GATE = REUSABLE_NOT_CONNECTED
DETAIL_API = INACTIVE
RECOMMENDATION = INACTIVE
SHARED_ELIGIBILITY = CURRENT_FIXED_DEITY_OR_HISTORY
DEEP_DIVE = INACTIVE
EVIDENCE_TRANSPORT = FOUNDATION_EXTENSION_REQUIRED
WEB = INACTIVE
MOBILE = INACTIVE

NEXT_GATE = MOTHER_SHIP_RUNTIME_ACTIVATION_DECISIONS
~~~

A-6-0はここでSTOPする。
