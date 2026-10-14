# NIIGATA-001-H002 — nsrc-000006 G4 Knowledge Fact + Evidence

## 1. Status

```text
candidate_id                 = nsrc-000006
name_jp                      = 赤井神社
address                      = 新潟県佐渡市加茂歌代2662番地

G1                           = PASS / NEW
G2                           = CLOSED / PASS
G3                           = PASS / NORMAL_MODEL_FIT
G4 Source Packet             = PASS / FROZEN / G4_EVIDENCE_READY
Base Shrine prerequisite     = PASS / 124 rows / exact target 1

Knowledge Seed schema        = READY_FOR_CI_MEASUREMENT
Source conflict              = NOT_OBSERVED_IN_REPOSITORY_SCAN
Source ambiguity             = NOT_OBSERVED_IN_REPOSITORY_SCAN

H1 relation                  = S2 exactly
H2 relation                  = S2 exactly
H3 relation                  = S3 exactly

source-less History          = expected 0
Deity                        = 0
Collective                   = 0
SourceFact                   = 0

Evidence Gate                = PENDING_CI_MEASUREMENT
validate-only                = PENDING_CI_MEASUREMENT
dry-run                      = PENDING_CI_MEASUREMENT
apply                        = PENDING_CI_MEASUREMENT
second import                = PENDING_CI_MEASUREMENT

goriyaku state               = expected unchanged
Production write             = NONE
G5                           = NOT_EXECUTED

FORMAL_G4                    = PENDING_CI_MEASUREMENT
```

- Recorded at: 2026-10-14
- Base: `develop@9af35c6776aaba8d19b1d9566c941809ff69e586`（PR #3206 merged）
- Branch: `feature/nsrc-000006-g4-knowledge-materialization`

## 2. Authority

- `docs/audit/niigata-h002-nsrc-000006-g4-source-packet-freeze.md`
- `docs/audit/niigata-h002-nsrc-000006-g3-source-knowledge-fit.md`
- `docs/audit/niigata-h002-nsrc-000006-base-shrine-materialization.md`
- `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`
- `docs/knowledge/shrine-expansion-gate-contract.md` §7
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/services/evidence_gate.py`

This G4 task materializes only the Source-backed History payload authorized by Mother Ship G3 decision A.

```text
CURRENT_DEITY                = NOT_FROZEN
SHRINE_DEITY_ROWS_AUTHORIZED = 0
```

## 3. Base Shrine prerequisite

PR #3206 materialized exactly:

```text
name_jp   = 赤井神社
address   = 新潟県佐渡市加茂歌代2662番地
latitude  = 38.085938
longitude = 138.418312
```

Current Base Seed count:

```text
124
```

G4 does not modify identity, address, or coordinate.

## 4. Knowledge Seed

Target:

`backend/temples/data/knowledge_seeds/nsrc_000006_seed.json`

Schema:

```text
schema_version = 1.0
Source rows    = 2
Deity rows     = 0
History rows   = 3
```

### S2 — 佐渡芸能アーカイブ

```text
key                 = SADO_GEINOU_KAMOUTASHIRO_ONIDAIKO
source_type         = tourism_official
title               = 加茂歌代まつりの鬼太鼓
publisher           = 佐渡芸能アーカイブ
url                 = https://sado-geinou.com/geinou/kamoutashiro/
language            = ja
accessed_at         = 2026-10-14
verification_status = source_confirmed
confidence          = high
verified_at         = 2026-10-14T00:00:00+09:00
```

### S3 — 『佐渡神社誌』

```text
key                 = SADO_JINJASHI_1926
source_type         = local_history
title               = 佐渡神社誌
publisher           = 新潟県神職会佐渡支部
url                 = https://dl.ndl.go.jp/pid/971197
bibliography        = 新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602
language            = ja
accessed_at         = 2026-10-14
verification_status = source_confirmed
confidence          = high
verified_at         = 2026-10-14T00:00:00+09:00
```

`verified_at = 00:00:00+09:00` is a date-level serialization placeholder.
The upstream audit verified the Source on 2026-10-14; the zero time is not a claim about an observed clock time.

S1 新潟県神社庁 is not serialized because it is identity / listing provenance only and has no frozen History relation.

## 5. Frozen History payload

### H1

```text
history_type = regional_context
title        = 4月16日の赤井神社例祭と鬼太鼓奉納
content      = 赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が神社で舞を奉納した後、各地区を門付けする。
period_text  = ""
event_date   = null
source       = S2 exactly
```

### H2

```text
history_type = tradition
title        = 元日午前0時の鬼太鼓奉納
content      = 加茂歌代の鬼太鼓は、元日の午前0時にも赤井神社で舞を奉納する。
period_text  = ""
event_date   = null
source       = S2 exactly
```

The `tradition` type is preserved. G4 does not promote H2 into a confirmed historical event.

### H3

```text
history_type = regional_context
title        = 加茂の五神社としての記録
content      = 1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を「加茂の五神社」と記録している。
period_text  = ""
event_date   = null
source       = S3 exactly
```

The publication year is Source context, not an event date for the underlying shrine relation.

## 6. Fact ↔ Source relation

Frozen graph:

```text
S2
├─ H1
└─ H2

S3
└─ H3
```

Expected persisted invariants:

```text
H1 Source count = 1
H2 Source count = 1
H3 Source count = 1
source-less target History = 0
```

No relation to S1 is serialized.

## 7. Current Deity boundary

No current Deity row is authorized.

Historical S3 names remain outside the current Deity payload:

```text
素盞嗚尊
別雷尊
倉稲魂命
菅原道真公
```

Third-party research leads also remain excluded.

Expected materialized counts:

```text
ShrineDeity           +0
ShrineDeityCollective +0
```

## 8. Source identity / reuse preflight

Repository-wide Knowledge Seed search before this PR found no other Seed containing:

```text
https://sado-geinou.com/geinou/kamoutashiro/
https://dl.ndl.go.jp/pid/971197
```

Proposed stable Source keys also had no existing repository match.

Therefore the static preflight state is:

```text
SOURCE_REUSE_CONFLICT_STATIC  = 0
SOURCE_REUSE_AMBIGUOUS_STATIC = 0
```

The importer dry-run / isolated apply remains authoritative for actual reuse behavior.

## 9. Required G4 measurement

The target-specific regression test must prove on an isolated test DB:

1. Base Seed import resolves exact `(name_jp, address)`.
2. noncanonical address variants fail closed.
3. Knowledge Seed parser has zero errors.
4. validate-only performs zero writes.
5. dry-run plans exactly Source +2 / History +3 / Deity +0.
6. apply persists exactly Source +2 / History +3 for this target.
7. all three History rows have exactly one Source.
8. target source-less History count = 0.
9. target Deity / Collective / SourceFact count = 0.
10. Evidence Gate returns `usable=True` for H1/H2/H3.
11. H2 remains `history_type=tradition`.
12. second import is idempotent.
13. goriyaku / goriyaku_tags / ShrineGoriyakuAssignment state is unchanged.
14. no Source conflict / ambiguity / identity ambiguity stop code occurs.

Regression:

`backend/temples/tests/test_nsrc_000006_knowledge_seed.py`

## 10. Isolation boundary

This G4 task does not change:

```text
Candidate Master
Position
Base Shrine values
current Deity
goriyaku / goriyaku_tags
ShrineGoriyakuAssignment
Recommendation mapping
Ranking / Score
Concierge / Compass
models / migrations
other H002 candidates
Production DB
```

## 11. G4 acceptance matrix

| Condition | Pre-CI state |
|---|---|
| Fact owner matches G1/G3 | PASS |
| exact Base Shrine exists | PASS |
| source-less Fact = 0 | PENDING isolated apply |
| Source identity conflict = 0 | STATIC PASS / runtime PENDING |
| Fact / Source verification fits contract | payload PASS / runtime PENDING |
| usable Deity or History >= 1 | PENDING Evidence Gate |
| tradition not promoted to historical_event | PASS in Seed |
| AI-only material used as confirmed Source | NO |
| Deity inference | NONE |
| goriyaku isolation | PENDING regression |
| idempotency | PENDING regression |
| Production write | NONE |

## 12. Current classification

Before CI measurement:

```text
G4_PAYLOAD_FREEZE = PASS
G4_SEED_CREATED   = YES
FORMAL_G4         = PENDING_CI_MEASUREMENT
FACT_READY        = NO
G5                = NOT_EXECUTED
PRODUCTION_WRITE  = NONE
```

Do not infer Formal G4 PASS from Seed presence alone.

## 13. STOP boundary

If any target regression or importer STOP code fails:

```text
FORMAL_G4 = HOLD
STOP      = TRUE
```

Do not modify Production, Recommendation, Ranking, or current Deity to make the test pass.

After all required CI measurements pass, update this audit to the observed results and close G4.
