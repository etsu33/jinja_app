> **Status: Active — Mother Ship Decision Pending**
>
> 本ドキュメントはrepoの実装・設定・docsのみから行った調査記録である。**本番投入は行って
> いない。DB write・migration生成・Knowledge Fact変更は一切行っていない。**

# Knowledge Production Readiness Audit

## Phase 0 — Base

| 項目 | 値 |
|---|---|
| develop HEAD | `d2410456b863d07fd5270d2807e2d9826158ad1b` |
| working tree | clean |
| PR #2311 / #2312 / #2313 | いずれもMERGED（develop反映済み） |
| Knowledge Coverage baseline | 41/100（再確認済み） |
| `docs/audit/shrine-knowledge-rollout-batch-7.md` | 存在確認済み |
| `docs/knowledge/shrine-knowledge-contract.md` | 存在確認済み |

---

## Phase 1 — Environment Inventory

repoの実装・設定・`infra/README.md`から以下を確認した。

| 環境 | 実装/設定上の証拠 |
|---|---|
| local | `docker-compose.db.yml`、`.env.local`（`postgresql://admin@127.0.0.1:5432/jinja_db`）。本Auditシリーズ全体で使用してきたDB |
| development（CI） | `.github/workflows/backend-pr.yml`が`pull_request: branches: [develop]`で起動。SQLite/一時Postgresでのテスト実行のみ、永続DBではない |
| preview（frontend限定） | `.vercel/project.json`（`projectId: prj_odAjGXc6alMlAGSx46q4RQ9EBrjp`、`projectName: jinja-app-web`）が実在。PRごとにVercel Preview URLが発行される（本session全PRの`gh pr checks`で`Vercel Deployment has completed`を確認済み） |
| staging | `infra/README.md`のTODO節に「ステージング環境（stg用Render/Vercelプロジェクト）を分けるか検討」と記載。**未決定・未着手のTODOとして明記されており、実装上の証拠は一切見つからなかった** |
| production | `backend/shrine_project/settings.py`が`.onrender.com`を`ALLOWED_HOSTS`へ明示的に追加。`apps/web/next.config.ts`が`jinja-backend.onrender.com`を画像remote patternとして参照。`apps/web/src/app/g/[username]/page.tsx`が`https://jinja-app-web.vercel.app`をfallback URLとして参照。**いずれもTODOプレースホルダーではなく実コードに埋め込まれた実際のホスト名** |

### Deploy Automation

- `.github/workflows/deploy.yml.disabled`: ファイル名に`.disabled`が付き、**無効化されている**。中身は`main`/`develop` push時にstaging/prodへ振り分けるロジックを持つが、実行されない
- `scripts/deploy.sh`: 実処理が空のスタブ（`echo "[deploy] start"` → コメントアウトされた手順 → `echo "[deploy] done"`のみ）
- `infra/README.md`はRender/Vercelの**ネイティブなGitHub連携による自動デプロイ**（`main` push → Render Web Serviceが自動リデプロイ、Vercel Projectが自動デプロイ）を前提とした記述であり、本repo内の`deploy.yml`/`deploy.sh`はこの自動デプロイの実体ではない（無効化・未実装のまま放置された別経路と考えられる）

### 分類: **`STAGING_NOT_FOUND`**

Vercel PR Previewはfrontend限定の等価物として機能しうるが、backend/DBを含む
staging環境の証拠はrepo内に存在しない。`infra/README.md`自身がこれを未決定の
TODOとして明記している。

### 重大な発見: `main`ブランチの著しい遅延

`infra/README.md`は`main`を「本番デプロイ対象ブランチ」と明記している。
`origin/main`の状態を確認したところ、以下が判明した。

```
git rev-list --left-right --count origin/main...origin/develop
= 50   3088
（mainのみに存在するcommit: 50件、developのみに存在するcommit: 3088件）

origin/main 最新commit: 7d5e7b02（2026-03-19、"Render本番環境にdrf-spectacular依存を追加"）
```

**`main`は現在（2026-08-08）から遡って約5ヶ月間、一度も更新されていない。**
最新commitのメッセージ自体が「Render本番環境」への言及であり、`main`→Render
という経路の実在性を裏付けている。

---

## Phase 2 — Knowledge Data Source of Truth Audit

### 確認結果

| 確認項目 | 結果 |
|---|---|
| KnowledgeデータがGit管理されているか | **否**。`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`の実データ（Batch 1-7、41社分）はGit管理下のいかなるファイルにも存在しない |
| fixtureが存在するか | 否。`grep`で`ShrineDeity(`/`ShrineHistory(`/`ShrineKnowledgeSource(`のコンストラクタ呼び出しを検索した結果、`models.py`（クラス定義自体）以外に該当なし。`temples/fixtures/`・`temples/tests/fixtures/`のいずれにもKnowledge実データは含まれない |
| seed dataが存在するか | 否 |
| management commandが存在するか | `knowledge_coverage_report`のみ存在するが、これは**読み取り専用の集計コマンド**であり、データ投入コマンドではない |
| import scriptが存在するか | 否 |
| data migrationが存在するか | `0093_shrine_knowledge_model_foundation.py`のみ存在するが、これは**スキーマ作成migration**（テーブル定義）であり、特定のFactデータを投入するdata migrationではない |
| Admin手入力のみなのか | 否。本session全Batchのデータ投入は、Django shell（`manage.py shell -c "..."`）経由での一回限りのPythonコード実行によるもので、Admin画面経由でもfixture経由でもない |
| local PostgreSQLにしか存在しないデータがあるか | **有**。Batch 1-7の全41社・188 Factは、local開発DBの行としてのみ存在する |
| Batch 1〜7のFactをrepoだけから再構築可能か | 下記参照 |

### 最重要質問への回答

> 「新しい空のPostgreSQLを用意した場合、現在の41社分Knowledgeをrepoから再現できるか？」

**`PARTIALLY_REPRODUCIBLE`**

理由:

- **内容そのものは十分に文書化されている。** `docs/audit/shrine-knowledge-rollout-batch-1.md`
  〜`-7.md`は、各Fact（deity/history）について`display_name`/`role`/`sort_order`相当の情報、
  `history_type`、`content`本文、`period_text`、`confidence`、Source（`title`/`publisher`/
  `url`/`source_type`）を表形式で記録しており、人間が読んでDjango shellから再入力する
  ことは原理的に可能である。
- **しかし、実行可能な（executable）再現手段が存在しない。** fixture・management
  command・data migrationのいずれも存在しないため、`python manage.py loaddata`や
  専用コマンド一発での再現はできない。再現には、docsを読みながら手作業でPythonコードを
  再構成する必要があり、これは本Auditシリーズの各Batchで実際に行った手順そのものを
  人手で繰り返すことに等しい。
- **完全な同一性（同一ID等）は再現できない。** `full_clean()`によるvalidationは
  再現できるが、`ShrineKnowledgeSource.id=999040`のような具体的なDB行IDは、
  新規DBでは別の値になる。意味内容は再現できるが、バイト単位の同一性はない。

`FULLY_REPRODUCIBLE`（実行可能なスクリプト/fixtureで完全一致再現可能）でも
`LOCAL_DB_ONLY`（docsにすら記録がない）でもない、**中間の状態**であることを
明確にする。

---

## Phase 3 — Batch Data Persistence Audit

Batch 1-7（全41社）について、各データ要素がどこに存在するかを分類した。

| データ要素 | 存在場所 |
|---|---|
| Source（`title`/`publisher`/`url`/`source_type`） | 1（docs記録）+ 2（local DB）。実行可能形式（3）では存在しない |
| Deity（`display_name`/`role`/`sort_order`） | 同上 |
| History（`content`/`history_type`/`period_text`） | 同上 |
| Fact↔Source relation | **2（local DBのみ）**。docsは「どのSourceに基づくか」を文章で記述しているが、DB上のM2M relation構造そのものはdocsに機械可読な形では存在しない |
| confidence | 1（docs記録）+ 2（local DB） |
| verification_status | 1（docs記録、全件`source_confirmed`と明記）+ 2（local DB） |
| history_type | 1（docs記録）+ 2（local DB） |
| role | 1（docs記録）+ 2（local DB） |
| sort_order | **2（local DBのみ）**。docsは複数Deity/Historyの提示順序を表の行順として示すのみで、`sort_order`という数値フィールドとして明示していないBatchがある |
| production存在 | **なし（4に該当するデータはゼロ）** |

**docsにFact Sheetが存在することと、DBを再構築できることは混同していない。**
上表の「1（docs記録）」は人間可読な記録であり、「3（executable seed/import）」は
別軸の要件として、いずれのBatchにも存在しないことを明確に区別した。

---

## Phase 4 — Production Deployment Path

### 現状確認

Knowledge Dataをproductionへ投入する**正式な経路は存在しない**。候補として
提示された方式（fixture／seed command／custom management command／data
migration／Admin manual entry／DB dump-restore／dedicated import pipeline）の
いずれも、repo内に実装・設定として存在しない。存在しない方式を採用したとは
記載しない。

### 関連する確認項目（該当経路が存在しないため、いずれも未評価）

- idempotency: 評価不能（経路が存在しない）
- duplicate protection: 評価不能
- transaction safety: 本Auditシリーズの手動投入では`transaction.atomic()`を
  一貫して使用したが、これは**再現可能な仕組みではなく、その場のDjango shell
  コードの書き方**に過ぎない
- Source relation preservation: 評価不能
- verification_status / confidence / history_type preservation: 評価不能
- rollback可能性: 評価不能
- dry-run可能性: 評価不能

---

## Phase 5 — Environment Parity

| 項目 | develop（local検証環境） | main（推定production） |
|---|---|---|
| Django version | 5.2.16 | 5.2.5（`git show origin/main:backend/requirements.txt`で確認） |
| djangorestframework | 3.17.1 | 3.16.1 |
| django-filter | 26.1 | 24.3 |
| PostgreSQL前提 | 有（`postgresql://admin@127.0.0.1:5432/jinja_db`） | 有（`DATABASE_URL`環境変数、Render PostgreSQL想定） |
| migrations | 最新（`0093_shrine_knowledge_model_foundation.py`以降を含む） | **`0044_deity_remove_conciergesession_user_and_more.py`が最新**（Knowledge関連migrationを一切含まない） |
| Knowledge models | 有（`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`） | **存在しない**（`git show origin/main:backend/temples/models.py`で`grep`した結果、該当クラス定義が0件） |
| Evidence Gate | 有（`temples/services/evidence_gate.py`） | 未確認（Knowledge modelsが無いため機能しえない） |
| Recommendation Reason（Knowledge対応） | 有（PR-B以降のconfidence/tradition対応含む） | 未確認（同上） |

**`main`はKnowledge機能そのものを一切含まないバージョンである。** これは
「production環境へのデータ投入手段が未整備」という運用上の課題ではなく、
**production（と推定される`main`）のコード自体がこの機能を実装する前の
状態にある**という、より根本的な事実である。

staging環境が存在しないため、Phase 5後半（staging→production手順の同一性等）は
評価対象外。新規staging作成の要否についても、本Auditでは決定しない
（必要性の評価のみ: developとmain間の乖離が著しく大きいため、両者の中間で
段階的に検証できる環境があれば、今後の統合リスクを下げられる可能性がある、
という評価に留める）。

---

## Phase 6 — Reproducibility Test Design（手順設計のみ、実行は限定的）

空DBから41社を復元する場合の手順を設計した（**production DBでは一切実験して
いない**）。

1. `main`ブランチへ`develop`の差分（Knowledge関連migration一式を含む）を
   マージまたはcherry-pickし、schema自体を追いつかせる
2. `python manage.py migrate`でschemaを適用
3. Batch 1-7の各Fact Sheet（`docs/audit/shrine-knowledge-rollout-batch-*.md`、
   `docs/audit/recommendation-fact-integrity-negative-pilot.md`）を順に読み、
   Source→Deity→History→relationの順で`full_clean()`検証込みのDjango shell
   コードとして再入力する（本Auditシリーズ全体で実際に使用した手順と同一）
4. 各Batch投入後、`evidence_gate.decide_fact_usability()`で`usable=True`を
   個別確認する
5. `knowledge_coverage_report`でCoverageが41/100に一致することを確認する
6. `build_recommendation_reason_v4()`を実データへ適用し、reason_textが
   各Batch記録時点の値と一致することを確認する
7. 同一手順をもう一度実行し、`full_clean()`のunique制約・重複防止が機能する
   ことを確認する（**現状、明示的な重複防止ロジックは存在しないため、
   同一Factを2回投入すると重複行が生成される可能性が高い。これは
   Phase 4のduplicate protection評価不能と対応する具体的リスクである**）

本Auditでは、上記手順の**設計のみ**を行い、実行は行っていない
（productionはもちろん、新規の一時DBに対しても実行していない）。

---

## Phase 7 — Batch 8 Gate

Production Readiness Auditの結果は、以下の技術的根拠に基づき評価できる。

| 候補 | 該当性評価 |
|---|---|
| `READY_FOR_BATCH_8` | **該当しない**。正本は明確でなく（docs記録とlocal DBに分散）、完全な再現可能性もなく、本番投入経路も存在しない |
| `READY_WITH_FOLLOWUP` | 部分的に該当しうる（Batch 8自体の技術的実行——local DBへの追加投入——は、これまでのBatchと同じ手順でリスクなく継続できる） |
| `PAUSE_BATCH_ROLLOUT` | 最も強く支持される。理由: (1) Batch 1-7が実質的にlocal DBにしか存在しない（PARTIALLY_REPRODUCIBLEであり、実行可能な再構築手段はない）、(2) `main`にKnowledge機能自体が存在せず、再構築手段が無い、(3) Batch追加のたびに「いずれ本番移行が必要になった時の手作業での再現負債」が線形に増加する |

**本Auditの技術的所見としては`PAUSE_BATCH_ROLLOUT`の根拠が最も強いが、最終判断は
本Auditでは行わず、Mother Shipへ返す。** Batch 8自体を「local DBでの追加検証」
として続ける判断もあり得るが、その場合は「production投入経路が整備されるまで、
local DBの内容は将来的に手作業で移行し直す前提である」ことを明示的に認識した
上での継続になる。

---

## Phase 8 — Deferred Tracks Inventory（現在地のみ、実装しない）

### A. Batch 8

- candidate数: 前提として、Zero-Knowledge残数からさらに絞り込みが必要
- Zero-Knowledge残数: 59/100（Batch 7時点）
- Source Availability Audit開始条件: 未着手（本Auditの結果次第でPAUSE対象になりうる）

### B. Ranking Explainability

- `docs/audit/ranking-contract-decision-record.md`で`RANKING_EXPLAINABILITY_GAP`
  として記録済み、未解決のまま
- current ranking理由（`_prefilter_debug`）は内部的にはDjango shellから
  直接取得可能だが、API/Recommendation Reasonの正規出力には含まれない
- API contract変更が必要か: 未評価（本Auditのスコープ外）
- UI変更が必要か: 未評価（同上）

### C. Production Readiness

- Phase 1-7の結果（本ドキュメント）

### D. Score Refinement

- `docs/audit/ranking-contract-decision-record.md`で`KEEP_CURRENT_SCORING_
  TEMPORARILY`確定済み
- mental/protection/rest overlapは`GORIYAKU_OVERLAP_DOUBLE_COUNT_CONFIRMED`
  として記録済み
- `SEPARATE_AXIS_SCORE_FROM_TAG_SCORE`は将来候補として記録、未実装
- 再開条件: 同ドキュメントのPhase 5参照（4条件、いずれも未充足）
- 現時点ではcode変更なし（本Auditでも変更していない）

### PER_FACT_RENDERING

- `docs/audit/mixed-confidence-policy-decision.md`で`PER_FACT_RENDERING_
  DEFERRED`として記録済み。4条件のうちいずれも未充足のまま

### Source UI

- `docs/audit/batch4-closure-trust-ux-audit-batch5-gate.md`で候補A-D比較済み、
  いずれも未採用。C案（Recommendationへの根拠導線）は「Recommendation API
  contract変更が必要」というStop Conditionに該当するとして特に慎重に扱う
  よう記録済み

---

## Phase 9 — Priority Matrix

| Track | Current State | Blocking Issue | Risk | Next Gate |
|---|---|---|---|---|
| Batch 8 | Zero-Knowledge 59/100残、次candidate未選定 | Production Readinessが未解決のまま追加投入するかどうか | Local DBのみでの追加投入自体は低リスク。ただし本番移行負債は増加する | 本Audit（Phase 7）のMother Ship判断 |
| Ranking Explainability | Gapとして記録済み、未解決 | reason_text生成ロジックの拡張が必要（未設計） | 低（ユーザー体験上の説明力不足のみ、Fact Integrityには無関係） | Score Refinement着手時に合わせて検討が自然 |
| Production Readiness | 本Auditで初めて体系的に調査 | `main`が5ヶ月停滞、Knowledge機能が production未実装、再現手段が未整備 | **高**（Batch追加のたびに将来の移行負債が増加） | Mother Ship判断（Phase 7） |
| Score Refinement | Decision Record確定済み（現状維持） | Product方針・回帰セット・churn許容範囲・Explainability整合の4条件未充足 | 低（局所的な問題、Fact Integrityへ無関係と確認済み） | 4条件が揃った時点 |
| PER_FACT_RENDERING | Deferred確定済み | Mixed confidence実害の規模・Fact単位payload監査範囲・API contract分離のいずれも未確認 | 低（現状維持で安全と確認済み） | 4条件が揃った時点 |
| Source UI | 候補比較済み、未採用 | C案はAPI contract変更を要し、Stop Condition該当 | 低〜中（B案は技術的障壁が低いが文言設計はProduct判断が必要） | Trust UX関連の別途Product判断 |

優先順位の最終決定はしない。Mother Shipへ返す。

---

## Phase 10 — Final Report

1. **stagingは存在するか**: 存在しない（`STAGING_NOT_FOUND`）。Vercel PR Previewが
   frontend限定の部分的等価物として機能するのみ。`infra/README.md`自身が
   staging構築を未決定のTODOとして記載している。
2. **productionとは何か**: `main`ブランチへのpushをトリガーに、Render
   （backend、Web Service + PostgreSQL）とVercel（frontend）へそれぞれ
   ネイティブ自動デプロイされる構成と推定される（`infra/README.md`の記述、
   実コード中の`.onrender.com`/`jinja-app-web.vercel.app`参照、`.vercel/
   project.json`の実在から）。本repo内の`deploy.yml`（無効化済み）・
   `deploy.sh`（空スタブ）はこの経路の実体ではない。
3. **production DBはどこか**: Render PostgreSQL（`DATABASE_URL`経由）と
   推定される。直接の接続確認は行っていない（本Auditのスコープ外、
   productionアクセス禁止のため）。
4. **41社Knowledgeの正本は何か**: 内容としての正本は`docs/audit/shrine-
   knowledge-rollout-batch-1.md`〜`-7.md`等の一連のAudit文書（人間可読）。
   実データとしての正本はlocal PostgreSQLの行そのもの。**両者は一致して
   いるが、後者を機械的に再構築する手段は前者からは提供されない。**
5. **空DBから41社を再現できるか**: `PARTIALLY_REPRODUCIBLE`。内容は
   十分文書化されているが、実行可能な自動再現手段（fixture/seed command/
   data migration）は存在しない。
6. **production投入経路は何か**: **存在しない。** fixture・seed command・
   custom management command・data migration・Admin manual entry・DB
   dump/restore・dedicated import pipelineのいずれも未実装。加えて、
   `main`にはKnowledge機能自体（models/migrations）が存在しないため、
   投入経路以前に受け皿となるschemaが無い。
7. **Batch 8を続けても技術負債が増えないか**: **増える。** Local DBへの
   追加投入自体は技術的に安全（これまでのBatchと同じ品質のQAプロセスで
   実行可能）だが、production未対応のまま件数が増えるほど、将来の
   手作業移行（またはツール整備後の移行）にかかる負債は線形に増加する。
8. **今後必要なPR候補**:
   - `main`へのKnowledge機能（migration一式）のマージ、またはmain自体の
     develop追従方針の決定（Mother Ship判断）
   - Knowledge Fact投入の実行可能な手段（management command等）の設計・実装
   - staging環境の要否判断、必要であれば構築
   - 上記が整うまでのBatch 8の扱い方針（continue as local-only / pause）
9. **Stop Condition該当有無**: 該当あり。「Batch 1〜7のKnowledgeがlocal DBに
   しか存在しない」「空DBから再現不能」（正確には`PARTIALLY_REPRODUCIBLE`で
   あり完全な`不能`ではないが、実行可能な手段が無いという意味で該当と判断）
   「production投入方法が未定義」の3条件に該当する。したがって**実装へは
   進まず、Mother Shipへ判断を返す。**

## Stop Conditions（該当確認）

| 条件 | 判定 |
|---|---|
| Batch 1〜7のKnowledgeがlocal DBにしか存在しない | **該当**（内容はdocsにも存在するが、実行可能な再構築手段はlocal DBの行のみ） |
| 空DBから再現不能 | **該当**（`PARTIALLY_REPRODUCIBLE`、実行可能な自動再現手段が無いという意味で） |
| production投入方法が未定義 | **該当** |
| production DBへ直接手入力する必要がある | 未評価（現状production DBへは一切アクセスしていない） |
| Source relationを安全に再現できない | **該当**（M2M relation自体がdocsに機械可読形式で存在しない） |
| idempotencyがない | **該当**（投入経路自体が存在しないため、idempotency設計も存在しない） |
| duplicate riskがある | **該当**（Phase 6で具体的に指摘した通り、明示的な重複防止ロジックは存在しない） |
| production/staging構成がdocsと実装で矛盾 | 該当なし（`infra/README.md`はTODOとして正直に未完了を記載しており、矛盾ではなく未完了） |
| production writeが必要 | 該当なし（本Auditでは一切のwriteを行っていない） |
| migration変更が必要 | 該当なし（本Auditではmigrationを生成していない。ただし将来の対応では必要になる） |

**上記の通り、複数のStop Conditionに該当するため、本Auditは実装（production
投入・migration作成・fixture作成等）へ進まず、ここで停止する。**

## Repository Changes

- `docs/audit/knowledge-production-readiness-audit.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Migration/Service/Score/Ranking/DB書き込み: すべて変更なし）
