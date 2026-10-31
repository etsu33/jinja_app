> **Status: Audit record (read-only) — Root cause UNCONFIRMED**
>
> 本番 `https://jinja-app-web.vercel.app/` の初回アクセスでアプリ独自の「ページが見つかりません」画面が表示され、
> 再読み込みでは正常表示される事象の原因監査。証拠収集のみ。アプリコード・認証契約・Vercel 設定・本番は変更していない。
>
> - Audit date: 2026-10-31
> - Audited code: `develop` @ `d3b55156c3a1a0cd368d7b11120647098771725a`
> - Production deployment at audit time: `dpl_9LCM39JbwL4PryyNd7fL3vvWZwva`（READY / target=production / commit `d3b5515`）
> - Method: 静的コード読解、Vercel MCP（project / deployments / build log / runtime errors / share link 経由の本番 fetch）、
>   ローカル `next build` + `next start` に対する Playwright 再現。
> - Not available in this session: セッションのネットワークポリシーにより `jinja-app-web.vercel.app` への直接 HTTP は 403（proxy）。
>   本番取得は Vercel MCP の share link 経由のみ。Hobby プランのため runtime log は直近 1 時間しか取得できず、該当時間帯のログは無い。

# 本番初回アクセス 404 監査（2026-10-31）

## 1. 結論

- **Root cause: UNCONFIRMED.** 現時点の証拠では、アプリのコード経路・Middleware・認証処理のいずれからも
  `/` で not-found 画面に到達する経路は見つからなかった。
- **棄却（証拠あり）**
  - `/` で `notFound()` を呼ぶコードは存在しない。
  - Middleware は `/mypage/:path*` のみに一致し、`/` には介入しない。
  - `/api/users/me/` の 401 は Guest 状態に落ちるだけで、ルーティングに影響しない（ローカルで再現確認）。
  - 現在の本番デプロイは `/` に HTTP 200・`x-matched-path: /`・静的プリレンダー（`x-nextjs-prerender: 1`）を返す。
- **未検証のまま残る仮説**: 事象発生時点のデプロイ切替（skew）/ CDN キャッシュ、実際にアクセスした URL の差異、
  特定ブラウザ（アプリ内ブラウザ等）固有の挙動。いずれも事象発生時の一次証拠（ブラウザの Network 記録）が無いと判定できない。

## 2. 対象ファイルと関数

| ファイル | 関数 / 要素 | 役割 |
| --- | --- | --- |
| `apps/web/src/app/layout.tsx` | `RootLayout` | `AuthProvider` → `ClientBootstrap` / `HomeLogoLink` / `HeaderAuthButtons`（Suspense）/ `children` / `LegalFooter` / `ClientToaster` |
| `apps/web/src/app/page.tsx` | `Page` | `<Suspense>` で `HomePage` を描画 |
| `apps/web/src/features/home/HomePage.tsx` | `HomePage` (Server) | `WorldviewBackdrop` / `HomeToastClient` / `HomeMainClient` |
| `apps/web/src/features/home/components/HomeToastClient.tsx` | `HomeToastClient` | `?toast=` がある時のみ `history.replaceState` でクエリ削除。パスは変えない |
| `apps/web/src/features/home/components/HomeMainClient.tsx` | `HomeMainClient` | `HomeHero` + `HomeActionGrid`。リダイレクトなし |
| `apps/web/src/app/not-found.tsx` | `NotFound` | 表示されたとされる「ページが見つかりません」画面（唯一のカスタム 404） |
| `apps/web/src/app/error.tsx` | `Error` | Root error boundary（文言は「エラーが発生しました」で 404 画面とは別） |
| `apps/web/middleware.ts` | `middleware` / `config.matcher=["/mypage/:path*"]` | `access_token` Cookie 無しの `/mypage*` を `/login?next=` へ 307 |
| `apps/web/src/lib/auth/AuthProvider.tsx` | `AuthProvider` / `shouldAutoFetchMe` / `fetchMe` / `applyMeResult` | 初回マウント時の `/api/users/me/` 判定 |
| `apps/web/src/lib/auth/loggedInMarker.ts` | `markLoggedIn` / `markLoggedOut` / `maybeLoggedIn` | localStorage `auth:logged_in` |
| `apps/web/src/app/api/users/me/route.ts` | `GET` | `bffFetchWithAuthFromReq` で backend `/api/users/me/` へ中継 |
| `apps/web/src/components/layout/HeaderAuthButtons.tsx` | `HeaderAuthButtons` | `useSearchParams` 使用（CSR bailout）。`/mypage?tab=profile` へのリンクを常時表示 |
| `apps/web/next.config.ts` | `trailingSlash:false` / `skipTrailingSlashRedirect:true` / `rewrites()=[]` | `/` に影響する設定なし |

`notFound()` 呼び出し箇所（全件）:

- `apps/web/src/app/debug/score-v3-dashboard/page.tsx:5`（`NEXT_PUBLIC_ENABLE_DEBUG_PAGES !== "1"`）
- `apps/web/src/app/debug/concierge/page.tsx:7`（同上）
- `apps/web/src/app/users/[username]/page.tsx:23`
- `apps/web/src/app/g/[username]/page.tsx:108`

いずれも `/` の描画経路に含まれない。`vercel.json` はリポジトリに存在しない。Service Worker の登録も無い。

## 3. ルーティング / 認証の実行フロー（`/`）

1. Vercel Edge: Middleware matcher は `/mypage/:path*` のみ → `/` は Middleware を通らない。
   （build log に `ƒ Proxy (Middleware)` があり、`apps/web/middleware.ts` は検出されている。）
2. `/` は build 時に静的プリレンダー（build log: `┌ ○ /`）。CDN から HTML を返す。
3. ブラウザで hydrate。`AuthProvider` の `useEffect`:
   - `shouldAutoFetchMe("/") === false`。
   - `maybeLoggedIn()`（localStorage `auth:logged_in === "1"`）が false なら `/api/users/me/` を**呼ばず** Guest。
   - true の場合のみ `fetchMe()` → 401 なら `markLoggedOut()` + Guest、その他失敗は `unknown`。
   - いずれの分岐もナビゲーション（`router.*` / `location.*`）を行わない。
4. Next の Link prefetch（viewport 内）: `/compass?ref=home`・`/map`・`/shrines`・`/ranking`・`/mypage?tab=profile` 等。
   `/mypage` は Middleware により 307 → `/login?...`。prefetch 結果は表示に影響しない。

**401 と 404 の関係**: `/` では marker が無い限り `/api/users/me/` 自体が呼ばれない。本番ログの 401 は、
marker を持つブラウザ、または `/` 以外（`shouldAutoFetchMe` が true の route）からのアクセスで発生しうる正常系であり、
404 画面との因果は**確認されていない**。

## 4. 仮説ごとの証拠

| # | 仮説 | 判定 | 証拠 |
| --- | --- | --- | --- |
| H1 | `/` の描画中に `notFound()` が呼ばれる | **棄却** | §2 の全件 grep。`/` 経路に該当なし |
| H2 | Middleware / 認証ガードが `/` を書き換える | **棄却** | matcher が `/mypage/:path*` のみ。`withAuth` は `/shrines/new` 系でのみ使用 |
| H3 | `/api/users/me/` 401 が原因 | **棄却（コード上）** | ローカル本番ビルドで marker=1・`/api/users/me/` を 401 に固定 → Home 表示、marker 削除、ログインボタン表示、404 なし。500 でも同様 |
| H4 | クライアント側リダイレクト / 遷移で存在しない path へ移る | **棄却** | `/` 経路の client component に `router.push/replace`・`location.*` なし（`HomeHeroConsultationInput` の `router.push` はユーザー操作時のみ） |
| H5 | 本番サーバーが `/` に 404 を返す | **現時点では棄却 / 発生時点は不明** | 2026-10-31T11:13:58Z の fetch: `200`、`x-matched-path: /`、`x-nextjs-prerender: 1`、`x-vercel-cache: HIT`、`age: 4159`。事象発生時のレスポンスは未取得 |
| H6 | デプロイ切替時の skew（旧 HTML / 新 RSC・chunk の不整合）または CDN キャッシュ | **未検証** | 事実: production デプロイが docs のみのコミットでも発生しており、2026-10-31 だけで 5 回（約 4 時間）。事象との時刻相関は未取得。Hobby のログ保持 1 時間のため遡及不可 |
| H7 | Vercel Deployment Protection（SSO）の影響 | **棄却（表示内容から）** | `ssoProtection: all_except_custom_domains`。保護に掛かった場合は Vercel のログイン画面になり、アプリの 404 画面は出ない |
| H8 | 実際にアクセスした URL が `/` と異なる（末尾文字・パス付き共有リンク・アプリ内ブラウザによる書き換え等） | **未検証** | アドレスバーの実 URL・遷移元（共有リンク / アプリ内ブラウザ）は未取得。`next.config.ts` は `skipTrailingSlashRedirect: true` で末尾スラッシュの正規化リダイレクトを行わない（`/` 以外の URL での挙動は本監査で未検証） |

## 5. 再現手順と結果

### 5.1 ローカル（実施済み）

```bash
pnpm install --frozen-lockfile --filter frontend...
cd apps/web && pnpm build && pnpm start -p 3123
```

Playwright（新規 context、Cookie / storage 無し）で以下を実施:

| シナリオ | 期待 | 実際 |
| --- | --- | --- |
| 新規 context で `/` | Home 表示 | Home 表示（404 なし） |
| 同 context で reload | Home 表示 | Home 表示 |
| `/?fbclid=abc` | Home 表示 | Home 表示 |
| `/terms` → ヘッダーロゴで `/` へ client navigation | Home 表示 | Home 表示 |
| marker=1 + `/api/users/me/` 401 で `/` | Home 表示・Guest | Home 表示・Guest・marker 削除 |
| marker=1 + `/api/users/me/` 500 で `/` | Home 表示・unknown | Home 表示・marker 維持 |

→ **ローカルでは再現しない。**

### 5.2 本番（未再現）

本セッションからは本番へ直接アクセスできず、ブラウザでの初回アクセスを再現できていない。次の手順で一次証拠を採取する必要がある:

1. シークレットウィンドウで DevTools → Network を開き「Preserve log」「Disable cache」を有効化。
2. アドレスバーに `https://jinja-app-web.vercel.app/` を入力して遷移。
3. 404 画面が出たら、**document リクエスト**の URL・Status・`x-vercel-id`・`x-vercel-cache`・`x-matched-path`・`age` と、
   直後の `?_rsc=` リクエストの Status を記録。HAR を保存。
4. 発生時刻（UTC）と、その時点の production deployment ID を照合。
5. 発生から 1 時間以内に Vercel runtime logs を確認（Hobby 保持期間）。

期待: document が 200 / `x-matched-path: /`。実際: 未取得。

## 6. 根本原因

**UNCONFIRMED。** コード起因の経路は §4 の通り見つかっていない。H5（発生時点）・H6・H8 の判定には §5.2 の一次証拠が必要。

## 7. 最小修正案（未実装）

原因未確定のため、現時点でコード修正は提案しない。証拠採取後の分岐:

- document が 404 かつ `x-matched-path` が `/_not-found` → 実 URL（H8）またはデプロイ切替（H6）を確認。
  H6 なら docs のみの変更で production デプロイしない設定（Ignored Build Step）を検討。これは Vercel 設定変更なので別途判断。
- document は 200 で、直後の RSC 取得が 404 → クライアントルーターの skew（H6）。
- document が 200 で RSC も 200 → ブラウザ固有（H8）。UA を記録して再調査。

## 8. 回帰テストの推奨

- `apps/web/e2e/01_home.spec.ts` は `toHaveTitle(/shrine|jinja/i)` を期待するが、実タイトルは `KAMI MUSUBI` で一致しない。
  さらに CI（`test:e2e:ci`）は `05_direction_flow.spec.ts` のみを実行するため、Home スモークは CI で実行されていない。
- 追加推奨（いずれも未実装）:
  1. 新規 context で `/` に遷移し、`ページが見つかりません` が無いこと・`#home-hero-consultation` があることを検証する E2E。
  2. marker=1 + `/api/users/me/` 401 のとき Home が表示され Guest になる E2E（§5.1 の内容）。
  3. デプロイ後の本番スモーク（document の status と `x-matched-path` を確認）。

## 9. 残存リスク / 未解決事項

- 事象発生時の URL・時刻・ブラウザ・Network 記録が無い。これが無い限り原因は確定できない。
- 事象は 1 回限りなのか常時なのかが不明。本監査時点の本番では 200 だった。
- docs のみのコミットでも production デプロイが頻発しており、デプロイ切替と初回アクセスが重なる確率を上げている（事実）。事象との相関は未確認（仮説）。
- 盲点: 「再読み込みで直る」は H6（デプロイ切替）と H8（URL 差異で reload 時に正規 URL を開き直した）のどちらでも説明できる。
  再読み込みで直ること自体はコード起因の否定にも肯定にもならない。
