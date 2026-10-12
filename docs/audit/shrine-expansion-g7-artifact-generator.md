# Shrine Expansion G-7: G7 Artifact Generator — Phase 1（SQL generation）

> Status:
>
> ```text
> G7_SQL_GENERATOR = PASS
> G7_OVERALL       = NOT_CLOSED
> ```
>
> Recorded at: 2026-10-12
>
> Base: `develop@2ce0fe2cbbd9217b9858482e094384f09ee61bde`（PR #3172 merge）
>
> Production write: **NONE** / Production connection: NONE
> 既存 G7 判定ルール / Importer / Gate semantics 変更: 0
> Candidate Master / handoff manifest / Base Seed / Knowledge Seed / models / migrations / Recommendation 変更: 0

Phase 1 は characterization、G7 artifact input contract、generic SQL generation だけを扱う。
generic subset extractor と generic Runtime QA generator は次の G-7 subphase に回したため、G-7 全体は CLOSED にしない。

## 1. Characterization（refactor 前の手書き artifact）

### 1.1 Inventory

| candidate | artifact | lines |
|---|---|---|
| nsrc-000002 | `sql/nsrc_000002_g7_preflight.sql` | 633 |
| | `sql/nsrc_000002_g7_pre_base_guard.sql` | 185 |
| | `sql/nsrc_000002_g7_post_base_guard.sql` | 185 |
| | `sql/nsrc_000002_g7_post_knowledge_verification.sql` | 242 |
| | `nsrc_000002_g7_extract_base_subset.py` | 81 |
| | `nsrc_000002_g7_runtime_qa.py` | 196 |
| | `backend/temples/tests/test_nsrc_000002_g7_source_identity_sql.py` | 237 |
| nsrc-000004 | `sql/nsrc_000004_g7_preflight.sql` | 132 |
| | `sql/nsrc_000004_g7_pre_base_guard.sql` | 29 |
| | `sql/nsrc_000004_g7_post_base_guard.sql` | 18 |
| | `sql/nsrc_000004_g7_post_knowledge_verification.sql` | 71 |
| | `nsrc_000004_g7_runtime_qa.py` | 179 |
| | （subset extractor script は無い） | — |

### 1.2 A. Common structure（両 candidate 共通）

- header comment: `-- <candidate> G7 …`、SELECT-only、credential / hostname / database identifier を含まない宣言。
- preflight の構成:
  - database / user の可用性は `IS NOT NULL` の boolean だけで出す。
  - latest `temples` migration と table 存在確認を出す。
  - aggregate 5種（Shrine / Source / Deity / History / SourceFact）を出す。
  - target exact と same-name の件数を出す。
  - target の Deity / History / SourceFact 行、goriyaku tag link 件数を出す。
- guard は `SELECT 1 / CASE WHEN (…) THEN 1 ELSE 0 END AS g7_<phase>_pass` の division-by-zero fail-closed で書く。
- pre-Base guard の確認内容:
  - aggregate が pre-state と一致する。
  - target exact / same-name が 0。
  - candidate の Source / Knowledge が未登録。
- post-Base guard の確認内容:
  - Shrine だけが +1 で、他の aggregate は不変。
  - target exact / same-name が 1。
  - 座標が 1e-8 以内、goriyaku が `''`、goriyaku tag link が 0。
- post-Knowledge verification は aggregate と target integrity（target の Deity / History / SourceFact 件数）を出す。
- identity は canonical な `name_jp` + `address` の完全一致。Production の numeric PK を参照しない。

### 1.3 B. Candidate-specific values

| 値 | nsrc-000002 | nsrc-000004 |
|---|---|---|
| name / address | 青澤神社 / 新潟県糸魚川市大字青海2696番地 | 青海神社 / 新潟県加茂市大字加茂字宮山229番地 |
| alternate name | 青沢神社（新字） | なし |
| 座標 | 37.00763484 / 137.79024297 | 37.65657387 / 139.0536436 |
| pre-state | 121 / 140 / 295 / 228 / 34 | 120 / 137 / 293 / 226 / 23 |
| post-state（audit 記録） | 122 / 141 / 295 / 229 / 34 | 121 / 140 / 295 / 228 / 34 |
| Source | government / `https://matsuri.geo-itoigawa.com/calendar/m04/` | shrine_official × 3（gosaisin / yuisyo / syurui） |
| Knowledge | History 1（青沢神社の春季祭礼） | Deity 2 / History 2 / SourceFact 11 |
| SQL label | `same_name_aosawa_kyuji_count` 等 | — |
| frozen evidence | PostgreSQL 17.6、latest temples 0120_shrine_source_fact_foundation、PASS / CLEAN_CREATE / ABSENT | required migration 0120_shrine_source_fact_foundation（preflight で applied を確認） |

nsrc-000004 の post-state は nsrc-000002 の pre-state と一致する（記録同士の整合）。

### 1.4 C. Source-identity-strategy-specific logic

| | nsrc-000002: `normalized_url_identity` | nsrc-000004: `url_pattern_set` |
|---|---|---|
| identity | `source_type` + `knowledge_seed.normalize_source_url()` 互換の SQL 正規化（`source_url_norm` CTE） | `source_type = 'shrine_official'` + 明示 URL の `lower(url) LIKE '%…%'` 集合 |
| reuse | `source_metadata_compatible`（publisher / verification_status / confidence / bibliography / language を strip して一致） | 概念なし（pre-Base で pattern 一致 Source が 0 であることを要求） |
| 診断 | `source_url_lookalike`（host token と path token の LIKE。identity の superset） | なし |
| state | `accepted_source_count` 0/1、`source_identity_state`（ABSENT / REUSABLE / CONFLICT_*）、importer が parse できない URL の検出 | なし |
| 共有 block | `nsrc_000002_source_identity` block を6箇所に持つ（preflight 3 / guard 各1）。既存 test が importer と照合する | なし |

2つは別の規則である。1つの推論規則に統合しない。

### 1.5 D. Knowledge-shape-specific logic

nsrc-000002（History-only / Source 1）:

- frozen pre-state CTE。3本の guard で同一である。
- preflight の state class:
  - CLEAN_CREATE / CONFLICT / ALREADY_MATERIALIZED / PARTIAL_EXISTING。
  - History 1件の期待属性で判定する。
- post-Knowledge は fail-closed guard。確認内容:
  - Source +(1 − accepted)、History +1、Deity / SourceFact +0。
  - History の期待属性（type / title / period_text / event_date null / verification / confidence）。
  - History–Source の relation が 1、metadata compatible、sourceless History が 0。
- goriyaku assignment 0 も確認する。

nsrc-000004（Deity + History + SourceFact / Source 3）:

- 各 phase で SourceFact の stable_key を列挙する。pre-Base では 0 であることを要求する。
- post-Knowledge は fail-closed ではなく、人が audit で確認する報告 SELECT である。報告内容:
  - aggregate、target integrity、pattern 一致 Source 件数。
  - sourceless Deity / History / SourceFact。
  - relation 件数、stable_key の件数と一意性。
- frozen CTE、state class、goriyaku assignment の確認は無い。

## 2. Spec contract

配置: `scripts/migration_safety/g7_specs/<candidate>.json`。

- `nsrc_000002.json` と `nsrc_000004.json` を置く。
- G-5 の test-only `backend/temples/tests/fixtures/shrine_expansion_handoffs.json` は使わない。
- generator からの参照も無い（test で固定）。

```text
schema_version                1
candidate                     candidate_id, name_jp, address, latitude, longitude, alternate_names
production_pre_state          shrine_total, source_total, deity_total, history_total, source_fact_total
base                          expected_exact_before/after, expected_same_name_before/after,
                              expected_goriyaku_tag_links_after, expected_goriyaku_text
source_identity               strategy + strategy fields
  normalized_url_identity     source_type, normalized_url, publisher, verification_status,
                              confidence, language, bibliography,
                              diagnostic_host_tokens, diagnostic_path_tokens, accepted_source_count
  url_pattern_set             source_type, url_patterns
knowledge                     expected_source/deity/history/source_fact_count,
                              expected_goriyaku_tag_links, deity_names, history_titles,
                              source_fact_stable_keys
post_state                    shrine_total, source_total, deity_total, history_total, source_fact_total
normalized_url_identity_sql   (strategy = normalized_url_identity のときだけ必須)
                              frozen_evidence {server_version, latest_temples_migration,
                                               preflight_result, production_state_class,
                                               source_identity_state}
                              sql_labels {identity, canonical, alternates}
                              history_attributes [{title, history_type, period_text, event_date,
                                                   verification_status, confidence}]
                              source_identity_regression_test
url_pattern_set_sql           (strategy = url_pattern_set のときだけ必須)
                              required_temples_migration
```

提案 field 以外に追加した field と、その出典:

| field | 理由 / 出典 |
|---|---|
| `source_identity.accepted_source_count` | nsrc-000002 frozen CTE と Source delta `+(1 − accepted)`。G7 preflight audit で Mother Ship が確定した値 |
| `normalized_url_identity_sql.frozen_evidence` | nsrc-000002 frozen CTE の comment に記録された実測値 |
| `normalized_url_identity_sql.sql_labels` | preflight の列名（`same_name_aosawa_kyuji_count` 等）。名前から作らず明示する |
| `normalized_url_identity_sql.history_attributes` | post-Knowledge guard / state class が照合する History 属性（Knowledge Seed と一致） |
| `normalized_url_identity_sql.source_identity_regression_test` | identity block の comment が参照する test。実在を検証する |
| `url_pattern_set_sql.required_temples_migration` | nsrc-000004 preflight の `temples_0120_applied` |

提案 field のうち、既存 evidence から導けず値を作る必要があったものは無い。
nsrc-000004 の Deity 名と History 名は runtime QA / Knowledge Seed / G7 audit から取った。nsrc-000002 の post-state は G7 preflight audit §16.1 から取った。

`diagnostic_host_tokens` / `diagnostic_path_tokens` は lookalike pattern を次の規則で生成する。

- host token ごとに `'%<token>%'` を作る。
- path token 列から `'%t1%t2%'` を1本作る。
- これらを AND で結合する。

nsrc-000002 の `'%matsuri.geo-itoigawa.com%' AND '%calendar%m04%'` を再現する。

## 3. Fail-closed validation

`validate_spec` は次の場合に `SpecError` を出す。

- schema / field の不正:
  - schema_version ≠ 1。
  - 未知の top-level / nested field。
  - 必須 field の欠落。
- strategy の不正:
  - 未知の strategy、または strategy の欠落。
  - 他の strategy に属する field。例: normalized の `url_patterns` や `url_pattern_set_sql`、url_pattern_set の `normalized_url` / `publisher` / `diagnostic_*` / `accepted_source_count` / `normalized_url_identity_sql`。
- candidate の不正:
  - candidate_id が `nsrc-NNNNNN` でない。
  - name / address が空、前後空白、または制御文字を含む。
  - 座標が数値でない、範囲外、NaN、bool。
- total / delta の不正:
  - 負や非整数の total。
  - `post_state − production_pre_state` が次の値と一致しない。
    - Shrine = exact_after − exact_before
    - Source = expected_source_count − accepted
    - Deity / History / SourceFact = expected 件数
  - expected 件数が列挙 list の長さと一致しない。
- list の重複:
  - stable_key、URL pattern、deity 名、history 名、alternate name の重複。
- 範囲・値域の不正:
  - base 期待値が family の表現できる値（CLEAN_CREATE: 0→1、goriyaku tag 0、goriyaku `''`）以外。
  - enum が model choices 外（backend test で同期を固定）。
  - LIKE token / pattern が小文字でない、または `%` / quote / backslash を含む。
  - frozen evidence の state が `accepted_source_count` と矛盾する。
  - regression test path が repo 外、または存在しない。
- family が表現できない形:
  - normalized family は Source 1 / Deity 0 / History 1 / SourceFact 0、event_date null だけを表現する。
  - url_pattern_set family は alternate name を持たず、stable_key が1件以上の形だけを表現する。
- 複数 spec を読み込むときの candidate_id 重複。

## 4. Generator / generated artifacts

`scripts/migration_safety/g7_sql_generator.py`（stdlib + `guard` のみ。DB / network / credential を使わない）。

```text
g7_sql_generator.py validate SPEC [SPEC ...]
g7_sql_generator.py generate --spec SPEC --output-dir DIR [--overwrite]
```

出力は固定順の4本である。

```text
1. g7_preflight.sql
2. g7_pre_base_guard.sql
3. g7_post_base_guard.sql
4. g7_post_knowledge_verification.sql
```

- 明示した output directory にだけ書く。対象4ファイルが既にあれば `--overwrite` 無しでは拒否する。他のファイルには触れない。
- 生成時に各 SQL を `guard.is_readonly_sql` で検査し、不合格なら書かない。
- template は strategy ごとの family に分ける。どちらも歴史的 artifact から件数を assert した置換で機械的に導出した。

```text
g7_templates/normalized_url_identity/{preflight, pre_base_guard, post_base_guard,
                                       post_knowledge_verification, source_identity_block}.sql.tmpl
g7_templates/url_pattern_set/{preflight, pre_base_guard, post_base_guard,
                               post_knowledge_verification}.sql.tmpl
```

## 5. nsrc-000002 golden result

| artifact | result |
|---|---|
| g7_preflight.sql | byte-identical to `sql/nsrc_000002_g7_preflight.sql` |
| g7_pre_base_guard.sql | byte-identical |
| g7_post_base_guard.sql | byte-identical |
| g7_post_knowledge_verification.sql | byte-identical |

正規化した差分は **0**。header の例外も設けていない。

Source identity block:

- 生成物の6箇所の block は committed block と同一（1種類）。
- 既存 `test_nsrc_000002_g7_source_identity_sql.py` は無変更で PASS する。生成物 = committed SQL なので、importer との照合 coverage がそのまま生成物に及ぶ。

## 6. nsrc-000004 characterization result

- spec は次をすべて明示的に表現する。
  - `shrine_official` source_type と URL pattern 3件。
  - Deity 2、History 2、SourceFact stable_key 11。
  - expected delta +1 / +3 / +2 / +2 / +11（G7 audit の記録値）。
- url_pattern_set family で生成した4本は、歴史的 `sql/nsrc_000004_g7_*.sql` と **byte-identical**。textual identity は要求されていなかったが、結果として一致した。歴史的 artifact は変更していない。
- nsrc-000004 の SQL family は Deity 名 / History 名を照合しない（歴史的 SQL がそうであるため）。これらは spec に表現され、backend test で Knowledge Seed と照合する。

## 7. Read-only proof

- 生成時の検査: `guard.is_readonly_sql`。
- test での検査: 生成8本それぞれを `guard.py check-readonly-sql` にかけ、exit 0 を確認した。
- 厳格検査（test）: `is_readonly_sql` は文頭 verb しか見ないため、data-modifying CTE を検出できない。そこで comment と string literal を除いた上で次を確認した。
  - write / DDL / transaction token が 0。
  - side-effect 関数（nextval / setval / set_config / pg_advisory* / dblink* / lo_* など）が 0。
  - 全 statement が SELECT / WITH で始まる。
- leakage 0:
  - `postgres://`、`DATABASE_URL`、`PG*` 変数名、`inet_server_addr` が出現しない。
  - `current_database()` / `current_user` は必ず `IS NOT NULL` の boolean として出す。
- generator の import は stdlib + `guard` に限る（AST で固定）。`environ` / `subprocess` を参照しない。
- isolated test DB では、生成 SQL を `SET TRANSACTION READ ONLY` の transaction 内で実行した。

## 8. Deterministic proof

- 同じ入力は byte-identical な出力になる。
- spec の dict key 順を全階層で逆順にしても、出力は byte-identical。
- artifact 順序とファイル名は `ARTIFACTS` で固定する。
- 生成は spec を変更しない。

## 9. Isolated test DB sequence（Production ではない）

`backend/temples/tests/test_g7_sql_generator_db.py` は2つの strategy を、実際の importer で作った state に対して実行する。
Production totals は test DB の実測値に置き換え、delta は保持した。

normalized_url_identity（nsrc-000002）:

```text
preflight -> CLEAN_CREATE、pre-Base guard 1、post-Base guard division by zero
Base import -> post-Base 1、pre-Base / post-Knowledge division by zero
Knowledge import -> post-Knowledge 1、post-Base division by zero、preflight ALREADY_MATERIALIZED
Knowledge 再 import -> post-Knowledge 1
lookalike（非 identity）Source -> preflight CONFLICT、pre-Base division by zero
```

url_pattern_set（nsrc-000004）:

```text
pre-Base guard 1、post-Base division by zero
Base import -> post-Base 1、pre-Base division by zero
Knowledge import -> post-Base division by zero
post-Knowledge report = post_state / Deity 2 / History 2 / SourceFact 11 / tag 0 / Source 3 /
                        sourceless 0 / relation > 0 / stable_key 11 unique
既存の pattern 一致 Source -> pre-Base division by zero
```

pre-state の drift では、両 strategy の pre-Base guard が division by zero で止まる。

Environment note:

- 非 GIS の test DB は `temples.migrations_nogis` を使う。Production の `0120_shrine_source_fact_foundation` は、そこでは `0019_shrine_source_fact_foundation` という名前である。
- test は、spec の Production 値では `temples_0120_applied = false` になることを固定する。その上で、test DB 名に置き換えると true になることを確認する。spec は Production の値のまま。

## 10. Validation

| check | result |
|---|---|
| focused generator tests（`scripts/migration_safety/tests/test_g7_sql_generator.py`） | 174 passed |
| generator DB tests + 既存 `test_nsrc_000002_g7_source_identity_sql.py`（無変更） | 15 passed |
| migration_safety tests（test_guard 含む） | 223 passed |
| scripts/tests | 685 passed |
| Candidate Master consumers | 454 passed |
| full backend suite（xdist、2回） | 5281 passed, 12 skipped（2回とも） |
| makemigrations --check | No changes detected |
| ruff check（新規ファイル） | All checks passed |
| ruff check `scripts/migration_safety/` | 11 件。base と同数で、全て変更していない `nsrc_000004_g7_runtime_qa.py` の既存指摘 |
| git diff --check | clean |

### 10.1 Observations（既存の問題。本 PR では変更していない）

1. `test_migration_0105_w0b02t02_remove_qa_artifact_id102.py::test_reverse_fails_closed_when_operator_user_is_absent_but_db_is_not_fresh` は実行順序に依存する。
   - test 内で作る `ShrineInteractionLog` の pk が sequence で決まり、それが `LOG_IDS = (3, 6)` に当たると `assert not … exists()` が落ちる。
   - 同じ worker で先に log が2件（または5件）作られていれば決定的に再現する。G7 code を含まない状態でも再現を確認した。
   - xdist の分配次第で一度だけ観測した。その後の full run 2回は PASS。
   - 本 PR の test は InteractionLog を作らない。修正は scope 外なので、別 PR で扱うべき既存の順序依存である。
2. `scripts/migration_safety/guard.py` と `scripts/analytics_safety/guard.py` は同名 module である。
   - repo root から全 test を1プロセスで collect すると、先に import された側に他方が隠され、collection error になる。base でも `scripts/migration_safety/tests/test_guard.py` が error になる。
   - 本 PR の generator は `guard.py` を private module 名（`_g7_migration_safety_guard`）で読み込み、top-level の `guard` を登録しない。
   - そのため root collection の結果は base と同じ1件 error のままである（本 PR で悪化させない。test で固定）。

## 11. Known limits

1. **G7_OVERALL = NOT_CLOSED**。generic subset extractor と generic Runtime QA generator は次の subphase に回した。
   `nsrc_000002_g7_extract_base_subset.py` と各 runtime QA script は変更していない。
2. 対応する SQL family は、2件の歴史的 candidate が示した2形だけである。
   - normalized family: History-only / Source 1。
   - url_pattern_set family: Deity・History・SourceFact、Source = pattern 集合、alternate name なし、stable_key 1件以上。
   - 他の形（例: normalized identity + Deity / SourceFact、複数 Source の reuse）は、判定ルールが決まるまで validation で拒否する。
3. 2つの family は検証の強さが異なる（歴史的差異をそのまま保持した）。
   - url_pattern_set の post-Knowledge は fail-closed guard ではなく報告 SELECT である。
   - frozen CTE、state class、goriyaku assignment の確認も無い。
   - これを揃えるのは gate semantics の変更になるため、本 PR では行わない。
4. frozen totals / evidence は、read-only preflight の実測後に人が spec へ記入する。generator は Production を読まない。
5. 新 candidate の normalized URL の表記揺れ corpus（既存 test の nsrc-000002 用 corpus 相当）は自動生成しない。
6. url_pattern_set の LIKE pattern では `_` が1文字 wildcard として働く（歴史的 SQL と同じ）。

```text
G7_SQL_GENERATOR = PASS
G7_OVERALL       = NOT_CLOSED
Production write = NONE
```
