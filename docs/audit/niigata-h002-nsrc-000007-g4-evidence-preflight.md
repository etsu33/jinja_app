# NIIGATA-001-H002 — nsrc-000007 G4 Evidence / Seed Preflight

## 1. Status

```text
candidate_id                = nsrc-000007
candidate_name              = 赤城社
canonical_address           = 新潟県十日町市四日町2534番地

UPSTREAM_G3                 = PASS / NORMAL_MODEL_FIT
UPSTREAM_SOURCE_PACKET      = PASS / FROZEN / G4_EVIDENCE_READY

G4_EVIDENCE_PREFLIGHT       = HOLD
reason_code                 = BASE_SHRINE_NOT_MATERIALIZED

KNOWLEDGE_SEED_SCHEMA       = PASS（parse errors = 0）
SOURCE_REUSE_CONFLICT       = 0
SOURCE_REUSE_AMBIGUOUS      = 0
EVIDENCE_SEMANTIC_READINESS = PASS（contract-level only）
KNOWLEDGE_IMPORT_READY      = HOLD
FORMAL_G4                   = HOLD

Production write            = NONE
G5 / G6 / G7 / G8           = NOT EXECUTED
```

- Recorded at: 2026-10-13
- Base: `develop@48f5e18ef4d59c5f3cd1d81571ef6c32b3710ffb`
- Branch: `audit/niigata-h002-nsrc-000007-g4-evidence-preflight`
- Upstream Source Packet（authority）: `docs/audit/niigata-h002-nsrc-000007-g4-source-packet-freeze.md`
- Upstream G3: `docs/audit/niigata-h002-nsrc-000007-g3-source-knowledge-fit.md`
- Precedent（same HOLD shape）: `docs/audit/niigata-h001-nsrc-000002-g4-evidence-preflight.md`

This preflight keeps the existing contract split:

```text
Source Packet PASS
!= Knowledge import ready
!= Formal G4 PASS
```

## 2. Duplicate work check

```text
open PR matching "nsrc-000007"        = 0
remote branch for nsrc-000007 G4 preflight = NONE
（existing remote branch: audit/nsrc-000007-g1-identity-duplicate = G1, unrelated to this task）
```

## 3. Scope

```text
G4_EVIDENCE_PREFLIGHT_SCOPE = { nsrc-000007 }
```

Out of scope（not read as Fact owners, not serialized, not imported）:
nsrc-000006 / nsrc-000008 / nsrc-000009 / nsrc-000010.

## 4. Contracts / implementations re-read（develop@48f5e18e）

| Area | Implementation | Relevant rule |
|---|---|---|
| Knowledge Seed schema | `backend/temples/services/knowledge_seed.py` `parse_seed()` | schema_version `1.0`/`1.1`/`1.2`; `source_type` / `history_type` enum; `verification_status ∈ {source_confirmed, reviewed}` requires `verified_at`; `source_keys` must reference keys in the same seed |
| Source identity | `resolve_source_identity()` | URL-backed Source identity = `source_type + normalize_source_url(url)`; >1 match = `SOURCE_REUSE_AMBIGUOUS`; 1 match with differing `publisher / verification_status / confidence / bibliography / language` = `SOURCE_REUSE_CONFLICT` |
| Shrine identity | `resolve_shrine(name_jp, address)` | filter by `name_jp`, then narrow by exact `address`; no match = `NOT_FOUND`; unresolved multiple = `AMBIGUOUS` |
| Evidence Gate | `backend/temples/services/evidence_gate.py` `decide_fact_usability()` | usable = Fact `verification_status ∈ {reviewed, source_confirmed}` AND ≥1 related Source in the same set; `confidence` is metadata only |
| Importer | `import_shrine_knowledge` | `--validate-only` = schema + shrine resolution; `--dry-run` = full CREATE/SKIP plan, no write; apply = same plan, then one atomic transaction only when errors = 0; existing identical History/Deity = `SKIP_EXISTS`, Source = `REUSE_EXISTING` |

## 5. Frozen Source verification metadata

Stable Source keys are seed-local keys（not Production IDs）. Semantic identity stays `source_type + normalized URL`.

| | S2 | S3 |
|---|---|---|
| stable key | `TOKAMACHI_REKIBUN_SHIRYOU` | `TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN` |
| source_type | `government` | `museum_or_archive` |
| title | `歴史文化基本構想 資料集` | `越後縮幡` |
| publisher | `十日町市` | `十日町市博物館` |
| url | `https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf` | `https://www.tokamachi-museum.jp/archives/bunka023/` |
| bibliography | `中魚沼郡誌上 p.398` | （none） |
| language | `ja` | `ja` |
| accessed_at | `2026-10-13` | `2026-10-13` |
| verification_status | `source_confirmed` | `source_confirmed` |
| confidence | `high` | `high` |
| verified_at（date authority） | `2026-10-13` | `2026-10-13` |

S1（新潟県神社庁）は identity / listing provenance only であり、Packet §7 のとおり H1 / H2 の relation を持たないため Knowledge Seed の Source に含めない。

Basis:

- `verification_status = source_confirmed`: Packet / G3 record `content_verified_on = 2026-10-13` for S2 / S3（content confirmed, not only accessed）.
- `confidence = high`: municipal（S2）and municipal museum（S3）primary publication of shrine-specific material; same classification as the accepted H001 government Sources（`nsrc_000002_seed.json`）.

### verified_at precision note

Upstream records only the date（`2026-10-13`）. The model field is a datetime.
The preflight serialization used `2026-10-13T00:00:00+09:00`; the time component is a
serialization placeholder and carries **no** time-of-day precision.

```text
VERIFIED_AT_DATE           = 2026-10-13（authority: Packet / G3）
VERIFIED_AT_TIME_COMPONENT = NOT RECORDED UPSTREAM（placeholder 00:00:00+09:00 in preflight payload only）
```

The re-entry materialization PR must either keep this date-level placeholder with the same
note or record a real verification time; it must not invent a time-of-day.

## 6. Frozen History verification metadata

| | H1 | H2 |
|---|---|---|
| history_type | `historical_event` | `regional_context` |
| title | `安政7年正月の再建` | `赤城社に伝わった越後縮幡` |
| content | `赤城社は安政7年正月に再建された。` | `越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。` |
| period_text | `安政7年正月` | `""` |
| event_date | `null` | `null` |
| source_keys | `[TOKAMACHI_REKIBUN_SHIRYOU]`（S2 only） | `[TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN]`（S3 only） |
| verification_status | `source_confirmed` | `source_confirmed` |
| confidence | `high` | `high` |
| verified_at（date authority） | `2026-10-13` | `2026-10-13` |

Title / history_type / content / period_text / event_date / owner are copied verbatim from the frozen Packet §6.
No field was changed; the Packet was serializable as-is.

```text
deities          = []（0）
collectives      = []（0）
source_facts     = []（0）
土田岐入彦命      = NOT SERIALIZED（historical Source evidence only）
経津主命          = NOT SERIALIZED（research lead only）
source-less History in payload = 0
```

## 7. Base Shrine prerequisite

Current `develop` Base Seed:

```text
path = backend/temples/data/shrines_seed_clean.json
rows = 122
```

Exact target lookup:

```text
name_jp = 赤城社
address = 新潟県十日町市四日町2534番地

exact row count        = 0
same-name 赤城社 rows   = 0
```

```text
BASE_SHRINE_MATERIALIZED = NO
```

Frozen Base Shrine identity for the re-entry（identity only; this PR does not materialize it）:

```text
name_jp = 赤城社
address = 新潟県十日町市四日町2534番地
```

Coordinates are not frozen by this preflight. The G2 Position authority is
`docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`; the re-entry PR must take
values from that record, not from this document.

## 8. Frozen `shrine_ref`

```json
{
  "name_jp": "赤城社",
  "address": "新潟県十日町市四日町2534番地"
}
```

Exact `name_jp + address`. Name-only resolution is not used as Fact ownership.

## 9. Preflight payload（not committed）

The payload below was used only for the isolated preflight. It is **not** added to
`backend/temples/data/knowledge_seeds/` by this PR.

```text
sha256 = 53d6f9e0219deb764e94fd8503ed709be0ca3450c386d2c00d7d1ac8c11fb96f
```

```json
{
  "schema_version": "1.0",
  "sources": [
    {
      "key": "TOKAMACHI_REKIBUN_SHIRYOU",
      "source_type": "government",
      "title": "歴史文化基本構想 資料集",
      "publisher": "十日町市",
      "url": "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
      "bibliography": "中魚沼郡誌上 p.398",
      "language": "ja",
      "accessed_at": "2026-10-13",
      "verified_at": "2026-10-13T00:00:00+09:00",
      "verification_status": "source_confirmed",
      "confidence": "high"
    },
    {
      "key": "TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN",
      "source_type": "museum_or_archive",
      "title": "越後縮幡",
      "publisher": "十日町市博物館",
      "url": "https://www.tokamachi-museum.jp/archives/bunka023/",
      "language": "ja",
      "accessed_at": "2026-10-13",
      "verified_at": "2026-10-13T00:00:00+09:00",
      "verification_status": "source_confirmed",
      "confidence": "high"
    }
  ],
  "shrines": [
    {
      "shrine_ref": {
        "name_jp": "赤城社",
        "address": "新潟県十日町市四日町2534番地"
      },
      "deities": [],
      "histories": [
        {
          "history_type": "historical_event",
          "title": "安政7年正月の再建",
          "content": "赤城社は安政7年正月に再建された。",
          "period_text": "安政7年正月",
          "event_date": null,
          "verification_status": "source_confirmed",
          "confidence": "high",
          "verified_at": "2026-10-13T00:00:00+09:00",
          "source_keys": ["TOKAMACHI_REKIBUN_SHIRYOU"]
        },
        {
          "history_type": "regional_context",
          "title": "赤城社に伝わった越後縮幡",
          "content": "越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。",
          "period_text": "",
          "event_date": null,
          "verification_status": "source_confirmed",
          "confidence": "high",
          "verified_at": "2026-10-13T00:00:00+09:00",
          "source_keys": ["TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN"]
        }
      ]
    }
  ]
}
```

## 10. Isolated DB preflight（actual measurement）

Environment:

```text
DB          = isolated local PostgreSQL/PostGIS database（created for this preflight, dropped afterwards）
Production  = NOT CONNECTED
migrations  = develop@48f5e18e, applied from empty
```

Setup:

```text
import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags
  -> created=122

import_shrine_knowledge <each repository knowledge seed>（to reproduce the repository Source universe）
  -> 18 seeds imported
  -> a5b_collective_pattern_b_seed.json blocked（23 errors; its shrine_refs are not in the Base Seed）

state before preflight:
  Shrine = 122 / ShrineKnowledgeSource = 139 / ShrineDeity = 295 / ShrineHistory = 229
  ShrineSourceFact = 34 / Shrine.goriyaku_tags links = 0 / ShrineGoriyakuAssignment = 0 / GoriyakuTag = 0
```

### 10.1 Schema（no DB）

```text
parse_seed(payload).errors = []
sources  = TOKAMACHI_REKIBUN_SHIRYOU, TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN
shrines  = 1（赤城社 / 新潟県十日町市四日町2534番地）, deities 0, histories 2, collectives 0, source_facts 0
H1 -> [TOKAMACHI_REKIBUN_SHIRYOU], event_date None, period_text 安政7年正月
H2 -> [TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN], event_date None, period_text ""
```

### 10.2 Shrine identity

```text
Shrine name_jp=赤城社（any address）          = 0 rows
Shrine 赤城社 / 新潟県十日町市四日町2534番地    = 0 rows
resolve_shrine                               = NOT_FOUND
```

### 10.3 Source reuse

```text
existing Sources matching normalized S2 URL（any source_type） = 0
existing Sources matching normalized S3 URL（any source_type） = 0
repository seed files referencing S2 / S3 URL               = 0

S2 resolve_source_identity = CREATE
S3 resolve_source_identity = CREATE

SOURCE_REUSE_CONFLICT  = 0
SOURCE_REUSE_AMBIGUOUS = 0
```

### 10.4 Importer runs

```text
$ import_shrine_knowledge <payload> --validate-only
ERROR: shrine '赤城社': NOT_FOUND (no shrine with name_jp='赤城社')
CommandError: validation failed with 1 error(s)              exit=1

$ import_shrine_knowledge <payload> --dry-run
[source] CREATE [TOKAMACHI_REKIBUN_SHIRYOU] government: 歴史文化基本構想 資料集
[source] CREATE [TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN] museum_or_archive: 越後縮幡
plan summary: {'source_CREATE': 2}
ERROR: shrine '赤城社': NOT_FOUND (no shrine with name_jp='赤城社')
CommandError: import blocked: 1 error(s), see above          exit=1

$ import_shrine_knowledge <payload>（isolated apply attempt）
（same plan / same error）
CommandError: import blocked: 1 error(s), see above          exit=1
```

Table counts before / after all three runs: identical（`DB_UNCHANGED`）.
The importer aborted before its write transaction; no Source / History / Deity row was created.

### 10.5 Evidence Gate

```text
Actual DB measurement（H1 / H2 usable on materialized rows） = NOT EXECUTABLE（no History row can be created）

Contract-level check only:
decide_fact_usability(verification_status=source_confirmed, confidence=high,
                      source_verification_statuses=[source_confirmed])
H1 -> usable=True, reason=fact_ready_with_source
H2 -> usable=True, reason=fact_ready_with_source
```

This contract-level result is **not** the PASS-required actual Evidence Gate measurement.

### 10.6 Remaining measurements

```text
source-less History count（materialized） = NOT EXECUTABLE（payload design = 0）
second-run idempotency                   = NOT EXECUTABLE
Deity rows created                       = 0（import aborted; payload deities = 0）
goriyaku-related data                    = UNCHANGED（0 / 0 / 0 before and after）
```

## 11. Formal G4 decision

| G4 PASS condition | Result |
|---|---|
| canonical Shrine identity resolves exactly | **NO — NOT_FOUND** |
| Fact owner remains nsrc-000007 | PASS（shrine_ref exact name + address） |
| Source identity conflict = 0 | PASS（CONFLICT 0 / AMBIGUOUS 0） |
| source-less adopted History = 0 | design PASS / materialized **NOT MEASURED** |
| Fact / Source verification metadata comply with contract | PASS（parse errors 0; verified_at date-level, §5 note） |
| ≥1 usable History under actual Evidence Gate | **NOT MEASURED** |
| Source precision not exceeded | PASS（H1 period_text 安政7年正月 / event_date null; H2 no date） |
| no unsupported current Deity inference | PASS（deities 0） |
| isolated validation / idempotency pass | **NO — validate-only / dry-run fail on NOT_FOUND; idempotency not executable** |
| no Production write | PASS |

```text
FORMAL_G4   = HOLD
reason_code = BASE_SHRINE_NOT_MATERIALIZED
```

This is a data-materialization prerequisite HOLD（same shape as the nsrc-000002 G4 preflight）.
It does not reverse G1 / G2 / G3 or the G4 Source Packet freeze.
Nothing was repaired by inference: no Base Shrine row was synthesized, in the repository or in the isolated DB.

## 12. Required re-entry（not executed here）

A separate PR dedicated to `nsrc-000007` must:

1. materialize exactly one Base Shrine row `赤城社 / 新潟県十日町市四日町2534番地`, with
   coordinates from the G2 Position Resolution Record, no inferred goriyaku, no inferred visit-style values;
2. add `backend/temples/data/knowledge_seeds/nsrc_000007_seed.json` equal to the §9 payload
   （or a reviewed, recorded verified_at time; §5 note）;
3. measure on an isolated DB:
   - validate-only / dry-run PASS, NOT_FOUND = 0, IMPORT_IDENTITY_AMBIGUOUS = 0;
   - SOURCE_REUSE_CONFLICT = 0 / SOURCE_REUSE_AMBIGUOUS = 0;
   - H1 Source relation = exactly S2, H2 Source relation = exactly S3;
   - H1 / H2 Evidence Gate usable on materialized rows;
   - source-less History = 0, Deity rows for nsrc-000007 = 0;
   - second import: Source `REUSE_EXISTING`, History `SKIP_EXISTS`, zero new CREATE;
   - goriyaku state unchanged.

Then re-enter G4 for the formal PASS / HOLD decision.

### Risk carried into re-entry

`resolve_shrine()` filters by `name_jp` first. If the exact address matches no row but exactly one
`赤城社` exists elsewhere, it returns `OK` for that row. Today there are 0 `赤城社` rows, so this is not
triggered, but H002 has four distinct `赤城社` candidates（nsrc-000007〜000010）. The re-entry tests must
assert the exact `(name_jp, address)` row is the one resolved.

## 13. Impact boundary

```text
Candidate Master                       NONE
Base Shrine Seed                       NONE
Knowledge Seed                         NONE（payload kept out of the repository）
Model / Migration / Serializer / Runtime NONE
Evidence Gate / importer code          NONE
goriyaku / goriyaku_tags / Assignment  NONE
Recommendation / Ranking / Score       NONE
Concierge / Compass                    NONE
Production DB                          NONE（not connected）
G5                                     NOT EXECUTED
```

## 14. Rollback

This PR adds one audit document only. Rollback = revert the commit.
The isolated database was local and was dropped after the preflight; no other state exists.

## 15. Final state

```text
G4 Source Packet Freeze      = PASS / FROZEN
G4 Evidence / Seed Preflight = HOLD / BASE_SHRINE_NOT_MATERIALIZED
G5 / G6 / G7 / G8            = NOT EXECUTED
PRODUCTION_WRITE             = NONE
```

## 16. STOP

Do not execute G5. Do not materialize Base Shrine or Knowledge Seed in this PR. Do not write Production.
