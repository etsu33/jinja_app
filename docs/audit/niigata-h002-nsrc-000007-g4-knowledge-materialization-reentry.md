# NIIGATA-001-H002 — nsrc-000007 G4 Knowledge Materialization + Formal Re-entry

## 1. Status

```text
candidate_id                 = nsrc-000007
name_jp                      = 赤城社
address                      = 新潟県十日町市四日町2534番地

Base Shrine prerequisite     = PASS / 123 rows / exact target 1
Source Packet                = unchanged / frozen
Knowledge Seed schema        = PASS

Source conflict              = 0
Source ambiguity             = 0

H1 relation                  = S2 exactly
H2 relation                  = S3 exactly

source-less History          = 0
Deity                        = 0
Collective                   = 0
SourceFact                   = 0

actual H1 Evidence Gate      = measured / usable=True
actual H2 Evidence Gate      = measured / usable=True

validate-only                = PASS
dry-run                      = PASS
apply                        = PASS
second import                = IDEMPOTENT

goriyaku state               = unchanged
Production write             = NONE
G5                           = NOT EXECUTED

FORMAL_G4                    = PASS
```

- Recorded at: 2026-10-13
- Base: `develop@9ad55dc3672d7a448abaa9a1e3321db901a721f8`（#3189 merged; includes #3188）
- Branch: `feature/nsrc-000007-g4-knowledge-materialization-reentry`

## 2. Re-entry context

The earlier preflight `docs/audit/niigata-h002-nsrc-000007-g4-evidence-preflight.md`（PR #3187, still open）
recorded `FORMAL_G4 = HOLD / BASE_SHRINE_NOT_MATERIALIZED` against a 122-row Base Seed.

- #3188 made `resolve_shrine()` fail closed on exact-address misses.
- #3189 materialized the nsrc-000007 Base Shrine（Base Seed 122 -> 123）, resolving that prerequisite.

G4 was **re-measured from the current repository state** in this document. The #3187 HOLD conclusion is
obsolete and is not carried over. Only its frozen payload was used, as historical input: the committed
seed is semantically equal（parsed JSON `==`）to the #3187 preflight payload.

Correction to a #3187 note: #3187 §10 said `a5b_collective_pattern_b_seed.json` was blocked because "its
shrine_refs are not in the Base Seed". That was wrong. Its 6 shrine_refs all match the Base Seed exactly
（verified in #3188）. It failed there only because it was imported first in alphabetical order, before
the batch seeds that create the Deities its memberships reference. Imported after them（§6）, it applies
cleanly. This does not affect nsrc-000007.

## 3. Authority re-read

- `docs/audit/niigata-h002-nsrc-000007-g4-source-packet-freeze.md`（Fact scope, H1 -> S2, H2 -> S3, Deity boundary）
- `docs/audit/niigata-h002-nsrc-000007-g3-source-knowledge-fit.md`（NORMAL_MODEL_FIT, content_verified_on 2026-10-13）
- `docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`（identity / position; unchanged）
- `docs/knowledge/shrine-expansion-gate-contract.md` §7（G4 PASS / STOP conditions）
- `docs/knowledge/shrine-knowledge-contract.md`（verification metadata, accessed_at vs verified_at）
- `backend/temples/services/knowledge_seed.py`（`parse_seed`, `resolve_source_identity`, `resolve_shrine`）
- `backend/temples/services/evidence_gate.py`（`decide_fact_usability`）

## 4. Knowledge Seed

`backend/temples/data/knowledge_seeds/nsrc_000007_seed.json`（schema 1.0）

| | S2 | S3 |
|---|---|---|
| key | `TOKAMACHI_REKIBUN_SHIRYOU` | `TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN` |
| source_type | `government` | `museum_or_archive` |
| title | `歴史文化基本構想 資料集` | `越後縮幡` |
| publisher | `十日町市` | `十日町市博物館` |
| url | `https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf` | `https://www.tokamachi-museum.jp/archives/bunka023/` |
| bibliography | `中魚沼郡誌上 p.398` | — |
| language / accessed_at | `ja` / `2026-10-13` | `ja` / `2026-10-13` |
| verification_status / confidence | `source_confirmed` / `high` | `source_confirmed` / `high` |
| verified_at | `2026-10-13T00:00:00+09:00` | `2026-10-13T00:00:00+09:00` |

S1（新潟県神社庁）is not serialized. It is identity / listing provenance only and has no H1 / H2 relation.

| | H1 | H2 |
|---|---|---|
| history_type | `historical_event` | `regional_context` |
| title | `安政7年正月の再建` | `赤城社に伝わった越後縮幡` |
| content | `赤城社は安政7年正月に再建された。` | `越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。` |
| period_text | `安政7年正月` | `""` |
| event_date | `null` | `null` |
| verification_status / confidence | `source_confirmed` / `high` | `source_confirmed` / `high` |
| verified_at | `2026-10-13T00:00:00+09:00` | `2026-10-13T00:00:00+09:00` |
| source_keys | `[TOKAMACHI_REKIBUN_SHIRYOU]` | `[TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN]` |

`shrine_ref = {"name_jp": "赤城社", "address": "新潟県十日町市四日町2534番地"}`. `deities = []`.
There are no collectives, source_facts, goriyaku, or derived fields.

### verified_at semantics

```text
authority date             = 2026-10-13（Packet / G3 content_verified_on）
serialized                 = 2026-10-13T00:00:00+09:00
time-of-day factual meaning = NONE（00:00:00 is a date-level serialization placeholder）
real verification time     = NOT RECORDED（this task did not re-verify the Sources）
```

Storage note: the DB stores the instant in UTC as `2026-10-12T15:00:00+00:00`, the same instant as
`2026-10-13T00:00+09:00`. Any consumer that renders `verified_at` as a UTC calendar date would show
`2026-10-12`. No such rendering is part of G4, but it is recorded here as a known representation risk.

## 5. Schema validation（no DB）

```text
parse_seed errors = 0
sources = 2 / shrines = 1 / deities = 0 / histories = 2 / collectives = 0 / source_facts = 0

H1 -> [S2] exactly        H2 -> [S3] exactly
H1 -> S1 none / H2 -> S1 none / H1 -> S3 none / H2 -> S2 none
S1 URL present in seed = NO
土田岐入彦命 / 経津主命 present in seed = NO
```

## 6. Isolated PostgreSQL execution（actual measurement）

Environment:

```text
DB          = isolated local PostgreSQL/PostGIS database, created for this run and dropped afterwards
Production  = NOT CONNECTED
migrations  = develop@9ad55dc3, applied from empty
```

Repository state reproduced first:

```text
import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags
  -> done created=123 updated=0 skipped=0 total_seed=123
all 19 other repository Knowledge Seeds
  -> imported（a5b collective seed applied after the batch seeds; §2 correction）

state before nsrc-000007:
  Shrine 123 / ShrineKnowledgeSource 139 / ShrineDeity 295 / ShrineHistory 229
  ShrineDeityCollective 6 / ShrineSourceFact 34
  Shrine.goriyaku_tags links 0 / ShrineGoriyakuAssignment 0 / GoriyakuTag 0
  target（赤城社 / 四日町2534番地）: goriyaku "" / tags [] / histories 0 / deities 0 / collectives 0 / source_facts 0
  existing Sources matching S2 / S3 normalized URL = 0 / 0
```

### 6.1 Exact identity

```text
resolve_shrine("赤城社", "新潟県十日町市四日町2534番地")   = OK, pk == target row
resolve_shrine("赤城社", "新潟県十日町市上組2059番地子")   = NOT_FOUND
resolve_shrine("赤城社", "新潟県十日町市伊達乙48番地")     = NOT_FOUND
resolve_shrine("赤城社", "新潟県南魚沼市芹田79番地")       = NOT_FOUND
```

### 6.2 Importer output（exact）

```text
$ import_shrine_knowledge nsrc_000007_seed.json --validate-only
validate-only: OK, no errors                                                    exit=0

$ import_shrine_knowledge nsrc_000007_seed.json --dry-run
[source] CREATE [TOKAMACHI_REKIBUN_SHIRYOU] government: 歴史文化基本構想 資料集
[source] CREATE [TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN] museum_or_archive: 越後縮幡
[history] CREATE 赤城社: historical_event: 安政7年正月の再建
[history] CREATE 赤城社: regional_context: 赤城社に伝わった越後縮幡
plan summary: {'source_CREATE': 2, 'history_CREATE': 2}
dry-run: OK, no DB writes performed                                             exit=0

（table / target snapshot after validate-only + dry-run = identical to before）

$ import_shrine_knowledge nsrc_000007_seed.json            （apply #1）
（same 4 CREATE lines）
plan summary: {'source_CREATE': 2, 'history_CREATE': 2}
import complete: sources created=2, deities created=0, histories created=2, collectives created=0, memberships created=0, source_facts created=0
                                                                                exit=0

$ import_shrine_knowledge nsrc_000007_seed.json            （apply #2）
[source] REUSE_EXISTING [TOKAMACHI_REKIBUN_SHIRYOU] government: 歴史文化基本構想 資料集 matched existing id=140
[source] REUSE_EXISTING [TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN] museum_or_archive: 越後縮幡 matched existing id=141
[history] SKIP_EXISTS 赤城社: historical_event: 安政7年正月の再建 matched existing id=230
[history] SKIP_EXISTS 赤城社: regional_context: 赤城社に伝わった越後縮幡 matched existing id=231
plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}
import complete: sources created=0, deities created=0, histories created=0, collectives created=0, memberships created=0, source_facts created=0
                                                                                exit=0
```

```text
NOT_FOUND / IMPORT_IDENTITY_AMBIGUOUS        = 0 / 0
SOURCE_REUSE_CONFLICT / SOURCE_REUSE_AMBIGUOUS = 0 / 0
```

The Source reuse state is unchanged since the #3187 preflight（0 existing matches）, so first apply = 2 Source CREATE.

### 6.3 Materialized state after apply #1

```text
ShrineKnowledgeSource 139 -> 141（+2） / ShrineHistory 229 -> 231（+2）
ShrineDeity 295 -> 295 / ShrineDeityCollective 6 -> 6 / ShrineSourceFact 34 -> 34

target: histories 2 / deities 0 / collectives 0 / source_facts 0
source-less History（target）= 0

S2 related histories = [安政7年正月の再建]
S3 related histories = [赤城社に伝わった越後縮幡]
```

After apply #2: every table count and the target snapshot are identical to after apply #1.

### 6.4 Actual Evidence Gate（materialized rows + persisted relations）

| | H1 安政7年正月の再建 | H2 赤城社に伝わった越後縮幡 |
|---|---|---|
| verification_status | `source_confirmed` | `source_confirmed` |
| confidence | `high` | `high` |
| related Sources | S2 only（`government`, `source_confirmed`） | S3 only（`museum_or_archive`, `source_confirmed`） |
| related Source verification_statuses | `[source_confirmed]` | `[source_confirmed]` |
| usable | `True` | `True` |
| display_mode | `full` | `full` |
| reason_strength | `assertive` | `assertive` |
| reason | `fact_ready_with_source` | `fact_ready_with_source` |
| period_text / event_date | `安政7年正月` / `None` | `""` / `None` |

### 6.5 goriyaku invariance

```text
target Shrine.goriyaku          "" -> ""
target Shrine.goriyaku_tags     [] -> []
ShrineGoriyakuAssignment        0 -> 0
GoriyakuTag master              [] -> []
```

The pytest regression additionally compares full GoriyakuTag / Assignment tuples before and after two imports.

## 7. Tests

New: `backend/temples/tests/test_nsrc_000007_knowledge_seed.py`（16 tests）

It covers:

- Seed:
  - the seed exists exactly once;
  - parser contract（2 / 1 / 0 / 2 / 0 / 0）;
  - exact `shrine_ref`;
  - the Sources are exactly the frozen S2 / S3（and no S1）;
  - H1 / H2 have the exact frozen wording;
  - H1 -> S2 only and H2 -> S3 only;
  - the `verified_at` placeholder semantics;
  - no unauthorized Deity or derived keys.
- Identity: exact-address resolution; wrong addresses never resolve to nsrc-000007, even when the other 赤城社 rows exist.
- Importer: validate-only / dry-run PASS with no writes; apply PASS（exact counts, relations, no source-less, no Deity / Collective / SourceFact）.
- Evidence Gate: actual gate for H1 and H2 from persisted relations.
- Idempotency and invariance: second import idempotent; goriyaku state unchanged.

No existing test needed changes. The G6 H002 expectation（nsrc-000007 = `INELIGIBLE`）imports only the
nsrc-000002 / nsrc-000004 Knowledge Seeds, so it is unaffected.

```text
test_nsrc_000007_knowledge_seed.py                                   16 passed
nsrc-000007 / nsrc-000002 / nsrc-000004 seed tests + knowledge_seed_import
  + resolve_shrine exact-address + 4 Evidence Gate suites           157 passed
backend full suite（-n auto）                                        5403 passed, 12 skipped
scripts/tests                                                        685 passed
scripts/migration_safety/tests                                       320 passed
makemigrations --check                                               No changes detected
ruff check / format --check（new test）                               clean
git diff --check                                                     clean
Base Seed                                                            123 rows, file sha256 unchanged vs develop
```

## 8. Formal G4 evaluation（`shrine-expansion-gate-contract.md` §7）

| G4 condition | Evidence | Result |
|---|---|---|
| Fact owner matches G1 / G3 | exact `shrine_ref` = 赤城社 / 四日町2534番地; `resolve_shrine` OK to that row; other addresses NOT_FOUND | PASS |
| source-less Fact = 0 | materialized source-less History = 0; Deity = 0 | PASS |
| Source identity conflict = 0 | SOURCE_REUSE_CONFLICT 0 / AMBIGUOUS 0 | PASS |
| Fact / Source verification fits contract | `source_confirmed` + `verified_at` present（parse 0 errors）; date-level placeholder documented（§4） | PASS |
| ≥1 usable Deity or History under Evidence Gate | H1 usable=True, H2 usable=True（actual rows） | PASS |
| tradition not promoted to confirmed history | H1 / H2 are Source-recorded facts with the frozen history_type; no `tradition` content was upgraded | PASS |
| AI-only material not treated as confirmed Source | S2 municipal publication, S3 municipal museum | PASS |
| STOP: SOURCE_REUSE_CONFLICT / AMBIGUOUS | none | — |
| STOP: Shrine NOT_FOUND / IMPORT_IDENTITY_AMBIGUOUS | none | — |
| STOP: Source insufficient / Fact exceeds Source / Model Risk hidden | Fact text = frozen Packet wording; G3 NORMAL_MODEL_FIT; no Deity | — |
| Isolation: no Ranking / Score / identity / coordinate change | none changed | PASS |

```text
FORMAL_G4 = PASS
```

## 9. Impact boundary

```text
Knowledge Seed            + nsrc_000007_seed.json
Base Shrine Seed          NONE（123 rows, sha256 unchanged）
Candidate Master          NONE
resolve_shrine() / Knowledge importer / Evidence Gate   NONE
models / migrations       NONE
goriyaku / goriyaku_tags / ShrineGoriyakuAssignment / derived knowledge   NONE
Recommendation / Ranking / Score / Concierge / Compass  NONE
other H002 candidates     NONE
PR #3187                  not modified / not closed
Production DB             NONE（not connected）
```

## 10. Rollback

Revert the commit. This removes the seed, the test, and this audit. Nothing was written outside the
repository; the isolated DB was dropped.

## 11. Final state / STOP

```text
G4 nsrc-000007     = PASS（Formal re-entry）
G5 / G6 / G7 / G8  = NOT EXECUTED
Production write   = NONE
```

Do not execute G5. Do not update Candidate Master. Do not write Production.
