# KAMI MUSUBI Rule Conflict Resolution Decision

> **Status: DECIDED — MOTHER SHIP RULE CONFLICT RESOLUTION / Phase 2B**
>
> 本書は `docs/audit/rule-authority-resolution.md`（Phase 2A）でHOLDされた真正Conflictについて、
> Mother Shipとして意図したCurrent仕様を確定するDecision Recordである。
>
> 本PRではRuntime、Ranking、DB、Migration、API Schema、Frontend挙動を変更しない。
> 既存実装の正誤を推測で書き換えず、Currentとして採用する契約境界と、Currentではない記述を明示する。
>
> Fixed Rulesの最終抽出は次工程で行う。

## 1. Base / Scope

- Base: `develop` after PR #2832
- Phase 2A: `docs/audit/rule-authority-resolution.md`
- Phase 2B branch: `audit/rule-conflict-resolution`

対象Conflict:

1. Recommendation Eligibility
2. Recommendation Score v3 source designation
3. MIXED_CURRENT_DESIRED文書のCurrent範囲

対象外:

- Ranking weight変更
- Recommendation candidate logic変更
- Eligibility gate実装変更
- Score式変更
- Product UI変更
- DB / Migration
- Fixed Rules最終確定

---

# 2. Decision A — Recommendation Eligibility

## 2.1 Conflict

Core canonicalには、Knowledge完全性を理由にRecommendation候補を除外しない旨の古い記述が残っている。

一方、Current runtimeにはShared Recommendation Eligibility gateが存在する。

Current contract:

```text
Shrine DB presence
!= Recommendation eligibility

Recommendation eligibility
= at least one usable Deity or History Fact
```

実装位置:

```text
backend/temples/services/concierge_chat_candidates.py
```

- `is_recommendation_eligible()`
- `filter_recommendation_eligible_candidates()`
- `build_chat_candidates_with_eligibility()`

Knowledge usability authority:

```text
shrine_knowledge_selector
  -> evidence_gate.decide_fact_usability()
```

## 2.2 Chronology / Intent Evidence

Shared Eligibilityは偶発的な実装ではない。

- PR #2710（2026-09-05）で `Concierge / Compass` 共通gateとして意図的に実装
- PR本文で `Mother Ship review 待ち` と明示
- PR #2716で `recommendation_eligibility_zero_candidates` の成立条件をさらに限定し、frontend copy / tests / contractを整合
- `docs/knowledge/shrine-knowledge-contract.md` がRecommendation Eligibilityの適格条件を `docs/knowledge/recommendation-eligibility-contract.md` へ明示委譲
- Backend service/API testsとCompass frontend testsが専用stateを固定

したがって、現在のShared Eligibilityは単なるimplementation driftではなく、後続PRで継続的に維持・精緻化されたCurrent runtime contractである。

## 2.3 Mother Ship Decision

**Decision: KEEP CURRENT SHARED ELIGIBILITY**

Current Recommendation Eligibilityは以下とする。

```text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1
```

このgateは:

- Concierge / Compassで共有する
- Ranking signalではない
- Scoreを下げて残す仕組みではない
- Legacy goriyaku / history_themeからeligibilityを推測しない
- ineligible Shrineをsilent fallbackで復活させない
- Shrine一覧 / Detailの可視性を制限しない

Exact rule / zero-candidate behavior / Compass state contractは
`docs/knowledge/recommendation-eligibility-contract.md`の委譲scopeをCurrentとする。

## 2.4 Superseded / Stale Current Claims

以下の主張はCurrent仕様として採用しない。

- `docs/core/recommendation-readiness.md` の「Knowledge完全性を候補除外に使っていない」という監査時点記述
- `docs/core/recommendation-architecture.md` Section 5 の「現状は明示的な除外を行わない」
- 「情報不足神社を候補除外すべきか」が現在も未決である、という記述

これらはShared Eligibility導入前のCurrent Stateを表した**時点記述**として扱い、次工程で`SUPERSEDED`分類へ送る。

重要:

`recommendation-readiness.md`のGovernance責務そのものは維持する。

```text
Recommendation Readiness Governance
!= Shared Recommendation Eligibility
```

Readiness Level 0〜3は引き続きSupersededであり、Shared Eligibilityを旧Readiness Levelの復活として扱わない。

## 2.5 Runtime Change

**NONE**

Phase 2Bでは現在稼働中のEligibility gateを変更しない。

---

# 3. Decision B — Recommendation Score Authority

## 3.1 Conflict

Core canonical:

```text
docs/core/architecture.md
docs/core/recommendation-architecture.md
```

はScoreの正本として:

```text
docs/analytics/recommendation-score-v3-design.md
```

を指定している。

しかしAnalytics domain classificationでは:

- `recommendation-score-v2-current-design.md` = Active / Current
- `recommendation-score-v3-design.md` = Reference

である。

さらにv3文書自身も:

```text
Status: Reference
現行仕様は関連するActive文書、実装コードおよびテストを最終的な正本とする
```

と明記している。

## 3.2 Physical Runtime Evidence

Current rankingは主に:

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/services/recommendation_score_v2.py
```

で稼働している。

`docs/analytics/recommendation-score-v2-current-design.md`は現行実装を読み取り、
`score_total_ranked_base`、`score_need_rank_weighted`、behavior contribution、profile / direction signal等をCurrentとして管理している。

一方 `recommendation-score-v3-design.md` は、将来のsignal / weight / phase構成を記したReference設計であり、そのドラフト式をCurrent runtime contractとして扱う根拠はない。

## 3.3 Mother Ship Decision

**Decision: CURRENT SCORE AUTHORITY = V2 CURRENT DESIGN + BACKEND / TESTS**

Current Recommendation Scoreの仕様Authorityは:

```text
1. docs/analytics/recommendation-score-v2-current-design.md
2. backend current implementation
3. related tests
```

とする。

`docs/analytics/recommendation-score-v3-design.md`は**Reference / Future Design**のまま維持する。

v3をCurrentへ昇格しない。

Core側の「v3を正本」とする参照はstale canonical referenceであり、次工程で`SUPERSEDED / STALE_REFERENCE`として扱う。

## 3.4 Runtime Change

**NONE**

Score式・weight・rankingは変更しない。

---

# 4. Decision C — MIXED_CURRENT_DESIRED Current Scope

## 4.1 General Rule

Current / Proposed / Desired / Should / Future / Open Questionが1文書へ混在する場合、**文書全体をCurrentとして採用しない**。

Section / statement単位で次の基準を使用する。

```text
CURRENT
= 明示的にCurrentと記載
  AND current implementation / testsで確認可能

IMPLEMENTED
= 後続Addendum / implementation recordがあり
  current code / testsと一致

DESIRED / PROPOSED / SHOULD / FUTURE
= Currentではない

OPEN QUESTION / MOTHER SHIP DECISION REQUIRED
= UNRESOLVED
```

後続実装がDesired Contractを実装済みにした場合でも、文書のラベルだけで昇格させず、Current implementation / testsでstatement単位に確認する。

---

## 4.2 `docs/product/recommendation-signal-authority.md`

### Currentとして使用可能

- `Current Implementation` と明記された実測内容
- Candidate / Ranking / Explanationへの現在の影響を実装・テストで確認できる記述
- 現在のsignal flowを説明する事実記述

### Currentとして使用しない

- `Desired Contract`
- `Should`
- `Future`
- `Follow-up PR Plan`
- 未実装のDesired Authority
- Mother Ship判断待ちの設計方針

### Phase 2B Classification

```text
Document = MIXED_CURRENT_DESIRED
Current-scope = CURRENT_VERSIONED candidate
Desired-scope = UNRESOLVED / FUTURE
```

文書全体をFixed Rule Sourceにしない。

---

## 4.3 `docs/product/concierge-input-architecture.md`

本文自身がCurrent / Proposed / Gapを分離している。

### Currentとして使用可能

- `Current` と明記されたSignal挙動
- Backend / Web / testsで確認できる現行Level責務
- `Addendum: Implemented Contract Foundation` 等、後続実装を記録しcurrent code / testsと一致する範囲

### Currentとして使用しない

- `Proposed`
- `Redesign`
- `Hold`
- `Open Questions`
- 後続PR前提の設計事項

### Phase 2B Classification

```text
Document = MIXED_CURRENT_DESIRED
Current + Implemented Addendum = CURRENT_VERSIONED candidate
Proposed / Open Question = UNRESOLVED / FUTURE
```

Level 1 / 2 / 3という語彙自体を、旧Recommendation Readiness Level 0〜3と同一視しない。

---

## 4.4 `docs/product/deep-dive-answer-generation-contract.md`

作成時点ではdesign-onlyだったが、現在はBackend retrieval / answer / serializer / API / frontend / testsが本書を実装契約として参照している。

### Currentとして使用可能

current implementation / testsで確認できるMVP contract:

- Backend Authority
- Question classification
- Fact retrieval
- Evidence filtering
- usable Factなし時のfail-safe
- provenance / source保持
- Frontendがreadiness / fact selection / confidenceを再判断しない境界

### Currentとして使用しない

- 未実装のpost-generation grounding verification
- `Should-have`
- PR-B7等のFuture hardening

既存E2E readiness監査も、post-generation grounding verificationはMVP必須ではなく未実装が契約どおりであることを確認している。

### Phase 2B Classification

```text
Implemented MVP scope = CURRENT_VERSIONED candidate
Future hardening = FUTURE / UNRESOLVED
Document lifecycle = mixed historical-design + implemented contract
```

文書作成時の「production code変更なし」という時点記述だけを理由に、現在の実装済みscopeまで非Current扱いしない。

---

# 5. Phase 2B Resolution Table

| Conflict | Decision | Current | Not Current |
| --- | --- | --- | --- |
| Recommendation Eligibility | KEEP CURRENT SHARED ELIGIBILITY | usable Deity OR History gate | Coreの旧「除外なし」記述 |
| Recommendation Score | V2 CURRENT DESIGN | v2 current doc + backend/tests | v3 draftをCurrent正本扱いすること |
| Recommendation Signal Authority | section-scoped | Current Implementationのみ | Desired / Should / Future |
| Concierge Input Architecture | section-scoped | Current + implemented addenda | Proposed / Open Questions |
| Deep Dive Answer Generation | section-scoped | implemented MVP scope | PR-B7 / future hardening |

---

# 6. Classification Impact for Next Phase

次工程 `CURRENT_FIXED / CURRENT_VERSIONED / SUPERSEDED / UNRESOLVED` 分類へ、以下を引き渡す。

## `CURRENT_VERSIONED` candidate

- Shared Recommendation Eligibility contract
- Recommendation Score v2 current implementation contract
- recommendation-signal-authorityのCurrent Implementation部分
- concierge-input-architectureのCurrent / Implemented Addendum部分
- deep-dive-answer-generation-contractのimplemented MVP部分

## `SUPERSEDED` candidate

- Coreの「Knowledge由来のcandidate exclusionは存在しない」という時点記述
- Coreの「Eligibility Filterは候補集合をそのまま通す」という時点記述
- CoreのRecommendation Score正本をv3 Referenceへ向ける記述

## `UNRESOLVED`

- recommendation-signal-authorityのDesired / Should / Future
- concierge-input-architectureの未実装Proposed / Open Questions
- Deep Dive PR-B7 / post-generation grounding hardening

## `CURRENT_FIXED`

Phase 2Bではまだ確定しない。

Fixed Rule化には、Current Versionedな実装詳細と、長期的に維持する不変原則を次工程で分離する。

---

# 7. Canonical Reconciliation Required

Phase 2BのDecisionをCurrent canonicalへ反映するため、後続canonical cleanupでは少なくとも以下が必要になる。

1. `docs/core/recommendation-readiness.md`
   - Shared Eligibility導入前の時点記述をCurrent説明から外す
   - Governance ReadinessとShared Eligibilityを明示分離

2. `docs/core/recommendation-architecture.md`
   - Eligibility FilterをCurrent Shared Eligibilityへ整合
   - Score正本参照をv2 Current Designへ整合

3. `docs/core/architecture.md`
   - Recommendation Score正本参照をv2 Current Designへ整合

このcleanupは仕様変更ではなく、Phase 2Bで確定したCurrent truthへの文書追随である。

Fixed Rules最終確定前に実施する。

---

# 8. STOP Conditions

以下は本Decisionから推測しない。

- Eligibility条件の追加（confidence threshold等）
- deity/history以外の新Eligibility source
- v2 Score weight変更
- v3 Score rollout
- Desired Contractの自動実装扱い
- Deep Dive Future hardeningのMVP必須化

これらは別Product / Implementation判断である。

---

# 9. Phase 2B Result

Phase 2AでHOLDされた3論点について、Current仕様を確定した。

```text
Eligibility
  -> current Shared Eligibilityを維持

Score
  -> v2 Current Design + backend/testsがCurrent
  -> v3 DesignはReference

Mixed docs
  -> section-scoped classification
  -> Current / ImplementedのみCurrent候補
  -> Desired / Proposed / FutureはCurrentではない
```

Runtime変更は不要。

次工程は:

```text
CURRENT_FIXED
CURRENT_VERSIONED
SUPERSEDED
UNRESOLVED
```

の全体分類である。
