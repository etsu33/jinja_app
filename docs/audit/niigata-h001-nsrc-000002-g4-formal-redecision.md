# NIIGATA-001-H001 — nsrc-000002 Formal G4 Redecision

## 1. Status

```text
candidate_id                = nsrc-000002
candidate_name              = 青澤神社
fact_owner                  = 青澤神社（糸魚川市）

UPSTREAM_G2                 = PASS
UPSTREAM_G3                 = PASS / NORMAL_MODEL_FIT
UPSTREAM_SOURCE_PACKET      = PASS / FROZEN
HISTORICAL_G4_PREFLIGHT     = HOLD / BASE_SHRINE_NOT_MATERIALIZED
BASE_SHRINE_MATERIALIZATION = PASS
KNOWLEDGE_MATERIALIZATION   = PASS

FORMAL_G4_REDECISION        = PASS
FORMAL_G4                   = PASS

Production write            = NONE
G5 / G6 / G7 / G8           = NOT EXECUTED
```

- Recorded at: 2026-10-10
- Mother Ship redecision after PR #3148 merge
- PR #3147 merge: Base Shrine materialization
- PR #3148 merge: Knowledge materialization validation

This record does not rewrite the historical G4 preflight HOLD.

```text
historical HOLD
!= current Formal G4 result

2026-10-10 preflight:
FORMAL_G4 = HOLD
reason_code = BASE_SHRINE_NOT_MATERIALIZED

after prerequisite resolution and isolated materialization validation:
FORMAL_G4 = PASS
```

## 2. Governing authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/services/evidence_gate.py`
- `docs/audit/niigata-h001-nsrc-000002-g4-source-packet-freeze.md`
- `docs/audit/niigata-h001-nsrc-000002-g4-evidence-preflight.md`
- `docs/audit/niigata-h001-nsrc-000002-g4-knowledge-materialization.md`

Formal G4 PASS requires:

```text
Fact owner matches G1/G3
source-less Fact = 0
Source identity conflict = 0
Fact / Source verification complies with contract
usable Deity or History >= 1
tradition is not promoted into asserted history
AI-only evidence is not treated as confirmed
```

## 3. Frozen identity / ownership

```text
candidate_id     = nsrc-000002
official_name    = 青澤神社
official_address = 新潟県糸魚川市大字青海2696番地
fact_owner       = 青澤神社（糸魚川市）
```

The accepted Knowledge Source writes `青沢神社`, while G1 canonical identity remains
`青澤神社`.

The orthographic difference is already controlled by the G1/G2 identity chain and does not create
a second Fact owner.

Result:

```text
FACT_OWNER = PASS
```

## 4. Materialized Knowledge

Current merged Knowledge Seed:

`backend/temples/data/knowledge_seeds/nsrc_000002_seed.json`

Materialized payload:

```text
Sources   = 1
Shrines   = 1
Deities   = 0
Histories = 1
```

Source:

```text
key                 = ITOIGAWA_AOSAWA_SPRING_FESTIVAL
source_type         = government
url                 = https://matsuri.geo-itoigawa.com/calendar/m04/
verification_status = source_confirmed
confidence          = high
verified_at         = 2026-10-10T18:00:00+09:00
```

History:

```text
history_type         = regional_context
title                = 青沢神社の春季祭礼
period_text          = 毎年4月第3日曜日
event_date           = null
verification_status  = source_confirmed
confidence           = high
verified_at          = 2026-10-10T18:00:00+09:00
Source relation      = ITOIGAWA_AOSAWA_SPRING_FESTIVAL only
```

No Deity Fact is materialized.

```text
ShrineDeity = 0
```

The secondary deity research lead is not promoted into Knowledge.

## 5. Historical blocker resolution

Historical preflight blocker:

```text
reason_code = BASE_SHRINE_NOT_MATERIALIZED
```

PR #3147 materialized the exact Base Shrine identity:

```text
name_jp   = 青澤神社
address   = 新潟県糸魚川市大字青海2696番地
latitude  = 37.00763484
longitude = 137.79024297
```

Isolated PostgreSQL validation after materialization observed:

```text
exact identity rows = 1
resolve_shrine      = OK
```

Therefore:

```text
BASE_SHRINE_NOT_MATERIALIZED = RESOLVED
```

## 6. G4 PASS condition review

| G4 PASS condition | Result | Evidence |
|---|---|---|
| Fact owner matches G1/G3 | PASS | nsrc-000002 / 青澤神社（糸魚川市） |
| source-less Fact = 0 | PASS | H1 has exactly one Source relation |
| Source identity conflict = 0 | PASS | no SOURCE_REUSE_CONFLICT / SOURCE_REUSE_AMBIGUOUS |
| Fact / Source verification complies | PASS | Source and H1 are source_confirmed / high / verified_at present |
| usable Deity or History >= 1 | PASS | actual Evidence Gate measurement: History 1 / 1 usable |
| tradition is not promoted into asserted history | PASS | H1 is current recurring `regional_context`, not a tradition/founding claim |
| AI-only evidence is not treated as confirmed | PASS | accepted Source is the 糸魚川市 regional festival site |

All PASS conditions are satisfied.

## 7. G4 STOP condition review

| G4 STOP condition | Current state |
|---|---|
| SOURCE_REUSE_CONFLICT | NOT ACTIVE |
| SOURCE_REUSE_AMBIGUOUS | NOT ACTIVE |
| Shrine NOT_FOUND | NOT ACTIVE |
| IMPORT_IDENTITY_AMBIGUOUS | NOT ACTIVE |
| Source insufficient | NOT ACTIVE |
| Fact exceeds Source | NOT ACTIVE |
| Model Risk hidden by Fact | NOT ACTIVE |

No G4 STOP condition is active.

## 8. Actual Evidence Gate measurement

The materialization test measured the persisted History and its persisted Source relation.

Observed:

```text
usable              = True
display_mode        = full
reason_strength     = assertive
verification_status = source_confirmed
confidence          = high
reason              = fact_ready_with_source
```

Therefore:

```text
USABLE_DEITY   = 0
USABLE_HISTORY = 1
USABLE_TOTAL   = 1
```

This is an actual post-materialization measurement, not a semantic preflight expectation.

## 9. Source boundary / semantic safety

The frozen History remains within the accepted Source scope:

- recurring spring festival;
- every third Sunday of April;
- eve kagura;
- mikoshi / children mikoshi procession;
- kagura dedication;
- teodori.

The materialized Fact does not add:

- founding date;
- ancient continuity claim;
- deity identity;
- religious efficacy;
- guaranteed outcome;
- goriyaku mapping;
- recommendation interpretation.

```text
FACT_TEXT_WITHIN_SOURCE = PASS
MODEL_RISK_HIDDEN       = NO
```

## 10. Deity boundary

```text
materialized Deity count = 0
```

No Source-backed deity was available in the frozen accepted packet.

Therefore the following are not promoted:

```text
沼河比賣命
沼河比売命
```

The History-only path satisfies G4 because the contract requires at least one usable Deity
**or** History Fact.

## 11. Idempotency / isolation

Second Knowledge import:

```text
source_REUSE_EXISTING = 1
history_SKIP_EXISTS   = 1
CREATE                = 0
```

Observed:

```text
Source PK unchanged
History PK unchanged
History -> Source relation unchanged
duplicate Source = 0
duplicate History = 0
```

Repository / domain isolation:

```text
Base Seed change in Knowledge PR        = 0
Candidate Master change                 = 0
Position change                         = 0
Ranking / Score change                  = 0
Recommendation logic change             = 0
Concierge / Compass change              = 0
Model / Migration change                = 0
goriyaku / goriyaku_tags change         = 0
GoriyakuTag master change               = 0
ShrineGoriyakuAssignment change         = 0
Production write                        = NONE
```

This satisfies the G4 Isolation Rule.

## 12. Formal Mother Ship decision

Under `docs/knowledge/shrine-expansion-gate-contract.md` §7:

```text
FORMAL_G4_REDECISION = PASS
FORMAL_G4            = PASS

reason:
all G4 PASS conditions satisfied
AND
no G4 STOP condition active
AND
G4 Isolation Rule satisfied
```

The historical preflight remains valid as a record of the earlier blocked state.

It is not rewritten or retroactively changed.

## 13. Boundary

This PASS means:

```text
G4 Knowledge Fact + Evidence = PASS
```

It does **not** mean:

```text
G5 Shared Recommendation Eligibility = PASS
G6 Runtime QA = PASS
G7 Production Import = PASS
G8 CORE_READY = PASS
Candidate Master lifecycle transition = authorized
Production write = authorized
```

G5 must be evaluated separately under the Recommendation Eligibility Contract.

## 14. Final state

```text
G0 nsrc-000002 = PASS
G1 nsrc-000002 = PASS / NEW
G2 nsrc-000002 = PASS
G3 nsrc-000002 = PASS / NORMAL_MODEL_FIT
G4 nsrc-000002 = PASS

G5 = NOT EXECUTED
G6 = NOT EXECUTED
G7 = NOT EXECUTED
G8 = NOT REACHED
```

STOP after Formal G4 redecision.
