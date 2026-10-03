# W0-DB04 G4 Knowledge Fact + Evidence Preflight

## Status

- Status: `W0_DB04_G4_HOLD_0_OF_3_READY`
- Recorded at: `2026-10-03`
- Branch: `feature/shrine-expansion-wave0-db04-g4-knowledge-facts`
- Base: `develop@51ad210e6fde4a877be9c266e0d18281b58e36c1`（PR #3071 merged）
- Gate: `G4 Knowledge Fact + Evidence`（`docs/knowledge/shrine-expansion-gate-contract.md` §7）
- Frozen input: `docs/audit/shrine-expansion-wave0-db04-source-packet-freeze.md`
- Execution subset: `wave0-019 建勲神社` / `wave0-021 大阪天満宮` / `wave0-025 大崎八幡宮`
- Excluded: `wave0-020 水堂須佐男神社`（G2 `HOLD_POSITION_REVIEW`）/ `wave0-022 毛谷黒龍神社`（G3 `MODEL_REVIEW_REMAINS`）
- Phase 2 Deterministic Knowledge Build: **NOT EXECUTED**（READY Fact = 0）
- Production access / write: `NONE`
- G5 以降: `NOT EXECUTED`

`SOURCE_PACKET_FREEZE = PASS` を `KNOWLEDGE_FACT_READY = PASS` とみなさず、
凍結された各Factを現行Knowledge Contractと現行model / importerの要件で評価した。
Official Factの再調査・web researchは行っていない。

---

## 1. 評価に使った現行要件（repository code / contract）

| 要件 | 正本 | 内容 |
|---|---|---|
| verification fields | `backend/temples/services/knowledge_seed.py` `_check_verification_fields` | `verification_status` / `confidence` は有効値必須。`verification_status ∈ {source_confirmed, reviewed}` のとき `verified_at` 必須 |
| Fact usable | `backend/temples/services/evidence_gate.py` / `temples.models.KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES` | Fact自身とrelation先Sourceの双方が `source_confirmed` または `reviewed` のときのみusable |
| Source entry | `knowledge_seed.py` Source parser | `key` / `title` 必須。URL-backed Sourceは `source_type + normalized URL` がsemantic identity |
| Deity / History | `knowledge_seed.py` | `source_keys` は空でないlist必須（source-less Fact禁止） |
| Source要件 | `docs/knowledge/shrine-knowledge-contract.md`「出典必須条件」「accessed_atとverified_at」「verification_status候補」 | Factには `source_reference` 必須。`accessed_at` と `verified_at` は独立して記録 |
| G4 PASS | Gate Contract §7 | source-less Fact = 0、Evidence Gateで usable Deity または History >= 1 |
| W0-DB03 precedent | `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md` | Candidate Master hydrate（official_name / address / source_url / verified_at / lat / lng / goriyaku / goriyaku_tags）→ Base Seed行追加 → Knowledge Seed（Source `source_confirmed` / `high` / `accessed_at` / URL） |

## 2. 凍結Source Packetの未解決field（PR #3071 §Field gaps）

Repository evidenceおよびMother Ship凍結情報から解決できるかを確認した。

| Field | 対象 | 解決可否 | 根拠 |
|---|---|---|---|
| Knowledge Fact `verified_at` | 019 / 021 / 025 | **未解決** | Repositoryに当該Factの内容確認時刻の記録なし。G2 position `verified_at`・git時刻・audit日付・`accessed_at` は流用しない |
| Fact `verification_status` | 019 / 021 / 025 | **未解決** | Mother Ship凍結値なし。W0-DB03の `source_confirmed` は別Batchの値であり流用しない |
| Fact `confidence` | 019 / 021 / 025 | **未解決** | 同上（W0-DB03の `high` を流用しない） |
| Factごとの正確なSource URL | 019 / 021 / 025 | **未解決** | Repository内のURLは2026-09-09 availability auditの記録のみで、どのFactを支えるかが確定していない |
| Source `title` | 019 / 021 / 025 | **未解決** | importer必須。Repositoryに凍結値なし |
| `official_address` | 019 | **未解決** | Repositoryに記録なし |
| History要素1〜3の年代・本文 | 025 | **未解決** | Mother Shipは構造のみ凍結 |
| `history_type`（1869 / 949 のfounding以外） | 019 / 021 / 025 | 部分的 | Mother Shipのsemantic boundary（prehistory / regional context、historical event、relocation）は記録済み。model choiceへの割当は凍結値なし |

## 3. Fact-level classification

分類: `READY` / `HOLD_MISSING_EVIDENCE` / `HOLD_MODEL_BOUNDARY` / `NOT_APPLICABLE`

### wave0-019 建勲神社（Fact owner: 建勲神社 本社）

| # | Fact | Type | Model fit | 分類 | 不足要件 |
|---|---|---|---|---|---|
| D1 | 織田信長公（主祭神 → `primary`） | ShrineDeity | fit（`ROLE_CHOICES` に `primary`） | HOLD_MISSING_EVIDENCE | source URL / title、`verification_status`、`confidence`、`verified_at` |
| D2 | 織田信忠卿（配祀 → `enshrined`） | ShrineDeity | fit（`enshrined`） | HOLD_MISSING_EVIDENCE | 同上 |
| H1 | 1869 神社創立の宣下（founding） | ShrineHistory | fit（`founding`） | HOLD_MISSING_EVIDENCE | 同上 |
| H2 | 1870 神号「建勲」の宣下 | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | 同上 + `history_type` |
| H3 | 1875 別格官幣社列格・船岡山に社地 | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | 同上 + `history_type` |
| H4 | 1880 社殿造営・織田信忠卿配祀 | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | 同上 + `history_type` |
| H5 | 1910 現在地へ移建（relocation） | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | 同上 + `history_type` |
| G | goriyaku（DIRECT_OFFICIAL_GOSHINTOKU_WORDING、7語） | — | §4 | HOLD_MODEL_BOUNDARY | §4 |

Prerequisite: Base Shrine行がrepositoryに存在しない。`official_address` 未解決のため、W0-DB03 precedentの
Candidate Master hydrate / Base Seed追加を実施できない。

### wave0-021 大阪天満宮（Fact owner: 大阪天満宮 本社）

| # | Fact | Type | Model fit | 分類 | 不足要件 |
|---|---|---|---|---|---|
| D1 | 菅原道真公（`primary`） | ShrineDeity | fit | HOLD_MISSING_EVIDENCE | source URL / title、`verification_status`、`confidence`、`verified_at` |
| H1 | 650 大将軍社（prehistory / regional context） | ShrineHistory | type未凍結（`regional_context` 等の割当は凍結値なし） | HOLD_MISSING_EVIDENCE | 同上 + `history_type`。大阪天満宮の創建として扱わない |
| H2 | 901 菅原道真公の大将軍社参拝（historical event） | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | 同上 + `history_type` |
| H3 | 949 創建 / official origin | ShrineHistory | fit（`founding` / `official_origin` のいずれかは凍結値なし） | HOLD_MISSING_EVIDENCE | 同上 + `history_type`（2候補から選ばない） |
| G | goriyaku（OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED、7語） | — | §4 | HOLD_MODEL_BOUNDARY | §4 |

Prerequisite: Base Shrine行がrepositoryに存在しない。

### wave0-025 大崎八幡宮（Fact owner: 大崎八幡宮、宮城県仙台市青葉区八幡4-6-1）

| # | Fact | Type | Model fit | 分類 | 不足要件 |
|---|---|---|---|---|---|
| D1 | 応神天皇（`primary`） | ShrineDeity | fit | HOLD_MISSING_EVIDENCE | source URL / title、`verification_status`、`confidence`、`verified_at` |
| D2 | 仲哀天皇（`primary`） | ShrineDeity | fit | HOLD_MISSING_EVIDENCE | 同上 |
| D3 | 神功皇后（`primary`） | ShrineDeity | fit | HOLD_MISSING_EVIDENCE | 同上 |
| H1 | older origin / lineage context | ShrineHistory | 本文なし | HOLD_MISSING_EVIDENCE | 年代・本文（`content` はimporter必須）、type、verification fields、source |
| H2 | consolidation into current shrine lineage | ShrineHistory | 本文なし | HOLD_MISSING_EVIDENCE | 同上 |
| H3 | construction at current Sendai location | ShrineHistory | 本文なし | HOLD_MISSING_EVIDENCE | 同上 |
| H4 | 1607-08-12 遷座祭 | ShrineHistory | type未凍結 | HOLD_MISSING_EVIDENCE | source URL / title、verification fields、`history_type`。1607を起源として扱わない |
| G | goriyaku（OFFICIAL_PRAYER_SUPPORTED、16語） | — | §4 | HOLD_MODEL_BOUNDARY | §4 |

Prerequisite: Base Shrine行がrepositoryに存在しない。

### Counts

| candidate_id | Shrine | READY | HOLD_MISSING_EVIDENCE | HOLD_MODEL_BOUNDARY | NOT_APPLICABLE | G4 |
|---|---|---:|---:|---:|---:|---|
| wave0-019 | 建勲神社 | 0 | 7（Deity 2 / History 5） | 1（goriyaku） | 0 | **HOLD** |
| wave0-021 | 大阪天満宮 | 0 | 4（Deity 1 / History 3） | 1（goriyaku） | 0 | **HOLD** |
| wave0-025 | 大崎八幡宮 | 0 | 7（Deity 3 / History 4） | 1（goriyaku） | 0 | **HOLD** |
| 合計 | | **0** | **18** | **3** | 0 | 0 / 3 PASS |

Deity ownership・History semantic boundary・anonymous collective = NONE の凍結判断は維持している。
HOLDの原因はModel Fitではなく、Fact / Sourceのverification fieldsとSource URLの不足である。
ShrineDeityCollectiveは使わない（3社とも記名個別祭神のみ）。

## 4. goriyaku evidenceのarchitecture boundary

現行architectureでgoriyakuに関係する保存先:

| 保存先 | 性質 | Source-backed wordingの保存先として |
|---|---|---|
| `Shrine.goriyaku`（TextField） | 「ご利益（自由メモ）」 | evidence typeを保持できない。free memoへtyped evidenceを押し込まない |
| `Shrine.goriyaku_tags`（M2M `GoriyakuTag`） | Recommendation Signal / compatibility layer | KAMIMUSUBI taxonomyへのmappingであり、本タスクでは禁止 |
| `ShrineGoriyakuAssignment` | `goriyaku_taxonomy_v1` の承認済みcanonical key 18件のみ受理 | taxonomy keyへのmappingを前提とする。source wordingをそのまま保持しない |

```text
canonical storage for typed source-backed goriyaku wording (without taxonomy mapping) = NONE
```

- DIRECT_OFFICIAL_GOSHINTOKU_WORDING / OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED の区別を
  保持できる既存の保存先はない。
- 新しいstorage modelを作らない。無関係なfieldを流用しない。taxonomyを変更しない。
- goriyaku evidenceは凍結Source Packet（`shrine-expansion-wave0-db04-source-packet-freeze.md`）に記録されたままとする。

## 5. Phase 2〜3

```text
Phase 2 Deterministic Knowledge Build = NOT EXECUTED (READY Fact = 0)
```

READY Factが0件のため、W0-DB03 precedentの次の工程はいずれも実施していない。

- Candidate Master hydrate
- Base Seed（`shrines_seed_clean.json`）行追加
- `backend/temples/data/knowledge_seeds/wave0_batch_04_seed.json` 作成
- isolated PostgreSQL preflight / Evidence Gate実測 / idempotency

Data / build logicを変更していないため、新規targeted testは追加していない。
既存のCandidate Master regression testで無変更を確認した（§7）。

## 6. Re-entry requirements

各Factを `READY` にするには、Factごとに次がMother Ship凍結値として必要である。

```text
source: title / source_type / exact URL / accessed_at / verification_status / confidence / verified_at
fact:   verification_status / confidence / verified_at（source_confirmed / reviewed の場合必須）
        source_keys（上記Sourceへのrelation）
history: history_type（未凍結分）、wave0-025 H1〜H3 の年代・本文
shrine:  wave0-019 official_address（Base Shrine行の前提）
goriyaku: 保存先のarchitecture判断（taxonomy mappingを行うか、typed evidence storageを設計するか）は別タスク
```

供給後、G4を本書§3から再判定する。

## 7. Validation

- `backend/temples/tests/test_shrine_expansion_candidate_master.py` + `test_wave0_db03_shrine_seed.py`: 63 passed（local PostgreSQL、既存regression）。
- W0-DB04 5社の `candidate_status = BUILD_READY` / `build_batch = W0-DB04` は無変更。
- wave0-020 / wave0-022 は本書で評価対象外。Factを作成・変更していない。

## 8. Files / Data Changed

```text
Candidate Master JSON                          NONE
backend/temples/data/shrines_seed_clean.json   NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
goriyaku_tags / goriyaku taxonomy / mapping    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
Model Risk Resolution Record                   NONE
A-5b                                           NONE
```

変更は本Audit文書の新規作成のみ。

## Final Classification

```text
W0_DB04_G4 = HOLD (0 / 3 PASS)
READY Fact             = 0
HOLD_MISSING_EVIDENCE  = 18
HOLD_MODEL_BOUNDARY    = 3 (goriyaku storage)
CORE_READY / G5+       = NOT EXECUTED
```
