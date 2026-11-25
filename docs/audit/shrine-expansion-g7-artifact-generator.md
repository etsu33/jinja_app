# Shrine Expansion G-7: G7 Artifact Generator

> Status（Phase 2 PR、merge 前）:
>
> ```text
> G7_SQL_GENERATOR             = PASS
> G7_SUBSET_EXTRACTOR          = PASS
> G7_RUNTIME_QA_GENERATOR      = PASS
> G7_CLOSURE_CRITERIA          = PASS
> G7_OVERALL                   = PENDING_MERGE
> ```
>
> Mother Ship が本 PR の develop への merge を確認した時点で `G7_OVERALL = CLOSED` とする（merge 前に CLOSED と書かない）。
>
> Phase 1（SQL generation）: PR #3173（`develop@eaea0a62`）、Recorded at 2026-10-12。
> Phase 2（subset + Runtime QA）: 本 PR、Base `develop@eaea0a622767e346384c6c6a3b471fec6c18df42`、Recorded at 2026-10-12。
>
> Production write: **NONE** / Production connection: NONE
> 既存 G7 判定ルール / Importer / Gate semantics 変更: 0
> Candidate Master / handoff manifest / Base Seed / Knowledge Seed / models / migrations / Recommendation / Concierge / Compass 変更: 0

§1〜§11 は Phase 1 の記録である（Phase 1 時点の status / known limit #1 は §12 以降で更新した）。§12 以降が Phase 2 の記録である。

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

---

# Phase 2 — Target-only Base subset + Runtime QA generation

## 12. Characterization（Phase 2 対象の手書き artifact）

### 12.1 A. Reusable subset behavior（`nsrc_000002_g7_extract_base_subset.py`）

- canonical Base Seed（`backend/temples/data/shrines_seed_clean.json`）だけを読む。DB / network / credential は使わない。
- exact `name_jp` + `address` で抽出する（正規化しない）。
- 1件でなければ `BLOCKED: expected exactly 1 target row, found N` で止める。
- 抽出した行全体が reviewed frozen row と一致しなければ `BLOCKED: … differs from the frozen G7 row` で止める。
- 行は書き換えず、`json.dumps([row], ensure_ascii=False, indent=2) + "\n"` で出力する。
- 出力先は `guard.is_safe_dump_path`（repository 外）に限る。
- 出力時に `SUBSET_ROWS=1` / identity / `SUBSET_SHA256` を表示する。

### 12.2 B. Candidate-specific subset evidence

| candidate | frozen row の出典 |
|---|---|
| nsrc-000002 | 歴史的 extractor の `EXPECTED_ROW`（Production 適用 subset sha256 `d5bcc322…`、G7 preflight audit §14.2） |
| nsrc-000004 | `docs/audit/niigata-h001-g4-data-materialization-reentry.md` の materialized Base Shrine row（G4 re-entry。nsrc-000004 用の subset script は存在しない） |

どちらも8 key（name_jp / address / latitude / longitude / goriyaku / kyusei / astro_elements / location）だけを持つ。

### 12.3 C. Reusable Runtime QA structure（両 script 共通）

- Django setup（`REPO_ROOT / backend`、`DJANGO_SETTINGS_MODULE` の setdefault）。
- `main()` 冒頭の `with transaction.atomic():` 内で、最初に `cursor.execute("SET TRANSACTION READ ONLY")` を実行する。
- exact identity で `Shrine.objects.get(name_jp=…, address=…)` を取得する。
- 4 surface を検証する。
  1. `ShrineDetailSerializer`（Detail）
  2. `build_chat_candidates`（Concierge candidate path）：exact match 1件、id / shrine_id / lat / lng / distance 0 / goriyaku_tag_ids `[]`
  3. score v3 profile → recommendation input → reason v4（fact / reason_text）
  4. `_distance_m` / `_bearing` / `_direction_label` / `filter_candidates_by_direction`（Compass）
- `FORBIDDEN_GUARANTEE_PHRASES`（10語）を reason_text に含めない。
- 出力 marker は DETAIL_RUNTIME / CONCIERGE_CANDIDATE_PATH / RECOMMENDATION_REASON / COMPASS_DISTANCE / COMPASS_DIRECTION / G7_PRODUCTION_RUNTIME_QA / TRANSACTION_MODE=READ_ONLY。

### 12.4 D. Candidate / strategy-specific Runtime QA assertions

| | nsrc-000002（history_only_v1） | nsrc-000004（deity_history_v1） |
|---|---|---|
| Deity | `body["deities"] == []`、candidate `knowledge_deities == []`、profile / fact の deity は None | `EXPECTED_DEITIES` 集合と件数 2、profile の deity_text に全祭神を含み、fact deity == deity_text、reason_text に全祭神を含む |
| History | 1件、exact title / type / verification、profile の history_type / confidence | `EXPECTED_HISTORY_TITLES` 集合と件数 2 |
| H1 content | candidate_profile / fact の shrine_history == H1 | 同左 |
| Source | 1件、source_type、`normalize_source_url()` で比較、verification | 各 Deity / History 行が verification `source_confirmed`、Source 1件、Source も `source_confirmed` |
| 除外 | `UNSUPPORTED_DEITY_NAMES`（tuple）を detail / reason に含めない | `EXCLUDED_DEITIES`（set）を detail / deity_text / reason に含めない |
| reason | `「{名}には、{H1}という背景があります。」` を含む | 祭神名を含む |
| 表現差 | `QA_ORIGIN` / `DIRECTIONS` は module 定数、`ShrineHistory` の id 集合も照合 | `origin` / `directions` は local 変数 |

2つは別の検証規則なので、1つの推論規則に統合しない。

## 13. Spec extension（同じ `g7_specs/*.json` に追加。別 manifest は作らない）

```text
base_subset
  expected_row        reviewed frozen Base Seed row（全 key）
runtime_qa
  family              history_only_v1 | deity_history_v1
  trace_id            build_chat_candidates の trace_id
  qa_origin           {lat, lng}
  primary_history_content
  excluded_deity_names
  forbidden_guarantee_phrases
  history_only_v1:    source_url
  deity_history_v1:   knowledge_row_verification_status, sources_per_knowledge_row,
                      source_verification_status
```

| field | 出典 |
|---|---|
| base_subset.expected_row | §12.2 |
| runtime_qa.family | 歴史的 script の構造（§12.4）。candidate id / 名前から推論しない明示値 |
| trace_id | 各 script の `trace_id=` |
| qa_origin | nsrc-000002 `QA_ORIGIN`、nsrc-000004 `origin` |
| primary_history_content | 各 script の `H1_CONTENT`（Knowledge Seed の History content と一致を backend test で照合） |
| excluded_deity_names | nsrc-000002 `UNSUPPORTED_DEITY_NAMES`、nsrc-000004 `EXCLUDED_DEITIES` |
| forbidden_guarantee_phrases | 各 script の `FORBIDDEN_GUARANTEE_PHRASES`（両 candidate で同値だが、spec ごとに明示する） |
| source_url | nsrc-000002 `SOURCE_URL`（Knowledge Seed の source url と一致。`normalize_source_url()` 結果が `normalized_url` と一致） |
| knowledge_row_verification_status / sources_per_knowledge_row / source_verification_status | nsrc-000004 の per-row assertion（Knowledge Seed と一致を照合） |

再利用した既存値（重複させない）:

- `knowledge.deity_names` → EXPECTED_DEITIES
- `knowledge.history_titles` → EXPECTED_HISTORY_TITLES / HISTORY_TITLE
- `knowledge.expected_deity_count` / `expected_history_count` → 件数
- `normalized_url_identity_sql.history_attributes[0]` → HISTORY_TYPE / history verification / confidence
- `source_identity.source_type` / `verification_status` → SOURCE_TYPE / Source verification
- `candidate` → identity / 座標

Validation（fail-closed）:

- missing / unknown field を拒否する。
- `expected_row` は8 key 必須とし、許すのは canonical の任意 key（`visit_style_tags` / `goriyaku_tags`）だけ。
- `expected_row` の identity と座標は candidate と同値・同型であること。location は mirror、goriyaku は `base.expected_goriyaku_text`、kyusei は null か文字列であること。
- 未知の family を拒否する。
- trace_id は `[a-z0-9-]` に限る（Python literal に安全）。
- excluded と expected deity の重複、空の excluded、空の forbidden を拒否する。
- `history_only_v1` は `normalized_url_identity` に限る。
- `deity_history_v1` は Deity と History がそれぞれ1件以上あることを要求する。

schema_version は 1 のまま、`base_subset` / `runtime_qa` を必須 section にした。consumer は repository 内の generator / test だけで、spec と validator を同じ PR で更新した。

## 14. Generic subset proof（`g7_extract_base_subset.py`）

```text
g7_extract_base_subset.py --spec <G7_SPEC> --output <OUTPUT_PATH> [--overwrite]
```

- canonical Base Seed だけを読む（CLI に Seed path の入力は無い）。DB / network / credential を使わない。
- exact name + address で抽出する。0件 / 2件以上 / frozen row との差異はいずれも BLOCKED。正規化しない。
- 出力は deepcopy した1行で、data と key 順を保つ。1行以外は render しないので、full Base Seed は書けない。
- 出力先は repository 外に限る。既存ファイルは `--overwrite` 無しでは置換しない。symlink / directory は `--overwrite` があっても拒否する。
- 歴史的 `nsrc_000002_g7_extract_base_subset.py` は golden reference として残した（無変更）。

| proof | result |
|---|---|
| nsrc-000002 | generic 出力 == 歴史的 extractor 出力（byte-identical）、sha256 = `d5bcc322…`（Production 適用値） |
| nsrc-000004 | canonical 青海神社 row と完全一致（1行） |
| 0件 / 2件 / drift（latitude / goriyaku / kyusei / astro / location / visit_style_tags / goriyaku_tags） | BLOCKED |
| 表記揺れ（末尾空白 / 新字 / 全角数字 / 都道府県欠落） | 一致しない（found 0） |
| 無関係行の追加・並び替え・変更 | 出力不変 |
| repository 内の出力先 / 既存ファイル / symlink / directory | BLOCKED |

## 15. Runtime QA generation proof（`g7_runtime_qa_generator.py`）

```text
g7_runtime_qa_generator.py --spec <G7_SPEC> --output <OUTPUT_PATH> [--overwrite]
```

- `runtime_qa.family` で `g7_templates/runtime_qa/<family>.py.tmpl` を選ぶ。2 family は歴史的 script から件数を assert した置換で機械的に導出した。
- generator 自身は DB / network / credential を使わず、QA も実行しない（生成物を `compile()` で構文検査するだけ）。
- `transaction.atomic()` と `SET TRANSACTION READ ONLY` を失った出力は拒否する。

| proof | result |
|---|---|
| nsrc-000002 golden | generated == `nsrc_000002_g7_runtime_qa.py`（byte-identical） |
| nsrc-000004 golden | generated == `nsrc_000004_g7_runtime_qa.py`（byte-identical） |
| 正規化した差分 | 0（header の例外も無い） |
| 決定性 | 同一入力・key 順の変更で byte-identical、spec を変更しない |

H1 content の文字列 literal 分割（`。` ごとに1 literal、1文なら1行）は表示上の規則である。両 golden を再現する。

## 16. Generated Runtime QA safety

AST で確認した（両 family）:

- `main()` の最初の文が `with transaction.atomic():` で、その最初の文が `cursor.execute('SET TRANSACTION READ ONLY')`。
- `execute` の呼び出しはこの1つだけ。
- save / create / update / delete / bulk_* / get_or_create / update_or_create / add / remove / clear / set / raw / executemany / call_command / subprocess 系の呼び出しが 0。
- subprocess / psycopg / socket / requests / urllib を import しない。migrate も呼ばない。
- credential / hostname pattern、`environ[` が無い（`DJANGO_SETTINGS_MODULE` の setdefault のみ）。

isolated DB（transaction=True）でも確認した:

- READ ONLY transaction 内の INSERT は DB 側で拒否される。
- 生成 Runtime QA の実行前後で、対象10 table の件数は不変。

## 17. Isolated test DB results（Production ではない）

各 candidate で `generic subset → import_shrines_seed --skip-goriyaku-tags → import_shrine_knowledge` を実行し、生成 Runtime QA の `main()` を実行した。

| candidate | result |
|---|---|
| nsrc-000002 | DETAIL / CONCIERGE / REASON / COMPASS_DISTANCE / COMPASS_DIRECTION / G7_PRODUCTION_RUNTIME_QA = PASS、TRANSACTION_MODE=READ_ONLY、DB 件数不変 |
| nsrc-000004 | 同上 |
| negative: nsrc-000002 の History から Source を外す | AssertionError（fail closed） |
| negative: nsrc-000004 の Deity を除外祭神名に変える | AssertionError（fail closed） |

## 18. Complete artifact reproducibility

1つの validated spec から、3つの CLI で6 artifact を生成した。

```text
g7_sql_generator.py generate        -> 1 preflight / 2 pre-Base / 3 post-Base / 4 post-Knowledge
g7_extract_base_subset.py           -> 5 one-row target-only subset
g7_runtime_qa_generator.py          -> 6 Runtime QA
```

| candidate | 1–4 SQL | 5 subset | 6 Runtime QA |
|---|---|---|---|
| nsrc-000002 | byte-identical to `sql/nsrc_000002_g7_*.sql` | byte-identical、sha256 = Production 適用値 | byte-identical |
| nsrc-000004 | byte-identical to `sql/nsrc_000004_g7_*.sql` | canonical row（歴史的 subset 成果物は無い） | byte-identical |

## 19. Validation（Phase 2）

| check | result |
|---|---|
| Phase 2 pure tests（`scripts/migration_safety/tests/test_g7_phase2_artifacts.py`） | 97 passed |
| Phase 2 DB tests（`backend/temples/tests/test_g7_phase2_db.py`） | 7 passed |
| Phase 1 SQL generator tests（pure + DB） | pass |
| 既存 nsrc-000002 G7 tests（`test_nsrc_000002_g7_*.py`） | 4 passed（無変更） |
| G7 関連 test 合計（migration_safety + Phase 1/2 DB + 既存 nsrc-000002 G7） | 342 passed |
| scripts/tests | 685 passed |
| Candidate Master consumers | 454 passed |
| full backend suite（xdist、2回） | 1回目: 1 failed（既知の順序依存 test。§10.1-1）/ 5287 passed、2回目: 5288 passed, 12 skipped |
| makemigrations --check | No changes detected |
| ruff check / format（変更・新規ファイル） | pass |
| git diff --check | clean |
| Candidate Master / Base Seed / Knowledge Seed / handoff manifest | sha256 22 files 不変 |

Phase 1 の `test_phase_1_generates_no_subset_or_runtime_qa` は、Phase 2 で runtime_qa template を追加したため、次の同等以上に厳格な境界 test に置き換えた（`test_sql_generator_generates_only_the_four_sql_artifacts`）。

- SQL generator の artifact は4本の SQL だけ。
- strategy template dir には `.sql.tmpl` だけを置く。
- runtime_qa には `.py.tmpl` だけを置く。

`g7_sql_generator.py` の差分は追加のみ（Phase 1 の SQL 生成 logic は無変更。SQL golden 8本は引き続き byte-identical）。

既知の既存問題（§10.1）は変わっていない。

- `test_migration_0105_…_db_is_not_fresh` は順序に依存する。今回も1回観測し、2回目は PASS。
- repo root からの単一プロセス collection は、`guard.py` の同名問題で base と同じ1件 error になる。

## 20. Known limits（Phase 2 時点）

1. 対応する Runtime QA family は、2件の歴史的 candidate が示した2形だけである。他の Knowledge 形の Runtime QA は、その期待値（surface ごとの assertion）を決めるまで validation で拒否する。
2. Runtime QA の期待値（primary history content、除外祭神、forbidden phrases、trace_id、origin）は、G6 / G7 の確認結果から人が spec へ転記する。generator は Knowledge Seed や DB から推論しない。
3. Runtime QA の除外祭神 / forbidden phrases は部分文字列 assertion であり、歴史的 script と同じ強さである。
4. `G7_OVERALL` は本 PR の merge 確認後に CLOSED とする。

```text
G7_SQL_GENERATOR             = PASS
G7_SUBSET_EXTRACTOR          = PASS
G7_RUNTIME_QA_GENERATOR      = PASS
G7_CLOSURE_CRITERIA          = PASS
G7_OVERALL                   = PENDING_MERGE
Production write             = NONE
```
