# NIIGATA-001-H001 — nsrc-000004 G4 Data Materialization Re-entry

## 1. Status

~~~text
candidate_id              = nsrc-000004
candidate_name            = 青海神社
fact_owner                = 青海神社（加茂市）

UPSTREAM_G3               = PASS / CURATION_RELEASE_CANDIDATE
UPSTREAM_G4_PREFLIGHT     = HOLD / BASE_SHRINE_NOT_MATERIALIZED
G4_REENTRY_VALIDATION     = COMPLETE
FORMAL_G4_REDECISION      = PENDING

Production write          = NONE
G5 / G6 / G7 / G8         = NOT EXECUTED
~~~

- Recorded at: 2026-10-10
- Branch: `feature/nsrc-000004-g4-data-materialization`
- PR: #3129 `feat(data): materialize nsrc-000004 G4 evidence`
- Re-entry validation head before this audit record: `6a7a9153019baaa3e11384844fe0b705f3038590`
- Upstream G4 preflight: `docs/audit/niigata-h001-g4-evidence-preflight.md`
- Upstream Source Packet: `docs/audit/niigata-h001-g4-source-packet-freeze.md`
- Upstream G3: `docs/audit/niigata-h001-g3-source-knowledge-fit.md`

本書は、G4 Evidence Preflightで記録された
`BASE_SHRINE_NOT_MATERIALIZED` blockerの解消後に実施した
Base Shrine / Knowledge Seed materializationとisolated PostgreSQL検証を記録する。

過去のHOLDは履歴として維持する。

~~~text
2026-10-09:
G4_EVIDENCE_PREFLIGHT = HOLD
reason_code            = BASE_SHRINE_NOT_MATERIALIZED

2026-10-10:
Base Shrine prerequisite materialized
Knowledge Seed materialized
isolated PostgreSQL validation completed

Historical HOLD
!= invalid audit
!= retroactive PASS
~~~

Formal G4 PASS / HOLDの再判定は本書作成とは分離し、次工程で行う。

---

## 2. Governing authority

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/services/evidence_gate.py`
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`
- `backend/temples/models.py`
- `docs/audit/niigata-h001-g4-evidence-preflight.md`

G4で確認する主要条件:

~~~text
Fact ownerがG1/G3と一致
source-less Fact = 0
Source identity conflict = 0
Fact / Source verificationが契約に適合
usable Deity または History >= 1
Fact本文がSource本文を越えない
AI Generatedのみをconfirmed Sourceとして扱わない
upstream HOLD候補を巻き込まない
Recommendation / Ranking / Mappingへ越境しない
~~~

---

## 3. Execution scope

~~~text
G4_REENTRY_SCOPE = { nsrc-000004 }
~~~

対象外:

| candidate_id | Shrine | State |
|---|---|---|
| nsrc-000001 | 相吉神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000002 | 青澤神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000003 | 蒼柴神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000005 | 青山稲荷神社 | G2 HOLD_POSITION_REVIEW |

4社についてG3 / G4 materializationを実行していない。

---

## 4. Historical blocker and resolution

Upstream preflight:

~~~text
G4_EVIDENCE_PREFLIGHT = HOLD
reason_code            = BASE_SHRINE_NOT_MATERIALIZED
~~~

当時のHOLD理由はEvidence不足ではなく、
`import_shrine_knowledge` がKnowledge Seedの `shrine_ref` を解決するための
Base Shrine rowが存在しなかったことだった。

本re-entryで次のBase Shrine rowをmaterializeした。

~~~json
{
  "name_jp": "青海神社",
  "address": "新潟県加茂市大字加茂字宮山229番地",
  "latitude": 37.65657387,
  "longitude": 139.0536436,
  "goriyaku": "",
  "kyusei": null,
  "astro_elements": [],
  "location": {
    "lat": 37.65657387,
    "lng": 139.0536436
  }
}
~~~

禁止した追加:

~~~text
goriyaku_tags key   = ABSENT
visit_style_tags    = NOT INFERRED
identity rewrite    = NONE
~~~

Base Seed row count:

~~~text
before = 120
after  = 121
delta  = +1
~~~

---

## 5. Knowledge Seed materialization

Path:

`backend/temples/data/knowledge_seeds/nsrc_000004_seed.json`

Materialized payload:

~~~text
schema_version = 1.2

Sources       = 3
Shrines       = 1
Deities       = 2
Histories     = 2
SourceFacts   = 11
Collectives   = 0
~~~

Materialized Sources:

| key | Role | URL |
|---|---|---|
| AOMI_OFFICIAL_DEITY | D1 / D2 Source | https://www.aomi-jinjya.or.jp/history/gosaisin.html |
| AOMI_OFFICIAL_HISTORY | H1 / H2 Source | https://www.aomi-jinjya.or.jp/history/yuisyo.html |
| AOMI_OFFICIAL_PRAYER_GUIDE | SF01-SF11 Source | https://www.aomi-jinjya.or.jp/gokitou/syurui.html |

`NIIGATA_JINJACHO_DIRECTORY` はidentity/listing provenanceのみとして維持し、
Knowledge Seedへmaterializeしていない。

Knowledge `shrine_ref`:

~~~text
name_jp = 青海神社
address = 新潟県加茂市大字加茂字宮山229番地
~~~

---

## 6. Materialized Deity / History Facts

Deity:

~~~text
D1 椎根津彦命 -> AOMI_OFFICIAL_DEITY
D2 大国魂命   -> AOMI_OFFICIAL_DEITY
~~~

History:

~~~text
H1 神亀3年の創建         -> AOMI_OFFICIAL_HISTORY
H2 明治5年の三社本殿合殿 -> AOMI_OFFICIAL_HISTORY
~~~

Excluded Deity ownership remains unchanged:

~~~text
賀茂別雷命
多多須玉依媛命
賀茂建角身命
~~~

三社に関係する歴史事象を理由に、上記祭神を
nsrc-000004のShrineDeityへ統合していない。

---

## 7. Base Shrine isolated import / identity resolution

Canonical Base Seedをisolated PostgreSQL test DBへ投入した。

Observed result:

~~~text
Base Seed import = PASS

name_jp + address exact match = 1 row
resolve_shrine status         = OK
NOT_FOUND                     = 0
AMBIGUOUS                     = 0
~~~

`OK_CANONICAL_PREFERRED` 等のfallbackへ依存せず、
exact `name_jp + address` で解決した。

---

## 8. Knowledge Seed validation and dry-run

Observed:

~~~text
Knowledge Seed --validate-only = PASS
Knowledge Seed --dry-run       = PASS

Source CREATE     = 3
Deity CREATE      = 2
History CREATE    = 2
SourceFact CREATE = 11

dry-run Knowledge writes = 0
~~~

Blocked code observation:

~~~text
Shrine NOT_FOUND             = 0
IMPORT_IDENTITY_AMBIGUOUS    = 0
SOURCE_REUSE_CONFLICT        = 0
SOURCE_REUSE_AMBIGUOUS       = 0
~~~

---

## 9. Knowledge Seed apply

Dedicated regression test:

`test_nsrc_000004_knowledge_seed_apply_passes_with_no_identity_or_source_errors`

Local isolated PostgreSQL result:

~~~text
1 passed
~~~

Apply contract verified by the test:

~~~text
sources created      = 3
deities created      = 2
histories created    = 2
collectives created  = 0
memberships created  = 0
source_facts created = 11

NOT_FOUND                  = 0
IMPORT_IDENTITY_AMBIGUOUS = 0
SOURCE_REUSE_CONFLICT     = 0
SOURCE_REUSE_AMBIGUOUS    = 0
~~~

Post-apply:

~~~text
source-less Deity   = 0
source-less History = 0
~~~

Production DBへのapplyではない。
pytest isolated PostgreSQL DBでのmaterialization実測である。

---

## 10. Evidence Gate actual measurement

Dedicated regression test:

`test_nsrc_000004_d1_d2_h1_h2_are_usable_under_evidence_gate`

Local isolated PostgreSQL result:

~~~text
1 passed
~~~

DB materialization後のFact / Source relationから
`evidence_gate.decide_fact_usability()` を実行した。

| Fact | Source | usable | display_mode | reason_strength | reason |
|---|---|---:|---|---|---|
| D1 椎根津彦命 | S1 | True | full | assertive | fact_ready_with_source |
| D2 大国魂命 | S1 | True | full | assertive | fact_ready_with_source |
| H1 神亀3年の創建 | S2 | True | full | assertive | fact_ready_with_source |
| H2 明治5年の三社本殿合殿 | S2 | True | full | assertive | fact_ready_with_source |

Common observed metadata:

~~~text
verification_status = source_confirmed
confidence           = high
~~~

Result:

~~~text
usable Deity   = 2 / 2
usable History = 2 / 2
usable total   = 4 / 4
~~~

これはupstream preflightのexpected値ではなく、
apply後DB relationを使ったactual measurementである。

---

## 11. ShrineSourceFact relation verification

Dedicated regression test:

`test_nsrc_000004_source_facts_all_link_exactly_to_s4`

Local isolated PostgreSQL result:

~~~text
1 passed
~~~

Observed:

~~~text
ShrineSourceFact count = 11
orphan SourceFact       = 0
extra Source relation   = 0

SF01-SF11
-> exactly one Source each
-> AOMI_OFFICIAL_PRAYER_GUIDE only
~~~

S4:

~~~text
url                 = https://www.aomi-jinjya.or.jp/gokitou/syurui.html
source_type         = shrine_official
verification_status = source_confirmed
~~~

Stable key setはSource Packet Freezeの11件と完全一致する。

---

## 12. Idempotency

Dedicated regression test:

`test_nsrc_000004_second_import_is_idempotent`

Local isolated PostgreSQL result:

~~~text
1 passed
~~~

Second import plan:

~~~text
source_REUSE_EXISTING   = 3
deity_SKIP_EXISTS       = 2
history_SKIP_EXISTS     = 2
source_fact_SKIP_EXISTS = 11
CREATE                  = 0
~~~

Second apply result:

~~~text
sources created      = 0
deities created      = 0
histories created    = 0
collectives created  = 0
memberships created  = 0
source_facts created = 0
~~~

Additional invariants:

~~~text
PK mutation            = 0
Deity Source diff      = 0
History Source diff    = 0
SourceFact Source diff = 0
~~~

---

## 13. Goriyaku boundary verification

Dedicated regression test:

`test_nsrc_000004_knowledge_import_keeps_goriyaku_state_unchanged`

Local isolated PostgreSQL result:

~~~text
1 passed
~~~

Knowledge apply前後:

~~~text
Shrine.goriyaku diff          = 0
Shrine.goriyaku_tags diff     = 0
GoriyakuTag master diff       = 0
ShrineGoriyakuAssignment diff = 0
~~~

同時に:

~~~text
ShrineSourceFact = 11 materialized
~~~

したがって本re-entryでは次を維持した。

~~~text
official prayer wording
-> typed ShrineSourceFact storage

official prayer wording
!= automatic goriyaku_tags mapping
!= GoriyakuTag create/update
!= ShrineGoriyakuAssignment write
!= Need mapping
!= Recommendation score write
~~~

---

## 14. Existing Base Shrine preservation

develop Base Seedとcurrent branchをidentity単位で比較した。

Observed:

~~~text
develop rows           = 120
current branch rows    = 121
added                  = 1
removed                = 0
modified existing rows = 0
~~~

Added row:

~~~text
青海神社
新潟県加茂市大字加茂字宮山229番地
~~~

既存120件canonical fingerprint:

~~~text
develop existing 120 SHA-256
= dd9a958eb5a7c51345fe5b9f9bb2a2f696a1b3edef8e67f6fcee7301f91a66b7

current branch excluding nsrc-000004 SHA-256
= dd9a958eb5a7c51345fe5b9f9bb2a2f696a1b3edef8e67f6fcee7301f91a66b7
~~~

Dedicated regression test:

`test_nsrc_000004_base_seed_preserves_existing_120_rows`

Result:

~~~text
1 passed
~~~

---

## 15. Base Seed builder contract

Base Seed builder validation after the 121st row addition:

~~~text
TOTAL=121
DUPLICATE_IDENTITY=0
DUPLICATE_ID=0
MISSING_REQUIRED=0
PREFECTURES=31
IDENTITY_MUTATION=0
SCHEMA_UNEXPECTED_CHANGE=0
PREFECTURE_UNRESOLVED=0
ID_FIELD_ROWS=0
VISIT_STYLE_INVALID=0
WRITTEN=0
BASE_SEED_BUILD=OK
~~~

Wave0 historical count-pin tests were adjusted only for the new Base Seed boundary.

Relevant changes:

~~~text
test_wave0_db01_knowledge_seed.py
120 -> 121 count pin

test_wave0_db02_shrine_seed.py
120 -> 121 count pin

test_wave0_db04_shrine_seed.py
W0-DB04 cohort boundary decoupled from whole-file final count
~~~

W0-DB04対象3社自体のcohort内容は変更していない。

---

## 16. Isolation verification

PR #3129 implementation diff before this audit document:

~~~text
backend/temples/data/knowledge_seeds/nsrc_000004_seed.json
backend/temples/data/shrines_seed_clean.json
backend/temples/tests/test_nsrc_000004_knowledge_seed.py
backend/temples/tests/test_wave0_db01_knowledge_seed.py
backend/temples/tests/test_wave0_db02_shrine_seed.py
backend/temples/tests/test_wave0_db04_shrine_seed.py
~~~

Not present in implementation diff:

~~~text
Candidate Master
G2 HOLD Position records
Ranking / Score implementation
Recommendation logic
Mapping Registry
Need mapping
Compass logic
DB schema / migrations
~~~

Therefore the re-entry implementation remains scoped to
nsrc-000004 data materialization, its regression coverage, and historical Base Seed count boundaries.

Production write:

~~~text
NONE
~~~

G5 / G6 / G7 / G8:

~~~text
NOT EXECUTED
~~~

---

## 17. CI infrastructure note

During the apply regression phase, GitHub Actions `backend-pr` run #332 failed before pytest.

Observed root cause:

~~~text
docker pull postgres:16
-> Docker Hub unauthenticated pull rate limit
-> PostgreSQL service container init failure
-> checkout skipped
-> pytest skipped
~~~

This was not classified as a Knowledge Seed / migration / test assertion failure.

For G4 re-entry evidence, dedicated tests were then executed against the developer's
local PostgreSQL instance through pytest's isolated test DB path.

Observed dedicated tests:

~~~text
test_nsrc_000004_knowledge_seed_apply_passes_with_no_identity_or_source_errors
= 1 passed

test_nsrc_000004_d1_d2_h1_h2_are_usable_under_evidence_gate
= 1 passed

test_nsrc_000004_source_facts_all_link_exactly_to_s4
= 1 passed

test_nsrc_000004_second_import_is_idempotent
= 1 passed

test_nsrc_000004_knowledge_import_keeps_goriyaku_state_unchanged
= 1 passed

test_nsrc_000004_base_seed_preserves_existing_120_rows
= 1 passed
~~~

CI infrastructure failure and product/data validation resultを混同しない。

---

## 18. Re-entry acceptance matrix

| G4 re-entry condition | Result | Evidence |
|---|---|---|
| Base Shrine prerequisite materialized | PASS | Base Seed 120 -> 121 |
| shrine_ref exactly one row | PASS | resolve_shrine=OK |
| Knowledge schema 1.2 | PASS | validate-only |
| Shrine NOT_FOUND = 0 | PASS | dry-run + apply test |
| IMPORT_IDENTITY_AMBIGUOUS = 0 | PASS | dry-run + apply test |
| SOURCE_REUSE_CONFLICT = 0 | PASS | dry-run + apply test |
| SOURCE_REUSE_AMBIGUOUS = 0 | PASS | dry-run + apply test |
| Source-less Deity / History = 0 | PASS | apply test |
| D1 / D2 usable=True | PASS | actual Evidence Gate |
| H1 / H2 usable=True | PASS | actual Evidence Gate |
| SourceFact 11 relation | PASS | S4-only actual relation |
| idempotency | PASS | second import |
| goriyaku boundary | PASS | tracked goriyaku state unchanged |
| existing Base Shrine preservation | PASS | 120-row fingerprint |
| Candidate Master isolation | PASS | implementation diff |
| G2 HOLD four isolation | PASS | implementation diff |
| Ranking / Mapping isolation | PASS | implementation diff |
| Production write | NONE | isolated test DB only |

No re-entry validation blocker is recorded in this matrix.

Formal G4 PASS / HOLD is intentionally not declared in this section.

---

## 19. Current classification

~~~text
G4_REENTRY_VALIDATION
= COMPLETE

BASE_SHRINE_NOT_MATERIALIZED blocker
= RESOLVED IN REENTRY BRANCH

Knowledge payload
= MATERIALIZED

isolated Knowledge apply
= PASS

Evidence Gate actual usability
= 4 / 4 usable

SourceFact relation
= 11 / 11 S4-linked

idempotency
= PASS

goriyaku direct-write boundary
= PASS

existing Base Shrine preservation
= PASS

Formal G4
= PENDING REDECISION
~~~

Historical preflight remains:

~~~text
G4_EVIDENCE_PREFLIGHT = HOLD
reason_code            = BASE_SHRINE_NOT_MATERIALIZED
~~~

The historical record is not rewritten.

---

## 20. Completion checklist

- [x] Historical G4 preflight HOLDを維持
- [x] nsrc-000004だけをre-entry scopeとして固定
- [x] Base Shrine rowをmaterialize
- [x] existing Base Shrine 120件不変を確認
- [x] Knowledge Seed schema 1.2をmaterialize
- [x] S1 / S2 / S4のみmaterialize
- [x] S3をKnowledge Seedへmaterializeしない
- [x] D1 / D2 -> S1 relationをmaterialize
- [x] H1 / H2 -> S2 relationをmaterialize
- [x] SourceFact 11件 -> S4 relationをmaterialize
- [x] Base shrine_ref exactly 1 row
- [x] validate-only PASS
- [x] dry-run PASS
- [x] isolated PostgreSQL apply PASS
- [x] NOT_FOUND = 0
- [x] IMPORT_IDENTITY_AMBIGUOUS = 0
- [x] SOURCE_REUSE_CONFLICT = 0
- [x] SOURCE_REUSE_AMBIGUOUS = 0
- [x] source-less Deity / History = 0
- [x] D1 / D2 / H1 / H2 Evidence Gate usable=True
- [x] SourceFact 11件のS4 relation確認
- [x] 2巡目import idempotency PASS
- [x] goriyaku_tags direct write = 0
- [x] GoriyakuTag create/update = 0
- [x] ShrineGoriyakuAssignment write = 0
- [x] Candidate Masterを変更しない
- [x] G2 HOLD 4社を変更しない
- [x] Ranking / Mapping / Recommendation logicを変更しない
- [x] Production writeを行わない
- [x] G4 re-entry監査文書を作成
- [ ] Formal G4をPASS / HOLDで再判定
- [ ] PR #3129 closure stateを更新
- [ ] STOP

---

## STOP

~~~text
STOP AFTER AUDIT RECORD

Do not execute G5.
Do not write Production.
Do not rewrite the historical G4 preflight HOLD.
Next work item:
Formal G4 PASS / HOLD redecision from this re-entry evidence.
~~~
