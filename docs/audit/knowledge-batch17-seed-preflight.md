> **Status: `BATCH17_SEED_ADDED_VALIDATE_ONLY_PASS_DRY_RUN_PASS_PRODUCTION_IMPORT_NOT_EXECUTED`。**
>
> 本ドキュメントは、Human Review・Post Human Review Validation・Data
> Quality Closureまで完了したBatch 1（北海道神宮・建部大社・波上宮、
> 25 Fact）を、既存Knowledge Seed運用へ正式なrepository artifact
> （`batch_17_seed.json`）として追加した記録である。
>
> **本タスクではProduction Importを実行していない。** Production DBへの
> 接続・書き込みは一切なし。実行したのは、このセッション専用のscratch DB
> （local PostgreSQL、Batch 1〜16のPilot/Validationから継続使用している
> 既存環境）に対する`--validate-only`・`--dry-run`（いずれもDB書き込み
> を行わないモード）と、既存Evidence Gate・Detail Display Stateの
> 直接呼び出しのみである。新しいModel・Migration・Importer・Evidence
> Gate・Recommendation・Knowledge Contract・Source Contractの変更は
> 一切行っていない。

# Knowledge Batch 17 — Seed Preflight

## Scope

- Human Review Closure（PR #2536・#2538・#2540）・Post Human Review
  Validation（PR #2542）・Data Quality Closure（PR #2544）まで完了した
  Batch 1最終Knowledge 25 Factを、Production Knowledge Seedとして
  repositoryへ追加する
- Production Importは実行しない（Production Seed作成とProduction
  Importを同一タスクにしない）
- 新しいModel・Migration・Importer・Evidence Gate・Recommendation・
  Knowledge Contract・Source Contractは作らない・変更しない
- Fact（Deity 12・History 13・Total 25）の追加・削除・統合・再分割は
  行わない

## 作業ブランチ / worktree（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存worktree（`shrine-human-review`・`naminoue-human-review`・`batch1-validation`・`takebe-h2-closure`） | 変更なし。いずれもtouchしていない |
| `origin/develop`最新化 | `git fetch origin develop`実行、`origin/develop` SHA=`47d4c964785c0c2c94cdfd68f8aa55ef7f9aa10d`（`docs: Batch 1 Shrine Knowledge Data Quality Closure (#2544)`）を記録 |
| PR #2542相当（Post Review Validation）のdevelop反映確認 | `git show origin/develop:docs/audit/shrine-expansion-batch1-post-review-validation.md`で全文直接確認済み |
| PR #2544相当（Data Quality Closure）のdevelop反映確認 | `git show origin/develop:docs/audit/shrine-expansion-batch1-data-quality-closure.md`で全文直接確認済み |
| `data/shrine-knowledge-batch17-seed`branch/worktree衝突 | なし（`git branch -a` / `git worktree list`で事前確認） |
| worktree作成 | `git worktree add ../jinja_app-batch17-seed -b data/shrine-knowledge-batch17-seed origin/develop` |
| worktree内working tree | clean（作成直後に確認） |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

STOP条件（Data Quality Closure未反映、branch/worktree衝突、unrelated
change存在、他branchへの変更が必要）はいずれも該当しなかった。

## 既存Knowledge Seed運用の確認（Phase 1）

`backend/temples/data/knowledge_seeds/`の既存9ファイル
（`batch_1_7_seed.json`〜`batch_16_seed.json`）、
`backend/temples/tests/test_batch9_knowledge_seed.py`〜
`test_batch16_knowledge_seed.py`、`docs/audit/knowledge-batch16-seed-preflight.md`、
`backend/temples/management/commands/import_shrine_knowledge.py`、
`backend/temples/services/knowledge_seed.py`をfresh readした。

| 確認項目 | 結果 |
|---|---|
| 最新Batch番号 | 16（`batch_16_seed.json`が最新） |
| Seed filename規則 | `batch_<N>_seed.json` |
| schema_version | `"1.0"`固定 |
| Source key規則 | `batch<N>-<slug>[-qualifier]`（例: `batch16-hachiman-official`） |
| Shrine block構造 | `shrine_ref{name_jp, address}` / `deities[]` / `histories[]` |
| Deity field構造 | `display_name, canonical_name, role, sort_order, verification_status, confidence, verified_at, note, source_keys` |
| History field構造 | `history_type, title, content, period_text, event_date, sort_order, verification_status, confidence, verified_at, note, source_keys` |
| verified_at運用 | 同一Batch・同一セッション内で固定UTC timestampを、Source・全Fact共通で使用（`batch_16_seed.json`で確認） |
| source_keys運用 | 1 Fact複数Source可、未知keyは`parse_seed`がエラーとする |
| Batch test命名規則 | `backend/temples/tests/test_batch<N>_knowledge_seed.py` |
| validate-only運用 | `import_shrine_knowledge <seed> --validate-only`、DB書き込みなし |
| dry-run運用 | `import_shrine_knowledge <seed> --dry-run`、DB書き込みなし、CREATE/SKIP/CONFLICT/AMBIGUOUS判定を出力 |
| Production Import前に必要なAudit/Test | Seed Preflight Audit（`docs/audit/knowledge-batch<N>-seed-preflight.md`）＋Batch専用test |
| Batch branch命名実例 | `docs/audit/knowledge-batch16-seed-preflight.md`はBatch16 Production Import実行記録を別ドキュメント（`knowledge-batch16-production-import-execution.md`）に分離している。本タスクはSeed追加のみのため、Production Import実行記録は本タスクの対象外（Phase 26） |

新しい命名・Schemaは作らず、上記を完全に踏襲した。

## Batch 17相当か確認（Phase 2）

| 確認項目 | 結果 |
|---|---|
| `batch_17_seed.json`の存在 | 事前確認で存在しないことを確認（`test -f`で確認） |
| Batch 17 Auditの存在 | `docs/audit/`配下に`*batch17*`ファイルが存在しないことを確認 |
| Batch 17の別用途予約 | 確認できず |

**Batch 17として進めることが妥当と判断した。**

## Final Fact Structure（Phase 3）

| Shrine | Deity | History | Total |
|---|---:|---:|---:|
| 北海道神宮 | 4 | 3 | 7 |
| 建部大社 | 2 | 4 | 6 |
| 波上宮 | 6 | 6 | 12 |
| **TOTAL** | **12** | **13** | **25** |

期待値と実測値（`parse_seed()`結果）が完全一致。期待値へ合わせるための
補完は行っていない。

## Source of Truth（正本の優先順位、禁止事項23）

Fact内容は以下の優先順位で採用した。

1. `docs/audit/shrine-expansion-batch1-data-quality-closure.md`（PR #2544）
2. `docs/audit/shrine-expansion-batch1-human-review.md`（PR #2536・#2538・#2540）
3. `docs/audit/shrine-expansion-batch1-post-review-validation.md`（PR #2542）

このセッションのscratchpadに残存していたPR #2542の実際のscratch Seed
（`/tmp/kami-musubi-batch1-post-review/knowledge_seed.json`、
`--validate-only`/`--dry-run`/Evidence Gate 23 usable/2 not usableを
実際に通過済みの実物）を技術的な出発点として使用し、以下の2点のみを
機械的に反映して最終Production Seedを構成した。

1. **建部大社Source B（見どころ）のURL**: Data Quality Closure §2で
   RESOLVEDと確認された`https://takebetaisha.jp/features/`へ更新した
   （旧scratch Seedでは空文字のまま）
2. **Source key命名**: 既存Batch命名規則（`batch17-<slug>`）へ機械的に
   rename した（`hokkaido-jingu-official-history` →
   `batch17-hokkaidojingu-official`等）。参照する`source_keys`側も
   同時に更新した。この変更はSourceの参照識別子のみに関するものであり、
   Fact自体（`history_type`/`verification_status`/`confidence`/
   `content`/`title`/`period_text`/`event_date`/`role`）はいずれも
   一切変更していない

上記2点以外の全field（`history_type`/`verification_status`/
`confidence`/`content`/`title`/`period_text`/`event_date`/`role`/
`sort_order`/`note`）は、PR #2542のscratch Seedから無変更で転記した。
これは既にHuman Review Audit・Data Quality Closureの内容と完全一致
することを本タスクのPhase 1で確認済みである（北海道神宮H1=`founding`、
建部大社H2-A/H2-B=`disputed`+`confidence:high`+2 Fact分離維持、波上宮
H5-Bのcontentに「境内整備」を含まない、波上宮role割当が本殿祭神3柱=
`unknown`/別鎮斎3柱=`enshrined`、等）。

## Seed Path

`backend/temples/data/knowledge_seeds/batch_17_seed.json`

SHA-256: `7b11943e137f8040ff25b21becc726b2df3182cb0b0f699f8e23c5c322fd8013`

## Source Set

| key | source_type | publisher | URL | verification_status | confidence |
|---|---|---|---|---|---|
| `batch17-hokkaidojingu-official` | shrine_official | 北海道神宮 | https://www.hokkaidojingu.or.jp/history.html | source_confirmed | high |
| `batch17-takebetaisha-official-about` | shrine_official | 建部大社 | https://takebetaisha.jp/about/ | source_confirmed | high |
| `batch17-takebetaisha-official-highlights` | shrine_official | 建部大社 | **https://takebetaisha.jp/features/**（Data Quality Closure §2でRESOLVED） | source_confirmed | high |
| `batch17-takebetaisha-japan-heritage` | government | 日本遺産ポータルサイト | https://japan-heritage.bunka.go.jp/ja/culturalproperties/result/6883/ | source_confirmed | high |
| `batch17-naminouegu-official` | shrine_official | 波上宮 | https://naminouegu.jp/yuisyo.html | source_confirmed | high |

Batch14〜16の既存Sourceと本Batchの5 SourceのURLに重複がないことを
`test_batch17_seed_source_semantic_identity_no_conflict_with_prior_batches`
で固定化した（PASS）。

## Timestamp / verified_at（Phase 8）

`accessed_at: "2026-08-23"` / `verified_at: "2026-08-23T07:00:00+00:00"`
を全5 Source・全25 Fact共通で使用した。

判断根拠:

- この値は、Source本文が実際に確認された時点（Fact Generation Pilot、
  PR #2533）で最初に記録され、その後Post Human Review Validation
  （PR #2542のscratch Seed）まで一貫して同一値が使われていることを、
  このセッションのscratchpadに残存する両ファイル
  （`/tmp/.../scratchpad/fact_pilot_knowledge_seed.json`と
  `/tmp/kami-musubi-batch1-post-review/knowledge_seed.json`）を直接
  比較して確認した（両ファイルとも全Source・全Factで
  `2026-08-23T07:00:00+00:00`のみ、値のブレなし）
- Source Contract（`docs/knowledge/shrine-knowledge-contract.md`）の
  `verified_at`定義「内容を人または承認済み工程で確認した日」に従い、
  Source本文の内容確認自体が行われた日（Pilot時点）を採用する。
  Human Review・Data Quality Closureはこの確認済み内容の妥当性を
  追認する工程であり、Source本文そのものを新たに確認し直した工程では
  ないため、Human Review実施日をverified_atとして新たに採用すること
  はしなかった（Source確認日とHuman Review日を混同しない、禁止事項の
  遵守）
- 適当な現在時刻の新規挿入は行っていない。既存の一貫した記録値を
  そのまま踏襲したのみであり、新しい判断を追加していない

## Seed Syntax / Structural Gate（Phase 9）

`parse_seed()`（既存実装、無変更）で確認した。

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 3 |
| Deity count | 12 |
| History count | 13 |
| Total | 25 |
| Deity–Source relation | 14（建部大社D1/D2が各2 Source） |
| History–Source relation | 13 |
| within-shrine重複 | 0 |
| source-less Deity/History | 0 |
| unresolved source_key参照 | 0 |
| role値 | `unknown`/`enshrined`のみ、既存`ROLE_CHOICES`範囲内 |
| history_type値 | `founding`/`historical_event`/`tradition`/`regional_context`、既存`HISTORY_TYPE_CHOICES`範囲内 |
| verification_status値 | `source_confirmed`（23件）/`disputed`（2件、建部大社H2-A/H2-B）、既存`KNOWLEDGE_VERIFICATION_STATUS_CHOICES`範囲内 |
| confidence値 | 全25 Factとも`high` |
| event_date | 全25 Factとも`null`（推測生成なし） |

期待値（Source 5・Deity 12・History 13・Total 25）と完全一致した。

## validate-only（Phase 10）

```
$ python manage.py import_shrine_knowledge backend/temples/data/knowledge_seeds/batch_17_seed.json --validate-only
validate-only: OK, no errors
```

**結果: PASS。** scratch DB（このセッション専用のlocal PostgreSQL、
Fact Generation Pilot・Post Review Validationから継続使用している
既存環境。3 Shrine（北海道神宮id=133・建部大社id=134・波上宮id=135）は
既存済みでDeity/Historyはいずれも0件）に対して実行した。既存
`import_shrine_knowledge`のCLI usageをコードから再確認した上で実行
した（コード変更なし）。

## dry-run（Phase 11）

```
$ python manage.py import_shrine_knowledge backend/temples/data/knowledge_seeds/batch_17_seed.json --dry-run
plan summary: {'source_CREATE': 5, 'deity_CREATE': 12, 'history_CREATE': 13}
dry-run: OK, no DB writes performed
```

**結果: PASS。** 全25 Fact + 5 SourceがすべてCREATE判定
（SKIP_EXISTS/CONFLICT/AMBIGUOUSは0件）、エラー0件、DB書き込み0件。
scratch DB以外（Production DB含む）への接続・書き込みは一切行って
いない。3 Shrineとも一意にidentity解決した。

## Evidence Gate（Phase 12）

既存`evidence_gate.decide_fact_usability()`（コード変更なし）を、
`batch_17_seed.json`の全25 Factに対し実際に呼び出した。

```
total facts: 25, usable: 23, suppressed: 2
```

| Shrine | Fact | verification_status | confidence | usable |
|---|---|---|---|---|
| 建部大社 | 白鳳4年（675年）に瀬田へ遷し祀られたとする由緒（H2-A） | disputed | high | **False** |
| 建部大社 | 天武天皇4年（676年）に現在地へ移されたと伝わる（H2-B） | disputed | high | **False** |
| その他23 Fact | （全件） | source_confirmed | high | **True** |

期待どおり。H2-A/H2Bは`display_mode=hidden`・`reason_strength=suppressed`・
`reason=fact_not_ready`。**confidence=highがdisputedを上書きしないこと
を実測で再確認した。**

## H2-A/H2-B disputed（Phase 13）

既存`evidence_gate.decide_detail_display_state()`（コード変更なし）を
H2-A/H2-Bへ適用した。

| Fact | detail_display_state |
|---|---|
| H2-A（白鳳4年/675年） | `disputed` |
| H2-B（天武天皇4年/676年） | `disputed` |

期待どおり。**Recommendation側は既存契約により非利用
（`usable=False`）、Detail側は`disputed`状態で個別Fact表示可能** という
既存の責務分離が、コード変更なしに維持されることを実測で再確認した。
675年/676年のどちらが正しいかは判断していない。H2-A/H2-Bは2 Factの
まま統合していない。

## Tests（Phase 14）

新規: `backend/temples/tests/test_batch17_knowledge_seed.py`（13件、
既存`test_batch16_knowledge_seed.py`と同型の構成）。

- `test_batch17_seed_schema_counts_and_relations`
- `test_batch17_seed_per_shrine_fact_counts`
- `test_batch17_seed_hokkaidojingu_h1_is_founding_not_tradition`
- `test_batch17_seed_takebe_h2_disputed_multiple_fact`
- `test_batch17_seed_takebe_source_b_url_resolved`
- `test_batch17_seed_naminoue_h5b_excludes_keidai_seibi`
- `test_batch17_seed_naminoue_role_assignment`
- `test_batch17_seed_no_within_shrine_duplicates`
- `test_batch17_seed_verified_at_present_for_all_facts`
- `test_batch17_seed_source_semantic_identity_no_conflict_with_prior_batches`
- `test_batch17_seed_evidence_gate_matches_data_quality_closure`
- `test_batch17_seed_import_is_idempotent_and_preserves_unrelated_knowledge`
- `test_batch17_seed_validate_only_fails_when_target_shrine_missing`

既存`test_batch9_knowledge_seed.py`・`test_batch14_knowledge_seed.py`・
`test_batch15_knowledge_seed.py`・`test_batch16_knowledge_seed.py`と
合わせて実行し、**合計48件すべてPASS（回帰なし）**。

```
$ python -m pytest temples/tests/test_batch9_knowledge_seed.py \
    temples/tests/test_batch14_knowledge_seed.py \
    temples/tests/test_batch15_knowledge_seed.py \
    temples/tests/test_batch16_knowledge_seed.py \
    temples/tests/test_batch17_knowledge_seed.py -p no:dotenv -q
48 passed in 5.22s
```

新しいテスト思想は導入していない（既存Batch16の構成をそのまま踏襲）。

## Production Safety

| 項目 | 結果 |
|---|---|
| Production DB接続 | 0（scratch DBのみ。接続先は`127.0.0.1:5432/jinja_db`、このセッション専用のlocal PostgreSQL） |
| Production write | 0 |
| Model / Migration変更 | 0 |
| Importer変更 | 0（既存`import_shrine_knowledge`をそのまま使用） |
| Evidence Gate変更 | 0 |
| Recommendation変更 | 0 |
| Source Contract変更 | 0 |
| Knowledge Contract変更 | 0 |
| Human Review済みFactの再解釈 | 0 |
| Fact追加・削除・統合・再分割 | 0（25 Factのまま） |
| role/history_type/verification_status/confidence再判断 | 0（いずれも既存確定値をそのまま転記） |
| event_date推測生成 | 0（全件`null`のまま） |
| 675年/676年の正誤判断 | 0 |
| H2-A/H2-Bの1 Factへの統合 | 0 |
| 波上宮H5-Bへの「境内整備」再追加 | 0 |
| Source本文にない情報の追加 | 0 |

## Repository Diff Gate（Phase 16）

```
$ git status --short
?? backend/temples/data/knowledge_seeds/batch_17_seed.json
?? backend/temples/tests/test_batch17_knowledge_seed.py
?? docs/audit/knowledge-batch17-seed-preflight.md
$ git diff --check
（無出力 = 問題なし）
```

変更（新規追加）は上記3ファイルのみ。Models・Migrations・Importer・
Evidence Gate・Recommendation・Contract・unrelated docs/codeへの変更は
0件。main working tree・他worktree（Compass含む）はいずれも未変更。

## Remaining Issues

- H2-B「天武天皇4年（676年）」の「伝わる」という伝承性は、引き続き
  `event_date`へ確定していない（意図的な保持であり、未解決の問題では
  ない）
- Source B（`/features/`）ページ本文の`WebFetch`による直接照合は、
  Data Quality Closureの時点から引き続き未実施（既存ネットワーク
  egress制約）。domain/title/publisher整合による対応確認に留まる
  （技術的な妨げにはならない、Data Quality Closure §2・§8参照）
- 建部大社H2-A/H2Bの`content`は、Human Review Auditが与えた`title`
  相当の記述とSource名のみから機械的に構成したものである点は、Post
  Review Validation・Data Quality Closureの時点から変わらず継続する
  残存事項として記録する
- Production Import自体は本タスクでは未実施・未判断

## Mother Ship Decision Inputs

以下を事実として返す。**Production Importを実行するかは判断しない。**

- **Human Review**: 3社とも完了済み（PR #2536・#2538・#2540）
- **Source provenance**: 完了（建部大社Source B含む、Data Quality
  Closure PR #2544でRESOLVED）
- **Content Closure**: 完了（H2-A/H2B含む、Data Quality Closure PR #2544）
- **validate-only結果**: PASS（本タスクで再実行、scratch DB、エラー0件）
- **dry-run結果**: PASS（本タスクで再実行。Source5・Deity12・History13、全件CREATE、エラー0件）
- **Evidence Gate結果**: 25 Fact中23 Factが`usable=True`、建部大社
  H2-A/H2Bの2 Factが`usable=False`（disputed、confidence=highによる
  上書きなし）
- **disputed期待挙動**: Recommendation側`usable=False`・Detail側
  `detail_display_state=disputed`という既存Contractの責務分離が実測で
  確認された
- **Test結果**: 新規13件＋既存35件＝合計48件PASS（回帰なし）
- **Seed path**: `backend/temples/data/knowledge_seeds/batch_17_seed.json`
  （repository追加済み、Production未反映）
- **Production変更0**: DB接続0・書き込み0・Model/Migration変更0・
  Evidence Gate/Recommendation/Contract変更0
- **Production Import**: **NOT EXECUTED**（本タスクの対象外。実施する
  場合は、既存Batch16の`knowledge-batch16-production-import-execution.md`
  相当の別タスク・別Human Execution Boundary Gateとして、Mother Shipの
  明示判断のもとで別途行う必要がある）

「Production Importしてよい」とは断定しない。
