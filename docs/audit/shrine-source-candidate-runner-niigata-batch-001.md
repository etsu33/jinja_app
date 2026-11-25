# Shrine Source Candidate Runner — NIIGATA Batch 001 実装記録

> **Status: RUNNER_IMPLEMENTATION = COMPLETE / REAL_BATCH_EXECUTION = BLOCKED_INPUT_SNAPSHOT_REQUIRED**
>
> 正本: `docs/audit/shrine-source-candidate-extraction-contract.md`（M1〜M5 決定済み）。
> 本記録は Runner の実装と検証だけを記録する。Contract の本文・Mother Ship 決定は変更していない。

```text
PREFECTURE            = 新潟県 / NIIGATA
BATCH_ID              = NIIGATA-001
RAW_CANDIDATES        = exactly 100（M1。新潟県 Source は100件超のため Batch 001 は部分 Batch にならない）
DUPLICATE_LOOKUP      = find_duplicate_candidates(name=raw_name, address=raw_address, limit=100)
READY_HANDOFF         = max 5 / source_position 順（M4）
REVIEW_REQUIRED_OWNER = MOTHER_SHIP（M5。Runner は解決しない）
PRODUCTION_WRITE      = 0
```

## 1. 実装範囲

```text
凍結 Source snapshot（外部で取得）
  -> NIIGATA adapter（schema / entry gate の検証）
  -> Runner（既存の正規化・collision lookup・分類）
  -> JSON 監査 artifact（--output 指定時のみ書き込み）
```

Source の取得（scraping / HTTP fetch / browser 自動化 / Google Sheets）は実装していない。
`fetch_shrine_candidates.py` は使っていない。

## 2. 変更ファイル

| file | 役割 |
| --- | --- |
| `backend/temples/services/shrine_source_candidate_extraction.py` | 共通 Runner（行の分類、batch 検証、read-only guard、集計、handoff 計画、review packet、再現性比較） |
| `backend/temples/services/shrine_source_candidate_niigata.py` | NIIGATA Batch 001 の凍結 snapshot adapter と `NIIGATA_BATCH_001` contract |
| `backend/temples/management/commands/extract_shrine_source_candidates.py` | CLI（`--adapter niigata-batch-001 --input ... [--output ...] [--verify-reproducibility]`） |
| `backend/temples/tests/services/test_shrine_source_candidate_extraction.py` | contract test（T1〜T20 と adapter / command / guard / 再現性） |
| `docs/audit/shrine-source-candidate-runner-niigata-batch-001.md` | 本記録 |

変更していないもの: `find_duplicate_candidates()` / `normalize_shrine_name_for_duplicate()` /
`normalize_shrine_address_for_duplicate()`、model、migration、seed、Candidate Master、
Recommendation / Concierge / Compass、frontend / mobile。

## 3. 再利用した authority

| 用途 | 再利用したもの |
| --- | --- |
| 名称の正規化 | `shrine_duplicate_normalize.normalize_shrine_name_for_duplicate()` |
| 住所の正規化 | `shrine_duplicate_normalize.normalize_shrine_address_for_duplicate()` |
| collision lookup | `shrine_submission.find_duplicate_candidates()`（COLLISION_SIGNAL_ONLY） |
| 47都道府県名 | `temples.forms.PREF_CHOICES`（新しい一覧は作っていない） |

独自の normalizer・duplicate algorithm・identity rule（ID-01〜09 / EXACT / SOURCE_MATCH / AMBIGUOUS）は作っていない。

## 4. 凍結 snapshot の形（adapter の入力）

```json
{
  "snapshot": {
    "prefecture": "新潟県",
    "batch_id": "NIIGATA-001",
    "source_type": "prefectural_jinjacho_official",
    "source_url": "...",
    "source_verified_at": "...",
    "captured_at": "...",
    "selection_rule": "..."
  },
  "candidates": [
    {"source_position": "...", "raw_name": "...", "raw_address": "...",
     "kana": null, "phone": null, "source_id": null, "detail_url": null}
  ]
}
```

- snapshot の7項目はすべて必須の非空文字列（欠ければ `STOP_INPUT`。Source registry の entry gate §3.1）。
- candidate は `source_position` / `raw_name` / `raw_address` の key が必須。optional key は省略可。
  省略・null はどちらも「Source に無い」として None のまま保持し、補完しない。
- 想定外の key・文字列以外の値は `STOP_SOURCE_DRIFT`。
- 候補の順序は snapshot 内の並び（Source traversal 順）のまま。並べ替えない。
- `captured_at` は snapshot の凍結 metadata であり、実行時刻ではない（byte 単位で決定的にするため）。

## 5. 分類（Contract §9〜§14 の実装）

| step | 条件 | 結果 |
| --- | --- | --- |
| A | `raw_name` / `raw_address` が空・空白・null | `INVALID` / `STOP_SOURCE_REVIEW`。lookup しない |
| B | `raw_address` に新潟県以外の都道府県名（47都道府県の正式名）が明示されている | `REVIEW_REQUIRED` / `STOP_PREFECTURE_REVIEW`。住所は直さない |
| C | 既存 normalizer で `normalized_name` / `normalized_address`、`identity_candidate = normalized_name + "\|" + normalized_address` | 監査用 key。identity ではない |
| D | `find_duplicate_candidates(..., limit=100)` が1〜99件 | `REVIEW_REQUIRED` / `STOP_MOTHER_SHIP_REVIEW` |
| D | 100件 | 同上 + `possibly_truncated = true` |
| E | 候補0・必須 PASS・県整合 PASS | `READY_CANDIDATE` / `HANDOFF_NEXT_GATE` / `schema_gate_result = PASS` |

- 都道府県名の省略は不一致としない。新潟県を住所へ前置しない。
- 県不一致の行も、Mother Ship 用の Evidence として lookup を行う（分類は県不一致の review のまま）。
- `DUPLICATE` は作らない。候補が1件でも同一神社・merge・bind とはしない。

### 実装で定めた値（Contract に明記がないもの）

| 項目 | 値 |
| --- | --- |
| collision / truncation の `planned_action` | `STOP_MOTHER_SHIP_REVIEW`（Contract §14「Human/Mother Ship review まで STOP」と M5 に対応） |
| `review_reason` | list。`MISSING_RAW_NAME` / `MISSING_RAW_ADDRESS` / `PREFECTURE_MISMATCH` / `COLLISION_CANDIDATES_RETURNED` / `COLLISION_LOOKUP_POSSIBLY_TRUNCATED` |
| `schema_gate_result` | READY = `PASS`、INVALID = `FAIL`、REVIEW_REQUIRED = `NOT_EVALUATED`（§11: Schema Gate へ進むのは候補0の行だけ） |
| INVALID 行の lookup 系 field | `returned_candidate_count = null` / `possibly_truncated = null` / `identity_candidate = null`（0 と区別する） |
| handoff id | `NIIGATA-001-H001` から連番。member は `source_position` / `raw_name` / `raw_address` |
| 県不一致の判定 | 他の都道府県の正式名が住所のどこかに含まれるか（fail closed。review は人が解く） |

## 6. Batch / 停止

| 条件 | 結果 |
| --- | --- |
| snapshot の必須 metadata が空 | `STOP_INPUT` |
| 想定外の key / 型（schema drift） | `STOP_SOURCE_DRIFT` |
| `prefecture != 新潟県` | `STOP_PREFECTURE` |
| `batch_id != NIIGATA-001` / 件数が100以外 / `source_position` が空・重複 | `STOP_BATCH_CONTRACT` |
| `source_type` が違う | `STOP_INPUT` |
| 分類漏れ / 集計の不一致 | `STOP_CONTRACT` |
| SELECT 以外の SQL | `FAIL`（read-only guard） |
| 2回実行で決定的 field が違う | `STOP_REPRODUCIBILITY`（差分を詳細に出す） |

行単位の INVALID / REVIEW_REQUIRED は停止ではなく、artifact に残る（次 Gate へは送らない）。

## 7. Artifact

top-level: `runner_version` / `contract` / `prefecture` / `batch_id` / `selection_rule` / `captured_at` /
`source_type` / `source_url` / `source_verified_at` / `duplicate_lookup_limit` / `ready_handoff_max` /
`summary` / `rows` / `ready_handoffs` / `review_packets`。

- `rows`: Contract §13 の canonical output の全 field（+ `duplicate_lookup_performed`）。
- `summary`: `total_raw` / `ready_count` / `review_required_count` / `invalid_count` / `possibly_truncated_count`
  （`ready + review + invalid = total` を検証。崩れたら `STOP_CONTRACT`）。
- `ready_handoffs`: READY だけ、source_position 順、最大5件。REVIEW / INVALID は入らない。計画のみで書き込まない。
- `review_packets`: REVIEW_REQUIRED ごとに M5 の Evidence 14項目。Runner は判断しない。
- JSON は key 順固定・`ensure_ascii=False`・indent 2。file は `--output` 指定時だけ書く。

## 8. 検証

| check | 結果 |
| --- | --- |
| Runner focused tests（`test_shrine_source_candidate_extraction.py`） | 46 passed |
| 既存の duplicate tests（`test_shrine_duplicate_normalize.py` / `test_shrine_submission_duplicate_candidates.py` / `test_shrine_submission_api.py`） | 23 passed |
| backend full suite | 4869 passed, 12 skipped |
| `python manage.py makemigrations --check` | No changes detected |
| ruff / black（新規 file） | PASS |
| CLI 2回実行（架空の100行 snapshot、local DB） | 2回とも `reproducibility=PASS db_write=0`、artifact は byte 一致 |

CLI の確認に使った local DB は Shrine 0行だったため、全行 READY になった。collision（1件 / 複数 / 100件）の経路は
test DB の fixture で検証している（T5〜T7）。

### Test matrix

| test | 内容 | 結果 |
| --- | --- | --- |
| T1 / T2 | name / address 欠損 → INVALID、lookup なし | PASS |
| T3 | 別の都道府県が明示 → REVIEW_REQUIRED / STOP_PREFECTURE_REVIEW、住所は不変 | PASS |
| T4 | 候補0 → READY_CANDIDATE | PASS |
| T5 / T6 | 候補1件 / 複数 → REVIEW_REQUIRED（DUPLICATE にしない） | PASS |
| T7 | 候補100件 → REVIEW_REQUIRED + possibly_truncated | PASS |
| T8 / T9 / T10 | 同じ source_url・detail_url / source_id / identity_candidate だけでは duplicate・identity・merge にしない | PASS |
| T11 | raw 値は不変、正規化値は別 field | PASS |
| T12 | 同じ入力・同じ DB 状態で決定的（byte 一致・`diff_runs == []`） | PASS |
| T13 | Shrine 行は不変。SELECT 以外の SQL は FAIL | PASS |
| T14 | 分類の合計 = total | PASS |
| T15 | 101 / 99 / 0 行 → STOP_BATCH_CONTRACT | PASS |
| T16 | source_position の重複・空 → STOP_BATCH_CONTRACT | PASS |
| T17 / T18 / T19 | handoff は最大5件、READY のみ、source_position 順 | PASS |
| T20 | 都道府県の前置がない住所は不一致にしない | PASS |
| 追加 | adapter の drift / STOP_INPUT、県・batch_id・source_type の不一致、review packet、command、再現性の差分検出 | PASS |

## 9. DB 書き込みの証跡

- `run_extraction()` は分類の間 `read_only_guard()`（`connection.execute_wrapper`）を有効にし、
  SELECT 以外の SQL を `FAIL` として止める。test で INSERT が止まることを確認した。
- T13: 実行前後で Shrine の `(id, name_jp, address)` が一致する。
- 新規コードに ORM の `save()` / `create()` / `update()` / `delete()` / `update_or_create()` / `get_or_create()` はない
  （`row.update(...)` は artifact 用の dict の更新）。
- Production DB には接続していない。

```text
PRODUCTION_WRITE_PATH = NONE
MIGRATION             = NONE
MODEL_CHANGE          = NONE
```

## 10. 実データの snapshot

新潟県 Source の凍結 100行 snapshot は repository に存在しない（既存 Pilot の20件は Google Sheets 側の記録）。
本 PR は実在の神社の行を作っていない。test の snapshot はすべて架空の fixture である。

```text
RUNNER_IMPLEMENTATION = COMPLETE
REAL_BATCH_EXECUTION  = BLOCKED_INPUT_SNAPSHOT_REQUIRED
REPRODUCIBILITY       = PASS（fixture / 同一 DB 状態。実データでは未実行）
```

実行に必要な入力: §4 の形をした、新潟県神社庁 Source の既定表示順で最初の100件の凍結 snapshot
（`source_url` / `source_verified_at` / `captured_at` / `selection_rule` を含む）。

## 11. STOP

本 PR はここで止まる。Production import、Coordinate Audit、Batch 002、沖縄県、15県への展開は行わない。
