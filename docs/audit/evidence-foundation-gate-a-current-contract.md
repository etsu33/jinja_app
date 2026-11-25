# Evidence Foundation Gate A — Current Contract Audit

> **Status: Audit / Historical**
>
> **Audited commit:** `a5945398ff66df4fc3004a37073db2fdb7763875`
>
> **Scope:** Evidence Foundation Gate A
>
> 本文書は、上記commit時点におけるEvidence Foundationの現行実装契約を記録する監査snapshotである。
> Current Source of Truthを新たに定義する文書ではなく、実装・migration・domain contract・test・Adminを確認した結果を記録する。

---

## 1. 目的

Evidence Foundationの後続設計・Production wiringへ進む前に、以下4契約の現在地を推測なしで固定する。

1. Assignment current contract
2. Fact current contract
3. Source current contract
4. Provenance current contract

本監査では新しい仕様を決定しない。

また、以下も行わない。

* Ranking変更
* Recommendation変更
* DB data変更
* Production変更
* Evidence Qualificationルール変更
* 自動supersede追加
* Source relation追加
* taxonomy変更

---

## 2. Audit Base

監査時点で以下を確認した。

```text
HEAD:
a5945398ff66df4fc3004a37073db2fdb7763875

origin/develop:
a5945398ff66df4fc3004a37073db2fdb7763875
```

したがって、本監査の対象コードは監査開始時点の`origin/develop`と一致する。

主な確認対象:

* `backend/temples/models.py`
* `backend/temples/admin.py`
* `backend/temples/domain/evidence_provenance.py`
* `backend/temples/migrations/0093_shrine_knowledge_model_foundation.py`
* `backend/temples/migrations/0102_history_theme_assignment_foundation.py`
* `backend/temples/tests/test_models_history_theme_assignment.py`
* `backend/temples/tests/test_admin_history_theme_assignment.py`
* `docs/knowledge/evidence-foundation-shared-contract.md`

---

# 3. Assignment Current Contract

## 3.1 HistoryThemeAssignment

現行field:

| Field              | Contract                                                                    |
| ------------------ | --------------------------------------------------------------------------- |
| `id`               | `BigAutoField`, primary key                                                 |
| `shrine`           | `ForeignKey(Shrine)`, `CASCADE`, `related_name="history_theme_assignments"` |
| `canonical_key`    | `CharField(max_length=64)`                                                  |
| `taxonomy_version` | `CharField(max_length=8)`                                                   |
| `lifecycle`        | `ACTIVE` / `SUPERSEDED`                                                     |
| `producer`         | `CharField(max_length=32)`                                                  |
| `mechanism`        | `CharField(max_length=32)`                                                  |
| `assigned_at`      | `DateTimeField`, callerが明示指定                                                |
| `created_at`       | `DateTimeField(default=timezone.now)`                                       |

`assigned_at`と`created_at`は責務が異なる。

* `assigned_at`: semantic assignmentが実際に行われた時刻
* `created_at`: DB rowが作成された時刻

---

## 3.2 Lifecycle

`HistoryThemeAssignment.Lifecycle`が定義元。

```text
ACTIVE
SUPERSEDED
```

PR-F2時点では自動supersedeは存在しない。

lifecycle変更は明示的に行う。

---

## 3.3 Unique Constraint

現行constraint:

```text
uniq_history_theme_assignment_active_per_shrine
```

Contract:

```text
fields = ["shrine"]
condition = lifecycle == "ACTIVE"
```

したがって、

* 1 ShrineにつきACTIVEは最大1件
* SUPERSEDEDは複数保持可能
* ACTIVEとSUPERSEDEDは共存可能

となる。

---

## 3.4 Explicit Indexes

`HistoryThemeAssignment.Meta`には明示的な`indexes = [...]`定義は存在しない。

現行Metaで明示されるのは以下。

* `ordering`
* `constraints`

なお、本記述はDjango model上の明示indexについての監査結果であり、ForeignKey等によってDB側に作成されるindexの存在を否定するものではない。

---

## 3.5 clean()

`HistoryThemeAssignment.clean()`は以下を検証する。

### canonical_key

`validate_history_theme_v1_canonical_key()`を利用する。

invalidなcanonical keyは`ValidationError`になる。

以下も拒否対象としてtestで固定されている。

* unsupported namespace
* `goriyaku:*` namespace
* unknown history theme key
* blank semantic identity

### taxonomy_version

`get_current_taxonomy_version(HISTORY_THEME_TAXONOMY_NAMESPACE).version`と一致する必要がある。

現行taxonomy versionと異なる値は`ValidationError`になる。

---

## 3.6 save()

`HistoryThemeAssignment`は`save()`をoverrideしていない。

したがって、このmodelの`save()`によって以下は実行されない。

* taxonomy inference
* provenance自動生成
* auto-supersede
* `Shrine.history_theme`との自動同期
* Assignmentからlegacy fieldへの書き戻し

---

## 3.7 Legacy Boundary

`HistoryThemeAssignment`と既存`Shrine.history_theme`は独立している。

Assignment row作成によって`Shrine.history_theme`は変更されない。

また、`Shrine.history_theme`変更によって`HistoryThemeAssignment`が自動生成されることもない。

---

# 4. Fact Current Contract

Evidence FoundationのFact structureとして、少なくとも以下2modelが存在する。

* `ShrineHistory`
* `ShrineDeity`

---

## 4.1 ShrineHistory

主要field:

| Field                 | Contract                                         |
| --------------------- | ------------------------------------------------ |
| `id`                  | `BigAutoField`, primary key                      |
| `shrine`              | `ForeignKey(Shrine)`, `related_name="histories"` |
| `history_type`        | History type classification                      |
| `title`               | Fact title                                       |
| `content`             | Fact content                                     |
| `period_text`         | optional                                         |
| `event_date`          | optional                                         |
| `sort_order`          | integer                                          |
| `verification_status` | knowledge verification status                    |
| `confidence`          | knowledge confidence                             |
| `verified_at`         | optional datetime                                |
| `note`                | optional                                         |
| `created_at`          | created timestamp                                |
| `updated_at`          | updated timestamp                                |
| `sources`             | M2M → `ShrineKnowledgeSource`                    |

History type:

```text
official_origin
founding
historical_event
tradition
regional_context
editorial_summary
```

---

## 4.2 ShrineHistory Validation

`clean()`では、

```text
_validate_verified_at_consistency(
    verification_status,
    verified_at
)
```

が実行される。

verification statusと`verified_at`の整合性をmodel validationで確認する。

---

## 4.3 ShrineHistory Index

明示index:

```text
idx_shrine_history_sort
```

fields:

```text
shrine
sort_order
```

---

## 4.4 ShrineDeity

ShrineDeityにもFactとして共通するKnowledge構造が存在する。

主要field:

| Field                 | Contract                      |
| --------------------- | ----------------------------- |
| `id`                  | primary key                   |
| `shrine`              | FK → Shrine                   |
| `display_name`        | deity display name            |
| `canonical_name`      | optional canonical name       |
| `role`                | deity role                    |
| `sort_order`          | ordering                      |
| `verification_status` | verification state            |
| `confidence`          | confidence                    |
| `verified_at`         | verification timestamp        |
| `note`                | optional                      |
| `created_at`          | created timestamp             |
| `updated_at`          | updated timestamp             |
| `sources`             | M2M → `ShrineKnowledgeSource` |

したがって、Source-backed Fact構造は`ShrineHistory`だけに限定されていない。

---

# 5. Source Current Contract

## 5.1 ShrineKnowledgeSource

`ShrineKnowledgeSource`はDjango modelとして永続化される。

主要field:

| Field                 | Contract              |
| --------------------- | --------------------- |
| `id`                  | primary key           |
| `source_type`         | source classification |
| `title`               | source title          |
| `publisher`           | optional              |
| `url`                 | optional              |
| `bibliography`        | optional              |
| `accessed_at`         | optional date         |
| `verified_at`         | optional datetime     |
| `verification_status` | verification state    |
| `confidence`          | confidence            |
| `language`            | optional              |
| `note`                | optional              |
| `created_at`          | created timestamp     |
| `updated_at`          | updated timestamp     |

---

## 5.2 Fact → Source Relation

現行relation:

```text
ShrineHistory
    └── sources ── M2M ── ShrineKnowledgeSource

ShrineDeity
    └── sources ── M2M ── ShrineKnowledgeSource
```

したがってFactとSourceの物理relationは既に存在する。

---

# 6. Provenance Current Contract

## 6.1 EvidenceProvenance

`EvidenceProvenance`はDjango modelではない。

pure Pythonのimmutable domain contract:

```text
@dataclass(frozen=True)
EvidenceProvenance
```

field:

```text
producer
mechanism
assigned_at
```

DB migration責務を持たない。

---

## 6.2 Producer

定義元:

```text
backend/temples/domain/evidence_provenance.py
```

許可値:

```text
admin
curator
migration
verified_import
controlled_automation
```

---

## 6.3 Mechanism

許可値:

```text
manual_review
source_backed_import
verified_migration
controlled_rule
```

---

## 6.4 Provenance Validation

`build_evidence_provenance()`は以下を検証する。

1. producerが許可値であること
2. mechanismが許可値であること
3. assigned_atがdatetimeであること

invalidの場合、例外による暗黙処理ではなくinvalid resultを返す。

---

## 6.5 Non-responsibilities

現行`EvidenceProvenance`は以下を行わない。

* producer × mechanism pair compatibility判定
* Evidence Qualification判定
* Source Evidence判定
* semantic assignment判定
* database persistence

Provenanceは「誰が・どのmechanismで・いつAssignmentを行ったか」を表すdomain contractである。

---

# 7. Admin Current Contract

`HistoryThemeAssignment`はAdminから直接編集可能。

`HistoryThemeAssignmentAdmin`では以下を表示する。

* id
* shrine
* canonical_key
* taxonomy_version
* lifecycle
* producer
* mechanism
* assigned_at
* created_at

また、`ShrineAdmin`には`HistoryThemeAssignmentInline`が存在する。

Inline fields:

```text
canonical_key
taxonomy_version
lifecycle
producer
mechanism
assigned_at
```

Admin側にも以下の暗黙処理は存在しない。

* provenance自動生成
* taxonomy自動推論
* auto-supersede

---

# 8. Current Boundary

Gate Aで最も重要な現行境界は以下。

```text
Fact
  ↓
ShrineHistory / ShrineDeity
  ↓
ShrineKnowledgeSource
```

は既に存在する。

一方、

```text
HistoryThemeAssignment
  ↓
specific Fact / Source Evidence
```

を直接結ぶ物理relationは、監査対象commit時点では存在しない。

また、

```text
HistoryThemeAssignment
  + producer
  + mechanism
  + assigned_at
```

だけではQualified Evidenceにはならない。

現行model docstringおよびEvidence Foundation contractでは、Source Evidence linkは後続scopeとして扱われている。

本監査では、その後続relationの設計・実装方法を決定しない。

---

# 9. Gate A Result

| Gate                        | Result |
| --------------------------- | ------ |
| Assignment current contract | PASS   |
| Fact current contract       | PASS   |
| Source current contract     | PASS   |
| Provenance current contract | PASS   |

## Gate A

```text
PASS
```

Evidence Foundationの現行4契約を、監査対象commitに基づいて固定できた。

次フェーズでは、このcurrent contractを変更せずに、Evidence Qualification / Source Evidence connectionの現在地を別Gateとして確認する。

---

# 10. Audit Checklist

* [x] HistoryThemeAssignment current fields
* [x] unique constraint
* [x] explicit indexes
* [x] clean() validation
* [x] save() behavior
* [x] lifecycle definition source
* [x] producer definition source
* [x] mechanism definition source
* [x] EvidenceProvenance current fields
* [x] EvidenceProvenance model / domain contract boundary
* [x] EvidenceProvenance validation
* [x] ShrineHistory primary key / shrine relation
* [x] ShrineHistory verification fields
* [x] ShrineHistory → ShrineKnowledgeSource relation
* [x] ShrineDeity Fact structure
* [x] HistoryThemeAssignment Admin editing path
* [x] local HEAD / origin/develop SHA match
* [x] Assignment current contract frozen
* [x] Fact current contract frozen
* [x] Source current contract frozen
* [x] Provenance current contract frozen
