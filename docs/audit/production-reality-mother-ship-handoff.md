> **Status: Active — Mother Ship Action Required（Render Deploy Branch特定のみ確認待ち）**
>
> 本ドキュメントは、Renderダッシュボード・production DBへのアクセス権限を持たない
> 立場から実施可能な範囲の確認と、Mother Ship側でのみ実施可能な確認事項の切り分けを
> 記録する。**productionへのwrite・設定変更・merge・migration実行は一切行っていない。
> 実施した操作はすべて、一般ユーザーのブラウザアクセスと同等の読み取り専用GET
> リクエストのみである。**

# Production Reality Audit — Mother Ship Handoff

## Phase 0 — Closure

| 項目 | 値 |
|---|---|
| PR #2315 | MERGED（2026-08-08T14:46:20Z、merge commit `f5426198`） |
| develop HEAD | `f5426198e1daf2c6c3d734004be4501f28d1ecbc` |
| working tree | clean |
| `docs/audit/production-reality-audit-stop-gate-1.md` | develop反映済み |

---

## 重要な更新: Backendが応答を再開し、決定的な証拠が得られた

前回Audit（`docs/audit/production-reality-audit-stop-gate-1.md`）時点では
`jinja-backend.onrender.com`は3回連続で`503 Service Unavailable`を返していた。
本Audit実施中に同一URLへ再度読み取り専用リクエストを行ったところ、**今回は
正常に応答した**（Render Free tierの自動スリープからの復帰と推測される。
Renderダッシュボードでの確認は依然Mother Ship側でのみ可能）。

これにより、**Backend production の実コードにKnowledge機能が含まれているか
どうかを、推測ではなく直接確認できた。**

### 確認結果: Backend production APIにKnowledge機能は存在しない

`https://jinja-backend.onrender.com/api/schema/`（drf-spectacularが実際に
稼働中のDjangoアプリから動的生成するOpenAPIスキーマ、`info.title: "Shrine
API"`、`info.version: "v1"`）を取得し、以下のキーワードの有無を確認した。

| キーワード | 結果 |
|---|---|
| `ShrineDeity` | 含まれていない |
| `ShrineHistory` | 含まれていない |
| `ShrineKnowledgeSource` | 含まれていない |
| `knowledge_deities` | 含まれていない |
| `knowledge_histories` | 含まれていない |
| `recommendation_reason_v4_detail` | 含まれていない |
| `history_type` | 含まれていない |
| `verification_status` | 含まれていない |
| `evidence_gate` | 含まれていない |

**9項目すべてが「含まれていない」。** drf-spectacularのスキーマは実際に
稼働しているDjangoアプリのモデル・シリアライザから動的生成されるため、
これは「production backendの現在動いているコードには、Knowledge機能が
一切実装されていない」ことの直接証拠である（推測ではない）。

これは前回Auditが`main`ブランチの静的解析（`git show origin/main:...`）から
導いた「Knowledge機能が存在しない」という結論と**内容として一致する**。
ただし、これが「Render deploy branch = `main`」であることの証明にはならない
（`main`と同等かそれ以前の別コミット・別ブランチである可能性も残る）。
「Backend productionにKnowledge機能が存在するか」という、本Auditシリーズが
最終的に必要としていた問いへの答えとしては、**この時点で直接確認できた**。

### 追加確認（範囲を広げすぎないよう最小限に留めた）

`GET /api/shrines/?limit=1`を試行したところ`500 Internal Server Error`が
返った。原因は追跡していない（クエリパラメータの形式が想定と異なる可能性が
高く、production自体の不具合とは断定できない）。これ以上の追加リクエストは
「読み取り専用の妥当な確認」の範囲を超えると判断し、行っていない。

---

## Phase 1 — Known Facts（事実と推論の分離、削除せず維持）

過去のAudit文書（`docs/audit/knowledge-production-readiness-audit.md`、
`docs/audit/production-reality-audit-stop-gate-1.md`）の内容は削除せず、以下の通り
「確認済み事実」と「そこから導いた推論」を分離して記録する。

### 確認済み事実（`git`・Vercel API・公開URLで直接検証済み）

- `origin/main`は`origin/develop`より3088 commit遅れ、最新commitは2026-03-19
- `origin/main`の`models.py`にはKnowledge関連クラス定義が存在しない
- `origin/main`の最新migrationは`0044`番、Knowledge関連migration
  （`0093`番以降）を含まない
- Vercelの`list_deployments`で直近20件を確認した結果、`target: production`が
  付いた10件は全て`branch: develop`だった
- `infra/README.md`は「`main`が本番デプロイ対象ブランチ」と明記している
  （Frontendの実態と矛盾する）
- `jinja-backend.onrender.com`は一時的に503を返す状態だったが、その後
  正常応答するようになった（Free tierの自動スリープ挙動と整合する）
- **`jinja-backend.onrender.com`の実際に稼働中のOpenAPIスキーマには、
  Knowledge関連の型・フィールド・エンドポイントが一切含まれていない
  （直接確認済み）**

### 誤り・未証明のまま残る推論

- 「Backend production deploy branchが`main`である」こと自体は、依然として
  **未証明**。ただし、この問いの実質的な目的（Knowledge機能がproductionに
  存在するか）については、上記の直接確認によって**Branchが何であるかに
  関わらず、答えが出た**（存在しない）。

---

## Phase 2 — Render Dashboard確認（一部はMother Ship Actionが必要なまま）

Backend production にKnowledge機能が無いことは直接確認できたが、
**具体的なDeploy branch名・最新デプロイSHA・Auto-Deploy設定・Service状態の
詳細**は、依然としてRenderダッシュボードでなければ確認できない。以下は
Mother Ship側での確認を引き続き依頼する。

- [ ] Deploy branch（`main`か、それとも別の未確認ブランチか）
- [ ] Auto-Deploy ON/OFF
- [ ] Latest successful deployのcommit SHA
- [ ] Latest deployの日時
- [ ] Service status／Suspend状態（今回応答が復活した原因の裏付け）

## Phase 3 — 503 Cause Classification

| 候補 | 判定 |
|---|---|
| `SERVICE_SLEEPING` | **最も有力**。前回503、今回応答という推移が、Render Free tierの
  自動スリープ／復帰パターンと整合する |
| `SERVICE_SUSPENDED` | 該当しない可能性が高い（復帰したため） |
| `DEPLOY_FAILED` / `STARTUP_CRASH` | 該当しない（現在正常応答している） |
| `DATABASE_UNAVAILABLE` | 該当しない（`/api/schema/`が正常に返り、シリアライザ定義まで
  正しく生成されている） |
| `HEALTHCHECK_FAILED` / `BILLING_OR_PLAN_LIMIT` | 未確認、Renderダッシュボードの
  Eventsログでの裏付けが望ましい |

**確定的な原因特定にはRenderダッシュボードのEventsログが必要**だが、
「サービス自体は現在正常に機能している」ことは直接確認できたため、
Stop Gate 2（503原因不明のため実装へ進まない）は、コード修正を要する
文脈では引き続き有効だが、**Knowledge機能の有無という当初の目的に対しては
解消された**。

---

## Phase 4 — Backend Deploy Branch Decision Tree

Case A（develop）/ Case B（main）/ Case Cのいずれであるかは未確定のまま
残るが、**いずれのCaseであっても、現在のBackend production コードには
Knowledge機能が存在しないという事実は変わらない**（Case AだとしてもKnowledge
関連migrationが未適用の状態でdeployされている可能性、Case Bであれば
`main`自体がKnowledge機能実装前であることと整合、のいずれかを意味する）。

## Phase 5 — Production DB Reality

DB shellへの直接アクセスは行っていない。ただし、Phase 0で得たAPIスキーマの
直接証拠により、「Knowledge tables（`ShrineKnowledgeSource`等）がproduction
DBに存在するか」という問いは、**API層からの間接的だが十分に強い証拠**で
代替できた。migration未適用であればテーブル自体が存在せず、Djangoアプリの
起動時にモデル参照エラーが発生する可能性が高いところ、`/api/schema/`が
正常にモデル定義を含まずに生成されていることは、「Knowledge modelを含まない
コードが動いている」こととも、「コードにはあるがmigration未適用」の
いずれとも矛盾しない（後者の場合は起動時エラーになりやすいため、前者の
可能性がより高いと考えられる）。**確定にはRenderのmigration実行ログが
必要**であり、この点はMother Ship確認へ委ねる。

---

## Phase 6 — Frontend Deploy Governance（判断しない、論点整理のみ）

- `infra/README.md`は`main`を前提に書かれているが、Vercel実態は`develop`。
  意図した設計か、単なる文書の未更新かは、設定した本人（Mother Ship）で
  なければ判断できない
- 現状、PRブランチ＝Preview、`develop` push＝Productionという構成
- `main`はVercelから見て実質的に参照されていない可能性が高い
- Backendについても、今回`main`相当（Knowledge機能なし）のコードが動いて
  いることが確認できたため、Frontend（develop相当の最新コード）とBackend
  （Knowledge機能を持たない古いコード）が**実際に乖離した状態で本番運用
  されている可能性がある**。これは技術的リスクとして記録するに留め、
  対応方針は決定しない

## Phase 7 — infra/README Drift

Backend Deploy Branch名自体は未確定のため、本Phaseでは`infra/README.md`の
更新候補を作成しない。ただし、「Backend productionには現時点でKnowledge
機能が存在しない」という事実は、Phase 8の前提として確定した。

## Phase 8 — Knowledge Production Readiness再評価

**`KNOWLEDGE_SCHEMA_PRODUCTION_MISSING`**

Backend production の実際に稼働中のAPIスキーマを直接確認した結果に基づき
確定する。Deploy branch名の特定（`main`か別ブランチか）は未確定のまま
残るが、「Knowledge機能自体がproductionに存在しない」という、本Audit
シリーズが一貫して問うてきた核心の問いには、直接証拠に基づき回答できた。

## Phase 9 — Knowledge Data Reproduction

Phase 8で`KNOWLEDGE_SCHEMA_PRODUCTION_MISSING`が確定したため、着手する
前提条件を満たさない。Schemaがproductionへ配備されるまで、本Phaseは
未着手のままとする。

---

## Phase 10 — Final Matrix

| Item | State |
|---|---|
| Frontend production branch | **develop**（確認済み） |
| Backend production branch名 | **TBD**（Mother Ship確認待ち。ただし機能面の帰結は確定済み） |
| Backend service state | **正常応答（今回確認）**。前回503は`SERVICE_SLEEPING`が有力 |
| Backend deployed SHA | **TBD** |
| Production Knowledge schema | **存在しない（`KNOWLEDGE_SCHEMA_PRODUCTION_MISSING`、直接確認済み）** |
| Knowledge data reproducibility | `PARTIALLY_REPRODUCIBLE`（変更なし） |
| Batch 8 | **PAUSED** |
| Score refinement | **PAUSED** |
| Source UI | **PAUSED** |
| PER_FACT_RENDERING | **PAUSED** |
| Ranking Explainability | **PAUSED** |

---

## Phase 11 — Final Classification

| 候補 | 判定 |
|---|---|
| `PRODUCTION_REALITY_CONFIRMED` | **不採用**。Deploy branch名の特定は未完了 |
| `FRONTEND_DEPLOY_DOC_DRIFT_CONFIRMED` | **採用**。Vercel実態とdocsの食い違いを直接確認済み |
| `BACKEND_DEPLOY_BRANCH_CONFIRMED` | **不採用**。branch名自体はMother Ship確認待ち |
| `BACKEND_SERVICE_OUTAGE_CONFIRMED` | **不採用に変更**。現在は正常応答しており、継続的なoutageではなく`SERVICE_SLEEPING`が有力（確定にはRenderログが必要） |
| `KNOWLEDGE_SCHEMA_PRODUCTION_READY` | **不採用** |
| **`KNOWLEDGE_SCHEMA_PRODUCTION_MISSING`** | **採用**。稼働中のAPIスキーマを直接確認した結果に基づく |
| `RELEASE_GAP_CRITICAL` | **採用**。Backend/Frontend間のコード乖離が実在することが確認できたため（branch名の特定は不要、機能面の乖離自体が根拠） |
| `KNOWLEDGE_IMPORT_FOUNDATION_REQUIRED` | **採用**。Schema自体が存在しない以上、Import基盤の設計はSchema配備より後の課題として明確に位置づけられる |

**最終確定分類: `FRONTEND_DEPLOY_DOC_DRIFT_CONFIRMED` + `KNOWLEDGE_SCHEMA_
PRODUCTION_MISSING` + `RELEASE_GAP_CRITICAL` + `KNOWLEDGE_IMPORT_FOUNDATION_
REQUIRED`。**

---

## Repository Changes

- `docs/audit/production-reality-mother-ship-handoff.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Migration/DB書き込み/Render設定/Vercel設定: すべて変更なし）

## Phase 12 — Stop

以下へは一切進んでいない。

- Batch 8
- production DB write
- Render設定変更
- Vercel branch変更
- develop→main merge
- migration実行
- Knowledge import
- Score/Ranking変更

## Mother Shipへの依頼事項（まとめ、更新版）

1. RenderダッシュボードでBackendの実際のDeploy branch名・Auto-Deploy設定・
   Latest deploy SHAを確認してほしい（**Knowledge機能が無いこと自体は
   本Auditで確認済みのため、緊急性は下がったが、正確なbranch名の特定は
   今後のRelease Strategy検討に必要**）
2. Backendが一時的に503を返していた原因（Free tier自動スリープと推測される
   が、確定にはRender Eventsログが必要）を確認してほしい
3. `develop`のbranch protection設定と、Vercel/RenderのProduction Branch設定
   （特にBackend側）が「意図した設計」か「意図しないdrift」かを教えてほしい
4. `KNOWLEDGE_SCHEMA_PRODUCTION_MISSING`が確定した今、Batch 1-7で蓄積した
   41社分のKnowledgeデータをどう本番へ載せるか（Release Strategy Candidates
   A-D、`docs/audit/knowledge-production-readiness-audit.md` Phase 4参照）を
   検討するタイミングかどうかの判断
