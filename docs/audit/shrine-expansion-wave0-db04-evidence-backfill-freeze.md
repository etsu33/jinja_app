# W0-DB04 Source-backed Evidence Backfill Freeze

## Status

- Status: `EVIDENCE_BACKFILL_FREEZE = PASS`
- Recorded at: `2026-10-03`
- Base: `develop@80fc08c2055401f0af0bd032b01eca1bdde667b5`（PR #3072 merged）
- Scope: wave0-019 建勲神社 / wave0-021 大阪天満宮 / wave0-025 大崎八幡宮 の Deity + History 18 Facts
- Purpose: G4再実行のcanonical frozen input
- G4 Knowledge Fact + Evidence: **NOT RE-EXECUTED**
- Candidate Master / Base Seed / Knowledge Seed / Production write: `NONE`
- goriyaku_tags / taxonomy: `NONE`（本書の対象外）

本書はMother Shipが確定したEvidence Backfill結果の記録である。本実行環境はSource本文へ到達しておらず、
値を再導出・補完・正規化していない。

`docs/audit/shrine-expansion-wave0-db04-g4-evidence-preflight.md`（PR #3072）は、
本書以前の G4 実行記録（READY 0 / HOLD 18 + 3、0/3 HOLD）としてそのまま保持する。本書はそれを書き換えない。

## Governing contracts / inputs

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`
- `docs/audit/shrine-expansion-wave0-db04-source-packet-freeze.md`（PR #3071）
- `docs/audit/shrine-expansion-wave0-db04-g4-evidence-preflight.md`（PR #3072、Field gapsの出典）
- Precedent: `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md`、
  `backend/temples/data/knowledge_seeds/wave0_batch_03_seed.json`
- Code: `backend/temples/models.py`、`backend/temples/services/knowledge_seed.py`、`backend/temples/services/evidence_gate.py`

---

## Global evidence metadata

```text
Knowledge verification date   = 2026-10-03
Source.accessed_at            = 2026-10-03
Source.verified_at            = 2026-10-03T00:00:00+09:00
ShrineDeity.verified_at       = 2026-10-03T00:00:00+09:00
ShrineHistory.verified_at     = 2026-10-03T00:00:00+09:00
verification_status           = source_confirmed
confidence                    = high
```

- これらはG4 Knowledge verificationの値である。
- G2 Positionの `verified_at` を流用していない。git・PR・audit `recorded_at`・commit時刻から導出していない。
- 時刻形式（`YYYY-MM-DDT00:00:00+09:00`）はW0-DB03 repository precedent
  （`wave0_batch_03_seed.json` の `verified_at = 2026-09-25T00:00:00+09:00`）に従う。
- `source_confirmed` は `knowledge_seed._check_verification_fields` により `verified_at` を要求する。上記で充足する。
- Evidence Gate（`evidence_gate.py`）は Fact と relation先Source の双方が `source_confirmed` / `reviewed` のときusable。
  全Fact・全Sourceが `source_confirmed` である。

---

# 1. 建勲神社（wave0-019）

## Fact owner / identity

```text
fact_owner        = 建勲神社 本社
official_address  = 京都府京都市北区紫野北舟岡町49
```

## Primary Source

```text
title         = 建勲神社について
publisher     = 建勲神社
source_type   = shrine_official
url           = https://kenkun-jinja.org/history/
language      = ja
```

## Deity

| # | display_name | source_role | model_role | verification_status | confidence |
|---|---|---|---|---|---|
| D1 | 織田信長公 | 主祭神 | `primary` | `source_confirmed` | `high` |
| D2 | 織田信忠卿 | 配祀 | `enshrined` | `source_confirmed` | `high` |

## History

| # | year | history_type | fact |
|---|---|---|---|
| H1 | 1869 | `founding` | 明治天皇による神社創立の宣下 |
| H2 | 1870 | `historical_event` | 神号「建勲」の宣下 |
| H3 | 1875 | `historical_event` | 別格官幣社に列格、船岡山に社地 |
| H4 | 1880 | `historical_event` | 社殿造営、織田信忠卿を配祀 |
| H5 | 1910 | `historical_event` | 山麓から山上の現在地へ本殿以下諸舎を移建 |

## Boundary

- founding = 1869。1910は移建であり創建ではない。
- 摂末社の祭神を取り込まない。
- 織田信長の一般的な伝記をShrineHistoryとして取り込まない。

## Result

```text
Deity   = 2 / 2 EVIDENCE_READY
History = 5 / 5 EVIDENCE_READY
Total   = 7 / 7 EVIDENCE_READY
```

---

# 2. 大阪天満宮（wave0-021）

## Fact owner / identity

```text
fact_owner        = 大阪天満宮 本社
official_address  = 大阪市北区天神橋2丁目1番8号
```

## Primary Source

```text
title         = 大阪天満宮について
publisher     = 大阪天満宮
source_type   = shrine_official
url           = https://osakatemmangu.or.jp/about
language      = ja
```

## Deity

| # | display_name | model_role | verification_status | confidence |
|---|---|---|---|---|
| D1 | 菅原道真公 | `primary` | `source_confirmed` | `high` |

## History

| # | year | history_type | fact |
|---|---|---|---|
| H1 | 650 | `regional_context` | 大将軍社がこの地に祀られる |
| H2 | 901 | `historical_event` | 菅原道真公が太宰府へ向かう途中、大将軍社に参拝し旅の無事を祈願 |
| H3 | 949 | `founding` | 村上天皇の勅命により社を建立し、菅原道真公の御霊を祀る |

## Boundary

- 650は大将軍社の前史・地域文脈であり、大阪天満宮の創建ではない。
- 901は歴史的関係（historical relationship）である。
- 949が大阪天満宮の創建である。
- 大将軍社の祭神を本社の祭神へ混入させない。

## Result

```text
Deity   = 1 / 1 EVIDENCE_READY
History = 3 / 3 EVIDENCE_READY
Total   = 4 / 4 EVIDENCE_READY
```

---

# 3. 大崎八幡宮（wave0-025）

## Fact owner / identity

```text
fact_owner        = 大崎八幡宮
official_address  = 宮城県仙台市青葉区八幡4-6-1
```

## Primary Source

```text
title         = 宮城県神社庁「大崎八幡宮」
publisher     = 宮城県神社庁
source_type   = government
url           = https://miyagi-jinjacho.or.jp/jinja-search/detail.php?code=310010033
language      = ja
```

### Source type normalization

- Wave0のdiscovery / availability分類（`shrine-expansion-wave0-official-source-availability.md`）ではこのSourceを
  `jinja_authority` と記録している。
- `ShrineKnowledgeSource.SOURCE_TYPE_CHOICES`（`backend/temples/models.py`）に `jinja_authority` はない。
- 既存repository precedentは神社庁Sourceを `government` として記録している（本書作成時に確認）:
  - `backend/temples/data/knowledge_seeds/wave0_batch_02_seed.json`: 北海道神社庁「諏訪神社」→ `government`
  - `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`: 東京都神社庁「品川神社」→ `government`
- よって `government` とする。`local_history` は使わない。

## Deity

| # | display_name | model_role | verification_status | confidence |
|---|---|---|---|---|
| D1 | 応神天皇 | `primary` | `source_confirmed` | `high` |
| D2 | 仲哀天皇 | `primary` | `source_confirmed` | `high` |
| D3 | 神功皇后 | `primary` | `source_confirmed` | `high` |

## History

| # | period | history_type | fact |
|---|---|---|---|
| H1 | （単一年なし） | `regional_context` | 成島八幡系統の福島伊達時代から米沢を経て仙台へ遷る系譜 |
| H2 | （単一年なし） | `regional_context` | 大崎八幡系統が葛西大崎地方で崇敬され、中世以来水沢・田尻を経て岩出山に仮宮を設けた系譜 |
| H3 | （単一年なし） | `official_origin` | 二つの系統を集結し、仙台開府後、現在地に社殿を造営 |
| H4 | 慶長12年（1607）8月12日 | `historical_event` | 遷座祭を斎行 |

- H1 / H2: Sourceが単一の `event_date` を与えないため、作らない。
- H3: 任意の単一創建年へ平坦化しない。

## Boundary

- 古い系譜 != 現在地での創建。
- 社殿造営 != 遷座祭。
- 1607は元となる信仰・歴史の起源ではない。
- 単一の創建年を作らない。
- 大崎市岩出山の、類似名の別の神社と混同しない。
- anonymous collective = NONE

## Result

```text
Deity   = 3 / 3 EVIDENCE_READY
History = 4 / 4 EVIDENCE_READY
Total   = 7 / 7 EVIDENCE_READY
```

---

# Cross-candidate freeze

```text
Deity Facts                = 6 / 6 EVIDENCE_READY
History Facts              = 12 / 12 EVIDENCE_READY
Total                      = 18 / 18 EVIDENCE_READY

Fact ownership             = PASS
History semantic boundary  = PASS
Deity model fit            = PASS
Anonymous collective risk  = NONE
Cross-candidate conflict   = NONE_FOUND
Source type normalization  = PASS
Timestamp normalization    = PASS
```

| candidate | State |
|---|---|
| wave0-020 水堂須佐男神社 | EXCLUDED — G2 `HOLD_POSITION_REVIEW` |
| wave0-022 毛谷黒龍神社 | EXCLUDED — G3 `MODEL_REVIEW_REMAINS` |

## PR #3072 field gapsとの対応

| PR #3072 gap | 本書での状態 |
|---|---|
| Source title / exact URL | 3 Sourceとも凍結 |
| Fact / Source `verification_status` / `confidence` | `source_confirmed` / `high` で凍結 |
| Fact `verified_at` | `2026-10-03T00:00:00+09:00` で凍結 |
| `history_type`（未凍結分） | 12 History すべて凍結 |
| wave0-025 H1〜H3 の内容 | 凍結（単一年は持たない） |
| wave0-019 `official_address` | `京都府京都市北区紫野北舟岡町49` で凍結 |
| goriyaku storage | 未解決のまま（本書の対象外。§goriyaku boundary） |

---

# goriyaku boundary

goriyaku architectureは本書で解決しない。evidence typeは次のまま保持する。

| candidate | evidence type |
|---|---|
| wave0-019 | `DIRECT_OFFICIAL_GOSHINTOKU_WORDING` |
| wave0-021 | `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` |
| wave0-025 | `OFFICIAL_PRAYER_SUPPORTED` |

これらのevidence typeは:

- goriyaku_tagsではない
- KAMIMUSUBI taxonomy mappingではない
- 無関係なfieldへ書き込まない
- 本書の18 Fact readiness結果の外にある

goriyaku typed evidence storageは別のarchitecture taskである。

---

# G4 re-entry build notes（freeze判断の一部ではない）

本書はMother Ship凍結値の記録である。G4再実行時の参考として、現行importer
（`knowledge_seed.py`）とW0-DB03 seed precedentの項目のうち、本書で値が凍結されていないものを列挙する。
本書ではこれらを作成・補完しない。

| Item | 現行要件 / precedent | 本書の状態 |
|---|---|---|
| History `title` | importer必須（`title: required, must not be blank`） | 凍結値なし |
| History `content` | importer必須 | 各Historyの `fact` 文言が凍結されている。content化の文面は凍結値なし |
| History `period_text` | precedentで記録（例: `貞観元年（859）`） | 019 / 021 は西暦年のみ、025 H4 は `慶長12年（1607）8月12日` |
| Source `key` | seed内のfile-local key（precedent: `wave0-db03-<shrine>-official`） | 凍結値なし（file-local識別子） |
| Deity `canonical_name` | precedentでは `display_name` と同値 | 凍結値なし |

G4再実行で、これらを凍結Fact文言から機械的に越えて推測しない。必要に応じてMother Ship確認を経る。

---

# Final freeze status

```text
EVIDENCE_BACKFILL_FREEZE = PASS

wave0-019 = 7 / 7 EVIDENCE_READY
wave0-021 = 4 / 4 EVIDENCE_READY
wave0-025 = 7 / 7 EVIDENCE_READY

TOTAL = 18 / 18 EVIDENCE_READY
```

This means:

```text
G4 RE-ENTRY INPUT READY
```

This does NOT mean:

- G4 PASS
- FACT_READY lifecycle promotion
- G5 eligibility
- Production imported
- CORE_READY

これらは後続の実行を要する。

## Files / Data Changed

```text
Candidate Master JSON                          NONE
backend/temples/data/shrines_seed_clean.json   NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
goriyaku_tags / goriyaku taxonomy / mapping    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
wave0-020 / wave0-022                          NONE
docs/audit/shrine-expansion-wave0-db04-g4-evidence-preflight.md  NONE（履歴として保持）
```

変更は本Audit文書の新規作成のみ。
