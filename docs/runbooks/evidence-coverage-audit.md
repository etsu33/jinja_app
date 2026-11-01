# Runbook: Evidence Coverage Audit（read-only）

> **Status: Active（Runbook）**
>
> `python manage.py evidence_coverage_audit` の実行手順。分類の定義は
> `docs/audit/shrine-recommendation-evidence-eligibility-audit-2026-11-01.md` §6 を正本とする。
> 本 command は**観測のみ**であり、Recommendation の eligibility / ranking / score / Reason / API を変えない。

## 1. 何を出すか

| 出力 | 意味 |
|---|---|
| `D` | 出典で追跡できる usable な祭神 Fact が 1 件以上ある（fact-ready の Source に URL か書誌があり、`verified_at` がある） |
| `H` | 同じ条件を満たす由緒・伝承の Fact が 1 件以上ある（`official_origin` / `founding` / `historical_event` / `tradition`。`regional_context` / `editorial_summary` は数えない） |
| `C(need)` | Channel B（`ShrineSourceFact` → registry → `NEED_TO_GORIYAKU_IDS`）の一致があり、その Source Fact に出典で追跡できる Source がある |
| `legacy_unattributed` | `goriyaku_tags` から写像した Need。**出典は追跡できない（未検証）が、誤りという意味ではない。** C には数えない |
| `VERIFIED` | `eligible_now` で、D と H があり、かつ CONFLICTING を除いて C(need) が 1 つ以上ある |
| `PARTIAL_A` | `eligible_now` で、D と H があるが、検証済みの Need が無い |
| `PARTIAL_B` | `eligible_now` だが、D か H が欠けている |
| `INSUFFICIENT` | 現行の Shared Eligibility を満たさない（`eligible_now = false`） |
| `conflicting_needs` | `--axis-conflicts-file` で渡した、review 済みの軸単位の矛盾。DB には永続的な marker が無いため推測しない |
| `pillar_conflicts` | ある柱に `disputed` の Fact しか無い |
| `attributable_fact_epistemic` | 出典追跡可能な Fact を `fact`（独立した公的・学術 Source が裏付ける `founding` / `historical_event`）／`tradition`（祭神、伝承、公式由緒、神社公式のみが裏付ける記述）／`interpretation`（`regional_context` / `editorial_summary`）に分けた件数 |
| `summary.by_need` / `summary.by_prefecture` | Need 別・都道府県別の集計（都道府県は住所の前方一致で判定し、解決できなければ `UNRESOLVED`） |
| `trace_chains` | Shrine → Fact → Source → 相談根拠 → Reason inputs の代表例。各分類から `--trace-per-class` 件と、`--trace-shrine-id` で指定した Shrine |
| `execution.read_only_guard` | 実際に適用された DB 側の read-only guard |

出力は決定的である（時刻・乱数を含まず、並びは id 昇順・キー昇順）。相談文・Concierge thread / message・利用ログは一切読まない（test で固定）。

## 2. 安全性

1. **主たる保証は接続ロール。** Production では SELECT 権限だけを持つ DB ロールで接続する。
2. **多層防御。** PostgreSQL では、command 全体を `SET TRANSACTION READ ONLY` の transaction の中で実行する。書き込みは DB 側で拒否される（`execution.read_only_guard = postgresql_transaction_read_only`）。
3. `--data-origin production-readonly` を指定したときは、`--confirm-read-only-production` が無いと実行しない。
4. **Production での実行は、オーナーが読み取り専用の経路を明示的に承認した場合に限る。** 承認が無い session（AI agent を含む）では実行しない。

## 3. 実行手順

### 3.1 Repository seed baseline（ローカル）

PostGIS が使えるローカル DB（`docker-compose.db.yml` など）に対して実行する:

```bash
python manage.py migrate
```

```bash
python manage.py bootstrap_production_data --skip-debug-counts
```

```bash
for f in batch_1_7 batch_8 batch_9 batch_10 batch_11 batch_12 batch_13 batch_14 batch_15 batch_16 batch_17 nsrc_000002 nsrc_000004 nsrc_000006 nsrc_000007 nsrc_000009 nsrc_000021 nsrc_000022 nsrc_000024 nsrc_000025 wave0_batch_01 wave0_batch_02 wave0_batch_03 wave0_batch_04 wave0_batch_04_source_facts a5b_collective_pattern_b; do python manage.py import_shrine_knowledge "temples/data/knowledge_seeds/${f}_seed.json"; done
```

```bash
python manage.py evidence_coverage_audit --data-origin repository-seed-local --format json > /tmp/evidence-coverage-seed.json
```

### 3.2 Production（承認済みの読み取り専用経路でのみ）

- 接続先は SELECT 権限だけを持つロールにする。credential は repo 外のファイル（mode 600）から環境変数として読み込み、argv・ログ・出力に出さない（`scripts/migration_safety/README.md` と同じ規律）。
- 書き込みが可能なロールしか無い場合は実行しない。

```bash
python manage.py evidence_coverage_audit --data-origin production-readonly --confirm-read-only-production --format json --compare-with /tmp/evidence-coverage-seed.json > /tmp/evidence-coverage-production.json
```

- 実行後、`execution.read_only_guard` が `postgresql_transaction_read_only` であることを確認する。
- 出力 JSON には公開情報（神社名・住所・出典 URL・Fact の見出し）だけが含まれる。それでも共有は監査文書に要約を転記する形で行い、raw JSON は repo に commit しない。

### 3.3 軸単位の CONFLICTING

review 済みの矛盾は JSON 配列で渡す。identity は環境間で比較できるよう `name_jp` + `address` で指定する（DB id は使わない）:

```json
[{"name_jp": "明治神宮", "address": "東京都渋谷区代々木神園町1-1", "need": "love", "basis": "shrine-evidence-integrity-full-audit.md §11.2 CANONICAL_BUT_UNSUPPORTED"}]
```

```bash
python manage.py evidence_coverage_audit --data-origin repository-seed-local --axis-conflicts-file conflicts.json
```

DB と一致しなかった entry は `axis_conflict_input.unmatched_identity_keys` に出る。黙って無視しない。

## 4. 差分（discrepancy）の扱い

`--compare-with` は 2 つの report を identity（`name_jp` + `address`）で突き合わせる。どちらが正しいかは判定しない。

| 差分 | 想定される原因 | 対応 |
|---|---|---|
| `only_in_other`（seed にはあるが Production に無い） | seed の未 import、住所表記の差、identity の統合 | import 記録と identity 監査（canonical set）を確認する。この command では直さない |
| `only_in_current`（Production にだけある） | Places 同期・Admin 作成・投稿による Shrine | 想定内。多くは `INSUFFICIENT` になる |
| `changed`（class / pillar / `c_needs`） | Knowledge の部分 import、Production 側でのデータ編集、registry の差 | 対象 Shrine を `--trace-shrine-id` で追い、Fact と Source の状態を確認する |
| `schema_version` の不一致 | command の版が違う | 同じ版で取り直す（比較は CommandError で止まる） |

差分はすべて監査文書に記録し、データの修正は別 PR・別承認で行う。provenance の欠落を「誤り」として扱わない。

## 5. Rollback

本 command はデータを変えないため、データの rollback は不要である。機能を取り下げる場合は、追加した 3 ファイル（service / command / test）とこの runbook を revert する。
