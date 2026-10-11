# Shrine Expansion 10社バッチ化 Pipeline Readiness Audit

> Status: **READ-ONLY AUDIT / DECISION REQUIRED**
>
> Recorded at: 2026-10-11
>
> Base: `develop@aade279c`（PR #3164 merge 後）
>
> Production access: 0 / Production write: 0 / Seed 実投入: 0
> Recommendation・Meaning・API 契約の変更: 0

```text
PIPELINE_10_BATCH_READINESS = PARTIAL
REUSABLE_COMPONENTS         = Seed Builder / Coordinate Audit / Knowledge Import / Duplicate Evidence / Eligibility Verifier / Migration Safety
BLOCKING_DECISION           = D-1 Batch size（既存契約は 5社 / Batch・handoff max 5）
MINIMUM_CHANGE              = 契約不変の「5社 handoff × 2」運用 + テスト会計・G7 artifact の parameter 化
```

---

## 1. 目的と制約

目的: 既存の品質・出典・座標・重複判定ルールを変えずに、神社データを10社単位で追加して
1,000社まで拡張するために必要な最小変更を特定する。

制約（本監査で守ったもの）:

- Production DB への接続・変更なし
- Seed の実投入なし（`import_shrines_seed` / `import_shrine_knowledge` の apply 未実行）
- Recommendation / Meaning / API 契約の変更なし
- 既存の未完了バッチ（H002 の nsrc-000008 / nsrc-000010 G1、nsrc-000006 G2 HOLD）と OPEN PR に触れない
- 本 PR は本書1ファイルだけを追加する

本書の表記: **[事実]** = repository / 実行結果で確認、**[推測]** = 事実からの推論、**[提案]** = 本書の提案。

---

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md`（G0〜G8）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（schema 1.4）
- `docs/audit/shrine-expansion-wave0-data-build-plan.md`（Data Build 単位）
- `docs/audit/shrine-source-candidate-extraction-contract.md`（M1〜M5、§32 M4）
- `docs/knowledge/shrine-position-contract.md`（Position / Navigation Anchor）
- `scripts/migration_safety/README.md`（backup / restore）

---

## 3. 既存契約との衝突（最初に判断が必要な点）

**[事実]** 現行契約は「5社」を上限にしている。

| 契約 | 記述 | 実装 |
| --- | --- | --- |
| Data Build Plan | 「Data Buildの標準単位を **5社 / Batch、最大5社** とする」 | Wave0 は W0-DB01〜07 × 5社 |
| Extraction Contract §32 | `M4_READY_CANDIDATE_HANDOFF_SIZE = MAX 5`、`M4_STATUS = DECIDED` | `backend/temples/services/shrine_source_candidate_extraction.py:38 READY_HANDOFF_MAX = 5` |
| Ready Set Freeze | NIIGATA-001 100件を「最大5社単位の20 handoff」で immutable に固定 | `NIIGATA-001-H001`〜`H020` |

**[事実]** handoff membership は Extraction snapshot ごとに freeze され、後から差し込まない（§32）。

したがって「10社単位」は既存の決定済み契約と衝突する。本監査はこの契約を変更しない。

```text
D-1 Batch size decision = Mother Ship decision required
```

選択肢:

| 案 | 内容 | 既存契約 | 評価 |
| --- | --- | --- | --- |
| A（推奨） | 10社の「運用 Batch」= 凍結済み 5社 handoff × 2（例: H002+H003）。Gate 判定・Production apply・rollback は handoff 単位のまま | 変更なし | 契約・freeze を壊さずに PR / レビュー回数を半減できる |
| B | M4 / Data Build Plan を 10社へ改定 | 改定が必要（DECIDED の再判定） | blast radius が倍になる。既存 NIIGATA-001 の20 handoff freeze と不整合 |

**[推測]** 1社の G2 HOLD（例: nsrc-000006）で Batch 全体を止めない、という Data Build Plan の意図は
案 A なら handoff 内の candidate 単位進行として維持できる。

---

## 4. Component 別の現状（実装根拠・再利用可否・不足）

### 4.1 Seed Builder

**[事実]**

- `scripts/build_base_shrine_seed.py`（W0-B01）。入力・出力は `backend/temples/data/shrines_seed_clean.json` の1ファイル。
- 検証: `DUPLICATE_IDENTITY`（`(name_jp, address)`）、`DUPLICATE_ID`、`MISSING_REQUIRED`、`IDENTITY_MUTATION`、`SCHEMA_UNEXPECTED_CHANGE`（`EXPECTED_KEYS`）、`UNTRIMMED_IDENTITY`、`VISIT_STYLE_INVALID`、`PREFECTURE_UNRESOLVED`。
- identity を正規化しない（NFKC・住所表記変換なし）。行順は入力順のまま。
- 本監査で `python scripts/build_base_shrine_seed.py --check` を実行: `TOTAL=122`、`WRITTEN=0`、`BASE_SEED_BUILD=OK`。
- `backend/temples/tests/test_base_shrine_seed_build_contract.py` が byte 一致・再現性・全 gate を CI で検証する（workflow から script を直接呼ぶ箇所は無い）。
- target-only subset 抽出は候補ごとの script（`scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py`）。

再利用: builder と gate はそのまま使える（10社追加でも契約は変わらない）。

不足:

- **G-1 global count pin**: 次の test が Base Seed 全体の行数・末尾行を固定しており、Seed 追加 PR のたびに過去 Batch の test を書き換える必要がある。
  - `test_wave0_db01_knowledge_seed.py:64` `len(base_rows) == 122`
  - `test_wave0_db02_shrine_seed.py:480` `len(base_rows) == 122`
  - `test_nsrc_000002_base_shrine_seed.py:34,75,76` `EXPECTED_TOTAL_ROWS = 122` / `rows[-1] == EXPECTED_ROW`
  - 対照: `test_wave0_db03_shrine_seed.py` / `test_wave0_db04_shrine_seed.py` は「既存 prefix の sha256 + 追加範囲 slice」で書かれており、後続の追加で壊れない。
- **G-2 subset 抽出が候補別**: 10社分の subset を作る汎用 extractor が無い。

### 4.2 Coordinate Audit（Position）

**[事実]**

- `scripts/audit_shrine_positions_v2.py`（read-only・deterministic、2234行）。`--candidate-ids` / `--batch` / `--production-snapshot` / `--primary-evidence-snapshot` / `--spreadsheet-snapshot` を取り、AUTO_PASS / REVIEW / HOLD を返す。座標を書き換えない。
- 本監査で `--candidate-ids nsrc-000002 nsrc-000006 nsrc-000007`（snapshot なし）を実行: `total=3 hold=3`。理由は `PRODUCTION_SNAPSHOT_UNAVAILABLE` / `PRIMARY_EVIDENCE_NOT_RETRIEVED` 等で、入力不足時に fail closed する。
- Position Resolution Record は `docs/audit/shrine-position/*.md`（現在8件）。Candidate Master test が `HOLD_POSITION_REVIEW` 行の CORE_READY 昇格を拒否する。

再利用: Nationwide `nsrc-*` を `--candidate-ids` で指定でき、10社でもそのまま使える。

不足:

- **G-3 `--batch` は Wave0 の `build_batch` 前提**。Nationwide 行は `build_batch = null` のため、handoff 単位の指定（`--handoff NIIGATA-001-H002` 等）が無い。現状は `--candidate-ids` を列挙すれば代替できる。
- Primary Position Evidence の取得は人手（Mother Ship）。自動化しないこと自体は Position Contract に沿っている（変更対象ではない）。

### 4.3 Source-backed Backfill（Knowledge）

**[事実]**

- `import_shrine_knowledge`（`--validate-only` / `--dry-run` / apply、transaction 1つ）と `temples/services/knowledge_seed.py`。
- Source identity は `source_type + normalize_source_url()`、metadata drift / 複数一致は `SOURCE_REUSE_CONFLICT` / `AMBIGUOUS` で停止する。Shrine 解決は exact `(name_jp, address)`、曖昧なら停止（`.first()` を使わない）。
- 1 seed に複数 Shrine を持てる（既存 `batch_8_seed.json`〜`batch_17_seed.json`、`wave0_batch_0N_seed.json`）。
- Evidence Gate（`evidence_gate.decide_fact_usability`）で usable 判定。

再利用: 10社分を1つの Knowledge Seed にまとめて import できる。

不足: なし（契約上の追加機能は不要）。
**[推測]** 10社 Seed の review 量は増えるが、これは運用負荷であり実装の不足ではない。

### 4.4 重複判定

**[事実]**

| 層 | 実装 | 判定 |
| --- | --- | --- |
| Source 抽出 | `shrine_source_candidate_extraction.py` | Production collision lookup → `REVIEW_REQUIRED`（M5 Human Review） |
| G1 | Candidate Master `identity_status` / `duplicate_status`（Mother Ship 判定、per-candidate audit） | NEW / SAME_NAME_DIFFERENT_SHRINE / ... |
| Address evidence | `scripts/shrine_identity_evidence.py`（B03）、`scripts/position_identity_integration.py`（B04） | assessment のみ。最終判定はしない |
| Production 突合 | `scripts/reconcile_production_shrine_identity.py`（W0-B02、read-only、exact pair） | 差分は FAIL / STOP |
| Seed | builder `DUPLICATE_IDENTITY` | exact pair 重複で停止 |
| Knowledge import | `resolve_shrine` | 曖昧なら `IMPORT_IDENTITY_AMBIGUOUS` |

再利用: すべて変更なしで使える。

不足:

- **G-4 Production collision 検索の条件が毎回手書き**。nsrc-000009 G1 では広すぎる `%48%` 条件で false positive（玉前神社 / 千葉県長生郡一宮町一宮3048）が出た。
  name / 市区町村 / 町名+番地 を組み合わせた read-only SQL の template が無い。**[提案]** 判定ルールは変えずに、検索 SQL を parameter 化する。

### 4.5 Schema Validation

**[事実]**

- Base Seed: builder の `EXPECTED_KEYS` / `REQUIRED_KEYS`。
- Knowledge Seed: `parse_seed`（schema 1.0〜1.2）。
- Candidate Master: `test_shrine_expansion_candidate_master.py`（namespace 分割、Nationwide contract、cohort 会計）。
- Migration safety SQL: `guard.py check-readonly-sql`。

再利用: そのまま使える。

不足:

- **G-5 Handoff ごとの regression が手書き**。H001 / H002 はそれぞれ専用 block（定数・exact row・mutation 20件超）を持ち、
  Candidate Master test は現在 2198行・`def test_` + `pytest.param` 150件。1,000社 = 200 handoff を同じ書き方で増やすと test が数万行になる。
  **[提案]** 判定内容は変えずに、Handoff 定義（member / position / 現在の G1 値）を data 化し、同じ exact 検査を parameter で回す。

### 4.6 Readiness 判定

**[事実]**

- `verify_recommendation_eligibility`（read-only）。`--batch W0-DBxx` は Candidate Master の `build_batch` と `official_name` / `official_address` で解決する（`recommendation_eligibility_verifier.py:144-182`）。
- Nationwide 行は `build_batch = null` で `official_name` / `official_address` を持たない（Candidate Master contract）。
- そのため Nationwide では `--shrine-name` または test 内の `ShrineIdentity(name, address)` で個別に検証している（nsrc-000002 / 000004 G5）。
- G8 Completion Contract #1〜#12 は per-candidate audit で判定（nsrc-000002 / 000004）。

再利用: verifier 本体（eligibility rule の委譲先）はそのまま使える。

不足:

- **G-6 Nationwide の batch / handoff 単位 readiness 入力が無い**。identity を Candidate Master に持たせない現行契約のまま、
  G1 audit が保持する canonical identity を handoff 単位の read-only 入力（例: frozen identity manifest）として verifier に渡す経路が必要。
  **[提案]** Candidate Master に official_* を足すのではなく、別 artifact から渡す（契約不変）。

### 4.7 登録・Rollback

**[事実]**

- Base: `import_shrines_seed --source <subset> --skip-goriyaku-tags [--dry-run]`。transaction 1つ、dry-run は rollback。exact pair が既にあれば UPDATE 経路（`Shrine.objects.filter(name_jp, address).order_by("id").first()`）。full Base Seed の Production apply は禁止（G7 記録）。
- G7 guard: `scripts/migration_safety/sql/nsrc_000002_g7_*.sql`（frozen pre-state + identity block）、Runtime QA script も候補別（`nsrc_000002_g7_runtime_qa.py` / `nsrc_000004_g7_runtime_qa.py`）。現在 nsrc 用 SQL は11 file。
- Backup / restore: `dump_readonly.sh` / `restore_isolated.sh`（disposable DB のみ）。PostgreSQL 17 client が必要（nsrc-000002 G7 で 17.10 を使用）。
- 候補単位の Production rollback（作成した Shrine / Source / History だけを戻す）の command・SQL は **無い**。現状の rollback 手段は full backup からの復元だけ。

再利用: importer / guard の設計（frozen pre-state、fail closed、read-only check）と backup 手順はそのまま使える。

不足:

- **G-7 G7 artifact が候補別の手書き**（SQL 4本 + subset extractor + runtime QA）。10社 handoff ごとに書くと誤りの余地が大きい。
  **[提案]** 現行 SQL / script と同じ判定を、handoff manifest（対象 identity・期待 delta）から生成する read-only generator にする。
- **G-8 targeted rollback が無い**。Production write を伴う rollback 手順は本監査の範囲外で、追加するには Mother Ship 判断が要る（D-2）。
  **[提案]** まず read-only の「rollback preview」（削除対象の id を exact identity から列挙するだけの SELECT）を用意し、実行手順は別判断にする。
- **G-9 Linux で `readonly_query.sh` / `check_credential_presence.sh` の permission 確認が誤って BLOCK する**（`stat -f` を先に試すため。nsrc-000002 G7 で観測）。fail closed 側の不具合で、macOS では動く。

### 4.8 Audit 文書

**[事実]** 1候補あたりの audit 文書は nsrc-000002 で9本（G3〜G8）、H001 共通の G1〜G8 で10本。
**[推測]** 1,000社を候補別文書で進めると数千本になり、review が律速になる。
**[提案]** 判定ルールは変えずに、handoff 単位の Gate record（候補ごとの行 + 例外だけ個別文書）を template 化する。

---

## 5. 再利用できる機能（まとめ）

| 機能 | file | 10社でそのまま使えるか |
| --- | --- | --- |
| Base Seed builder / gate | `scripts/build_base_shrine_seed.py` | はい |
| Position Audit v2 | `scripts/audit_shrine_positions_v2.py` | はい（`--candidate-ids`） |
| Address identity evidence | `scripts/shrine_identity_evidence.py` / `position_identity_integration.py` | はい |
| Production reconciliation | `scripts/reconcile_production_shrine_identity.py` | はい |
| Source candidate extraction | `extract_shrine_source_candidates` | はい（handoff は max 5 のまま） |
| Knowledge import | `import_shrine_knowledge` / `knowledge_seed.py` | はい（複数 Shrine seed 対応済み） |
| Base import | `import_shrines_seed --source <subset>` | はい |
| Eligibility verifier | `verify_recommendation_eligibility` | 部分的（Nationwide は個別指定） |
| Migration safety | `scripts/migration_safety/*` | はい（PG17 client 必須） |

---

## 6. 不足機能（優先度）

| ID | 不足 | 影響 | 優先度 | 既存ルール変更 |
| --- | --- | --- | --- | --- |
| D-1 | Batch size 判断（10社 = 5×2 か、契約改定か） | 全 PR の前提 | P0（判断） | 案 A なら不要 |
| G-1 | Base Seed の global count / 末尾行 pin | Seed 追加ごとに過去 test を改変 | P1 | 不要（test の書き方のみ） |
| G-5 | Handoff regression の手書き | test 肥大・誤り | P1 | 不要 |
| G-7 | G7 artifact の候補別手書き | Production 前の誤り余地 | P1 | 不要（同じ判定を生成） |
| G-6 | Nationwide の handoff 単位 readiness 入力 | G5 / G8 の個別作業 | P2 | 不要（別 artifact で渡す） |
| G-4 | collision 検索 SQL template | false positive / 漏れ | P2 | 不要 |
| G-2 | 汎用 subset extractor | G7 準備 | P2（G-7 に含める） | 不要 |
| G-3 | Position Audit の handoff 指定 | 利便性 | P3 | 不要 |
| G-9 | Linux の `stat` 判定 | Linux 実行環境で検証不可 | P3 | 不要 |
| G-8 / D-2 | targeted rollback | 復旧が full restore のみ | 判断待ち | Production write 手順のため判断が必要 |
| — | Audit 文書の handoff template | review 律速 | P2 | 不要 |

---

## 7. 10社バッチ化の PR 分割案（案 A 前提）

各 PR は1テーマ。既存の未完了 H002（nsrc-000008 / 000010 G1、nsrc-000006 G2）とは別 file / 別 block で進め、競合させない。

| # | PR | 変更範囲 | Production | 依存 |
| --- | --- | --- | --- | --- |
| 0 | 本監査（本 PR） | 本書のみ | なし | — |
| 1 | D-1 決定記録 | 決定 audit 1本（案 A なら契約文書は不変） | なし | 0 |
| 2 | Seed test 会計の cohort 化（G-1） | 3 test の global pin を「prefix sha256 + 自 cohort の exact 行」へ置換。builder・Seed は不変 | なし | 1 |
| 3 | Handoff manifest と data 駆動 regression（G-5） | Handoff 定義を test data 化し、H001 / H002 の既存 exact 検査を同じ結果で再現（mutation 件数を減らさない） | なし | 1。H002 の G1 PR と同時に触らないよう、H002 の G1 が揃ってから着手 |
| 4 | G7 artifact generator（G-7 / G-2） | manifest から preflight / guard SQL・subset・runtime QA を生成する read-only tool + test（既存 nsrc-000002 SQL と同一出力になることを golden test で固定） | なし | 3 |
| 5 | Readiness 入力（G-6） | G1 identity manifest を verifier に渡す read-only 経路 + test。Candidate Master schema 不変 | なし | 3 |
| 6 | Collision 検索 template（G-4） | read-only SQL template + guard test | なし | 1 |
| 7 | Handoff Gate record template | audit template 1本 | なし | 1 |
| 8 | Linux `stat` 修正（G-9） | `readonly_query.sh` / `check_credential_presence.sh` + 既存 e2e test | なし | 独立 |
| 9 | 最初の10社運用 Batch（例: H003+H004）G0 登録 | Candidate Master + test（PR 3 の manifest 形式） | なし | 3 |
| — | targeted rollback（D-2） | 判断後に別途 | 判断次第 | D-2 |

**[推測]** PR 2〜5 が揃うと、1運用 Batch（10社）あたりの PR は G0 / G1 / G2 / G3〜G6 / G7 / G8 の数本に収まる。
1,000社は約100運用 Batch で、NIIGATA-001 以外の Source batch の freeze（M1〜M5）も別途必要。

---

## 8. テスト計画

| 対象 | テスト | 合格条件 |
| --- | --- | --- |
| PR 2 | 既存 3 test の置換前後で同じ Seed に対し PASS、1行追加した fixture でも過去 cohort の test が PASS、既存行を1行変えた fixture は FAIL | 既存の検査内容を減らさない |
| PR 3 | H001 / H002 の現行 exact 検査・mutation を manifest 経由で再現。現行 test と同じ件数以上の mutation が FAIL | 期待値は現行 Candidate Master と完全一致 |
| PR 4 | generator 出力が既存 `nsrc_000002_g7_*.sql` と一致（golden）。全 SQL が `check-readonly-sql` SAFE。disposable DB で pre / post-Base / post-Knowledge の PASS / FAIL 系列が nsrc-000002 G7 の記録と一致 | Production 接続なし |
| PR 5 | Nationwide identity manifest で nsrc-000002 / 000004 が ELIGIBLE、Candidate Master に official_* が増えない | 既存 G5 test と同じ結果 |
| PR 6 | 既知の false positive（`%48%`）を template が出さない、既知 collision fixture を検出する | read-only |
| PR 8 | Linux で mode 600 を PASS、644 を BLOCK。既存 `test_credential_bridge_e2e.sh` / `test_readonly_query_hostname_redaction.sh` が Linux で PASS | macOS 挙動不変 |
| 共通 | Candidate Master tests、consumer tests、`scripts/tests`、backend full suite、`makemigrations --check`、ruff、`git diff --check` | 全 PASS |

本監査の実行結果（参考）:

```text
python scripts/build_base_shrine_seed.py --check    -> TOTAL=122 / WRITTEN=0 / BASE_SEED_BUILD=OK
audit_shrine_positions_v2 --candidate-ids nsrc-000002 nsrc-000006 nsrc-000007
                                                    -> total=3 hold=3（snapshot 未指定で fail closed）
```

---

## 9. 盲点・反証

- **[推測]** 案 A でも Gate review の総量（1,000社 × G1〜G8）は減らない。減るのは PR 数と手書き artifact の誤り余地である。律速は Mother Ship の G1 / G2 判定（Primary Position Evidence の取得）になる可能性が高い。
- **[推測]** G-5 の data 化は「test が読みやすくなる」一方で、manifest 自体の誤りを test が検出できなくなる危険がある。manifest は frozen handoff（Ready Set Freeze）と突合する test を併設する必要がある。
- **[事実]** 現行 Production 書き込み経路は候補ごとの Mother Ship 承認を前提にしている。10社を1回の apply にまとめる場合、1社の guard FAIL で10社全体が止まる。案 A（apply は handoff = 5社単位）を推奨する理由の一つ。

---

## 10. 変更していないもの

- 品質・出典・座標・重複判定の各ルール
- Seed（Base / Knowledge）、Candidate Master、Position Record
- Recommendation / Meaning / API 契約、models / migrations
- Production（接続・書き込みとも0）
- OPEN PR（#2981 / #2982 Canonical Anchor ほか）と未完了 H002 Gate

```text
NEXT = D-1 Batch size decision（Mother Ship）
```
