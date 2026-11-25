# Shrine Expansion G-5: Data-driven Handoff Regression

> Status: **G-5 = CLOSED**
>
> Recorded at: 2026-10-11
>
> Base: `develop@31b8f54d6125b972c7d5c9ca94e220813f6d3d41`（PR #3171 merge）
>
> Candidate Master mutation: 0
> Seed mutation: 0
> Production write: 0
> Runtime change: 0
> Gate semantics change: 0

## 1. Purpose

Candidate Master の handoff regression（H001 / H002）は handoff ごとに手書きされていた。

```text
H001: H001_* 定数 + _expected_h001_immutable/_row + _h001_violations + 専用 main test
H002: H002_* 定数 + _expected_h002_row        + _h002_violations + 専用 main test
```

`_h001_violations` と `_h002_violations` は handoff の identity 以外ほぼ同じ処理で、
H003 以降を登録するたびに同じ巨大 block を複製する構造だった。

本変更は、期待値を test 専用 manifest に移し、全 handoff を同じ generic validator と
parametrized contract で検証する構造へ変える。Candidate Master / Seed / runtime / gate semantics は変えない。

## 2. Changed files

```text
backend/temples/tests/fixtures/shrine_expansion_handoffs.json   (new, test-only)
backend/temples/tests/test_shrine_expansion_candidate_master.py
docs/audit/shrine-expansion-g5-handoff-regression-data-driven.md (this file)
```

manifest は test 専用 data であり、runtime code からは import しない
（`backend` 配下の non-test `.py` から `shrine_expansion_handoffs` への参照は 0）。

## 3. Characterization（refactor 前）

```text
Base                                   = develop@31b8f54d
worktree                               = clean
Candidate Master sha256                = a8622d233c6fa7c983307ca657cef6dba21040de56e359f623d2b9ce2f96af32
shrines_seed_clean.json sha256         = 60ed829f9b21ffb91609da41a687f624f1ba101edb9f0be8c40fc99570d3a0bb
focused (test_shrine_expansion_candidate_master.py) = 186 passed
  test_niigata_h001_contract_rejects_mutations     = 48 ids
  test_niigata_h002_contract_rejects_mutations     = 86 ids
```

H001 / H002 current state（Candidate Master `develop@31b8f54d`）:

| candidate_id | name | source_position | identity / duplicate | lifecycle |
|---|---|---|---|---|
| nsrc-000001 | 相吉神社 | page001-row001 | CONFIRMED / NEW | DISCOVERED |
| nsrc-000002 | 青澤神社 | page001-row002 | CONFIRMED / NEW | CORE_READY |
| nsrc-000003 | 蒼柴神社 | page001-row003 | CONFIRMED / NEW | DISCOVERED |
| nsrc-000004 | 青海神社 | page001-row004 | CONFIRMED / SAME_NAME_DIFFERENT_SHRINE | CORE_READY |
| nsrc-000005 | 青山稲荷神社 | page001-row005 | CONFIRMED / NEW | DISCOVERED |
| nsrc-000006 | 赤井神社 | page001-row006 | CONFIRMED / NEW | DISCOVERED |
| nsrc-000007 | 赤城社 | page001-row007 | CONFIRMED / SAME_NAME_DIFFERENT_SHRINE | DISCOVERED |
| nsrc-000008 | 赤城社 | page001-row008 | CONFIRMED / SAME_NAME_DIFFERENT_SHRINE | DISCOVERED |
| nsrc-000009 | 赤城社 | page001-row009 | CONFIRMED / SAME_NAME_DIFFERENT_SHRINE | DISCOVERED |
| nsrc-000010 | 赤城社 | page001-row010 | CONFIRMED / SAME_NAME_DIFFERENT_SHRINE | DISCOVERED |

DISCOVERED = `REGISTRY_ADMISSION_COMPLETE / AVAILABLE / UNREVIEWED / build_batch null`。
CORE_READY = `CORE_READY_CONTRACT_PASS / CONFIRMED / FACT_READY / build_batch null`。

## 4. Structure after refactor

### 4.1 Test-only manifest

`backend/temples/tests/fixtures/shrine_expansion_handoffs.json`:

```text
handoffs[]:
  handoff_id, source_batch_id, prefecture, source_snapshot_sha256,
  source_url, source_verified_at, captured_at,
  members[]:
    candidate_id, candidate_name, source_position,
    identity_status, duplicate_status,
    lifecycle { candidate_status, status_reason_code,
                official_source_status, knowledge_status, build_batch }
```

H001 の lifecycle 差（nsrc-000002 / nsrc-000004 = CORE_READY、他3件 = DISCOVERED）は member ごとに明示する。default は持たない。

### 4.2 Generic validator / contract

| 旧 | 新 |
|---|---|
| `_h001_violations` / `_h002_violations` | `_handoff_violations(master, spec)`（共通） |
| `_expected_h001_immutable` / `_expected_h001_row` / `_expected_h002_row` | `_expected_member_immutable` / `_expected_member_row`（manifest から構築） |
| `H001_*` / `H002_*` 定数、`H001_CURRENT_LIFECYCLE`、`H002_G1_STATUS` | manifest |
| `H001_LIFECYCLE_FIELDS` | `HANDOFF_LIFECYCLE_FIELDS` |
| `H002_FORBIDDEN_G0_FIELDS` | `HANDOFF_FORBIDDEN_HYDRATION_FIELDS`（同じ集合。H001 にも適用） |
| `_H001_DISCOVERED` / `_H001_CORE_READY` | `NATIONWIDE_DISCOVERED_LIFECYCLE` / `NATIONWIDE_CORE_READY_LIFECYCLE` |
| `test_niigata_h001_membership_provenance_and_current_lifecycle_are_exact` | `test_handoff_contract_is_exact[NIIGATA-001-H001]` |
| `test_niigata_h002_is_registered_exactly_at_g0` | `test_handoff_contract_is_exact[NIIGATA-001-H002]` + `test_handoffs_are_appended_after_wave0_in_manifest_order` |

`_handoff_violations` は旧 `_h001_violations` と `_h002_violations` の check の和集合である:

- candidate_id uniqueness / valid namespace（global）
- handoff membership と順序（exact）
- member id が nationwide namespace
- 行全体の exact 比較（name / prefecture / provenance 全 field / G1 / lifecycle / wave_id / candidate_reason）
- effective wave_id = null、effective lifecycle（Wave0 `candidate_defaults` の継承を key 欠落でも検出）
- Wave0 ranking provenance（`discovery_sources` / `discovery_rank`）
- forbidden hydration field（旧 H002 のみ → H001 にも適用。緩和ではなく強化）
- build_batch に Source batch / handoff を入れない

旧 main test の各 assertion は `test_handoff_contract_is_exact`（membership / 名称 / position / batch / handoff / SHA / lifecycle / build_batch / wave_id / candidate_reason / G1 / discovery_* 不在 / forbidden field 不在 / Wave0 accounting）と
`test_handoffs_are_appended_after_wave0_in_manifest_order`（Wave0 → H001 → H002 の並び）へ移した。
H002 の「赤城社4件は別 Candidate」は Candidate 固有 test（nsrc-000007〜000010）に残っている。

追加した manifest 自体の guard:

- `test_handoff_manifest_is_well_formed`: key 集合、id / source_position の一意性、enum 値、status_reason_code の整合、build_batch null。
- `test_every_registered_handoff_is_in_the_manifest`: Candidate Master に登録された handoff は全て manifest の contract を通る（manifest に無い handoff を見逃さない）。

### 4.3 Candidate-specific tests（保持）

handoff identity ではなく Candidate 固有の履歴的遷移を表すため、そのまま残した（参照する helper 名だけ変更）:

```text
test_nsrc_000004_is_core_ready_with_unchanged_evidence
test_nsrc_000002_is_core_ready_with_unchanged_evidence
test_nsrc_000006 ... 000010_g1_is_confirmed_*_and_stays_discovered
test_niigata_h002_g1_is_resolved_for_all_five_candidates
```

これらは manifest から独立した literal（名称・position・`NATIONWIDE_*_LIFECYCLE`・G1 値）で期待値を持つため、manifest の誤りに対する二重 check にもなる。

## 5. Mutation coverage mapping

### 5.1 既存 mutation（削除 0）

`test_niigata_h001_contract_rejects_mutations`（48 ids）と `test_niigata_h002_contract_rejects_mutations`（86 ids）は
**全 id をそのまま保持**し、判定だけ `_handoff_violations(master, _handoff_spec(...))` へ差し替えた。

```text
old mutation id -> new mutation id : identical (134 / 134)
deleted mutation                   : 0
```

refactor 前後で collect した test id を比較し、消えた id は旧 main test 2件だけであることを確認した（§4.2 の対応表）。

### 5.2 Generic mutation matrix（追加）

`test_handoff_contract_rejects_generic_mutations` は manifest の全 handoff に同じ category を適用する（H001 / H002 で計 146 ids）。
H003 以降は manifest に追加するだけで同じ coverage を得る。各 mutation は manifest の現在値と**異なる値**を生成し、
`mutated != master` を assert して no-op mutation を fail させる。

| Protection category | Generic（全 handoff） | 既存 handoff-specific の例（保持） |
|---|---|---|
| member removed | `member-removed` | `h002-member-removed`, `h002-akagi-deduplicated` |
| member added | `member-added` | `h002-member-added` |
| reordered member | `member-reordered` | `h002-member-reordered` |
| reused candidate_id | `reused-candidate-id`, `reused-wave0-id` | `reused-id`, `reused-wave0-id`, `h002-reused-nsrc-id` |
| invalid namespace | `unknown-namespace` | `unknown-namespace`, `h002-unknown-namespace` |
| changed source_position | `source-position-changed` | `changed-source-position`, `h002-changed-source-position` |
| changed provenance | `source-url-changed`, `verified-at-changed`, `captured-at-changed`, `provenance-track-changed`, `provenance-prefecture-changed` | `n2/n4/n6/n7/n8/n9/n10-changed-provenance` |
| changed snapshot SHA | `snapshot-sha-changed` | `changed-snapshot-sha`, `h002-changed-snapshot-sha` |
| wrong handoff_id | `wrong-handoff-id` | `h002-changed-handoff-id` |
| wrong source_batch_id | `wrong-source-batch-id` | （新規 category として追加） |
| candidate_name / prefecture | `candidate-name-changed`, `prefecture-changed` | `h002-akagi-renamed` |
| lifecycle regression / advancement | `<id>-lifecycle-changed`, `<id>-status-reason-changed`, `<id>-official-source-changed`, `<id>-knowledge-changed`（全 member） | `build-ready`, `n2-regressed-to-*`, `n4-regressed-to-imported`, `other-member-*`, `n6..n10-lifecycle-beyond-g1` |
| identity regression | `<id>-identity-changed`（全 member） | `g1-identity-regression`, `n2-identity-regression`, `n6..n10-identity-regression` |
| duplicate classification regression | `<id>-duplicate-changed`（全 member） | `same-name-classification-regression`, `n*-duplicate-*` |
| Wave0 default inheritance | `inherits-wave-id-W0`, `inherits-wave0-knowledge-default`, `inherits-wave0-identity-default`, `wave-id-W0`, `candidate-reason-changed` | `inherits-*`, `n2-inherits-wave0-official-default` |
| forbidden hydration field | `forbidden-<field>`（`HANDOFF_FORBIDDEN_HYDRATION_FIELDS` 全16 field） | `premature-hydration`, `h002-premature-*`, `n*-official-*-hydrated`, `n*-reading-hydrated`, `n*-coordinate-before-g2` |
| Wave0 ranking provenance leakage | `forbidden-discovery_sources`, `forbidden-discovery_rank`, `wave0-omairi-provenance` | `wave0-omairi-provenance`, `wave0-ranking`, `h002-wave0-discovery-*` |
| build_batch misuse | `build-batch-source`, `build-batch-handoff`, `build-batch-invented-wave0`, `build-batch-reused-wave0` | `build-batch-*`, `n2/n4-*-build-batch`, `h002-build-batch-*` |

旧 validator との整合性: generic matrix の 146 mutation は全て、develop の旧 `_h001_violations` / `_h002_violations` でも reject されることを確認した（新 matrix が旧 contract と異なる意味を持ち込んでいない）。

## 6. Frozen Ready Set cross-check

Blind spot: manifest 自体が誤っていると、data-driven test は誤った data を忠実に検証してしまう。

対策として `docs/audit/niigata-batch001-ready-set-freeze.md` を厳格に parse する。

- §3 `Frozen input identity` の `text` block から `batch_id` / `prefecture` / `captured_at` / `source_verified_at` / `snapshot_sha256` を、各1回だけ読む。
- §6 の `### <handoff_id>` heading 直後の table を読む。header `| source_position | raw_name | raw_address | ready_basis |` と separator が完全一致し、各行がちょうど4 cell、`source_position` が `pageNNN-rowNNN`、`ready_basis` が既知値であることを要求する。
- 構造が想定と異なれば `ValueError` で fail-closed する。推測で読まない。heading の重複や table 欠落も同様。

| Test | 内容 |
|---|---|
| `test_handoff_manifest_matches_frozen_ready_set[H00x]` | manifest の handoff identity（batch / prefecture / captured_at / verified_at / SHA）と member `(source_position, candidate_name)` 列が frozen と一致 |
| `test_candidate_master_provenance_matches_frozen_ready_set[H00x]` | manifest を経由せず、Candidate Master provenance の `(source_position, candidate_name)` 列が frozen と一致し、manifest の id 列がその順序に対応 |
| `test_frozen_ready_set_parser_reads_the_frozen_handoff_boundaries` | 20 handoff × 5、100 position 一意、page001-row001 〜 page010-row010 |
| `test_frozen_ready_set_cross_check_detects_manifest_drift` | manifest の並び替え / 削除 / 追加 / position / 名称 / handoff / batch / SHA / timestamp / prefecture の改変を検出（22 ids） |
| `test_frozen_ready_set_cross_check_detects_frozen_drift` | frozen 側の名称・position 改変を検出 |
| `test_frozen_ready_set_parser_fails_closed_on_structure_drift` | header 変更 / cell 数 / position 形式 / 未知 ready_basis / heading 重複 / heading 消失 / identity 欠落で `ValueError` |

実ファイルでの確認（一時変更して元に戻した）:

```text
manifest の H002 member 2件を入れ替え
  -> test_handoff_manifest_matches_frozen_ready_set[H002] FAIL
  -> test_candidate_master_provenance_matches_frozen_ready_set[H002] FAIL
  -> test_handoff_contract_is_exact[H002] ほか FAIL
frozen doc の page001-row007 名称を改変
  -> 上記2つの frozen cross-check FAIL（Candidate Master と manifest は一致したまま）
```

## 7. Verification（refactor 後）

| check | result |
|---|---|
| Candidate Master sha256 | `a8622d23…` identical |
| shrines_seed_clean.json sha256 | `60ed829f…` identical |
| H001 / H002 expected state | 旧 `_expected_h001_row` / `_expected_h002_row`（develop の test code を load）と新 `_expected_member_row` が全10 member で identical、member 順序も identical |
| focused | 372 passed（186 → 372。旧 main test 2件 → 新 contract test へ置換、他は追加） |
| Candidate Master consumers（CM / DB02 / DB03 / DB04 tests） | 454 passed |
| scripts/tests | 685 passed |
| full backend suite | 5270 passed, 12 skipped |
| ruff check | All checks passed |
| git diff --check | clean |

`ruff format --check` はこの test file で base から失敗している。新規 section は formatter clean。
保持した既存 block（Candidate 固有 test と既存 mutation list）は既存 style のまま reformat していない。

## 8. Closure

| Criterion | Result |
|---|---|
| H001 and H002 use the shared data-driven contract | YES（`_handoff_violations` + `test_handoff_contract_is_exact[...]`） |
| no handoff-specific duplicate validator remains solely because of handoff identity | YES（`_h001_violations` / `_h002_violations` 削除） |
| frozen Ready Set drift is detectable | YES（§6） |
| existing protection categories are preserved | YES（既存 134 mutation id を全保持 + generic matrix） |
| Candidate Master is byte-identical | YES |
| full backend suite passes | YES |

```text
G-5 = CLOSED
```

## 9. Known limits

- frozen Ready Set の cross-check は `source_position` と名称（`raw_name` = `candidate_name`）までを照合する。`raw_address` は Candidate Master に持たないため照合対象外。
- `source_url` は frozen Ready Set に記録が無いため、manifest と Candidate Master の一致までしか保証しない。
- frozen doc の Markdown 構造が将来変わると parser は fail-closed で FAIL する。その場合は parser を構造に合わせて更新する（値の hard-coded copy では代替しない）。
