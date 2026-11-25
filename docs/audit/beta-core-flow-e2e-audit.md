> **Status: Audit Result（読み取り専用の観測記録）**
>
> 本ドキュメントは KAMI MUSUBI の Main E2E Flow（`Home → Concierge Input → Recommendation → Shrine Detail → Route / Save → Auth Return → Premium State`）に対する**監査結果**である。
>
> 本書は Current Source of Truth ではない。製品仕様・Recommendation 契約・API Schema・Analytics 契約を新たに定義しない。現在仕様は `docs/core/` / `docs/product/` / `docs/analytics/` の Active 正本を参照する。
>
> 本監査では**修正を行わない**。Recommendation Score / Ranking、Meaning Translation、API Response Schema、Analytics Event 名、Production Data、環境設定のいずれにも変更を加えていない。
>
> 本書に認証情報（username / password / token / cookie 値）、個人情報、正確な位置情報を記録しない。

# Beta Core Flow E2E Audit

## 0. 監査メタデータ

| 項目 | 値 |
| --- | --- |
| Base commit SHA | `6c94cdb5e61756186c2f3c1fc6180ed3d449c35b`（`origin/develop` HEAD / `Fix/w0 db02 sapporo suwa position (#2855)`） |
| 監査日 | 2026-09-16 |
| Working tree | 監査開始時点で clean（`git status --short` 出力なし） |
| 同一スコープの既存 branch | なし（`git ls-remote --heads origin` に `audit/beta-core-flow-stability` は存在しない） |
| 同一スコープの既存 open PR | なし（open PR 12 件はすべて Dependabot） |
| 追加したファイル | `docs/audit/beta-core-flow-e2e-audit.md`、`apps/web/src/lib/server/__tests__/bffFetch.audit.test.ts`（証拠用テストのみ） |

### 0.1 Branch に関する申し送り

タスク指示の branch 名は `audit/beta-core-flow-stability` だが、本セッションに与えられた
designated branch は `claude/tender-davinci-9wrj4u` である。designated branch 以外への push は
明示許可なしには行わない規約のため、本監査は `claude/tender-davinci-9wrj4u` 上で作業している。
branch 名を `audit/beta-core-flow-stability` に揃える必要がある場合は、PR の head branch を
差し替えるだけでよい（内容差分はない）。

---

## 1. 監査対象（inspected files / domains）

### Frontend / Next.js BFF（`apps/web`）

- Entry: `src/app/page.tsx`、`src/features/home/HomePage.tsx`、`src/features/home/components/{HomeMainClient,HomeHero,HomeHeroConsultationInput,HomeActionGrid}.tsx`
- Concierge: `src/app/concierge/{page,layout,ConciergeClientFull}.tsx`、`src/app/concierge/full/page.tsx`、`src/features/concierge/{hooks.ts,buildConciergeRequestPayload.ts,detailHref.ts}`、`src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- Recommendation → Detail: `src/lib/nav/{buildShrineHref,buildShrineResolveHref,login,returnTo}.ts`、`src/app/shrines/[id]/page.tsx`、`src/app/shrines/resolve/page.tsx`、`src/components/shrine/{ShrineDetailShell,ShrineSaveButton,ShrineDetailViewTracker,ConciergeShrineCard}.tsx`、`src/components/shrine/detail/ShrineDetailArticle.tsx`、`src/components/shrines/ShrineConciergeCard.tsx`
- Auth: `middleware.ts`、`src/lib/auth/{AuthProvider.tsx,actionGuards.ts,withAuth.tsx}`、`src/app/{login,signup}/*`、`src/app/auth/{login,register}/page.tsx`、`src/app/api/auth/{login,logout,register}/route.ts`、`src/app/api/users/me/route.ts`、`src/app/api/me/route.ts`
- Save / Favorite: `src/hooks/useFavorite.ts`、`src/lib/api/favorites.ts`、`src/lib/api/favorites.server.ts`、`src/lib/server/favorites.server.ts`、`src/app/api/favorites/{route.ts,[id]/route.ts,preload/route.ts}`、`src/app/favorites/*`
- Billing / Premium: `src/app/billing/{page,upgrade,success,cancel,manage}/*`、`src/app/api/billings/{status,checkout,portal}/route.ts`、`src/lib/api/billing{,.server}.ts`、`src/features/billing/hooks/useBilling.ts`、`src/lib/premium/{accessLevel,cardVisibility}.ts`
- Route / Map: `src/lib/maps/destinationContract.ts`、`src/components/shrine/GoogleMapRouteLink.tsx`（呼び出し境界）、`src/app/api/shrines/nearby/route.ts`
- BFF 共通基盤: `src/lib/server/{bffFetch.ts,backend.ts,resolveServerBaseUrl.ts,logging.ts}`、`src/lib/api/{client.ts,http.ts}`
- Analytics: `src/lib/analytics/{track.ts,cardEvents.ts,searchEvents.ts,directionEvents.ts,billing.ts}`
- Debug 境界: `src/app/debug/**`、`src/app/api/concierge/score-v3/dashboard/route.ts`

### Backend（`backend`）

- `temples/api_views_concierge.py`（public response 境界 / `_debug` 除去 / thread 永続化 / quota consume）
- `temples/api/views/concierge.py`（Thread List / Detail の所有権判定）
- `temples/api/views/score_v3_dashboard.py` + `temples/tests/api/test_score_v3_dashboard_api.py`
- `temples/api/urls.py`、`shrine_project/settings.py`（JWT 設定の有無）、`users/api/auth.py`

---

## 2. 実行した検証（tests executed and results）

| 対象 | コマンド | 結果 |
| --- | --- | --- |
| Web contract tests | `pnpm --filter ./apps/web test:contract` | **PASS** — 207 files / 1667 tests passed（本監査で追加した 2 test を含む）, 114.35s |
| Type check | `npx tsc -p apps/web/tsconfig.json --noEmit` | **PASS**（exit 0） |
| Lint（repo root） | `npx eslint . --cache --cache-location .eslintcache` | **PASS**（exit 0） |
| Lint（apps/web） | `apps/web` で `npx eslint . --cache --cache-location .eslintcache` | **PASS**（exit 0） |
| 証拠用テスト | `npx vitest run src/lib/server/__tests__/bffFetch.audit.test.ts` | **PASS** — 2/2（E2E-001 / E2E-002 の再現を固定） |
| Whitespace | `git diff --check` | **clean** |
| Backend focused tests | `python -m pytest temples/tests/api/test_score_v3_dashboard_api.py users/tests/test_login_throttling.py` | **実行不能（環境要因）** — `django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library`。本監査コンテナに GDAL / PostGIS が無く、`apt-get install libgdal-dev` も upstream 404 で失敗した。backend 側の到達点は実装読解と既存テストの assertion 内容で確認した（§6 参照）。 |

### 2.1 本監査と無関係な既存失敗（pre-existing / 修正しない）

- `pnpm --filter ./apps/web guard:no-next-public-in-server` が **base commit 時点で FAIL** する。
  - 実測: `rg -n "NEXT_PUBLIC_" src/lib/server src/app/api` →
    `src/app/api/billings/status/route.ts:18: const forcedPlan = process.env.NEXT_PUBLIC_FORCE_BILLING_PLAN;`
  - `.github/workflows/web-tests.yml` の `web-full` job 最終ステップがこの guard を実行する。
    直近の develop push は `apps/web/**` を触っていないため path filter で web-ci が起動しておらず、
    失敗が顕在化していないだけである。次に web を触る PR で赤くなる。
  - 本監査では修正しない。fix PR 境界は §8 の `PR-F` を参照。

---

## 3. Findings（P0）

### E2E-001

| Field | 内容 |
| --- | --- |
| **ID** | E2E-001 |
| **Severity** | **P0** |
| **Status** | **CONFIRMED** |
| **Flow** | 任意の認証済み Flow（`/mypage`、`/favorites`、Shrine Detail SSR、`/api/users/me/`、`/api/favorites/` など `bffFetchWithAuthFromReq` を通る全経路） |
| **Reproduction** | 1. ユーザー A とユーザー B が、同一 Next.js server instance に対してほぼ同時にリクエストする。2. 双方の `access_token` が失効済み（または不在）で `refresh_token` が有効。3. A のリクエストが先に `refreshAccessViaBackendMutex()` に入り、backend の `/api/auth/jwt/refresh/` 応答待ちになる。4. その待機中に B が同じ関数に入る。→ 決定的再現テスト: `apps/web/src/lib/server/__tests__/bffFetch.audit.test.ts` の `E2E-001`。 |
| **Expected** | 各リクエストは自分の `refresh_token` で発行された access token のみを受け取り、自分の access token のみを Set-Cookie される。 |
| **Actual** | `refreshInFlight` は module scope の単一 Promise で、**refresh token をキーにしていない**。B は A の in-flight Promise をそのまま受け取り、(a) B の upstream リクエストが `Authorization: Bearer <A の access token>` で送信され、(b) B のブラウザに `Set-Cookie: access_token=<A の access token>` が書き込まれる。以後 B は A として振る舞う。 |
| **Root cause** | `apps/web/src/lib/server/bffFetch.ts:34-44`（`let refreshInFlight` / `refreshAccessViaBackendMutex(refresh)` が引数 `refresh` を無視して in-flight Promise を返す）と `:196-203`（`tokenToSet` を無条件に `access_token` cookie へ書く） |
| **Evidence** | 追加テスト `bffFetch.audit.test.ts::E2E-001` が PASS。backend refresh 呼び出しは 1 回のみ、その body は `{"refresh":"REFRESH_USER_A"}`。B 側 upstream の `Authorization` に `Bearer ACCESS_FOR_USER_A` が現れ、B のレスポンス `set-cookie` に `access_token=ACCESS_FOR_USER_A` が含まれる。 |
| **Impact** | **auth / data**。セッション横断（アカウント乗っ取り相当）。Favorite・Concierge Thread・Goshuin・Billing を含む全ての認証済みデータが他ユーザーへ露出しうる。 |
| **Fix scope** | `apps/web/src/lib/server/bffFetch.ts` のみ（in-flight map を refresh token でキー化する、または dedup を廃止する）。API schema・Analytics・Ranking に影響しない。 |
| **Suggested owner** | Codex（単一ファイルの限定的修正） |
| **Separate PR** | `PR-A: fix(bff) — scope the token-refresh in-flight dedup per refresh token` |

> **成立条件の注記**: 1 つの server instance が複数リクエストを並行処理していることが前提である。
> 本番は Vercel（`docs/audit/production-environment-configuration-verification.md` §8）で、
> Node.js ランタイムの Next.js route handler は 1 instance 内で並行実行される。
> さらに E2E-011（access token の実寿命 5 分）により refresh は「1 時間に 1 回」ではなく
> **ほぼ全リクエストで発生**するため、衝突窓は理論値ではなく実用上の頻度になる。

---

## 4. Findings（P1）

### E2E-002

| Field | 内容 |
| --- | --- |
| **ID** | E2E-002 |
| **Severity** | **P1** |
| **Status** | **CONFIRMED** |
| **Flow** | Auth Return 以降の全 Flow（token refresh が発生したすべてのレスポンス） |
| **Reproduction** | 1. ログインする（`/api/auth/login` は production かつ https のとき `secure: true` で cookie を発行する）。2. access token が失効するまで待つ。3. 任意の BFF API（`/api/users/me/`、`/api/favorites/` 等）を叩く。4. レスポンスの `Set-Cookie: access_token=...` に `Secure` が無い。→ 決定的再現テスト: `bffFetch.audit.test.ts::E2E-002`。 |
| **Expected** | refresh 後に再発行する cookie は、ログイン時と同じ属性（production/https では `Secure`）で書かれる。 |
| **Actual** | `bffFetch.ts:198-203` と `api/concierge/chat/route.ts:54-71` は `httpOnly` / `sameSite` / `path` / `maxAge` のみを指定し `secure` を省略する。初回ログイン時に `Secure` だった cookie が、最初の refresh で **`Secure` なしに降格**する。 |
| **Root cause** | `apps/web/src/lib/server/bffFetch.ts:198-203`、`apps/web/src/app/api/concierge/chat/route.ts:54-71`。`apps/web/src/app/api/auth/login/route.ts:117-139` の `isSecureCookie(req)` 判定が共有されていない。 |
| **Evidence** | 追加テスト `bffFetch.audit.test.ts::E2E-002` が PASS（`set-cookie` に `HttpOnly` はあるが `secure` が無いことを固定）。 |
| **Impact** | **auth / security**。平文 HTTP リクエストが同一ドメインに発生した場合にセッション cookie が漏出しうる。HSTS preload が有効（同 §8）なため実害は限定されるが、cookie 属性の契約破れであることに変わりはない。 |
| **Fix scope** | `apps/web/src/lib/server/bffFetch.ts`、`apps/web/src/app/api/concierge/chat/route.ts`、`apps/web/src/app/api/auth/login/route.ts`（`isSecureCookie` を共通 helper へ切り出す） |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-A`（E2E-001 と同じ cookie 書き込み箇所のため同一 PR が妥当） |

### E2E-003

| Field | 内容 |
| --- | --- |
| **ID** | E2E-003 |
| **Severity** | **P1** |
| **Status** | **CONFIRMED** |
| **Flow** | `Guest → 保護アクション → /auth/login → 新規登録 → /auth/register → 登録成功 → 元の遷移先` |
| **Reproduction** | 1. Guest で `/shrines/49` を開き「ログインしてあとで見返す」を押す。2. `/auth/login?returnTo=/shrines/49` → 「新規登録はこちら」→ `/auth/register?returnTo=/shrines/49`。3. 登録を完了する。4. `/shrines/49` に戻る。5. ヘッダーが「ログイン」のまま。`/concierge` に遷移すると Recommendation Hero の保存ボタンが Guest 表示になり、押すと再びログイン画面へ飛ばされる。 |
| **Expected** | 登録直後のユーザーは全ページでログイン済みとして扱われる。 |
| **Actual** | `SignupForm` は `AuthProvider.login()` ではなく `@/lib/api/auth` の `login()` を直接呼ぶ（`SignupForm.tsx:5,102-107`）。`AuthProvider` の `markLoggedIn()`（`localStorage["auth:logged_in"]`）は `AuthProvider.login()` 内でしか実行されないため、登録経路ではフラグが立たない。`shouldAutoFetchMe()` は `/`・`/shrines/*`・`/concierge*` で `false` を返すので `/api/users/me/` も叩かれず、`AuthProvider` は `status: "guest"` に確定する。 |
| **Root cause** | `apps/web/src/app/signup/SignupForm.tsx:102-107`、`apps/web/src/lib/api/auth.ts:8-20`、`apps/web/src/lib/auth/AuthProvider.tsx:26-32,77-96,120-145` |
| **Evidence** | `markLoggedIn()` の呼び出し箇所は `AuthProvider.tsx:167` のみ（`grep -rn "markLoggedIn" apps/web/src` で他に無い）。`SignupForm` は `AuthProvider` を import していない。 |
| **Impact** | **auth / user**。新規登録直後という最も離脱しやすい地点で、認証済みユーザーが Guest UI を見せられ、保存操作でログイン画面に戻される。Shrine Detail の保存ボタンだけは server 由来の `guestMode` を受け取るため正しく動く（`shrines/[id]/page.tsx:316,562`）が、ヘッダーと Concierge Hero は client 判定のため誤る。 |
| **Fix scope** | `apps/web/src/app/signup/SignupForm.tsx`（`AuthProvider.login()` 経由に統一）、または `AuthProvider` 側でフラグ管理を `lib/api/auth` に寄せる |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-B: fix(auth) — make client auth state authoritative after register / transient /me failure` |

### E2E-004

| Field | 内容 |
| --- | --- |
| **ID** | E2E-004 |
| **Severity** | **P1** |
| **Status** | **CONFIRMED** |
| **Flow** | 任意のページ →（`/api/users/me/` が一時的に失敗）→ `/`・`/shrines/*`・`/concierge*` |
| **Reproduction** | 1. ログイン済みで `/mypage` を開く（`localStorage["auth:logged_in"]="1"`）。2. `/api/users/me/` が 1 度でも非 401 の失敗（5xx / network error）を返す。3. `fetchMe()` の catch が `markLoggedOut()` を実行し、フラグが消える。4. `/concierge` へ遷移する。5. `shouldAutoFetchMe("/concierge")` が `false`、`maybeLoggedIn()` も `false` なので `/api/users/me/` は二度と呼ばれず、`status: "guest"` で固定される。 |
| **Expected** | 一時的な `/me` 失敗は次のページ遷移で回復する。ログイン済みユーザーが Guest 表示に固着しない。 |
| **Actual** | `/`・`/shrines/*`・`/concierge*` は auto-fetch 対象外で、かつ唯一の回復手段である localStorage フラグが失敗時に消される。Concierge Result の Hero 保存ボタンは `guestMode` prop を受け取らないため `!loading && !isLoggedIn` で Guest と判定され（`ConciergeSectionsRenderer.tsx:1101-1108`）、押下で 401 → ログイン画面へリダイレクトされる。`accessLevel` も `"anonymous"` になり、Analytics が誤った access level で送出される。 |
| **Root cause** | `apps/web/src/lib/auth/AuthProvider.tsx:56-74`（`fetchMe` の catch が `markLoggedOut`）、`:77-96`（`shouldAutoFetchMe` の除外リスト）、`:120-145`（`shouldFetch = auto \|\| maybe`） |
| **Evidence** | `AuthProvider.tsx:89-96` の分岐。なお `:94` の `if (pathname.startsWith("/concierge/full")) return true;` は直前の `:92` で `/concierge/` が既に `false` を返すため**到達しない dead branch** であり、この除外リストが意図どおり機能していないことの傍証になる。 |
| **Impact** | **auth / user / observability**。認証済み Free ユーザーが Guest として扱われ、Save 導線が破壊され、`accessLevel` を含む Analytics が汚染される。 |
| **Fix scope** | `apps/web/src/lib/auth/AuthProvider.tsx`（回復可能な失敗で `markLoggedOut` しない / SSR 由来の初期認証状態を注入する）、`apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`（server 由来 `guestMode` を Hero の `ShrineSaveButton` へ渡す） |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-B`（E2E-003 と同根） |

### E2E-005

| Field | 内容 |
| --- | --- |
| **ID** | E2E-005 |
| **Severity** | **P1** |
| **Status** | **CONFIRMED** |
| **Flow** | `Recommendation → Shrine Detail`（存在しない / 削除済み shrine ID への直接アクセス） |
| **Reproduction** | 1. `GET /api/shrines/999999/data` を叩く（backend は 404 を返す）。2. BFF のレスポンスが `502` で、body に `{"error":"upstream_failed","status":404,"upstream":"<backend origin>/api/shrines/999999/data/","body":"..."}` が入る。 |
| **Expected** | 存在しない shrine は 404 として伝播する。内部 backend origin をクライアントへ返さない。 |
| **Actual** | upstream が 2xx 以外のとき一律 `502` を返し、`upstream: upstream.url`（= `DJANGO_ORIGIN` を含む完全 URL）と upstream body 1000 文字をそのまま body に載せる。 |
| **Root cause** | `apps/web/src/app/api/shrines/[id]/data/route.ts:26-34`（および `:48-51` の `invalid_json` 分岐も同様に `upstream` を返す）。同じ「upstream の非 2xx を一律 502 に丸める」パターンは `apps/web/src/app/api/shrines/nearby/route.ts:20-25` にもあるが、そちらは `upstream.url` を返さない |
| **Evidence** | 同ファイルのソース。対照として `docs/audit/production-environment-configuration-verification.md` §10 は「client JS bundle 内の `jinja-backend.onrender.com` 出現数 0」を成果として記録しているが、この route は**実行時に**同じ origin を返す。 |
| **Impact** | **user / observability / 情報開示**。(a) 404 が 5xx に化けるため監視ノイズと誤アラートを生む。(b) BFF 境界の目的である backend origin 隠蔽が破れる。 |
| **Fix scope** | `apps/web/src/app/api/shrines/[id]/data/route.ts`（upstream status を保持し、`upstream` / `body` を server log 側へ移す） |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-C: fix(bff) — preserve upstream status and stop echoing backend origin in error bodies` |

---

## 5. Findings（P2）

### E2E-006 — Shrine Detail の `accessLevel` が Guest を `free` と誤送出する

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Recommendation → Shrine Detail`（Guest） |
| **Reproduction** | Guest で `/shrines/49` を開く。card 系 Analytics（`card_view` 等）の `accessLevel` が `"free"` で送出される。 |
| **Expected** | Guest は `"anonymous"`。 |
| **Actual** | `resolveAccessLevel({...}, true)` と第 2 引数を `true` 固定にしているため、`isAuthenticated` が常に真になる。 |
| **Root cause** | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx:558-564` |
| **Evidence** | 同ファイル `:312` は同じ画面内で `accessLevel: isGuestUser ? "anonymous" : "free"` と正しく分岐しており、内部で矛盾している。`src/lib/premium/cardVisibility.ts` の `saved_record` は `anonymous: "hidden"` / `free: "visible"` だが、Shrine Detail では `savedRecordVisibility` を `"visible"` にハードコード（`:568`）しているため、表示自体は現状変わらない。 |
| **Impact** | **observability**。Guest / Free のファネル分離が Shrine Detail で不能。Premium 転換率の分母が汚染される。表示ゲートへの影響は現時点では無い。 |
| **Fix scope** | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-D: fix(analytics) — report the real access level on Shrine Detail` |

### E2E-007 — `/api/favorites/by-shrine/:id` の BFF route が存在しない

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Save / Favorite`（pk 不明時の解除フォールバック） |
| **Reproduction** | `useFavorite` に `initial: { fav: true, favorite_id: null }` を渡し、解除する。`DELETE /api/favorites/by-shrine/<id>/` が発行され、Next.js に該当 route が無いため 404（HTML）になり、`toggle()` が throw して UI が保存済みに巻き戻る。 |
| **Expected** | pk 不明時のフォールバックが機能する、または経路自体を持たない。 |
| **Actual** | `apps/web/src/app/api/favorites/` 配下は `route.ts` / `[id]/route.ts` / `preload/route.ts` のみ。`by-shrine` は 2 セグメント深いため `[id]` にもマッチしない。 |
| **Root cause** | `apps/web/src/lib/api/favorites.ts:70-72`（`api.delete("/favorites/by-shrine/<id>/")`）に対応する BFF route 不在。`apps/web/src/hooks/useFavorite.ts:92` が唯一の呼び出し元。 |
| **Evidence** | route tree（`find apps/web/src/app/api/favorites -name route.ts`）。既存テスト `src/lib/api/__tests__/favorites.branch.test.ts:69` は axios 呼び出しの URL のみを assert しており、route の存在は検証していない。 |
| **Impact** | **user（限定的）**。本番 Main Flow からの到達は現状なし。`favorite_id: null` を渡す唯一の実コンポーネントは `ShrineConciergeCard.tsx:181` で、これは `ConciergeShrineCard` 経由で `/debug/concierge-fixture` からのみ描画される（E2E-008 参照）。Shrine Detail は `favorite_id` を server から供給する。潜在バグ + 技術的負債。 |
| **Fix scope** | `apps/web/src/lib/api/favorites.ts` / `apps/web/src/hooks/useFavorite.ts`（フォールバックを削除するか BFF route を追加） |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-E: chore(favorites) — remove or implement the by-shrine unsave fallback` |

### E2E-008 — Debug route の gate が一貫していない

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | 直接 URL アクセス |
| **Reproduction** | production build で `/debug/concierge-fixture` および `/debug/location` を開く。表示される。 |
| **Expected** | `/debug/**` は `NEXT_PUBLIC_ENABLE_DEBUG_PAGES` で一律に閉じる。 |
| **Actual** | `debug/score-v3-dashboard/page.tsx` と `debug/concierge/page.tsx` は `if (process.env.NEXT_PUBLIC_ENABLE_DEBUG_PAGES !== "1") notFound();` を持つが、`debug/concierge-fixture/page.tsx` と `debug/location/page.tsx` は gate を持たない。`concierge-fixture` は fixture として `score_element` / `score_need` / `score_popular` / `score_total` / `weights` / `matched_need_tags` という内部 scoring フィールド名を含むコードを公開ページに載せる。 |
| **Root cause** | `apps/web/src/app/debug/concierge-fixture/page.tsx:1-`、`apps/web/src/app/debug/location/page.tsx:1-` |
| **Evidence** | 4 ファイルの先頭比較。 |
| **Impact** | **user / 情報開示（低）**。公開されるのは実データではなく固定 fixture だが、Recommendation 内部契約の形と項目名が露出する。`/debug/location` は Geolocation 取得ボタンを無条件に公開する。 |
| **Fix scope** | `apps/web/src/app/debug/**` |
| **Suggested owner** | config / Codex |
| **Separate PR** | `PR-F: chore(debug) — gate every /debug route behind NEXT_PUBLIC_ENABLE_DEBUG_PAGES` |

### E2E-009 — `/api/concierge/chat/` が常に top-level `_debug` を返す

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Concierge Input → Recommendation` |
| **Reproduction** | 任意の相談を送信し、レスポンス body を見る。`_debug: { rid, before, after, applied, flow, mode }` が常に含まれる。 |
| **Expected** | pipeline 内部の候補件数・適用フィルタ・内部 flow ラベルは public response に出さない（あるいは env / 権限で gate する）。 |
| **Actual** | `data._debug`（生の相談文を含む service 層 payload）は public 境界で正しく除去される（`api_views_concierge.py:298-303`）が、**top-level `_debug` は無条件に付与される**（`:1005-1012` で常に dict を渡し、`:329-330` で body に載せる）。 |
| **Root cause** | `backend/temples/api_views_concierge.py:329-330, 1005-1012` |
| **Evidence** | 同ファイルのソース。`debug=None` を渡す分岐は `:650`（limit reached 経路）のみ。 |
| **Impact** | **observability / 情報開示（低）**。候補プールの before/after 件数と内部 flow 名が全クライアントに露出する。score 本体は露出しない。 |
| **Fix scope** | `backend/temples/api_views_concierge.py`（**API response schema を変更するため、削除ではなく gate 化の可否を製品判断として先に確定すること**） |
| **Suggested owner** | Mother Ship（契約判断）→ Codex（実装） |
| **Separate PR** | `PR-G: chore(concierge) — gate the top-level _debug payload`（契約決定後） |

### E2E-010 — 座標欠損時の経路案内 fallback 文言が描画されない

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Shrine Detail → Route`（座標が無効な神社） |
| **Reproduction** | `latitude` / `longitude` が無効な神社の詳細を開く。「操作」セクションから経路案内 CTA が消えるだけで、理由の説明が一切出ない。 |
| **Expected** | 呼び出し側が渡している説明文（「神社情報が見つからなかったため、経路案内を表示できません。」等）が表示される。 |
| **Actual** | `ShrineDetailShell` は `googleDirFallbackText` を prop として受けるが、`googleDirFallbackText: _googleDirFallbackText` と意図的に未使用化しており、**どこにも描画しない**。 |
| **Root cause** | `apps/web/src/components/shrine/ShrineDetailShell.tsx:28,52` |
| **Evidence** | `grep -rn "googleDirFallbackText" apps/web/src` → 定義 2 箇所と呼び出し 2 箇所（`shrines/[id]/page.tsx:275`、`shrines/[id]/goshuins/page.tsx:63`）のみ。描画箇所なし。 |
| **Impact** | **UX**。座標欠損は「安全に失敗」しているが（`toValidDestinationCoords` が捏造しない点は正しい）、ユーザーには無言で CTA が消える。 |
| **Fix scope** | `apps/web/src/components/shrine/ShrineDetailShell.tsx` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-H: fix(shrine-detail) — render the route-unavailable explanation` |

### E2E-011 — JWT 実寿命と cookie `maxAge` の不一致（`SIMPLE_JWT` 未設定）

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | Auth Return / セッション継続全般 |
| **Reproduction** | `grep -rn "SIMPLE_JWT\|ACCESS_TOKEN_LIFETIME" backend/` → **0 件**。`djangorestframework_simplejwt==5.5.1` の既定値は access 5 分 / refresh 1 日。一方 BFF は access cookie `maxAge = 60*60`、refresh cookie `maxAge = 60*60*24*7` を設定する。 |
| **Expected** | cookie 寿命とトークン寿命が整合し、cookie の存在がセッション有効性の近似として使える。 |
| **Actual** | access は 12 倍、refresh は 7 倍のズレ。結果として (a) 5 分経過後はほぼ全ての SSR / BFF リクエストで backend refresh 往復が 1 回増える、(b) `middleware.ts` の `/mypage` gate と `hasAuthContext()`（`lib/server/favorites.server.ts:12-15`）は cookie の**存在**しか見ないため、死んだトークンでも「認証あり」と判定する。 |
| **Root cause** | `backend/shrine_project/settings.py`（`SIMPLE_JWT` 定義なし）、`apps/web/src/app/api/auth/login/route.ts:126-139`、`apps/web/src/lib/server/bffFetch.ts:196-203` |
| **Evidence** | 上記 grep 結果と `requirements.txt:16`。 |
| **Impact** | **auth / performance / observability**。単体では graceful に縮退する（refresh 失敗 → 401 → `guestMode: true`）が、**E2E-001 の衝突窓を常時化させる増幅要因**である。 |
| **Fix scope** | `backend/shrine_project/settings.py`（明示的な `SIMPLE_JWT`）と BFF の cookie `maxAge`。**環境設定の変更を伴うため単独 PR で慎重に扱うこと。** |
| **Suggested owner** | Mother Ship（寿命ポリシー決定）→ config |
| **Separate PR** | `PR-I: chore(auth) — pin JWT lifetimes and align cookie maxAge` |

### E2E-012 — BFF の path セグメントが一部で未エンコード

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **SUSPECTED** |
| **Flow** | `/api/concierge-threads/[id]`、`/api/my/goshuins/[id]` |
| **Reproduction（要 runtime 確認）** | `GET /api/concierge-threads/..%2F..%2Fusers%2Fme/` のようにエンコードされた `..` を含む segment を送る。Next.js が param をデコードして渡すと `upstreamPath = "/api/concierge-threads/../../users/me/"` となり、`new URL()` / `fetch` の正規化で `/users/me/` へ折り畳まれ、BFF が意図しない backend endpoint を中継する。 |
| **Expected** | すべての動的 segment を `encodeURIComponent` する。 |
| **Actual** | `apps/web/src/app/api/concierge-threads/[id]/route.ts:9` と `apps/web/src/app/api/my/goshuins/[id]/route.ts:23,37` のみ未エンコード。同種の全 route（`favorites/[id]`, `shrines/[id]/data`, `shrines/[id]/meaning`, `shrines/[id]/visit`, `shrines/[id]/reflection`）は `encodeURIComponent` 済み。 |
| **Root cause** | 上記 2 ファイル |
| **Evidence** | `grep -rn 'bffFetchWithAuthFromReq(req, \`\|upstreamPath = \`' apps/web/src/app/api` の結果比較。 |
| **Impact** | **auth / security（限定的）**。中継されるのは呼び出し元自身の資格情報なので権限昇格は起きないが、BFF が公開する endpoint 面を越える。Next.js が `%2F` を含む segment をどう扱うかの runtime 確認が必要なため **SUSPECTED**。 |
| **Fix scope** | 上記 2 ファイル |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-C`（同じ BFF 堅牢化のため統合可） |

### E2E-013 — `/api/auth/login` が upstream の status と body をクライアントへ返す

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | Auth |
| **Reproduction** | 誤った資格情報でログインする。レスポンス body に `{"detail":"Login failed","upstreamStatus":401,"upstreamBody":"<Django の生 body 1000 文字>"}` が返る。 |
| **Expected** | クライアントには汎用エラーのみ。upstream 詳細は server log に留める。 |
| **Actual** | `apps/web/src/app/api/auth/login/route.ts:103-106` が `upstreamStatus` と `upstreamBody.slice(0,1000)` を body に含める。 |
| **Root cause** | 同上 |
| **Evidence** | 同ファイルのソース。既存テスト `route.test.ts` はこの分岐の body を assert していない。 |
| **Impact** | **security（低）/ observability**。Django のエラー形式・フィールド名が露出する。`DEBUG=1` 環境では露出量が増える。 |
| **Fix scope** | `apps/web/src/app/api/auth/login/route.ts` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-C` |

### E2E-014 — 相談本文が URL query（`/concierge?theme=...`）に載る

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Home → Concierge Input` |
| **Reproduction** | Home の相談入力に自由記述して送信する。`/concierge?theme=<相談本文>` へ遷移する。応答が返って thread id が確定すると `navReplace("/concierge?tid=N")` で URL は置換されるが、**送信失敗時（`thread: null`）は `theme` が URL に残り続ける**。 |
| **Expected** | 相談本文を URL に載せない（POST body または session storage で渡す）。 |
| **Actual** | `buildConciergeHref()` が `params.set("theme", trimmed)` する。URL は browser history・`Referer` ヘッダ・edge / access log に残る。 |
| **Root cause** | `apps/web/src/features/home/components/HomeHeroConsultationInput.tsx:7-16,51-53`、`apps/web/src/app/concierge/ConciergeClientFull.tsx:509-517`（`sp.get("theme")`、`:510`）、`:1272-1289`（成功時のみ replace） |
| **Evidence** | 同ファイルのソース。`docs/audit/*` の既存契約（本書冒頭の banner と同様、監査文書に個人情報を残さない方針）と方向が逆である。 |
| **Impact** | **user / privacy**。相談本文は「疲れている」「人間関係」等、センシティブになりうる自由記述である。 |
| **Fix scope** | `apps/web/src/features/home/components/HomeHeroConsultationInput.tsx`、`apps/web/src/app/concierge/ConciergeClientFull.tsx`。**Analytics event 名は変更しないこと。** |
| **Suggested owner** | Mother Ship（受け渡し方式の決定）→ Codex |
| **Separate PR** | `PR-J: fix(concierge) — stop carrying consultation free text in the URL` |

### E2E-015 — Concierge chat リクエストに client timeout も route `maxDuration` も無い

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **SUSPECTED** |
| **Flow** | `Concierge Input → Recommendation` |
| **Reproduction（要 runtime 確認）** | backend / LLM が遅延したとき、フロントは `sending` のまま無期限に待つ。プラットフォーム側が先にタイムアウトすると 504 になり、`useConciergeChat` の catch が `ok: false` の unified を投げて「チャット送信に失敗しました (504)」を出す。 |
| **Expected** | 明示的な timeout / AbortController と、それに対応した fallback 表示。 |
| **Actual** | `apps/web/src/lib/api/client.ts:5-8` の axios instance に `timeout` 指定がなく、`apiPost` にも渡していない。`apps/web/src/app/api/concierge/chat/route.ts` に `maxDuration` の指定もなく、`apps/web/next.config.ts` にも無い。 |
| **Root cause** | 上記 |
| **Evidence** | `grep -rn "maxDuration" apps/web` → 0 件。`client.ts` のソース。 |
| **Impact** | **UX / observability**。無限ローディングと、プラットフォーム既定値依存の切断。実際の切断閾値は Vercel の設定に依存するため **SUSPECTED**。 |
| **Fix scope** | `apps/web/src/lib/api/client.ts`（または concierge 用の個別 config）、`apps/web/src/app/api/concierge/chat/route.ts` |
| **Suggested owner** | Codex / config |
| **Separate PR** | `PR-K: fix(concierge) — bound the chat request with an explicit timeout` |

### E2E-016 — `sanitizeNext` の allowlist が正当な内部遷移先を無言で捨てる

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Guest → ログイン → 元の遷移先` |
| **Reproduction** | `/ranking`（あるいは `/map`, `/compass`, `/populars`, `/shrines`（一覧は許可）以外の `/goshuins`, `/plan`, `/g/<username>`, `/users/<username>`）でヘッダーの「ログイン」を押す。`buildLoginHref` が `null` を返すため `returnTo` が付かず、ログイン後は常に `/` に着地する。 |
| **Expected** | 同一オリジンの内部パスであれば元の位置に戻る。 |
| **Actual** | `sanitizeNext` の allowlist は `/shrines`・`/mypage`・`/concierge`・`/billing`・`/favorites`・`/goshuin/new` のみ。それ以外は外部 URL と同じ扱いで `null` になる。 |
| **Root cause** | `apps/web/src/lib/nav/login.ts:26-40` |
| **Evidence** | 同ファイルのソース。`HeaderAuthButtons.tsx:15-18` が現在パスから `buildLoginHref` を組む。 |
| **Impact** | **UX**。安全側に倒れており脆弱性ではないが、Auth Return 体験が経路によって不揃いになる。 |
| **Fix scope** | `apps/web/src/lib/nav/login.ts`（allowlist 方式のまま網羅するか、`//` / scheme / auth ページのみを denylist する方式へ寄せる。**方式変更は security レビュー対象**） |
| **Suggested owner** | Mother Ship（方式判断）→ Codex |
| **Separate PR** | `PR-L: fix(nav) — cover the remaining internal destinations in returnTo sanitization` |

### E2E-017 — 最後のお気に入りを解除すると `/map` へ強制遷移する

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Save / Favorite`（`/favorites`） |
| **Reproduction** | お気に入りが 1 件の状態で解除する。`/map` へ push される。 |
| **Expected** | 空状態 UI（「お気に入りの神社はまだありません」）がその場で出る。同じ画面に空状態の実装が存在する。 |
| **Actual** | `if (nextItems.length === 0) router.push("/map");` |
| **Root cause** | `apps/web/src/app/favorites/FavoritesListClient.tsx:88` |
| **Evidence** | 同ファイル `:105-118` に空状態 UI が実装済みで、到達不能になっている。 |
| **Impact** | **UX**。意図しない画面遷移。 |
| **Fix scope** | `apps/web/src/app/favorites/FavoritesListClient.tsx` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-M: fix(favorites) — keep the user on the empty state after the last unsave` |

### E2E-018 — Concierge の `redirectToAuth` が thread context を捨てる

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Concierge Result（tid あり）→ 保護アクション → ログイン → 復帰` |
| **Reproduction** | `/concierge?tid=N` で認証必須アクションを起こす。`/auth/login?returnTo=%2Fconcierge` へ飛び、ログイン後は thread を失った入口 `/concierge` に戻る。 |
| **Expected** | `returnTo` に `?tid=N` を含める。 |
| **Actual** | `const returnTo = "/concierge";` とハードコード。 |
| **Root cause** | `apps/web/src/app/concierge/ConciergeClientFull.tsx:454-465` |
| **Evidence** | 同ファイルのソース。`sanitizeNext` は `/concierge?tid=N` を許可するので、渡せば通る。 |
| **Impact** | **UX**。相談結果への復帰が失われる。 |
| **Fix scope** | `apps/web/src/app/concierge/ConciergeClientFull.tsx` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-L` |

### E2E-019 — 存在しない shrine が HTTP 200 のソフト 404 になる

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Shrine Detail` 直接アクセス |
| **Reproduction** | `/shrines/999999` を開く。「神社の詳細情報が見つかりませんでした。」が **HTTP 200** で返る。`generateMetadata` は generic metadata を返す。 |
| **Expected** | `notFound()`（HTTP 404）。 |
| **Actual** | `getShrineDetailServer` の throw を catch して `shrine = null` にし、200 のまま fallback shell を描画する。 |
| **Root cause** | `apps/web/src/app/shrines/[id]/page.tsx:252-281` |
| **Evidence** | 同ファイルのソース。不正 ID（`Number` にならない / 0 以下）も同様に 200 で「不正な神社IDです。」を返す（`:233-243`）。 |
| **Impact** | **user / SEO / observability**。ユーザーに対しては安全に失敗しているが、クローラと監視からは正常応答に見える。E2E-005 と合わせると「404 が 502 にも 200 にもなる」状態。 |
| **Fix scope** | `apps/web/src/app/shrines/[id]/page.tsx`（E2E-005 の修正と同時に判断する） |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-C` |

### E2E-020 — `concierge_anon_id` が `SameSite=None` で発行される

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | `Concierge Input`（匿名） |
| **Reproduction** | 匿名で相談を送る。`Set-Cookie: concierge_anon_id=...; HttpOnly; Secure; SameSite=None; Path=/; Max-Age=7776000`。 |
| **Expected** | 同一サイト用の identity cookie なので `SameSite=Lax`（他の auth cookie と同じ）。 |
| **Actual** | `sameSite: "none", secure: true` 固定。結果として (a) cross-site リクエストでも送出される、(b) `secure: true` 固定のため **http のローカル開発ではブラウザが cookie を破棄**し、匿名スレッドの継続が壊れる。 |
| **Root cause** | `apps/web/src/app/api/concierge/chat/route.ts:39-46` |
| **Evidence** | 同ファイルのソース。`access_token` / `refresh_token` は同ファイル `:54-71` で `sameSite: "lax"`。 |
| **Impact** | **auth（匿名 identity）/ 開発体験**。匿名スレッドの所有権はこの cookie で判定される（`backend/temples/api/views/concierge.py:118-128`）。 |
| **Fix scope** | `apps/web/src/app/api/concierge/chat/route.ts` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-A` |

### E2E-021 — SSR の self-fetch base URL が `x-forwarded-host` / `host` を信用する

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **SUSPECTED** |
| **Flow** | Shrine Detail SSR / `/favorites` SSR / `/mypage` SSR / `/shrines/resolve` |
| **Reproduction（要 runtime 確認）** | `WEB_BASE_URL` / `PLAYWRIGHT_BASE_URL` が未設定のとき、`resolveServerBaseUrlFromHeaders` は `x-forwarded-host`（無ければ `host`）から origin を組む。この origin へ **利用者の cookie を添えて** server fetch する。edge がこれらのヘッダを検証せず透過するなら、cookie を攻撃者ホストへ送出できる。 |
| **Expected** | server 側の self-fetch base は環境変数で固定する。 |
| **Actual** | ヘッダ由来が env より優先されるのは `WEB_BASE_URL` / `PLAYWRIGHT_BASE_URL` が設定されている場合のみで、未設定時はヘッダが第一候補になる。 |
| **Root cause** | `apps/web/src/lib/server/resolveServerBaseUrl.ts:10-31`、呼び出し元 `lib/server/favorites.server.ts:52-59`、`lib/api/favorites.server.ts:12-22`、`app/shrines/resolve/page.tsx:20-32` |
| **Evidence** | 同ファイル群のソース。`.env.example` に `WEB_BASE_URL` の記載はない。 |
| **Impact** | **auth / security**。本番は Vercel で `Host` がプロジェクトドメインに対して検証され `x-forwarded-host` はプラットフォームが設定するため、実害は現時点では想定されない。ただし self-host / 別 proxy へ移す場合は成立する。**SUSPECTED（production の header 透過性の runtime 確認が必要）**。 |
| **Fix scope** | `apps/web/src/lib/server/resolveServerBaseUrl.ts` + 環境変数（`WEB_BASE_URL` の常時設定）。**環境設定変更を伴うため独立 PR。** |
| **Suggested owner** | config / Mother Ship |
| **Separate PR** | `PR-N: chore(server) — pin the SSR self-fetch origin to an env value` |

### E2E-022 — server 側 upstream origin が `NEXT_PUBLIC_API_BASE_URL` にフォールバックする

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED（technical debt）** |
| **Flow** | `Shrine Detail` SSR |
| **Reproduction** | `DJANGO_API_BASE_URL` と `BACKEND_URL` が未設定で `NEXT_PUBLIC_API_BASE_URL` が設定されている環境では、`getShrineDetailServer` の upstream origin が public 変数で決まる。値が `/api` のような相対値だと `new URL()` が壊れて詳細取得が全滅する。 |
| **Expected** | server 側 upstream は server-only 変数のみで決める（`lib/server/backend.ts` の `getDjangoOrigin` と同じ規約）。 |
| **Actual** | `resolveBackendPublicBaseUrl()` が `NEXT_PUBLIC_API_BASE_URL` を第 3 候補に持つ。 |
| **Root cause** | `apps/web/src/lib/api/shrines.server.ts:11-19` |
| **Evidence** | 同ファイルのソース。`apps/web/package.json` の `guard:no-next-public-in-server` は `src/lib/server` と `src/app/api` しか見ないため、`src/lib/api/*.server.ts` を検出できない。 |
| **Impact** | **config risk / technical debt**。現時点の production では `DJANGO_API_BASE_URL` 系が設定されている前提のため顕在化していない。 |
| **Fix scope** | `apps/web/src/lib/api/shrines.server.ts` と `guard:no-next-public-in-server` の対象範囲 |
| **Suggested owner** | Codex / config |
| **Separate PR** | `PR-F` |

### E2E-023 — BFF が upstream 403 を「トークン失効」として refresh + retry する

| Field | 内容 |
| --- | --- |
| **Severity / Status** | P2 / **CONFIRMED** |
| **Flow** | 権限不足で 403 を返す全 endpoint（例: 非管理者による `/api/concierge/score-v3/dashboard`） |
| **Reproduction** | 一般ユーザーで `/api/concierge/score-v3/dashboard` を叩く。backend が 403 を返すたびに BFF が refresh を 1 回発行し、再度 upstream を叩き、結局 403 を返す。さらに新しい `access_token` cookie を書く。 |
| **Expected** | 403（permission denied）は refresh 対象にしない。401 のみ retry する。 |
| **Actual** | `if ((upstream.status === 401 \|\| upstream.status === 403) && retryOn401 && refresh)` |
| **Root cause** | `apps/web/src/lib/server/bffFetch.ts:163-166` |
| **Evidence** | 同ファイルのソース。 |
| **Impact** | **performance / observability**。backend 往復が最大 3 倍になり、不要な token 再発行が起きる（E2E-001 の衝突窓を広げる副次効果もある）。 |
| **Fix scope** | `apps/web/src/lib/server/bffFetch.ts` |
| **Suggested owner** | Codex |
| **Separate PR** | `PR-A` |

---

## 6. 明示的な NON-ISSUE（確認済みで問題なし）

| 対象 | 確認内容 | 根拠 |
| --- | --- | --- |
| Premium / Billing の正本 | Backend が唯一の正本。フロントは独自に Premium を推論しない。取得失敗時は Free へ fail-close する。 | `app/api/billings/status/route.ts:36-42`（非 ok → FREE stub）、`lib/api/billing.server.ts:12-19,35-39`（例外 → FREE）、`lib/premium/accessLevel.ts` は `plan === "premium" && is_active === true` のみを Premium とする |
| `NEXT_PUBLIC_FORCE_BILLING_PLAN` の premium 上書き | `NODE_ENV !== "production"` で gate 済み。production では不活性。 | `app/api/billings/status/route.ts:18-27` |
| Billing success / cancel / refetch | `useBilling.refresh()` を手動再取得ボタンと `pageshow`（bfcache 復帰）で再実行し、Premium 未反映時は誤って有効表示しない。 | `app/billing/success/page.tsx:104-140`、`app/billing/manage/page.tsx:30-41` |
| `data._debug`（相談本文を含む内部 payload） | public response 境界で確実に除去される。 | `backend/temples/api_views_concierge.py:298-303` |
| Concierge Thread の所有権 | 認証済みは `user=user`、匿名は `user__isnull=True, anonymous_id=<cookie>` でのみ一致。どちらにも合致しなければ 404。 | `backend/temples/api/views/concierge.py:118-128` |
| Score V3 Dashboard | BFF route に gate は無いが、backend が `IsAdminUser`。非管理者 403 / 匿名 401 が既存テストで担保されている。 | `backend/temples/api/views/score_v3_dashboard.py:23`、`backend/temples/tests/api/test_score_v3_dashboard_api.py:25-35` |
| `returnTo` / `next` の外部リダイレクト防止 | `//`・`://`・任意の scheme prefix・auth ページ自身をすべて reject する。二重デコードでの `//` 復元も、先頭 `/` チェックで落ちる。 | `lib/nav/login.ts:18-41,48-72` |
| 経路案内の destination | 座標が無効なら CTA を出さず、住所・神社名・東京駅などへ**フォールバックしない**。 | `lib/maps/destinationContract.ts:35-52`、`app/shrines/[id]/page.tsx:288-295` |
| Recommendation URL の query allowlist | `/shrines/:id` に載る query は `ctx` / `tid` / `recommendation_instance_id` / `recommendation_rank` / `place_id` / `toast` に限定され、score・breakdown・内部 tag は載らない。 | `lib/nav/buildShrineHref.ts:5-6,56-86` |
| Recommendation instance の detail href | `recommendation.id` を shrine_id として使わない（`shrine_id` / `shrineId` / `shrine.id` のみ）。 | `features/concierge/detailHref.ts:26-31` |
| Concierge Debug Panel | `NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL !== "1"` で早期 return する。 | `app/concierge/ConciergeClientFull.tsx:268-269` |
| `/mypage` の guest 直接アクセス | middleware が `/login?next=...` へ、`/login` が `sanitizeNext` 経由で `/auth/login?returnTo=...` へ正規化する。 | `apps/web/middleware.ts:8-16`、`app/login/page.tsx:20-38` |
| Shrine Detail の保存ボタン | `guestMode` を server（cookie の実在＋`/api/favorites/` の 401 判定）から受け取るため、E2E-003 / E2E-004 の client 側誤判定の影響を受けない。 | `app/shrines/[id]/page.tsx:316,562,570`、`lib/server/favorites.server.ts:36-86`、`components/shrine/ShrineSaveButton.tsx:44` |
| Favorite の楽観更新 | 失敗時は必ず `setFav(prev)` で巻き戻し、成功時のみ cache を更新する。リロード時は server 値が正本。 | `hooks/useFavorite.ts:55-96`、`app/shrines/[id]/page.tsx:316,562,570` |
| 空 Recommendation の fallback | `hasRestoredCandidates` / `shouldShowEntry` により、候補 0 件では結果 UI ではなく入口 UI に倒れる。 | `app/concierge/ConciergeClientFull.tsx:1421-1428` |
| 経路案内リンク | `href` を `new URL()` で検証し `https:` 以外は「経路リンクを利用できません」に縮退する。Analytics 送出はすべて try/catch で囲われ、外部遷移を遅延・阻害しない。 | `components/shrine/GoogleMapRouteLink.tsx:46-54,63-107` |
| `/mypage` の section 単位 fail-safe | favorites / threads のどちらかが落ちても HUB 全体は落ちない。 | `app/mypage/page.tsx:16-23` |

---

## 7. 技術的負債（bug ではないが記録）

| 項目 | 根拠 |
| --- | --- |
| `ShrineSaveToggle` は完全な未使用コンポーネント | `grep -rn "ShrineSaveToggle" apps/web/src` → 定義のみ |
| `getShrineFavoriteStateServer`（`lib/api/favorites.server.ts:30-86`）は未使用。`lib/server/favorites.server.ts` の `getShrineFavoriteInitialState` と責務が重複し、戻り値の形（`initial` vs `fav` / `favorite_id`）も異なる | `grep -rn "getShrineFavoriteStateServer" apps/web/src` → 定義のみ |
| `ConciergeDebugPanel` の Candidate Pool / Ranking Breakdown / Visit Style / Trim の 4 セクションは `unified.data._debug` を読むが、その値は backend の public 境界で常に除去される（E2E-009）。env を ON にしても描画されない dead UI | `ConciergeClientFull.tsx:271-274` と `api_views_concierge.py:303` |
| `AuthProvider.shouldAutoFetchMe` の `/concierge/full` 分岐が到達不能 | `AuthProvider.tsx:91-94` |
| `useConciergeChat` の `send` が `options`（毎レンダー新規オブジェクト）に依存するため参照が毎回変わる | `features/concierge/hooks.ts:226,423` |
| `/billing`・`/billing/manage` は未認証でもアクセスでき、401 が Free stub に丸められるため Guest に「Free プラン」を表示する | `app/api/billings/status/route.ts:36-38`、`app/billing/page.tsx` |

---

## 8. 推奨する修正 PR 境界（実装は本 PR では行わない）

| PR | 範囲 | 含む Finding | 備考 |
| --- | --- | --- | --- |
| **PR-A** | BFF の token refresh と cookie 属性 | E2E-001, E2E-002, E2E-020, E2E-023 | **最優先**。`bffFetch.ts` と `api/concierge/chat/route.ts` に閉じる。API schema 変更なし |
| **PR-B** | Client 認証状態の正本化 | E2E-003, E2E-004 | `SignupForm` / `AuthProvider` / Concierge Hero の `guestMode` 受け渡し |
| **PR-C** | BFF エラー境界の堅牢化 | E2E-005, E2E-012, E2E-013, E2E-019 | status 伝播・内部 origin 非開示・segment エンコード |
| **PR-D** | Shrine Detail の accessLevel 是正 | E2E-006 | **Analytics event 名は変更しない**。property 値のみ |
| **PR-E** | Favorite の by-shrine フォールバック整理 | E2E-007 | 削除 or route 追加の判断が必要 |
| **PR-F** | Debug / guard の整合 | E2E-008, E2E-022, §2.1 の既存 CI guard 失敗 | `/debug/**` の gate と guard 対象範囲 |
| **PR-G** | `_debug` の gate 化 | E2E-009 | **API response schema に触れるため製品判断が先** |
| **PR-H** | 経路案内 fallback 文言の描画 | E2E-010 | UI のみ |
| **PR-I** | JWT 寿命と cookie maxAge | E2E-011 | **環境設定変更を含む。単独で慎重に** |
| **PR-J** | 相談本文を URL から外す | E2E-014 | 受け渡し方式の製品判断が先 |
| **PR-K** | Concierge chat の timeout | E2E-015 | runtime 実測後 |
| **PR-L** | Auth Return の遷移先復元 | E2E-016, E2E-018 | sanitize 方式変更は security レビュー対象 |
| **PR-M** | Favorites 空状態 | E2E-017 | UI のみ |
| **PR-N** | SSR self-fetch origin の固定 | E2E-021 | **環境設定変更を含む。単独で慎重に** |

---

## 9. 追加した監査用テスト

監査時点（base commit `6c94cdb`）では
`apps/web/src/lib/server/__tests__/bffFetch.audit.test.ts` に
E2E-001 / E2E-002 の**現状挙動**を固定するテストだけを置いた。望ましい挙動の
assertion ではなく、実装コードには一切触れていない。

このファイルは §10 のとおり PR-A で
`apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts`
（正しい期待値の regression test）へ置き換えられた。

---

## 10. 更新履歴

本セクションだけは監査後の状態追跡のために追記する。§3〜§8 の記述は
base commit `6c94cdb` 時点の観測記録であり、遡って書き換えない。

### PR-A — Auth Refresh Isolation（`fix/auth-refresh-isolation`）

| Finding | 監査時 Status | PR-A 後 |
| --- | --- | --- |
| E2E-001 | CONFIRMED | **RESOLVED** — in-flight refresh を refresh token 単位の Map に分離 |
| E2E-002 | CONFIRMED | **RESOLVED** — cookie 属性を `lib/server/authCookies.ts` に一本化し `Secure` を共有 |
| E2E-020 | CONFIRMED | **RESOLVED** — Web origin 側の `concierge_anon_id` を `SameSite=Lax` + 条件付き `Secure` へ |
| E2E-023 | CONFIRMED | **RESOLVED** — refresh + retry の起動条件を 401 のみに限定 |

- Regression test: `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts`（8 cases）。
  修正前の実装に対して 4 cases が落ちることを実測で確認済み。
- E2E-011（JWT 寿命と cookie `maxAge` の不一致）は **未解決のまま**である。
  PR-A は cookie の `maxAge` 値を変更しておらず、`SIMPLE_JWT` にも触れていない。
  E2E-001 の発火頻度を押し上げる増幅要因は残っているため、PR-I は引き続き必要。
- E2E-003 / E2E-004 / E2E-005 ほかは PR-A のスコープ外で、未着手のままである。
