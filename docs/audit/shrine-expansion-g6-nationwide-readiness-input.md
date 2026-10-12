# Shrine Expansion G-6 Nationwide Handoff Readiness Input

> Base: `develop@9838b4d4ae4b42de4896a9f5ddc2dfa5425dd765`（PR #3175 merge）
>
> H001 identity authority: `docs/audit/niigata-h001-g6-verifier-identity-decision.md`
>
> Candidate Master change: NONE
> Base Seed / Knowledge Seed change: NONE
> G-5 test manifest / G7 spec change: NONE
> Recommendation Eligibility semantics change: NONE
> Production write: NONE

## 1. Scope

`verify_recommendation_eligibility` に Nationwide handoff 単位の入力（`--handoff`）を追加する。
対象 identity は新設の Nationwide identity manifest の exact `(name, address)` だけから取る。
Eligibility の判定は既存 authority へそのまま委譲する。

変更ファイル:

- `backend/temples/data/shrine_expansion_nationwide_identity_manifest.json`（新規）
- `backend/temples/services/recommendation_eligibility_verifier.py`（追加のみ: manifest validator / loader）
- `backend/temples/management/commands/verify_recommendation_eligibility.py`（`--handoff` 追加）
- `backend/temples/tests/test_g6_nationwide_handoff_identity.py`（新規）
- 本 audit

ranking / scoring / Concierge / Compass は変更しない。

## 2. 変更前の経路

### 2.1 Wave0 `--batch` 経路（変更なし）

`--batch <build_batch>` は Candidate Master の `build_batch` が一致する行の `official_name` / `official_address` を identity にする。
1件でも identity を欠く Candidate があれば中止する。

Nationwide 行は `build_batch = null` で `official_name` / `official_address` を持たない。
したがって `--batch NIIGATA-001-H001` は `--batch: no candidates found for build_batch=NIIGATA-001-H001` で中止する。
この挙動は変えず、test で固定した。

### 2.2 Nationwide per-candidate 経路（変更なし）

Nationwide candidate の eligibility は、candidate ごとの G5 test / audit が `ShrineIdentity(name, address)` を直接書いて検証していた。

- `niigata-h001-nsrc-000002-g5-recommendation-eligibility.md`
- `niigata-h001-g5-recommendation-eligibility.md`（nsrc-000004）

handoff 単位で同じ verifier を回す入力は存在しなかった。

## 3. Manifest contract

File: `backend/temples/data/shrine_expansion_nationwide_identity_manifest.json`

```text
top level   : schema_version (=1), purpose, handoffs            （これ以外の field は拒否）
handoff     : handoff_id, members                              （同上）
member      : candidate_id, source_position, name, address, identity_evidence（同上）
evidence    : verifier_identity_authority, g1_identity_audit   （同上、docs/audit/**.md のみ）
```

- `name` / `address` は exact 文字列。
  - 前後空白・制御文字は拒否する。
  - strip・正規化・`新潟県` の付加や除去・`番地` の補完や削除は行わない。
- handoffs / members は空を拒否する。
- 次は manifest 全体で一意でなければならない。
  - handoff_id
  - candidate_id
  - exact `(name, address)`
- 同名は許容する（H002 の `赤城社` ×4）。
- 1つの handoff の drift でも manifest 全体を信頼しない。全 handoff を validate してから選択する。
- loader は DB に触れない（`django_assert_num_queries(0)`）。

### 3.1 内容

| handoff | candidate | source_position | name | address |
|---|---|---|---|---|
| NIIGATA-001-H001 | nsrc-000001 | page001-row001 | 相吉神社 | 新潟県中魚沼郡津南町大字谷内4797番地 |
| | nsrc-000002 | page001-row002 | 青澤神社 | 新潟県糸魚川市大字青海2696番地 |
| | nsrc-000003 | page001-row003 | 蒼柴神社 | 新潟県長岡市悠久町707 |
| | nsrc-000004 | page001-row004 | 青海神社 | 新潟県加茂市大字加茂字宮山229番地 |
| | nsrc-000005 | page001-row005 | 青山稲荷神社 | 新潟県柏崎市荒浜4丁目1754番地2 |
| NIIGATA-001-H002 | nsrc-000006 | page001-row006 | 赤井神社 | 新潟県佐渡市加茂歌代2662番地 |
| | nsrc-000007 | page001-row007 | 赤城社 | 新潟県十日町市四日町2534番地 |
| | nsrc-000008 | page001-row008 | 赤城社 | 新潟県十日町市上組2059番地子 |
| | nsrc-000009 | page001-row009 | 赤城社 | 新潟県十日町市伊達乙48番地 |
| | nsrc-000010 | page001-row010 | 赤城社 | 新潟県南魚沼市芹田79番地 |

nsrc-000003 は Mother Ship decision §3.2 のとおり `707` のままにした（`707番地` にしない）。

## 4. Evidence provenance

- H001
  - `verifier_identity_authority` = `docs/audit/niigata-h001-g6-verifier-identity-decision.md`（§3 freeze）
  - `g1_identity_audit` = `docs/audit/niigata-h001-g1-identity-duplicate.md`
  - G1 の Source 表記（都道府県名なし）は historical evidence として変更しない。G6 はそこから導出しない。
- H002
  - 両 field とも `docs/audit/niigata-h002-<candidate_id>-g1-identity-duplicate.md`
  - 各 audit の `official_name = …` / `official_address = …` の値をそのまま使う。

Regression test は次を照合し、全参照ファイルの存在も確認する。

- H001: decision record の freeze block
- H002: 各 G1 audit の `official_name` / `official_address` 行（各1行のみであることも確認）

G-5 test-only manifest（`shrine_expansion_handoffs`）、G7 specs、Base Seed、Knowledge Seed は identity authority にしない。
verifier service と command がこれらを参照しないことを test で固定した。
runtime code（tests 以外）が G-5 manifest を参照しないことも test で固定した。

## 5. Candidate Master cross-check

validator は manifest の各 handoff について、Candidate Master と次を照合する。

- `admission_provenance.handoff_id` が一致する行の集合と順序 == manifest members の順序（membership / order drift を拒否）
- member ごとに次が成り立つこと:
  - `admission_provenance.source_position` が一致する
  - `candidate_name == name`
  - `identity_status == "CONFIRMED"`
  - `build_batch is None`
  - `official_name` / `official_address` を持たない

Candidate Master は address を持たない。そのため canonical address の exact 文字列は runtime cross-check の対象外である。
代わりに regression test が manifest を §4 の authority record と照合し、fail closed にする（§8.2）。

Candidate Master 自体は変更しない（sha256 一致、§10）。

## 6. `--handoff` contract

```text
python manage.py verify_recommendation_eligibility --handoff NIIGATA-001-H001 [--json] [--require-all-eligible]
```

- identity は `load_handoff_shrine_identities(handoff_id)` が manifest 順で返す。
  - manifest / Candidate Master の不整合は `HandoffIdentityError` になる。
  - unknown handoff も同じく `HandoffIdentityError` になる。
  - command はこれを `CommandError` に変換する。
- `--batch` と `--handoff` の併用は `CommandError` にする。合成規則が定義されていないため。
- `--shrine-id` / `--shrine-name` との併用は `--batch` と同じ扱いで、既存挙動を変えない。
- 既存の `--batch` / `--shrine-id` / `--shrine-name` 入力の互換性を保つ。既存 verifier test は無変更で PASS。
- **identity != eligibility.** manifest に identity があっても、Shrine が DB に無ければ UNRESOLVED と報告する。
  - 不足行を作らない（verifier / command に write 呼び出しが無いことを AST test で固定した）。
  - `--require-all-eligible` は handoff に ELIGIBLE 以外があれば失敗する（下記の H001 現状では失敗する）。

## 7. H001 reproduction（isolated test DB）

Test DB の state は次の手順で作った。

- `import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags`
- `import_shrine_knowledge` で `nsrc_000002_seed.json` / `nsrc_000004_seed.json`

これは既存 G5 test と同じ state である。

| candidate | requested | status | usable deity | usable history |
|---|---|---|---|---|
| nsrc-000001 | 相吉神社 / 新潟県中魚沼郡津南町大字谷内4797番地 | UNRESOLVED | - | - |
| nsrc-000002 | 青澤神社 / 新潟県糸魚川市大字青海2696番地 | **ELIGIBLE** | 0 | 1 |
| nsrc-000003 | 蒼柴神社 / 新潟県長岡市悠久町707 | UNRESOLVED | - | - |
| nsrc-000004 | 青海神社 / 新潟県加茂市大字加茂字宮山229番地 | **ELIGIBLE** | 2 | 2 |
| nsrc-000005 | 青山稲荷神社 / 新潟県柏崎市荒浜4丁目1754番地2 | UNRESOLVED | - | - |

```text
summary = requested 5 / ELIGIBLE 2 / INELIGIBLE 0 / UNRESOLVED 3 / ALL_ELIGIBLE = FAIL
```

- nsrc-000002 は ELIGIBLE（deity 0 / history 1）、nsrc-000004 は ELIGIBLE（2 / 2）。既存 G5 test と一致する。
- `--handoff` の JSON 出力は、同じ identity を direct `ShrineIdentity` で渡した report と完全一致する。
- 各 candidate の単体 direct 検証とも一致する。
- nsrc-000001 / 000003 / 000005 は Base Seed に存在しないため UNRESOLVED。これは現状の観測であり、G6 が作り出したものではない。
- H002 は 5 / 5 UNRESOLVED（Base Seed に存在しない）。
- 実行前後で `Shrine` / `ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory` の件数は不変。

## 8. Fail-closed mutations

### 8.1 Validator（`HandoffIdentityError`、37 cases）

manifest:

- member-removed / member-added / member-reordered
- candidate-id-changed / source-position-changed / handoff-id-changed / canonical-name-changed
- member-identity-copied-from-another-member
- duplicate-candidate-id / duplicate-exact-name-address / duplicate-handoff-id
- address-surrounding-whitespace / address-control-character
- empty-handoff
- missing-evidence-reference / empty-evidence-reference / evidence-reference-outside-docs / missing-identity-evidence
- unknown-top-field / unknown-handoff-field / unknown-member-field / unknown-evidence-field
- malformed-schema-version / malformed-handoffs / malformed-member / malformed-candidate-id / missing-name

Candidate Master:

- cm-identity-status-regression
- cm-membership-drift-removed / cm-membership-drift-added / cm-order-drift
- cm-source-position-drift / cm-candidate-name-drift
- cm-gained-official-address / cm-gained-official-name / cm-build-batch-assigned
- cm-shape

Loader:

- unknown handoff（`NIIGATA-001-H003` / `W0-DB01` / 空文字 / 小文字）
- missing file / invalid JSON
- 別 handoff（H002）の Candidate Master drift でも H001 の読み込みを拒否する

### 8.2 Canonical address vs authority（regression、4 cases）

- prefecture-stripped
- 707-banchi-added
- h002-address-rewritten
- width-normalized

いずれも §4 の authority record との不一致として検出する。

## 9. Unchanged eligibility semantics

Recommendation Eligibility は次のとおりで、変更しない。

- usable Deity Fact OR usable History Fact
- `shrine_knowledge_selector` → `evidence_gate.decide_fact_usability()` → `is_recommendation_eligible()`

`--handoff` は対象 identity の入力経路を追加しただけで、判定は既存 `verify_recommendation_eligibility()` をそのまま呼ぶ。
`docs/knowledge/recommendation-eligibility-contract.md` の "Shrine DB presence != Recommendation eligibility" を維持する。

## 10. Validation

```text
G6 focused tests (test_g6_nationwide_handoff_identity.py)   60 passed
verifier / W0-DB01 / nsrc-000002・000004 G5 / eligibility / Candidate Master consumers
                                                           637 passed
backend full suite (-n auto)                               5348 passed, 12 skipped
scripts/tests                                               685 passed
scripts/migration_safety/tests                              320 passed
scripts/analytics_safety/tests                               90 passed
makemigrations --check                                      No changes detected
ruff check (changed files)                                  new findings 0（I001 x2 は base から既存）
ruff format (changed files)                                 new findings 0（verifier の既存 1 hunk は base から既存）
git diff --check                                            clean
protected files sha256 (24: Candidate Master, Base Seed, Knowledge Seeds, G-5 manifest, G7 specs)
                                                            24 / 24 unchanged
```

## 11. Status

```text
G6_IDENTITY_MANIFEST        = PASS
G6_HANDOFF_INPUT            = PASS
G6_ELIGIBILITY_REPRODUCTION = PASS
G6_CLOSURE_CRITERIA         = PASS
G6_OVERALL                  = PENDING_MERGE
PRODUCTION_WRITE            = NONE
```

本 audit は次を主張しない。

- H001 / H002 の G2 PASS
- Knowledge readiness
- Production existence
- CORE_READY
