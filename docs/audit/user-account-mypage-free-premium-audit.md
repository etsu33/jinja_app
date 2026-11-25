# User Account / My Page / Free-Premium Integration Audit

> **Status: Audit / Historical（2026-09-04時点のruntime code読解）**
>
> 本書はaudit専用。実装変更・schema変更・Free/Premium境界変更・認証挙動変更・Compass/Conciergeロジック変更のいずれも行っていない。
> 結論はすべてruntime codeを正とし、ファイル名・docs・コメントの記述はruntime codeと矛盾する場合は採用していない。

## 0. 監査手法と限界

- 対象commit: `claude/user-account-audit-3fuyxt`（`develop`相当）
- 手法: 静的読解（ROOT_URLCONFからの到達可能性追跡、BFF route → Django view → service層のトレース）
- **テストは実行していない**（`node_modules`未インストール、Django未インストールのため）。本書で「test」として挙げたものは、テストファイルが当該挙動をassertしていることをコード上で確認したものであり、pass/failの実測ではない。
- 判定語彙:
  - `CONFIRMED` — runtime codeで経路が閉じている
  - `NOT FOUND` — 探索したが実装が存在しない
  - `UNRESOLVED` — 証拠が不足または矛盾しており、コードだけでは決められない

### 0-1. 最重要の前提: 到達可能なURLConf

`backend/shrine_project/settings.py:299` → `ROOT_URLCONF = "shrine_project.urls"`。

- `backend/config/urls.py` は**どこからも参照されていない死んだURLConf**（`grep -rn "config.urls"` のヒットは当該ファイル自身とテストのコメントのみ）。
- したがって `backend/users/urls.py` に定義された `MeView` / `CurrentUserView` / `MeIconUploadView`（`backend/users/views.py`）は**HTTP経由で到達不能**。
- 実際に稼働している `/api/users/me/` は `backend/users/api/views.py::MeView`（`backend/shrine_project/urls.py:82` の明示path、および `users.api.urls` 経由の二重登録）。
- 証拠: `backend/users/tests/test_views_no_sensitive_logging.py:1-6` が同じ事実をコメントで明記し、URL routingをbypassしてviewを直接呼んでいる。
- status: **CONFIRMED**

この分岐を取り違えると誤読する。`backend/users/serializers.py::UserProfileSerializer` は `("nickname", "is_public", "bio")` しか持たず生年月日を扱わないが、これは**死んだ経路側**のserializerである。生きているのは `backend/users/api/serializers.py::UserProfileUpdateSerializer`（birthday/birth_time/birth_place/worship_styleを持つ）。

---

## 1. 現行アクセスマトリクス

| Feature | Anonymous | Free Registered | Premium | Source of Truth |
| --- | --- | --- | --- | --- |
| Compass（方位提案） | 利用可 | 利用可（挙動は匿名と同一） | 利用可（挙動は匿名と同一） | `backend/temples/api_views_compass.py:45` `permission_classes = [AllowAny]`。frontend `features/compass/CompassClient.tsx` にauth/billing参照は0件 |
| Concierge chat（相談） | 利用可（3回/上限） | 利用可（3回/上限） | 無制限 | `backend/temples/services/quota_policy.py:8-26` + `backend/temples/api_views_concierge.py:654,1013` |
| Concierge スレッド自動保存 | **保存される**（anon_id紐付） | 保存される（user紐付） | 同左 | `backend/temples/api_views_concierge.py:918-947` `append_chat(user=…, anonymous_id=…)` |
| Concierge スレッド一覧 `/api/concierge-threads/` | 401 | 利用可 | 利用可 | `backend/temples/api/views/concierge.py:59` `IsAuthenticated` |
| Concierge スレッド詳細 `/api/concierge-threads/<id>/` | 利用可（anon cookie一致時のみ） | 利用可（自ユーザーのみ） | 同左 | `backend/temples/api/views/concierge.py:89` `AllowAny` + `:120-125` の所有者判定 |
| 神社詳細 / 検索 / Deep Dive / ランキング / 公開御朱印 | 利用可 | 利用可 | 利用可 | `temples/api/views/shrine.py:112,161,212` / `deep_dive.py:79` / `ranking.py:17` / `goshuin.py:28` すべて `AllowAny` |
| Shrine Meaning payload（premiumタグ付きblock含む） | **全block取得可** | 全block取得可 | 全block取得可 | `backend/temples/api/views/shrine_meaning.py:13` `AllowAny`、`compose_shrine_meaning_payload(shrine)` はuser/access引数を取らない |
| お気に入り（Favorite） | 401 | 利用可（**上限なし**） | 利用可 | `backend/temples/api_views.py:27` `IsAuthenticated`。`QUOTA_POLICY["free"]["favorite"]={"limit":10}` は**未使用** |
| 参拝記録 / Reflection / Interaction log | 401 | 利用可 | 利用可 | `temples/api/views/visit.py:13,60` / `reflection.py:11,48` / `shrine_interaction.py:18` |
| 神社投稿（Shrine Submission） | 401 | 利用可 | 利用可 | `backend/temples/api/views/shrine_submission.py:21` |
| 御朱印アップロード | 401 | 最大10件 | **最大10件（Premium差なし）** | `backend/temples/services/goshuin_limit.py` は `user` を無視して定数10を返す。UI側も `GOSHUIN_TAB_ENABLED = false`（`components/views/MyPageView.tsx:18`） |
| My Page `/mypage` | `/login` へリダイレクト | 利用可 | 利用可 | `apps/web/middleware.ts:8-16`（`access_token` cookieの有無のみ判定） |
| Billing checkout | 401 | 利用可 | 利用可 | `backend/temples/api/views/billing.py:94` `IsAuthenticated` |
| Billing status | 200（stub/free） | 200 | 200 | `backend/temples/api/views/billing.py:49` `AllowAny` |
| ストレージ使用量 `/api/users/me/storage/` | 401 | 利用可 | 利用可（**上限差なし**） | `backend/users/api/views.py:38-40`、上限は `settings.STORAGE_LIMIT_BYTES` 固定 |
| 深い意味カード（personal_meaning / action_meaning / shrine_meaning / history_shift / deep_reflection / previous_comparison） | teaser or hidden | teaser or hidden | visible | **frontendのみ**: `apps/web/src/lib/premium/cardVisibility.ts` |

### 1-1. Source of Truthの所在（`anonymous / free / premium`）

**backend側（authorizationの正本）**

- `backend/temples/services/plan_service.py::resolve_plan_context` — `anonymous | free | premium` の3値を決定する唯一のbackend関数。未認証は `anonymous`、認証済みは `is_premium_for_user()` の結果で `premium|free`。
- `backend/temples/services/billing_state.py::is_premium_for_user` — `is_staff` なら無条件でTrue、それ以外は `get_billing_status()` に委譲。
- `backend/temples/services/billing_state.py::get_billing_status` — **provider分岐が最上位**。`BILLING_PROVIDER=stub`（デフォルト）の場合、**認証済みユーザーでもDBを一切見ず環境変数 `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE` を正とする**（`:56-58`）。stripe/revenuecat運用時のみ `UserProfile.subscription_status` / `current_period_end` を読む。
- `backend/users/services/billing.py::is_subscription_active` — `current_period_end` があればstatusより期限を優先。
- **plan_contextが実際にauthorizationに効いているのはConcierge quotaのみ**（`api_views_concierge.py:654` の `check_quota` / `:1013` の `consume_quota`）。それ以外のendpointはplanを参照しない。
- status: **CONFIRMED**

**frontend側（表示制御の正本、backendとは別系統）**

- `apps/web/src/lib/premium/accessLevel.ts::resolveAccessLevel(billingStatus, isAuthenticated)` — `/api/billings/status` のレスポンスと `useAuth().isLoggedIn` から3値を再計算。
- `apps/web/src/lib/premium/cardVisibility.ts::CARD_VISIBILITY_POLICIES` — 23カードの `visible|teaser|partial|hidden` を3階層で定義。**この表に対応するbackend側の出し分けは存在しない**。
- status: **CONFIRMED**

### 1-2. Frontend-onlyのアクセス判定（backend authorizationと乖離するもの）

いずれも「UIは隠すがAPIは返す」型の乖離。

| # | 乖離 | 証拠 | status |
| --- | --- | --- | --- |
| A | Premiumコンテンツの出し分けが**完全にfrontend専任**。`/api/concierge/chat/` のresponse bodyはplanによって内容が変わらない（`_build_chat_response`、`api_views_concierge.py:321-374` — plan依存は `plan` / `remaining` / `limit` / `limitReached` の4フィールドのみ） | `api_views_concierge.py:321-374`、`lib/premium/cardVisibility.ts` | CONFIRMED |
| B | `ShrineMeaningView` は `AllowAny` かつ `compose_shrine_meaning_payload(shrine)` にuser引数がない。`access: "premium"` タグ付きblock（`action_meaning` / `after_visit_reflection` / `history_context` / `deity_symbol` / `benefit_action`）が**未認証でもbody込みで返る** | `temples/api/views/shrine_meaning.py:13-29`、`temples/services/shrine_meaning_composer.py:809-851` | CONFIRMED |
| B' | しかもfrontendはこの `access` フィールドを**一切読んでいない**（`grep` で `payloadV2.ts` の型定義以外に参照なし）。backendがaccess階層を宣言し、frontendは別テーブル（`cardVisibility.ts`）で判定している二重管理 | `lib/shrineMeaning/payloadV2.ts:89` のみ | CONFIRMED |
| C | `lib/auth/actionGuards.ts::isAuthRequiredForAction("save_concierge_thread") === true` だが、backendは匿名の相談も無条件でthreadに永続化する | `lib/auth/actionGuards.ts:16-21` vs `api_views_concierge.py:918-947` | CONFIRMED |
| D | `components/shrine/detail/ShrineDetailArticle.tsx:558-563` は `resolveAccessLevel(…, true)` と**isAuthenticatedをtrue固定**で呼ぶ。神社詳細では `anonymous` 階層が構造的に発生せず、未ログインでも `free` として扱われる（`anonymous` 行を持つポリシーが空振りする） | `ShrineDetailArticle.tsx:558-563` | CONFIRMED |
| E | 開発環境限定のfrontend override `NEXT_PUBLIC_FORCE_BILLING_PLAN=premium` がBFFでbackendを迂回してpremiumを返す（`NODE_ENV !== "production"` ガードあり） | `app/api/billings/status/route.ts:20-28` | CONFIRMED |
| F | `middleware.ts` は `/mypage` のみを `access_token` cookieの**存在**で判定。失効tokenでも通過し、その先はclient側の `useAuth` 依存 | `apps/web/middleware.ts:8-22` | CONFIRMED |
| G | `QUOTA_POLICY` の `favorite` / `goshuin_upload` / `shrine_search` は定義のみで**enforcement先がない**（`check_quota` の呼び出しはconciergeの1箇所のみ） | `quota_policy.py:8-26` vs `grep check_quota` | CONFIRMED |

---

## 2. My Page 責務マップ

`/mypage` の実体は `apps/web/src/app/mypage/page.tsx` → `apps/web/src/components/views/MyPageView.tsx`（tabs: profile / submissions / favorites / visits、+ 別route `/mypage/history`）。

| # | 責務 | 実装 | 経路 | 専用My Page必須か（技術的観点のみ） |
| --- | --- | --- | --- | --- |
| 1 | プロフィール編集（nickname / is_public / **birthday** / birth_time / birth_place / worship_style） | `MyPageView.tsx:373-430`（入力）、`:194-216`（保存） | `updateUser()` → `PATCH /api/users/me/` → `users/api/views.py::MeView.patch` → `UserProfileUpdateSerializer` | **不要**。frontendの単一フォーム。プロダクト上のprofile編集面は現状ここだけだが、`PATCH /api/users/me/` は呼び出し元を問わない |
| 2 | 派生プロフィール表示（九星 / 五行 / ライフパス / 吉方位） | `MyPageView.tsx:192-193, 386-402` | `lib/profile/derivedProfile.ts` のpure関数、**未保存のform stateから毎回再計算**（保存値でも保存前値でもなくform） | **不要**。純粋関数の表示のみ。永続化なし、他機能への受け渡しなし |
| 3 | 保存した神社（Favorites） | `features/mypage/components/FavoritesSection.tsx`、SSR初期値は `app/mypage/page.tsx:8` | `GET /api/favorites/`（`IsAuthenticated`） | **不要**。独立route `/favorites`（`app/favorites/page.tsx`）が**同じデータで既に存在する** |
| 4 | 参拝履歴 | `MyPageView.tsx:157-178, 302-352` | `GET /api/visits/` | 不要（独立routeにできる） |
| 5 | 投稿した神社 | `features/mypage/components/MyPageScreen.tsx`（`activeTab="submissions"`） | `getMyShrineSubmissions()` | 不要 |
| 6 | 相談履歴 | **My Page外の独立route** `/mypage/history`（`app/mypage/history/page.tsx`）。My Pageからはリンクのみ（`MyPageView.tsx:280-286`） | `GET /api/concierge-threads/` | 既にMy Page本体から分離済み |
| 7 | 御朱印管理 | `MyPageScreen.tsx`（`activeTab="goshuin"`） | — | **UIから到達不能**。`GOSHUIN_TAB_ENABLED = false`（`MyPageView.tsx:18`）でtabが描画されず、`normalizeTab` も `"goshuin"` を返さない（`:34`）。ただし `?tab=goshuin` 直叩き時のフォールバック分岐は残存 |
| 8 | プロフィールアイコン変更 | `features/mypage/components/ProfileIconCard.tsx` | **どこからも参照されていない**（`grep` でimport 0件）。`lib/api/users.ts::uploadUserIcon` もテスト以外の呼び出し元なし | 実装のみ存在 |
| 9 | ログアウト | `MyPageScreen.tsx:24` の `logout`、`components/layout/HeaderAuthButtons.tsx` | `POST /api/auth/logout` | ヘッダにも存在（重複） |

**別実装のMy Page（完全な死にコード）**

- `accounts/` Djangoアプリ（`accounts/urls.py` に `mypage/`、`accounts/views.py::mypage`、`templates/accounts/mypage.html`）は **`INSTALLED_APPS` に入っておらず**（`backend/shrine_project/settings.py` の `INSTALLED_APPS` に `accounts` なし）、`accounts.urls` をincludeしている箇所も存在しない。
- status: **CONFIRMED（到達不能）**

**判定**: 「My Pageでしか技術的に成立しない責務」は**発見できなかった**。責務1〜9はいずれも独立routeまたは既存の別面（`/favorites`、`/mypage/history`、ヘッダ）に配置可能で、API側にMy Page固有の制約はない。ただし**プロフィール編集フォーム（責務1）は現状My Page以外に入口が存在しない**ため、「移設可能」と「今すぐ削除可能」は別問題である。存廃判断は本書の範囲外。

---

## 3. 生年月日（birthday）データフローマップ

### 3-1. 保存

```
MyPageView profile tab (input type="date", MyPageView.tsx:376)
  → form.birthday (client state)
  → handleSave() 差分のみ payload 化 (MyPageView.tsx:201: form.birthday !== initial.birthday → payload.birthday)
  → lib/api/users.ts::updateUser()  PATCH /api/users/me/  (credentials: same-origin)
  → BFF: apps/web/src/app/api/users/me/route.ts::PATCH
       → bffFetchWithAuthFromReq(req, "/api/users/me/", …)  ※ access_token cookie → Authorization: Bearer、401時 refresh再試行
  → Django: backend/users/api/views.py::MeView.patch  (JWTAuthentication + IsAuthenticated)
       → UserProfileUpdateSerializer  (backend/users/api/serializers.py:60-72)
            validate_birthday: 未来日を400で拒否 (:69-72)
       → users.models.UserProfile.birthday  (DateField, null=True)  ← 唯一の永続化先
```

- 登録（signup）では**生年月日を一切収集しない**: `apps/web/src/app/signup/SignupForm.tsx` は username / email / password のみ。`backend/users/api/serializers.py::SignupSerializer` も `("username","password","email")` のみ。
- 関連test: `backend/users/tests/test_users_me_api.py:66-95`（birth系4フィールドのPATCH永続化とGET復元、未来日/不正日の400）
- status: **CONFIRMED**

### 3-2. 取得

```
AuthProvider.fetchMe()  GET /api/users/me/  (lib/auth/AuthProvider.tsx:51-77)
  → BFF app/api/users/me/route.ts::GET → Django users/api/views.py::MeView.get
  → UserMeSerializer → profile: UserProfileSerializer
       fields: nickname, is_public, bio, icon, icon_url, birthday, birth_time, birth_place, worship_style, created_at
  → AuthUser.profile.birthday  (lib/auth/types.ts:14)
  → useAuth().user?.profile?.birthday
```

- `AuthProvider.shouldAutoFetchMe()`（`:79-101`）は `/`、`/shrines/*`、`/concierge`、`/login`系で**自動fetchをスキップ**する（`localStorage["auth:logged_in"] === "1"` の場合のみfetchする）。つまり `/concierge` ではログイン済みでも**初回訪問端末では `user` が `null` のまま**になりうる。→ 3-4のConcierge接続に影響。
- status: **CONFIRMED**

### 3-3. 消費先（feature logic）

| 消費先 | 生年月日の入手経路 | 判定 |
| --- | --- | --- |
| Concierge（ranking / direction計算） | **クライアントがrequest bodyに載せた値のみ**。backendは `UserProfile.birthday` をDBから読まない | **implemented and connected**（ただしclient経由） |
| Compass | request bodyの `birthdate`（Compass画面のフォーム入力のみ） | **implemented but disconnected**（保存プロフィールとは非接続） |
| My Page 派生プロフィール表示 | form state（未保存値を含む） | implemented and connected（表示のみ、他機能に流れない） |
| 公開プロフィール `/api/profiles/<username>/` | `UserProfile.birthday` をDBから読み、`is_public=True` なら**年齢付きで公開**（`app/users/[username]/page.tsx:44-60`） | **implemented but disconnected**（下記3-5参照） |
| `birth_time` / `birth_place` | 保存・GET復元・Conciergeへの送信（`profile_context.user_profile.birthTime/birthPlace`）まで到達するが、**backendに読み手が存在しない**（`grep -rn "birthTime\|birthPlace"` はbackendで0件） | **field exists only** |
| `worship_style` | `profile_context.user_profile.worshipStyle` → `_score_profile_signal`（`concierge_chat_ranking.py:356-368`）で最大 +0.01 | implemented and connected |

**backendがDBの `UserProfile.birthday` を読む箇所は0件**（`grep -rn "UserProfile\|\.birthday" backend/temples/` のヒットは `billing_checkout.py` / `billing_state.py` のsubscription用途のみ）。
status: **CONFIRMED**

### 3-4. 保存生年月日 → Concierge の接続（唯一の実接続経路）

```
useAuth().user.profile.birthday
  → app/concierge/ConciergeClientFull.tsx:1003  savedProfile: user?.profile
  → features/concierge/buildConciergeRequestPayload.ts:66
       birthdate = normalizeBirthdateInput(temporaryBirthdate ?? "")
                   ?? normalizeProfileBirthday(savedProfile?.birthday)
  → payload.birthdate / payload.filters.birthdate / payload.profile_context.user_profile.{birthday,birthdate}
  → POST /api/concierge/chat → backend/temples/api_views_concierge.py
       :551 canonical_input.birthdate            → element/astro scoring (_attach_breakdown)
       :564 resolve_profile_context_birthdate()  → direction計算（profile_contextが優先）
       :570-572 planned_visit_lucky_directions(profile_birthdate or birthdate, visit_date)
                / annual_lucky_directions(profile_birthdate or birthdate)
```

- **backendには生年月日の二重precedence chainが存在する**。`backend/temples/services/concierge_input_contract.py:299-317` のdocstringが「これはDocumented Current Gapであり統一していない」と明記。`profile_context` 側とcanonical側が食い違う場合、方位計算だけ `profile_context` が勝つ。
- status: **CONFIRMED**

### 3-5. 公開プロフィール経路の断線

- `backend/temples/api/views/public_profile.py:44` は `birthday` をレスポンスに含め、`app/users/[username]/page.tsx:44-60` が「YYYY-MM-DD（N歳）」として描画する。ゲートは `profile.is_public` のみで、`is_public` の既定値は `True`（`users/models.py:11`、`users/apps.py:23` の `ensure_profile` も `is_public: True`）。
- ただし frontend の `lib/api/publicProfile.ts:16` は `/api/public/profile/<username>/` を呼ぶ。**このpathはbackendにもBFFにも存在しない**（backendは `/api/profiles/<username>/`、`app/api/public/` 配下は `goshuins` と `shrines` のみ）。加えて `apiGet` は `baseURL: "/api"` の相対URLで、Server Component からの呼び出しでは解決できない。
- 結果として当該ページは現状 `notFound()` に落ちる想定だが、**backend endpoint 自体は生きており、直接叩けば公開プロフィールの生年月日は取得できる**。
- status: **CONFIRMED（frontend断線 / backend露出は生存）**

### 3-6. 断線している周辺実装

| 実装 | 状態 | 証拠 |
| --- | --- | --- |
| アイコンアップロード `POST /api/users/me/icon/` | **backend未ルーティング**。`users/api/urls.py` は `users/me/`, `users/me/storage/`, `users/signup/`, `stripe/webhook/` のみ。`MeIconUploadView` は死んだ `users/urls.py` にしかない | `backend/users/api/urls.py`、`backend/users/urls.py`、`apps/web/src/app/api/users/me/icon/route.ts` |
| `uploadUserIcon` / `ProfileIconCard` | 呼び出し元なし（テストのみ） | `lib/api/users.ts:24`、`features/mypage/components/ProfileIconCard.tsx` |
| `updateMe()`（`lib/api/users.ts:19`） | 呼び出し元なし。`MyPageView` は `updateUser()` を使う | `lib/api/users.ts` |
| `lib/auth/withAuth.tsx`（`withAuth` / `RequireAuth`） | **どこからも使われていない** | `grep -rn "withAuth\|RequireAuth"` のヒットは定義ファイルと無関係な `onRequireAuth` prop のみ |
| `app/api/me/route.ts` | 「互換API。新規参照禁止」と自称。呼び出し元なし | `app/api/me/route.ts:9-10` |
| `favorites` Djangoアプリ（`INSTALLED_APPS` にあり） | `favorites.urls` をincludeする箇所がなく、`temples.models.Favorite` と重複したモデルがmigrationごと残存 | `backend/favorites/`、`backend/shrine_project/urls.py` |

---

## 4. Compass 接続状況

### 4-1. 匿名利用の実際

- Route: `/compass` → `features/compass/CompassClient.tsx`（`"use client"`、Suspense fallbackのみのpage）。
- 入力3点はすべて**画面内で毎回収集**: purpose（chip、`:87`）、birthdate（`useState("")`、`:89`、`<input type="date">` `:249`）、origin（端末位置 or 住所検索、`:91`）。
- 送信: `POST /api/compass/recommendations`（`:170-179`）→ BFF `app/api/compass/recommendations/route.ts` → `bffFetchWithAuthFromReq`。cookieが無ければAuthorizationヘッダも付かない。
- backend: `CompassRecommendationsView`（`permission_classes = [AllowAny]`、`throttle_scope = "compass"`）。view docstringが「Free/Premium判定・quota・threadはこのViewの責務ではない（Phase 5時点でCompassはgatingなし）」と明記。
- quota消費なし（`check_quota` はconciergeのみ）。thread保存なし。
- status: **CONFIRMED**

### 4-2. ログインユーザー向けにプロフィール生年月日を使う接続は存在するか

- `features/compass/` 配下に `useAuth` / `useBilling` / `premium` / `isLoggedIn` の参照は**0件**（`grep` 実行済み）。
- `CompassClient` の `birthdate` state に初期値を注入する箇所は存在しない（`useState("")` 固定、`searchParams` から読むのは `ref` のみ）。
- `AuthProvider.shouldAutoFetchMe()` は `/compass` について `true`（既定の最終 `return true`）を返すため、**`/api/users/me/` 自体はCompass画面でも取得されている**。つまりデータは手元にあるが、Compassがそれを読んでいない。
- 結論: **技術的にはオプショナル接続が可能な状態にあり（`user.profile.birthday` はclientで参照可能、backendは `birthdate` をrequest bodyから受けるためログイン必須化は不要）、その接続は現在存在しない**。
- status: **NOT FOUND（接続が存在しないことをCONFIRMED）**

---

## 5. Concierge 接続状況

### 5-1. 生年月日の入手元

**both**（フォーム直接入力と保存プロフィールの両方）。

- 直接入力: `sessionState.temporaryBirthdate`（`ConciergeClientFull.tsx:946-947, 1002, 1306, 1640-1643`）。フィルタパネルの生年月日入力（`filter_set_birthdate` action）で設定される。
- 保存プロフィール: `user?.profile?.birthday`（`ConciergeClientFull.tsx:971, 1003`）。

### 5-2. precedence と fallback（実コード）

```ts
// features/concierge/buildConciergeRequestPayload.ts:66
const birthdate =
  normalizeBirthdateInput(temporaryBirthdate ?? "")            // ① セッション入力が最優先
  ?? normalizeProfileBirthday(savedProfile?.birthday);         // ② 保存プロフィールにfallback
const payloadBirthdate = input?.birthdate ?? birthdate;        // ③ 呼び出し側overrideが更に優先
```

同じ順序が `ConciergeClientFull.tsx:971-972` の `baseFilters` memoにも複製されている（二重実装だが順序は一致）。

- **正規化に失敗した入力は「無視」であり「エラー」ではない**。`normalizeBirthdateInput` が `null` を返せば黙って保存プロフィールにfallbackする。
- `birth_time` / `birth_place` / `worship_style` は**保存プロフィールからのみ**取得され、セッション入力の対応物が存在しない（`buildConciergeRequestPayload.ts:105-110`）。したがって未ログインユーザーは生年月日だけを供給できる。
- backend側では更に第2のprecedenceが走る（3-4参照）: 方位計算のみ `profile_context.user_profile.{birthdate,birthday}` が `canonical_input.birthdate` に優先。
- status: **CONFIRMED**

### 5-3. 関連test

- `apps/web/src/features/concierge/__tests__/buildConciergeRequestPayload.test.ts`
  - `:89-98` L3-A: 生年月日がtop-level / filters / profile_context の3箇所に載ること
  - `:135-168` Full Integration: `temporaryBirthdate` と `savedProfile.birthday` に**同じ値**を与えたケース
  - **「`temporaryBirthdate` が空で `savedProfile.birthday` のみ存在する」fallbackケース、および両者が食い違うケースを直接assertするテストは存在しない**（`savedProfile` は他の全ケースで `null`）。
  - status: **UNRESOLVED（コード上の順序はCONFIRMED、テストによる保護はNOT FOUND）**
- `backend/temples/tests/test_concierge_l3_contract.py:31-45` — `resolve_profile_context_birthdate` が `birthdate` / `birthday` の両フィールドを読むこと
- `backend/temples/tests/api/test_concierge_chat_l3_context_contract.py:150` — 二重precedence chainの存在を明記

### 5-4. Concierge の保存導線の不整合

`ConciergeClientFull.tsx:1538-1560` の `save_concierge_thread` ハンドラ:

- 未ログインなら `redirectToAuth("login")`
- ログイン済みなら **何もしない**（`// 現時点では server 保存API未接続。` `:1558-1560`）

一方backendは、匿名・ログイン問わず `/api/concierge/chat/` の**全リクエストでthreadを自動永続化**している（`api_views_concierge.py:918-947`）。「保存」ボタンは実際には保存を起動しておらず、匿名の相談も既にDBに残っている。
status: **CONFIRMED**

---

## 6. 責務の重複・矛盾

| # | 領域 | 内容 | 証拠 |
| --- | --- | --- | --- |
| R1 | 登録 ↔ My Page | 登録は username/email/password のみ。プロフィール（生年月日含む）の入力面は**My Pageにしかない**。両者を跨いだオンボーディング導線はコード上に存在しない | `SignupForm.tsx`、`MyPageView.tsx:373-430` |
| R2 | My Page ↔ Compass | 生年月日の入力面が2つあり、値が同期しない。My Pageで保存してもCompassは毎回再入力を要求する | `MyPageView.tsx:376` vs `CompassClient.tsx:89,249` |
| R3 | My Page ↔ Concierge | 生年月日の入力面が2つあり、precedenceは「セッション入力 > 保存値」。ユーザーには片方しか見えていないため、どちらが効いているかUIから判別できない | `buildConciergeRequestPayload.ts:66` |
| R4 | Compass ↔ Concierge | 生年月日から方位を計算するロジックが**3実装**存在する。① `apps/web/src/lib/profile/derivedProfile.ts::buildDirectionProfile`（My Page表示専用、`annual_kyusei_v1`）② `backend/temples/domain/kyusei.py::annual_lucky_directions` / `planned_visit_lucky_directions`（Concierge、`api_views_concierge.py:570-572`）③ `backend/temples/services/compass_runtime.py::build_compass_direction_runtime`（Compass、`annual_monthly_kyusei_v1` / `monthly_kyusei_v1`）。① と ②③ は算出方式が異なる | 各ファイル |
| R5 | Premium境界 | 階層宣言が**3箇所**にある。① backend `shrine_meaning_composer.py` の `access` タグ ② frontend `cardVisibility.ts` の23カード表 ③ backend `quota_policy.py` のfeature別上限。①はfrontendに読まれず、②に対応するbackend enforcementがなく、③はconcierge以外未使用 | 6章 表 A/B/B'/G |
| R6 | Premium境界 | Premium実効差分は **Concierge回数無制限のみ**。`favorite` 上限、`goshuin_upload` 上限、`shrine_search` の `db_only`/`extended` モードはpolicyに書かれているが実行経路がない。御朱印上限は `get_my_goshuin_limit(user)` が `user` を無視して10固定 | `quota_policy.py`、`goshuin_limit.py` |
| R7 | Premium境界 | `is_premium_for_user` は `is_staff` を無条件でpremium扱いする。運用アカウントの計測が混入しうる | `billing_state.py:130-144` |
| R8 | Premium境界 | `BILLING_PROVIDER=stub`（デフォルト）では、**認証済みユーザーでも `UserProfile.subscription_status` を読まず環境変数を正とする**。Stripe webhookが `UserProfile` を更新しても、providerがstubのままなら反映されない | `billing_state.py:52-58` |
| R9 | My Page ↔ 独立route | Favorites が `/mypage?tab=favorites` と `/favorites` の2箇所に存在し、同じ `getFavoritesServer()` を使う | `app/mypage/page.tsx`、`app/favorites/page.tsx` |
| R10 | 認証 | `/login` と `/auth/login`、`/signup` と `/auth/register` の二重route（前者は後者へredirect）。`middleware.ts` は `?next=` を、`MyPageView` の未ログイン表示は `?returnTo=` を使う（`buildLoginHref`）。redirect chainで吸収されている | `app/login/page.tsx`、`app/auth/login/page.tsx`、`middleware.ts:12`、`MyPageView.tsx:236-244` |
| R11 | 認証 | 到達不能な認証実装が3系統残存: `backend/config/urls.py`、`backend/users/urls.py` + `users/views.py`、`accounts/` アプリ（Djangoテンプレート版のログイン/登録/マイページ） | 0-1章、2章 |
| R12 | My Page ↔ 公開プロフィール | My Pageの `is_public` チェックボックスが、`/api/profiles/<username>/` 経由の**生年月日の公開**を制御している。UI上のラベルは「プロフィールを公開」のみで、生年月日が対象である旨の表示はない | `MyPageView.tsx:404-415`、`public_profile.py:44` |

---

## 7. Mother Ship 承認が必要な未解決のプロダクト判断

以下はいずれも**コードからは決定できない**。本書では判断せず、選択肢の存在のみを記す。

| # | 未解決事項 | コード上の現状 | 判断できない理由 |
| --- | --- | --- | --- |
| D1 | 保存プロフィールの生年月日をCompassに使うか（使う場合の必須/任意の別） | 非接続。Compassは毎回フォーム入力 | Compassの「匿名で完結する」設計意図（`api_views_compass.py` docstring）と、プロフィール活用のどちらを優先するかは製品判断 |
| D2 | Concierge の生年月日 precedence（セッション入力 > 保存値）を正とするか | この順序で実装済み。ただし食い違い時の挙動をassertするテストなし | 「その場の入力を優先」も「登録済みプロフィールを優先」もありうる |
| D3 | backendの二重precedence chain（方位計算のみ `profile_context` 優先）を統一するか | `concierge_input_contract.py:311-316` が「Documented Current Gap、統一は範囲外」と明記 | 統一すると既存の方位計算結果が変わる |
| D4 | Premium境界をbackendでenforceするか、frontend表示制御のままとするか | Premiumコンテンツは未認証でもAPIから全文取得可能（乖離A・B） | 「UI上の体験差」で足りるのか「APIレベルの保護」が要るのかはビジネス判断 |
| D5 | `access` タグ（backend）と `cardVisibility.ts`（frontend）のどちらをPremium階層の正本とするか | 二重管理、相互参照なし | — |
| D6 | `QUOTA_POLICY` の未使用エントリ（favorite / goshuin_upload / shrine_search）を実装するか削除するか | 定義のみ。favoriteは実質無制限、御朱印は全プラン10件固定 | Premiumの価値提案そのもの |
| D7 | `BILLING_PROVIDER` の本番既定値と、stub時に認証済みユーザーのDB状態を無視する挙動を許容するか | 既定 `stub` → env優先（R8） | 課金導入フェーズの意思決定 |
| D8 | `is_staff` を無条件premium扱いすることを許容するか | `billing_state.py:130-137` | 運用/計測ポリシー |
| D9 | My Page を専用面として維持するか（責務の再配置先） | 技術的必然性は発見できず（2章）。ただしプロフィール編集の唯一の入口 | 存廃・再配置は製品判断。本書は evidence のみ |
| D10 | 御朱印機能の扱い（`GOSHUIN_TAB_ENABLED = false` で凍結中） | UI到達不能、backendは生存、アイコンアップロードはbackend未ルーティング | 凍結解除・削除・現状維持のいずれか |
| D11 | 公開プロフィールで生年月日（＋年齢）を公開してよいか。`is_public` 既定値 `True` を維持するか | backendは公開する。frontendはpath不一致で断線中（3-5） | 個人情報の公開範囲。断線の修正は公開の是非を決めてから |
| D12 | 匿名相談を無条件でDBに永続化する現行挙動を維持するか。「保存」ボタンの意味を何にするか | 匿名含め全件保存済み。「保存」ボタンは実質no-op（5-4） | データ保持ポリシー + UX |
| D13 | 到達不能な認証/My Page実装3系統（R11）と `favorites` アプリを削除するか | 死にコードとして残存 | 削除自体は技術判断だが、`accounts/` テンプレート版の将来利用意図が不明 |
| D14 | `middleware.ts` の保護対象を `/mypage` のみとするか | 他のログイン必須画面はclient側判定のみ | — |

---

## 8. UNRESOLVED 一覧（証拠不足・矛盾により本書で結論を出していないもの）

| # | 項目 | 理由 |
| --- | --- | --- |
| U1 | Concierge の生年月日fallback（保存値のみのケース）の実挙動 | コード上の順序はCONFIRMEDだが、テストによる保護がなく、実行検証もしていない（テスト環境未構築） |
| U2 | 本番環境の `BILLING_PROVIDER` / `BILLING_STUB_PLAN` の実値 | 環境変数はリポジトリ内にない。`.env.example` にも当該キーは**存在しない**（Django core / DB / Concierge / Places / Storage のみ）。実運用のFree/Premium判定がDB由来かenv由来かは**コードだけでは決定不能** |
| U3 | 本書内のすべてのテスト参照 | テストを実行していないため、記載したtestが現在passしているかは未確認 |

**補足（U3から降格・解決済み）**: `lib/api/billing.ts:18` は `/api/billings/status/`（末尾スラッシュ付き）をfetchするが、`apps/web/next.config.ts:13` は `trailingSlash: false`。308 redirect を1ホップ挟んで到達する（`fetch` は既定でredirectを追う）。機能上の断線ではない。status: **CONFIRMED**
