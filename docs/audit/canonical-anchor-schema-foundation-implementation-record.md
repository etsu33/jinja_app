# Canonical Shrine Anchor — Schema Foundation Implementation Record

## Status

- Status: `IMPLEMENTED (schema only)`
- Recorded at: `2026-09-24`
- Design authority: `docs/core/split-anchor-architecture.md`（PHASE_1。設計内容は変更せず、header の実装状態のみ更新）
- Base: `origin/develop` = `31cf9dd21db84c77f0ba3715915fe471f0ab50e5`（実装時）→ `c2ed75e22d768b7916a410b5524b42b839b5f3a5` を merge で取り込み（Web Worldview 系のみ。backend / migration への変更なし）
- Branch: `feature/canonical-anchor-schema-foundation`
- Canonical backfill: `NONE`
- Runtime change: `NONE`
- Production change: `NONE`

本記録は Split Anchor Architecture §13「Schema Foundation の実装境界」に従い、
神社中心座標を保存する「器」だけを追加した結果を記録する。
Canonical data adoption、Runtime cutover、Production適用は含まない。

## 1. Models added

```text
Shrine
 └── 1 : 0..1 ShrineCanonicalAnchor              (temples_shrine_canonical_anchor)
                ├── 1 : N ShrineCanonicalAnchorComponent   (temples_shrine_canonical_anchor_component)
                └── 1 : N ShrineCanonicalAnchorEvidence    (temples_shrine_canonical_anchor_evidence)
```

| file | 内容 |
| --- | --- |
| `backend/temples/models_canonical_anchor.py` | 3 model / DB制約 / cross-row validation |
| `backend/temples/domain/canonical_anchor.py` | enum値定義 / `compute_unweighted_component_mean()` |
| `backend/temples/models.py` | 上記modelのimport 1箇所のみ（`Shrine` 定義は無変更） |

### ShrineCanonicalAnchor

`shrine`（OneToOne, CASCADE, `related_name="canonical_anchor"`）/ `status` / `subject` /
`subject_type` / `point_method` / `component_set_status` / `latitude` / `longitude` /
`verified_at` / `note` / `created_at` / `updated_at`

| field | 値 |
| --- | --- |
| `status` | `CONFIRMED` / `HOLD_POSITION_REVIEW`（`NOT_ADJUDICATED` = row不在。DB値にしない） |
| `subject_type` | `SINGLE_PRINCIPAL_UNIT` / `MULTI_PRINCIPAL_UNIT` / `NON_BUILDING_RITUAL_CENTER`（nullable） |
| `point_method` | `DIRECT_POINT` / `UNWEIGHTED_COMPONENT_MEAN`（nullable） |
| `component_set_status` | `COMPLETE` / `INCOMPLETE`（nullable。単一対象・非建物対象では必須としない: §6） |

### ShrineCanonicalAnchorComponent

`anchor`（FK, CASCADE, `related_name="components"`）/ `source_attested_name` /
`classification`（`INCLUDED` / `EXCLUDED` / `UNCLASSIFIED`）/ `classification_rationale` /
`latitude` / `longitude` / `sort_order`

`source_attested_name` は入力をそのまま保存する（正規化・strip しない）。

### ShrineCanonicalAnchorEvidence

`anchor`（FK, CASCADE, `related_name="evidences"`）/ `component`（nullable FK, **RESTRICT**）/
`evidence_role`（`SEMANTIC` / `COORDINATE`）/ `source_type` / `title` / `publisher` / `url` /
`accessed_at` / `verified_at` / `extraction_method` / `evidence_strength` /
`stated_precision` / `note`

`source_type` / `extraction_method` / `evidence_strength` / `stated_precision` は
正式taxonomy未定義のため enum を持たない文字列fieldとした。
`ShrineKnowledgeSource` は流用していない。

### 意図的に追加していないもの

```text
component_count               (派生値: INCLUDED componentから導出)
canonical_navigation_delta_m  (派生値: Navigation / Canonical 座標から導出)
canonical_location PointField (§11: NOT_IN_INITIAL_SCHEMA)
Shrine への field 追加・変更
```

## 2. Migrations

| lineage | file | dependency |
| --- | --- | --- |
| standard | `backend/temples/migrations/0115_canonical_anchor_schema_foundation.py` | `0114_f6d_explicit_place_ref_backfill` |
| NoGIS | `backend/temples/migrations_nogis/0014_canonical_anchor_schema_foundation.py` | `0013_remove_legacy_temples_models` |

- 実装前に確認した leaf: standard = `0114_f6d_explicit_place_ref_backfill`、NoGIS = `0013_remove_legacy_temples_models`（どちらも単一leaf、branch / sibling なし）
- 実装後の leaf: standard = `0115_...`、NoGIS = `0014_...`（どちらも単一leaf）
- 2 fileは `dependencies` 1行以外 byte-identical（`makemigrations` をそれぞれの lineage 設定で生成）
- operation は `CreateModel` ×3 と `AddConstraint` のみ。`RunPython` / `RunSQL` / Shrine・PlaceRef への operation なし
- 既存migrationは1行も変更していない

## 3. DB constraints（CheckConstraint）

### ShrineCanonicalAnchor

| name | 内容 |
| --- | --- |
| (OneToOne unique) | 1 Shrine に最大 1 Anchor |
| `chk_canon_anchor_status` | status ∈ 2値 |
| `chk_canon_anchor_subject_type` | NULL または 3値 |
| `chk_canon_anchor_point_method` | NULL または 2値 |
| `chk_canon_anchor_component_set_status` | NULL または 2値 |
| `chk_canon_anchor_lat_lng_pair` | both NULL / both NOT NULL |
| `chk_canon_anchor_lat_range` | -90..90 |
| `chk_canon_anchor_lng_range` | -180..180 |
| `chk_canon_anchor_hold_no_coordinate` | HOLD → lat/lng NULL |
| `chk_canon_anchor_confirmed_required` | CONFIRMED → subject非空 / subject_type / point_method / lat / lng / verified_at |
| `chk_canon_anchor_confirmed_not_incomplete` | CONFIRMED かつ INCOMPLETE を禁止（§6） |
| `chk_canon_anchor_multi_mean_complete` | CONFIRMED + MULTI + MEAN → COMPLETE（NULLも拒否） |

`chk_canon_anchor_multi_mean_complete` は、実装中のテストで
`component_set_status = NULL` が SQL の3値論理によりCHECKを素通りすることを検出したため、
`component_set_status IS NOT NULL` を明示して塞いだ。

### ShrineCanonicalAnchorComponent

| name | 内容 |
| --- | --- |
| `chk_canon_component_classification` | classification ∈ 3値 |
| `chk_canon_component_name_nonempty` | source_attested_name 非空 |
| `chk_canon_component_lat_lng_pair` | both NULL / both NOT NULL |
| `chk_canon_component_lat_range` / `_lng_range` | 範囲 |
| `chk_canon_component_coord_included_only` | EXCLUDED / UNCLASSIFIED → lat/lng NULL |

### ShrineCanonicalAnchorEvidence

| name | 内容 |
| --- | --- |
| `chk_canon_evidence_role` | evidence_role ∈ {SEMANTIC, COORDINATE} |

## 4. Application validation（fail closed）

3 model とも `save()` で `full_clean()` を実行する（既存 `EvidenceLink` と同じ方式）。

| 条件 | 実装位置 |
| --- | --- |
| CONFIRMED + MULTI + MEAN: COMPLETE / INCLUDED ≥ 1 / 全INCLUDEDに座標 / Anchor座標 == 全INCLUDEDのmean | `ShrineCanonicalAnchor.clean()` |
| 確定済み MULTI + MEAN Anchor の component 追加・座標変更・再分類・削除で mean が崩れる変更を拒否 | `ShrineCanonicalAnchorComponent.save()` / `delete()` |
| 既存 component の `anchor` 付け替えを拒否 | `ShrineCanonicalAnchorComponent.clean()` |
| Evidence.component が別 Anchor の component なら拒否 | `ShrineCanonicalAnchorEvidence.clean()` |
| Evidence が紐付く component の単体削除を拒否（`RestrictedError`） | `Evidence.component` の `on_delete=RESTRICT` |
| CONFIRMED の subject が空白のみなら拒否 | `ShrineCanonicalAnchor.clean()` |

`Evidence.component` の `on_delete=RESTRICT` により、component 単体の削除で監査 Evidence が
暗黙に消えることはない。Anchor の明示削除（および Shrine 削除からの CASCADE）では、
Evidence も同じ削除集合に含まれるため Anchor / Component / Evidence を aggregate として一括削除できる。

Anchor と component の cross-row 検証は、Anchor row の `SELECT ... FOR UPDATE` で直列化する。

mean の一致判定は **完全一致**（許容誤差なし）。値は
`compute_unweighted_component_mean()` の出力をそのまま保存する前提とする。

### Deterministic mean helper

`temples.domain.canonical_anchor.compute_unweighted_component_mean(components)`

- `classification == INCLUDED` のみを使用（EXCLUDED / UNCLASSIFIED は座標があっても無視）
- INCLUDED 0件 / 座標欠損INCLUDEDあり → `CanonicalMeanError`
- `math.fsum(...) / n`（正しく丸められた和のため入力順序に依存しない。重み・距離補正なし）

### 既知の限界

`QuerySet.update()` / `bulk_create()` / raw SQL は `save()` を経由しないため、
cross-row 条件（mean一致・Evidenceのcomponent所属）は保証されない。
単一row条件は DB CheckConstraint が保証する。
本Schema FoundationではCanonical rowを書くcodeは存在しない（書込経路 = 0）。

## 5. Test results

Dedicated: `backend/temples/tests/test_canonical_anchor_schema_foundation.py`

```text
70 passed
```

指示 §25 の 1〜35 と対応（各DB制約は ValidationError と IntegrityError の両経路で確認）:

| # | test |
| --- | --- |
| 1–10 | `test_01` 〜 `test_10*`（範囲境界 / 未知enum / CONFIRMED+INCOMPLETE を追加） |
| 11–16 | `test_11` 〜 `test_16*` |
| 17–23 | `test_17` 〜 `test_23*`（確定後の component 変更拒否 / anchor 付け替え拒否を追加） |
| 24–28 | `test_24_25` 〜 `test_28` |
| RESTRICT | `test_28b`（on_delete=RESTRICT）/ `test_28c`（Evidenceありcomponent単体削除 → reject、行は残存）/ `test_28d`（Evidenceなしcomponentは削除可）/ `test_28e`（Anchor明示削除で aggregate 一括削除）/ `test_28f`（Shrine削除から aggregate 一括削除） |
| 29–33 | `test_29_to_32_applying_migration_leaves_existing_rows_untouched`（NoGIS 0014 を 0013 相当schemaへ実適用し、Shrine件数・lat/lng・location・place_ref・updated_at・PlaceRef 不変、Canonical rows 0、DML 0件）/ `test_33_migration_contains_no_data_operation` |
| 34 | `test_34_standard_and_nogis_migrations_are_logically_identical`（operation を deconstruct して比較） |
| 35 | `test_35_makemigrations_check_passes` |
| 追加 | `test_36_no_runtime_consumer_reads_canonical_anchor`（tests以外のbackend codeが Canonical を参照しない） |

Regression（local, PostgreSQL 16, CI unit job と同じ NoGIS 環境変数）:

```text
backend full suite                         : 3970 passed, 12 skipped  (RESTRICT修正 + develop同期後)
relevant migration tests                   : 134 passed
  (dedicated + shrine_knowledge_migration + migration_0108 + migration_0114
   + settings_migration_modules_nogis_scope)
makemigrations --check (NoGIS lineage)      : No changes detected
makemigrations --check (standard, PostGIS)  : No changes detected
migrate (standard, fresh PostGIS DB)        : 0001 → 0115 OK
rollback / reapply (standard)               : 0115 → 0114 → 0115 → 0114 → 0115 OK
migration parity (standard vs NoGIS)        : dependency 1行以外 byte-identical / test_34 pass
ruff check / format (new files)             : pass
git diff --check                            : pass
```

`backend/temples/models.py` の ruff 指摘（import順 / 未使用import）は develop 時点から
存在するもので、本変更では修正していない。

## 6. Required statements

```text
SCHEMA_FOUNDATION_IMPLEMENTED       = YES
MODELS_ADDED                        = ShrineCanonicalAnchor
                                      ShrineCanonicalAnchorComponent
                                      ShrineCanonicalAnchorEvidence
CANONICAL_DATA_BACKFILLED           = NO   (backfill = 0 rows)
NAVIGATION_COORDINATES_COPIED       = NO
EXISTING_SHRINE_COORDINATES_CHANGED = NO
EXISTING_PLACE_REF_CHANGED          = NO
PUBLIC_API_CHANGED                  = NO
SERIALIZER_CHANGED                  = NO
COMPASS_RUNTIME_CHANGED             = NO
MAP_RUNTIME_CHANGED                 = NO
DISTANCE_RUNTIME_CHANGED            = NO
ROUTE_RUNTIME_CHANGED               = NO
PRODUCTION_DB_CHANGED               = NO
RUNTIME_CUTOVER                     = NOT_PERFORMED
```

## 7. Not changed

- `docs/core/split-anchor-architecture.md` の設計内容（Mother Ship 指示により header の `Schema implementation` のみ `IMPLEMENTED — FOUNDATION ONLY` へ更新。`Runtime activation: NONE` / `Canonical backfill: NOT_STARTED` / `Runtime cutover: NOT_PERFORMED` は維持）
- `docs/knowledge/shrine-position-contract.md`
- `Shrine` / `PlaceRef` / `ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`
- Serializer / API / OpenAPI / Compass / distance / Map / route / Recommendation / Ranking / Concierge / Frontend / Mobile

## 8. Open points（本PRでは決めていない）

- `subject_type` × `point_method` の完全matrix（例: `CONFIRMED + UNWEIGHTED_COMPONENT_MEAN` で `subject_type != MULTI_PRINCIPAL_UNIT`）は PHASE_1 正本で未確定のため DB制約を発明していない。PHASE_2 前の Mother Ship decision へ残す。
- mean 一致判定の tolerance policy は新設しない（完全一致を維持）。
- Evidence の `source_type` 等の正式taxonomy、および Evidence の必須field要件は PHASE_2 で定義する。

## 9. STOP

```text
NEXT     = PHASE_2 Canonical adjudication batch procedure（別 Mother Ship 指示が必要）
NOT NEXT = Production / Compass cutover
```
