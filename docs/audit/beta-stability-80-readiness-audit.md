> **Status: Active Tracking（Phase 0 / Audit Contract）**
>
> 本ドキュメントは、KAMI MUSUBI Beta Stability 80% Readiness Auditの**監査条件契約**である。監査結果ではない。
>
> 本書はCurrent Source of Truthではない。製品仕様・Recommendation契約・DB設計・Analytics契約を新たに定義しない（`FR-HIST-02`）。現在仕様は`docs/core/` / `docs/product/` / `docs/knowledge/` / `docs/analytics/`のActive正本を参照する。
>
> 本書に認証情報（username / password / token / cookie値）、個人情報および正確な位置情報を記録しない。

# Beta Stability 80% Readiness Audit

## 1. 監査の目的

Beta公開に耐える安定性が満たされているかを、**再現可能な条件下で**観測し、記録する。

本監査は次の2点のみを責務とする。

1. 事象を検出し、再現条件とともに記録すること
2. 記録した事象を分類し、Beta影響度で優先度を付けること

本監査は次を責務としない。

- 不具合の修正
- 仕様の決定
- Recommendationの品質改善
- Shrine Dataの整備

修正が必要な場合は、監査とは独立した修正タスクを起票する。監査タスク内で修正を行わない。

---

## 2. Scope

### 2.1 本監査が扱うもの

- 監査対象ジャーニーを通じて到達できるRoute上の挙動
- Guest状態および認証済み状態での挙動
- 375 / 390 / 430 のモバイルviewportにおける表示・操作
- 監査対象ジャーニーを通じて遭遇したShrine Data（Phase 4）

### 2.2 本監査が扱わないもの

- Recommendation ranking / scoring / 意味づけロジックの評価と変更
- Database schemaの評価と変更
- Shrine Seed dataの一括整備・広域cleanup
- Coordinate Audit / Seed pipeline（別監査の責務）
- Production環境の挙動（本Phase 0はLocal環境をbaselineとして凍結する）
- Production設定・Production dataの参照および変更

### 2.3 Phaseの割り当て

Phase番号ごとのScopeは本Phase 0では確定していない。現時点で確定しているのは以下のみである。

| Phase | 確定内容 | 出典 |
| --- | --- | --- |
| Phase 0 | 監査条件の凍結（本書） | 本タスク |
| Phase 2 | signup挙動の監査 | Mother Ship決定 |
| Phase 4 | Shrine Data validation（監査対象ジャーニーで遭遇したデータに限定） | 本タスク指示 |

Phase 1・Phase 3のScopeは**未定義**である。推測で定義しない。

---

## 3. 凍結した監査条件（Frozen Audit Conditions）

凍結時刻における値を記録する。以降のPhaseは本節の条件下でのみ実行する。条件を変更する場合は、本書を更新し、変更前後のBUG記録を区別する。

### 3.1 Revision

| 項目 | 値 |
| --- | --- |
| 監査Commit SHA | `f4a77443061fbb229a326d6c190cac01a6e1f81d` |
| Commit subject | `fix: 新規登録後の正規化済みユーザー名で自動ログインする (#2850)` |
| Commit date | 2026-09-15 10:43:50 +0900 |
| Base branch | `develop` |
| 凍結時の`origin/develop` | `f4a77443061fbb229a326d6c190cac01a6e1f81d`（監査SHAと同一） |
| 監査branch | `audit/beta-stability-80-readiness` |
| 監査branchの分岐元 | `origin/develop`（上記SHA） |

Phase 1以降で`develop`が進んでも、監査対象は上記SHAに固定する。SHAを更新する場合は本書を更新し、更新前後のBUG記録を区別する。

### 3.2 Target Environment

**Local development environment**をbaselineとする。Production環境はbaselineとしない。

| Layer | 値 | Repository上の根拠 |
| --- | --- | --- |
| Frontend | Next.js dev server / `http://localhost:3000` | `README.md`「アクセスURL」、`apps/web/playwright.config.ts`（`PLAYWRIGHT_BASE_URL`既定値） |
| Frontend → Backend経路 | Next.js BFF経由のみ。FrontendはDjangoへ直接通信しない | `docs/core/authentication-flow.md`、`FR-SEC-01` |
| Frontend API base | `/api`（同一origin。BFF Route Handler） | `apps/web/src/lib/api.ts:2` |
| BFF → Backend origin | `http://127.0.0.1:8000`（`DJANGO_ORIGIN`または`BACKEND_ORIGIN`で上書き可。既定値を使用する） | `apps/web/src/lib/server/backend.ts:6` |
| Backend | Django runserver / `127.0.0.1:8000` | `README.md`「セットアップ手順 / Backend」 |
| Django settings module | `shrine_project.settings` | `Makefile` |
| Database | PostgreSQL + PostGIS（`postgis/postgis:16-3.4-alpine`） / port `5432` / DB `jinja_db` / user `admin` | `docker-compose.db.yml`、`docker-compose.yml` |
| DB password | 環境変数`POSTGRES_PASSWORD`。**値は本書に記録しない** | `docker-compose.db.yml` |

Production URL（Vercel / Render）は本監査では**使用しない**。

### 3.3 Backend起動条件（再現に必須）

以下の環境変数条件を凍結する。既定値と異なる起動を行うとBeta実挙動が変わるため、**`make dev`は本監査では使用しない**。

| 環境変数 | 監査時の値 | 根拠 / 備考 |
| --- | --- | --- |
| `DEBUG` | 既定値`True`（local） | `backend/shrine_project/settings.py:109` |
| `CONCIERGE_USE_LLM` | `0`（LLM OFF） | `backend/shrine_project/settings.py:114`（既定`False`）。`README.md`も既定OFFと記載 |
| `BILLING_PROVIDER` | 既定値`stub` | `backend/temples/services/billing_state.py:27` |
| `BILLING_STUB_PLAN` | `free` | `backend/temples/services/billing_state.py:32`（既定`free`） |
| `BILLING_STUB_ACTIVE` | `0` | `backend/temples/services/billing_state.py:33`（既定`0`） |
| `DISABLE_THROTTLE` | 設定しない（既定`0`＝throttle有効） | `backend/shrine_project/settings.py:351`。throttleはBeta実挙動の一部であるため無効化しない |
| `ALLOWED_HOSTS` | 既定値`localhost,127.0.0.1,web` | `backend/shrine_project/settings.py:414` |
| `CORS_ALLOWED_ORIGINS` | 既定値（`http://localhost:3000`を含む） | `backend/shrine_project/settings.py:443` |

#### `make dev`を使用しない理由

`Makefile`の`dev` targetは`BILLING_STUB_PLAN=premium BILLING_STUB_ACTIVE=1`を設定する（`Makefile:11-13`）。これはFree / Premium境界を暗黙にPremium側へ倒すため、Guest / 認証済みFreeの観測が再現不能になる。本監査ではREADMEに記載されたFree起動形を使用する。

```bash
BILLING_STUB_PLAN=free BILLING_STUB_ACTIVE=0 \
  python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

Premium状態の観測が必要になった場合は、**そのBUG記録のPreconditionsへ明示的に記載**する。無記載の記録はすべてFree条件下の観測として扱う。

### 3.4 Shrine Data状態

| 項目 | 凍結内容 |
| --- | --- |
| DB状態 | `python manage.py migrate`適用済み |
| Seed投入経路 | `make seed-representative`（source: `backend/temples/seed/representative_shrines.yaml`） |
| Shrine件数 | **本書では固定しない。** Phase 1開始時に実測して記録する（Historical Snapshotとして扱う。`FR-HIST-01`） |

Seed dataの改変は禁止する（§8）。

### 3.5 Browser Baseline

| 項目 | 値 |
| --- | --- |
| Browser family | **Chrome-family** |
| 実体 | Chromium（Playwright `devices["Desktop Chrome"]`系。`apps/web/playwright.config.ts`の`chromium` project） |
| Browser名・version | Phase 1開始時に実測して記録する |
| 対象外 | `webkit` project は本監査のbaselineとしない |

Chrome-family以外のbrowserでのみ再現する事象は、本監査のScope外として記録し、Priorityを付与しない。

### 3.6 Mobile Viewport Baseline

| ID | Width (CSS px) | Height (CSS px) | deviceScaleFactor | touch |
| --- | --- | --- | --- | --- |
| `VP-375` | 375 | 812 | 2 | 有効 |
| `VP-390` | 390 | 844 | 2 | 有効 |
| `VP-430` | 430 | 932 | 2 | 有効 |

- Repository内に先例があるのは`375×812`のみである（`docs/audit/production-critical-journey-qa.md` §8）。`VP-390` / `VP-430`は本監査で新規に凍結する値である。
- Chromiumの`isMobile`を有効にする（meta viewport解釈を実機モバイルWebへ合わせるため）。
- `apps/web/playwright.config.ts`にモバイルviewport projectは**存在しない**。本監査のviewport条件はPlaywright configに依存せず、本書を正本とする。config追加は本監査のScope外である。

### 3.7 User States

#### `US-GUEST` — Guest（未ログイン）

| 項目 | 凍結内容 |
| --- | --- |
| 定義 | 認証Cookieを持たない利用者。匿名Ownerとして`anonymous_id`で識別される |
| 開始条件 | Cookie / `localStorage` / `sessionStorage`をクリアした新規セッション |
| 判定 | `GET /api/users/me/` → `401` |
| 想定される利用範囲 | 相談・閲覧は可能。保存操作から認証を要求する |
| 根拠 | `docs/core/auth-flow.md`、`docs/ops/guest-data-retention.md` |

#### `US-AUTH` — 認証済みユーザー（Free tier）

| 項目 | 凍結内容 |
| --- | --- |
| 定義 | 通常のログインフローでセッションを確立した利用者。課金状態はFree |
| 認証経路 | Login Form → `AuthProvider.login` → `POST /api/auth/login`（BFF） → Django `/api/auth/jwt/create/` → access / refresh tokenをHttpOnly Cookieへ保存 |
| 根拠 | `docs/core/authentication-flow.md` |
| アカウント要件 | 既存のlocalアカウントであること / `is_active=True` / 課金状態Free（§3.3） |
| アカウント選定手順 | `make auth-users`で既存localアカウントを列挙し、監査実行者が1件を選択する（`Makefile:199-203`） |
| ログイン不能時の回復手順 | `make auth-reset-pass AUTH_USER=<user> AUTH_PASS=<pass>`（`Makefile:205-215`）。これは既存アカウントのパスワード再設定であり、認証バイパスではない |
| ログイン方法 | アプリケーションの通常ログイン画面（`/auth/login`）からのみ行う |
| 禁止事項 | 認証バイパスの作成、テスト専用ログイン経路の追加、Cookieの手動注入、認証情報の文書・commit・PRへの記載 |
| 記録してよいもの | 再現可能な認証**手段**と、必要な**アカウント状態**のみ |
| 記録してはならないもの | username / email / password / token / cookie値 |
| **検証状態** | **UNRESOLVED**（§3.9） |

signup（新規登録）挙動そのものはPhase 2の監査対象であり、本Phase 0では認証手段として使用しない（Mother Ship決定）。

### 3.8 監査対象Route（Phase 1以降で確定する）

本Phase 0ではRoute一覧を確定しない。`apps/web/src/app`配下に41のpage routeが存在するが、どれをBeta Core Journeyとするかは**製品判断**であり、Phase 0の責務外である。

- Repository内に`Core Journey`の定義文書は存在しない（`docs/`配下に該当記述なし）
- 近接する先例は`docs/audit/production-critical-journey-qa.md`のJourney A / B / C / Dのみであり、これはProduction向けのCritical Journey QAであってBeta Core Journeyの正本ではない

Core Journeyの確定が必要になった時点で、§9のSTOP条件（製品仕様判断）に該当する。

### 3.9 UNRESOLVED条件

| ID | 条件 | 状態 | 理由 | 解消手順 |
| --- | --- | --- | --- | --- |
| `UNRES-01` | `US-AUTH`で使用する既存local test userの実在と、通常ログイン成立の検証 | **UNRESOLVED** | 本Phase 0の実行環境にlocal runtimeが存在しないため検証不能。Docker daemon利用不可、PostgreSQL `127.0.0.1:5432`未起動、Python venv（`.venv`）不在 | ローカル環境で `make auth-users` を実行し`is_active=True`のアカウントが1件以上存在することを確認する。次に`/auth/login`から通常ログインが成立し`GET /api/users/me/`が`200`を返すことを確認する。確認できたら本表を`RESOLVED`へ更新する（**アカウント識別子と認証情報は記録しない**。「検証済み: YES」「検証日」のみ記録する） |

`UNRES-01`が未解消の間、認証済みユーザーを前提とする観測は再現不能である。

---

## 4. BUG-ID Format

```text
BETA-NNN
```

| 規則 | 内容 |
| --- | --- |
| 接頭辞 | `BETA-`固定 |
| 連番 | `NNN` = 3桁ゼロ埋め。`001`から昇順 |
| 採番単位 | 本監査全体で通し。Phaseをまたいでも番号を分けない |
| Phaseの表現 | BUG-ID内ではなく、記録の`Phase`フィールドで表す |
| ID再利用 | 禁止。取り下げた場合も欠番のまま残す |
| 999超過時 | 4桁へ拡張する（`BETA-1000`）。既存の3桁IDは変更しない |

例: `BETA-001`、`BETA-042`

---

## 5. Bug Classification

すべての事象は、以下4分類の**いずれか1つ**をprimary categoryとして持つ。複数分類を同時に付与しない。判断できない場合は`SPEC`とする。

| 分類 | 定義 |
| --- | --- |
| `BUG` | 現在の実装が、確立された仕様または期待される技術的挙動どおりに動作していない |
| `SPEC` | 期待される挙動が不明確、矛盾している、または製品判断を要する |
| `DATA` | 問題の起点が、神社データ・コンテンツ・座標・metadata等の保存済みデータにあり、アプリケーション挙動ではない |
| `UX` | 技術的には動作しているが、使いやすさ・可読性・操作・提示に問題がある |

### 分類ルール

- `SPEC`または`DATA`を、根拠なく実装バグ（`BUG`）へ変換しない
- 「確立された仕様」とは、Current Source of Truth・実装・テストのいずれかに実在する記述を指す。監査者の期待を仕様として扱わない
- 文書・実装・テストが食い違う場合、どれか1つを推測で正しいものとして扱わない。`SPEC`として記録し、§9のSTOP条件を評価する（`FR-GOV-01`）

---

## 6. Priority Levels

優先度は**Beta影響度**で決める。実装難易度で決めない。

| Priority | 基準 |
| --- | --- |
| `P0` | データの破壊または破損 / 重大なセキュリティ障害 / Core Journeyの完全な遮断 |
| `P1` | 主要なBeta機能が使用不能 / 認証の遮断 / 実用的な回避策のないCore Journey失敗 |
| `P2` | 実用的な回避策のある、重大または部分的な機能欠陥 |
| `P3` | UX / UI欠陥 / 軽微な挙動の不整合 / 遮断を伴わない機能上の問題 |
| `P4` | 表層的な問題 / 改善機会 / 遮断を伴わないpolish |

Core Journeyが未確定である間（§3.8）、`P0` / `P1`の「Core Journey」基準は適用できない。該当しうる事象は、Core Journey確定待ちである旨を`Suspected Scope`へ記載し、Priorityを暫定値として記録する。

---

## 7. Bug Record Contract

### 7.1 フィールド定義

| フィールド | 必須 | 内容 |
| --- | --- | --- |
| `BUG-ID` | 必須 | §4の形式 |
| `Phase` | 必須 | 検出したPhase番号 |
| `Route` | 必須 | 検出したRoute（例: `/shrines/[id]`）。Route外の場合は`N/A`と理由 |
| `User State` | 必須 | `US-GUEST` / `US-AUTH` |
| `Viewport` | 必須 | `VP-375` / `VP-390` / `VP-430` / `desktop` |
| `Classification` | 必須 | `BUG` / `SPEC` / `DATA` / `UX`のいずれか1つ |
| `Priority` | 必須 | `P0`〜`P4` |
| `Preconditions` | 必須 | 再現に必要な事前状態。§3.3と異なる起動条件を使った場合は必ず明記 |
| `Reproduction Steps` | 必須 | 決定的な手順。番号付き。「時々」「たまに」等の非決定的記述を含めない |
| `Expected` | 必須 | 期待される挙動。`Actual`と**分けて**記述する |
| `Actual` | 必須 | 実際に観測された挙動。`Expected`と**分けて**記述する |
| `Evidence` | 必須 | 観測の根拠（§7.3） |
| `Reproducibility` | 必須 | `ALWAYS` / `INTERMITTENT` / `ONCE` / `NOT_REPRODUCED` |
| `Suspected Scope` | 任意 | 影響範囲の推定。**Evidenceに裏付けられる場合のみ**記載する |
| `Workaround` | 必須 | 実用的な回避策。無い場合は`NONE` |
| `Root Cause` | 必須 | 判明していない場合は`UNKNOWN`。**推測を書かない** |
| `Status` | 必須 | §7.4。初期値は`OPEN` |

### 7.2 記録テンプレート

```text
BUG-ID:            BETA-000
Phase:
Route:
User State:        US-GUEST | US-AUTH
Viewport:          VP-375 | VP-390 | VP-430 | desktop
Classification:    BUG | SPEC | DATA | UX
Priority:          P0 | P1 | P2 | P3 | P4
Preconditions:
Reproduction Steps:
  1.
  2.
  3.
Expected:
Actual:
Evidence:
Reproducibility:   ALWAYS | INTERMITTENT | ONCE | NOT_REPRODUCED
Suspected Scope:
Workaround:        NONE
Root Cause:        UNKNOWN
Status:            OPEN
```

`BETA-000`はテンプレート検証用のplaceholderであり、実在のBUG記録ではない。実記録は`BETA-001`から採番する。

### 7.3 Evidence要件

`Evidence`は「何が観測されたか」を特定できるものとする。「なぜそうなったか」は`Root Cause`の領域であり、`Evidence`へ書かない。

#### 許容するEvidence

- 画面上の可視テキスト（引用）
- DOM上の識別子（`data-testid`等）
- HTTP status codeとrequest path
- Browser Consoleのエラー出力
- Networkの失敗リクエスト
- スクリーンショット（下記の禁止事項に抵触しないもの）

#### Evidenceへ含めてはならないもの

- 認証情報（username / password / token / cookie値）
- 個人情報
- 正確な位置情報
- secret値

この境界は`docs/audit/production-critical-journey-qa.md`の先例および`FR-SEC-03`に従う。

#### Evidenceに関する禁止事項

- 推測をEvidenceとして記載しない
- 観測していない挙動をEvidenceとして記載しない
- Evidenceの無い`Suspected Scope`を記載しない

### 7.4 Status語彙

| Status | 意味 |
| --- | --- |
| `OPEN` | 検出済み。未対応。**初期値** |
| `FIX_TASK_CREATED` | 独立した修正タスクを起票済み |
| `FIXED_VERIFIED` | 修正タスク完了後、本監査の凍結条件下で再検証し解消を確認 |
| `STOP_MOTHER_SHIP` | §9のSTOP条件に該当。Mother Ship判断待ち |
| `WONT_FIX` | Beta範囲では対応しないと判断 |
| `NOT_A_BUG` | 再検証の結果、事象が成立しなかった |

---

## 8. Audit Workflow

1. 事象を検出する
2. BUG-IDを採番する（§4）
3. 再現条件を凍結する（§3の条件 + `Preconditions`）
4. `Expected`と`Actual`を分けて記録する
5. `BUG` / `SPEC` / `DATA` / `UX`へ分類する（§5）
6. `P0`〜`P4`を付与する（§6）
7. `Suspected Scope`は、Evidenceに裏付けられる場合のみ記載する
8. 実装が必要な場合、**独立した修正タスク**を起票する
9. **監査タスク内で修正を行わない**
10. 修正タスクが独立に完了した後にのみ、監査を再開する

監査と実装は分離したまま維持する。

### 禁止する変更（Prohibited Changes）

監査中に以下を行わない。

- 新規プロダクト機能の追加
- Recommendation rankingの変更
- Recommendation scoringの変更
- recommendation meaning logicの変更
- Database schemaの変更
- Shrine Seed dataの変更
- Production dataの変更
- Production configurationの変更
- プロダクト挙動の再設計
- 不明確な仕様を仮定で解決すること
- 監査中の不具合修正
- Shrine dataの広域cleanup

Phase 4のShrine Data validationは、監査対象ジャーニーを通じて遭遇したデータに限定する。Coordinate Audit / Seed pipelineは本監査のScope外である。

---

## 9. STOP Conditions

### 9.1 Mother Ship STOP条件

以下のいずれかを要する所見が出た場合、監査を停止し、Mother Shipへ報告する。推測で判断を確定しない。

- 製品仕様の判断
- Recommendation rankingの変更
- Recommendation scoringの変更
- Database設計 / schemaの判断
- Production dataの変更
- Production configurationの変更
- 破壊的migration
- セキュリティアーキテクチャの変更
- 競合する正本仕様の解決

該当する記録は`Status: STOP_MOTHER_SHIP`とする。

### 9.2 監査側のSTOP条件

以下の場合、当該Phaseの観測を停止する。

- §3で凍結した条件が成立しなくなった場合（環境が起動しない、SHAが変わった等）。条件を復旧してから再開する
- `UNRES-01`が未解消のまま、認証済みユーザーを前提とする観測へ到達した場合
- `P0`に該当する事象を検出した場合、当該ジャーニーの継続観測を停止し、独立した修正タスクを起票する（他ジャーニーの観測は継続してよい）

`P0`検出時も、監査タスク内での修正は行わない。

---

## 10. Phase 1 Entry Gate

### 10.1 判定

| # | 条件 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 1 | 監査Commit SHAが凍結されている | PASS | §3.1 |
| 2 | Target environmentが記録されている | PASS | §3.2 / §3.3 |
| 3 | Browser baselineが記録されている | PASS | §3.5 |
| 4 | 375 / 390 / 430のviewport条件が記録されている | PASS | §3.6 |
| 5 | Guest / 認証済みユーザー状態が定義されている | PASS | §3.7 |
| 6 | BUG-ID形式が固定されている | PASS | §4 |
| 7 | `BUG` / `SPEC` / `DATA` / `UX`の定義が固定されている | PASS | §5 |
| 8 | `P0`〜`P4`の定義が固定されている | PASS | §6 |
| 9 | Bug record templateが固定されている | PASS | §7.1 / §7.2 |
| 10 | Evidence要件が固定されている | PASS | §7.3 |
| 11 | STOP条件が固定されている | PASS | §9 |
| 12 | 再現可能なテストを妨げる未解決のPhase 0条件が存在しない | **FAIL** | `UNRES-01`（§3.9） |

### 10.2 結論

Phase 1 Entry Gateの判定は **NOT READY** である。

`UNRES-01`（既存local test userの実在とログイン成立が未検証）が、認証済みユーザーを前提とする観測の再現性を妨げている。

- `UNRES-01`を解消するまでPhase 1を開始しない
- `US-GUEST`のみを対象とする観測についても、条件12を満たさない状態でのPhase 1開始は行わない

---

## 11. Phase Status

| Phase | 内容 | 状態 |
| --- | --- | --- |
| Phase 0 | 監査条件の凍結 | **完了（`UNRES-01`をUNRESOLVEDとして記録）** |
| Phase 1 | 未定義（§2.3） | 未着手 / Gate NOT READY |
| Phase 2 | signup挙動の監査 | 未着手 |
| Phase 3 | 未定義（§2.3） | 未着手 |
| Phase 4 | Shrine Data validation（ジャーニー経由で遭遇したデータに限定） | 未着手 |

---

## 12. 本書の位置づけと更新ルール

- 本書はAudit契約であり、Current Source of Truthではない（`FR-HIST-02`）
- 本書は製品仕様・Recommendation契約・DB設計・Analytics契約を定義しない
- `docs/audit/README.md`は主要3 audit chainのみのnavigationであり、個別audit文書の内容・Status・追加を管理しない。本書の追加に伴う同READMEの更新は行っていない
- §3の凍結条件を変更する場合、本書を更新し、変更前後のBUG記録を区別する
- `UNRES-01`等の未解決条件を解消した場合、§3.9と§10を同一PRで更新する
- 本書へ認証情報・個人情報・正確な位置情報・secret値を記載しない

## 関連ドキュメント

- `docs/core/fixed-rules.md`（横断Fixed Rules）
- `docs/core/authentication-flow.md`（認証アーキテクチャの正本）
- `docs/core/auth-flow.md`（認証導線のReference）
- `docs/ops/guest-data-retention.md`（匿名Ownerの扱い）
- `docs/audit/production-critical-journey-qa.md`（Production向けCritical Journey QAの先例。本監査の正本ではない）
- `docs/audit/production-environment-configuration-verification.md`（Production環境検証の先例。本監査の正本ではない）
