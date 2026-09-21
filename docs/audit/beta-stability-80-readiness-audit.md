> **Status: Active Tracking（Phase 1 / Audit Contract）**
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

現時点で確定しているPhase Scopeは以下のとおりとする。

| Phase | 確定内容 | 出典 |
| --- | --- | --- |
| Phase 0 | 監査条件の凍結・Entry Gate契約の整備（本書） | 本タスク |
| Phase 1 | Core Journey Stability Audit。§3.8のMain E2E Flowを監査baselineとして使用する | 既存`Beta Core Flow E2E Audit` / §3.8 |
| Phase 2 | signup挙動の監査 | Mother Ship決定 |
| Phase 4 | Shrine Data validation（監査対象ジャーニーで遭遇したデータに限定） | 本タスク指示 |

Phase 3のScopeは**未定義**である。推測で定義しない。
---

## 3. 凍結した監査条件（Frozen Audit Conditions）

凍結時刻における値を記録する。以降のPhaseは本節の条件下でのみ実行する。条件を変更する場合は、本書を更新し、変更前後のBUG記録を区別する。

### 3.1 Audit Revision History

| Revision | SHA | Status | Scope |
| --- | --- | --- | --- |
| `R0` | `f4a77443061fbb229a326d6c190cac01a6e1f81d` | `HISTORICAL / SUPERSEDED` | Phase 0 baseline |
| `R1` | `73f60f36ef314f1dba833aa4a2575645339391f5` | `ACTIVE` | Phase 1 Entry Gate以降 |

#### R1 Freeze Rule

- `R0`のSHA・Evidenceは履歴として保持し、上書きしない
- Phase 1用branchを作成する直前に最新`origin/develop`を確認する
- その時点のSHAを`R1`へ記録し、Statusを`ACTIVE`へ変更する
- 既存BUG-IDは振り直さない
- 各BUG記録は`Audit Revision`と`Observed SHA`で更新前後を区別する
- 旧RevisionのEvidenceは書き換えない

#### R1 Freeze Record

| 項目 | 値 |
| --- | --- |
| Base branch | `develop` |
| Frozen SHA | `73f60f36ef314f1dba833aa4a2575645339391f5` |
| Commit subject | `fix(recommendation): remove culture translation from primary authority tier (#2901)` |
| Freeze date | 2026-09-21 |
| Phase 1 branch | `audit/beta-stability-phase1-entry-gate-v2` |

`R1`は上記SHAで凍結済みであり、以降のPhase 1観測はこのRevisionを基準とする。
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

#### `US-AUTH` — 認証済みユーザー（Free tier） / Auth Contract v2

| 項目 | 凍結内容 |
| --- | --- |
| 定義 | 通常のLogin Flowを通過し、`GET /api/users/me/`が`200`と有効なuserを返し、`AuthProvider`が`authenticated`状態となった利用者 |
| 課金状態 | Free tier。`BILLING_STUB_PLAN=free` / `BILLING_STUB_ACTIVE=0`をbaselineとする（§3.3） |
| 認証経路 | Login Form → `AuthProvider.login` → `POST /api/auth/login`（BFF） → Django JWT endpoint → access / refresh tokenをHttpOnly Cookieへ保存 → `GET /api/users/me/`でidentityを確認 |
| Frontend identity確定条件 | `/api/users/me/`が`200`を返し、有効なuserを取得できた場合のみ`authenticated`として扱う |
| `authenticated` | `/me = 200 + valid user`。FrontendはLogged-inとして扱い、logged-in markerを保持・復元する |
| `unauthenticated` | `/me = 401`。session無効が確定したものとしてGuestへ遷移し、logged-in markerを削除する |
| `indeterminate` | `/me`の5xx / network failure / response parse failure等。認証状態を確定せず`unknown`として扱い、logged-in markerは保持する |
| Fail-closed UI | `indeterminate`中は`isLoggedIn=false`として認証済みUIを表示しない。ただしsession失効とは判定しない |
| Recovery | `indeterminate`後の`refreshMe()`または再mountで`/me`が成功した場合、`authenticated`へ復旧できる |
| Logged-in marker | `localStorage`上のmarkerは「`/me`を問い合わせるべき可能性がある」というhintであり、認証identityの正本ではない |
| Token Refresh | Access Token失効時のrefreshはBFFが担当する。Frontend ComponentはRefresh Tokenを直接扱わない |
| Refresh判定 | Backend `401`のみrefresh retry対象とする。`403`は認可結果としてrefreshしない |
| Identity isolation | Refresh処理はrefresh token単位で分離し、異なるuser間でaccess token結果を共有しない |
| 根拠 | `docs/core/authentication-flow.md`、関連するAuth実装およびRegression Test |
| アカウント要件 | 既存のlocalアカウント / `is_active=True` / Free tier |
| アカウント選定手順 | `make auth-users`で既存localアカウントを確認し、監査実行者が1件を選択する |
| ログイン不能時の回復手順 | 必要な場合のみ既存local accountのpasswordを通常の開発手順で再設定する。認証バイパスとして扱わない |
| ログイン方法 | アプリケーションの通常ログイン画面`/auth/login`からのみ行う |
| 禁止事項 | 認証バイパス、テスト専用Login route追加、Cookie手動注入、JWT / tokenのFrontend直接読取、認証情報の文書・commit・PRへの記録 |
| 記録してよいもの | `VERIFIED: YES/NO`、検証日、Audit Revision、Observed SHA、HTTP status、Auth状態遷移 |
| 記録してはならないもの | username / email / password / access token / refresh token / Cookie値 |
| 検証状態 | `RUNTIME_REVALIDATION_REQUIRED`（§3.9）。現行Audit Revisionのlocal runtimeで実測後に`RESOLVED / VERIFIED`へ変更する |

signup（新規登録）挙動そのものはPhase 2の監査対象とし、Phase 1 Entry Gateで`US-AUTH`を成立させるための認証手段には使用しない。
### 3.8 Phase 1 Core Journey Audit Baseline

Phase 1では、既存の`Beta Core Flow E2E Audit`で使用されたMain E2E Flowを
監査上のCore Journey baselineとして使用する。

これは新しいProduct Specificationを定義するものではない。
本書では、既存監査で実際に使用されたJourneyを
Beta Stability Auditの再現可能な観測経路として採用する。

#### Main E2E Flow

```text
Home
→ Concierge Input
→ Recommendation
→ Shrine Detail
→ Route / Save
→ Auth Return
→ Premium State
```

#### Phase 1で扱うRoute / Domain

| Journey Segment | 主な対象 |
| --- | --- |
| Home | HomeからConciergeへのentry |
| Concierge Input | 相談入力・送信 |
| Recommendation | 推薦結果表示 |
| Shrine Detail | 神社詳細表示 |
| Route | 経路導線 |
| Save | Favorite / 保存操作 |
| Auth Return | Guest → Login → 元の内部Routeへの復帰 |
| Premium State | Free / Premium境界の表示・導線 |

#### User State適用

- `US-GUEST`で再現可能なJourney Segmentは、§10のGuest Gateが`READY`であれば観測を開始できる
- `US-AUTH`を必要とするJourney Segmentは、`UNRES-01`解消後に観測する
- Guest → Auth Returnの途中で`US-AUTH`成立が必要になった場合、その地点で観測を停止し、Gate解消後に再開する

#### Scope Boundary

Phase 1では以下を評価しない。

- Recommendation ranking / scoring品質
- Recommendation意味ロジックの妥当性
- Shrine Seed全体の品質
- Database schema
- Production環境
- Signup機能そのもの（Phase 2）
- Coordinate Audit / Seed pipeline

Phase 1で観測するのは、
上記Core Journeyを通過した際の機能安定性・表示・遷移・認証境界・エラー挙動に限定する。

既存`Beta Core Flow E2E Audit`は本節の監査baselineの出典であり、
Current Source of Truthそのものではない。

---
### 3.9 UNRESOLVED条件

| ID | 条件 | 状態 | 理由 | 解消条件 |
| --- | --- | --- | --- | --- |
| `UNRES-01` | Phase 1で使用する`US-AUTH` local Free userが、現行Audit Revision上で通常Login Flowを通り、`/api/users/me/`の`200 + valid user`によって`authenticated`へ到達できること | **RUNTIME_REVALIDATION_REQUIRED** | Auth Contract自体は現行実装・Regression Testで確認済みだが、Phase 1監査で使用するlocal runtime / local accountについては新Audit Revision上でまだ実測していない | local環境で既存`is_active=True`のFree userを1件選択し、`/auth/login`から通常ログインする。Login成功後に`GET /api/users/me/`が`200`と有効なuserを返し、Frontendが`authenticated`となることを確認する。さらにpage reload後も同一identityとして復元されることを確認する。完了後、本項目を`RESOLVED / VERIFIED`へ変更する |

#### UNRES-01 実測時の必須確認

- Loginはアプリケーションの通常`/auth/login`経路から行う
- Cookie手動注入・認証バイパス・テスト専用Login routeは使用しない
- `/api/users/me/`が`200`と有効なuserを返すこと
- `AuthProvider`が`authenticated`として扱うこと
- page reload後も同一user identityとして復元できること
- 課金状態はFree baselineのままとする
- username / email / password / token / Cookie値は監査文書・commit・PRへ記録しない
- 記録するのは`VERIFIED: YES/NO`、検証日、Audit Revision、Observed SHAのみとする

#### Auth Contract v2で既に固定済みのため、UNRES-01には含めない項目

以下は現行実装およびRegression TestでContractが固定されており、
`US-AUTH` runtime accountの存在確認とは分離する。

- `/me = 401`のみを`unauthenticated`としてGuestへ遷移させる
- `/me = 5xx`をGuest確定として扱わない
- network failureをGuest確定として扱わない
- response parse failureをGuest確定として扱わない
- indeterminate時にlogged-in markerを保持する
- 一時失敗後の`refreshMe()`でauthenticatedへ復旧できる
- reload後の再試行でauthenticatedへ復旧できる
- access token refreshをBFF側で処理する
- refresh retryは401のみとし、403では実行しない
- refresh処理をuser identity間で共有しない

`UNRES-01`が未解消の間は、Phase 1における
`US-AUTH`実ブラウザ観測を開始しない。
`US-GUEST`のみで観測可能な項目については、
`UNRES-01`を理由に停止する必要はない。
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

Phase 1では§3.8のCore Journey baselineに対して、`P0` / `P1`の「Core Journey」基準を適用する。

§3.8のbaseline外にあるRouteや機能については、Core Journey影響を推測で拡張しない。Evidenceに裏付けられる場合のみ`Suspected Scope`へ記録する。

---

## 7. Bug Record Contract

### 7.1 フィールド定義

| フィールド | 必須 | 内容 |
| --- | --- | --- |
| `BUG-ID` | 必須 | §4の形式 |
| `Audit Revision` | 必須 | 観測時のAudit Revision（`R0` / `R1` / ...） |
| `Observed SHA` | 必須 | 観測対象となった正確なcommit SHA |
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
Audit Revision:     R0 | R1 | ...
Observed SHA:
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

### 10.1 Gate方針

Phase 1 Entry Gateは、`US-GUEST`と`US-AUTH`を分離して判定する。

`UNRES-01`は`US-AUTH`のlocal runtime再検証に限定された条件であり、
未解消であることだけを理由に`US-GUEST`で再現可能な観測まで停止しない。

Gate状態は以下の3つを使用する。

| Gate Status | 意味 |
| --- | --- |
| `READY` | 必要な監査条件が成立し、対象User StateでPhase 1観測を開始できる |
| `BLOCKED` | 対象User Stateに必要な未解決条件があり、観測を開始しない |
| `NOT_APPLICABLE` | 当該条件が対象User Stateの観測に関係しない |

### 10.2 共通条件

| # | 条件 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 1 | Audit Revision方式とR1 Freeze Ruleが定義されている | PASS | §3.1 |
| 2 | Target environmentが記録されている | PASS | §3.2 / §3.3 |
| 3 | Browser baselineが記録されている | PASS | §3.5 |
| 4 | 375 / 390 / 430のviewport条件が記録されている | PASS | §3.6 |
| 5 | `US-GUEST`の状態契約が定義されている | PASS | §3.7 |
| 6 | `US-AUTH`のAuth Contract v2が定義されている | PASS | §3.7 |
| 7 | BUG-ID形式が固定されている | PASS | §4 |
| 8 | `BUG` / `SPEC` / `DATA` / `UX`の定義が固定されている | PASS | §5 |
| 9 | `P0`〜`P4`の定義が固定されている | PASS | §6 |
| 10 | Bug record templateが固定されている | PASS | §7.1 / §7.2 |
| 11 | Evidence要件が固定されている | PASS | §7.3 |
| 12 | STOP条件が固定されている | PASS | §9 |

`R1`の実SHAは§3.1で凍結済みである。

### 10.3 User State別判定

#### `US-GUEST`

| 条件 | 判定 | 根拠 |
| --- | --- | --- |
| Guest開始状態を再現できる | READY | §3.7 `US-GUEST` |
| Guest判定条件が固定されている | READY | `/api/users/me/ = 401` |
| Guest観測を妨げる未解決条件が存在しない | READY | §3.9 |
| `UNRES-01` | `NOT_APPLICABLE` | `UNRES-01`は`US-AUTH` runtime revalidationに限定される |

**`US-GUEST` Gate: READY**

`US-GUEST`のみで再現可能なPhase 1観測は開始してよい。

#### `US-AUTH`

| 条件 | 判定 | 根拠 |
| --- | --- | --- |
| Auth Contract v2が定義されている | READY | §3.7 |
| `/me`の状態分類とRecovery Contractが固定されている | READY | §3.7 |
| Token Refresh / Identity isolation Contractが固定されている | READY | §3.7 |
| 現行Audit Revisionのlocal Free userで通常Login Flowを実測済み | BLOCKED | `UNRES-01`（§3.9） |
| Login後`/me = 200 + valid user`を実測済み | BLOCKED | `UNRES-01`（§3.9） |
| page reload後の同一identity復元を実測済み | BLOCKED | `UNRES-01`（§3.9） |

**`US-AUTH` Gate: BLOCKED**

`UNRES-01`を`RESOLVED / VERIFIED`へ変更するまで、
`US-AUTH`を前提とするPhase 1実ブラウザ観測は開始しない。

### 10.4 結論

Phase 1 Entry GateはUser Stateごとに以下の状態とする。

```text
US-GUEST : READY
US-AUTH  : BLOCKED — UNRES-01 runtime revalidation待ち
```

したがって、Phase 1全体を`NOT READY`として停止する旧判定は廃止する。

`US-GUEST`のみで完結する観測は開始可能とする。

認証状態、Auth Return、保存操作、My Page等、
`US-AUTH`成立を必要とする観測は`UNRES-01`解消後に開始する。

`UNRES-01`解消時は§3.9と本§10を同一PRで更新し、
`US-AUTH Gate`を`READY`へ変更する。
---

## 11. Phase Status

| Phase | 内容 | 状態 |
| --- | --- | --- |
| Phase 0 | 監査条件の凍結・Entry Gate契約の整備 | **完了**（`R1`を凍結しPhase 1へ移行） |
| Phase 1 | Core Journey Stability Audit（§3.8） | `US-GUEST`: `READY` / `US-AUTH`: `UNRES-01`により`BLOCKED` |
| Phase 2 | signup挙動の監査 | 未着手 |
| Phase 3 | 未定義（§2.3） | 未着手 |
| Phase 4 | Shrine Data validation（ジャーニー経由で遭遇したデータに限定） | 未着手 |
---

## 12. 本書の位置づけと更新ルール

- 本書はAudit契約であり、Current Source of Truthではない（`FR-HIST-02`）
- 本書は製品仕様・Recommendation契約・DB設計・Analytics契約を定義しない
- `docs/audit/README.md`は主要3 audit chainのみのnavigationであり、個別audit文書の内容・Status・追加を管理しない。本書の追加に伴う同READMEの更新は行っていない
- §3の凍結条件を変更する場合、本書を更新し、変更前後のBUG記録を区別する
- 新しいAudit Revisionを凍結する場合、Revision History・該当Entry Gate・Phase Statusを同一PRで同期する
- `UNRES-01`等の未解決条件を解消した場合、§3.9と§10を同一PRで更新する
- 本書へ認証情報・個人情報・正確な位置情報・secret値を記載しない

## 関連ドキュメント

- `docs/core/fixed-rules.md`（横断Fixed Rules）
- `docs/core/authentication-flow.md`（認証アーキテクチャの正本）
- `docs/core/auth-flow.md`（認証導線のReference）
- `docs/ops/guest-data-retention.md`（匿名Ownerの扱い）
- `docs/audit/production-critical-journey-qa.md`（Production向けCritical Journey QAの先例。本監査の正本ではない）
- `docs/audit/production-environment-configuration-verification.md`（Production環境検証の先例。本監査の正本ではない）
