# Evidence Link Responsibility Gate B

## Status

**PASS**

Gate Bでは、Evidence Linkの責務、関係境界、cardinality、および削除時の論理契約を確定する。

本GateではDjango model、field、constraint、migration等の物理schemaは確定しない。

---

## 1. Purpose

Evidence Foundationにおいて、Semantic Assignmentとその根拠となるStored Factの関係を明示し、Derivedな意味から根拠Factまでtrace可能な構造を定義する。

Gate Aで確認した既存のFact / Source / Provenance / Assignment契約を変更せず、その間に必要となるEvidence Linkの責務だけを確定する。

---

## 2. Responsibility

Evidence Linkの責務を次の1文で定義する。

> **Evidence Link = Semantic Assignmentと、その根拠となるStored Factのtraceabilityを表現する構造**

Evidence LinkはSemantic AssignmentそのものでもStored Factそのものでもない。

Semantic Assignmentが「なぜその意味を持つのか」を、根拠として使用されたStored Factまで追跡可能にするrelationである。

---

## 3. Layer Boundary

Evidence Linkが表現する関係は以下とする。

```text
Semantic Assignment
        │
        │ Evidence Link
        ▼
Stored Fact
        │
        │ existing Fact → Source relation
        ▼
ShrineKnowledgeSource
```

Evidence Linkは、

```text
Semantic Assignment → Stored Fact
```

のtraceabilityを所有する。

以下の直接relationはEvidence Linkの責務ではない。

```text
Semantic Assignment → ShrineKnowledgeSource
```

SourceへのtraceabilityはStored Factを経由する。

したがって、SourceをSemantic Assignmentへ直接紐付ける構造はGate Bの契約に含めない。

---

## 4. Fact → Derived Relationship

Evidence Linkは、Stored FactからDerived / Meaning Layerへ至る根拠関係を表現する。

概念上の方向は以下とする。

```text
Stored Fact
    ↓ evidence
Semantic Assignment
```

物理的な参照方向やForeignKeyの向きはGate Bでは決定しない。

Gate Bで確定するのは、Evidence Linkがこの2つのdomain object間のtraceabilityを担当するという責務のみである。

---

## 5. Source Verification Boundary

Evidence LinkはSource verificationを所有しない。

以下はEvidence Linkの責務外とする。

* Sourceのverification status
* Sourceのconfidence
* Sourceのverified_at
* Source自体の品質判定
* Sourceの取得方法
* FactがSourceによって十分裏付けられているかの判定

既存のFact / Source側のverification contractをEvidence Linkへ移動しない。

Evidence LinkはSource verification結果を生成・更新する構造ではない。

---

## 6. Evidence Qualification Boundary

Evidence LinkはEvidence Qualification結果を所有しない。

Evidence Linkの存在そのものを、

```text
qualified = true
```

とは扱わない。

Evidence LinkはQualification判定に必要となるtraceabilityを提供し得るが、Qualificationの判定主体ではない。

したがって、

```text
Evidence Link exists
≠
Qualified Evidence
```

とする。

Evidence Qualificationの判定ルール、dimension、result persistence等は別責務として維持する。

---

## 7. Recommendation Boundary

Evidence LinkはRecommendation情報を所有しない。

以下をEvidence Linkへ含めない。

* recommendation score
* recommendation reason
* recommendation rank
* consultation-specific state
* user input
* recommendation eligibility
* Recommendation API response情報

Evidence LinkはKnowledge / Evidence Foundationの構造であり、Recommendation Runtimeの状態を保持しない。

Evidence Linkが存在することだけを理由としてRecommendationへの採用を決定しない。

---

## 8. Ranking Boundary

Evidence LinkはRanking情報を所有しない。

以下をEvidence Linkへ含めない。

* ranking score
* favorite count
* view count
* ranking position
* popularity
* ranking weight

RankingとEvidence FoundationはGate Bでは接続しない。

---

## 9. Assignment Evidence Cardinality

### Decision

**MULTIPLE**

1つのSemantic Assignmentは、複数のStored FactをEvidenceとして持つことができる。

概念構造は以下とする。

```text
Semantic Assignment A
        │
        ├── Evidence Link 1 ── Stored Fact 1
        ├── Evidence Link 2 ── Stored Fact 2
        └── Evidence Link 3 ── Stored Fact 3
```

Semantic Assignmentの根拠を単一Factへ限定しない。

複数の独立したStored Factが同一Semantic Assignmentを支える場合、それぞれを独立したEvidenceとしてtrace可能にする。

### Non-goal

Gate Bでは以下を決定しない。

* Evidence件数の上限
* Evidenceの優先順位
* primary evidenceという概念
* Evidence weight
* Evidence score
* Evidence同士の順序

---

## 10. Fact Reuse

### Decision

**REUSABLE**

1つのStored Factは、複数のSemantic AssignmentのEvidenceとして利用可能とする。

概念構造は以下とする。

```text
Stored Fact 1
     │
     ├── Evidence Link 1 ── Semantic Assignment A
     └── Evidence Link 2 ── Semantic Assignment B
```

Stored FactはFact Layerの正本であり、特定のSemantic Assignment専用データとして扱わない。

同一Factを別Assignmentで利用するためだけにStored Factを複製することを要求しない。

---

## 11. Logical Cardinality

B-1およびB-2のDecisionから、Semantic AssignmentとStored Factの論理関係はmany-to-manyとなる。

```text
Semantic Assignment
        N
        │
        │ Evidence Link
        │
        M
Stored Fact
```

ただし、これはdomain上のcardinalityを表す。

Gate BではDjangoの`ManyToManyField`、中間model、ForeignKey構成等の物理実装方法を確定しない。

---

## 12. Evidence Deletion Semantics

「Evidence削除」は曖昧な表現となるため、以下を別々に定義する。

1. Evidence Linkの削除
2. Stored Factの削除

---

### 12.1 Evidence Link Delete

Evidence Linkを削除した場合、削除対象はrelationのみとする。

```text
Evidence Link DELETE
        │
        ├── Semantic Assignment KEEP
        └── Stored Fact KEEP
```

Evidence Link削除によって以下を削除しない。

* Semantic Assignment
* Stored Fact
* ShrineKnowledgeSource

Evidence Linkはrelationであり、その削除をFactやAssignmentの所有権削除として扱わない。

---

### 12.2 Stored Fact Delete

Stored FactがEvidence Linkから参照されている場合、そのStored Factの削除を許可しない。

```text
Stored Fact
    ↑
Evidence Link exists

→ Stored Fact DELETE BLOCK
```

Stored Factを削除する必要がある場合は、先にそのFactを参照しているEvidence Linkを明示的に解除する。

```text
1. Evidence Linkを解除
2. Stored FactへのEvidence参照が存在しないことを確認
3. Stored Factを削除
```

これにより、Semantic Assignmentが存在しているにもかかわらず根拠Factだけが暗黙に消失する状態を防止する。

Gate Bでは、この論理契約をDjangoのどの`on_delete`実装へ変換するかは決定しない。

---

## 13. Assignment Delete Semantics

### Decision

**LINK_DELETE_ONLY**

Semantic Assignmentを削除した場合、そのAssignmentに属するEvidence Linkは削除する。

ただしEvidence Linkが参照していたStored Factは削除しない。

```text
Semantic Assignment DELETE
        │
        ▼
Evidence Link DELETE
        │
        └── Stored Fact KEEP
```

さらにStored Factが参照しているShrineKnowledgeSourceも削除しない。

Assignment削除はDerived / Semantic Layerの削除であり、Stored Fact Layerの削除へ伝播させない。

---

## 14. Lifecycle Boundary

既存Semantic Assignmentがlifecycleを持つ場合、

```text
ACTIVE
SUPERSEDED
```

等のlifecycle transitionとhard deleteは別概念として扱う。

Gate Bの「Assignment削除時のEvidence Link」はhard delete時のrelation整合性を定義するものであり、Assignmentのlifecycle policyを変更するものではない。

Gate Bでは以下を決定しない。

* ACTIVE → SUPERSEDED時にEvidence Linkを変更するか
* supersede時にEvidenceを複製するか
* superseded AssignmentのEvidence保持期間
* auto supersede
* Assignment versioning

これらは必要になった時点で別Gateとして定義する。

---

## 15. Ownership Summary

| Concern                                        | Evidence Link owns? |
| ---------------------------------------------- | ------------------- |
| Semantic Assignment → Stored Fact traceability | YES                 |
| 1 Assignment → multiple Stored Facts           | YES                 |
| 1 Stored Fact → multiple Assignments           | YES                 |
| Source verification                            | NO                  |
| Fact verification                              | NO                  |
| Evidence Qualification result                  | NO                  |
| Recommendation                                 | NO                  |
| Ranking                                        | NO                  |
| Source metadata                                | NO                  |
| Stored Fact lifecycle                          | NO                  |
| Semantic Assignment lifecycle                  | NO                  |

---

## 16. Delete Contract Summary

| Operation                       | Evidence Link           | Semantic Assignment | Stored Fact    | Source                      |
| ------------------------------- | ----------------------- | ------------------- | -------------- | --------------------------- |
| Evidence Link delete            | DELETE                  | KEEP                | KEEP           | KEEP                        |
| Assignment delete               | DELETE                  | DELETE              | KEEP           | KEEP                        |
| Referenced Stored Fact delete   | KEEP / reference exists | KEEP                | BLOCK          | KEEP                        |
| Unreferenced Stored Fact delete | N/A                     | KEEP                | DELETE allowed | Existing Source contractに従う |

Source自体の削除contractはGate Bでは変更・定義しない。

---

## 17. Explicitly Out of Scope

Gate Bでは以下を確定しない。

### Schema

* model名
* table名
* ForeignKey構成
* GenericForeignKey使用可否
* ContentType使用可否
* Django ManyToManyField使用可否
* through model構成
* `on_delete`の具体的指定
* index
* unique constraint
* check constraint
* migration

### Evidence Link fields

* rationale
* evidence_type
* created_at
* created_by
* producer
* mechanism
* confidence
* verification status
* qualification result
* priority
* weight

これらが必要かどうかをGate Bでは判断しない。

### Other domains

* Recommendation接続
* Ranking接続
* Concierge接続
* Premium接続
* Analytics接続
* API schema変更
* Serializer変更
* Production data migration
* taxonomy変更
* Evidence Qualification rule変更

---

## 18. Gate B Decisions

Mother Ship Decisionを以下で固定する。

```text
EVIDENCE_LINK:
Semantic Assignmentと、その根拠となるStored Factのtraceabilityを表現する構造

B-1 Assignment Evidence Cardinality:
MULTIPLE

B-2 Fact Reuse:
REUSABLE

B-3 Evidence Delete:
EVIDENCE_LINK と STORED_FACT を別々に定義

EVIDENCE_LINK:
Linkのみ削除。
Assignment / Stored Fact / Sourceは削除しない。

STORED_FACT:
Evidence Linkから参照されている間は削除を許可しない。
削除には先にEvidence Linkの明示的解除が必要。

B-4 Assignment Delete:
LINK_DELETE_ONLY

Assignment削除時はEvidence Linkを削除する。
Stored Fact / Sourceは削除しない。
```

---

## 19. Gate B Acceptance Criteria

以下をすべて満たした場合、Gate BをPASSとする。

* [x] Evidence Linkの責務が1文で定義されている
* [x] Fact → Derivedのrelationである
* [x] Source → Derivedの直接relationではない
* [x] Source verificationをEvidence Linkが所有しない
* [x] Evidence Qualification resultをEvidence Linkが所有しない
* [x] Recommendation情報をEvidence Linkが所有しない
* [x] Ranking情報をEvidence Linkが所有しない
* [x] 1 Assignmentに複数Evidenceを許可する
* [x] 1 Factを複数Assignmentで再利用可能とする
* [x] Evidence Link削除とStored Fact削除を別々に定義する
* [x] Assignment削除時のEvidence Link挙動を定義する

**Gate B Result: PASS**

---

## 20. Next Gate

次工程は以下とする。

```text
Gate C — Evidence Link Schema Contract
```

Gate Cで初めて、Gate Bで固定した責務を満たすための物理schemaを検討する。

主な確認対象候補は以下。

* Evidence Linkが参照するAssignment model
* Evidence Linkが参照可能なStored Fact model
* 複数Fact typeの表現方法
* Linkの最小field
* duplicate Evidence Linkの扱い
* deletion contractのDjango実装
* constraint
* migration strategy

Gate C開始前にRecommendation、Ranking、Qualification等へ責務を拡張しない。
