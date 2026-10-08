# W0-DB04 CORE READY Gate 実測（G8 / PRE_TRANSITION）

## Status

- Batch: `W0-DB04`
- Recorded at: `2026-10-08`
- Gate: `G8 CORE READY Closure`（`docs/knowledge/shrine-expansion-gate-contract.md` §11）
- Original membership: 5社（`wave0-019` / `020` / `021` / `022` / `025`）
- G8 execution subset: 3社（`wave0-019` / `021` / `025`）
- Excluded: `wave0-020`（G2 `HOLD_POSITION_REVIEW`）/ `wave0-022`（G3 `MODEL_REVIEW_REMAINS`）
- Candidate lifecycle（現在値）: `IMPORTED`（3社）
- `knowledge_status`（現在値）: `FACT_READY`（3社）
- CORE_READY transition: **`NOT_EXECUTED`（未承認）**

```text
W0_DB04_G8_EVIDENCE_GATE          = PASS_3_OF_3（#1〜#11。#8 は evidence 範囲の限界つき。§6.1）
W0_DB04_PRE_TRANSITION_ALIGNMENT  = PASS
W0_DB04_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
W0_DB04_PARTIAL_BATCH_DECISION    = PENDING（Mother Ship。§2.2）
W0_DB04_COMPLETION_CONTRACT       = 11/12_PASS + #12 PRE_TRANSITION_PASS / POST_TRANSITION_NOT_EXECUTED
W0_DB04_G8_DECISION               = CONDITIONAL_GO（Mother Ship review 待ち）
W0_DB04_CORE_READY                = NOT_EXECUTED
CANDIDATE_STATUS_TRANSITION       = NOT_EXECUTED
```

**本書は CORE_READY への遷移を承認しない。G8 を CLOSED とせず、POST_TRANSITION を PASS としない。**
遷移は Mother Ship review と明示承認の後に、別 PR で行う。

---

## 1. Purpose

`docs/audit/shrine-expansion-wave0-data-build-plan.md` の CORE READY Completion Contract 12条件について、
W0-DB04 execution subset 3社の Evidence と、遷移前（PRE_TRANSITION）の Candidate Master 状態を、
repo 内の永続 Audit として固定する。構成は `docs/audit/shrine-expansion-wave0-db03-core-ready-gate.md` を踏襲する。

| 区分 | 節 |
| --- | --- |
| Scope と batch 分割の根拠 | §2 |
| Upstream Gate evidence（G1〜G7） | §3 |
| Mother Ship による Production read-only evidence（G8） | §4 |
| G7 idempotency evidence | §5 |
| Completion Contract #1〜#11 | §6 |
| #12 PRE_TRANSITION / POST_TRANSITION | §7 |
| Non-target candidates | §8 |

判定の表記:

| 表記 | 意味 |
| --- | --- |
| `PASS` | repo 内の記録または提供された Production evidence で確認済み |
| `PENDING` | 判断・承認が未了（Mother Ship） |
| `NOT_EXECUTED` | 実行していない（承認前のため） |
| `NOT_RECORDED` | 実行はされたが、値が提供・記録されていない。推測で補完しない |

---

## 2. Scope と batch 分割の根拠

### 2.1 対象3社

| candidate_id | canonical identity `(name_jp, address)` | Production `id`（provenance） |
| --- | --- | ---: |
| wave0-019 | 建勲神社 / 京都府京都市北区紫野北舟岡町49 | 123 |
| wave0-021 | 大阪天満宮 / 大阪府大阪市北区天神橋2丁目1番8号 | 124 |
| wave0-025 | 大崎八幡宮 / 宮城県仙台市青葉区八幡4-6-1 | 125 |

Production `id` は `docs/audit/shrine-expansion-wave0-db04-production-import.md` §4 の post-write 観測値であり、
identity contract ではない。canonical identity は `(name_jp, address)` である。

対象は candidate_id で明示的に指定する。`build_batch = W0-DB04` だけで選ばない
（同じ batch に G7 NOT EXECUTED の wave0-020 / wave0-022 が含まれるため）。

### 2.2 3 / 5 で CORE_READY へ遷移する根拠（PENDING）

Data Build Plan は「Batch 5社すべてが Completion Contract を満たした場合のみ Candidate Master を
`CORE_READY` 相当 state へ更新する」と定め、失敗がある場合の扱いは「Mother Ship へ判断を返す」としている。

W0-DB03 では、この判断が `docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md` の
Mother Ship Decision A（Original membership = KEEP 5 / Execution subset = 4 CONTINUE）として記録されていた。

W0-DB04 の記録で確認できるのは次の範囲である。

- `docs/audit/shrine-expansion-wave0-db04-unified-gate-preflight.md`:
  「2社のHOLDは候補ごとの判定であり、他3社のG4進行を止めない」。
- `docs/audit/shrine-expansion-wave0-db04-g4-reentry.md` §7 / §8:
  execution subset 3社、wave0-020 / wave0-022 は評価しない、original membership は5社のまま。
- G5 / G6 / G7 は execution subset 3社で実行・完了している。

一方、**3 / 5 の部分 batch で `CORE_READY` へ遷移することを明示した Mother Ship decision record は、
repo 内で確認できなかった。** 上の記録は G4 以降の進行についての判断であり、本書はこれを
CORE_READY 遷移の承認として読み替えない。

```text
W0_DB04_PARTIAL_BATCH_DECISION = PENDING（Mother Ship が W0-DB03 Decision A 相当の判断を記録する必要がある）
```

---

## 3. Upstream Gate evidence（execution subset 3社）

| Gate | 結果 | 記録 |
| --- | --- | --- |
| G1 Identity | PASS | `shrine-expansion-wave0-db04-unified-gate-preflight.md` |
| G2 Position | PASS | 同上 / `shrine-expansion-wave0-db04-source-packet-freeze.md` |
| G3 Source / Model Fit | PASS（NORMAL_MODEL_FIT） | `shrine-expansion-wave0-db04-unified-gate-preflight.md` |
| G4 Knowledge / Evidence | `W0_DB04_G4 = PASS_3_OF_3` | `shrine-expansion-wave0-db04-g4-reentry.md` |
| G5 Shared Eligibility | `W0_DB04_G5 = PASS_3_OF_3` | `shrine-expansion-wave0-db04-g5-recommendation-eligibility.md` |
| G6 Runtime QA | `G6_STATUS = CLOSED / PASS` | `shrine-expansion-wave0-db04-g6-runtime-qa.md`（Closure addendum） |
| G7 Production Import | `G7_STATUS = CLOSED` / `G7_RESULT = PASS` | `shrine-expansion-wave0-db04-production-import.md`（PR #3090） |
| Candidate Master lifecycle sync | `IMPORTED` / `FACT_READY`（3社） | `backend/temples/data/shrine_expansion_candidate_master.json`（PR #3091） |

本 Audit はこれらの判定を再解釈・変更しない。

---

## 4. Production read-only evidence（G8）

Mother Ship が Production に対して read-only で確認した結果として提供された判定である。
本 PR の作成環境から Production へは接続していない。

```text
execution date / instant = NOT_RECORDED
develop used             = NOT_RECORDED
audit authored on        = develop@be2be9ee29066b09bb5d694647acbf1614f243b8
G8_TARGETS               = 3
```

### 4.1 判定の一覧

| 観点 | 判定 |
| --- | --- |
| Canonical identity | PASS 3/3 |
| Coordinates | PASS 3/3 |
| Source-backed knowledge and relations | PASS 3/3 |
| Shared recommendation eligibility | PASS 3/3 |
| Concierge candidate path | PASS 3/3 |
| Compass distance / direction / filter / stage | PASS 3/3 |
| Production GoriyakuTag canonical master | EXACT MATCH 39/39、mismatch 0 |
| Candidate Master PRE state | PASS 3/3 |

### 4.2 個別値

W0-DB03 の G8 記録にある shrine ごとの値（`exact`、position / location、Deity / History / Source 件数、
sourceless 件数、eligibility の母数、QA origin と direction）は、本 G8 では判定だけが提供された。

```text
G8_PER_SHRINE_VALUES = NOT_RECORDED（判定 PASS のみ提供）
```

参考として、G7 post-write で記録済みの値（`shrine-expansion-wave0-db04-production-import.md` §4 / §5 / §8）:

| candidate_id | exact | same_name | Deity | History | ShrineSourceFact | Channel B typed match | `goriyaku` | `goriyaku_tags` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| wave0-019 建勲神社 | 1 | 1 | 2 | 5 | 0 | 0 | `""` | `[]` |
| wave0-021 大阪天満宮 | 1 | 1 | 1 | 3 | 7 | 7 | `""` | `[]` |
| wave0-025 大崎八幡宮 | 1 | 1 | 3 | 4 | 16 | 14 | `""` | `[]` |

source-less Deity / History / ShrineSourceFact = 0（G7）。これは G7 時点の記録であり、G8 時点の再測定ではない。

---

## 5. G7 idempotency evidence

Idempotency は G7 の Evidence であり、本 G8 のために Production へ再接続・再実行していない。

```text
G7_BASE_IDEMPOTENCY            = PASS
G7_KNOWLEDGE_FILE1_IDEMPOTENCY = PASS
G7_KNOWLEDGE_FILE2_IDEMPOTENCY = PASS
G7_GORIYAKU_ASSIGNMENT_DELTA   = 0
```

出典: `docs/audit/shrine-expansion-wave0-db04-production-import.md` §4 / §5。
G7 の2回目 dry-run の個別出力は G7 記録で `NOT_RECORDED` であり、本書でも補完しない。
G7 の idempotency 確認中に local database へ接続した運用 incident があり、Production identity を確認し直した上で
再検証が PASS している（同 §9）。

---

## 6. Completion Contract #1〜#11（3社）

| # | 条件 | Evidence | 判定 |
| ---: | --- | --- | --- |
| 1 | Production Shrine が canonical `name_jp + address` で一意 | §4.1 canonical identity PASS 3/3。G7 で `exact = 1` / `same_name = 1` | PASS |
| 2 | 採用 `latitude / longitude` が保存されている | §4.1 coordinates PASS 3/3 | PASS |
| 3 | Source-backed `ShrineKnowledgeSource` | §4.1 PASS 3/3。G7 で Source +6（reuse なし） | PASS |
| 4 | Fact-ready Deity / History が1件以上 | §4.1 PASS 3/3。G7 で Deity 2 / 1 / 3、History 5 / 3 / 4 | PASS |
| 5 | Fact-ready Source relation / Evidence Gate `usable=True` | §4.1 PASS 3/3。G7 で source-less 0、G5 で 3社 ELIGIBLE | PASS |
| 6 | `Shrine.goriyaku` が承認済みの意味のみ | G7 で3社とも `goriyaku = ""`（承認されていない意味を保持しない） | PASS |
| 7 | `goriyaku_tags` が canonical 39 の safe subset | G7 で3社とも `goriyaku_tags = []`（空集合は canonical 39 の subset） | PASS |
| 8 | 新規 GoriyakuTag を自動生成しない | §6.1 | PASS（evidence 範囲の限界つき） |
| 9 | Concierge の shared eligibility / candidate path で読める | §4.1 shared eligibility PASS 3/3、Concierge candidate path PASS 3/3 | PASS |
| 10 | Compass distance / direction 計算が可能 | §4.1 distance / direction / filter / stage PASS 3/3 | PASS |
| 11 | Import 再実行で unexpected CREATE / UPDATE なし | §5（G7 evidence） | PASS |

```text
#1〜#11 = PASS（3 / 3）。#8 は §6.1 の限界を伴う。
```

### #6 / #7 の注記

W0-DB04 の3社は、`Shrine.goriyaku` / `goriyaku_tags` を空のまま import した（HOLD_MODEL_BOUNDARY。
`docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md`）。#6 / #7 の PASS は
「承認されていない意味・tag を保持していない」ことを示すだけであり、ご利益情報が揃っていることは主張しない。

- wave0-021 / wave0-025 の Source Facts は Channel B であり、Channel A（`goriyaku` / `goriyaku_tags`）へ書き込まれていない
  （`shrine-expansion-wave0-db04-production-import.md` §4 `G7_GORIYAKU_ISOLATION = PASS`）。
- wave0-019 の公式ご神徳表記のうち、canonical tag と EXACT に一致するもの（開運）は、`goriyaku_tags` へ書き込む判断が
  未決定（F1 記録の `NOT_YET_DECIDED`）であり、本書でも書き込みを前提としない。

### 6.1 #8 の evidence と限界

確認できていること:

1. **G8 時点**: Production GoriyakuTag canonical master は 39/39 EXACT MATCH、mismatch 0（§4.1）。
2. **G7**: GoriyakuTag assignment delta = 0（`shrine-expansion-wave0-db04-production-import.md` §4）。
3. **repo の code**: `import_shrines_seed` は GoriyakuTag を検索するだけで作成しない。W0-DB04 の Base 行は
   `goriyaku_tags` key を持たないため、tag の解決自体が行われない。`import_shrine_knowledge` は GoriyakuTag を参照しない。

確認できていないこと:

- G8 時点で canonical 39 と一致することは、**G7 実行中に一時的な GoriyakuTag が作られ、その後削除されなかったか**を
  独立に証明しない。G7 記録には G7 実行前後の GoriyakuTag 総数・id 範囲が記録されていない。
- 本書はその値を推測で補完しない。

```text
#8 = PASS（現在状態 39/39 一致 + G7 assignment delta 0 + importer の code path）
#8 LIMITATION = G7 実行中の一時的な GoriyakuTag 作成がなかったことは、Production 実測では独立に証明されていない
```

---

## 7. #12 Candidate Master / Production alignment

### 7.1 本条件の役割

#12 は #1〜#11 と独立した Production Evidence を追加する条件ではない。#1〜#11 で確認された状態を、
Candidate Master の Governance state が正しく表現していることを確認する **Synchronization Gate** である
（`docs/audit/shrine-expansion-wave0-db03-core-ready-gate.md` §7 と同じ構成）。

### 7.2 PRE_TRANSITION

`origin/develop`（`be2be9ee`）の `backend/temples/data/shrine_expansion_candidate_master.json` で確認した。

| candidate_id | candidate_status | knowledge_status | build_batch | status_reason_code | identity_status | official_source_status |
| --- | --- | --- | --- | --- | --- | --- |
| wave0-019 | IMPORTED | FACT_READY | W0-DB04 | WAVE0_CORE_READY_CANDIDATE | CONFIRMED | CONFIRMED |
| wave0-021 | IMPORTED | FACT_READY | W0-DB04 | WAVE0_CORE_READY_CANDIDATE | CONFIRMED | CONFIRMED |
| wave0-025 | IMPORTED | FACT_READY | W0-DB04 | WAVE0_CORE_READY_CANDIDATE | CONFIRMED | CONFIRMED |

- Production の Base / Knowledge import 済み状態（G7）と整合する。
- Mother Ship 提供の Candidate Master PRE state: PASS 3/3（§4.1）。

```text
W0_DB04_PRE_TRANSITION_ALIGNMENT = PASS
```

### 7.3 POST_TRANSITION 条件（未実行）

遷移を承認する場合、以下をすべて満たしたときだけ PASS とする（W0-DB03 §7.3 と同じ条件を W0-DB04 に当てはめたもの）。

1. execution subset 3社だけが `candidate_status: IMPORTED -> CORE_READY` へ変更されている
2. 3社の `candidate_status` 以外の field が変更されていない
3. `knowledge_status = FACT_READY` が3社すべて保持されている
4. `build_batch = W0-DB04` が3社すべて保持されている
5. identity / official source / coordinates / duplicate_status / status_reason_code / discovery provenance が保持されている
6. wave0-020 / 022 / 023 / 024 を含む他の candidate row が変更されていない
7. `candidate_defaults` が変更されていない
8. lifecycle 件数の delta が `IMPORTED -3 / CORE_READY +3 / TOTAL ±0` で、他 status 件数は不変
9. Candidate Master / W0-DB04 tests が PASS する（W0-DB04 original membership 5社を維持）
10. #1〜#11 の Evidence が再解釈・書き換えされていない

```text
W0_DB04_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
```

**#12 判定: `PRE_TRANSITION PASS / POST_TRANSITION NOT_EXECUTED`**

---

## 8. Non-target candidates

以下は本 G8 の対象外であり、Candidate Master の行を変更しない（`origin/develop` `be2be9ee` の値）。

| candidate_id | Shrine | candidate_status | status_reason_code | build_batch | 理由 |
| --- | --- | --- | --- | --- | --- |
| wave0-020 | 水堂須佐男神社 | BUILD_READY | WAVE0_CORE_READY_CANDIDATE | W0-DB04 | G2 `HOLD_POSITION_REVIEW`。G4〜G8 NOT EXECUTED |
| wave0-022 | 毛谷黒龍神社 | BUILD_READY | WAVE0_CORE_READY_CANDIDATE | W0-DB04 | G3 `MODEL_REVIEW_REMAINS`。G4〜G8 NOT EXECUTED |
| wave0-023 | 富知六所浅間神社 | HOLD | SOURCE_HOLD | null | Batch 未割り当て |
| wave0-024 | 居多神社 | HOLD | UNKNOWN_EVIDENCE | null | Batch 未割り当て |

4行の全体は `backend/temples/tests/test_wave0_db04_shrine_seed.py` の `UNCHANGED_CANDIDATE_ROWS` で固定されている（PR #3091）。

---

## 9. Provenance / 限界

```text
PRODUCTION_RECONNECT = NONE（本 PR の作成環境から Production へ接続していない）
PRODUCTION_WRITE     = NONE
G7_RERUN             = NONE
VALUE_COMPLETION     = NONE
```

| 項目 | 記録 |
| --- | --- |
| G8 read-only 各 command の実行 UTC instant | `NOT_RECORDED` |
| G8 実行時の develop commit | `NOT_RECORDED` |
| 実行 operator | `NOT_RECORDED` |
| Production DB identifier | `NOT_RECORDED` |
| G8 の shrine ごとの個別値 | `NOT_RECORDED`（§4.2） |
| G7 実行前後の GoriyakuTag 総数・id 範囲 | `NOT_RECORDED`（§6.1） |

いずれも推測で補完しない。一次 log file は repo 内に保存していない。
Production `id`（123 / 124 / 125）は G7 post-write 時点の provenance 値であり、identity ではない。

---

## 10. Known separate issues（本書の判定には含めない）

- **Full canonical Base Seed Production apply は BLOCKED のまま。** #11 は W0-DB04 subset 3行の idempotency のみを主張する。
- **local database に誤って作られた Base 行の cleanup** は G7 の範囲外として残っている（`shrine-expansion-wave0-db04-production-import.md` §9 / §11）。
- **wave0-019 の `goriyaku_tags`（開運）** の書き込み判断は未決定のまま（§6 注記）。
- **Reason Need Coverage Gap（communication）/ Compass F2** は本 G8 の scope 外。
- **visit_style_tags** は現行 Completion Contract の条件ではなく、W0-DB04 3社について推測・補完していない。

---

## 11. 本 PR が変更していないもの

```text
Production DB                          接続なし / write なし
Candidate Master                       変更なし（CORE_READY 遷移なし）
Base Seed / Knowledge Seed / Source Fact seed  変更なし
Schema / Migration / Model             変更なし
Ranking / Score / Recommendation mapping / Source Fact registry / Evidence Gate / Eligibility  変更なし
Compass / Concierge / runtime          変更なし
goriyaku / GoriyakuTag                 変更なし
G6 / G7 の記録                          変更なし
wave0-020 / 022 / 023 / 024             変更なし
```

---

## 12. Final

```text
W0_DB04_G8_EVIDENCE_GATE          = PASS_3_OF_3（#8 は §6.1 の限界つき）
W0_DB04_PRE_TRANSITION_ALIGNMENT  = PASS
W0_DB04_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
W0_DB04_PARTIAL_BATCH_DECISION    = PENDING
W0_DB04_G8_DECISION               = CONDITIONAL_GO
W0_DB04_CORE_READY                = NOT_EXECUTED
CANDIDATE_STATUS_TRANSITION       = NOT_EXECUTED（未承認）
G8_STATUS                         = OPEN（CLOSED ではない）
```

| # | 条件 | 判定（3社） |
| ---: | --- | --- |
| 1 | Production Shrine canonical identity | PASS |
| 2 | latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History | PASS |
| 5 | Fact-ready Source relation / Evidence Gate | PASS |
| 6 | `Shrine.goriyaku` | PASS（空。承認されていない意味なし） |
| 7 | `goriyaku_tags` canonical safe subset | PASS（空集合） |
| 8 | 新規 GoriyakuTag 自動生成なし | PASS（§6.1 の限界つき） |
| 9 | Shared Recommendation Eligibility / candidate path | PASS |
| 10 | Compass distance / direction | PASS |
| 11 | Import idempotency | PASS |
| 12 | Candidate Master / Production alignment | PRE_TRANSITION PASS / POST_TRANSITION NOT_EXECUTED |

CONDITIONAL_GO の条件（Mother Ship review）:

1. 3 / 5 の部分 batch で CORE_READY へ遷移する判断を記録する（§2.2）
2. #8 の evidence 範囲の限界（§6.1）を受け入れるか、追加の確認を求めるかを決める
3. CORE_READY 遷移を明示承認する（別 PR。§7.3 の POST_TRANSITION 条件で検証する）
