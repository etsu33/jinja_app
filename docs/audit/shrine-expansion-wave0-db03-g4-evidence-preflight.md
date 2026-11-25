# W0-DB03 G4 Knowledge Fact + Evidence Preflight

## Status

- Status: `W0_DB03_G4_PASS_4_OF_4`
- Recorded at: `2026-09-25`
- Branch: `feature/w0-db03-g4-knowledge-evidence`
- Base: `develop@710695889d6b3df555897dd1584e9099dfd25301`
- Gate: `G4 Knowledge Fact + Evidence`（`docs/knowledge/shrine-expansion-gate-contract.md` §7）
- Frozen input: `docs/audit/shrine-expansion-wave0-db03-source-packet-freeze.md`
- Execution subset: `wave0-012 大神神社` / `wave0-013 北野天満宮` / `wave0-015 平安神宮` / `wave0-016 岡田宮`
- Excluded: `wave0-014 宮城縣護國神社`（G3 `MODEL_CHANGE_REQUIRED`、Mother Ship Decision A）
- Production access / write: `NONE`
- G5 Shared Recommendation Eligibility: `NOT EXECUTED`

本書は G4 の実測記録である。Official Fact の再調査は行っていない。
すべての値は凍結 Source Packet から取り、Packet と現行 canonical contract の矛盾は検出されなかった。

---

## 1. 変更した成果物

| 成果物 | 変更 |
| --- | --- |
| `backend/temples/data/shrine_expansion_candidate_master.json` | wave0-012 / 013 / 015 / 016 の4行のみ hydrate |
| `backend/temples/data/shrines_seed_clean.json` | 4行を末尾へ追加（113 → 117）。既存113行は無変更 |
| `backend/temples/data/knowledge_seeds/wave0_batch_03_seed.json` | 新規（Source 4 / Deity 18 / History 5） |
| `backend/temples/tests/test_wave0_db03_shrine_seed.py` | 新規（24 tests） |
| 既存テストの pin 更新 | 下記 §7 |

### Candidate Master

4行に対して以下のみを設定した。

```text
official_name / official_address / official_source_type / official_source_url
verified_at (= 2026-09-25) / latitude / longitude / goriyaku / goriyaku_tags
identity_status        = CONFIRMED   (G1 PASS + Source Packet Freeze)
official_source_status = CONFIRMED   (Source Packet Freeze)
```

維持したもの:

```text
candidate_status = BUILD_READY
build_batch      = W0-DB03
knowledge_status = 行overrideなし（既定 ACQUISITION_PATH_CONFIRMED）
discovery_sources / status_reason_code / duplicate_status = 無変更
```

`FACT_READY` / `IMPORTED` / `CORE_READY` は設定していない。`FACT_READY` は Production 実測が要件の後続 Gate である。

`wave0-014` の行は1文字も変更していない（テストで行全体を固定）。

---

## 2. Per-shrine result

| candidate_id | Shrine | Source | Deity | History | source-less | Evidence Gate usable | isolated import | idempotency | unresolved blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wave0-012 | 大神神社 | 1 | 1 | 1 | 0 | 2 / 2（Deity 1 / History 1） | PASS | PASS | なし |
| wave0-013 | 北野天満宮 | 1 | 3 | 1 | 0 | 4 / 4（Deity 3 / History 1） | PASS | PASS | なし |
| wave0-015 | 平安神宮 | 1 | 2 | 2 | 0 | 4 / 4（Deity 2 / History 2） | PASS | PASS | なし |
| wave0-016 | 岡田宮 | 1 | 12 | 1 | 0 | 13 / 13（Deity 12 / History 1） | PASS | PASS | なし |

合計: Source 4 / Deity 18 / History 5 / source-less 0 / usable 23 / 23。

### Fact-level boundary

| Shrine | 保持した境界 |
| --- | --- |
| 大神神社 | 現祭神は `大物主大神`（primary）1件のみ。創祀伝承は採用せず、年代の明示された `historical_event`（貞観元年の正一位叙位）のみ |
| 北野天満宮 | `菅原道真公`（primary）+ 相殿 `中将殿` / `吉祥女`（secondary）。摂社・末社の祭神は持ち込まない |
| 平安神宮 | `桓武天皇` / `孝明天皇` とも `role=unknown`（序列を推測しない） |
| 岡田宮 | 12柱を個別rowで保持（集合ラベルへ畳まない）。History は `history_type=tradition` 1件で、本文は「伝えられている」表現。`source_confirmed` は Source がその伝承を記載していることの確認であり、確定史実化ではない |

### Source provenance

4 Source とも `source_type=shrine_official` / `verification_status=source_confirmed` /
`confidence=high` / `accessed_at=2026-09-25`。`url` は Packet の `official_source_url` と一致する。
既存 `ShrineKnowledgeSource` との URL 衝突はない（Source identity conflict = 0）。

大神神社のみ、Packet は Deity と History の出典ページを分けて記録している
（`/jinja/` と `/jinja/goyuisho/`）。Packet の Source key 提案（1 key）に従い、
`url=https://oomiwa.or.jp/jinja/` の1 Source とした。History の出典ページ
`https://oomiwa.or.jp/jinja/goyuisho/` は同 Source の `bibliography` に記録している。

### goriyaku

Packet / normalization audit の safe subset をそのまま採用した。すべて既存 canonical 39 tag 内。

| Shrine | goriyaku_tags | 採用しなかった表記 |
| --- | --- | --- |
| 大神神社 | 家内安全 / 商売繁盛 / 交通安全 / 縁結び / 病気平癒 / 厄除け | 健康（健康長寿へ写像しない） |
| 北野天満宮 | 合格祈願 / 学業成就 / 厄除け / 開運 / 商売繁盛 / 縁結び | — |
| 平安神宮 | 厄除け / 家内安全 / 商売繁盛 / 交通安全 / 心願成就 / 安産 / 合格祈願 / 病気平癒 | 身体健康（健康長寿へ写像しない） |
| 岡田宮 | 交通安全 / 病気平癒 / 商売繁盛 / 合格祈願 | 旅行安全 / 海外旅行安全 |

---

## 3. Isolated PostgreSQL preflight

### 環境

```text
database : w0db03_preflight（本 preflight 専用に新規作成）
host     : localhost:5432（サンドボックス内 PostgreSQL 16 + PostGIS）
engine   : django.contrib.gis.db.backends.postgis
lineage  : temples/migrations（標準 GIS lineage。NoGIS ではない）
```

Production への接続・書き込みはない。`DATABASE_URL` は上記 scratch DB のみを指す。

W0-DB02 preflight はサンドボックスに GDAL / PostGIS が無く NoGIS lineage で実施したが、
本 preflight は **GIS 有効環境の標準 lineage** で実施した。

### Baseline（develop の Base Seed）

W0-DB03 追加前の状態を再現するため、`develop@7106958` の clean worktree から
`migrate` と `bootstrap_production_data` を実行した。

```text
migrate                      -> EXIT 0
bootstrap_production_data    -> EXIT 0
Shrine total 113 / GoriyakuTag 39 / Source 0 / Deity 0 / History 0
fingerprint = cc92dd08cb515b9bdd5f195148e43224320bb11a3767bb9970c70b0dfecc7e8c
existing 113 rows hash (id/name/address/lat/lng/location/goriyaku/tags/updated_at)
            = 35f0485e220ebcafd641e32c4fddbf7e72f264a8856242eea75d02f95e3069db
```

### Sequence（feature branch）

| # | Step | 結果 |
| --- | --- | --- |
| 1 | Base Seed import `--dry-run` | `CREATE ×4`（大神神社 / 北野天満宮 / 平安神宮 / 岡田宮）/ `done created=4 updated=0 skipped=113 total_seed=117`。DB fingerprint 不変 |
| 2 | Base Seed apply | `done created=4 updated=0 skipped=113` / `goriyaku_tags rows=14 updated=4 added_links=24 removed_links=0` |
| 3 | 既存113行の不変 | hash `35f0485e…` が apply 前後で完全一致（`updated_at` 含む） |
| 4 | Knowledge `--validate-only` | `validate-only: OK, no errors` |
| 5 | Knowledge `--dry-run` | `{'source_CREATE': 4, 'deity_CREATE': 18, 'history_CREATE': 5}` / DB write なし |
| 6 | Knowledge apply | `sources created=4, deities created=18, histories created=5` |
| 7 | DB 検証（40 checks） | PASS 40 / FAIL 0 |
| 8 | Evidence Gate | usable 23 / 23、4社すべて usable Deity と usable History を保持 |
| 9 | 2巡目 dry-run / re-import | 下記 §4 |
| 10 | `makemigrations --check`（GIS / NoGIS） | 両方 `No changes detected` |

### DB 検証の内訳（40 checks）

各社ごと:

- `(name_jp, address)` が exactly 1 行へ解決
- 同名別住所の行なし
- latitude / longitude が DB == Base Seed == Candidate Master == Packet
- PostGIS `location` の x / y が lng / lat と一致
- M2M goriyaku_tags == Seed goriyaku_tags
- source-less Fact 0
- usable Deity または History >= 1

全体:

- GoriyakuTag 総数 39 / max id 39（新規 tag 0）
- 宮城縣護國神社の行なし
- 参照 0 の Source なし
- Source URL 重複なし
- DB 全体の source-less Deity / History 0
- Evidence Gate usable 23 / 23

| candidate_id | Shrine id | latitude | longitude | tags |
| --- | --- | --- | --- | --- |
| wave0-012 | 114 | 34.528817 | 135.852894 | 6 |
| wave0-013 | 115 | 35.03115 | 135.735003 | 6 |
| wave0-015 | 116 | 35.0164902 | 135.7824269 | 8 |
| wave0-016 | 117 | 33.861611 | 130.767333 | 4 |

北野天満宮の Packet 表記 `35.031150` と DB 値 `35.03115` は同一の float 値である（末尾0の表記差のみ）。

### Evidence Gate

`evidence_gate.decide_fact_usability()`（Recommendation / Detail 共通の正本）へ DB 上の Fact 23 件を通した。
Evidence Gate の判定基準・閾値は変更していない。

---

## 4. Idempotency

2巡目として Base / Knowledge の dry-run と apply を再実行した。

```text
Base --dry-run : done created=0 updated=0 skipped=117 / added_links=0 removed_links=0
Base apply     : done created=0 updated=0 skipped=117 / added_links=0 removed_links=0
Knowledge --dry-run : {'source_REUSE_EXISTING': 4, 'deity_SKIP_EXISTS': 18, 'history_SKIP_EXISTS': 5}
Knowledge apply     : sources created=0, deities created=0, histories created=0
```

DB 指紋（全 Shrine の座標・location・goriyaku・M2M、GoriyakuTag、Source、Deity、History と relation）:

```text
2巡目 前 : 6f2f442b05377cbc0555594b691b187cca3c324863f0146a48eea3287955cf7b
2巡目 後 : 6f2f442b05377cbc0555594b691b187cca3c324863f0146a48eea3287955cf7b
```

完全一致。既存113行の hash も `35f0485e…` のまま不変。

---

## 5. Tests

### Focused（`temples/tests/test_wave0_db03_shrine_seed.py`）

```text
24 passed
```

以下を固定した。

- 実行 subset がちょうど4社であること（Packet / Candidate Master / Base Seed / Knowledge Seed）
- wave0-014 が Base / Knowledge に存在せず、Candidate Master の行が完全に無変更であること
- W0-DB03 original membership 5社と discovery provenance が不変であること
- canonical identity の一意性
- Candidate Master と Base Seed の identity / 座標 / goriyaku が一致すること
- Knowledge の shrine_ref が Base Seed と Candidate Master に一致すること
- source_keys がすべて解決し、参照されない Source が無く、source-less Fact が無いこと
- goriyaku_tags が Packet の safe subset と一致し、canonical 39 内に収まること
- 除外表記（健康長寿 / 身体健康 / 旅行安全 / 海外旅行安全）が混入しないこと
- `location` が latitude / longitude と完全一致すること
- 既存 Base Seed 113 行が SHA-256 で無変更であること
- Packet の Fact 境界（役割、tradition、12柱の個別保持）を保持していること
- DB 上で2回 import しても状態が変わらず、GoriyakuTag が新規作成されないこと

### Regression（CI unit job と同じ NoGIS 設定）

```text
backend full suite : 3994 passed, 12 skipped, 0 failed
makemigrations --check (NoGIS / GIS) : No changes detected
ruff check / format（変更・新規テスト） : pass
git diff --check : pass
```

`test_bootstrap_goriyaku_master_exact39_contract`（実 bootstrap による GoriyakuTag id 1..39 固定）は
4行追加後も PASS。Recommendation の tag id 対応は変化していない。

---

## 6. G4 Acceptance

| 条件 | 大神 | 北野天満宮 | 平安神宮 | 岡田宮 |
| --- | --- | --- | --- | --- |
| Fact owner が G1 / G3 と一致 | PASS | PASS | PASS | PASS |
| source-less Fact = 0 | PASS | PASS | PASS | PASS |
| Source identity conflict = 0 | PASS | PASS | PASS | PASS |
| Fact / Source verification が契約に適合 | PASS | PASS | PASS | PASS |
| Evidence Gate usable Deity / History >= 1 | PASS | PASS | PASS | PASS |
| 伝承を確定史実へ昇格させない | PASS | PASS | PASS | PASS（tradition） |
| 選択 Fact 集合が未解決 Model Risk を持ち込まない | PASS | PASS | PASS | PASS |

STOP 条件（identity ambiguity、coordinate provenance conflict、Source conflict、
unsupported Fact、unknown canonical tag、source-less Fact、
Evidence Gate が unusable のみの結果、既存 Shrine 行の予期しない更新、wave0-014 の変更）は
いずれも発生しなかった。

---

## 7. 既存テストの pin 更新

W0-DB03 の追加により値が変わる pin だけを最小更新した。判定ロジックは変えていない。

| test | 変更 |
| --- | --- |
| `test_wave0_db01_knowledge_seed.py::test_wave0_db01_shrine_refs_exist_in_base_seed` | Base Seed 行数 113 → 117 |
| `test_wave0_db02_shrine_seed.py::test_wave0_db02_base_seed_appends_five_rows_without_duplicates` | Base Seed 行数 113 → 117 |
| `test_shrine_expansion_candidate_master.py` | `W0_DB03_G4_HYDRATED_IDS`（4社）を追加。未 hydrate 検査からこの4社だけを除外し（wave0-014 は引き続き検査対象）、sub-status 検査で4社に `CONFIRMED / CONFIRMED / ACQUISITION_PATH_CONFIRMED` を要求 |

---

## 8. Not changed / Not executed

```text
Production DB                          NOT ACCESSED / NOT WRITTEN
G5 Shared Recommendation Eligibility   NOT EXECUTED
  (verify_recommendation_eligibility は実行していない)
G6 Runtime QA / G7 Production Import / G8 CORE READY   NOT EXECUTED
Ranking / Recommendation mapping / Compass logic        UNCHANGED
Evidence Gate の判定基準                                UNCHANGED
GoriyakuTag canonical master                             UNCHANGED (39)
Schema / Migration                                       UNCHANGED
wave0-014 宮城縣護國神社                                 UNCHANGED
既存 Base Seed 113 行                                    UNCHANGED
```

---

## 9. Final

```text
W0_DB03_G4_PASS_4_OF_4

G4_PASS          = wave0-012 / wave0-013 / wave0-015 / wave0-016
G4_NOT_EXECUTED  = wave0-014 (G3 MODEL_CHANGE_REQUIRED)
NEXT             = G5 Shared Recommendation Eligibility（別 PR / 別指示）
```
