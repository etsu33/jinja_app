# NIIGATA-001-H002 — nsrc-000009 G4 Formal PASS

## 1. Status

```text
candidate_id                 = nsrc-000009
name_jp                      = 赤城社
address                      = 新潟県十日町市伊達乙48番地

Base Shrine prerequisite     = PASS
G3                           = CLOSED / PASS / NORMAL_MODEL_FIT
Knowledge Seed               = MERGED / schema 1.3
Source provenance model      = MERGED / ShrineFactSourceCitation

Source reuse                 = REUSE_EXISTING
Source conflict              = 0
Source ambiguity             = 0

H1                           = 天明3年8月の創立記録
H2                           = 大正2年の改築記録
H1 / H2 Source               = TOKAMACHI_REKIBUN_SHIRYOU
H1 / H2 citation locator     = 中魚沼郡誌上 p.445

source-less History          = 0
ShrineDeity                  = 0
ShrineDeityCollective        = 0
ShrineSourceFact             = 0

actual H1 Evidence Gate      = measured / usable=True
actual H2 Evidence Gate      = measured / usable=True

validate-only                = PASS
dry-run                      = PASS
apply                        = PASS
second import                = IDEMPOTENT

Production write             = NONE
Candidate Master write       = NONE
G5                           = NOT EXECUTED

FORMAL_G4                    = PASS
```

- Recorded at: 2026-10-16
- Base: `develop@63a4693777bf6f1d5c39d6f1dcdcf13f86650c3e`（PR #3233 merged）
- Branch: `docs/nsrc-000009-g4-formal-pass`

## 2. Authority

This closure is evaluated under:

- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/fact-source-citation-contract.md`
- `docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md`
- `backend/temples/services/evidence_gate.py`
- `backend/temples/services/knowledge_seed.py`

This document records the G4 result only.
It does not execute G5, G6, G7, or G8.

## 3. Frozen Fact owner and scope

```text
FACT_OWNER
= nsrc-000009
= 赤城社 / 新潟県十日町市伊達乙48番地
```

Authorized G4 Fact scope inherited from G3:

```text
ShrineHistory
- H1 天明3年8月の創立記録 / historical_event
- H2 大正2年の改築記録 / historical_event

ShrineDeity
- 0 rows

ShrineDeityCollective
- 0 rows
```

The historical Source wording `祭神：大山祇命` remains historical evidence only.
No current ShrineDeity row is created.

## 4. Source and citation boundary

Shared Source:

```text
key          = TOKAMACHI_REKIBUN_SHIRYOU
source_type  = government
publisher    = 十日町市
url          = https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
bibliography = 中魚沼郡誌上 p.398
```

The `bibliography = 中魚沼郡誌上 p.398` value is retained only to satisfy the legacy Source reuse
contract for the existing nsrc-000007 Source row.

It is not the authority for the nsrc-000009 Fact location.

Fact-specific authority:

```text
H1 ShrineFactSourceCitation.locator_text
= 中魚沼郡誌上 p.445

H2 ShrineFactSourceCitation.locator_text
= 中魚沼郡誌上 p.445
```

The importer keeps `SOURCE_REUSE_CONFLICT` fail-closed behavior unchanged.

## 5. Knowledge Seed

Repository Seed:

```text
backend/temples/data/knowledge_seeds/nsrc_000009_seed.json
schema_version = 1.3
```

H1:

```text
history_type = historical_event
title        = 天明3年8月の創立記録
content      = 赤城社は天明3年8月に創立されたと記録されている。
period_text  = 天明3年8月
event_date   = null
source       = TOKAMACHI_REKIBUN_SHIRYOU
citation     = 中魚沼郡誌上 p.445
```

H2:

```text
history_type = historical_event
title        = 大正2年の改築記録
content      = 赤城社は大正2年に改築されたと記録されている。
period_text  = 大正2年
event_date   = null
source       = TOKAMACHI_REKIBUN_SHIRYOU
citation     = 中魚沼郡誌上 p.445
```

Both Facts:

```text
verification_status = source_confirmed
confidence          = high
event_date          = null
```

No exact Gregorian date is synthesized.

## 6. Isolated execution result

The regression in `backend/temples/tests/test_nsrc_000009_knowledge_seed.py` reproduces the
important legacy state by importing nsrc-000007 first, making the shared municipal Source already
exist before nsrc-000009 is executed.

Measured contract:

### validate-only

```text
PASS
DB writes = 0
```

### dry-run

```text
Source REUSE_EXISTING = 1
History CREATE         = 2
Citation CREATE        = 2

NOT_FOUND                       = 0
IMPORT_IDENTITY_AMBIGUOUS       = 0
SOURCE_REUSE_CONFLICT           = 0
SOURCE_REUSE_AMBIGUOUS          = 0
CITATION_SOURCE_NOT_RELATED     = 0

DB writes = 0
```

### apply

```text
Source CREATE      = 0
History CREATE     = 2
Citation CREATE    = 2
ShrineDeity        = 0
ShrineDeityCollective = 0
ShrineSourceFact   = 0
```

Persisted state:

```text
H1 Source relation = shared municipal Source exactly
H2 Source relation = shared municipal Source exactly

H1 citation = p.445 exactly
H2 citation = p.445 exactly

shared Source bibliography remains p.398
source-less target History = 0
```

### second import

```text
Source REUSE_EXISTING = 1
History SKIP_EXISTS   = 2
Citation SKIP_EXISTS  = 2

Source CREATE         = 0
History CREATE        = 0
Citation CREATE       = 0

state after import #2 = state after import #1
```

Therefore:

```text
IDEMPOTENCY = PASS
```

## 7. Evidence Gate result

The persisted H1 / H2 rows are evaluated using their actual M2M Source relations.

For both H1 and H2:

```text
Fact verification_status     = source_confirmed
Fact confidence              = high
Source verification_statuses = [source_confirmed]

usable          = True
display_mode    = full
reason_strength = assertive
reason          = fact_ready_with_source
```

Therefore:

```text
USABLE_HISTORY_COUNT = 2
G4_USABLE_FACT_MINIMUM_MET = YES
```

## 8. Formal G4 evaluation

| G4 condition | Evidence | Result |
|---|---|---|
| Fact owner matches G1 / G3 | exact target = 赤城社 / 伊達乙48番地 | PASS |
| source-less Fact = 0 | H1 / H2 each have the shared Source relation | PASS |
| Source identity conflict = 0 | SOURCE_REUSE_CONFLICT / AMBIGUOUS not observed | PASS |
| Fact / Source verification contract | source_confirmed / high / verified_at present | PASS |
| usable Deity or History >= 1 | H1 usable=True, H2 usable=True | PASS |
| Fact does not exceed Source | H1 / H2 remain within frozen G3 historical wording | PASS |
| current Deity inference absent | ShrineDeity = 0 | PASS |
| citation locator traceable | H1 / H2 each persist p.445 citation | PASS |
| importer idempotent | second import CREATE = 0 | PASS |
| Ranking / Score / Position isolation | no changes | PASS |
| Production isolation | no Production connection/write in this closure | PASS |

No active G4 STOP condition remains.

```text
FORMAL_G4 = PASS
```

## 9. Impact boundary

```text
Knowledge Seed                         unchanged / already merged
Knowledge importer                     unchanged
Evidence Gate                          unchanged
Source provenance model                unchanged / already merged

Candidate Master                       NONE
Base Shrine Seed                       NONE
Position                               NONE
goriyaku / tags                        NONE
Recommendation / Ranking / Score       NONE
Concierge / Compass                    NONE
Production DB                          NONE
other H002 candidates                  NONE
```

## 10. Final state / STOP

```text
NSRC_000009_G0 = PASS
NSRC_000009_G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
NSRC_000009_G2 = CLOSED / PASS
NSRC_000009_G3 = CLOSED / PASS / NORMAL_MODEL_FIT
NSRC_000009_G4 = CLOSED / PASS

G5 = NOT EXECUTED
G6 = NOT EXECUTED
G7 = NOT EXECUTED
G8 = NOT EXECUTED

Production write = NONE
```

Do not infer G5 PASS from G4 PASS.
Do not update Candidate Master lifecycle in this closure.
Do not write Production.
