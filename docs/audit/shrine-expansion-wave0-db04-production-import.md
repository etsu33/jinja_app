# W0-DB04 Production Import 実測（G7）

## Status

- Status: `CLOSED / PASS`（execution subset 3社）
- Recorded at: `2026-10-07`
- Batch: `W0-DB04`
- Gate: `G7 Production Import`（`docs/knowledge/shrine-expansion-gate-contract.md` §10）
- Execution subset: 建勲神社 / 大阪天満宮 / 大崎八幡宮（`wave0-019` / `021` / `025`）
- Out of scope（G7 NOT EXECUTED）: `wave0-020` / `022` / `023` / `024`
- Base Shrine Production Import: `PASS`（Shrine +3）
- Knowledge Production Import: `PASS`（file 1: G4 Knowledge、file 2: Source Facts）
- Base / Knowledge idempotency: `PASS`
- Production Runtime QA（G6 scenario on Production data）: `PASS`
- Full canonical Base Seed Production apply: **`BLOCKED`**（変更なし。3行 subset のみ適用）

```text
G7_SECTION_B_0120_MIGRATION    = PASS
G7_PREFLIGHT                   = PASS
G7_PRODUCTION_BACKUP_RESTORE   = PASS

G7_BASE_IMPORT                 = PASS
G7_BASE_IDEMPOTENCY            = PASS

G7_KNOWLEDGE_FILE1             = PASS
G7_KNOWLEDGE_FILE1_IDEMPOTENCY = PASS

G7_KNOWLEDGE_FILE2             = PASS
G7_KNOWLEDGE_FILE2_IDEMPOTENCY = PASS

G7_AGGREGATE_INVARIANT         = PASS
G7_BASE_IDENTITY               = PASS
G7_GORIYAKU_ISOLATION          = PASS
G7_KNOWLEDGE_INTEGRITY         = PASS
G7_SOURCE_RELATION_INTEGRITY   = PASS
G7_REGISTRY_DB_CONSISTENCY     = PASS

G6_RUNTIME_PRODUCTION_QA       = PASS
```

---

## 1. Purpose

W0-DB04 execution subset 3社の G7 Production Import と、Production data 上の Runtime QA の結果を、
repo 内の永続 Audit として固定する。構成と Provenance 規約は
`docs/audit/shrine-expansion-wave0-db03-production-import.md` を踏襲する。

Upstream Gate:

| Gate | 記録 |
| --- | --- |
| G4 | `docs/audit/shrine-expansion-wave0-db04-g4-evidence-preflight.md` / `docs/audit/shrine-expansion-wave0-db04-g4-reentry.md` |
| G5 | `docs/audit/shrine-expansion-wave0-db04-g5-recommendation-eligibility.md` |
| F1 / Policy C | `docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md` |
| Source Facts（PR-D） | `docs/audit/shrine-expansion-wave0-db04-pr-d-source-facts.md` |
| G6 | `docs/audit/shrine-expansion-wave0-db04-g6-runtime-qa.md` |

Import した artifact（repo の正本。本 PR では変更していない）:

| artifact | 内容 |
| --- | --- |
| `backend/temples/data/shrines_seed_clean.json` | Base Seed。3社の行だけを機械的に抽出した subset を `import_shrines_seed --source` へ渡した |
| `backend/temples/data/knowledge_seeds/wave0_batch_04_seed.json` | Knowledge file 1（schema 1.0。Source / Deity / History） |
| `backend/temples/data/knowledge_seeds/wave0_batch_04_source_facts_seed.json` | Knowledge file 2（schema 1.2。Source / ShrineSourceFact） |

---

## 2. Provenance / 記録の限界

**本 Audit は Current Source of Truth ではない。** Production 実測の point-in-time 記録である。

| 種別 | 正本 |
| --- | --- |
| Production の現在値 | Production 自身 |
| Candidate lifecycle の canonical 定義 | `docs/knowledge/shrine-expansion-candidate-master-contract.md` |
| Gate の定義 | `docs/knowledge/shrine-expansion-gate-contract.md` |
| 採用座標・Fact の値 | repo の Seed |
| Source Fact → canonical concept の mapping | `backend/temples/domain/source_fact_mapping_registry_v1.py` |

本 Audit に記載する値は、Mother Ship が Production に対して実行・検証した結果として提供されたものである。
本 PR の作成環境から Production へ接続・再測定はしていない。

```text
PRODUCTION_RECONNECT = NONE
PRODUCTION_WRITE     = NONE（本 PR では追加の write を行っていない）
VALUE_COMPLETION     = NONE（提供されていない値は補完していない）
CREDENTIAL_RECORDED  = NONE
```

以下は提供されておらず、**推測で補完しない**。

| 項目 | 記録 |
| --- | --- |
| Import 実行時刻（UTC instant） | `NOT_RECORDED` |
| Base / Knowledge write 承認時刻 | `NOT_RECORDED`（明示承認があったことのみ記録） |
| 実行 operator | `NOT_RECORDED` |
| Production DB identifier | `NOT_RECORDED` |
| deploy 時の application commit | `NOT_RECORDED` |
| backup identifier | `NOT_RECORDED`（backup / isolated restore が PASS したことのみ記録） |
| dry-run / apply の個別出力 | `NOT_RECORDED`（各段階が PASS したことと、下の最終値のみ記録） |

### Identity と Production id

canonical identity は `(name_jp, address)` である。本書に記載する Production `id` は post-write 時点で観測した
**provenance 値**であり、契約値ではない。**`id` を Shrine identity として扱ってはならない。**

---

## 3. Preflight / Backup

```text
G7_SECTION_B_0120_MIGRATION  = PASS（temples 0120_shrine_source_fact_foundation）
G7_PREFLIGHT                 = PASS
G7_PRODUCTION_BACKUP_RESTORE = PASS
```

Production write の前に、read-only preflight（migration / 物理 schema、target shrine・Knowledge・Source・
stable_key の collision、baseline）と、backup の取得および isolated restore の確認を行った。

---

## 4. Base Shrine Production Import

scope は canonical Base Seed から3社の行を機械的に抽出した subset のみ。Base Seed 全件の Production apply は行っていない。

```text
G7_BASE_IMPORT      = PASS
G7_BASE_IDEMPOTENCY = PASS
G7_BASE_IDENTITY    = PASS
```

| canonical identity | Production `id`（provenance） | `exact` | `same_name` | `goriyaku` | `goriyaku_tags` |
| --- | ---: | ---: | ---: | --- | --- |
| 建勲神社 / 京都府京都市北区紫野北舟岡町49 | 123 | 1 | 1 | `""` | `[]` |
| 大阪天満宮 / 大阪府大阪市北区天神橋2丁目1番8号 | 124 | 1 | 1 | `""` | `[]` |
| 大崎八幡宮 / 宮城県仙台市青葉区八幡4-6-1 | 125 | 1 | 1 | `""` | `[]` |

```text
W0_DB04_PRODUCTION_IDS       = 123, 124, 125   （provenance only）
GORIYAKU_ASSIGNMENT_DELTA    = 0
G7_GORIYAKU_ISOLATION        = PASS
```

Channel B（Source Facts）は Channel A（`Shrine.goriyaku` / `goriyaku_tags`）へ書き込まれていない。

---

## 5. Knowledge Production Import

```text
G7_KNOWLEDGE_FILE1             = PASS（wave0_batch_04_seed.json）
G7_KNOWLEDGE_FILE1_IDEMPOTENCY = PASS
G7_KNOWLEDGE_FILE2             = PASS（wave0_batch_04_source_facts_seed.json）
G7_KNOWLEDGE_FILE2_IDEMPOTENCY = PASS
G7_KNOWLEDGE_INTEGRITY         = PASS
G7_SOURCE_RELATION_INTEGRITY   = PASS
```

| Shrine | Deity | History | ShrineSourceFact |
| --- | ---: | ---: | ---: |
| 建勲神社 | 2 | 5 | 0 |
| 大阪天満宮 | 1 | 3 | 7 |
| 大崎八幡宮 | 3 | 4 | 16 |

```text
source-less Deity               = 0
source-less History             = 0
source-less ShrineSourceFact    = 0
ShrineSourceFact stable_key     = 23 / 23 unique
```

建勲神社には Source Fact を作っていない（Channel B の evidence を作り出していない）。

---

## 6. Aggregate invariant

| entity | final | delta |
| --- | ---: | ---: |
| Shrine | 120 | +3 |
| ShrineKnowledgeSource | 137 | +6 |
| ShrineDeity | 293 | +6 |
| ShrineHistory | 226 | +12 |
| ShrineSourceFact | 23 | +23 |

```text
G7_AGGREGATE_INVARIANT = PASS
```

### repo 内での cross-check

| 観点 | repo 側 | Production 実測 | 判定 |
| --- | --- | --- | --- |
| Shrine | subset 3行 | +3 | 一致 |
| Source | file 1 の Source 3 + file 2 の Source 3 | +6（既存 Source の reuse なし） | 一致 |
| Deity | 2 + 1 + 3 = 6 | +6 | 一致 |
| History | 5 + 3 + 4 = 12 | +12 | 一致 |
| ShrineSourceFact | 0 + 7 + 16 = 23 | +23 | 一致 |
| write 前の値（final − delta） | W0-DB03 G7 post-write（Shrine 117 / Source 131 / Deity 287 / History 214） | 117 / 131 / 287 / 214 | 一致 |

---

## 7. Registry consistency

```text
validate_registry_db_consistency() == ()
G7_REGISTRY_DB_CONSISTENCY = PASS
```

---

## 8. Production Runtime QA

G6 runtime の scenario を Production data 上で確認した（`docs/audit/shrine-expansion-wave0-db04-g6-runtime-qa.md`）。

| Shrine | Channel B typed match | request Need = `study` の理由文 | Channel B `rank_weighted` |
| --- | ---: | --- | ---: |
| 建勲神社 | 0 | Source-backed の claim を作らず、安全な generic fallback | 0.0 |
| 大阪天満宮 | 7 | `osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju` を選ぶ | 2.0 |
| 大崎八幡宮 | 14 | `osaki_hachimangu__prayer__gakugyo_joju` を選ぶ | 2.0 |

- 内部 provenance（`_channel_b_reason_provenance`）の `source_fact_key` は、理由文に選ばれた Source Fact と一致する。
- 公開 response には、provenance・typed carrier（`_channel_b_typed_need_matches`）・`source_fact_key` のいずれも出ない。
- 3社とも Candidate Universe に入っている。
- Channel A は不変: `score_need` = 0、`matched_need_tags` = 空、`rank_raw` = 0。

```text
G6_RUNTIME_PRODUCTION_QA = PASS
```

---

## 9. Operational incident と教訓

idempotency の確認中、1つの command が Production ではなく **local database** へ接続した。
その shell session で Production の `DATABASE_URL` が読み込まれていなかったためである。

- Production への損傷はない。
- Production の credential を読み込み直し、Production identity・ShrineSourceFact 件数・registry consistency・
  idempotency を再検証し、いずれも PASS した。
- 誤って local database に作られた Base 行の cleanup は本 Gate の範囲外である（§11）。

```text
OPERATIONAL_LESSON =
  今後、Production に対して Django management command を実行する前には、毎回 database identity を明示的に確認する。
  shell session が Production に恒久的に結び付いているとみなしてはならない。
```

---

## 10. 本 PR が変更していないもの

```text
Production DB（追加の接続・write なし）
application code / migration / Base Seed / Knowledge Seed / Source Fact seed / registry
ranking / recommendation logic / database configuration
Candidate Master（shrine_expansion_candidate_master.json）の lifecycle 値
```

Candidate Master の lifecycle 遷移（W0-DB03 では `BUILD_READY -> IMPORTED`）は data の変更であり、
本 documentation-only PR では行っていない。必要であれば別の判断・別 PR で扱う。

---

## 11. 範囲外

```text
local database に誤って作られた Base 行の cleanup
Reason Need Coverage Gap: communication
Compass F2
LLM work
Source Fact の追加・拡張
追加の Production write
wave0-020 / 022 / 023 / 024
G8 CORE READY Closure
```

---

## 12. Final

```text
G7_BLOCKERS_REMAINING    = NONE
G7_STATUS                = CLOSED
G7_RESULT                = PASS
PRODUCTION_WRITE         = PROHIBITED_AFTER_CLOSURE
W0_DB04_G8               = NOT_EXECUTED
```
