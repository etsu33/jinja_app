# Shrine Expansion G-7 / G-2: G7 Artifact Generator

> Status: **G-7 = CLOSED**（G-2 target-only subset を含む）
>
> Recorded at: 2026-10-11
>
> Base: `develop@2ce0fe2cbbd9217b9858482e094384f09ee61bde`（PR #3172 merge）
>
> Production write: **NONE**
> Production connection: NONE（generator は DB に接続しない）
> 既存 G7 判定ルール / Importer / Gate semantics 変更: 0
> Candidate Master / Base Seed / Knowledge Seed / models / migrations 変更: 0

## 1. Purpose

`docs/audit/shrine-expansion-10-shrine-batch-pipeline-readiness.md` の gap:

```text
G-7  G7 artifact が候補別の手書き（SQL 4本 + subset extractor + runtime QA）   P1
G-2  汎用 subset extractor が無い                                           P2（G-7 に含める）
```

validated input spec から G7 artifact を再現可能に生成する read-only generator を追加し、
nsrc-000002 の既存 artifact と byte 単位で同一になることを golden test で固定する。

## 2. Old manual artifacts（characterization）

### 2.1 nsrc-000002 青澤神社（golden case）

```text
scripts/migration_safety/sql/nsrc_000002_g7_preflight.sql                    633 lines
scripts/migration_safety/sql/nsrc_000002_g7_pre_base_guard.sql               185 lines
scripts/migration_safety/sql/nsrc_000002_g7_post_base_guard.sql              185 lines
scripts/migration_safety/sql/nsrc_000002_g7_post_knowledge_verification.sql  242 lines
scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py
scripts/migration_safety/nsrc_000002_g7_runtime_qa.py
backend/temples/tests/test_nsrc_000002_g7_source_identity_sql.py
```

Reusable structure:

- 4本の SQL は同一の `nsrc_000002_source_identity` block（`normalize_source_url()` を SQL で再現）を計6箇所に持つ（preflight 3 / 各 guard 1）。
- 3本の guard は同一の `frozen` CTE（frozen pre-state）を持ち、`SELECT 1 / CASE WHEN (...) THEN 1 ELSE 0 END` で fail-closed する。
- preflight は state class（CLEAN_CREATE / CONFLICT / ALREADY_MATERIALIZED / PARTIAL_EXISTING）を出す。
- runtime QA は `transaction.atomic()` + `SET TRANSACTION READ ONLY` の中で detail / concierge candidate / recommendation reason / compass を検証する。

Candidate-specific values（generator input に明示が必要なもの）:

| 種別 | 値 |
|---|---|
| canonical identity | 青澤神社 / 新潟県糸魚川市大字青海2696番地 |
| same-name variant | 青沢神社（新字。label `shinji`。canonical は `kyuji`）、preflight 列名の `aosawa` |
| Base Seed row | lat 37.00763484 / lng 137.79024297 / goriyaku "" / kyusei null / astro [] / location mirror |
| frozen pre-state totals | Shrine 121 / Source 140 / Deity 295 / History 228 / SourceFact 34 |
| frozen evidence | accepted_source_count 0、PostgreSQL 17.6、temples 0120_shrine_source_fact_foundation、G7_READ_ONLY_PREFLIGHT PASS、CLEAN_CREATE、source_identity_state ABSENT |
| expected delta | Shrine +1 / Source +(1 − accepted) / Deity +0 / History +1 / SourceFact +0 |
| Source identity | government / `https://matsuri.geo-itoigawa.com/calendar/m04/`（normalized `…/calendar/m04`） |
| Source reuse fields | publisher 糸魚川市 / 糸魚川ジオパーク協議会、source_confirmed、high、bibliography ""、ja |
| lookalike 診断 | `%matsuri.geo-itoigawa.com%` AND `%calendar%m04%` |
| Knowledge expectation | History 1件（regional_context / 青沢神社の春季祭礼 / 毎年4月第3日曜日 / event_date null / source_confirmed / high）、Deity 0、SourceFact 0 |
| Runtime QA expectation | H1 content、unsupported deity 沼河比賣命 / 沼河比売命、reason text の背景文、compass origin 35.681236 / 139.767125 |

Values that must NOT be inferred（generator は推測しない）:

- 新字 / 旧字の variant（青沢 ⇔ 青澤）や romanized label（aosawa / kyuji / shinji）を名前から作らない。
- lookalike pattern を URL から作らない。
- normalized URL を generator 内で計算しない（spec に明示し、backend test で `normalize_source_url()` と照合する）。
- frozen totals / evidence を他 candidate から流用しない。
- unsupported deity names、背景文の期待、compass origin を他 candidate と共有しない。

### 2.2 nsrc-000004 青海神社（second case: characterize only）

```text
scripts/migration_safety/sql/nsrc_000004_g7_preflight.sql                    132 lines
scripts/migration_safety/sql/nsrc_000004_g7_pre_base_guard.sql                29 lines
scripts/migration_safety/sql/nsrc_000004_g7_post_base_guard.sql               18 lines
scripts/migration_safety/sql/nsrc_000004_g7_post_knowledge_verification.sql   71 lines
scripts/migration_safety/nsrc_000004_g7_runtime_qa.py
docs/audit/niigata-h001-g7-production-import.md
（subset extractor script は無い）
```

| 項目 | nsrc-000004 |
|---|---|
| frozen pre-state | Shrine 120 / Source 137 / Deity 293 / History 226 / SourceFact 23（guard 内に literal） |
| expected delta | Shrine +1 / Source +3 / Deity +2 / History +2 / SourceFact +11 |
| Source matching | `shrine_official` + `lower(url) LIKE`（importer の normalize_source_url block を持たない） |
| frozen CTE / state class | 無し |
| Knowledge | Deity 2（椎根津彦命 / 大国魂命）、History 2、SourceFact 11（stable_key 列挙）、Source 3 |
| Runtime QA | Deity / History 集合、除外祭神3件、reason text に祭神を含む（背景文の assertion は無い） |

nsrc-000004 の post-state（121 / 140 / 295 / 228 / 34）は nsrc-000002 の frozen pre-state と一致する（記録同士の整合）。

nsrc-000004 は nsrc-000002 と構造が異なる（複数 Source / Deity / SourceFact、LIKE 照合、frozen CTE と state class が無い）。
nsrc-000002 の判定ルールをこの形へ一般化すると、複数 Source の `accepted_source_count`、Deity / SourceFact の部分状態
（PARTIAL_EXISTING）の扱いなど、**決定されていない gate semantics を新たに作る**ことになる。
したがって本 PR は nsrc-000004 を characterize のみ行い、generator の対象にしない。歴史的 artifact も変更しない。

## 3. Generator input contract

```text
scripts/migration_safety/g7_candidate_specs.json   （G7 生成入力。G-5 の test-only manifest とは別）
scripts/migration_safety/g7_artifacts.py           （validator + generator + CLI）
scripts/migration_safety/g7_templates/*.tmpl       （nsrc-000002 golden から機械的に導出した template）
```

G-5 の `backend/temples/tests/fixtures/shrine_expansion_handoffs.json` は使わない（test-only で、G7 に必要な identity / Knowledge / delta を持たない）。

Spec（schema_version 1）:

```text
candidates[]:
  candidate_id                      nsrc-NNNNNN
  knowledge_profile                 HISTORY_ONLY_SINGLE_SOURCE（唯一の対応 profile）
  identity
    official_name / official_address
    identity_label                  preflight 列名用 label
    name_variants[]                 {name_jp, label}; [0] は official_name（canonical）
  base_seed_row                     Base Seed の exact row（subset と座標の期待値）
  frozen_pre_state
    shrine/source/deity/history/source_fact_total, accepted_source_count (0|1)
    server_version, latest_temples_migration, preflight_result (PASS),
    production_state_class (CLEAN_CREATE), source_identity_state (ABSENT|REUSABLE)
  expected_delta                    {shrine, source, deity, history, source_fact}
  knowledge
    source                          source_type, url, normalized_url, publisher,
                                    verification_status, confidence, bibliography, language,
                                    lookalike_like_patterns[]
    deities []  / source_facts []   profile により空
    histories[1]                    history_type, title, content, period_text,
                                    event_date (null), verification_status, confidence
  runtime_qa
    unsupported_deity_names[], expect_history_background_sentence, compass_origin {lat, lng}
  source_identity_regression_test   repo-relative test path（存在を検証）
```

Validation（全て fail-closed、`SpecError`）:

- 全 object で missing / unknown field を拒否する。
- candidate_id の形式と重複を検査する。
- enum は model choices と一致させる（backend test で同期を固定）。
- string に前後空白と制御文字を許さない。
- `base_seed_row` と identity の一致、location の mirror、goriyaku "" を要求する。
- `source_identity_state` を `accepted_source_count` と整合させる。
- `expected_delta` を Knowledge / frozen から計算した値と完全一致させる（Source = 1 − accepted）。
- profile 外の形を拒否する: deity / source_fact が非空、history が1件でない、event_date が非 null。
- lookalike pattern は小文字で `%` を含み、quote / backslash を含まないことを要求する。
- regression test path は repo 相対で、実在することを要求する。

## 4. Generated artifact set

`generate_artifacts(candidate, base_rows)` は固定順で6件を返す:

```text
1. <slug>_g7_preflight.sql
2. <slug>_g7_pre_base_guard.sql
3. <slug>_g7_post_base_guard.sql
4. <slug>_g7_post_knowledge_verification.sql
5. <slug>_g7_base_subset.json
6. <slug>_g7_runtime_qa.py
```

CLI:

```text
g7_artifacts.py validate [--spec PATH]
g7_artifacts.py generate --candidate ID --output-dir DIR [--spec PATH] [--base-seed PATH]
```

`generate` は出力先が repository 外（`guard.is_safe_dump_path`）かつ新規 / 空 directory であることを要求する（subset を commit させない）。
各 artifact の sha256 と `PRODUCTION_CONNECTION=NONE` を出力する。

### 4.1 Target-only subset（G-2）

`extract_target_subset(base_rows, name_jp, address, expected_row)`:

- exact identity（文字列完全一致。strip / 全角半角 / 新字旧字の正規化をしない）で抽出する。
- 0件なら FAIL、2件以上でも FAIL、`expected_row` と異なる行も FAIL。
- 返す行は元の行の deepcopy で、data と key 順を保つ。
- `render_subset` は1行以外を拒否するので、full Base Seed は出力できない。
- DB にアクセスしない。

`nsrc_000002_g7_extract_base_subset.py` は CLI と出力を変えずに、この generic path と spec の frozen row を使う thin wrapper にした。

```text
SUBSET_SHA256 (旧 script / 新 script / generator) = d5bcc3229b883314d54826f4381877102c4adcda7cb1e1b662ee876260bb7e40
= docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md §14.2 の Production 適用値
```

## 5. Golden comparison（nsrc-000002）

| artifact | 結果 |
|---|---|
| preflight.sql | byte-identical |
| pre_base_guard.sql | byte-identical |
| post_base_guard.sql | byte-identical |
| post_knowledge_verification.sql | byte-identical |
| runtime_qa.py | byte-identical |
| base_subset.json | byte-identical（sha256 = Production 適用値） |

正規化した差分は **0**。header や formatting の例外も設けていない。

Source identity block:

- 生成した6箇所の block は committed block と同一の1種類だけである。
- 既存 `test_nsrc_000002_g7_source_identity_sql.py` は committed SQL に対してそのまま PASS する（変更なし）。
- generator 出力 = committed SQL なので、同じ coverage が generator 出力にも及ぶ。

## 6. Read-only proof

- 生成時に4本の SQL を `guard.is_readonly_sql` で検査し、不合格なら `SpecError` にする。
- test でも生成 SQL を tmp file に書き、`guard.py check-readonly-sql` の exit 0 を確認する（golden と synthetic の8本）。
- `is_readonly_sql` は文頭 verb しか見ず、`WITH … DELETE` のような data-modifying CTE を検出できない。そのため test では次の厳格検査も追加した。
  - comment と string literal を除いた上で、write / DDL / transaction token が 0。
  - side-effect 関数（nextval / setval / set_config / pg_advisory* / dblink* / lo_* など）が 0。
  - 全 statement が SELECT / WITH で始まる。
- credential / connection-target leakage が 0:
  - `postgres://`、`DATABASE_URL`、`PG*` 環境変数名、`inet_server_addr` が出現しない。
  - `current_database()` / `current_user` は必ず `IS NOT NULL` boolean としてだけ出力する。
- generator の import は stdlib と `guard` に限る（AST で固定）。`environ` / `subprocess` を参照しない。
- Runtime QA の `SET TRANSACTION READ ONLY` + `transaction.atomic()` は golden と同一であり、test で存在を固定する。READ ONLY transaction 中の INSERT が DB 側で拒否されることも確認する。

## 7. Deterministic proof

- 同じ入力から2回生成した結果は byte-identical。
- spec の dict key 順を全階層で逆順にしても、SQL / runtime QA は byte-identical。
- artifact の順序とファイル名は `ARTIFACT_KINDS` で固定する。
- 生成は入力（spec / Base Seed rows）を変更しない。

## 8. Local end-to-end（isolated test DB。Production ではない）

`backend/temples/tests/test_g7_artifact_generator.py` は2つの case で G7 の手順を実際の importer で再現する。

- `nsrc-000002-rebased`: nsrc-000002 の spec / Base Seed / Knowledge Seed をそのまま使い、frozen totals だけを test DB の実測値に置き換える。
- `synthetic`: 架空 candidate。名前に `'` を含め、variant 2件、別の source_type、背景文なしにした。

```text
preflight            -> CLEAN_CREATE
pre-Base guard       -> 1        post-Base guard -> division by zero
import_shrines_seed --source <generated subset> --skip-goriyaku-tags
post-Base guard      -> 1        pre-Base guard / post-Knowledge -> division by zero
import_shrine_knowledge <seed>
post-Knowledge       -> 1        post-Base guard -> division by zero
preflight            -> ALREADY_MATERIALIZED
import_shrine_knowledge <seed> (2回目)  -> post-Knowledge 1（idempotent）
generated runtime QA -> G7_PRODUCTION_RUNTIME_QA=PASS / TRANSACTION_MODE=READ_ONLY
```

追加の negative check:

- frozen totals が drift すると pre-Base guard は division by zero で止まる。
- non-identity lookalike Source があると preflight は CONFLICT を出し、pre-Base guard も止まる。

## 9. Validation

| check | result |
|---|---|
| generator pure tests（`scripts/migration_safety/tests/test_g7_artifacts.py`） | 121 passed |
| migration_safety tests（test_guard 含む） | 170 passed |
| generator DB tests + 既存 nsrc-000002 source identity test + migration_safety tests（repo root 実行） | 183 passed |
| Candidate Master consumers | 454 passed |
| scripts/tests | 685 passed |
| full backend suite | 5279 passed, 12 skipped |
| ruff check / ruff format（新規・変更ファイル） | pass（`scripts/migration_safety/` 全体の 11 件は base と同数で、全て変更していない `nsrc_000004_g7_runtime_qa.py` の既存 E402 等） |
| makemigrations --check | No changes detected |
| git diff --check | clean |

## 10. Changed files

```text
scripts/migration_safety/g7_artifacts.py                       (new)
scripts/migration_safety/g7_candidate_specs.json               (new)
scripts/migration_safety/g7_templates/*.tmpl                   (new, 6 files)
scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py (generic path を使う wrapper へ。出力不変)
scripts/migration_safety/tests/test_g7_artifacts.py            (new)
backend/temples/tests/test_g7_artifact_generator.py            (new)
docs/audit/shrine-expansion-g7-artifact-generator.md           (this file)
```

変更なし: nsrc-000002 / nsrc-000004 の SQL と runtime QA、Candidate Master、`shrine_expansion_handoffs.json`、Base Seed、Knowledge Seed、models、migrations、Recommendation、G1〜G8 decisions、Production。

## 11. Known limits

1. **対応 profile は `HISTORY_ONLY_SINGLE_SOURCE` だけ**（History 1 / Deity 0 / SourceFact 0 / Source 1、CLEAN_CREATE、event_date null）。
   Deity / SourceFact / 複数 Source / 複数 History を持つ candidate（nsrc-000004 型）は spec validation で拒否される。
   これらの G7 判定（複数 Source の accepted count、部分状態の分類）を定める Mother Ship decision が無いため、generator 側で作っていない。
   H002 以降の Knowledge 形が異なる場合は、その profile の判定ルール決定が先に必要になる。
2. frozen totals と evidence は read-only preflight の実測後に人が spec へ記入する。generator は Production を読まない。
3. 生成 SQL の source identity block が `normalize_source_url()` と等価であることの DB 照合は、nsrc-000002 の corpus（既存 test）で行っている。
   新しい candidate では target URL の正規化値を `test_spec_normalized_url_equals_importer_identity` で照合する。
   ただし、その URL 固有の表記揺れ corpus は自動生成しない。
4. `source_identity_regression_test` は新 candidate では generic test（または専用 test）を指す必要がある。generator はその test が存在することだけを検証する。
5. Runtime QA の期待値（背景文、unsupported deity、compass origin）は spec に明示された値だけを使う。
   G6 で確立した期待値を spec に転記する作業は人が行う。

## 12. Closure

| Criterion | Result |
|---|---|
| nsrc-000002 golden behavior is reproduced | YES（6 artifact byte-identical、subset sha = Production 適用値） |
| SQL remains read-only | YES（guard CLI + 厳格 token 検査 + 実 DB で READ ONLY 実行） |
| subset generation is target-only / fail-closed | YES（0 / >1 / drift / 正規化なし / 1行以外は render 不可） |
| Runtime QA expectations remain explicit | YES（spec の値のみ。READ ONLY transaction 不変。local DB で PASS） |
| generation is deterministic | YES |
| full backend suite passes | YES |

```text
G-7 = CLOSED
G-2 = CLOSED（G-7 に含める）
Production write = NONE
```
