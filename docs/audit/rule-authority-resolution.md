# KAMI MUSUBI Rule Authority Resolution Audit

> **Status: Audit / Historical — Phase 2A**
>
> 本書は `docs/audit/rule-canonicalization-audit.md` の Phase 1 結果を入力として、
> KAMI MUSUBI の文書・Decision Record・実装・テストが「どの責務範囲でAuthorityを持つか」を
> read-onlyで再分類する Phase 2A 監査である。
>
> 本書は既存Product仕様、Recommendationロジック、Ranking / Score、Knowledge Contract、
> Backend / Frontend実装、DB、Migration、設定を変更しない。
> Conflictを解消せず、Fixed Rulesも確定しない。

## 1. Purpose

Phase 1では、Current Source候補・Reference / Archive・Rule Candidate・重複・Conflict・Stale Reference・UNRESOLVEDを抽出した。
しかし、以下の事例により「Domain README掲載の有無」だけではAuthorityを安全に判定できないことが確認された。

- Domain README未掲載でも、上位のActive正本から責務を明示委譲されている文書がある
- Domain README未掲載でも、Mother Ship DecisionがActive正本へ取り込まれている文書がある
- 実装・テストが直接参照する文書でも、Product / Architecture上の正本であるとは限らない
- 自己Statusが`Active`でも、Domain READMEで`Reference`と分類される文書がある
- 1つの文書内にCurrent ImplementationとDesired Contractが混在するものがある

本Phaseの目的は、個別仕様の正誤を決めることではなく、
**Sourceがどの責務範囲でAuthorityを持つかを判定する規則を定義し、Phase 1のAuthority不明項目を再分類すること**である。

## 2. Base / Scope

- Base branch: `develop`
- Phase 2A branch: `audit/rule-authority-resolution`
- Branch creation base: `6fc42f69ee0fb31b8d87e38fd05ad21998c12c18`
- Input audit: `docs/audit/rule-canonicalization-audit.md`

対象:

- `docs/core/`
- `docs/product/`
- `docs/knowledge/`
- `docs/analytics/`
- `docs/infra/`
- `docs/ci/`
- `docs/ops/`
- `docs/design/`
- `docs/README.md`
- Phase 1 H-1 / H-2でAuthority不明とされた文書
- 現行実装・テストから明示参照される契約 / Decision Record

非対象:

- Product判断そのもの
- Conflictの仕様解決
- 既存正本文書の修正
- Status headerの修正
- Domain READMEへの文書追加
- 実装修正
- Fixed Rulesの確定

## 3. Authority Model

Phase 2Aでは、以下のAuthority Classを使用する。

### 3.1 `DOMAIN_CANONICAL`

Domain READMEが`Active`または`正本`として明示分類している文書。

対象Domain:

- `docs/core/README.md`
- `docs/product/README.md`
- `docs/knowledge/README.md`
- `docs/analytics/README.md`

Domain README自身が「文書構成、分類、読む順番、責務を管理する入口」と宣言しているため、
**同一Domain内のActive / Reference / Archive分類はDomain READMEを分類Authorityとする。**

### 3.2 `ROOT_CANONICAL`

Domain READMEが存在しない領域について、`docs/README.md`が対象文書を明示的に「正本」として指定しているもの。

単なるリンク・案内は`ROOT_CANONICAL`の根拠にしない。

### 3.3 `DELEGATED_AUTHORITY`

`DOMAIN_CANONICAL`または`ROOT_CANONICAL`文書が、別文書へ特定責務を明示委譲しているもの。

成立条件:

1. 委譲元がCurrent Source of Truthである
2. 委譲先pathが明示されている
3. 「正本」「委譲」「契約」「詳細仕様」等として責務範囲が判別できる
4. Authorityは委譲された責務範囲に限定する

「関連文書」「参考」「監査根拠」だけでは成立しない。

### 3.4 `INCORPORATED_DECISION_RECORD`

Mother Ship Decision Record自体は一般的なCurrent Source of Truthへ昇格させない。
ただし、Current canonical contractがそのDecisionを明示的に取り込み、現行契約へ反映している場合、
**そのDecisionのscopeだけ**を決定履歴として有効とする。

実際のCurrent Ruleは原則として、Decisionを取り込んだCurrent canonical contractから読む。

### 3.5 `IMPLEMENTATION_EVIDENCE`

実装コード・テストは、Endpoint、Field、保存、Runtime判定、Fallback、Response等の
**現在の物理挙動の証拠**である。

ただし:

```text
implementation exists
!=
Product / Core / Knowledge specification authority
```

実装されているという事実だけで、未分類文書を`DOMAIN_CANONICAL`へ昇格させない。

### 3.6 `CURRENT_OPERATIONAL_REFERENCE`

Root README等から現在の運用手順として案内されているが、
「正本」または明示委譲まで確認できない運用文書。

運用手順として参照可能だが、横断Fixed RulesのAuthorityには使用しない。

### 3.7 `ORPHAN_ACTIVE`

自己StatusがActive等でも、Domain README掲載・Root canonical指定・明示委譲のいずれも確認できない文書。

自己宣言だけではCurrent canonicalへ昇格させない。

### 3.8 `ORPHAN_IMPLEMENTED_CONTRACT`

Domain README / Root canonical / delegationが確認できない一方、
実装とテストがその文書を契約として広く参照しているもの。

これは「現在挙動との結びつきが強い」ことを示すが、仕様Authorityは未解決のままとする。

### 3.9 `MIXED_CURRENT_DESIRED`

1つの文書内でCurrent Implementation、Desired Contract、Future、Should等が混在し、
文書単位でCurrent Ruleとして採用できないもの。

Section単位の再分類または文書分割が必要になるまでFixed RulesのSourceにしない。

### 3.10 `DRAFT`

文書自身がDraft / Design Audit / Desired Contract only等と明記しているもの。
現行Rule Authorityには使用しない。

### 3.11 `REFERENCE` / `ARCHIVE` / `AUDIT_HISTORY`

Domain READMEまたはAudit governanceに従い、現行ContractのAuthorityには使用しない。

### 3.12 `CONFLICT`

同一責務について、Current canonical / delegated authority / implementation evidenceが互いに異なる契約を示す状態。

**自動解決禁止。**
Phase 2BまたはMother Ship Decisionへ送る。

### 3.13 `UNRESOLVED`

上記根拠だけではAuthorityを安全に決定できない状態。
推測でCurrentへ昇格させない。

## 4. Precedence / Conflict Rule

Authorityの利用順序は「上にあるものが常に正しい」という単純な優先順位ではない。
責務ごとにSourceを選ぶ。

```text
Domain classification
  -> Domain README

Product / Architecture / Knowledge / Analytics contract
  -> DOMAIN_CANONICAL またはその DELEGATED_AUTHORITY

Current physical behavior
  -> implementation + tests

Decision lineage
  -> INCORPORATED_DECISION_RECORD

Historical finding
  -> AUDIT_HISTORY
```

重要:

- Domain READMEは同一Domain内の文書分類を管理する
- `docs/README.md`は、Domain READMEがある領域のActive / Reference / Archive分類を上書きしない
- Self Statusは補助証拠であり、Domain classificationより強くない
- Implementationは物理挙動の証拠だがProduct意図を自動決定しない
- 文書・実装・テストが食い違う場合はHOLDする

この扱いは`docs/core/README.md`の「文書、実装およびテストが食い違う場合はいずれか一つを自動的に正しいものとして扱わない」という既存境界と整合する。

## 5. Domain README Classification Resolution

### 5.1 Root README vs Domain README

Phase 1 G1の6件は、Authority conflictというより**stale navigation / classification drift**として再分類できる。

| ID | document | Phase 2A classification |
| --- | --- | --- |
| G1-1 | `docs/product/pricing.md` | `ARCHIVE`; root README側がstale navigation |
| G1-2 | `docs/product/card-visibility-renderer-split.md` | `ARCHIVE`; root README側がstale navigation |
| G1-3 | `docs/core/auth-flow.md` | `REFERENCE`; root README側が過剰案内 |
| G1-4 | `docs/product/journey-timeline-design.md` | `DOMAIN_CANONICAL`; root README側がstale Reference placement |
| G1-5 | `docs/product/reflection-timeline-design.md` | `REFERENCE`; root README側がstale current placement |
| G1-6 | `docs/product/monetization-flow-design.md` | `REFERENCE`; root README内部の二重掲載はnavigation defect |

**結果:** G1×6はPhase 2Bで仕様判断を必要としない。README cleanup候補へ送る。

### 5.2 Self Status vs Domain README

Phase 1 G3もDomain classificationで再整理する。

| ID | document | Phase 2A classification |
| --- | --- | --- |
| G3-1 | `docs/product/direction-ranking-design.md` | `REFERENCE`; self `Active`はstale metadata |
| G3-2 | `docs/knowledge/evidence-foundation-shared-contract.md` | `REFERENCE`; self `Active`はstale metadata |
| G3-3 | `docs/core/desktop-development-contract.md` | `DOMAIN_CANONICAL`; missing Status headerはmetadata gap |
| G3-4 | Knowledge正本群 | `DOMAIN_CANONICAL`; missing Status headerはmetadata gap |

Self StatusだけでDomain README分類を反転させない。

## 6. Resolved Delegated Authority Inventory

### 6.1 `docs/core/direction-response-contract.md`

**Classification: `DELEGATED_AUTHORITY`**

Evidence:

- `docs/core/architecture.md` が方位計算と表示契約の具体的な省略条件・レスポンス形式を
  `docs/core/direction-response-contract.md`へ明示委譲している。

Scope:

- `direction_reference`表示契約
- client側再計算禁止
- malformed / unknown method時の縮退境界

Core README未掲載はindex gapだが、委譲された責務のAuthority自体は成立する。

### 6.2 `docs/ops/direction-fail-safe.md`

**Classification: `DELEGATED_AUTHORITY`**

Delegation chain:

```text
docs/core/architecture.md
  -> docs/core/direction-response-contract.md
      -> docs/ops/direction-fail-safe.md
```

`direction-response-contract.md`は、障害時の共通縮退条件と運用手順について
`direction-fail-safe.md`を「正本」と明記している。

加えてCurrent Product canonicalである`compass-product-contract.md` / `compass-mvp-runtime-contract.md`が
日盤・時盤のMVP対象外 / 追加禁止を同文書から継承している。

Scope:

- Direction fail-safe
- 日盤・時盤をMVPへ混在させない制約
- 方位機能障害時に通常推薦を維持する縮退契約

### 6.3 `docs/ci/testing_policy.md`

**Classification: `DELEGATED_AUTHORITY`**

`docs/core/runtime-security-baseline.md`が、テスト種別・外部API呼び出し方針・CI失敗時判断基準について
`docs/ci/testing_policy.md`を正本指定している。

### 6.4 `docs/infra/env_policy.md`

**Classification: `DELEGATED_AUTHORITY`**

`docs/core/runtime-security-baseline.md`から環境変数運用の正本として参照され、
`docs/README.md`からも環境変数の現行参照先として案内される。

### 6.5 `docs/product/recommendation-v4-frontend-adapter-contract.md`

**Classification: `DELEGATED_AUTHORITY`**

Evidence:

- `docs/core/recommendation-reason-contract.md`が`recommendation_reason_v4_detail`のWeb/Mobile表示Adapter責務を本書へ委譲
- `docs/core/recommendation-architecture.md`もFrontend Adapter契約として参照

Scope:

- Reason V4 detailのWeb/Mobile表示変換
- Fact text priority
- structured / legacy fallback

### 6.6 `docs/product/history-recommendation-navigation-design.md`

**Classification: `DELEGATED_AUTHORITY`（Navigation scope）**

Evidence:

- Active Analytics canonical `docs/analytics/consultation-history-events.md` はNavigation契約を自身の対象外とし、変更時の更新先として本書を指定
- `docs/core/openapi-contract-governance.md`からも関連契約として参照

Boundary:

- History navigation design: 本書
- 正確なHistory API物理挙動: Django実装 + Backend tests
- Reason表示: `recommendation-v4-frontend-adapter-contract.md`

### 6.7 `docs/knowledge/recommendation-eligibility-contract.md`

**Classification: `DELEGATED_AUTHORITY + IMPLEMENTATION_EVIDENCE + CONFLICT`**

Evidence:

- Knowledge canonical `docs/knowledge/shrine-knowledge-contract.md` は、Shared Recommendation Eligibilityの適格条件を
  `docs/knowledge/recommendation-eligibility-contract.md`へ明示委譲している
- `backend/temples/services/concierge_chat_candidates.py`が同契約を参照し、usable Deity / History Fact有無で候補をfilterする
- Backend service/API testsとCompass frontendが`recommendation_eligibility_zero_candidates`を独立stateとして固定している

ただしCore canonicalとのConflictは解消しない。§10参照。

### 6.8 `docs/analytics/compass-analytics-contract.md`

**Classification: `DELEGATED_AUTHORITY`（cross-domain）**

`docs/product/compass-product-logic-evaluation-framework.md` §Canonical Contractsが
Compass Analytics Contractとして本書を明示列挙している。

Scope:

- Compass Event / Payload
- Recommendation attribution
- Action source propagation
- Compass analytics privacy boundary

### 6.9 `docs/analytics/compass-posthog-query-contract.md`

**Classification: `DELEGATED_AUTHORITY`（cross-domain）**

同じくCurrent Product canonicalがCompass PostHog Query Contractとして明示列挙する。

Scope:

- PostHog query semantics
- result_state measurement interpretation
- calculationMethod segmentation

Analytics README未掲載はindex gapとして残る。

## 7. Root Canonical / No-Domain-README Resolution

### 7.1 `docs/design/design-token.md`

**Classification: `ROOT_CANONICAL`**

`docs/README.md` §Design・UI基盤が、Web / Mobile共通Design Token、UI基盤、視覚言語の正本文書として明示する。

### 7.2 `docs/infra/render-startup.md`

**Classification: `CURRENT_OPERATIONAL_REFERENCE`**

`docs/README.md`のRender現行案内と実運用runbookから参照されるが、
現時点で「正本」またはCurrent canonicalからの契約委譲は確認できない。

Fixed RulesのSourceには使用しない。

### 7.3 `docs/ops/production-smoke-checklist.md`

**Classification: `CURRENT_OPERATIONAL_REFERENCE`**

`docs/README.md`が本番確認手順として案内し、`production-smoke-log.md`が確認手順として参照する。
ただし横断契約の正本指定ではない。

### 7.4 `docs/ops/production-smoke-log.md`

**Classification: `AUDIT_HISTORY / OPERATIONAL_LOG`**

時点付き確認結果であり、Current Rule Authorityには使用しない。

### 7.5 Authority unresolved operational / design docs

以下はRoot canonical指定・Domain index・Current canonicalからの委譲を確認できない。

| document | classification |
| --- | --- |
| `docs/ops/guest-data-retention.md` | `UNRESOLVED` |
| `docs/ops/production-bff-hardening.md` | `UNRESOLVED` |
| `docs/design/premium-meaning-ui-direction.md` | `UNRESOLVED` |

`guest-data-retention.md`は自身でPrivacy Policyとの不一致・定期実行未設定を記録しており、Fixed Ruleへ昇格させない。

## 8. Phase 1 H-1 Reclassification

| document | Phase 2A classification | result |
| --- | --- | --- |
| `docs/core/direction-response-contract.md` | `DELEGATED_AUTHORITY` | resolved |
| `docs/product/compass-product-direction-decision.md` | `INCORPORATED_DECISION_RECORD` | resolved, scoped |
| `docs/product/concierge-input-architecture.md` | `ORPHAN_ACTIVE + IMPLEMENTATION_EVIDENCE` | unresolved authority |
| `docs/product/history-recommendation-navigation-design.md` | `DELEGATED_AUTHORITY` | resolved |
| `docs/product/recommendation-signal-authority.md` | `MIXED_CURRENT_DESIRED + ORPHAN_ACTIVE` | unresolved authority |
| `docs/product/recommendation-v4-frontend-adapter-contract.md` | `DELEGATED_AUTHORITY` | resolved |
| `docs/product/recommendation-result-information-architecture.md` | `DRAFT` | excluded from current rules |
| `docs/product/recommendation-result-observation-policy.md` | `ORPHAN_ACTIVE_POLICY` | unresolved authority |
| `docs/product/deep-dive-answer-generation-contract.md` | `ORPHAN_IMPLEMENTED_CONTRACT` | unresolved authority |
| `docs/knowledge/recommendation-eligibility-contract.md` | `DELEGATED_AUTHORITY + CONFLICT` | authority resolved, contract conflict remains |
| `docs/knowledge/recommendation-evidence-review-contract.md` | `ORPHAN_OPERATIONAL_CONTRACT` | unresolved authority |
| `docs/knowledge/shrine-expansion-candidate-master-contract.md` | `ORPHAN_OPERATIONAL_CONTRACT` | unresolved authority |
| `docs/analytics/compass-analytics-contract.md` | `DELEGATED_AUTHORITY` | resolved |
| `docs/analytics/compass-posthog-query-contract.md` | `DELEGATED_AUTHORITY` | resolved |

Phase 1 H-1 14件のうち、Authority自体をresolvedとできるのは7件 + scoped Decision Record 1件。
残りはCurrent implementation / operationとの結びつきがあっても、Domain classificationまたは明示委譲が不足しているためHOLDする。

## 9. Important Orphan Findings

### 9.1 `docs/product/concierge-input-architecture.md`

自己Statusは`Active（Architecture Decision）`で、Backend / Web / testsがLevel 1 / 2 / 3契約として広く参照している。

Examples:

- `backend/temples/domain/visit_preference.py`
- `backend/temples/services/concierge_input_contract.py`
- `backend/temples/api_views_concierge.py`
- Web request payload / type / UI
- Concierge input tests

しかし、Product READMEの正本一覧へ未掲載で、確認したCurrent canonicalからの明示委譲もない。

**Conclusion:** Current physical behaviorとの結びつきは強いが、Product Authorityは未確定。
Fixed Rule Sourceとして全文採用しない。

### 9.2 `docs/product/recommendation-signal-authority.md`

自己StatusはActiveかつ「正本」と宣言するが、同じ冒頭で以下を明示している。

- Current ImplementationとDesired Authorityを区別する
- Desired Contract / Should / Future / Follow-upは未実装
- 最終決定・実装着手はMother Shipへ委ねる

実装から参照される一方、文書単位でCurrent Ruleへ昇格するとDesired Contractを現行仕様と誤認する。

**Conclusion:** `MIXED_CURRENT_DESIRED`。Section-scoped canonicalizationまたは文書分割が必要。

### 9.3 `docs/product/recommendation-result-information-architecture.md`

自己Statusが`Draft（設計監査のみ、production code変更なし）`で、Desired ContractとMother Ship判断待ちを明示する。

**Conclusion:** `DRAFT`。Current Fixed Rulesから除外。

### 9.4 `docs/product/recommendation-result-observation-policy.md`

Status headerはないが、自身をResult IA v2のObservation / Measurement移行の「単一の正本」とし、Freeze Scopeを規定する。
複数の後続auditはこのFreezeをgoverning policyとして扱っている。

ただし、Product README掲載・Current canonicalからの明示委譲は確認できない。

**Conclusion:** `ORPHAN_ACTIVE_POLICY`。運用上は参照されているが、Product Authorityは未解決。

### 9.5 `docs/product/deep-dive-answer-generation-contract.md`

作成時点の本文は「設計・監査のみ」と記録する一方、現在はBackend retrieval / answer / API / serializer、Frontend、testsが
本書を実装契約として直接参照している。

**Conclusion:** `ORPHAN_IMPLEMENTED_CONTRACT`。
現在の物理挙動の根拠として強いが、Product README未掲載かつ明示delegationを確認できないため、Product AuthorityはHOLD。

### 9.6 `docs/knowledge/recommendation-evidence-review-contract.md`

文書自身はRecommendation Evidence human reviewのnormative contractを定義し、後続のExpansion audit chainが利用している。
一方、Knowledge README未掲載で、Current Knowledge canonicalからの明示delegationは確認できない。

**Conclusion:** `ORPHAN_OPERATIONAL_CONTRACT`。

### 9.7 `docs/knowledge/shrine-expansion-candidate-master-contract.md`

`Status: ACTIVE`、Effective from 2026-09-10、500社Expansion pre-import Candidate lifecycleを定義する。
後続Wave0 audit chainで運用されているが、Knowledge README未掲載である。

**Conclusion:** `ORPHAN_OPERATIONAL_CONTRACT`。
ScopeはExpansion pipelineに限定し、横断Fixed Rulesへ昇格させない。

## 10. Decision Record Exceptions

### 10.1 Compass Direction Decision

`docs/product/compass-product-direction-decision.md`

**Classification: `INCORPORATED_DECISION_RECORD`**

Evidence:

- Current canonical `compass-product-contract.md`がSection 2.2のFinal Product Promiseへ反映
- `compass-mvp-runtime-contract.md`がFinal Direction Logic Option CをContract Targetとして取り込み
- `backend/temples/services/compass_runtime.py`が実装根拠として参照

Decision Record全体をCurrent canonicalへ昇格させず、Current Ruleは取り込み先contractから読む。

### 10.2 Design Token Mother Ship Decisions

Phase 1 D-4で確認済みの以下Decision Recordは、Current `docs/design/design-token.md`から決定済み事項として参照される。

- `docs/audit/design-token-stage3-neutral-semantic-decision.md`
- `docs/audit/design-token-stage3-dark-surface-decision.md`
- `docs/audit/design-token-stage4-mother-ship-decisions.md`
- `docs/audit/design-token-stage4-d3-semantic-decisions.md`

**Classification: `INCORPORATED_DECISION_RECORD`（scope限定）**

Current Ruleの通常参照先は`docs/design/design-token.md`とする。

### 10.3 Implementation -> Audit direct references

Phase 1 D-3で検出した、実装が`docs/audit/*`の判定式・安全規則・設計判断を直接参照する経路は、
**参照されているという事実だけではDecision Record Authorityを付与しない。**

分類:

```text
IMPLEMENTATION_EVIDENCE
+
AUDIT_DEPENDENCY
+
UNRESOLVED_AUTHORITY（canonical incorporationがない場合）
```

後続でCurrent canonicalへ移設 / incorporationするかを別途判断する。

## 11. Authority Conflicts After Resolution

Phase 1の`CONFLICT 15件`をAuthority Modelで再分類すると、多くは仕様Conflictではなくclassification / navigation driftへ落とせる。

### 11.1 Resolved as metadata / navigation drift

- G1-1〜G1-6: Domain README classificationを採用。root navigation drift
- G3-1〜G3-2: Domain README classificationを採用。self Status drift
- G4-3: `docs/core/openapi-contract-governance.md`がOpenAPI Authorityを管理するため、root `docs/README.md`の`openapi.yaml`案内はstale navigation

これらはPhase 2BでProduct仕様判断を必要としない。

### 11.2 Real Contract Conflict: Recommendation Eligibility

**Status: `CONFLICT / HOLD`**

Core canonical:

- `docs/core/recommendation-readiness.md`
  - Runtime candidate exclusionを責務外とする
  - 旧Readiness LevelをSupersededとする
  - audit結果としてKnowledge完全性を候補除外に使っていない旨を記載
- `docs/core/recommendation-architecture.md`
  - Eligibility Filter段階は「現状は明示的な除外を行わない」と記載

Knowledge delegated authority + implementation:

- `docs/knowledge/shrine-knowledge-contract.md`
  - Shared Recommendation Eligibility条件を`recommendation-eligibility-contract.md`へ委譲
- `docs/knowledge/recommendation-eligibility-contract.md`
  - usable Deity FactまたはHistory Factを最低1件要求
- `backend/temples/services/concierge_chat_candidates.py`
  - eligibility filterを実装
- Backend / Frontend tests
  - eligibility zero candidatesを独立Product stateとして固定

これは「ORPHAN文書がcanonicalに逆らっている」問題ではない。
**Current canonical delegation chain + current implementationが、別のCurrent Core canonical記述と衝突している。**

Phase 2Aでは解消しない。

### 11.3 Real Authority Conflict: Score v3 designation

Phase 1 G4-1 / G4-2:

- `docs/core/architecture.md` / `docs/core/recommendation-architecture.md` がScoreのSignal / Component / Weight / 計算式の正本として
  `docs/analytics/recommendation-score-v3-design.md`を指定
- Analytics READMEは同文書を`Reference`に分類

**Status: `CONFLICT / HOLD`**

Domain classificationとcross-domain canonical designationが衝突しているため、Phase 2Bへ送る。

### 11.4 Mixed Authority: Analytics Dashboard

`docs/analytics/direction-analytics-dashboard.md`はAnalytics README上Activeだが、自己Statusに
`Proposed Dashboard Configuration / Implementation Active`が混在する。

**Status: `MIXED_CURRENT_DESIRED`**

文書全体をFixed Rule Sourceにせず、Current実装部分と提案部分を分ける必要がある。

### 11.5 Mixed Authority: Recommendation Signal Authority

§9.2のとおり、Current ImplementationとDesired Contractが同一文書に混在する。

**Status: `MIXED_CURRENT_DESIRED / HOLD`**

## 12. Stale References

Phase 1 G6はAuthority conflictではなく、原則としてstale reference / navigation debtとして維持する。

特に:

- `shrine-knowledge-contract.md`
- `shrine-profile-spec.md`
- `shrine-data-guide.md`

に残るSupersededなReadiness Level参照は、Current Ruleとして使用しない。

Phase 2Aは既存正本文書を変更しないため、修正は別PR候補とする。

## 13. Out-of-index 20 Documents

Phase 1で内容未精査とした以下8ディレクトリ・計20文書は、
Domain README・Root current index・Current canonical delegationが確認されていない。

- `docs/concierge/` 3
- `docs/meaning-layer/` 5
- `docs/mobile/` 7
- `docs/ui/` 1
- `docs/triage/` 1
- `docs/runbooks/` 1
- `docs/migration-audit/` 1
- `docs/llm/` 1

Phase 2A classification:

**`UNRESOLVED_ORPHAN_SCOPE`**

内容を読まずにCurrent Rule Authorityへ昇格させない。
Phase 3 Fixed Rules抽出対象からは除外し、必要なDomainのcanonicalから明示参照された場合のみ再評価する。

補足:

`docs/llm/overview.md`は存在するが、root `docs/README.md`が現在も「将来追加予定」と記載しており、少なくともCurrent canonicalとして扱える状態ではない。

## 14. Proposed Authority Resolution Contract

Phase 3でFixed Rulesを抽出する際の作業規則として、以下を提案する。

```text
R1. Indexed domainではDomain READMEのActive / Reference / Archive分類を使う。
R2. Domain READMEが無い領域では、root READMEの明示的な「正本」指定のみROOT_CANONICALとする。
R3. Current canonicalから特定責務を明示委譲された文書はDELEGATED_AUTHORITYとする。
R4. Delegated Authorityは委譲scopeを越えて拡張しない。
R5. Self StatusだけではCurrent canonicalへ昇格しない。
R6. Implementation / testsはCurrent physical behaviorのAuthorityであり、Product意図を自動決定しない。
R7. Mother Ship Decision Recordは、Current canonicalへ取り込まれたscopeだけ有効とする。
R8. Current / Desired / Futureが混在する文書は文書単位でFixed Rule Sourceにしない。
R9. Reference / Archive / Audit HistoryからCurrent Fixed Ruleを直接抽出しない。
R10. Canonical / delegated contractとimplementationが食い違う場合はCONFLICT / HOLDとする。
R11. root READMEとDomain READMEが分類で食い違う場合、Domain READMEの分類を採用しroot側をnavigation driftとして扱う。
R12. Superseded概念を参照するstale文言はCurrent Ruleへ昇格しない。
```

本書はAuditであり、この12項目自体を新たな永久Fixed Rulesとして確定しない。
Phase 3の抽出手順として利用し、必要ならCore governanceへ別PRで正本化する。

## 15. Mother Ship Decisions Required

Phase 2AでAuthority構造だけでは解決できない項目。

### M1. Recommendation Eligibility Contract Conflict

選択肢を本書では選ばない。

- Core canonicalを現行runtimeへ更新する
- Runtime eligibility gateをCore canonicalへ合わせて撤去 / 変更する
- 別のProduct eligibility方針を決め、Core / Knowledge / runtimeを同時に再整合する

Phase 2Bで意図した仕様を確認する必要がある。

### M2. Score v3 Authority Conflict

`recommendation-score-v3-design.md`をCurrent score contractへ昇格するのか、ReferenceのままとしCore側参照先を別Current contractへ変更するのかを決める必要がある。

### M3. Recommendation Signal Authority document lifecycle

`recommendation-signal-authority.md`を:

- Current / Desiredに分割する
- Section statusを導入する
- Product READMEへCurrent部分だけを正本として取り込む
- Reference / Decision recordとして再分類する

のどれにするか判断が必要。

### M4. Concierge Input Architecture authority

実装が広く依存する`concierge-input-architecture.md`をProduct canonicalへ正式採用するか、
現行契約部分を既存canonicalへ移設するか判断が必要。

### M5. Deep Dive contract authority

実装済みの`deep-dive-answer-generation-contract.md`をCurrent Product contractとしてindexするか、
実装済み責務だけを別Active contractへ整理するか判断が必要。

### M6. Result Observation Policy

Freeze policyを現在も有効なProduct policyとして維持するか、観測完了に伴い履歴化するかを確認する必要がある。

### M7. Expansion operational contracts

以下をKnowledge canonicalへ取り込むか、Expansion専用operations contractとして別indexを作るか判断が必要。

- `recommendation-evidence-review-contract.md`
- `shrine-expansion-candidate-master-contract.md`

### M8. Orphan domain strategy

`infra / ci / ops / design`およびout-of-index directoriesについて、Domain READMEを追加するか、
Core / Productからのexplicit delegation方式を継続するかを決める必要がある。

## 16. Next Phase Input

### 16.1 Phase 2Bへ送るもの

仕様Conflictとして優先的に解決が必要:

1. Recommendation Eligibility — Core vs Knowledge delegated contract vs runtime
2. Recommendation Score v3 source designation — Core vs Analytics classification
3. Mixed Current / Desired docsのCurrent scope確定

### 16.2 Phase 3 Fixed Rules抽出で使用可能なSource

- `DOMAIN_CANONICAL`
- `ROOT_CANONICAL`
- `DELEGATED_AUTHORITY`（scope内のみ）
- Current implementation/tests（物理挙動確認用）

使用禁止:

- `DRAFT`
- `REFERENCE`
- `ARCHIVE`
- `AUDIT_HISTORY`
- `ORPHAN_*`
- `MIXED_CURRENT_DESIRED`の未分類section
- `CONFLICT`
- `UNRESOLVED`
- Superseded rule

## 17. Phase 2A Result

Phase 1の「Domain READMEに載っていない = Authority不明」という判定を、
**明示delegation / root canonical / scoped Decision incorporation / implementation evidence**を区別するモデルへ更新した。

主な結果:

- Domain READMEは同一Domain内の分類Authorityとして維持
- root `docs/README.md`はDomain classificationを上書きしない
- `direction-response-contract.md` / `direction-fail-safe.md` / `testing_policy.md`等のdelegated authorityを確認
- `recommendation-v4-frontend-adapter-contract.md` / History navigation contractのdelegated authorityを確認
- Recommendation Eligibility contractはorphanではなくKnowledge canonicalからのdelegated authorityであることを確認
- Compass analytics 2契約はProduct canonicalからのcross-domain delegated authorityを確認
- Mother Ship Decision Recordはscope限定のincorporated decisionとして扱う
- implementation-only参照はProduct authorityへ自動昇格させない
- G1 / G3等の多くを真正Conflictではなくmetadata / navigation driftへ再分類
- Recommendation EligibilityとScore v3 source designationは真正ConflictとしてHOLD

## 18. Change Boundary

このPhase 2Aで変更するのは本監査文書1件のみ。

```text
docs/audit/rule-authority-resolution.md
```

変更しないもの:

- existing Core / Product / Knowledge / Analytics docs
- code
- tests
- config
- DB
- migration
- production state

Rollbackは本監査文書の削除のみで成立する。
