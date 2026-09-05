# Production Smoke QA

## Metadata

| 項目 | 値 |
|---|---|
| Date | 2026-09-05 |
| Base SHA | `350a64161696e72afdc4e3a19ce4f2dfc948c9bb`（`origin/develop` tip、PR #2699） |
| Branch | `claude/kami-musubi-smoke-qa-pyp2u5` |
| Browser | Chromium 1194（Playwright 1.58.2、headless） |
| Viewports | 375 / 390 / 430 / 1280 |
| Production deployment | Vercel `jinja-app-web`、production alias `jinja-app-web.vercel.app`、deployment `dpl_4oa3taU5rvU5ArwBYkrUn4futcE4`（`target: production`, `state: READY`, commit `350a641`） |
| Production build id | `JxFYOxxOxSuza627IqCvh`（deployment固有URLとproduction aliasの両方で一致を確認。alias が base SHA を配信していることの根拠） |

本監査は **QA / Audit only**。Production codeは一切変更していない。最終diffは本文書のみ。

### Branch名の逸脱（記録）

依頼文書は `qa/production-smoke-readiness` を指定しているが、本セッションのharnessは
`claude/kami-musubi-smoke-qa-pyp2u5` を作業ブランチとして指定している。後者を優先した。
`qa/production-smoke-readiness` は `git ls-remote origin` 上に存在せず、関連するopen PRも無い
（open PR 18件を確認、全てdependabot・shrine submission系で本監査と無関係）。

---

## Phase 0 — Repository Safety

- current branch: `claude/kami-musubi-smoke-qa-pyp2u5`（`origin/develop` と同一commit、ahead/behind = 0/0）
- `git fetch origin develop` 実行後、`origin/develop` = `350a641`
- `git status --porcelain -uall`: **空**（staged 0件 / untracked 0件）
- duplicate branch: 無し / 関連open PR: 無し
- `git clean` / `git add .` / `git add -A` は未使用

### PR #2597 merge確認

| 項目 | 値 |
|---|---|
| PR | [#2597 ShrineCardCompactのDark UI背景を修正](https://github.com/etsu33/jinja_app/pull/2597) |
| state | `closed` / `merged: true` |
| merged_at | 2026-08-28T12:18:47Z（merged_by: etsu33） |
| 実コード確認 | `apps/web/src/components/shrines/ShrineCardCompact.tsx:74` が `bg-[var(--kt-color-surface-default)]` / `border-[var(--kt-color-border-default)]` になっていること、`bg-white/90` が残っていないことをbase SHAのworking treeで確認 |

**#2597はdevelopへmerge済み。STOP条件に該当しない。**
なお #2597 のFQA-001修正が実際に効いていることは、Compass結果画面のレンダリング実測でも確認した（後述 Phase 14）。

---

## Phase 1 — Production Environment Readiness

### 実際に使用した環境と、その制約

本セッションのegress networkは組織ポリシーで制限されており、**production frontend / production backendのどちらにも直接接続できない**。

```
CONNECT jinja-backend.onrender.com:443            -> gateway 403 (policy denial)
CONNECT jinja-app-web.vercel.app:443              -> gateway 403 (policy denial)
CONNECT jinja-app-l7eugfruh-....vercel.app:443    -> gateway 403 (policy denial)
```
（`$HTTPS_PROXY/__agentproxy/status` の `recentRelayFailures` で確認）

そのため、以下の2経路を併用した。

**経路1: Production fresh read（server-side fetch経由）**
Vercel MCPの`web_fetch_vercel_url`はVercel側でfetchを実行するため、本セッションのnetwork制限を経由せずproductionの実レスポンスを取得できる。GETのみ。
これで取得できたもの:
- `/` のSSR HTML（prerender）
- `/shrines/49` のSSR HTML + RSC payload全体
- `/api/shrines?limit=2` の**実production DBレスポンス**（`count: 104`、`x-render-origin-server: gunicorn`）
- `/api/shrines/49/data` の**実production Stored Fact**（deities / histories / sources）

取得できなかったもの: **POST**（`/api/concierge/chat/`、`/api/compass/recommendations/`、login、favorite）。`web_fetch_vercel_url`にmethod指定が無いため。
また deployment固有URL（`jinja-app-l7eugfruh-...`）の dynamic route は Vercel Deployment Protection（SSO）で302されるため、production aliasのみを使用した。

**経路2: Local production build + local stub backend**
- `pnpm -C apps/web build`（`next build`、EXIT=0）→ `next start`（`NODE_ENV=production`, port 3000）
- 実production bundle（同一SHAの実CSS/JS）・実BFF route handler（`src/app/api/**`, `src/lib/bff`, `src/lib/server`）・実Server Componentがそのまま動作
- Django backendのみをlocal stub（`DJANGO_ORIGIN` / `DJANGO_API_BASE_URL` = `http://127.0.0.1:8001`）へ差し替え
- stubの `/api/shrines/49/data/` には**production実レスポンスをverbatimで投入**（上記経路1で取得したもの）
- Concierge / Compassのrecommendation payloadは、repo内のwire contract（`src/lib/api/concierge/types.ts`、`src/features/compass/types.ts`、`backend/temples/services/concierge_chat.py`）に沿って構成した合成データ

### 環境要件（repoから確定）

| 項目 | 値 |
|---|---|
| frontend起動 | `pnpm -C apps/web build` → `pnpm -C apps/web start`（Next.js 16.3.0 / React 19.2.8 / Turbopack） |
| backend接続先 | `DJANGO_ORIGIN` \| `BACKEND_ORIGIN`（BFF proxy用）、`DJANGO_API_BASE_URL` \| `BACKEND_URL` \| `NEXT_PUBLIC_API_BASE_URL`（Server Component直fetch用）。既定は `http://127.0.0.1:8000` |
| auth要件 | `/mypage/**` のみ `middleware.ts` が `access_token` cookieの存在を確認し、無ければ `/login?next=...` へredirect |
| API base URL | frontendは常に自ドメインのBFF（`/api/**`）を叩く。backendへの直アクセスは `guard:no-backend-direct` で禁止されている |
| map provider | 経路CTAは `https://www.google.com/maps/dir/?api=1&destination=...` の外部リンク生成のみ。API keyは不要 |
| external service | Google Places（`/api/places/**`）、PostHog（`posthog-js`）。本監査環境からは到達不可 |

### Environment Classification

| 分類 | 対象 |
|---|---|
| `VERIFIED_PRODUCTION` | Home SSR HTML / Shrine Detail SSR HTML + RSC payload / `GET /api/shrines` / `GET /api/shrines/{id}/data`。Phase 20のraw text監査（SSR出力範囲）、Phase 9のEvidence内容 |
| `VERIFIED_PREVIEW` | **該当なし**（preview deploymentもegress policyで到達不可） |
| `VERIFIED_LOCAL_PRODUCTION_BUILD` | Scenario A/B/C全journey、Dark UI実測、375/390/430/1280、console、network、focus/hover、overflow |
| `VERIFIED_COMPONENT_HARNESS` | 使用せず（本監査はcomponent単体harnessを根拠にしていない） |
| `BLOCKED_BY_ENVIRONMENT` | production上でのPOST journey（Concierge submit / Compass submit / login / favorite書き込み）、production上でのauth済みjourney、production実ブラウザでのconsole/network/viewport計測、Google Maps外部起動、PostHog analytics送信、Stripe billing |

**Harnessだけでproduction確認済みとは扱っていない。** production由来でない項目は上表どおり `VERIFIED_LOCAL_PRODUCTION_BUILD` として記録し、production側の裏取りができた項目のみ `VERIFIED_PRODUCTION` としている。

---

## Phase 2 — Baseline Verification

base SHA `350a641` のまま実行（QA用の改変なし）。

| Check | Command | Result |
|---|---|---|
| full web tests | `pnpm -C apps/web test` | **164 files / 1289 tests passed**、EXIT=0 |
| typecheck | `pnpm -C apps/web typecheck` | **0 errors**、EXIT=0 |
| lint | `pnpm lint` | **0 errors**、EXIT=0 |
| build | `pnpm -C apps/web build` | **成功**、EXIT=0 |
| contract tests | `pnpm test:contract` | **164 files / 1289 tests passed**、EXIT=0 |
| OpenAPI lint | `pnpm lint:openapi` | `No results with a severity of 'error' found!`、EXIT=0 |

既存warning: `punycode` DeprecationWarning（Node組み込み、spectral CLI由来）のみ。新規failure 0件。
**Baselineは healthy。STOP条件に該当しない。**

---

## Phase 3 — Production Route Fresh Read / Route Matrix

`apps/web/src/app` を実際に列挙して確定した（過去文書からの推測はしていない）。

| Feature | Route | Entry Point | Auth Required | Main Dependency |
|---|---|---|---|---|
| Home | `/` | `src/app/page.tsx` → `features/home/HomePage` | No | client-side only（Hero入力＋`/compass`・`/map`・`/shrines`へのlink） |
| Concierge | `/concierge`（`/concierge/full` も同一client） | `src/app/concierge/page.tsx` → `ConciergeClientFull.tsx` | No（匿名可、`concierge_anon_id` cookie） | `POST /api/concierge/chat/` → Django `/api/concierge/chat/`、`GET /api/goriyaku-tags/` |
| Recommendation Result | `/concierge?tid={id}`（**独立routeではない**。同一画面内で `ConciergeSectionsRenderer` が描画） | `ConciergeSectionsRenderer.tsx` → `ConciergeTopRecommendationHero` / `ShrineCardCompact` | No | 上記chat responseの `data.recommendations` |
| Shrine Detail | `/shrines/[id]` | `src/app/shrines/[id]/page.tsx`（Server Component） | No | `GET {backend}/api/shrines/{id}/data/`、`/api/shrines/{id}/meaning/`、billing status、favorites初期状態、concierge thread |
| MyPage | `/mypage` | `src/app/mypage/page.tsx` | **Yes**（`middleware.ts` matcher `/mypage/:path*`） | `/api/users/me/` |
| Consultation History | `/mypage/history`、詳細 `/mypage/history/[tid]` | `src/app/mypage/history/page.tsx` → `ConsultationHistoryListView.tsx` | **Yes** | `GET /api/concierge-threads/` |
| Compass | `/compass` | `src/app/compass/page.tsx` → `CompassClient.tsx` | No | `POST /api/compass/recommendations/` |

補助route（本監査で通過したもの）: `/favorites`、`/shrines`、`/auth/login`、`/consultation`。

Dark UIは `src/app/layout.tsx` の `<html className="... dark ...">` で**無条件・常時適用**（production HTMLでも同一classを確認）。テーマ切替UIは存在しない。

---

## Phase 4 — Smoke Scenario Definition

### Scenario A — Standard Concierge Journey
`/` → `/concierge` → 相談テキスト入力（「仕事の流れを整えて、次に進むきっかけがほしいです」）→ Submit → Recommendation描画 → `/shrines/49` → 経路CTA確認 → deep-dive質問入力

### Scenario B — Saved / MyPage Journey
未ログイン: `/mypage` / `/mypage/history` のauth挙動 → `/favorites` empty state
ログイン相当（local stubに `access_token` cookie付与）: `/mypage` → `/mypage/history` → `/favorites`（保存済み1件）

### Scenario C — Compass Journey
`/compass` → 目的「転機・仕事」選択 → 生年月日入力 → 出発地点Sheetで「現在地を使用」 → Submit → 方向コンテキスト＋推薦カード → `/shrines/49?ctx=compass&recommendation_instance_id=...&recommendation_rank=1`

---

## Phase 5–14 — Journey Smoke結果

### Phase 5 — Home（`/`）

`VERIFIED_PRODUCTION`（SSR HTML）＋ `VERIFIED_LOCAL_PRODUCTION_BUILD`（実ブラウザ）

- route loads: 200、fatal errorなし
- Hero `<h1>`「今の相談から、向かう神社を見つける」表示
- Primary CTA「この相談ではじめる」表示（未入力時 `disabled`、`disabled:opacity-45`）
- 相談のきっかけchip 6件、「＋ 条件を追加する」
- Concierge導線: Hero埋め込み型 / Compass導線: `/compass?ref=home` / sub paths: `/map`、`/shrines`
- Dark UI: `bg-[var(--kt-color-background-base)]`・`--kt-color-surface-elevated` で統一、白カード無し
- 375/390/430/1280 いずれも horizontal overflow **なし**
- raw key露出 / `undefined` / `null` / `[object Object]`: **なし**

### Phase 6 — Concierge Input（`/concierge`）

`VERIFIED_LOCAL_PRODUCTION_BUILD`

- route loads、textarea操作可能、テーマchip 4件＋「ほかのテーマも見る（他4件）」
- 未入力時「この相談で神社を提案してもらう」はdisabled（required state成立）
- focus ring: emerald（`--kt-color-border-focus`）が Dark 背景上で明確に視認可能
- 375pxでもtextarea・chipともclipなし、scrollingは縦のみ
- 補助条件パネルのラベルに低コントラストあり（PSQ-006、P2）

### Phase 7 — Concierge Submit / API

`VERIFIED_LOCAL_PRODUCTION_BUILD`（**production backendへの実POSTは `BLOCKED_BY_ENVIRONMENT`**）

- request送信・response成功・loading完了・Recommendation画面へ遷移（URLが `/concierge?tid=9001` へ更新）を確認
- fatal network error / timeout / 予期しない4xx・5xx: **なし**
- BFF (`src/app/api/concierge/chat/route.ts`) のcookie中継・anon cookie処理は実コードのまま通過

### Phase 8 — Recommendation Result

`VERIFIED_LOCAL_PRODUCTION_BUILD`

描画確認できた要素:

| 要素 | 実際の表示 |
|---|---|
| Top recommendation | 「今の相談に近い方向の神社」＋ 神社名「富岡八幡宮」 |
| Runtime Match | 「相談内容・ご利益との一致」＋ reason本文 |
| Ranking Reason | 「相談との一致が強い」 |
| Explanation-only Fact | 「参考情報」pill ＋「応神天皇」（**Ranking理由とは別ブロック**） |
| Action | 「参拝前にできること」＋ action本文 |
| CTA | 「神社の詳細を見る」→ `/shrines/49?ctx=concierge&tid=9001` 遷移成功 |
| 相談の整理 | 「今回の相談の整理」「今回の相談との接点」 |
| Premium境界 | 「ここから、より深い意味へ」＋「ログインして意味を深掘りする」 |
| 他候補 | 「迷った時だけ、ほかの神社を見る」（`ShrineCardCompact`） |

- internal need tag slug（`career` / `protection` 等）露出: **なし**（表示ラベルへ変換済み）
- raw JSON / `undefined` / `null`: **なし**
- Ranking Factと参考情報の混同: **なし**（「参考情報」pillで明確に分離）
- **Dark UI contrast: 重大なNG（PSQ-001、P1）** — 詳細は Findings

### Phase 9 — Shrine Detail（`/shrines/49`）

`VERIFIED_PRODUCTION`（内容）＋ `VERIFIED_LOCAL_PRODUCTION_BUILD`（描画・contrast）

production SSR HTMLで確認できた内容:
- shrine name「富岡八幡宮」（`<h1>` と header truncate の両方）
- 「この神社の意味」/ 住所
- 「神社について」→ 御祭神「応神天皇」/ 由緒・歴史（創始・歴史の2件、`period_text` 付き）
- **「出典」→「御由緒」（`http://www.tomiokahachimangu.or.jp/...`、`target=_blank rel="noreferrer noopener"`）** — provenance健全
- 「神社との意味の接続」→ 今のあなたとの接点 / この場所が合う理由 / 今の状態
- Premium CTA（`data-testid="shrine-detail-premium-teaser"`）→「ログインして意味を深掘りする」
- favorite: 「ログインしてあとで見返す」（guest mode、`initial: {fav:false, favorite_id:null}`）
- raw key / `undefined` / `null` / raw JSON: **なし**

**Route CTA**: 「Googleマップで経路案内」
`https://www.google.com/maps/dir/?api=1&destination=35.6717809%2C139.799519&travelmode=walking`
- 表示あり / clickable / dead linkなし / fatal navigation errorなし
- 座標はproduction DBの `latitude`/`longitude` と一致
- **実際の外部起動は `BLOCKED_BY_ENVIRONMENT`**（`www.google.com` へのCONNECTがegress policyで拒否される）。リンク生成までを確認範囲とした

**Dark UI: NG 2件（PSQ-002 P1 / PSQ-007 P2）** — 詳細は Findings

### Phase 10 — Favorite / Save

`VERIFIED_LOCAL_PRODUCTION_BUILD`（初期state・空state・保存済みstate）
`BLOCKED_BY_ENVIRONMENT`（実際のsave/duplicate/refresh後stateのproduction往復）

- 未ログイン初期state: 「ログインしてあとで見返す」（`aria-pressed="false"`）— dead UIにならず、authへ誘導
- `/favorites` 未ログイン: 「お気に入りの神社はまだありません」＋「近くの神社を探す」CTA（正常なempty state）
- ログイン相当: 「富岡八幡宮 / 住所 / 神社の詳細を見る / 保存解除」を描画、console error 0件
- save action自体のbackend往復（重複押下・refresh後の永続性）は production backendへ到達できないため未検証

### Phase 11 — MyPage

未ログイン（`VERIFIED_LOCAL_PRODUCTION_BUILD`）:
- `/mypage` → `/auth/login?returnTo=%2Fmypage` へredirect
- `/mypage/history` → `/auth/login?returnTo=%2Fmypage%2Fhistory` へredirect
- crashなし・dead UIなし。login formは正常描画
- 注: `middleware.ts` は `/login?next=...` を組み立てるが、実際の着地は `/auth/login?returnTo=...` である（`/login/page.tsx` 側のredirect）。挙動としては正しく、ユーザーに影響なし

ログイン相当（`VERIFIED_LOCAL_PRODUCTION_BUILD`）:
- タブ「プロフィール / 投稿した神社 / 保存した神社 / 参拝履歴 / 相談履歴」表示
- プロフィール項目（ニックネーム・生年月日・出生時間・出生地・参拝スタイル）表示
- 「派生プロフィール」（九星 / 五行 / ライフパス / 吉方位）は全て「未計算」＋「年盤をもとに凶方位を除外した補助情報です。月盤・日盤は含みません。」の但し書きあり
- horizontal overflow なし（375–1280）、console error 0件、raw key露出なし

### Phase 12 — Consultation History

`VERIFIED_LOCAL_PRODUCTION_BUILD`

- list loads: スレッド1件（タイトル / 日付 / 最終メッセージ / 「2件のやりとり」）
- empty state / auth未ログインstate / fetch失敗stateは実装上分岐あり（`ConsultationHistoryListView.tsx:56/73/91`）
- raw key / `undefined` / `null`: **なし**
- Explanation-only Factが推薦理由として誤表示される事象: list画面では**該当なし**（list画面はEvidenceを表示しない）
- **Dark UI: 重大なNG（PSQ-003、P1）** — 詳細は Findings
- `/mypage/history/[tid]` の詳細画面は、production実threadを生成できないため今回未到達（`BLOCKED_BY_ENVIRONMENT`）。
  なお同画面については既存監査 `docs/audit/app-wide-evidence-dark-ui-regression.md` の Bug-2（P2、LIVE）が未解決として記録されている

### Phase 13 — Compass Input

`VERIFIED_LOCAL_PRODUCTION_BUILD`

- route loads、目的chip 6件＋「その他の目的を見る（他9件）」→ 展開で全15件
- 出発地点: 「出発地点は設定されていません。」→「変更する」→ bottom Sheet「出発地点を選ぶ」
- 生年月日 `<input type="date" id="compass-birthdate">` 操作可能
- validation: purpose / birthdate / origin いずれか未設定でsubmitしても遷移せず、`role="alert"` のエラー文が出る設計（`CompassClient.tsx:216/236/257`）
- 375px でもchip・Sheetともclipなし
- **Sheet内 `OriginSelector` がDark UI非対応（PSQ-005、P2）**

### Phase 14 — Compass Result

`VERIFIED_LOCAL_PRODUCTION_BUILD`

- 「今月、意識したい方向」→ `年盤・月盤 共通` badge ＋ 8方位visual ＋「今月意識したい方向: 北西・東」
- 註記「年盤と月盤の両方で重なる、今月の参考方位です。日盤は使用していません。（**参考情報です**）」
- 「この方向の参拝候補」→ `ShrineCardCompact` 3枚
  - 神社名（`--kt-color-text-primary`）が **Dark surface上で明瞭に判読可能** → **PR #2597 の FQA-001 修正が有効に効いていることを実測で確認**
  - 距離チップ「約1.2km」/「約8.4km」
  - 「相談内容・ご利益との一致」＋ reason
  - 「参考情報: …」prefix付きのexplanation-only fact（Ranking理由と明確に分離）
  - 住所 / 「詳細だけ見る」
- `/shrines/49?ctx=compass&recommendation_instance_id=...&recommendation_rank=1` へ遷移成功
- raw key / `undefined` / `null` / `NaN`: **なし**
- horizontal overflow: **なし**（375/390/430/1280）

### Compass Ranking Truth

| 確認項目 | 結果 |
|---|---|
| 九星気学をscore理由として誤表示していないか | **PASS**。方位は独立セクションで「参考情報です」と明示。カード内のmatch reasonは `reason` / `reason_facts` 由来のみで、方位・九星への言及なし |
| astrology compatibilityを根拠なく表示していないか | **PASS**。Compass結果画面にastrology由来の断定表示なし |
| filter-only情報をranking score reasonとして表示していないか | **PASS**。方向・距離条件は「参考情報: 今回の方向・距離の条件に合う候補です」として *参考情報* 側に置かれ、「相談内容・ご利益との一致」とは別行 |

制約: 上記はいずれも**表示契約（presentation contract）レベルの確認**である。production backendのranking出力そのものは到達不能のため未検証（`BLOCKED_BY_ENVIRONMENT`）。

### Evidence Boundary（重大な意味崩れの有無）

| 境界 | 結果 |
|---|---|
| Stored Fact | PASS。Shrine Detailの御祭神・由緒・出典はproduction DBの `deities` / `histories` / `sources` と1:1一致（`verification_status: source_confirmed`） |
| Derived Meaning | PASS。「神社との意味の接続」は独立見出し配下に分離 |
| Runtime Match | PASS。「相談内容・ご利益との一致」ラベルで明示 |
| Ranking Reason | PASS。「相談との一致が強い」/「上位理由」として別扱い |
| Filter / Eligibility Context | PASS。Compassの方向・距離は「参考情報」側 |

**重大な意味崩れは検出せず。** 表示テキストの意味は正しいが、**Concierge Recommendationではその一部が視覚的に読めない**（PSQ-001）。これはEvidence契約の破壊ではなくDark UIの問題として分類した。

---

## Phase 15 — Dark UI Smoke

`.dark` トークン実値（`apps/web/src/styles/tokens.css:201-243`）:
`background-base #07101f` / `background-subtle #0b1424` / `surface-default #101827` / `surface-elevated #0b1424` /
`text-primary #f7f0e3` / `text-secondary #a99b80` / `text-muted #c4b89a` / `text-inverse #fff` /
`border-default #384154` / `border-focus emerald-400` / `action-primary emerald-500` / `action-primary-text #fff`
加えて `globals.css` の `.dark` が `body` 背景を `--background`（実測 `#020618`）に設定。

| 観点 | 結果 |
|---|---|
| Background / Surface / Elevated Surface | PASS（Home / Concierge input / Compass / Shrine Detail 本体 / MyPage） |
| Primary / Secondary / Muted Text | 主要routeはPASS。ただし **light surface上でこれらtokenを使う箇所がNG**（PSQ-001） |
| Border / Input | PASS |
| Primary CTA | 描画は成立するが token対比が **2.47:1**（PSQ-004、P2） |
| Secondary CTA | 一部でemerald系textが 2.33–3.31:1（PSQ-007、P2） |
| Premium | PASS（`--kt-color-premium-surface` / `--kt-color-premium-accent`） |
| Error / Success / Warning | 主要journeyでは未発火。`text-rose-700` on dark surface は約3.0:1（PSQ-007に含む） |
| Overlay / Sheet / Modal | Sheet自体はPASS。**内部の `OriginSelector` がlight固定（PSQ-005、P2）** |
| Toast | 主要journeyで未発火（未検証） |
| unintended white card | **検出（PSQ-001 / PSQ-005）** |
| white-on-white | **検出（PSQ-002: `text-white` on `--kt-color-text-primary` #f7f0e3 = 1.13:1）** |
| black-on-dark | **検出（PSQ-003 / PSQ-008: `text-stone-800/900` on `#020618` = 1.15–1.33:1）** |
| hover contrast regression | 検出（`hover:bg-slate-100` on Shrine Detail 戻るbutton、PSQ-007） |
| disabled unreadable | 「質問する」disabled時は `opacity-60` が乗るためさらに悪化（PSQ-002に含む） |
| focus ring invisibility | PASS（emerald-400のfocus ringはdark背景上で明瞭） |

---

## Phase 16 — Mobile Smoke（375 / 390 / 430）

| 観点 | 375 | 390 | 430 |
|---|---|---|---|
| horizontal overflow（`scrollWidth > clientWidth`） | なし | なし | なし |
| clipped button / card | なし | なし | なし |
| sticky overlap（sticky header z-100） | なし | なし | なし |
| bottom nav collision | 該当なし（bottom nav未実装） | 同左 | 同左 |
| modal / sheet overflow | なし（Compass 出発地点Sheet、`max-h-[85vh] overflow-y-auto`） | なし | なし |
| long shrine name | 「多摩川浅間神社」等でwrap正常。Shrine Detail headerは `truncate` で1行維持 | 同左 | 同左 |
| long reason text | 折返し正常、clipなし | 同左 | 同左 |
| source URL wrapping | Shrine Detailの出典linkはtitle表示（生URLを出さない）ため折返し問題なし | 同左 | 同左 |
| keyboard-induced blockage | headless実行のため未検証（`BLOCKED_BY_ENVIRONMENT`） | 同左 | 同左 |

対象route: Home / Concierge input / Concierge Recommendation / Shrine Detail / Compass input / Compass result / MyPage / Consultation History / Favorites / `/shrines`。全てで overflow 0件。

## Phase 17 — Desktop Smoke（1280）

- excessive width: なし（Concierge/Shrine Detailは `max-w-md lg:max-w-2xl`、Homeは `max-w-4xl`、Compassは `max-w-2xl` で中央寄せ）
- broken card grid / alignment: なし
- CTA hierarchy: Primary（emerald塗り）→ Secondary（border）→ text link の順序が保たれている
- modal / sheet: 正常
- Dark UI: mobileと同一の結果（PSQ-001〜003は1280でも同様に再現）
- Desktop最適化の新規着手はしていない

---

## Phase 18 — Console Error Audit

Scenario A/B/C を4viewportで実行中に収集（計60 step）。

| 分類 | 件数 | 内容 |
|---|---|---|
| ERROR | 2種 | ① `Failed to load resource: 401 (Unauthorized)` — 未ログイン時の `GET /api/users/me/`。**匿名ユーザーの正常系**（productionでも匿名は401）。② `Failed to load resource: 404 (Not Found)` — `/api/shrine-interactions/`・`/api/visits/`。**本監査のlocal stub backendが当該endpointを実装していないことに起因するQA環境固有の事象**であり、製品欠陥ではない |
| WARNING | 0 | — |
| React hydration error | **0** | — |
| uncaught exception / pageerror | **0** | — |
| invalid DOM nesting | **0** | — |
| missing key warning | **0** | — |
| map error | 0（外部起動未実施） | — |
| auth error | 上記401のみ（設計どおり） | — |
| source map error | 0 | — |

**release blockerに該当するconsole所見なし。**

## Phase 19 — Network / API Audit

| 分類 | 結果 |
|---|---|
| failed requests | `net::ERR_ABORTED` が `?_rsc=` 付きURLに多数。これは**Next.js App Routerのlink prefetchが遷移で中断された正常な挙動**。実際の画面遷移は全て成功しており、blockerではない |
| unexpected 4xx | なし（401はanonymous正常系、404はstub未実装endpoint） |
| unexpected 5xx | **0件** |
| CORS | 0件（frontendは常に自ドメインBFF経由。`guard:no-backend-direct` により直アクセスは構造的に排除されている） |
| timeout | 0件 |
| duplicate request explosion | なし。`GET /api/users/me/` が画面ごとに1回、`POST /api/concierge/chat/` は1 submitあたり1回 |
| malformed payload / parse error | 0件 |
| third-party telemetry | PostHog（`posthog-js`）・Google Maps・Google Places はegress policyで到達不可。**別分類（`BLOCKED_BY_ENVIRONMENT`）とし、失敗としてカウントしていない** |

production側APIについては、`GET /api/shrines`（`count: 104`, 200, `x-render-origin-server: gunicorn`）と `GET /api/shrines/49/data`（200）が正常応答することを確認済み（`VERIFIED_PRODUCTION`）。

## Phase 20 — Raw / Broken Text Audit

全主要routeの `document.body.innerText` を4viewportで走査。

| 検出対象 | 結果 |
|---|---|
| `undefined` | **0件** |
| `null` | **0件** |
| `[object Object]` | **0件** |
| `NaN` | **0件** |
| raw JSON | **0件** |
| internal need slug（`money` / `career` / `mental` / `rest` / `relationship` / `protection` / `courage` / `focus` / `family` / `study` / `health` / `communication` / `marriage` / `love` / `travel_safe`） | **0件**（全て表示ラベルへ変換済み。例: `career` → 「転機・仕事」/「仕事について考えたい」） |
| internal source key（`shrine_official` / `source_confirmed` / `goriyaku:` / `history_theme` / `explanation_only` / `reason_facts` / `recommendation_reason_v4`） | **0件** |
| empty heading | **0件**（実行時走査） |
| dangling colon / punctuation | 実行時走査では0件。ただし**静的に1件検出**（PSQ-008: `"で見ること"`） |

productionのSSR HTML（`/`、`/shrines/49`）に対しても同一観点で確認し、いずれも0件。

---

## Smoke Matrix

| Feature | Mobile (375/390/430) | Desktop (1280) | Console | Network | Verdict |
|---|---|---|---|---|---|
| Home | PASS | PASS | PASS | PASS | **PASS** |
| Concierge (input) | PASS | PASS | PASS | PASS | PASS（PSQ-006 P2） |
| Recommendation | 機能PASS / Dark UI **FAIL** | 機能PASS / Dark UI **FAIL** | PASS | PASS | **FAIL（PSQ-001 P1）** |
| Shrine Detail | 機能PASS / Dark UI **FAIL** | 機能PASS / Dark UI **FAIL** | PASS | PASS | **FAIL（PSQ-002 P1、PSQ-007 P2）** |
| Favorite | PASS（表示のみ） | PASS（表示のみ） | PASS | PASS | PARTIAL（往復は `BLOCKED_BY_ENVIRONMENT`） |
| MyPage | PASS | PASS | PASS | PASS | **PASS** |
| Consultation History | Dark UI **FAIL** | Dark UI **FAIL** | PASS | PASS | **FAIL（PSQ-003 P1）** |
| Compass | PASS | PASS | PASS | PASS | PASS（PSQ-005 P2） |

## Journey Matrix

| Journey | Start | End | Result |
|---|---|---|---|
| Concierge | Home | Shrine Detail | **完走**（`/` → `/concierge` → submit → Recommendation → `/shrines/49?ctx=concierge&tid=9001`）。ただしRecommendation画面の主要テキストが判読不能（PSQ-001） |
| Route | Shrine Detail | Route destination | **リンク生成まで確認**。外部起動は `BLOCKED_BY_ENVIRONMENT` |
| Saved | Recommendation | MyPage | **完走**（保存済みstateの描画まで）。実save往復は `BLOCKED_BY_ENVIRONMENT` |
| History | MyPage | History Detail | **list までPASS**。`/mypage/history/[tid]` は production thread を生成できず未到達（`BLOCKED_BY_ENVIRONMENT`） |
| Compass | Compass Input | Shrine Detail | **完走**（目的→生年月日→出発地点→submit→方向＋候補3件→`/shrines/49?ctx=compass&...`） |

---

## Findings

### PSQ-001 — Concierge Top Recommendation Hero が light card surface のまま Dark UI token text を載せている

| 項目 | 内容 |
|---|---|
| ID | `PSQ-001` |
| Severity | **P1** |
| Feature | Recommendation Result |
| Route | `/concierge`（`/concierge/full` も同一component） |
| Viewport | 375 / 390 / 430 / 1280（全て再現） |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD`（base SHAはproduction deployment build id `JxFYOxxOxSuza627IqCvh` と一致するため、production codeも同一） |
| Scenario | A |

**Expected**
Recommendation Heroの神社名・Ranking Reason・参考情報・参拝前アクションが、Dark UI上で判読可能であること。

**Actual**
`ConciergeTopRecommendationHero.tsx` のcard surfaceがtoken化されておらず、明るい固定色のまま:

- L137 `bg-gradient-to-b from-emerald-50/80 to-white`（section本体）
- L166 `border-emerald-100 bg-white/70`（Runtime Matchカード）
- L196 `border-teal-100 bg-teal-50/70`（Actionカード）
- L187 `bg-slate-100 text-slate-500`（「参考情報」pill）

一方その上のテキストはDark UI tokenを参照している:

- L144 神社名 `text-[var(--kt-color-text-primary)]`（`.dark` で `#f7f0e3`）
- L176 Ranking Reason `text-[var(--kt-color-text-muted)]`（`#c4b89a`）
- L190 Explanation-only Fact `text-[var(--kt-color-text-muted)]`
- L202 Action `text-[var(--kt-color-text-secondary)]`（`#a99b80`）

実測コントラスト（**実描画ピクセルのサンプリング**。測定方法は本節末尾を参照。390px）:

| 要素 | 前景 | 実描画背景 | 比 | 必要 |
|---|---|---|---|---|
| **神社名「富岡八幡宮」**（20px / 600） | `#f7f0e3` | `#c7d5d2` | **1.34:1** | 4.5 |
| 「相談との一致が強い」（Ranking Reason, 12px） | `#c4b89a` | `#f4f7f6` | **1.83:1** | 4.5 |
| 「応神天皇」（参考情報 = Explanation-only Fact, 12px） | `#c4b89a` | `#e3eae8` | **1.61:1** | 4.5 |
| 「参拝前に、今いちばん整理したいことを…」（Action, 14px） | `#a99b80` | `#effaf7` | **2.56:1** | 4.5 |

**推薦のTop候補名そのもの（1.34:1）が実質判読不能**であり、Ranking Reason・参考情報・参拝前アクションも同様に読めない。
判読できるのは、暗色を直接指定している reason 本文（`text-slate-*` 系）と emerald のラベルのみである。スクリーンショットでも同じ状態を確認した。

**Reproduction Steps**
1. `/concierge` を開く
2. 相談テキストを入力してsubmit
3. Recommendation Heroを見る（375/390/430/1280いずれでも同じ）

**Console Evidence**: なし（描画は成功しておりerrorは出ない）
**Network Evidence**: なし

**測定方法（本監査のcontrast実測すべてに共通）**
`background-image`（gradient）や `bg-white/70` のような半透明レイヤーは computed style からは実効背景を復元できないため、
**Chromiumで実際に描画されたピクセルを対象要素の直近から採取し（6×6 patchの最頻色）**、要素の computed `color`（`lab()` / `oklab()` はsRGBへ変換）との間で
WCAG 2.1 相対輝度比を算出した。したがって本文書の比の値は「計算上の推定」ではなく「実際に画面に出ている色」である。

**Likely Ownership**
`apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`（L137 / L166 / L187 / L196）

**Suggested Follow-up Scope**
PR #2597（`ShrineCardCompact`のFQA-001修正）と**同一クラスの欠陥**。同じ方針でcard surfaceのみを既存 `--kt-color-*` semantic tokenへ置換する。新規token・新規色は不要。
なお既存監査 `docs/audit/final-evidence-dark-ui-visual-qa.md:141,198` は「Concierge Heroのカード本体…PASS」と判定しているが、その判定対象は `ConciergeSectionsRenderer.tsx:53` の `conciergeSoftCardClass` であり、**`ConciergeTopRecommendationHero.tsx` のsection/cardクラスは対象外だった**。本件は未報告の新規検出である。

---

### PSQ-002 — Shrine Detail「この神社について質問する」が white-on-cream / dark-on-dark で使用不能

| 項目 | 内容 |
|---|---|
| ID | `PSQ-002` |
| Severity | **P1** |
| Feature | Shrine Detail |
| Route | `/shrines/[id]` |
| Viewport | 375 / 390 / 430 / 1280（全て再現） |
| Environment | `VERIFIED_PRODUCTION`（該当markup/classをproduction SSR HTMLで確認）＋ `VERIFIED_LOCAL_PRODUCTION_BUILD`（contrast実測） |
| Scenario | A / C |

**Expected**
質問入力欄に入力した文字と、送信buttonのラベルが判読できること。

**Actual**
`ShrineDeepDivePrompt.tsx`:

- L140 `<input ... bg-[var(--kt-color-surface-default)] ... text-slate-800 placeholder:text-slate-400>`
  → 入力文字 `#1d293d` on `#101827` = **1.21:1**（placeholderは `#94a3b8` で約6.4:1のため読めるが、**実際に打った文字だけが消える**）
- L147 `<button ... bg-[var(--kt-color-text-primary)] ... text-white>`
  → `#ffffff` on `#f7f0e3` = **1.13:1**。さらにdisabled時は `disabled:opacity-60` が乗る

production HTMLでも同一class（`text-slate-800`、`bg-[var(--kt-color-text-primary)] ... text-white`）を確認済み。

**Reproduction Steps**
1. `/shrines/49` を開く
2. 「この神社について質問する」欄に任意の文字を入力する → 入力文字が見えない
3. 「質問する」buttonのラベルを見る → 背景とほぼ同色

**Console Evidence**: なし / **Network Evidence**: なし

**Likely Ownership**: `apps/web/src/components/shrine/detail/ShrineDeepDivePrompt.tsx`（L140、L147）

**Suggested Follow-up Scope**
`text-slate-800` → `--kt-color-text-primary`、button背景 → `--kt-color-action-primary` + `--kt-color-action-primary-text`（既に確立済みのpattern）。error文の `text-rose-700`（L152）も同時に見直し対象。

---

### PSQ-003 — Consultation History が完全に light theme のまま Dark UI 上に描画される

| 項目 | 内容 |
|---|---|
| ID | `PSQ-003` |
| Severity | **P1** |
| Feature | Consultation History |
| Route | `/mypage/history` |
| Viewport | 390 / 1280（確認したviewport全て） |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` |
| Scenario | B |

**Expected**
相談履歴の見出し・スレッドタイトル・最終メッセージがDark UI上で判読できること。

**Actual**
`ConsultationHistoryListView.tsx` は全stateで `text-stone-*` / `bg-stone-50/30` / `bg-white` のみを使用し、`--kt-color-*` を一切参照していない。

実測（body背景 `#020618`、カード背景は `stone-50/30` 合成後 `#4c4f5b`）:

| 要素 | class | 前景 | 背景 | 比 | 必要 |
|---|---|---|---|---|---|
| 見出し「相談履歴」(20px) | L48/107-108 `text-stone-800` | `#292524` | `#020618` | **1.33:1** | 4.5 |
| スレッドタイトル (16px) | L120 `text-stone-900` | `#1c1917` | `#4c4f5b` | **2.15:1** | 4.5 |
| 最終メッセージ preview (14px) | L123 `text-stone-600` | `#57534d` | `#4c4f5b` | **1.06:1** | 4.5 |
| 日付 (12px) | L121 `text-stone-500` | `#79716b` | `#4c4f5b` | **1.69:1** | 4.5 |
| 「N件のやりとり」(12px) | L124 `text-stone-400` | `#a6a09b` | `#4c4f5b` | 3.14:1 | 4.5 |

最終メッセージ（1.06:1）は事実上不可視。空state（L94 `text-stone-600`）・fetch失敗state（L76 `text-rose-700` on `bg-rose-50/40`）・未ログインstate（L59）も同じ問題を持つ。

**Reproduction Steps**
1. ログイン状態で `/mypage/history` を開く
2. 見出しとスレッドカードの本文を見る

**Console Evidence**: なし（console error 0件）/ **Network Evidence**: なし

**Likely Ownership**: `apps/web/src/components/views/ConsultationHistoryListView.tsx`（L47-124 全体）

**Suggested Follow-up Scope**
画面全体の `text-stone-*` / `bg-stone-*` / `bg-white` を既存 `--kt-color-*` semantic tokenへ置換。Shrine Detailの `ShrineFactSection` 等で確立済みのcard patternを流用でき、新規token不要。

---

### PSQ-004 — Primary Action token の対比が WCAG AA 未満（全画面のPrimary CTAに影響）

| 項目 | 内容 |
|---|---|
| ID | `PSQ-004` / Severity **P2** |
| Feature | 全画面（Design Token） |
| Route | 全route |
| Viewport | 全viewport |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` |

**Expected / Actual**
`--kt-color-action-primary`（`emerald-500` = `#00bc7d`）＋ `--kt-color-action-primary-text`（`#ffffff`）の組合せが **2.47:1**（14px以下のtextには4.5:1が必要）。

影響範囲（実測で確認したもの）: header「マイページ」「ログイン」、Recommendation「神社の詳細を見る」、Shrine Detail「Googleマップで経路案内」、Compass「今月の方向を確認する」・選択中の目的chip、Favorites「近くの神社を探す」。

**判読自体は可能**であり、journeyを止めない。またこれは `tokens.css:242-244` に「母艦Decision: Emerald維持、Gold不採用」として明記された**意図的な設計判断**であるため、bug fixではなく製品判断が必要と考える。P2として記録し本PRでは修正しない。

**Likely Ownership**: `apps/web/src/styles/tokens.css`（`.dark` の `--kt-color-action-primary` / `--kt-color-action-primary-text`）

---

### PSQ-005 — Compass 出発地点 Sheet 内の `OriginSelector` が light 固定（意図しない white card）

| 項目 | 内容 |
|---|---|
| ID | `PSQ-005` / Severity **P2** |
| Feature | Compass（Concierge補助条件でも同component） |
| Route | `/compass`、`/concierge` |
| Viewport | 375 / 390 / 430 / 1280 |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` / Scenario C |

**Actual**
`OriginSelector.tsx` はDark UI tokenを一切使わない:
L87 `legend text-stone-600` / L98 未選択mode `border-stone-300 bg-white text-stone-700` / L98 選択時 `bg-emerald-50 text-emerald-900` / L118 `border-stone-300` の入力欄 / L163 `bg-white` / L168 `text-emerald-800`。

Dark UIのbottom Sheet上で4つのmode buttonが**白いカードとして浮く**（判読自体は可能。dark-on-white）。
一方 L168 のstatus行「出発地点は設定されていません。」は `text-emerald-800` on `#020618` = **2.65:1** で読みづらい。

Compassの必須入力導線ではあるが、選択操作は成立し journeyは完走するためP2とした。

**Likely Ownership**: `apps/web/src/features/concierge/components/OriginSelector.tsx`

---

### PSQ-006 — Concierge 補助条件パネルの見出し・説明が低コントラスト

| 項目 | 内容 |
|---|---|
| ID | `PSQ-006` / Severity **P2** |
| Feature | Concierge Input / Route `/concierge` / 全viewport |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` / Scenario A |

**Actual**
`bg-stone-50/60` の補助条件パネル（合成後 `#9ca0a5`）上で `text-stone-500`:
- 「もう少し自分に合わせる（任意）」 **1.82:1**
- 「参拝の希望・誕生日・ご利益・参拝の詳細は、相談テーマを補う条件として扱います。」 **1.82:1**

パネル自体は折り畳み済み（「条件を開く」）で、主要導線を止めない。

---

### PSQ-007 — Shrine Detail の secondary CTA / hover が Dark UI で低コントラスト

| 項目 | 内容 |
|---|---|
| ID | `PSQ-007` / Severity **P2** |
| Feature | Shrine Detail / Route `/shrines/[id]` / 全viewport |
| Environment | `VERIFIED_PRODUCTION`（class）＋ `VERIFIED_LOCAL_PRODUCTION_BUILD`（実測） |

**Actual**
- 「参拝しました」 `text-emerald-800` on `#101827` = **2.34:1**
- 「保存した神社を見る」 `text-emerald-700` on `#101827` = **3.31:1**
- 「ご利益」見出し `text-[var(--kt-color-text-secondary)]` = 2.73:1
- Premium teaser本文 `text-[var(--kt-color-text-secondary)]` = 2.73:1
- 「← 戻る」button `hover:bg-slate-100`（light hover。Dark UI上でhover時のみ明るいカードが出る hover regression）

いずれも判読可能なため主要導線を止めない。

---

### PSQ-008 — Premium section 見出しが助詞から始まる壊れたリテラル `"で見ること"`

| 項目 | 内容 |
|---|---|
| ID | `PSQ-008` / Severity **P2** |
| Feature | Shrine Detail（Premium tier） / Route `/shrines/[id]` |
| Environment | **`VERIFIED_PRODUCTION`**（production `/shrines/49` のRSC payload内に文字列として存在することを確認） |

**Actual**
`buildShrineDetailModel.ts:146` に `heading: "で見ること"` がハードコードされている。日本語として助詞「で」から始まる断片であり、本来は神社名など先行語を伴う想定と見られる。

production RSC payloadの `premiumDisplaySections[0].section.heading` に `"で見ること"` として実在する。ただし `tier: "premium"` のため、**Premium未加入ユーザーには描画されない**（今回のguest/free journeyのDOM走査では0件）。Premium加入ユーザーには見出しとして表示される。

**Likely Ownership**: `apps/web/src/lib/shrine/buildShrineDetailModel.ts:146`

---

### PSQ-009 — `/shrines`（Explore）の見出しが Dark UI 上で判読不能

| 項目 | 内容 |
|---|---|
| ID | `PSQ-009` / Severity **P1** |
| Feature | Shrine一覧（Home「神社一覧も見る」およびFavorites empty stateからの導線） |
| Route | `/shrines` / Viewport 375 / 390 / 430 / 1280 |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` / Scenario C（付随確認） |

**Actual**
`ExploreLayout.tsx` がlight固定:
- L51 `<h1 class="text-xl font-medium text-stone-900">神社をたどる</h1>` → `#1c1917` on `#020618` = **1.15:1**（ページタイトルが読めない）
- L50 `text-stone-500` "EXPLORE" = 4.19:1
- セクション見出し `text-stone-800` on `bg-stone-50/30`（実描画 `#4c4f5b`） = **1.86:1**
- ラベル「過ごし方」「歴史テーマ」 `text-stone-500` = **1.70:1**
- 「NEARBY」「今いる場所から行きやすい神社を確認できます。」 = **1.48:1**（computed style基準の概算）

**注記**: `/shrines` は依頼文書のRoute Matrix（Home / Concierge / Recommendation / Shrine Detail / MyPage / History / Compass）には含まれない**補助route**である。ただしHomeから直接遷移でき、ページタイトル自体が読めないためP1として記録する。

**Likely Ownership**: `apps/web/src/features/explore/components/ExploreLayout.tsx`

---

### PSQ-010 — `/consultation` が未リンクのプレースホルダのまま production に存在する

| 項目 | 内容 |
|---|---|
| ID | `PSQ-010` / Severity **P3** |
| Route | `/consultation` |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` |

**Actual**
`src/app/consultation/page.tsx` の実体は `<div className="p-6">参拝コンシェルジュ（仮）</div>` のみ。スタイルなし・導線なし・行き止まり。
アプリ内から `/consultation` への `href` は0件（未リンク）だが、URL直打ちで到達できる。

---

### PSQ-011 — meaning v2 fallback 時に「⑤ 補足（象徴・ご利益）」だけが単独で表示される

| 項目 | 内容 |
|---|---|
| ID | `PSQ-011` / Severity **P3** |
| Feature | Shrine Detail / Route `/shrines/[id]` |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD`（**fallback経路のみ**） |

**Actual**
`{backend}/api/shrines/{id}/meaning/` が取得できない場合、`meaningPayloadSource` が v2 にならず legacy sectionへfallbackする。このとき画面には `⑤ 補足（象徴・ご利益）` のみが表示され、①〜④が存在しないため番号が孤立する。

production（meaning v2が取得できている状態）では `freeDisplaySections`（「神社との意味の接続」）が描画され、この孤立番号は出ない。したがって**通常時には発生しないfallback経路の表示崩れ**である。

**注記**: 本監査環境ではlocal stubが `/meaning/` に404を返しているため、この経路を意図せず踏んだ。production側で `/meaning/` が落ちた場合の縮退表示として記録する。

**Likely Ownership**: `apps/web/src/lib/shrine/buildShrineDetailModel.ts` / `ShrineDetailArticle`

---

### PSQ-012 — auth 画面が Dark UI 非対応

| 項目 | 内容 |
|---|---|
| ID | `PSQ-012` / Severity **P2** |
| Route | `/auth/login`（`/mypage` 未ログイン時のredirect先） |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` / Scenario B |

**Actual**
submit buttonが `bg-blue-600 text-white`（token非使用）、「新規登録はこちら」が `text-blue-600` on `#020618` = **3.84:1**。
form自体は操作可能でcrashしないが、product全体のDark UI token体系から外れている。

---

## Severity Summary

| Severity | 件数 | ID |
|---|---|---|
| **P0 Critical** | **0** | — |
| **P1 High** | **4** | PSQ-001, PSQ-002, PSQ-003, PSQ-009 |
| P2 Medium | 6 | PSQ-004, PSQ-005, PSQ-006, PSQ-007, PSQ-008, PSQ-012 |
| P3 Low | 2 | PSQ-010, PSQ-011 |

P0が0件である根拠: app起動不能・major route crash・data corruption・cross-user data exposure・auth/security failure・Recommendationの完全破壊 のいずれも観測されなかった。全routeが200で描画され、Recommendationはデータとしては正しく生成・表示されている。

---

## Final Verdict

# BLOCKED

P1が4件検出されたため（Phase 21/22の定義による）。

**性質の要約（事実）**: 検出したP1は4件とも**Dark UI移行の取り残し**という単一クラスの欠陥である。
機能・API・Ranking・Evidence契約はいずれも健全で、P0は0件、5xxは0件、hydration errorは0件、raw key露出は0件、mobile overflowは0件。
Concierge / Compass / Shrine Detail / MyPage の各journeyは**すべて完走している**。壊れているのは「完走できるか」ではなく「読めるか」である。

**推測**: PSQ-001 は PR #2597 が修正したFQA-001と同一クラスであり、PR #2595時点の監査が `conciergeSoftCardClass` を Hero と取り違えて PASS 判定したために取り残された可能性が高い。PSQ-003 / PSQ-009 / PSQ-012 は、Dark UI token移行が `features/concierge` / `components/shrine` 系に集中し、`components/views` / `features/explore` / `app/auth` 系に及んでいないという範囲の問題と見られる。

**反証の余地（盲点）**: 本監査の contrast 実測は **local production build** 上で行っている。production alias が base SHA を配信していること（build id 一致）と、PSQ-002 については production HTML 上で同一classを直接確認したことで裏は取れているが、**PSQ-001 / PSQ-003 / PSQ-009 の実 production レンダリングは確認できていない**。Vercel側の環境変数やビルド差異が Dark UI 適用に影響する経路は確認範囲では見当たらなかったが、`BLOCKED_BY_ENVIRONMENT` の制約下での推定であることを明記する。
また `/mypage/history/[tid]`（History Detail）と Toast は今回未到達であり、**検証していないものをPASS扱いしていない**。

---

## Follow-up Candidates

本branchでは一切修正しない。以下は別PR候補としての記録であり、優先順位は決めない（母艦へ返す）。

| # | Proposed branch | Exact scope | Affected files | Risk |
|---|---|---|---|---|
| F-1 | `fix/concierge-hero-dark-surface` | PSQ-001。Hero の card surface 4箇所（L137 gradient / L166 `bg-white/70` / L187 pill / L196 `bg-teal-50/70`）を既存 `--kt-color-*` semantic token へ置換。新規token・新規色を追加しない。Ranking / Scoring / Evidence契約 / propsは無変更 | `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx` | **低**。PR #2597と同一手法。既存testは背景色をassertしていない見込みだが要確認 |
| F-2 | `fix/shrine-deep-dive-prompt-dark-ui` | PSQ-002。input の `text-slate-800` と button の `bg-[var(--kt-color-text-primary)] text-white` を token 化。error文 `text-rose-700` も併せて見直し | `apps/web/src/components/shrine/detail/ShrineDeepDivePrompt.tsx` | **低**。表示のみ。deep-dive APIには触れない |
| F-3 | `fix/consultation-history-dark-ui` | PSQ-003。list view 全state（通常 / empty / 未ログイン / fetch失敗）の `text-stone-*`・`bg-stone-*`・`bg-white` を token 置換 | `apps/web/src/components/views/ConsultationHistoryListView.tsx` | **低〜中**。stateが4つあるため全state分のvisual確認が必要 |
| F-4 | `fix/explore-layout-dark-ui` | PSQ-009。`/shrines` の見出し・ラベル・セクション背景を token 化 | `apps/web/src/features/explore/components/ExploreLayout.tsx`（+ 同featureの子component要確認） | **中**。Explore配下の他componentにも同種のlight固定が波及している可能性があり、範囲確定が先 |
| F-5 | `fix/origin-selector-dark-ui` | PSQ-005。`OriginSelector` 全体を token 化。Compass Sheet / Concierge 補助条件の両方に影響するため両画面のvisual確認が必要 | `apps/web/src/features/concierge/components/OriginSelector.tsx` | **中**。2画面で共有されている |
| F-6 | `fix/shrine-detail-secondary-cta-contrast` | PSQ-007。secondary CTAのemerald系text・`hover:bg-slate-100` を token 化 | `apps/web/src/components/shrine/ShrineSaveButton.tsx`、`ShrineDetailShell.tsx` ほか | 低 |
| F-7 | `fix/shrine-detail-premium-heading-copy` | PSQ-008。`"で見ること"` の見出し文言を確定する。**文言そのものが未決定のため、実装前に母艦のcopy決定が必要** | `apps/web/src/lib/shrine/buildShrineDetailModel.ts:146` | 低（実装）/ **要decision**（文言） |
| F-8 | `fix/concierge-aux-panel-contrast` | PSQ-006 | `apps/web/src/app/concierge/ConciergeClientFull.tsx` 周辺 | 低 |
| F-9 | `fix/auth-pages-dark-ui` | PSQ-012。login / register 画面の token 化 | `apps/web/src/app/auth/login/page.tsx` ほか | 低 |
| F-10 | `chore/remove-consultation-placeholder` | PSQ-010。未リンクのplaceholder routeを削除するか、正式画面にするかを決める | `apps/web/src/app/consultation/page.tsx` | 低（削除）/ **要decision** |
| F-11 | `fix/shrine-detail-meaning-fallback-numbering` | PSQ-011。meaning v2 fallback時の番号付き見出しの整合 | `apps/web/src/lib/shrine/buildShrineDetailModel.ts` | 中（fallback経路の再現条件を先に確定する必要あり） |
| F-12 | （token決定事項） | PSQ-004。`--kt-color-action-primary` × `--kt-color-action-primary-text` の対比 2.47:1 をAA準拠にするか、現行のEmerald維持判断を優先するか | `apps/web/src/styles/tokens.css` | **要decision**。全画面のPrimary CTAに波及するため単独の実装判断にしない |

### QA環境側のfollow-up候補（production codeとは無関係）

| # | Scope | 目的 |
|---|---|---|
| E-1 | production / preview環境へQAセッションからHTTP到達できるようにする（egress allowlistへ `*.vercel.app` と `jinja-backend.onrender.com` を追加） | 本監査で `BLOCKED_BY_ENVIRONMENT` となった項目（production上のPOST journey・auth済みjourney・実ブラウザ計測）を次回以降 `VERIFIED_PRODUCTION` に格上げする |

---

## Phase 28 — Final Verification

Audit文書作成後に再実行した結果。

| Check | Result |
|---|---|
| full web tests（`pnpm -C apps/web test`） | 164 files / 1289 tests passed |
| typecheck | 0 errors |
| lint | 0 errors |
| build | 成功 |
| contract tests（`pnpm test:contract`） | 164 files / 1289 tests passed |
| OpenAPI lint | error 0件 |
| `git diff --check` | 問題なし |
| production code diff | **0件**（`git diff origin/develop --stat` が `docs/audit/production-smoke-readiness.md` のみ） |

QA中に使用した一時ファイル（stub backend / Playwright harness / screenshots / logs / results.json）はすべてrepo外のscratchpadに置いており、repoへcommitしていない。

---

## Not Changed

Production code / UI redesign / Copy / Recommendation / Ranking / Scoring / Evidence contract / Backend / API schema / Serializer / DB / Migration / `apps/mobile` / Design Token / Dark theme / Analytics / Premium / Billing / Map provider / Performance。

STOP: 本監査はPR作成をもって終了する。Release作業・Production deployへは自動で進まない。
