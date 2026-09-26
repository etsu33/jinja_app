# Shrine Detail Transition Flash Audit

## Status

- Status: `AUDIT_ONLY`
- Recorded at: `2026-09-26`
- Base: `origin/develop` @ `2387f680fb3ef5963a4e3afe0163df894ddac251`
- Branch: `audit/shrine-detail-transition-flash`
- Production code change: `NONE`
- Test code change: `NONE`
- Observed on: real iPhone（Concierge Recommendation → `/shrines/[id]` 遷移中に、共有背景 / Footer が Shrine Detail 本文より先に見える）

この文書は、Concierge 推薦から Shrine Detail への遷移時に見える「空の中間状態」の原因を、base SHA の現行コードと production build の実測から切り分ける。修正は行わない。

---

## 1. Base SHA

```text
2387f680fb3ef5963a4e3afe0163df894ddac251  fix(reason): prevent duplicate hedge in tradition history copy (#2993)
```

前提確認:

- `develop` を `origin/develop` へ fast-forward、working tree clean を確認後に分岐
- 同名 remote branch なし、同目的の PR なし（`transition flash` で PR 検索 0 件）
- 過去の audit 結論には依存せず、上記 SHA のコードを読み直した

---

## 2. Reproduction status

| 観点 | 結果 | 環境 |
| --- | --- | --- |
| iPhone で観測された「背景 + Footer のみ」の描画 | **not reproduced** | Chromium (Playwright, iPhone 13 emulation) |
| 同上（WebKit / iOS Safari） | **environment-limited** | WebKit 実行環境なし（`/opt/pw-browsers` は Chromium のみ）。実機なし |
| Shrine Detail 本文が server fetch の直列待ちで遅延すること | **reproduced** | `next build` + `next start` + mock backend |
| 遷移待ち中に UI 上の pending 表示が一切ないこと | **reproduced** | 同上 |
| RSC stream が layout + Footer を本文より先に client へ届けること | **reproduced** | 同上（flight stream の chunk 時刻を計測） |

「Chromium で再現しない」は「存在しない」を意味しない。iPhone 実機での観測は事実として扱う。

### 2.1 再現手順（アプリコード無変更）

1. `pnpm install --frozen-lockfile --filter ./apps/web...`
2. `apps/web` で `next build`（Next.js 16.3.4 / Turbopack、exit 0）
3. repo 外（scratchpad）に Node 製の mock backend を置き、`127.0.0.1:8000` で Django API を模擬。全 GET に固定遅延 `MOCK_DELAY_MS`（400ms / 1500ms）を付け、各 request の START / END 時刻を記録
4. `DJANGO_ORIGIN=http://127.0.0.1:8000 DJANGO_API_BASE_URL=http://127.0.0.1:8000 next start`
5. Playwright（Chromium, `devices["iPhone 13"]`）で `/concierge` → 相談入力 → 「この相談で神社を提案してもらう」→ 推薦 Hero の「神社の詳細を見る」を実クリック
6. クリック直前に in-page の `requestAnimationFrame` sampler を仕込み、毎フレームの DOM 状態（pathname / Concierge frame の有無 / Detail h1 / 経路 CTA の有無 / scrollY / Footer 位置）を記録。250ms 間隔で screenshot
7. stress 条件: backend 1500ms/call + CPU 6x throttle + network（latency 400ms, 50KB/s）

mock backend / probe script は repo に含めない（audit 用の一時ファイル）。

### 2.2 実測結果（Chromium）

| 条件 | クリック → 本文表示 | 中間フレーム |
| --- | --- | --- |
| 400ms/call | 約 2.56s | なし。Concierge 画面がそのまま保持され、その後 Detail 全体が一度に commit |
| 1500ms/call + CPU 6x + slow network | 約 10.46s | なし。同上（約 10 秒間、旧画面のまま無反応に見える） |

rAF sampler の出力（1500ms 条件、状態が変化したフレームのみ）:

```text
t=4      path=/concierge  concierge=true  detail=false
t=10457  path=/shrines/1  concierge=false detail=true  h1="監査神社1" scrollY=0
```

注: `t=280` 付近の `scrollY 819→301` は Playwright の click が要素を viewport へ scroll した操作由来で、アプリの挙動ではない。

---

## 3. Production navigation chain

### 3.1 Concierge → Shrine Detail の全経路

| # | Source | Destination | Primitive | prefetch |
| --- | --- | --- | --- | --- |
| N1 | `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx:212-218`（「神社の詳細を見る」）。呼び出し: `ConciergeSectionsRenderer.tsx:967-972` | `/shrines/{id}?ctx=concierge&tid={tid}`（+ `direction_matched` / `direction_position`） | `next/link` `<Link>` | 未指定（default = auto） |
| N2 | `apps/web/src/components/shrines/ShrineCardCompact.tsx:179-185`（layout `compact`、「詳細だけ見る」）。呼び出し: `ConciergeSectionsRenderer.tsx:1219-1221` | 同上 | `next/link` `<Link>` | 未指定（auto） |
| N3 | `apps/web/src/components/ConciergeCard.tsx:163-165` via `components/shrine/PlaceShrineCard.tsx`。呼び出し: `ConciergeSectionsRenderer.tsx:1280` | `/shrines/resolve?place_id=...&ctx=concierge` → server `redirect()` で `/shrines/{id}`（`app/shrines/resolve/page.tsx:48`） | `next/link` `<Link>` + server redirect | `prefetch={false}` |

URL 生成:

- `features/concierge/detailHref.ts:43-74` `detailHrefFromRecommendation()` → `buildShrineHref()`（resolved）/ `buildShrineResolveHref()`（place_id のみ）
- `lib/analytics/directionRouteContext.ts:9-21` `withDirectionRouteContext()` が query を追記（path は不変）

`router.push` / `router.replace` / `location.href` / 素の `<a>` による Shrine Detail 遷移は Concierge 側に存在しない（`ConciergeClientFull.tsx` の `navPush` / `navReplace` は `/auth/*`, `/`, `/concierge`, `/map` のみ）。

### 3.2 他の推薦面

- Compass: `features/compass/components/CompassRecommendationsSection.tsx:140-153` → `ShrineCardCompact` layout `candidate`（`ShrineCardCompact.tsx:105`）→ `<Link>`（prefetch auto）、`ctx=compass`
- 非本番: `app/debug/concierge-fixture/page.tsx` → `ConciergeShrineCard` → `ConciergeCard`（`prefetch={false}`）

N1 / N2 / Compass は同一 primitive（`<Link>`, prefetch auto）。N3 のみ `prefetch={false}` + resolve redirect。

### 3.3 Runtime で確認した経路

実測では N1（Hero）のみ描画された（mock データでは Compact / Place card が出なかった）。N2 / N3 は静的解析のみ。

---

## 4. Shrine Detail ownership chain

```text
app/layout.tsx  (RootLayout, Server)
  <body class="min-h-dvh flex flex-col">
    <AuthProvider> (Client)
      <ClientBootstrap/>
      <header sticky>… <Suspense fallback={null}><HeaderAuthButtons/></Suspense></header>
      <main class="flex-1 min-h-0 overflow-y-auto">       ← app/layout.tsx:72
        {children}
        <LegalFooter/>                                    ← app/layout.tsx:74（children の直後）
      </main>
      <ClientToaster/>
  └─ app/shrines/layout.tsx:6  ShrinesWorldviewLayout (Server)
       <WorldviewFrame variant="standard">                ← components/worldview/WorldviewFrame.tsx:47-56
         <WorldviewBackdrop/>  + <div class="relative z-10">{children}</div>
     └─ app/shrines/[id]/page.tsx:213  Page (async Server Component)
          ├─ <ScrollToTopOnMount/>        (Client, useEffect で window.scrollTo(0,0))
          ├─ <ShrineDetailViewTracker/>   (Client, return null)
          ├─ <ShrineDetailToast/>         (Client, return null)
          └─ <ShrineDetailShell>          (Server) components/shrine/ShrineDetailShell.tsx
               └─ <ShrineDetailArticle>   (Client) components/shrine/detail/ShrineDetailArticle.tsx
                    └─ saveActionNode = <ShrineSaveButton/> (Client)
```

補足:

- `app/shrines/[id]/` に `layout.tsx` / `loading.tsx` / `error.tsx` / `template.tsx` はない
- 適用される `error.tsx` は `app/error.tsx`（root）のみ
- `generateMetadata`（`page.tsx:190-211`）が同じ `getShrineDetailServer()` を呼ぶ
- 本文の client component（`ShrineDetailArticle` 等）に `mounted` flag / `return null` による初回描画の gating はない（`return null` は section 単位の空データ時のみ）
- entrance animation（`animate-*` / `opacity-0` / view transition）は Shrine Detail / Worldview に存在しない

---

## 5. Prefetch findings

| 項目 | 結果 | 種別 |
| --- | --- | --- |
| N1 / N2 は `next/link` | はい | FACT |
| `prefetch` 明示 | N1 / N2: なし（auto）。N3: `false` | FACT |
| auto prefetch が発火するか | はい。推薦描画後、viewport 内 Link に対し `RSC: 1` + `Next-Router-Prefetch: 1` の request が 3 本発生 | FACT（runtime） |
| prefetch 応答の中身 | 412 bytes。`data-worldview-frame` も本文も含まない（route tree 情報のみ）。backend 呼び出しは発生しない | FACT（runtime） |
| prefetch が待ち時間を短縮するか | しない。dynamic route かつ `loading.tsx` がないため、prefetch で先取りできる UI が存在しない | FACT（runtime: クリック後に no-prefetch の RSC request が改めて発行され、本文はその完了を待つ） |
| 条件付き描画で prefetch が阻害されるか | Hero は推薦 payload 到着後にのみ描画されるが、描画後に prefetch は発火しており阻害は観測されない | FACT |
| prefetch 完了前にクリックされうるか | 可能（推薦表示直後のタップ）。ただし prefetch 応答に有用な UI が含まれないため、完了の有無は体感に影響しない | INFERENCE |

結論: PREFETCH は主因ではない。`loading.tsx` を追加すると auto prefetch が loading boundary までを先取りする対象になり、効果が変わる（§11 R1）。

---

## 6. Loading / Suspense findings

| # | 質問 | 回答 | 根拠 |
| --- | --- | --- | --- |
| 1 | `/shrines/[id]` に route-level `loading.tsx` はあるか | **ない** | `find apps/web/src/app -name loading.tsx` → `map/`, `mypage/` のみ |
| 2 | 適用される親 `loading.tsx` はあるか | **ない**（`app/shrines/`, `app/` にもない） | 同上 |
| 3 | Shrine Detail は Suspense で囲まれているか | **いいえ**。Next の `LoadingBoundary` は loading がない場合 Suspense を生成しない（`next/dist/client/components/layout-router.js:475-493`）。root layout の Suspense は `HeaderAuthButtons` のみ | FACT |
| 4 | fallback は何か | なし。soft navigation は transition として扱われ、旧画面（Concierge）が保持される | FACT（Chromium runtime） |
| 5 | 共有 layout が本文より先に render されうるか | **client へのデータ到着としては、はい**。RSC flight stream は約 85ms で `WorldviewFrame`（shrines layout）と `LegalFooter` を含む chunk を返し、本文 chunk は server 側 waterfall 完了後（1500ms 条件で約 9.1s）に届く。Chromium はこの部分木を paint せず旧画面を保持した | FACT（stream 計測）/ paint の有無は browser 依存（UNKNOWN） |
| 6 | 本文未解決中に Footer が見えうるか | 構造上、Footer は root layout の `{children}` 直後にあり（`app/layout.tsx:73-74`）、children が空または短ければ viewport 内に来る。Chromium では該当フレームは観測されない | FACT（構造）/ INFERENCE（iPhone での可視化経路） |
| 7 | 明示的な `return null` / 空 fragment / 同等の一時状態 | Page 本体にはない。`ShrineDetailToast` / `ShrineDetailViewTracker` / `ScrollToTopOnMount` は常に `return null` だが Shell / Article と並列で、本文を隠さない | FACT |

hard navigation（document 読み込み）の場合: HTML の最初の byte は server waterfall 完了まで返らず（1500ms 条件で TTFB 約 9.15s）、layout / Footer / 本文は同じ時刻の chunk で届く。document 経路で「layout だけ先に届く」HTML 流しはない（FACT）。

---

## 7. Fetch graph

`app/shrines/[id]/page.tsx` の本文表示前に完了が必要な fetch。すべて server-side、すべて `cache: "no-store"`、すべて **blocking**、Page 内で **直列**。

| 順 | 行 | 関数（file） | 経路 | 条件 | 認証 / cookie |
| --- | --- | --- | --- | --- | --- |
| M | `page.tsx:201` | `getShrineDetailServer`（`lib/api/shrines.server.ts:24`）in `generateMetadata` | Django 直（env 設定時） | ID 有効時 | なし |
| 1 | `page.tsx:255` | `getShrineDetailServer` | Django 直 | 常時 | なし |
| 2 | `page.tsx:287` | `fetchShrineMeaningPayloadV2Server`（`lib/api/shrineMeaning.server.ts:18`） | Next BFF `/api/shrines/{id}/meaning/` → Django | shrine 取得成功時 | cookie 転送。BFF は access 期限切れ時に refresh を先行実行しうる（`lib/server/bffFetch.ts:140-143`） |
| 3 | `page.tsx:312` | `getBillingStatusServer`（`lib/api/billing.server.ts:14`） | Next BFF `/api/billings/status/` → Django | 常時 | cookie 転送 |
| 4 | `page.tsx:316` | `getShrineFavoriteInitialState`（`lib/server/favorites.server.ts:35`） | Next BFF `/api/favorites/` → Django | `access_token` / `refresh_token` cookie または Authorization がある時のみ | cookie / Authorization 転送 |
| 5 | `page.tsx:320` | `fetchPublicGoshuinsForShrineServer`（`lib/api/publicGoshuins.server.ts:5`） | Next BFF `/api/public/goshuins` → Django | 常時 | なし |
| 6 | `page.tsx:363` | `getConciergeThreadServer(tid)`（`lib/api/concierge.server.ts:5`） | Next BFF → Django | `ctx=concierge && tid` | cookie 転送 |
| 7 | `page.tsx:376` | `getConciergeThreadsServer()`（`concierge.server.ts:30`） | Next BFF → Django | 6 の thread が取得できた時 | cookie 転送 |
| 8 | `page.tsx:383` | `getConciergeThreadServer(previousThreadId)` | Next BFF → Django | 前回 thread が存在する時 | cookie 転送 |

### 7.1 実測（mock backend 400ms/call、guest、前回 thread なし）

```text
[ 5125ms] START GET /api/shrines/1/data/
[ 5528ms] END   GET /api/shrines/1/data/ 200
[ 5568ms] START GET /api/shrines/1/meaning/
[ 5970ms] END   GET /api/shrines/1/meaning/ 404
[ 5985ms] START GET /api/billings/status/
[ 6387ms] END   GET /api/billings/status/ 200
[ 6398ms] START GET /api/goshuins/?is_public=true&shrine=1
[ 6799ms] END   GET /api/goshuins/?is_public=true&shrine=1 200
[ 6812ms] START GET /api/concierge-threads/10/
[ 7213ms] END   GET /api/concierge-threads/10/ 200
[ 7225ms] START GET /api/concierge-threads/
[ 7626ms] END   GET /api/concierge-threads/ 200
```

- 完全な直列 waterfall（重なりゼロ）。Concierge 経由 guest で 6 段、ログイン + 前回 thread ありで最大 8 段（FACT: コード / 6 段は runtime）
- 本文の到着時刻 ≒ 各段の backend 応答時間の総和（FACT）

### 7.2 依存関係と重複

| 観点 | 結果 | 種別 |
| --- | --- | --- |
| 2〜5 は 1（shrine）以外に相互依存なし | はい（入力は `numericId` と cookie のみ） | FACT（コード） |
| 6 は 1〜5 に依存しない | はい（`tid` のみ）。ただし現行コードは shrine 取得後にしか到達しない | FACT |
| 7 は 6 の結果に依存しない（引数なし）。8 は 7 に依存 | はい | FACT |
| `generateMetadata` と Page の shrine 取得が二重に backend を叩くか | 叩かない。mock log 上 `/api/shrines/1/data/` は 1 回のみ（同一 request 内の fetch memoization） | FACT（runtime） |
| 同一 resource の重複取得 | server 内ではなし。ただし current thread は Concierge client が既に取得済み（`app/concierge/ConciergeClientFull.tsx:792`）で、Detail server が再取得する | FACT（コード） |
| 認証解決が初回描画を block するか | する。cookie を読む fetch（2, 3, 4, 6, 7, 8）がすべて本文より前にある。token refresh が走る場合は段数がさらに増える | FACT（構造）/ refresh 回数は INFERENCE |
| BFF 二重 hop | 2, 3, 4, 5, 6, 7, 8 は Next server → 同一 Next の `/api/*` → Django の 2 hop | FACT（コード） |

---

## 8. Intermediate render state

### 8.1 Chromium（実測）

| 時間帯 | 画面 | DOM |
| --- | --- | --- |
| クリック〜本文到着（2.5s / 10.5s） | Concierge 画面がそのまま（CTA に pending 表示なし） | `[data-app-frame="concierge"]` あり、pathname `/concierge` |
| 本文到着時 | Shrine Detail 全体（Shell, Hero, 経路 CTA）が一度に表示、`scrollY=0` | pathname `/shrines/1`、Detail h1 あり |

中間状態の分類: **E（旧画面保持 + pending feedback なし）**。A〜D に該当するフレームは Chromium では観測されない。

### 8.2 iPhone（観測報告、未再現）

報告された状態は「共有背景 / Footer が本文より先に見える」＝ **C（layout-only render）** に相当する見た目。

- その部分木（`WorldviewFrame` + backdrop + `LegalFooter`、本文なし）のデータは、server waterfall の全期間 client に到着済みである（FACT、§6 #5）
- iOS Safari（WebKit）がそれを paint する経路があるかは本環境では検証できない（UNKNOWN）
- 可能性として、旧 Concierge 画面側の状態変化が同様の見た目になった可能性も排除できない（UNKNOWN）

---

## 9. Root-cause classification

| 分類 | 判定 | 内容 |
| --- | --- | --- |
| **SERVER_FETCH** | 主因（FACT） | 本文は 6〜8 本の blocking server fetch がすべて完了するまで client に届かない |
| **FETCH_WATERFALL** | 主因（FACT） | それらが完全に直列。独立な fetch も順番待ちになる |
| **LOADING_BOUNDARY** | 主因（FACT: 不在）/ flash への寄与は INFERENCE | `loading.tsx` / Suspense がないため、待ち時間中に構造のある中間 UI がなく、pending feedback もない。flight stream 上は layout + Footer だけが先行する |
| LAYOUT_COMPOSITION | 寄与（FACT: 構造） | Footer が root layout の `{children}` 直後にあるため、本文が空の部分木では Footer が上部に来る |
| PREFETCH | 主因ではない（FACT） | auto prefetch は発火するが route tree のみ（412 bytes）で、先取りできる UI がない |
| ROUTING | 主因ではない（FACT） | 通常の `<Link>` soft navigation。push / replace / location の混在なし |
| SUSPENSE | 該当なし（FACT） | 本文を囲む Suspense は存在しない |
| CLIENT_FETCH | 該当なし（FACT） | 本文表示に必要な client fetch はない |
| HYDRATION | 証拠なし | client component に初回描画 gating なし |
| OTHER | UNKNOWN | WebKit 固有の commit / paint 挙動（未検証） |

---

## 10. Facts / Inferences / Unknowns

### FACT

1. `/shrines/[id]` とその親に `loading.tsx` はなく、本文を囲む Suspense もない
2. Page は最大 8 本の server fetch を直列に await し、本文はその完了まで client に届かない（400ms/call で 6 段 ≒ 2.6s を実測）
3. soft navigation の RSC stream は shrines layout（WorldviewFrame）と Footer を約 85ms で、本文を waterfall 完了後に届ける
4. Chromium（iPhone 13 emulation、throttling 含む）では旧 Concierge 画面が保持され、layout-only フレームは描画されない
5. 待ち時間中、クリックした CTA にも画面にも pending 表示がない
6. hard navigation では HTML の TTFB 自体が waterfall 分遅れ、layout と本文は同時に届く
7. auto prefetch は発火するが UI を含まない
8. metadata と Page の shrine 取得は 1 回の backend call に集約される
9. 本番の backend 応答時間が長いほど、1〜5 の状態が続く時間は段数分だけ伸びる

### INFERENCE

1. iPhone で見えた「背景 + Footer のみ」は、FACT 3 の部分木（layout + Footer、本文なし）が WebKit 上で paint されたものである可能性が高い。部分木の中身と報告された見た目が一致するため
2. 本番環境（Render 上の backend、BFF 2 hop、token refresh）では 1 段あたりの遅延が mock より大きく、中間状態が視認できる長さになりやすい
3. `loading.tsx` による構造化 skeleton があれば、どの browser でも中間状態は「layout-only」ではなく「Shrine Detail の骨格」になる

### UNKNOWN

1. iOS Safari が Next.js 16.3.4 / React 19.3 の transition 中に未解決部分木を paint する条件（WebKit 実行環境なし）
2. 本番での各 fetch の実際の所要時間分布
3. 実機観測時の条件（ログイン状態、前回 thread の有無、cold start の有無、タップ時の hydration 完了有無）
4. iPhone で見えた画面が旧 Concierge 画面側の変化だった可能性

---

## 11. Minimal remediation options

いずれも未実装。

### R1. Route-level `loading.tsx`（Shrine Detail skeleton）

- Files: `apps/web/src/app/shrines/[id]/loading.tsx`（新規）。必要なら skeleton component 1 つ（`components/shrine/ShrineDetailSkeleton.tsx`）
- UX effect: クリック直後に Shrine Detail の骨格（閉じる / タイトル枠 / 経路 CTA 枠 / 本文枠）が表示される。layout-only 状態と「無反応に見える待ち」の両方を置き換える。auto prefetch が loading boundary までを先取りするため、skeleton は即時表示になる
- Blast radius: `/shrines/[id]` と、その配下の `/shrines/[id]/goshuins`（同じ loading boundary に入る）
- Implementation risk: 低〜中。高速応答時の skeleton の一瞬の表示、`ScrollToTopOnMount` / Next scroll handling との相互作用、skeleton の高さと本文の高さの差による layout shift
- Tests: loading component の render test（主要な骨格要素、`aria-busy`、Footer が骨格より上に来ないこと）。既存の detail / goshuins page test が通ること
- Visual QA: iPhone 実機 Safari（Concierge Hero / Compact / Compass から）、slow 3G 相当、Worldview 背景との連続性、skeleton → 本文の差し替えで大きな jump がないこと

### R2. Server fetch の並列化（blocking 時間の短縮）

- Files: `apps/web/src/app/shrines/[id]/page.tsx` のみ
- UX effect: 本文到着までの時間が「段数 × RTT」から概ね「2〜3 段分」へ短縮（shrine → {meaning, billing, favorites, goshuins, thread, threads} を並列、previous thread のみ後段）
- Blast radius: Shrine Detail の data 取得順序のみ。各 fetch の入出力・error handling（個別の try/catch と fallback）は維持する
- Implementation risk: 中。現行は shrine 取得失敗時に後続 fetch を行わない。並列化で失敗時にも他 fetch が走る場合の扱い、`GET_CONCIERGE_THREAD_FAILED` の catch 範囲（thread / threads / previous を一括 catch している）を変えないこと
- Tests: 各 fetch の失敗時 fallback が従来と同じであることの unit test、shrine 不在時の not-found shell、`ctx=concierge && tid` の有無による分岐
- Visual QA: Detail の表示内容が変わらないこと（Premium / Free、ログイン / guest、前回 thread あり / なし）

### R3. CTA の pending feedback

- Files: `features/concierge/components/ConciergeTopRecommendationHero.tsx`, `components/shrines/ShrineCardCompact.tsx`（`next/link` の `useLinkStatus` 等）
- UX effect: 旧画面保持中に「遷移中」であることが伝わる。layout-only 状態そのものは解消しない
- Blast radius: 推薦カード 2 component（Compass の candidate も共有）
- Implementation risk: 低
- Tests: pending 状態の表示 test
- Visual QA: CTA の見た目・押下感、Compass 側への影響

### R4.（後段）非必須 section の streaming

- `publicGoshuins` / `stateDelta`（前回 thread）を Suspense 配下の子 Server Component へ移す
- 効果は大きいが、`buildShrineDetailModel` の入力構造に触れるため最小修正ではない。R1 + R2 後に必要性を再評価する

---

## 12. Recommended implementation PR split

| 順 | PR | 内容 | 理由 |
| --- | --- | --- | --- |
| 1 | R1 | `app/shrines/[id]/loading.tsx` + skeleton | iPhone で見えた状態（layout-only）を、browser 依存なく構造のある中間 UI に置き換える唯一の案。business logic に触れない |
| 2 | R2 | `page.tsx` の fetch 並列化 | 中間状態の持続時間そのものを短くする。R1 と独立に review できる |
| 3（任意） | R3 | CTA pending feedback | R1 後も必要かを実機で判断 |

R1 着手前に、可能であれば iPhone 実機 Safari + Web Inspector で中間フレームの DOM を 1 回記録し、INFERENCE 1 を FACT に上げることを推奨する（修正方針は変わらないが、R1 の効果検証の基準になる）。

---

## 13. Proposed branch names

| PR | Branch |
| --- | --- |
| R1 | `feat/shrine-detail-route-loading-skeleton` |
| R2 | `perf/shrine-detail-parallel-server-fetch` |
| R3 | `feat/recommendation-cta-pending-feedback` |

---

## 14. Required tests

- R1: loading component render test（骨格要素・`aria-busy`・Worldview 内に収まること）、`/shrines/[id]` と `/shrines/[id]/goshuins` の既存 test
- R2: fetch ごとの失敗 fallback 維持、shrine not-found 分岐、`ctx` / `tid` 分岐、並列化後も metadata と Page の shrine 取得が 1 回であること
- R3: pending 表示の有無
- 共通: `pnpm -C apps/web lint`, typecheck, vitest。可能なら production build で Concierge → Detail の Playwright 遷移確認（本 audit の mock backend 手順を再利用）

## 15. Required visual QA

- iPhone 実機 Safari: Concierge Hero / Compact / Place card（resolve 経由）/ Compass candidate の各入口から Detail へ
- 遅延条件: 通常回線、低速回線、backend cold start 相当
- 状態: guest / ログイン、Free / Premium、前回 thread あり / なし
- 確認点: 背景 + Footer だけの状態が出ないこと、skeleton → 本文で大きな layout jump がないこと、遷移後の scroll 位置が先頭であること、戻る操作で Concierge が復元されること

## 16. Scope guard confirmation

本 audit で変更したファイルは本書のみ。

- production code: 変更なし
- test code: 変更なし
- recommendation / ranking logic、Evidence Boundary、Compass、Shrine Detail business logic、API contract、backend、database、analytics、authentication、global design token、無関係 UI: 変更なし
- 再現用の mock backend / probe script / build 成果物は repo 外または ignore 対象で、commit に含めない
