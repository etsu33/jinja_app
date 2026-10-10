# NIIGATA-001-H001 — nsrc-000002 G4 Evidence / Seed Preflight

## 1. Status

```text
candidate_id              = nsrc-000002
candidate_name            = 青澤神社

UPSTREAM_G3               = PASS / NORMAL_MODEL_FIT
UPSTREAM_SOURCE_PACKET    = PASS / FROZEN / G4_EVIDENCE_READY

G4_EVIDENCE_PREFLIGHT     = HOLD
reason_code               = BASE_SHRINE_NOT_MATERIALIZED

EVIDENCE_SEMANTIC_READINESS = PASS
KNOWLEDGE_PAYLOAD_DESIGN    = PASS
KNOWLEDGE_IMPORT_READY      = HOLD
FORMAL_G4                   = HOLD

Production write          = NONE
G5 / G6 / G7 / G8         = NOT EXECUTED
```

- Recorded at: 2026-10-10
- Branch: `audit/nsrc-000002-g4-evidence-preflight`
- Upstream G4 Source Packet:
  `docs/audit/niigata-h001-nsrc-000002-g4-source-packet-freeze.md`
- Upstream G3:
  `docs/audit/niigata-h001-nsrc-000002-g3-source-knowledge-fit.md`

This preflight preserves the existing 000004 G4 contract split:

```text
Source Packet PASS
!=
Knowledge import ready
!=
Formal G4 PASS
```

## 2. Governing authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/services/evidence_gate.py`
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`
- `backend/temples/models.py`

G4 PASS requires:

```text
Fact owner matches G1/G3
source-less Fact = 0
Source identity conflict = 0
Fact / Source verification metadata complies with contract
usable Deity or History >= 1
Fact text does not exceed Source
tradition is not promoted into asserted history
AI-only evidence is not treated as confirmed
```

## 3. Scope

```text
G4_EVIDENCE_SCOPE = { nsrc-000002 }
```

No G4 materialization is performed for other NIIGATA-H001 Candidates.

## 4. Frozen Fact owner

```text
candidate_id     = nsrc-000002
official_name    = 青澤神社
official_address = 新潟県糸魚川市大字青海2696番地
fact_owner       = 青澤神社（糸魚川市）
```

The accepted public Source writes the shrine name as `青沢神社`; the canonical Candidate name
remains `青澤神社`.

The G1 / G2 identity chain already controls this orthographic variant.

## 5. Frozen Knowledge payload design

### Source S1

Identity/listing provenance only:

```text
key         = NIIGATA_JINJACHO_AOSAWA
source_type = government
publisher   = 新潟県神社庁
url         = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15216
```

S1 is not required to be materialized in the Knowledge Seed because it does not support the
History Fact directly.

### Source S2

Primary Knowledge Source:

```text
key         = ITOIGAWA_AOSAWA_SPRING_FESTIVAL
source_type = government
title       = 4月の地域の祭り | 新潟県糸魚川市 - 地域のまつり紹介サイト
publisher   = 糸魚川市 / 糸魚川ジオパーク協議会
url         = https://matsuri.geo-itoigawa.com/calendar/m04/
language    = ja

verification_status = source_confirmed
confidence          = high
verified_at         = REQUIRED_AT_MATERIALIZATION
```

### History H1

```text
history_type = regional_context
title        = 青沢神社の春季祭礼
content      = 青沢神社では毎年4月第3日曜日に春季祭礼が行われ、前日の宵宮には神楽が奉納される。祭礼当日は神輿・子供みこしの地区巡回、神楽奉納、手踊りが行われる。
period_text  = 毎年4月第3日曜日
event_date   = null

verification_status = source_confirmed
confidence          = high
verified_at         = REQUIRED_AT_MATERIALIZATION
source_keys         = [ITOIGAWA_AOSAWA_SPRING_FESTIVAL]
```

No Deity row is planned in this G4 payload.

## 6. Source-boundary review

The accepted Source directly supports:

- `青沢神社 春季祭礼（春まつり）`
- recurrence: every third Sunday of April
- region: 青海地域 大沢地区
- venue: 青沢神社
- eve kagura
- festival-day mikoshi / children mikoshi procession
- kagura dedication
- teodori

The proposed H1 content remains within this Source scope.

The payload does not add:

- shrine founding date
- historical continuity duration
- deity identity
- religious efficacy
- derived goriyaku
- recommendation interpretation

```text
FACT_TEXT_WITHIN_SOURCE = PASS
```

## 7. Evidence Gate semantic preflight

Current Evidence Gate contract:

```text
usable = fact verification_status is fact-ready
         AND
         at least one linked Source verification_status is fact-ready
```

The current fact-ready statuses are the repository's
`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES`.

With the frozen payload design:

```text
S2.verification_status = source_confirmed
H1.verification_status = source_confirmed
H1.source_keys         = [S2]
```

the expected Evidence Gate decision is:

```text
usable          = True
display_mode    = full
reason_strength = assertive
reason          = fact_ready_with_source
confidence      = high
```

Therefore:

```text
EVIDENCE_SEMANTIC_READINESS = PASS
EXPECTED_USABLE_HISTORY     = 1
```

This is contract-level preflight only.

It is **not** an actual post-materialization DB relation measurement.

## 8. Base Shrine prerequisite check

Current `develop` Base Seed:

```text
path = backend/temples/data/shrines_seed_clean.json
rows = 121
```

Exact target lookup:

```text
name_jp = 青澤神社
address = 新潟県糸魚川市大字青海2696番地

exact row count = 0
same-name 青澤 / 青沢 row count = 0
```

Therefore the Knowledge importer cannot yet resolve the intended `shrine_ref` from the canonical
Base Seed.

```text
BASE_SHRINE_MATERIALIZED = NO
```

## 9. Knowledge Seed prerequisite check

Expected path:

`backend/temples/data/knowledge_seeds/nsrc_000002_seed.json`

Current develop:

```text
nsrc_000002_seed.json = NOT FOUND
```

This is expected before data materialization.

## 10. Import readiness

Because the Base Shrine prerequisite is absent:

```text
Knowledge Seed parse design        = READY
Knowledge Seed file                = NOT MATERIALIZED
Base Shrine row                    = NOT MATERIALIZED
resolve_shrine actual measurement  = NOT EXECUTABLE
Knowledge validate-only            = NOT EXECUTED
Knowledge dry-run                  = NOT EXECUTED
Knowledge isolated apply           = NOT EXECUTED
Evidence Gate DB measurement       = NOT EXECUTED
idempotency                        = NOT EXECUTED
```

Therefore:

```text
KNOWLEDGE_IMPORT_READY = HOLD
reason                 = BASE_SHRINE_NOT_MATERIALIZED
```

## 11. Formal G4 decision

PASS condition review:

| G4 condition | Preflight result |
|---|---|
| Fact owner matches G1/G3 | PASS |
| Source-backed History candidate exists | PASS |
| Fact text remains within Source | PASS |
| Model Risk hidden by Fact | NONE |
| Evidence Gate semantic design can produce usable History | PASS |
| Base Shrine resolves exactly once | **NOT YET** |
| Source / Fact relation exists in materialized DB | **NOT YET** |
| actual usable History >= 1 | **NOT YET** |
| import conflict codes = 0 | **NOT YET** |
| idempotency | **NOT YET** |

Formal decision:

```text
FORMAL_G4 = HOLD
reason_code = BASE_SHRINE_NOT_MATERIALIZED
```

This HOLD is a data-materialization prerequisite HOLD.

It does not reverse:

```text
G2 = PASS
G3 = PASS / NORMAL_MODEL_FIT
G4 Source Packet = PASS / FROZEN
EVIDENCE_SEMANTIC_READINESS = PASS
```

## 12. Required re-entry implementation

The next implementation PR must be dedicated to `nsrc-000002` only and must materialize:

1. one Base Shrine row:
   - name_jp = 青澤神社
   - address = 新潟県糸魚川市大字青海2696番地
   - latitude = 37.00763484
   - longitude = 137.79024297
   - location mirrors latitude / longitude
   - no inferred goriyaku
   - no inferred visit-style values

2. one Knowledge Seed:
   - Source S2 only for Knowledge Fact provenance
   - Deities = 0
   - Histories = 1
   - H1 = 青沢神社の春季祭礼
   - source-less Fact = 0
   - no SourceFact / goriyaku mapping unless a separately accepted Source Packet authorizes it

3. dedicated regression tests:
   - Base Seed exact identity = 1
   - existing 121 rows unchanged
   - validate-only PASS
   - dry-run PASS
   - isolated apply PASS
   - NOT_FOUND = 0
   - IMPORT_IDENTITY_AMBIGUOUS = 0
   - SOURCE_REUSE_CONFLICT = 0
   - SOURCE_REUSE_AMBIGUOUS = 0
   - H1 Source relation = exactly S2
   - H1 Evidence Gate usable=True
   - second import idempotent
   - goriyaku state unchanged

After those actual measurements, re-enter G4 and make the Formal PASS / HOLD decision.

## 13. AI ownership

This next task spans:

- Base Seed
- Knowledge Seed
- regression tests
- historical count pins / cohort boundaries if affected
- G4 audit

Therefore under the project AI-operation contract:

```text
implementation owner = Codex
ChatGPT owner         = specification / review / final G4 redecision
```

## 14. Isolation

This preflight changes documentation only.

No changes to:

- Candidate Master
- Base Seed
- Knowledge Seed
- Production DB
- Position
- Recommendation / Ranking
- Concierge / Compass
- models / migrations

## 15. Final state

```text
G0 nsrc-000002               = PASS
G1 nsrc-000002               = PASS / NEW
G2 nsrc-000002               = PASS
G3 nsrc-000002               = PASS / NORMAL_MODEL_FIT
G4 Source Packet Freeze      = PASS / FROZEN / G4_EVIDENCE_READY
G4 Evidence semantic preflight = PASS
G4 Knowledge import readiness  = HOLD / BASE_SHRINE_NOT_MATERIALIZED
FORMAL G4                     = HOLD
G5                            = NOT EXECUTED
```

STOP at G4 preflight.
