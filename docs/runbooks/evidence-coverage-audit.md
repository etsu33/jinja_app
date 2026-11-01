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

### 1.1 Need ごとの状態の読み方と限界

| 状態 | report 上の条件 |
|---|---|
| 根拠なし（absent） | その Need が `c_needs` にも `legacy_unattributed_needs` にも無い |
| 未検証（unreviewed） | `legacy_unattributed_needs` にだけある（出典を追跡できない。誤りではない） |
| 出典あり（source-backed） | `c_needs` にある。D と H も揃っていれば `verified_needs` |
| 矛盾（conflicting） | `conflicting_needs` にある（review 記録の入力による） |

限界:

- `recommendation-evidence-review-contract.md` で PASS になった goriyaku は、provenance が Markdown の review 文書にしか無く、DB には印が無い。そのため、本 command では `legacy_unattributed` として数え、C には数えない（過小評価の方向にずれる）。
- 軸単位の矛盾は、`--axis-conflicts-file` で渡したものしか出ない。入力が無い Need を「矛盾なし」と読まない。
- fact-ready の Source には model の `clean()` で `verified_at` が必須なので、出典追跡可否を実際に分けるのは主に URL と書誌の有無である。

## 2. 安全性

1. **主たる保証は接続ロール。** Production では SELECT 権限だけを持つ DB ロールで接続する。
2. **read-only guard（fail closed）。** 既定では、次をすべて満たした場合だけデータを読む。どれか 1 つでも満たさなければ、何も読まずに CommandError で止まる。
   - DB が PostgreSQL である
   - command の transaction が最外側である（入れ子の場合、guard が呼び出し側へ漏れるため止める）
   - `SET TRANSACTION READ ONLY` の後、`SHOW transaction_read_only` が `on` を返す

   成立した guard の種類は `execution.read_only_guard = postgresql_transaction_read_only` として記録する。
3. **production-readonly の追加条件。** 上記に加えて、次の 2 つを満たさなければ止まる。
   - `--confirm-read-only-production` を指定する。これは運用者の確認にすぎず、権限や接続先の証明ではない
   - 実効ロールが superuser ではなく、監査対象テーブル（M2M の中間テーブルを含む）のどれにも INSERT / UPDATE / DELETE / TRUNCATE 権限を持たないことを、DB に問い合わせて確認できる（`execution.select_only_role_verified = true`）
4. **検証できないこと。** 接続先が本当に意図した DB（Production）かどうかは、この command では確かめられない。そのため `execution.target_identity_verified` は常に `false` になる。接続先の確認は運用者の責任である。なお、ロールの確認は監査対象テーブルへの書き込み権限だけを見ており、それ以外の権限（schema の CREATE など）は対象外である。
5. `--allow-unguarded-local` は、ローカル / テスト専用の明示的な例外である（SQLite や入れ子 transaction で使う）。`production-readonly` と同時に指定すると拒否する。
6. **Production での実行は、オーナーが読み取り専用の経路を明示的に承認した場合に限る。** 承認が無い session（AI agent を含む）では実行しない。

### 2.1 `knowledge_coverage_report` との分担と意図的な重複クエリ

- `knowledge_coverage_report` は Knowledge の量（件数・分布・fact-ready 件数）を集計する。本 command はその出力を変えず、「出典を追跡できるか」と、相談根拠までのつながりを別の command で観測する。
- 本 command は、Source ごとの URL と確認日を見るために、Fact を Source 付きで読む。そのうえで、`eligible_now` は Shared Eligibility の正本（`fetch_fact_ready_*`）を通して別に読む。runtime と判定がずれないことを優先した意図的な重複で、クエリ数は対象数によらず一定である。
- Channel B は runtime の正本（`fetch_typed_need_matches`）で読む。そのうえで、出典の確認のために Source Fact を再読込し、次の 3 点を fail closed で確かめる。
  - Source Fact の所有 Shrine が一致の対象と同じであること
  - Source Fact が fact-ready であること
  - 出典を追跡できる Source があること
- `stable_key` は DB で一意である（`unique=True`）。

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
- 実行前の gate（専用ロール、権限境界、TLS、接続先の確認、credential の扱い）と STOP / GO 条件は `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` を参照する。2026-11-01 時点では **STOP**。

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
| `duplicate_identity_keys` | 同じ `name_jp` + `address` の行が複数ある（`place_ref` 付きの shadow 行など。過去例: migration 0100 で除去した 101 / 103 / 104） | 突き合わせから外して列挙する（1 行に潰さない）。identity 監査の手順で扱う |

差分はすべて監査文書に記録し、データの修正は別 PR・別承認で行う。provenance の欠落を「誤り」として扱わない。

## 5. Rollback

本 command はデータを変えないため、データの rollback は不要である。機能を取り下げる場合は、追加した 3 ファイル（service / command / test）とこの runbook を revert する。
