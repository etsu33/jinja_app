# W0-DB04 G4 Knowledge Fact + Evidence Re-entry

## 1. Status

```text
FACT_EVIDENCE_RESULT  = 18 / 18 usable（Deity 6 / 6、History 12 / 12）
CANDIDATE_G4_RESULT   = PASS（wave0-019 / wave0-021 / wave0-025）
BATCH_G4_RESULT       = W0_DB04_G4_PASS_3_OF_3（execution subset。original membership 5社）
```

- `FACT_EVIDENCE_RESULT` はFact単位のEvidence Gate実測値である。
- `CANDIDATE_G4_RESULT` はGate Contract §7のPASS条件をCandidate単位で判定した結果である（§19〜§20）。
  18 / 18 usable だけを根拠にG4 PASSとはしていない。goriyaku architecture boundaryの扱いは §18〜§19 で
  Gate Contractの条文に基づき判定した。
- G5以降: **NOT EXECUTED**。Candidate lifecycle: **変更なし**（`BUILD_READY`）。Production write: **NONE**。

## 2. Execution date

- Recorded at: `2026-10-04`
- Knowledge verification date（凍結値）: `2026-10-03`

## 3. Branch

`feature/shrine-expansion-wave0-db04-g4-reentry`

## 4. Base SHA

`develop@3f117df4d8a31e695df01e6c32356c74e580912f`（PR #3073 merged）

## 5. Governing contracts

| 領域 | 正本 |
|---|---|
| Formal G4 result | `docs/knowledge/shrine-expansion-gate-contract.md` §7（G4）、§1、§13、§17、§18 |
| Fact usability | `backend/temples/services/evidence_gate.py` + `docs/knowledge/shrine-knowledge-contract.md` |
| Knowledge Fact meaning / Source | `docs/knowledge/shrine-knowledge-contract.md`（「出典必須条件」「accessed_atとverified_at」「verification_status候補」） |
| Candidate lifecycle | `docs/knowledge/shrine-expansion-candidate-master-contract.md` |
| Wave0 operational flow | `docs/audit/shrine-expansion-wave0-data-build-plan.md` |
| Precedent | `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md` |

## 6. Dependency on PR #3073 evidence freeze

- 入力: `docs/audit/shrine-expansion-wave0-db04-evidence-backfill-freeze.md`（PR #3073）、
  `docs/audit/shrine-expansion-wave0-db04-source-packet-freeze.md`（PR #3071）、
  `docs/audit/shrine-expansion-wave0-db04-unified-gate-preflight.md`（G1〜G3、PR #3070）。
- 先行G4記録 `docs/audit/shrine-expansion-wave0-db04-g4-evidence-preflight.md`（PR #3072、`HOLD 0 / 3`）は
  当時の不足（verification fields / Source URL / title / official_address 等）を記録した履歴としてそのまま保持する。
- PR #3071 / #3072 / #3073 の audit は本書で書き換えていない。
- 例外: wave0-025 H3 は Mother Ship decision により PR #3073 の値を supersede した（§17）。

## 7. Execution subset

| candidate_id | Shrine | G1 | G2 | G3 |
|---|---|---|---|---|
| wave0-019 | 建勲神社 | PASS | PASS | `NORMAL_MODEL_FIT` PASS |
| wave0-021 | 大阪天満宮 | PASS | PASS | `NORMAL_MODEL_FIT` PASS |
| wave0-025 | 大崎八幡宮 | PASS | PASS | PASS |

## 8. Excluded candidates

| candidate_id | Shrine | 理由 | 本書での扱い |
|---|---|---|---|
| wave0-020 | 水堂須佐男神社 | G2 `HOLD_POSITION_REVIEW` | 評価しない。Candidate Master / Base Seed / Knowledge Seed すべて無変更 |
| wave0-022 | 毛谷黒龍神社 | G3 `MODEL_REVIEW_REMAINS` | 評価しない。Candidate Master / Base Seed / Knowledge Seed すべて無変更 |

W0-DB04 original membershipは5社のまま。replacement / renumberingなし。

## 9. Changed artifacts（本 re-entry branch 全体）

| File | 変更 |
|---|---|
| `backend/temples/data/shrine_expansion_candidate_master.json` | wave0-019 / 021 / 025 の3行だけhydrate（identity_status / official_source_status = `CONFIRMED`、official_name / official_address / official_source_type / official_source_url / verified_at / latitude / longitude）。goriyaku / goriyaku_tags / knowledge_status は付与しない |
| `backend/temples/data/shrines_seed_clean.json` | 末尾に3行追加（117 → 120）。既存117行は不変 |
| `backend/temples/data/knowledge_seeds/wave0_batch_04_seed.json` | 新規（Source 3 / Deity 6 / History 12） |
| `backend/temples/tests/test_wave0_db04_shrine_seed.py` | 新規（29件） |
| `backend/temples/tests/test_shrine_expansion_candidate_master.py` | W0-DB04 hydrate subset の固定を追加 |
| `backend/temples/tests/test_wave0_db01_knowledge_seed.py` / `test_wave0_db02_shrine_seed.py` | Base Seed行数 117 → 120 |
| `backend/temples/tests/test_wave0_db03_shrine_seed.py` | W0-DB03 追加行の検査範囲を `[113:117]` に限定 |
| `docs/audit/shrine-expansion-wave0-db04-g4-reentry.md` | 本書 |

Mother Ship decisions used in this branch:

- official_name = candidate_name（019 / 021 / 025、G1-confirmed）。
- wave0-021 Candidate Master canonical `official_address = 大阪府大阪市北区天神橋2丁目1番8号`。
  Source表記「大阪市北区天神橋2丁目1番8号」に「大阪府」を前置する。Base Seed prefecture導出のための
  wave0-021 限定のW0-DB04決定であり、global正規化ルールではない。Source表記を含むevidence / audit記録は書き換えない。
- Base Seed goriyaku: `goriyaku = ""`（既存の空表現）/ `goriyaku_tags` key省略。理由: goriyaku typed evidence /
  taxonomy mappingが `HOLD_MODEL_BOUNDARY`。
- wave0-025 H3 semantic correction（§17）。

## 10. Base Seed result

| candidate_id | name_jp | address | latitude | longitude | goriyaku | goriyaku_tags |
|---|---|---|---|---|---|---|
| wave0-019 | 建勲神社 | 京都府京都市北区紫野北舟岡町49 | 35.0386537 | 135.7431512 | `""` | key なし |
| wave0-021 | 大阪天満宮 | 大阪府大阪市北区天神橋2丁目1番8号 | 34.6958917 | 135.5126472 | `""` | key なし |
| wave0-025 | 大崎八幡宮 | 宮城県仙台市青葉区八幡4-6-1 | 38.2725678 | 140.8449622 | `""` | key なし |

- `scripts/build_base_shrine_seed.py`: 全gate 0（DUPLICATE_IDENTITY / MISSING_REQUIRED / IDENTITY_MUTATION /
  SCHEMA_UNEXPECTED_CHANGE / PREFECTURE_UNRESOLVED / VISIT_STYLE_INVALID）。`--check` WRITTEN=0、
  SHA256 `1f81fbdcda42f95f23f6a774dde5518fae86edeb8c8fe30424149ff8bdfe70a2`。
- 既存117行: 値・key順とも不変。`rows[:113]` SHA `86acbc9a…`（W0-DB03固定値）、`rows[:117]` SHA `e55dda63…`。
- 座標はG2 frozen値と完全一致。prefecture導出: 京都府 / 大阪府 / 宮城県。

## 11. Knowledge Seed counts

```text
Source  = 3
Deity   = 6
History = 12
Fact    = 18
Collective = 0
```

`parse_seed` errors = 0。schema_version `1.0`。sort_order はW0-DB03と同じ0始まり。

## 12. Per-candidate Fact counts

| candidate_id | Shrine | Source | Deity | History | Fact |
|---|---|---:|---:|---:|---:|
| wave0-019 | 建勲神社 | 1 | 2 | 5 | 7 |
| wave0-021 | 大阪天満宮 | 1 | 1 | 3 | 4 |
| wave0-025 | 大崎八幡宮 | 1 | 3 | 4 | 7 |
| 合計 | | 3 | 6 | 12 | 18 |

## 13. Source relation result

| key | source_type | title | publisher | url |
|---|---|---|---|---|
| `wave0-db04-kenkun-official` | shrine_official | 建勲神社について | 建勲神社 | https://kenkun-jinja.org/history/ |
| `wave0-db04-osaka-tenmangu-official` | shrine_official | 大阪天満宮について | 大阪天満宮 | https://osakatemmangu.or.jp/about |
| `wave0-db04-oosaki-hachiman-authority` | government | 宮城県神社庁「大崎八幡宮」 | 宮城県神社庁 | https://miyagi-jinjacho.or.jp/jinja-search/detail.php?code=310010033 |

- title / publisher / source_type / url / language は Evidence Backfill Freeze の Primary Source と完全一致（test固定）。
- 全18 Factが自Candidateの Source key だけを1件参照する。他Candidateへのcross-reference 0。
- 3 Sourceはすべて参照されている。source-less Fact = 0（seed / isolated DB の双方）。
- Source identity conflict: 既存Knowledge Seed全件との静的照合で、同一 normalized URL / 同一 key の再利用 = 0。
  isolated import では `source_CREATE = 3`、`SOURCE_REUSE_CONFLICT / AMBIGUOUS` なし。
- Source timestamps: `accessed_at = 2026-10-03`、`verified_at = 2026-10-03T00:00:00+09:00`（Knowledge Contract
  「accessed_atとverified_at」に従い独立記録）。`verification_status = source_confirmed`、`confidence = high`。

## 14. Evidence Gate actual result

Isolated PostgreSQL（scratch DB、NoGIS migration系列、本実行環境のlocal PostgreSQL 16）で、import後のDB行に対し
`evidence_gate.decide_fact_usability` を実行した実測出力:

```text
== 建勲神社 goriyaku='' goriyaku_tags=[]
   DEITY   #0 織田信長公 role=primary                                   source_confirmed/high sources=1 -> usable=True (fact_ready_with_source)
   DEITY   #1 織田信忠卿 role=enshrined                                 source_confirmed/high sources=1 -> usable=True (fact_ready_with_source)
   HISTORY #0 founding         | 建勲神社創立の宣下           | 1869 source_confirmed/high sources=1 -> usable=True
   HISTORY #1 historical_event | 神号「建勲」の宣下           | 1870 source_confirmed/high sources=1 -> usable=True
   HISTORY #2 historical_event | 別格官幣社列格と船岡山の社地 | 1875 source_confirmed/high sources=1 -> usable=True
   HISTORY #3 historical_event | 社殿造営と織田信忠卿の配祀   | 1880 source_confirmed/high sources=1 -> usable=True
   HISTORY #4 historical_event | 現在地への移建               | 1910 source_confirmed/high sources=1 -> usable=True
== 大阪天満宮 goriyaku='' goriyaku_tags=[]
   DEITY   #0 菅原道真公 role=primary                                   source_confirmed/high sources=1 -> usable=True
   HISTORY #0 regional_context | 大将軍社の鎮座               | 650  source_confirmed/high sources=1 -> usable=True
   HISTORY #1 historical_event | 菅原道真公の大将軍社参拝     | 901  source_confirmed/high sources=1 -> usable=True
   HISTORY #2 founding         | 大阪天満宮の創建             | 949  source_confirmed/high sources=1 -> usable=True
== 大崎八幡宮 goriyaku='' goriyaku_tags=[]
   DEITY   #0 応神天皇 role=primary                                     source_confirmed/high sources=1 -> usable=True
   DEITY   #1 仲哀天皇 role=primary                                     source_confirmed/high sources=1 -> usable=True
   DEITY   #2 神功皇后 role=primary                                     source_confirmed/high sources=1 -> usable=True
   HISTORY #0 regional_context | 成島八幡系統の系譜           | ''   source_confirmed/high sources=1 -> usable=True
   HISTORY #1 regional_context | 大崎八幡系統の系譜           | ''   source_confirmed/high sources=1 -> usable=True
   HISTORY #2 historical_event | 仙台開府後の現在地造営       | ''   source_confirmed/high sources=1 -> usable=True
   HISTORY #3 historical_event | 慶長12年の遷座祭             | 慶長12年（1607）8月12日 source_confirmed/high sources=1 -> usable=True
TOTAL deity usable 6/6  history usable 12/12  facts usable 18/18
source-less Facts (whole DB) = 0
```

- 全Fact・全Sourceの `verified_at` はDB上 `2026-10-02T15:00:00+00:00`（= `2026-10-03T00:00:00+09:00`）。
- 全Factの `event_date = null`。collective = 0。

```text
FACT_EVIDENCE_RESULT = 18 / 18 usable
  wave0-019 = 7 / 7
  wave0-021 = 4 / 4
  wave0-025 = 7 / 7
```

## 15. Isolated import result

| Step | 結果 |
|---|---|
| canonical GoriyakuTag master | 39 |
| baseline（develop Base Seed 117行） | created=117 |
| branch Base Seed dry-run | created=3 updated=0 skipped=117 |
| branch Base Seed apply | created=3 updated=0 skipped=117。既存117行の fingerprint（`updated_at` を含む）前後一致 |
| Knowledge `--validate-only` | OK, no errors |
| Knowledge `--dry-run` | source_CREATE 3 / deity_CREATE 6 / history_CREATE 12 |
| Knowledge apply | sources 3 / deities 6 / histories 12 / collectives 0 / memberships 0 |
| excluded shrines（wave0-020 / 022）in DB | 0 |
| GoriyakuTag master | 39 のまま（新規tagなし、追加M2M 0） |
| `makemigrations --check --dry-run` | No changes detected |

## 16. Idempotency result

| Step | 結果 |
|---|---|
| second Base dry-run / import | created=0 updated=0 skipped=120 |
| second Knowledge dry-run | source_REUSE_EXISTING 3 / deity_SKIP_EXISTS 6 / history_SKIP_EXISTS 12 |
| second Knowledge import | created 0 / 0 / 0 |
| DB fingerprint（Source / Deity / History / Shrine、`updated_at` 含む） | 前後一致 |

## 17. wave0-025 H3 semantic supersession

Mother Ship decision（W0-DB04 G4 re-entry）により、Evidence Backfill Freeze（PR #3073）の wave0-025 H3 を
次のcanonical G4 representationで **SUPERSEDE** した。

| | history_type | title | content | period_text | event_date |
|---|---|---|---|---|---|
| PR #3073（SUPERSEDED） | `official_origin` | （凍結値なし） | 二つの系統を集結し、仙台開府後、現在地に社殿を造営 | （単一年なし） | — |
| **Current（本書）** | `historical_event` | 仙台開府後の現在地造営 | 仙台開府後、仙台の現在地で社殿を造営 | `""` | `null` |

- 系統の集結は H1 / H2（`regional_context`）が持つ。H3 へ統合しない。
- H4 が 慶長12年（1607）8月12日 の遷座祭（`historical_event`）を持つ。1607 は起源・創建ではない。
- PR #3073 の audit 本文は書き換えていない（historical record として保持）。
- test `test_histories_match_the_frozen_facts_except_the_superseded_row` は、Backfill Freeze 側が当時の値のまま
  残っていることと、Seed 側が supersede 後の値であることを同時に固定する。

Formal verification（isolated DB 実測）:

```text
wave0-025 H1 = regional_context
wave0-025 H2 = regional_context
wave0-025 H3 = historical_event
wave0-025 H4 = historical_event
official_origin count = 0
founding count        = 0
single founding year  = NONE（年代を持つのは H4 の遷座祭だけ）
```

他Candidateの境界:

- wave0-019: founding = 1869（1行のみ）。1910 は `historical_event`（移建）。摂末社祭神・一般伝記なし。
- wave0-021: 650 = `regional_context`（大将軍社前史）、901 = `historical_event`、949 = `founding`。
  1843 再建なし。大将軍社の祭神を本社へ混入させない。

## 18. goriyaku architecture state

```text
goriyaku typed evidence storage / taxonomy mapping = HOLD_MODEL_BOUNDARY（未解決のまま）
```

- Base Seed: `goriyaku = ""` / `goriyaku_tags` key なし（Mother Ship decision）。isolated DB: goriyaku_tags = []。
- Knowledge Seed: goriyaku evidence を含まない（`goriyaku` / ご利益 / ご神徳 の語なし、test固定）。
- Candidate Master: `goriyaku` / `goriyaku_tags` を付与しない。
- 凍結 goriyaku evidence（evidence type と wording）は Source Packet Freeze（PR #3071）に記録されたまま。

この状態は次のいずれも意味しない:

- goriyaku evidence が完了した
- taxonomy mapping が完了した
- 当該神社にご利益がない
- goriyaku architecture が解決した

## 19. Gate Contract interpretation（goriyaku は G4 を block するか）

### Gate Contract の条文

`docs/knowledge/shrine-expansion-gate-contract.md`:

1. §7 G4「目的」の対象は次に限定されている。goriyaku は含まれない。

   ```text
   ShrineKnowledgeSource / ShrineDeity / ShrineHistory / Fact-Source relation /
   verification_status / confidence / verified_at
   ```

2. §7「PASS条件」は次の7項目であり、goriyaku に関する条件はない。

   ```text
   - Fact ownerがG1/G3と一致
   - source-less Fact = 0
   - Source identity conflict = 0
   - Fact / Source verificationが契約に適合
   - Evidence Gateで少なくとも1件のusable DeityまたはHistoryを作れる
   - 伝承を確定史実へ昇格させない
   - AI生成のみをconfirmed Sourceとして扱わない
   ```

3. §7「STOP」（SOURCE_REUSE_CONFLICT / AMBIGUOUS、Shrine NOT_FOUND / IMPORT_IDENTITY_AMBIGUOUS、Source不十分、
   FactがSource本文を越えている、Model RiskをFact本文で隠している）にも goriyaku はない。
4. §13 HOLD / REVIEW Routing の G4 行は「G4 Evidence | usable Factなし | Evidence / Knowledge HOLD」だけである。
5. §18 Completion Contract の G4 checklist は「G4 Fact / Source relation PASS」「G4 Evidence Gate usable Fact >= 1」だけである。
6. §1 Authority Map: G4 の Fact usability authority は `evidence_gate.py` + Knowledge Contract。
   goriyaku は §8（G5: 「Legacy goriyaku / history_theme でEligibilityを代替しない」）、§9（G6 Regression Boundary）、
   §16（Data Build PR に「NEED / Goriyaku mapping変更」を原則含めない）、§19（GoriyakuTag master を変更しない）に現れる。
   いずれも G4 の PASS 条件ではない。

### 反対方向の根拠（Wave0 Data Build Plan）と、その解決

`docs/audit/shrine-expansion-wave0-data-build-plan.md` は Wave0 operational flow の authority（Gate Contract §1）であり、
goriyaku を次の工程で扱う。

| Plan の工程 | goriyaku の記述 | Unified Gate（§17 Wave0 Mapping） | W0-DB04 での状態 |
|---|---|---|---|
| Phase 1 Source Packet Freeze | approved goriyaku wording / safe canonical goriyaku_tags | G1〜G3 | goriyaku_tags は NOT FROZEN（PR #3071）。wording は evidence type 付きで凍結済み |
| Phase 2 Candidate Master Update | approved goriyaku / safe goriyaku_tags | — | Mother Ship decision により付与しない |
| Phase 3 Base Seed Build | 「必須: goriyaku / goriyaku_tags」 | — | Mother Ship decision により `""` / key省略（builder / importer の既存 optional 表現） |
| Phase 6 step 7 isolated preflight | goriyaku_tags exact set確認 | G4 | 実行済み。expected set（Mother Ship decision: tag なし）= actual set（[]）。GoriyakuTag 39 不変 |
| Post-Import CORE READY QA | approved goriyaku一致 / expected tag set完全一致 / safe tagに対応するNeedでscore path | G6 / G7 / G8 | 未実行（下流） |

- Phase 1〜3 の goriyaku 項目は Base Seed / Candidate Master の入力値であり、W0-DB04 では Mother Ship decision
  （Gate Contract §1: Product scope / editorial HOLD の authority）で代替値が確定している。G4 の PASS 条件ではない。
- G4 に対応する Phase 6 step 7 は実施し、承認済みの expected set と一致した。
- Post-Import QA の goriyaku 項目は G6〜G8 の範囲であり、本書では判定しない（§22）。

### 判定

```text
goriyaku architecture boundary = B. NON-BLOCKING for G4
```

根拠は Gate Contract §7（対象・PASS条件・STOP）、§13 G4 routing、§18 G4 checklist、§1 Authority Map である。
Gate Contract は G4 で goriyaku を要求していない。Wave0 Data Build Plan の goriyaku 項目は、Mother Ship decision で
代替値が確定した Base Seed 入力（Phase 1〜3）、実施済みで一致した G4 preflight check（Phase 6 step 7）、
下流 Gate の QA（Post-Import）のいずれかに当たり、G4 の条文と矛盾しない。

PR #3072 の `HOLD_MODEL_BOUNDARY (goriyaku)` は Fact-level classification であった。同 audit は
「HOLDの原因はModel Fitではなく、Fact / Sourceのverification fieldsとSource URLの不足である」と記録しており、
goriyaku を G4 の PASS 条件として扱ってはいない。本書はその classification を「G4 の外にある未解決 boundary」として
引き継ぐ（§18、§22）。

## 20. Per-candidate formal G4 result

| 条件（Gate Contract §7） | wave0-019 建勲神社 | wave0-021 大阪天満宮 | wave0-025 大崎八幡宮 |
|---|---|---|---|
| Fact owner が G1 / G3 と一致 | PASS（本社。摂末社祭神なし） | PASS（本社。大将軍社祭神なし） | PASS（大崎八幡宮。岩出山の別entityと混同なし） |
| source-less Fact = 0 | PASS（0） | PASS（0） | PASS（0） |
| Source identity conflict = 0 | PASS | PASS | PASS |
| Fact / Source verification 適合 | PASS | PASS | PASS |
| usable Deity または History >= 1 | PASS（7 / 7） | PASS（4 / 4） | PASS（7 / 7） |
| 伝承を確定史実へ昇格させない | PASS（伝承Factなし。1910 は移建） | PASS（650 は regional_context） | PASS（系譜は regional_context。単一創建年なし） |
| AI生成のみを confirmed Source にしない | PASS（shrine_official） | PASS（shrine_official） | PASS（government: 宮城県神社庁） |
| STOP 該当 | なし | なし | なし |
| goriyaku boundary | G4 non-blocking（§19）。未解決のまま下流へ持ち越し | 同左 | 同左 |
| **CANDIDATE_G4_RESULT** | **PASS** | **PASS** | **PASS** |

## 21. Batch-level formal G4 result

```text
W0_DB04_G4 = PASS_3_OF_3（execution subset）

wave0-019 建勲神社     = G4 PASS
wave0-021 大阪天満宮   = G4 PASS
wave0-025 大崎八幡宮   = G4 PASS
wave0-020 水堂須佐男神社 = NOT EVALUATED（G2 HOLD_POSITION_REVIEW）
wave0-022 毛谷黒龍神社   = NOT EVALUATED（G3 MODEL_REVIEW_REMAINS）
```

## 22. Downstream gate authorization / prohibition

Authorized（次タスクとして実行可能。本書では実行していない）:

- wave0-019 / 021 / 025 の G5 Shared Recommendation Eligibility 判定。

Carry-forward（下流 Gate が判定する。本書では解決していない）:

- goriyaku architecture `HOLD_MODEL_BOUNDARY`。Data Build Plan Post-Import QA の goriyaku 項目と、
  Concierge QA「safe tagに対応するNeedでscore pathが存在する」は、goriyaku_tags がない状態で G6 / G8 が判定する。
  G4 PASS はこれらの PASS を意味しない。

Prohibited（本書の範囲外）:

- G5 / G6 / G7 / G8 の実行
- `knowledge_status = FACT_READY`（Production 実測が要件。isolated / local import では付与しない）
- `candidate_status = IMPORTED` / `CORE_READY`
- Recommendation / Ranking / Concierge / Compass の変更
- goriyaku architecture の解決、goriyaku_tags / taxonomy mapping の作成
- wave0-020 / wave0-022 の変更
- PR #3071 / #3072 / #3073 audit の書き換え

Candidate Master（本書時点）: 019 / 021 / 025 は `BUILD_READY` / `WAVE0_CORE_READY_CANDIDATE` / `build_batch = W0-DB04` /
`duplicate_status = NEW` / knowledge_status 既定値 `ACQUISITION_PATH_CONFIRMED`。

## 23. Production write

```text
Production DB access = NONE
Production write     = NONE
```

## Validation

- `test_wave0_db04_shrine_seed.py`: 29 passed
- `test_shrine_expansion_candidate_master.py`: 40 passed
- `test_wave0_db03_shrine_seed.py`: 24 passed
- `test_knowledge_seed_import.py` / `test_knowledge_seed_collective_import.py`: 25 / 114 passed
- Evidence Gate 関連 test 群: 318 passed
- backend 全体（NoGIS、local PostgreSQL 16）: 4484 passed / 8 skipped / 0 failed
- `scripts/build_base_shrine_seed.py --check`: BASE_SEED_BUILD=OK（WRITTEN=0）
- `git diff --check`: pass
