# Shrine / Goriyaku / Detail API Contract Audit

**Status**: AUDIT COMPLETE / MOTHER SHIP DECISIONS RECORDED
**Branch**:
> `audit/shrine-goriyaku-detail-api-contract` **Scope**: Shrine / GoriyakuTag / Evidence Foundation / Shrine Detail API
> / Google Spreadsheet / Local DB reproducibility **Out of scope**: Production DB mutation, Google Spreadsheet mutation,
> Recommendation ranking change, Purpose mapping change, new taxonomy creation, data deletion, local DB destructive
> rebuild

---

## 1. Purpose

This audit establishes the current data contract across:

- `Shrine`
- `GoriyakuTag`
- `Shrine.goriyaku`
- `Shrine.goriyaku_tags`
- `ShrineGoriyakuAssignment`
- Goriyaku Evidence Foundation v1
- Shrine Knowledge models
- Shrine Detail API
- Google Spreadsheet `神社のDB`
- local PostgreSQL `jinja_db`
- Production-compatible bootstrap path

The goal is to separate:

1. **Stored canonical data**
2. **Runtime / Recommendation configuration**
3. **Derived API values**
4. **Identity / coordinate audit metadata**
5. **Evidence Foundation semantic identity**

Mother Ship decisions recorded in this document are limited to the explicitly marked FINAL decisions in Section 30. All other product, taxonomy, ranking, and runtime decisions remain outside the scope of this audit.


---

# 2. Sources of Truth

## 2.1 Code

Current code source of truth:

```text
GitHub origin/develop
```

Local development target:

```text
~/Desktop/jinja_app
```

Current audit branch:

```text
audit/shrine-goriyaku-detail-api-contract
```

The audit branch was fast-forwarded to the then-current `origin/develop` before the final fresh reads.

Old archived repository code under Developer is not treated as current source of truth.

---

## 2.2 Data

The current authoritative operational `GoriyakuTag` master is the Production-compatible **39-row master**.

The current local `jinja_db` contains **46 GoriyakuTag rows** and is classified as local historical drift.

The tracked fixture:

```text
backend/temples/fixtures/goriyaku_tags.json
```

contains 15 rows from an older taxonomy and is not used by `bootstrap_production_data`.

---

## 2.3 Google Spreadsheet

Spreadsheet:

```text
神社のDB
```

Current tab:

```text
シート1
```

The Spreadsheet is currently an:

```text
Identity / Location Audit Registry
```

It is **not** the Backend Shrine Knowledge database and is not currently the runtime source of truth for Recommendation.

Spreadsheet row `id` must not be assumed to equal Production `Shrine.id`.

---

# 3. Current Shrine Model Contract

Current `Shrine` stores the following main data classes.

## 3.1 Identity

```text
id
kind
name_jp
name_romaji
address
```

`kind` currently supports:

```text
shrine
temple
```

---

## 3.2 Position

```text
latitude
longitude
location
place_ref
```

`latitude` and `longitude` are required to be both null or both populated.

`location` is synchronized from latitude / longitude by the model save path.

`place_ref` is a nullable OneToOne relation to `PlaceRef`.

---

## 3.3 Legacy / Compatibility Shrine Meaning Fields

```text
goriyaku
sajin
description
```

Current responsibilities:

- `goriyaku`
  - free-text reviewed / legacy benefit field
  - currently feeds the legacy Recommendation compatibility path

- `sajin`
  - legacy deity text

- `description`
  - legacy descriptive text

`Shrine Detail API` does not fallback from the Knowledge models to `sajin` or `description`.

---

## 3.4 Recommendation / Attribute Fields

```text
goriyaku_tags
element
history_theme
kyusei
astro_elements
visit_style_tags
```

`goriyaku_tags` is a ManyToMany relation to `GoriyakuTag`.

`history_theme` is still an existing compatibility / current read-path field and is independent of Evidence Foundation
`HistoryThemeAssignment`.

---

## 3.5 Popularity / Operational Fields

```text
views_30d
favorites_30d
popular_score
last_popular_calc_at
created_at
updated_at
owner
```

These are stored Backend fields but are not all returned by Shrine Detail API.

---

# 4. GoriyakuTag Operational Master Contract

Current `GoriyakuTag` model:

```text
id
name
category
```

`name` is unique.

Current category choices:

```text
ご利益
神格
地域
```

Current Production-compatible master uses the `ご利益` category.

---

## 4.1 Canonical 39-row Master

Current audited operational master:

|  ID | Canonical Label |
| --: | --------------- |
|   1 | 縁結び          |
|   2 | 厄除け          |
|   3 | 交通安全        |
|   4 | 商売繁盛        |
|   5 | 五穀豊穣        |
|   6 | 開運            |
|   7 | 家内安全        |
|   8 | 福徳            |
|   9 | 学業成就        |
|  10 | 合格祈願        |
|  11 | 勝運            |
|  12 | 仕事運          |
|  13 | 航海安全        |
|  14 | 海上安全        |
|  15 | 武運長久        |
|  16 | 安産            |
|  17 | 八方除          |
|  18 | 夫婦円満        |
|  19 | 八難除          |
|  20 | 恋愛成就        |
|  21 | 導き            |
|  22 | 美容            |
|  23 | 方除け          |
|  24 | 健康長寿        |
|  25 | 芸能            |
|  26 | 家庭円満        |
|  27 | 出世運          |
|  28 | 金運            |
|  29 | 芸能運          |
|  30 | 強運厄除け      |
|  31 | 技芸上達        |
|  32 | 八方除け        |
|  33 | 病気平癒        |
|  34 | 火防            |
|  35 | 子宝            |
|  36 | 心願成就        |
|  37 | 延命長寿        |
|  38 | 足腰健康        |
|  39 | 農業守護        |

Audit result:

```text
row_count = 39
min_id = 1
max_id = 39
gaps = none
duplicate_labels = none
```

---

# 5. Current Recommendation Runtime Contract

Current Recommendation path remains based on the operational / compatibility taxonomy:

```text
Shrine.goriyaku
    ↓
backfill_goriyaku_tags
    ↓
Shrine.goriyaku_tags / GoriyakuTag
    ↓
NEED_TO_GORIYAKU_IDS
    ↓
Recommendation scoring / eligibility
    ↓
Concierge / Compass
```

`NEED_TO_GORIYAKU_IDS` consumes numeric `GoriyakuTag` IDs.

Examples from the current audited contract include:

```text
love        -> {1, 20}
career      -> {6, 21, 30, 12, 27}
money       -> {5, 36, 4, 28}
study       -> {9, 10}
protection  -> {11, 32, 2}
travel_safe -> {3, 13, 14}
relationship -> {1}
health      -> {7, 8, 24, 33, 38}
focus       -> {9, 10}
family      -> {16, 35}
marriage    -> {1, 18}
communication -> set()
```

This runtime mapping is a separate concern from Evidence Foundation.

---

# 6. Goriyaku Evidence Foundation v1

Evidence Foundation does **not** replace the 39-row operational `GoriyakuTag` master.

The two identity systems are separate.

```text
Operational Recommendation
    GoriyakuTag PK + name

Evidence Foundation
    goriyaku:<stable_machine_key>
```

---

## 6.1 Activated Canonical Registry

Current G1 registry contains exactly 18 approved canonical semantic identities:

| Canonical local key      | Display label |
| ------------------------ | ------------- |
| `relationship_bonding`   | 縁結び        |
| `misfortune_warding`     | 厄除け        |
| `traffic_safety`         | 交通安全      |
| `business_prosperity`    | 商売繁盛      |
| `good_fortune`           | 開運          |
| `household_safety`       | 家内安全      |
| `academic_success`       | 学業成就      |
| `exam_success`           | 合格祈願      |
| `victory_fortune`        | 勝運          |
| `maritime_safety`        | 海上安全      |
| `safe_childbirth`        | 安産          |
| `all_direction_warding`  | 八方除        |
| `career_advancement`     | 出世運        |
| `financial_fortune`      | 金運          |
| `strong_fortune_warding` | 強運厄除け    |
| `illness_recovery`       | 病気平癒      |
| `wish_fulfillment`       | 心願成就      |
| `leg_lower_back_health`  | 足腰健康      |

Full canonical keys use:

```text
goriyaku:<local_key>
```

Example:

```text
goriyaku:academic_success
```

---

## 6.2 Deferred Concepts

The G1 18-key registry is not a full mirror of the operational 39-row master.

The remaining concepts are deferred to later DATA_REVIEW.

No missing canonical key may be invented automatically.

---

## 6.3 Alias Registry

Current alias registry contains exactly one approved alias:

```text
八方除け
    -> all_direction_warding
    -> goriyaku:all_direction_warding
    -> display label: 八方除
```

Canonical display label:

```text
八方除
```

is not itself stored as an alias.

---

## 6.4 Alias Resolution Contract

Alias resolution is exact-match only.

Forbidden behavior includes:

```text
strip
lower
replace
Unicode normalization
prefix matching
suffix matching
substring matching
regex normalization
fuzzy matching
semantic similarity
LLM inference
embedding similarity
legacy GoriyakuTag fallback
```

Resolution and validation are separate responsibilities:

```text
surface alias
    ↓
resolve_goriyaku_alias()
    ↓
canonical full key
    ↓
validate_goriyaku_v1_canonical_key()
```

---

# 7. ShrineGoriyakuAssignment Contract

`ShrineGoriyakuAssignment` is the Evidence Foundation semantic-assignment persistence model.

Main fields:

```text
shrine
canonical_key
taxonomy_version
lifecycle
producer
mechanism
assigned_at
created_at
```

Lifecycle:

```text
ACTIVE
REVOKED
```

An ACTIVE assignment is unique per:

```text
shrine
canonical_key
taxonomy_version
```

`canonical_key` must validate against the current Goriyaku v1 registry.

`taxonomy_version` must match the current taxonomy version.

---

## 7.1 Independence from Legacy Recommendation Path

`ShrineGoriyakuAssignment` is explicitly independent from:

```text
Shrine.goriyaku_tags
```

It does not automatically write to:

```text
Shrine.goriyaku
Shrine.goriyaku_tags
NEED_TO_GORIYAKU_IDS
```

and the legacy compatibility path does not automatically write Evidence Foundation assignments.

---

# 8. Evidence Foundation Runtime Boundary

Current G1 regression tests explicitly guarantee that Goriyaku Evidence Foundation is not wired into:

```text
Recommendation
Ranking
Concierge
Compass
Need mapping
backfill_goriyaku_tags
Shrine Meaning runtime
```

Current architecture:

```text
Recommendation Runtime
======================

Shrine.goriyaku
      ↓
GoriyakuTag 39-row
      ↓
NEED_TO_GORIYAKU_IDS
      ↓
Concierge / Compass


Evidence Foundation
===================

Source-backed evidence
      ↓
canonical semantic key
      ↓
ShrineGoriyakuAssignment
      ↓
EvidenceLink / Evidence qualification

NO current runtime bridge between the two
```

Any future connection between these paths requires an explicit Product / Mother Ship decision and a separate
implementation task.

---

# 9. Knowledge Model Contract

## 9.1 ShrineKnowledgeSource

Stored fields:

```text
source_type
title
publisher
url
bibliography
accessed_at
verified_at
verification_status
confidence
language
note
created_at
updated_at
```

Current source types:

```text
shrine_official
government
cultural_property
academic
museum_or_archive
local_history
tourism_official
secondary_editorial
user_observation
internal_research
```

AI Generated content is not treated as a confirmed Source.

---

## 9.2 Knowledge Verification Status

Current enum:

```text
draft
unverified
source_confirmed
reviewed
disputed
outdated
rejected
```

Current Fact Ready statuses:

```text
source_confirmed
reviewed
```

For Fact Ready status, `verified_at` is required by validation.

---

## 9.3 Knowledge Confidence

Current enum:

```text
low
medium
high
```

---

## 9.4 ShrineDeity

Stored fields:

```text
shrine
display_name
canonical_name
role
sort_order
sources
verification_status
confidence
verified_at
note
created_at
updated_at
```

Current role enum:

```text
primary
enshrined
secondary
unknown
```

`ShrineDeity.sources` is ManyToMany.

A Deity Fact may therefore have multiple supporting Sources.

---

## 9.5 ShrineHistory

Stored fields:

```text
shrine
history_type
title
content
period_text
event_date
sort_order
sources
verification_status
confidence
verified_at
note
created_at
updated_at
```

Current history types:

```text
official_origin
founding
historical_event
tradition
regional_context
editorial_summary
```

`ShrineHistory.sources` is ManyToMany.

A History Fact may therefore have multiple supporting Sources.

---

# 10. EvidenceLink

`EvidenceLink` connects Evidence Foundation semantic assignments to Stored Knowledge Facts.

The model supports:

```text
HistoryThemeAssignment
or
ShrineGoriyakuAssignment
```

as the semantic-assignment side, and:

```text
ShrineHistory
or
ShrineDeity
```

as Stored Fact evidence.

It persists an explicit evidence edge and rationale.

This is different from the general `ShrineDeity.sources` / `ShrineHistory.sources` Source relation.

---

# 11. Shrine Detail API Contract

Current Shrine Detail serializer returns:

```text
id
kind
name_jp
name_romaji
address
latitude
longitude
goriyaku
goriyaku_tags
is_favorite
distance
distance_text
location
kyusei
deities
histories
```

---

## 11.1 GoriyakuTag API Representation

Nested `goriyaku_tags` returns:

```text
id
name
category
```

---

## 11.2 Deity API Representation

Each returned Deity contains:

```text
id
display_name
canonical_name
role
sort_order
verification_status
confidence
sources
```

---

## 11.3 History API Representation

Each returned History contains:

```text
id
history_type
title
content
period_text
event_date
sort_order
verification_status
confidence
sources
```

---

## 11.4 Source API Representation

Nested Source representation contains:

```text
id
source_type
title
publisher
url
verification_status
confidence
```

Not every Source model field is exposed by the Detail API.

For example, the following stored Source fields are not part of the current nested Detail representation:

```text
bibliography
accessed_at
verified_at
language
note
created_at
updated_at
```

---

# 12. Detail API Evidence Display Gate

Stored Knowledge does not automatically mean Detail-visible Knowledge.

For Deity / History:

```text
Stored Fact
    ↓
Evidence Gate
    ↓
full / disputed / hidden
```

Detail API returns:

```text
full
disputed
```

and excludes:

```text
hidden
```

A `disputed` Fact may be displayed on Detail when the required Source relationship is present.

Recommendation applies a different policy and excludes disputed Facts.

Therefore:

```text
Knowledge Fact correctness
≠
Detail visibility
≠
Recommendation eligibility
```

These must remain separate axes.

---

## 12.1 No Legacy Fallback

When Knowledge is not registered:

```text
deities = []
histories = []
```

Detail API does not fallback to:

```text
Shrine.sajin
Shrine.description
```

---

# 13. Stored Fields Not Exposed by Current Detail API

The following examples exist in the Backend but are not part of the current Shrine Detail response:

```text
sajin
description
element
history_theme
astro_elements
visit_style_tags
views_30d
favorites_30d
popular_score
last_popular_calc_at
place_ref
owner
ShrineGoriyakuAssignment
EvidenceLink
```

Therefore:

```text
Not in Detail API
```

must never be interpreted as:

```text
Not needed / not canonical / safe to delete
```

API is a display contract.

Model is a persistence contract.

---

# 14. PlaceRef Contract

Current `PlaceRef` stores:

```text
place_id
name
address
latitude
longitude
snapshot_json
synced_at
```

`place_id` is the primary key.

`Shrine.place_ref` is a nullable OneToOne relation to `PlaceRef`.

Logical relation:

```text
Shrine.place_ref_id
    ↓
PlaceRef.place_id
```

---

# 15. Current Google Spreadsheet Contract

Current Spreadsheet columns:

```text
id
name_jp
address
latitude
longitude
place_ref_id
canonical_status
official_name
official_address
official_source_type
official_source_url
verified_at
reference_latitude
reference_longitude
coordinate_delta_m
coordinate_status
notes
google_place_id
position_source_type
position_source_url
position_source_note
```

---

# 16. Spreadsheet 21-column Classification

| Spreadsheet field      | Backend relation                                           | Classification             |
| ---------------------- | ---------------------------------------------------------- | -------------------------- |
| `id`                   | No safe direct ID join                                     | Audit row identity         |
| `name_jp`              | `Shrine.name_jp`                                           | Stored mirror / comparison |
| `address`              | `Shrine.address`                                           | Stored mirror / comparison |
| `latitude`             | `Shrine.latitude`                                          | Stored mirror / comparison |
| `longitude`            | `Shrine.longitude`                                         | Stored mirror / comparison |
| `place_ref_id`         | `Shrine.place_ref_id` / `PlaceRef.place_id`                | Stored-reference mirror    |
| `canonical_status`     | No Shrine DB field                                         | Identity Audit             |
| `official_name`        | No Shrine DB field                                         | Identity Audit             |
| `official_address`     | No Shrine DB field                                         | Identity Audit             |
| `official_source_type` | No direct Shrine field                                     | Audit provenance           |
| `official_source_url`  | No direct Shrine field                                     | Audit provenance           |
| `verified_at`          | Same name exists in Knowledge but different responsibility | Identity Audit             |
| `reference_latitude`   | No Shrine DB field                                         | Coordinate Audit reference |
| `reference_longitude`  | No Shrine DB field                                         | Coordinate Audit reference |
| `coordinate_delta_m`   | Derived from coordinate comparison                         | Derived Audit              |
| `coordinate_status`    | No Shrine DB field                                         | Coordinate Audit result    |
| `notes`                | No direct Shrine field                                     | Human Audit                |
| `google_place_id`      | External Google Places identity                            | External Identity / Audit  |
| `position_source_type` | No Shrine DB field                                         | Coordinate provenance      |
| `position_source_url`  | No Shrine DB field                                         | Coordinate provenance      |
| `position_source_note` | No Shrine DB field                                         | Coordinate Audit           |

---

# 17. Spreadsheet ID Boundary

Critical contract:

```text
Spreadsheet row id
≠
Production Shrine.id
```

Spreadsheet IDs must not be used directly for Production mutations.

Identity matching must instead use an evidence-based comparison such as:

```text
name_jp
official_name
address
official_address
coordinates
Place identity
Google Place identity
human-reviewed identity result
```

Spreadsheet ID equality alone is insufficient.

This boundary was previously demonstrated by Spreadsheet rows whose IDs do not correspond to Production Shrine IDs.

---

# 18. Spreadsheet Responsibility

Current Spreadsheet responsibility is:

```text
Shrine Identity
+
Location / Coordinate Audit
+
Official identity reference
+
Human review notes
```

It is not currently responsible for:

```text
ShrineDeity Knowledge
ShrineHistory Knowledge
Tradition Knowledge
Goriyaku Recommendation Evidence
Evidence Foundation semantic assignments
Recommendation scoring
Purpose mapping
```

Therefore the current Sheet should not be treated as an incomplete Backend database.

It already has a distinct audit-layer responsibility.

---

# 19. Google Sheet Normalization Options

If future Sheet expansion is approved, the normalized logical structure could be:

```text
shrine_identity_audit
shrine_master
goriyaku_master
shrine_goriyaku
shrine_deities
shrine_histories
sources
deity_sources
history_sources
goriyaku_evidence_taxonomy
goriyaku_aliases
goriyaku_evidence_assignments
evidence_links
```

This is a structural mapping only.

It is not a decision that all of these tables should actually become Google Sheet tabs.

---

# 20. Local DB Current State

Current Desktop Backend connects to local PostgreSQL:

```text
database = jinja_db
host = 127.0.0.1
```

The archived Developer repository was confirmed to point to the same physical local database.

Therefore the 46-row GoriyakuTag state is not caused by moving the repository from Developer to Desktop.

It is historical local DB state.

Current classification:

```text
LOCAL_DEV_ONLY_DRIFT
```

---

# 21. Current Local GoriyakuTag Drift

Current local DB contains 46 GoriyakuTag rows.

It includes legacy / compound labels such as:

```text
子宝・安産
金運・商売繁盛
仕事運・出世
厄除け・方除け
勝運・必勝祈願
地域安泰
開運招福
```

as well as later canonical-style labels.

This table does not match the Production canonical 39-row ID space.

Therefore local Recommendation testing that relies on numeric `GoriyakuTag.id` may be unreliable while this drift
remains.

---

# 22. Legacy 15-row Fixture

Tracked file:

```text
backend/temples/fixtures/goriyaku_tags.json
```

contains:

```text
1  縁結び
2  子宝・安産
3  学業成就
4  合格祈願
5  金運・商売繁盛
6  仕事運・出世
7  健康長寿
8  病気平癒
9  家内安全
10 交通安全
11 厄除け・方除け
12 勝運・必勝祈願
13 五穀豊穣
14 地域安泰
15 開運招福
```

This fixture does not represent the current canonical 39-row master.

Current `bootstrap_production_data` does not load this fixture.

---

# 23. Production Bootstrap Contract

Current bootstrap order:

```text
1. import_shrines_seed
2. backfill_goriyaku_tags --with-visit-style --force
```

`import_shrines_seed` reads:

```text
backend/temples/data/shrines_seed_clean.json
```

by list order.

---

## 23.1 Shrine ID Behavior

The Shrine seed does not explicitly set Shrine PK.

New Shrine rows are created using normal database sequence allocation.

Existing Shrines are resolved by:

```text
name_jp + address
```

with the first matching row by ID.

Therefore Shrine PK reproduction depends on database state.

---

## 23.2 GoriyakuTag Creation Behavior

`backfill_goriyaku_tags`:

1. loads Shrines with non-empty `goriyaku`
2. orders Shrine rows by `id`
3. splits `Shrine.goriyaku`
4. preserves first occurrence order within the string
5. resolves each label with:

```text
GoriyakuTag.objects.get_or_create(name=name)
```

No fuzzy normalization is performed.

---

# 24. Pristine DB Reproducibility

The current `shrines_seed_clean.json` was processed with the exact current backfill split rule without writing to the
database.

Result:

```text
count = 39
```

and the first-occurrence sequence exactly matches the canonical Production 39-row master:

```text
1  縁結び
2  厄除け
3  交通安全
...
38 足腰健康
39 農業守護
```

Therefore:

```text
PRISTINE_DB_REPRODUCIBLE = YES
```

under the current seed and current bootstrap behavior.

---

# 25. Existing Drift Self-healing

The current bootstrap does not delete, reorder, renumber, or reconcile pre-existing GoriyakuTag rows.

Because it uses:

```text
get_or_create(name=name)
```

an existing drifted GoriyakuTag table is preserved.

Therefore:

```text
EXISTING_DRIFTED_DB_SELF_HEALING = NO
```

This explains why the existing local 46-row DB does not automatically converge to the current canonical 39-row master.

---

# 26. Reproducibility Risk

Current Recommendation runtime treats numeric `GoriyakuTag.id` as semantic routing identity through:

```text
NEED_TO_GORIYAKU_IDS
```

while `GoriyakuTag.id` is generated by database insertion order.

Therefore the current architectural dependency is:

```text
semantic runtime contract
    ↓
database-generated PK
    ↓
seed / history ordering
```

Current Production compatibility works because the current pristine seed recreates the expected exact sequence.

However this is an implicit dependency, not a separately declared stable-key contract.

---

# 27. Existing Test Coverage

## 27.1 Backfill Tests

Current tests verify:

```text
tag creation
M2M linking
idempotency
--force behavior
```

They do not verify the entire Production bootstrap 39-row master.

---

## 27.2 Need Mapping Contract

Current tests pin:

```text
CANONICAL_MASTER_ID_RANGE = range(1, 40)
```

and assert runtime mappings do not reference IDs outside the canonical range.

These tests assume the 39-row master contract.

They do not generate it from the Production bootstrap path.

---

## 27.3 Migration Tests

Some migration tests construct the canonical 39-row master explicitly with fixed IDs.

This validates migration behavior against a canonical master shape.

It does not validate that:

```text
shrines_seed_clean.json
+
import_shrines_seed
+
backfill_goriyaku_tags
```

reproduces that shape.

---

## 27.4 Bootstrap End-to-End Regression

Current audit found no test that executes the full contract:

```text
fresh DB
    ↓
import_shrines_seed
    ↓
backfill_goriyaku_tags
    ↓
assert exact [(1, 縁結び), ..., (39, 農業守護)]
```

Classification:

```text
Unit / behavior coverage      = EXISTS
Mapping contract coverage     = EXISTS
Migration canonical coverage  = EXISTS
Bootstrap exact-39 E2E        = NOT FOUND
```

---

# 28. Stored / Derived / Runtime Classification

| Data                             | Classification                        |
| -------------------------------- | ------------------------------------- |
| `Shrine` fields                  | Stored                                |
| `GoriyakuTag`                    | Stored Master                         |
| `Shrine.goriyaku`                | Stored compatibility / reviewed text  |
| `Shrine.goriyaku_tags`           | Stored M2M                            |
| `ShrineKnowledgeSource`          | Stored Source                         |
| `ShrineDeity`                    | Stored Fact                           |
| `ShrineHistory`                  | Stored Fact                           |
| `ShrineGoriyakuAssignment`       | Stored Evidence Foundation assignment |
| `EvidenceLink`                   | Stored Evidence edge                  |
| `GORIYAKU_V1_CANONICAL_KEYS`     | Code-defined semantic taxonomy        |
| `GORIYAKU_V1_ALIASES`            | Code-defined alias registry           |
| `NEED_TO_GORIYAKU_IDS`           | Runtime configuration                 |
| Recommendation score             | Runtime derived                       |
| Candidate eligibility            | Runtime derived                       |
| Direction match                  | Runtime derived                       |
| Distance                         | Runtime derived                       |
| `distance_text`                  | API derived                           |
| `/meaning/` composition          | Derived                               |
| Spreadsheet `coordinate_delta_m` | Audit derived                         |
| Spreadsheet `canonical_status`   | Audit metadata                        |
| Spreadsheet `coordinate_status`  | Audit metadata                        |

---

# 29. Current Local Development Home

Target local repository home:

```text
~/Desktop/jinja_app
```

The archived Developer repository is not required as an alternate active development home.

However:

```text
Desktop code canonicalization
```

and:

```text
local DB canonicalization
```

are separate tasks.

The repository can be consolidated to Desktop while the current local database remains drifted.

The Mother Ship decision for local DB normalization is recorded in Section 30.

The approved target is a fresh reproducible local PostgreSQL environment built from the current repository-controlled migration / seed / bootstrap path, with the current 46-row drifted state preserved only until local-only data preflight is completed.

---

# 30. Mother Ship Decisions

The following decisions are FINAL as of this audit.

## Decision 1 — Local GoriyakuTag DB Remediation

**FINAL: Option C — Fresh Rebuild + Bootstrap Exact-39 Regression Test**

The current local 46-row `GoriyakuTag` state will not be manually reconciled and adopted as canonical.

The local development database will instead be rebuilt from the current repository-controlled migration / seed /
bootstrap path.

The expected canonical result is:

```text
GoriyakuTag row count = 39
IDs = 1..39
exact ID -> name mapping = Production-compatible canonical master
```

Before any destructive local DB replacement, local-only data must be identified and safely preserved where required.

Production data must not be mutated by this task.

An automated regression test must also be added to verify that the current bootstrap path reproduces the exact canonical
39-row `GoriyakuTag` master.

This protects the current Recommendation runtime contract, which still depends on numeric `GoriyakuTag.id`.

---

## Decision 2 — Google Spreadsheet Responsibility

**FINAL: Option A — Keep Identity / Location Audit Only**

The existing Google Spreadsheet `神社のDB` remains an Identity / Location audit layer.

Its responsibilities remain limited to:

```text
shrine identity review
official identity references
address review
coordinate verification
Google Places / position reference data
human audit notes
```

The existing Spreadsheet will not become the source of truth for:

```text
ShrineDeity
ShrineHistory
ShrineKnowledgeSource
Goriyaku Recommendation Evidence
Evidence Foundation assignments
EvidenceLink
Recommendation runtime configuration
```

Knowledge / Evidence structures remain Backend responsibilities.

If a future Human Review workflow for Knowledge or Recommendation Evidence is required, it must be designed separately
with an explicit import / validation contract rather than horizontally expanding the existing Identity / Location audit
sheet.

---

## Decision 3 — Active Local Development Home

**FINAL: `~/Desktop/jinja_app` is the sole active local development repository.**

The archived Developer-side repository must not be used for active development.

Physical deletion of archived repository data and replacement of the currently drifted local database are deferred until
the approved fresh-local-DB migration procedure has confirmed that required local-only data has been preserved.

After that migration is completed, the intended local environment is:

```text
~/Desktop/jinja_app
        ↓
current origin/develop
        ↓
fresh reproducible local PostgreSQL
        ↓
migrations
        ↓
current shrine seed / bootstrap
        ↓
canonical Production-compatible 39-row GoriyakuTag master
```

---

# 31. Regression Boundary

Any implementation following this audit must preserve unless explicitly authorized otherwise:

```text
no new GoriyakuTag labels
no automatic fuzzy normalization
no automatic alias invention
no Production data mutation from Spreadsheet row IDs
no Spreadsheet row-id == Production Shrine.id assumption
no automatic ShrineGoriyakuAssignment -> goriyaku_tags sync
no automatic goriyaku_tags -> ShrineGoriyakuAssignment sync
no Evidence Foundation Recommendation runtime wiring
no Ranking weight change
no Purpose mapping change
no Concierge interpretation change
no Direction behavior change
no Distance behavior change
no Detail disputed-policy change
no legacy sajin/description fallback into Detail
```

Any change to one of these boundaries requires a separate explicit task / PR.

---

# 32. Audit Findings Summary

## Confirmed

```text
[CONFIRMED] Production-compatible GoriyakuTag master = 39 rows
[CONFIRMED] canonical IDs = 1..39
[CONFIRMED] current local jinja_db = 46-row drift
[CONFIRMED] local drift is not caused by Developer -> Desktop repo move
[CONFIRMED] legacy tracked fixture = stale 15-row taxonomy
[CONFIRMED] current pristine shrine seed reproduces exact canonical 39-row order
[CONFIRMED] existing drifted DB does not self-heal through bootstrap
[CONFIRMED] Evidence Foundation Goriyaku v1 = 18 active canonical keys
[CONFIRMED] Evidence Foundation alias registry = 1 approved alias
[CONFIRMED] Evidence Foundation is not wired to current Recommendation runtime
[CONFIRMED] Shrine Detail uses Knowledge models, not legacy sajin/description fallback
[CONFIRMED] Detail may display disputed Fact under the Detail-specific Evidence Gate
[CONFIRMED] Recommendation excludes disputed Fact under a different policy
[CONFIRMED] current Google Spreadsheet = Identity / Location audit layer
[CONFIRMED] Spreadsheet row id must not be treated as Production Shrine.id
[CONFIRMED] canonical_status / official_name / official_address are Spreadsheet audit metadata, not Shrine model fields
[CONFIRMED] no exact bootstrap 39-row E2E regression test was found
```

---

# 33. Remaining Actions

```text
Implementation:
- add Bootstrap exact-39 regression test
- perform local-only data preflight before DB replacement
- rebuild fresh local PostgreSQL from current repository-controlled state
- verify canonical GoriyakuTag 39-row master after rebuild
- document ~/Desktop/jinja_app as the sole active local development home
- audit legacy 15-row fixture in a separate scoped task
- create implementation PRs separately from this audit PR
```

---

# 34. Final Audit State

Current architecture should be understood as four separate layers:

```text
1. Shrine / Knowledge Stored Data
2. Operational Recommendation Compatibility Taxonomy (39-row GoriyakuTag)
3. Evidence Foundation Semantic Taxonomy (18-key v1 + 1 alias)
4. Google Spreadsheet Identity / Coordinate Audit Layer
```

These layers overlap in subject matter but are not interchangeable sources of truth.

The current audit does not collapse them into a single master.

That separation is the primary contract established by this document.
