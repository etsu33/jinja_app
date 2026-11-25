# NIIGATA-H001 nsrc-000002 青澤神社 G4 Knowledge materialization validation

## Status

- Recorded at: `2026-10-10`
- Candidate: `nsrc-000002`
- Shrine: 青澤神社（新潟県糸魚川市大字青海2696番地）
- Scope: Knowledge Seed の materialization と isolated PostgreSQL 上の検証だけ
- Formal G4 redecision: **`NOT EXECUTED`**（本 PR merge 後に Mother Ship が行う）

```text
G4_MATERIALIZATION_VALIDATION = PASS

BASE_SHRINE_RESOLUTION        = PASS
KNOWLEDGE_VALIDATE_ONLY       = PASS
KNOWLEDGE_DRY_RUN             = PASS
ISOLATED_POSTGRESQL_APPLY     = PASS
HISTORY_SOURCE_RELATION       = PASS
ACTUAL_EVIDENCE_GATE          = PASS
IDEMPOTENCY                   = PASS
GORIYAKU_ISOLATION            = PASS
DEITY_COUNT                   = 0
PRODUCTION_WRITE              = NONE

FORMAL_G4_REDECISION          = NOT EXECUTED
```

本書は Formal G4 を PASS と判定しない。

---

## 1. Inputs

| artifact | 内容 |
| --- | --- |
| `backend/temples/data/shrines_seed_clean.json` | Base Shrine 行（PR #3147 で追加済み。本 PR では変更していない） |
| `backend/temples/data/knowledge_seeds/nsrc_000002_seed.json` | 本 PR で追加。schema 1.0、Source 1 / Deity 0 / History 1 |

Upstream: `docs/audit/niigata-h001-nsrc-000002-g4-source-packet-freeze.md` /
`docs/audit/niigata-h001-nsrc-000002-g4-evidence-preflight.md`。

Seed の内容:

```text
Source  ITOIGAWA_AOSAWA_SPRING_FESTIVAL
        source_type = government
        url         = https://matsuri.geo-itoigawa.com/calendar/m04/
        verification_status = source_confirmed / confidence = high

History regional_context / 青沢神社の春季祭礼
        period_text = 毎年4月第3日曜日 / event_date = null
        verification_status = source_confirmed / confidence = high
        source_keys = [ITOIGAWA_AOSAWA_SPRING_FESTIVAL]

Deity   なし（[]）
```

Seed は Deity を持たない。沼河比賣命 / 沼河比売命 を含め、Source-backed でない祭神名は追加していない。
SourceFact / collective / goriyaku / goriyaku_tags も持たない。

## 2. Parser

```text
parse_seed errors = []
schema_version    = 1.0
sources           = 1
shrines           = 1
deities           = 0
histories         = 1
```

## 3. Isolated PostgreSQL 実測

すべて pytest の isolated test DB で実行した（Base Seed を `import_shrines_seed --skip-goriyaku-tags` で import した後）。

### Base Shrine resolution

```text
exact (青澤神社, 新潟県糸魚川市大字青海2696番地) = 1
resolve_shrine(...).status                     = OK
```

### validate-only

```text
validate-only: OK, no errors
ShrineKnowledgeSource / ShrineDeity / ShrineHistory writes = 0
```

### dry-run

```text
[source] CREATE [ITOIGAWA_AOSAWA_SPRING_FESTIVAL] government: 4月の地域の祭り | 新潟県糸魚川市 - 地域のまつり紹介サイト
[history] CREATE 青澤神社: regional_context: 青沢神社の春季祭礼
plan summary: {'source_CREATE': 1, 'history_CREATE': 1}
dry-run: OK, no DB writes performed
```

deity CREATE = 0。`NOT_FOUND` / `IMPORT_IDENTITY_AMBIGUOUS` / `SOURCE_REUSE_CONFLICT` /
`SOURCE_REUSE_AMBIGUOUS` は出ない。dry-run 後の Knowledge 件数は変わらない。

### apply

```text
import complete: sources created=1, deities created=0, histories created=1,
                 collectives created=0, memberships created=0, source_facts created=0
```

| 項目 | 実測 |
| --- | --- |
| target の ShrineHistory | 1 |
| target の ShrineDeity | 0 |
| History title / type | 青沢神社の春季祭礼 / regional_context |
| period_text / event_date | 毎年4月第3日曜日 / None |
| verification_status / confidence | source_confirmed / high |
| History の Source | 1件。url = `https://matsuri.geo-itoigawa.com/calendar/m04/`、source_type = government、source_confirmed |
| source-less History | 0 |
| target の ShrineSourceFact | 0 |

### Actual Evidence Gate

DB に保存された ShrineHistory と、その Source relation の verification_status から測定した。

```text
evidence_gate.decide_fact_usability(...)
= EvidenceDecision(usable=True, display_mode='full', reason_strength='assertive',
                   verification_status='source_confirmed', confidence='high',
                   reason='fact_ready_with_source')
```

### Idempotency

同じ Knowledge Seed を2回目に import した結果:

```text
[source] REUSE_EXISTING [ITOIGAWA_AOSAWA_SPRING_FESTIVAL] ... matched existing id=1
[history] SKIP_EXISTS 青澤神社: regional_context: 青沢神社の春季祭礼 matched existing id=1
plan summary: {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 1}
import complete: sources created=0, deities created=0, histories created=0,
                 collectives created=0, memberships created=0, source_facts created=0
```

Source PK / History PK / History → Source relation は1回目と同じ。History・Source の重複なし。conflict code なし。

### Goriyaku isolation

Knowledge import の前後で次は変わらない: `Shrine.goriyaku`（`""`）、`Shrine.goriyaku_tags`（空）、
GoriyakuTag master、ShrineGoriyakuAssignment。target の ShrineSourceFact は 0。

## 4. Tests

| check | 結果 |
| --- | --- |
| `test_nsrc_000002_knowledge_seed.py` | 9 passed |
| Knowledge Seed を読む test（28 file） | 521 passed |
| `scripts/tests` | 685 passed |
| backend full suite | 4933 passed, 12 skipped |
| `makemigrations --check` | No changes detected |
| ruff / black（新規 test） | PASS |
| `git diff --check` | clean |

Seed を外した状態では新規 test 9件のうち8件が失敗する（Base Shrine resolution の1件は Seed に依存しない）。

## 5. Repository isolation

```text
backend/temples/data/shrines_seed_clean.json                diff = 0
backend/temples/data/shrine_expansion_candidate_master.json diff = 0
```

nsrc-000001 / 000003 / 000004 / 000005、Recommendation / Ranking / Concierge / Compass、
model / migration / Production 設定は変更していない。

```text
PRODUCTION_WRITE = NONE
```

## 6. Next

Formal G4 redecision は Mother Ship が本 PR merge 後に行う。G5 / G6 / Production import は開始していない。
