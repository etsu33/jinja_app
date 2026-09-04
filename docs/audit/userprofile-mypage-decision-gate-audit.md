# UserProfile / My Page / Free-Premium Decision Gate Audit

> **Status: Audit / Historical（2026-09-04、`aae0a0a` 時点のruntime code読解）**
>
> 本書はaudit専用。実装・refactor・schema・route・permission・billing・My Page・Compass統合・Conciergeロジックのいずれも変更していない。
> 先行audit `docs/audit/user-account-mypage-free-premium-audit.md` の再監査であり、**同書の誤りを2件訂正している**（§0-3）。
> Runtime code と test を最終正本とする。docs は「意図された契約とのmismatch検出」にのみ使用した。

## 0. 監査の前提

### 0-1. 概念の分離（本書の中核）

| 概念 | 定義 | 実体 |
| --- | --- | --- |
| `UserProfile` | 永続化されたユーザーデータ／ドメインモデル | `backend/users/models.py::UserProfile`（`django_user` に対する OneToOne、16フィールド） |
| `My Page` | ユーザー所有データを閲覧・編集する**UIのひとつ** | Next.js route `/mypage` → `apps/web/src/app/mypage/page.tsx` → `apps/web/src/components/views/MyPageView.tsx` |

「UserProfileが存在するからMy Pageが必要」という推論は本書では採らない。

### 0-2. 手法と限界

- 手法: `ROOT_URLCONF` からの到達可能性追跡 → BFF route → Django view → serializer → service層 の静的トレース。
- **テストは実行していない**（`apps/web/node_modules` 未インストール、Django未インストール）。本書が引用するtestは、当該assertionがファイル内に存在することをコード上確認したもの。pass/failは未実測 → 該当箇所は `CONFIRMED (static)` と表記する。
- 判定語彙: `CONFIRMED` / `NOT_FOUND` / `UNRESOLVED`
- 分類語彙:
  - `FACT_VERIFICATION` — code / test / 環境変数の確認だけで決着する。製品判断ではない
  - `CONTRACT_MISMATCH` — Active契約文書とruntimeが食い違う、または実装内部で2つの正本が併存する
  - `MOTHER_SHIP_DECISION` — code からは決められない製品判断

### 0-3. 先行auditとの差分（訂正）

| # | 先行auditの記述 | 実際 | 証拠 |
| --- | --- | --- | --- |
| C1 | 「Concierge quota は anonymous 3 / free 3」 | **free は 5**。`check_quota` が `QUOTA_POLICY["free"]["concierge"]["limit"]=3` を `settings.CONCIERGE_DAILY_FREE_LIMIT` で上書きする | `backend/temples/services/quota_service.py:196-198`、`backend/shrine_project/settings.py:16`（`CONCIERGE_DAILY_FREE_LIMIT = 5`）、`backend/temples/tests/api/test_concierge_chat_response_matrix_contract.py:142`（`assert body["limit"] == 5`） |
| C2 | 「Premium実効差分はConciergeの回数無制限のみ」（記述は正しいが不完全） | 加えて **Free/Anonymous の回数は日次ではなく累積（生涯）**。`FeatureUsage` に日付フィールドがない | `backend/temples/models_usage.py:8-33`（scope / user / anon_id / feature / count / created_at / updated_at のみ）、`quota_service.py:108-146` |

リポジトリ自体は先行audit時点から変化していない（`git log` の差分は先行audit文書の追加コミット `aae0a0a` のみ、working tree clean）。差分はすべて**先行auditの読み違い**であり、リポジトリの変化ではない。

---

## Main Question への回答

> UserProfile は `/mypage` を技術的依存とせずに Compass / Concierge / favorites / history 等の認証機能へ供給できるか。

**できる。`/mypage` に技術的に依存している機能は1つも存在しない。** status: **CONFIRMED**

根拠（3点、すべてcode-verifiable）:

1. **UserProfile の読み書きAPIは `/mypage` を知らない。** 読み取りは `GET /api/users/me/`（`apps/web/src/app/api/users/me/route.ts` → `backend/users/api/views.py::MeView.get`）、書き込みは `PATCH` 同エンドポイント。どちらも route / referer / 画面種別を一切参照しない。
2. **frontend の profile 供給点は `AuthProvider` であり、My Page ではない。** `apps/web/src/lib/auth/AuthProvider.tsx:51-77` の `fetchMe()` が `/api/users/me/` を叩き、`useAuth().user.profile` として全画面へ供給する。実際に Concierge（`app/concierge/ConciergeClientFull.tsx:1003`）は My Page を経由せず直接この値を読んでいる。**「My Pageを介さずUserProfileを消費する」経路は既に本番実装として存在する。**
3. **認証付きの全機能が汎用BFF経由で成立している。** favorites (`app/api/favorites/route.ts`)、visits (`app/api/visits/route.ts`)、concierge-threads (`app/api/concierge-threads/route.ts`)、my/goshuins (`app/api/my/goshuins/route.ts`)、shrine-submissions (`app/api/shrine-submissions/route.ts`) — いずれも `bffFetchWithAuthFromReq` に cookie 由来の JWT を載せるだけで、`/mypage` への依存はない。実際 favorites は `/favorites`（`app/favorites/page.tsx`）という独立routeで既に同じデータを描画している。

**唯一の非技術的依存**: プロフィール編集フォーム（`birthday` を含む UserProfile 書き込みの入口）は現状 `/mypage?tab=profile` にしか実装がない。これは「My Pageが技術的に必要」ではなく「**書き込みUIが現在そこにしか置かれていない**」という配置の事実である。`PATCH /api/users/me/` は呼び出し元を問わないため、別画面・モーダル・オンボーディングのいずれからでも成立する。status: **CONFIRMED**

---

## 1. UserProfile responsibility map

**Model**: `backend/users/models.py::UserProfile`
**Live read serializer**: `backend/users/api/serializers.py::UserMeSerializer` → `UserProfileSerializer`（`:28-49`）
**Live write serializer**: `backend/users/api/serializers.py::UserProfileUpdateSerializer`（`:60-72`）
**Live endpoint**: `GET|PATCH /api/users/me/` → `backend/users/api/views.py::MeView`（`JWTAuthentication` + `IsAuthenticated`、`:69-101`）
**Live BFF**: `apps/web/src/app/api/users/me/route.ts`
**Live frontend consumer**: `apps/web/src/lib/auth/AuthProvider.tsx::fetchMe` → `useAuth().user.profile`

> 注: `backend/users/serializers.py`（`MeSerializer` / `UserProfileSerializer`）は**死んだURLConf側**のserializerであり本表の対象外。§5参照。

| Field | stored | writable (API) | readable (API) | public exposure | actual consumers | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| `nickname` | ○ `models.py:11` | ○ `UserProfileUpdateSerializer` | ○ | **○** `public_profile.py:41` | `MyPageView.tsx:206,353` の編集フォームのみ。**frontendの表示用読み取りは全滅**（§1-1） | 部分的にdead |
| `is_public` | ○ default **True** `models.py:12` | ○ | ○ | ○（自身が公開可否のゲート） | `MyPageView.tsx:207,406`（チェックボックス）、`public_profile.py:35-37`（ゲート） | active |
| `bio` | ○ `models.py:13` | ○ | ○ | ○ `public_profile.py:43` | **編集UIが存在しない**（`grep -n "bio" MyPageView.tsx` → 0件）。読み手は断線中の公開プロフィールページのみ | **field exists only** |
| `icon` | ○ `models.py:14` | △ Django層では可（`MeView.patch` は `MultiPartParser` 対応）／**BFF経由では不可**（`app/api/users/me/route.ts::PATCH` が `Content-Type: application/json` 固定でbody textを転送） | ○（`icon` / `icon_url`） | ✕（`public_profile.py:42` は `getattr(profile,"icon_url")` を読むが**モデルに `icon_url` 属性はない** → 常に `None`） | 専用endpoint `POST /api/users/me/icon/` は**backend未ルーティング**。`ProfileIconCard.tsx` は import 0件。`uploadUserIcon` はtest以外に呼び出し元なし | **implemented but disconnected** |
| `birthday` | ○ `models.py:16` | ○（`validate_birthday` が未来日を400） | ○ | **○** `public_profile.py:44` → `app/users/[username]/page.tsx:44-60` が年齢付きで描画 | Concierge（clientがrequest bodyへ載せる経路のみ）、My Page派生表示 | **implemented and connected**（§4） |
| `birth_time` | ○ `models.py:17` | ○ | ○ | ✕ | `profile_context.user_profile.birthTime` としてConciergeへ送信されるが、**backendに読み手が0件**（`grep -rn "birthTime\|birth_time" backend/` は serializer / model / migration / test のみ） | **field exists only** |
| `birth_place` | ○ `models.py:18` | ○ | ○ | ✕ | 同上（`birthPlace`） | **field exists only** |
| `worship_style` | ○ `models.py:19` | ○ | ○ | ✕ | `profile_context.user_profile.worshipStyle` → `backend/temples/services/concierge_chat_ranking.py:356-368` の `_score_profile_signal` で最大 **+0.01** | **implemented and connected** |
| `created_at` | ○ `models.py:20` | ✕ read_only | ○ | ✕ | 消費者 **0件** | dead |
| `stripe_customer_id` | ○ `models.py:22` | ✕ serializer未収載 | ✕ | ✕ | 書: `billing_checkout.py:64`(read) / `stripe_webhook.py:274-283`(write)。読: `stripe_webhook.py:308-312`（customer_id → profile 逆引き） | active（stripe運用時のみ） |
| `stripe_subscription_id` | ○ `models.py:23` | ✕ | ✕ | ✕ | `stripe_webhook.py:280,325-328` の書き込みのみ。**読み手が存在しない** | write-only |
| `stripe_price_id` | ○ `models.py:24` | ✕ | ✕ | ✕ | `stripe_webhook.py:340-342` の書き込みのみ。**読み手が存在しない** | write-only |
| `subscription_status` | ○ default `"inactive"` `models.py:26-31` | ✕ | ✕ | ✕ | 書: webhook。読: `billing_state.py:66` — ただし **`BILLING_PROVIDER=stub`（既定）では読まれない**（§6） | conditional |
| `current_period_end` | ○ `models.py:32` | ✕ | ✕ | ✕ | 同上（`billing_state.py:67` → `users/services/billing.py::is_subscription_active`） | conditional |
| `updated_at` | ○ `models.py:34` | ✕ | ✕ | ✕ | webhookの `update_fields` に含まれるのみ | internal |

### 1-1. `nickname` の読み取り経路が全滅している件

- live serializer `UserMeSerializer`（`backend/users/api/serializers.py:52-57`）の fields は `("id","username","email","first_name","last_name","profile")`。**top-level に `nickname` は存在しない**。
- 一方 frontend は `apps/web/src/lib/auth/types.ts:8` で `AuthUser.nickname` を宣言し、`app/concierge/ConciergeClientFull.tsx:529,538` が `user?.nickname` を読む → **常に `undefined`**。
- `lib/profile/resolveDisplayName.ts::resolveDisplayName({sessionNickname, profileNickname})` の `profileNickname` は常に null に落ち、表示名は「セッション入力 or `"あなた"`」に縮退する。
- top-level `nickname` を返すのは**死んだ** `backend/users/serializers.py::MeSerializer:29,57-59` のみ。
- 同様に `AuthUser.birthday`（top-level、`types.ts:7`）と `toProfileState()`（`types.ts:30-35`）も live serializer に対応フィールドがなく、`toProfileState` は**呼び出し元 0件**。
- status: **CONFIRMED**

---

## 2. My Page dependency map

`/mypage` の live 責務と、その依存先。

| # | 責務 | 実装 | 依存している実体 | `/mypage` route への技術的依存 | 現行アーキテクチャで独立可能か |
| --- | --- | --- | --- | --- | --- |
| 1 | プロフィール編集（nickname / is_public / birthday / birth_time / birth_place / worship_style） | `components/views/MyPageView.tsx:340-430`, `:194-216` | `PATCH /api/users/me/`（UserProfile） | **なし** | **可能**。API は呼び出し元を問わない。ただし現在この書き込みUIは他に存在しない |
| 2 | 派生プロフィール表示（九星／五行／ライフパス／吉方位） | `MyPageView.tsx:192-193, 386-402` | `lib/profile/derivedProfile.ts` の pure 関数。**form state から毎回再計算**（保存値ではない） | なし | **可能**。永続化なし・他機能へ流れない純表示 |
| 3 | 保存した神社（Favorites） | `features/mypage/components/FavoritesSection.tsx`、SSR初期値 `app/mypage/page.tsx:8` | `GET /api/favorites/` | なし | **既に独立実装が存在**（`app/favorites/page.tsx` が同じ `getFavoritesServer()` を使用） |
| 4 | 参拝履歴 | `MyPageView.tsx:157-178, 302-352` | `GET /api/visits/` | なし | 可能 |
| 5 | 投稿した神社 | `features/mypage/components/MyPageScreen.tsx`（`activeTab="submissions"`） | `GET /api/shrine-submissions/`（`ShrineSubmissionCreateView` は `ListCreateAPIView`、`shrine_submission.py:19-27`） | なし | 可能 |
| 6 | 相談履歴 | **既に My Page 外の独立route** `/mypage/history`（`app/mypage/history/page.tsx`）。My Page からはリンクのみ（`MyPageView.tsx:280-286`） | `GET /api/concierge-threads/` | なし | **既に分離済み**（URL接頭辞が同じだけで別ページ） |
| 7 | 御朱印管理 | `MyPageScreen.tsx`（`activeTab="goshuin"`） | `GET/POST /api/my/goshuins/` | — | **UIから到達不能**。`GOSHUIN_TAB_ENABLED = false`（`MyPageView.tsx:18`）で tab 非描画、`normalizeTab`（`:33-37`）も `"goshuin"` を返さない |
| 8 | プロフィールアイコン変更 | `features/mypage/components/ProfileIconCard.tsx` | — | — | **import 0件**。かつ backend endpoint 未ルーティング（§1表 `icon` 行） |
| 9 | Premium状態の表示 | **My Page には存在しない**。`useBilling` / `getBillingStatus` の参照は `MyPageView.tsx` / `MyPageScreen.tsx` に 0件 | — | — | 現状 My Page は Premium 状態を一切表示していない。`docs/product/premium-experience.md`「マイページ = Premiumの継続価値を見せる画面」と不一致（§10 M6） |
| 10 | 設定（ログアウト） | `MyPageScreen.tsx:24,` `components/layout/HeaderAuthButtons.tsx:10,32` | `POST /api/auth/logout` | なし | **ヘッダに既に存在**（重複） |

**別実装の My Page（到達不能）**: `accounts/` Django アプリ（`accounts/urls.py` の `mypage/`、`accounts/views.py::mypage`、`templates/accounts/mypage.html`）は `INSTALLED_APPS` に存在せず（`backend/shrine_project/settings.py` の `INSTALLED_APPS` = django built-ins + django_filters, rest_framework, simplejwt, token_blacklist, corsheaders, drf_spectacular, **users, favorites, temples, storages**）、`accounts.urls` を include する箇所も 0件。status: **CONFIRMED（到達不能）**

**判定**: 責務1〜10のうち、`/mypage` route の存在を技術的前提とするものは **0件**。status: **CONFIRMED**
存廃・再配置は本書の責務外（§11 D9）。

---

## 3. Compass ↔ UserProfile status

| 観点 | 結果 | 証拠 | status |
| --- | --- | --- | --- |
| 匿名アクセス | 可 | `backend/temples/api_views_compass.py:45` `permission_classes = [AllowAny]` | CONFIRMED |
| auth 依存 | **なし** | `features/compass/` 配下に `useAuth` / `isLoggedIn` / `withAuth` の参照 0件（grep実行済み） | CONFIRMED |
| billing 依存 | **なし** | 同 grep で `useBilling` / `premium` / `accessLevel` も 0件 | CONFIRMED |
| quota | **なし** | `check_quota` の呼び出しは `api_views_concierge.py:654` の1箇所のみ。ただし DRF throttle は有効（`throttle_scope = "compass"`、`api_views_compass.py:47`） | CONFIRMED |
| persistence | **なし** | `temples/services/compass_recommendation_orchestrator.py` / `compass_runtime.py` に `objects.create` / `.save(` が 0件。view も thread を作らない | CONFIRMED |
| birthdate source | **画面フォームのみ** | `features/compass/CompassClient.tsx:89` `useState("")`、`:249` `<input type="date">`、`:175` `birthdate: birthdate.trim()` を POST。初期値を注入する経路なし | CONFIRMED |
| 保存 `UserProfile.birthday` の消費 | **していない** | 同上。backend も `UserProfile` を読まない（`grep -rn "UserProfile" backend/temples/` のヒットは `billing_checkout.py` / `billing_state.py` のみ） | NOT_FOUND |
| optional な profile 再利用が技術的に可能か | **可能** | ① backend は `birthdate` を request body から受ける設計（`api_views_compass.py:54`）で、ログイン必須化を伴わない ② `AuthProvider.shouldAutoFetchMe()`（`AuthProvider.tsx:79-101`）は `/compass` について既定の `return true` に落ちるため、**Compass 画面でも `/api/users/me/` は既に取得済み**。データは client 側の手元にあり、`CompassClient` が読んでいないだけ | CONFIRMED |

補足: view の docstring（`api_views_compass.py:37-43`）が「Free/Premium判定・quota・thread はこのViewの責務ではない（Phase 5時点でCompassはgatingなし）」と明記しており、runtime と一致している。**Compass に関しては docs と実装のmismatchは検出されなかった。**

---

## 4. Concierge ↔ UserProfile status

### 4-1. end-to-end トレース

```
[A] セッション入力 sessionState.temporaryBirthdate
      app/concierge/ConciergeClientFull.tsx:1002  ← filter_set_birthdate action (:1640-1643)
[B] 保存プロフィール  useAuth().user.profile
      ConciergeClientFull.tsx:1003  savedProfile: user?.profile
                    ↓
features/concierge/buildConciergeRequestPayload.ts:66-67
  birthdate        = normalizeBirthdateInput([A]) ?? normalizeProfileBirthday([B].birthday)
  payloadBirthdate = input?.birthdate ?? birthdate        // [C] 呼び出し側override が最優先
                    ↓  :90-110
  payload.birthdate
  payload.filters.birthdate
  payload.profile_context.user_profile.{birthday,birthdate,birthTime,birthPlace,worshipStyle}
  payload.profile_context.derived_profile.{kyusei,gogyo,lifePath}
                    ↓  POST /api/concierge/chat  →  app/api/concierge/chat/route.ts  →  Django
backend/temples/api_views_concierge.py
  :551  canonical_input.birthdate          → element/astro scoring
  :564  resolve_profile_context_birthdate(raw_profile_context)
  :570-572  planned_visit_lucky_directions(profile_birthdate or birthdate, visit_date)
            / annual_lucky_directions(profile_birthdate or birthdate)
  :579  raw_profile_context["direction_profile"] = calculated_direction   ← backend が上書き注入
  :808  build_chat_recommendations(..., profile_context=raw_profile_context)
            → concierge_chat_ranking.py:1345  _score_profile_signal   (gogyo +0.02 / worshipStyle +0.01, 上限 +0.03)
            → concierge_chat_ranking.py:1348  _score_direction_signal (direction_profile)
```

- backend 側 permission: `api_views_concierge.py:500` `AllowAny`（quota gate のみ）。status: **CONFIRMED**

### 4-2. 2層が異なる canonical value を生みうるケース（全件）

| # | 層 | 分岐点 | 異なる値になる条件 | 影響先 | status |
| --- | --- | --- | --- | --- | --- |
| P1 | frontend内 | `buildConciergeRequestPayload.ts:66` の `??` | セッション入力と保存プロフィールの生年月日が食い違うとき、**セッション入力が勝つ** | payload 全体 | CONFIRMED |
| P2 | frontend内（**ロジック重複**） | `ConciergeClientFull.tsx:971-972` が同じ precedence を独立に再実装（`baseFilters` memo 用） | 現状は順序一致。片方だけ変更されると乖離する | `baseFilters.birthdate` = UIチップ表示（`:1784`） | CONFIRMED |
| P3 | frontend内 | `buildConciergeRequestPayload.ts:105-110` | `birthday` は [A]優先だが、`birth_time` / `birth_place` / `worship_style` は **`savedProfile` からのみ**。未ログインユーザーは生年月日しか供給できず、セッション入力で birthday を上書きすると **birthday と birthTime が別人の値になりうる** | `profile_context.user_profile` | CONFIRMED |
| P4 | frontend内 | `buildConciergeRequestPayload.ts:99` | `derived_profile`（九星・五行）は `payloadBirthdate` から算出されるので P3 の不整合を継承する | `_score_profile_signal` | CONFIRMED |
| P5 | **backend内** | `api_views_concierge.py:564` vs `:551` | `profile_context.user_profile.birthdate` と `canonical_input.birthdate` が食い違うとき、**方位計算だけ `profile_context` が勝つ**（`resolve_profile_context_birthdate(...) or canonical_input.birthdate`）。scoring は canonical のまま | 方位 vs 五行スコアが別の生年月日に基づく | CONFIRMED |
| P6 | frontend↔backend | `buildProfileContext`（front）が `direction_profile` を送らず、backend が `:579` で自前計算を注入 | My Page が表示する吉方位（`buildDirectionProfile`, `annual_kyusei_v1`）と Concierge が使う方位（`temples/domain/kyusei.py::annual_lucky_directions` / `planned_visit_lucky_directions`）が**別実装** | ユーザーに見える方位が画面間で食い違いうる | CONFIRMED |
| P7 | 画面間 | Compass は第3の方位実装（`compass_runtime.py::build_compass_direction_runtime`、`annual_monthly_kyusei_v1` / `monthly_kyusei_v1`） | 同上、3実装目 | 同上 | CONFIRMED |

`backend/temples/services/concierge_input_contract.py:299-317` の docstring が P5 を「Documented Current Gap、統一は本PRの範囲外」と自己申告している。

### 4-3. 匿名ユーザーの永続化

`api_views_concierge.py:918-947` — `append_user = user if authenticated else None` / `append_anonymous_id = plan_context.anon_id`。**認証有無にかかわらず全リクエストで `append_chat` が呼ばれる。** §7 参照。

### 4-4. テスト被覆

| 対象 | test | status |
| --- | --- | --- |
| L3-A: birthdate が top-level / filters / profile_context の3箇所に載る | `apps/web/src/features/concierge/__tests__/buildConciergeRequestPayload.test.ts:89-98` | CONFIRMED (static) |
| Full Integration | 同 `:135-168`。ただし `temporaryBirthdate` と `savedProfile.birthday` に**同一値**を与えている | CONFIRMED (static) |
| **P1（食い違い時の precedence）** | **該当テストなし**。`savedProfile` は他の全ケースで `null` | **NOT_FOUND** |
| **P3（birthday と birthTime の出所が分かれる）** | **該当テストなし** | **NOT_FOUND** |
| P5（backend の二重 chain） | `backend/temples/tests/test_concierge_l3_contract.py:31-45`、`backend/temples/tests/api/test_concierge_chat_l3_context_contract.py:150` | CONFIRMED (static) |

---

## 5. Authentication runtime map

### 5-1. Live 経路

```
apps/web/src/app/login/LoginForm.tsx  (or SignupForm.tsx)
  → lib/api/auth.ts::login / signup            (fetch, credentials: same-origin)
  → BFF  app/api/auth/login/route.ts           → Django /api/auth/jwt/create/
         app/api/auth/register/route.ts        → Django /api/users/signup/
         app/api/auth/logout/route.ts          （cookie削除のみ、backend呼び出しなし）
  → access_token / refresh_token を HttpOnly Cookie へ (login/route.ts:120-134)
  → AuthProvider.refreshMe() → GET /api/users/me/
  → BFF bffFetchWithAuthFromReq (lib/server/bffFetch.ts)
         cookie → Authorization: Bearer、exp近接なら事前refresh、401/403でrefresh再試行
  → Django ROOT_URLCONF = shrine_project.urls  (settings.py:299)
       :82  path("api/users/me/", users.api.views.MeView)
       :83  include(("users.api.urls","users"), namespace="users_api")
       JWTAuthentication → request.user
```

`docs/core/authentication-flow.md`（Status: Active）の規定経路と一致。status: **CONFIRMED**

### 5-2. Dead / unreachable（ファイル名から liveness を推定していないことの明示）

| # | 実体 | 到達不能の根拠 | status |
| --- | --- | --- | --- |
| A1 | `backend/config/urls.py` | `ROOT_URLCONF = "shrine_project.urls"`（`settings.py:299`）。`grep -rn "config.urls"` のヒットは当該ファイル自身と `users/tests/test_views_no_sensitive_logging.py:5` のコメントのみ | CONFIRMED |
| A2 | `backend/users/urls.py` + `backend/users/views.py`（`MeView` / `CurrentUserView` / `MeIconUploadView`） | A1 経由でしか include されない。`shrine_project/urls.py` は `users.api.urls` のみ include | CONFIRMED |
| A3 | `backend/users/serializers.py`（`MeSerializer` / `UserProfileSerializer` / `MeIconUploadSerializer`） | A2 からのみ import。§1-1 の `nickname` 断線の原因 | CONFIRMED |
| A4 | `accounts/` Django アプリ一式（`urls.py` / `views.py` / `templates/accounts/`） | `INSTALLED_APPS` に不在、include 0件 | CONFIRMED |
| A5 | `backend/favorites/` Django アプリ | `INSTALLED_APPS` には**ある**が `favorites.urls` を include する箇所が 0件。`temples.models.Favorite` と重複したモデルが migration ごと残存 | CONFIRMED |
| A6 | `backend/<goshuin_app>/api_views_public.py` | ディレクトリ名が literal `<goshuin_app>`。`INSTALLED_APPS` に不在 | CONFIRMED |
| A7 | `POST /api/users/me/icon/`（backend） | live な `users/api/urls.py` は `users/me/`, `users/me/storage/`, `users/signup/`, `stripe/webhook/` のみ。`shrine_project/urls.py` にも icon path なし。BFF `app/api/users/me/icon/route.ts` は存在するが upstream が 404 | CONFIRMED |
| A8 | `apps/web/src/lib/auth/withAuth.tsx`（`withAuth` / `RequireAuth`） | import 0件（`grep` のヒットは無関係な `onRequireAuth` prop のみ） | CONFIRMED |
| A9 | `apps/web/src/app/api/me/route.ts` | 自身が「互換API。新規参照禁止」と明記（`:9-10`）。呼び出し元 0件 | CONFIRMED |
| A10 | `lib/api/client.ts:12-17` の Authorization interceptor | `getCookie`（`lib/api/authTokens.ts:2-6`）は `document.cookie` を読むが、`access_token` は **HttpOnly**（`app/api/auth/login/route.ts:123`）。ブラウザからは読めず、ヘッダは常に未設定。axios 経由の呼び出しは cookie（`withCredentials`）のみで成立している | CONFIRMED |
| A11 | `lib/api/authTokens.ts::setCookie` | 呼び出し元 0件 | CONFIRMED |
| A12 | `lib/api/users.ts::updateMe` | 呼び出し元 0件（`MyPageView` は `updateUser` を使用） | CONFIRMED |

### 5-3. Live BFF routes（認証付き）

`app/api/` 配下で `bffFetchWithAuthFromReq` / `bffPostJsonWithAuthFromReq` を使用: `users/me`, `users/me/icon`(upstream 404), `me`(dead), `favorites`, `favorites/[id]`, `favorites/preload`, `visits`, `concierge-threads`, `concierge-threads/[id]`, `my/goshuins`(+`count`,`[id]`), `my/shrines`, `shrine-submissions`, `billings/status`, `billings/checkout`, `compass/recommendations`, `shrines/[id]/visit`, `shrines/[id]/reflection`, `shrine-interactions`。
`app/api/concierge/chat` のみ独自プロキシ（`djFetch` + anon cookie 転送、`app/api/concierge/chat/route.ts`）。

### 5-4. 認証まわりの副次的な不整合（D項目化しない小粒）

- `apps/web/src/app/signup/SignupForm.tsx:37-50` は `AxiosError` 形（`e.response.status` / `e.response.data`）で分岐するが、`lib/api/auth.ts::signup` は fetch ベースで plain `Error` を throw する。したがって backend の 400 バリデーションメッセージは**常に表示されず**「通信に失敗しました。」へ縮退する。status: **CONFIRMED**
- `app/api/auth/login/route.ts:100-105` は失敗時に `upstreamBody: bodyText.slice(0,1000)` を client へ返す。`docs/core/runtime-security-baseline.md` §7 の禁止列挙（`_debug` / raw exception / path / DB情報 / secret / 相談本文）には該当しないが、upstream の生 body をそのまま返す設計である。status: **CONFIRMED**
- `apps/web/middleware.ts:8-16` は `/mypage` のみを対象とし、`access_token` cookie の**存在**だけを見る（署名・失効を検証しない）。失効済み cookie でも通過し、以降は client 側の `useAuth` に委ねられる。status: **CONFIRMED**

---

## 6. Free / Premium enforcement map

### 6-1. plan 解決の全経路

```
Environment                              backend/temples/services/billing_state.py
  BILLING_PROVIDER (既定 "stub")   ──→   provider()                      :26-28
  BILLING_STUB_PLAN (既定 "free")  ──→   _billing_stub_env()             :31-34
  BILLING_STUB_ACTIVE (既定 "0")
  BILLING_STUB_CANCEL_AT_PERIOD_END
                                          get_billing_status(user)        :37-83
                                            provider=="stub"  → _status_from_stub_env()  ★userを一切見ない :56-58
                                            provider in {stripe,revenuecat} かつ 認証済み
                                              → UserProfile.subscription_status / current_period_end  :59-80
                                                → users/services/billing.py::is_subscription_active
                                            未認証 → _status_from_stub_env()  :82
                                          is_premium_for_user(user)       :130-144
                                            user.is_staff → True（無条件）  :132-138
                                            else → status.plan=="premium" and is_active
                                                    ↓
temples/services/plan_service.py::resolve_plan_context(request)   :23-48
   未認証 → PlanContext(plan="anonymous", anon_id=…)
   認証済 → "premium" | "free"
                                                    ↓
temples/services/quota_service.py::check_quota(plan_context, "concierge")
   policy = quota_policy.get_feature_policy(plan, feature)
   free かつ concierge のとき limit = settings.CONCIERGE_DAILY_FREE_LIMIT (=5)   :196-198
   used   = get_used_count()  = max(FeatureUsage.count, ConciergeUsage(今日).count)  :108-170
                                                    ↓
api_views_concierge.py:654 check_quota / :1013 consume_quota   ← 唯一の enforcement 地点
                                                    ↓  response body の plan/remaining/limit/limitReached
BFF app/api/billings/status/route.ts  ← Django /api/billings/status/ (AllowAny)
    NODE_ENV!=="production" かつ NEXT_PUBLIC_FORCE_BILLING_PLAN==="premium" → backend迂回で premium 返却  :20-28
    upstream !ok → STUB(free) を 200 で返す（フェイルオープンではなくフェイル"free"）  :34-36
                                                    ↓
lib/premium/accessLevel.ts::resolveAccessLevel(billingStatus, isAuthenticated)
lib/premium/cardVisibility.ts::CARD_VISIBILITY_POLICIES（23カード × 3階層）
```

### 6-2. 4層の分離

| 層 | 実体 | 実効範囲 | status |
| --- | --- | --- | --- |
| **visual gating** | `lib/premium/cardVisibility.ts`（23カード）、`ShrineDetailArticle.tsx:558-571`、`ConciergeSectionsRenderer.tsx:365-377`、`ConciergeClientFull.tsx:470-473` | 表示のみ。API から届いた内容を隠すだけ | CONFIRMED |
| **backend authorization** | DRF `permission_classes`。plan を参照する view は **0件**（`IsAuthenticated` か `AllowAny` の二択） | 認証の有無のみ。**Premium という認可段階が backend に存在しない** | CONFIRMED |
| **quota enforcement** | `check_quota` / `consume_quota` | **`concierge` のみ**。`favorite` / `goshuin_upload` / `shrine_search` の policy は定義のみで呼び出し元なし | CONFIRMED |
| **data returned by API** | `_build_chat_response`（`api_views_concierge.py:321-374`）で plan 依存なのは `plan` / `remaining` / `limit` / `limitReached` の4フィールドのみ。本文・セクションは全プラン同一 | Premium 本文は Free / Anonymous にも届く | CONFIRMED |

### 6-3. quota の実挙動（先行auditからの訂正を含む）

| 対象 | limit | カウンタ | リセット | 証拠 |
| --- | --- | --- | --- | --- |
| anonymous / concierge | **3** | `FeatureUsage(scope="anonymous", anon_id, feature)` | **なし（累積・生涯）** | `quota_policy.py:9`、`models_usage.py:8-33`（date フィールドなし）、`quota_service.py:113-119` |
| free / concierge | **5**（`QUOTA_POLICY` の 3 を settings が上書き） | `max(FeatureUsage(scope="user"), ConciergeUsage(今日))` | **実質なし**。`ConciergeUsage` は日次だが `min(count+1, 5)` で頭打ち（`quota_service.py:272-274`）、`get_used_count` が `max()` を取るため累積側が下がらない | `quota_service.py:196-198`、`:148-160`、`settings.py:16`、`test_concierge_chat_response_matrix_contract.py:142` |
| premium / concierge | 無制限 | — | — | `quota_policy.py:21` |
| favorite / goshuin_upload / shrine_search | policy 定義あり | — | — | **enforcement 地点が存在しない** |
| 御朱印件数 | 全プラン **10** | — | — | `temples/services/goshuin_limit.py`（`get_my_goshuin_limit(user)` が `user` を捨てて定数を返す） |
| ストレージ | 全プラン `STORAGE_LIMIT_BYTES`（既定 200MB） | — | — | `backend/users/api/views.py:26-27`、`settings.py:451` |

**帰結**: 登録済み Free ユーザーは**生涯5回**で Concierge が恒久的に閉じる。匿名で3回使い切った後に登録すると、scope が `anonymous` → `user` に変わるため**カウンタがリセットされて追加5回**が得られる。status: **CONFIRMED**

### 6-4. checkout の実挙動

`temples/services/billing_checkout.py:38-46` — `provider() != "stripe"` のとき、Stripe を呼ばずに `session_id = f"stub_checkout_{user.pk}"` と `checkout_url = success_url + ?checkout_session_id=...` を返す。**決済なしで `/billing/success` へ遷移する。** かつ `get_billing_status` は stub のとき DB を読まないため、この遷移は plan を変えない。
→ 既定設定（`BILLING_PROVIDER` 未設定）では、**課金ループ全体（checkout → webhook → UserProfile → plan判定）が閉じていない**。webhook は `UserProfile` を正しく更新するが（`stripe_webhook.py:256-378`）、その値は provider が stripe でない限り読まれない。status: **CONFIRMED**

---

## 7. Premium content exposure

| 質問 | 回答 | 証拠 | status |
| --- | --- | --- | --- |
| 匿名ユーザーが Premium payload を受け取れるか | **受け取れる** | `temples/api/views/shrine_meaning.py:13` `AllowAny` かつ `compose_shrine_meaning_payload(shrine)` は user / access 引数を取らない（`:21`）。`shrine_meaning_composer.py:839-851` は `access="premium"` タグ付き block（`action_meaning` / `after_visit_reflection` / `history_context` / `deity_symbol` / `benefit_action`）を body ごと返す | CONFIRMED |
| Free ユーザーが Premium payload を受け取れるか | **受け取れる** | 同上。加えて `/api/concierge/chat/` の本文が plan 非依存（§6-2） | CONFIRMED |
| frontend は配信済みコンテンツを隠しているだけか | **そのとおり** | `cardVisibility.ts` の `teaser` / `hidden` は描画側の分岐。ネットワークには既に本文が届いている | CONFIRMED |
| backend は Premium コンテンツをフィルタするか | **しない** | plan を参照する view / serializer が 0件 | NOT_FOUND |
| backend が宣言する `access` を frontend は読むか | **読まない** | `ShrineMeaningAccessLevel` / `block.access` の参照は型定義 `lib/shrineMeaning/payloadV2.ts:18,89` のみ。`fetchShrineMeaningPayloadV2Server`（`app/shrines/[id]/page.tsx:286`）の結果から `access` を分岐に使う箇所なし | CONFIRMED |

**Active 契約との照合**: `docs/product/billing-paywall.md`（Status: Active）「真実の所在 — **利用可否**の最終判断はサーバー側で行う」。この条項の対象は *利用可否 / Paywall* であり、quota は実際にサーバー側で強制されている（§6）。**同書は「Premium 本文をサーバー側でフィルタする」とは規定していない。** したがって §7 の露出は billing-paywall.md の literal violation ではない。
一方、`shrine_meaning_composer.py` が block 単位で `access` 階層を**宣言しながら強制も伝達もしていない**点、および frontend が別テーブルで同じ階層を再宣言している点は、実装内部の二重正本であり `CONTRACT_MISMATCH`（§10 M1 / M2）。

---

## 8. Save / persistence map

| 概念 | 現行の実体 | 誰の所有 | status |
| --- | --- | --- | --- |
| **technical persistence（自動）** | `/api/concierge/chat/` の**全リクエスト**で `append_chat()` が `ConciergeThread` + `ConciergeMessage` + `recommendations` / `recommendations_v2` を書く | 認証済 → `thread.user`／未認証 → `thread.anonymous_id` | `api_views_concierge.py:918-947`、`temples/services/concierge_history.py:356-415` — CONFIRMED |
| **anonymous session persistence** | `concierge_anon_id` cookie（`app/api/concierge/chat/route.ts:41-47`、`httpOnly, sameSite:"none", secure, maxAge 90日`）に紐づく DB レコード | 誰の account にも属さない | CONFIRMED |
| **user-owned saved history** | `ConciergeThread.user` が非 NULL のもののみ。一覧 `GET /api/concierge-threads/` は `IsAuthenticated` かつ `filter(user=user)`（`temples/api/views/concierge.py:59,63`） | ユーザー | CONFIRMED |
| **匿名レコードの後日 claim** | **経路が存在しない** | — | `grep -rn "anonymous_id"` に user 再割り当てを行うコードなし。login / signup / webhook のいずれにも移行処理なし — **NOT_FOUND** |
| **explicit Save action（CTA）** | `save_concierge_thread`。未ログインなら `redirectToAuth("login")`、**ログイン済みなら何もしない**（`// 現時点では server 保存API未接続。` `:1558-1560`） | — | `ConciergeClientFull.tsx:1538-1560` — CONFIRMED |
| **save API が接続されているか** | **されていない**。保存専用エンドポイントは存在せず、保存は chat の副作用でしか起きない | — | NOT_FOUND |
| **history retrieval** | 認証済: `GET /api/concierge-threads/`（一覧、`IsAuthenticated`）＋ `GET /api/concierge-threads/<id>/`（詳細、`AllowAny` + 所有者判定）。匿名: **一覧は 401、詳細は anon cookie 一致時のみ取得可** | — | `temples/api/views/concierge.py:59,89,120-127` — CONFIRMED |
| **UI 文言と backend 挙動の一致** | **不一致**。`lib/auth/actionGuards.ts:16-21` が `save_concierge_thread` を「auth 必須」と宣言し、UI は未ログインをログインへ誘導するが、backend は既に匿名の相談を保存済み。逆にログイン済みで「保存」を押しても新たな保存は発生しない | — | CONFIRMED |

**DB 永続化 ≠ ユーザーから見た「保存」**: 現行では前者のみが実装され、後者は UI 上の概念としてしか存在しない。status: **CONFIRMED**

---

## 9. Privacy / public-profile map

### 9-1. 未認証で到達可能な profile 系エンドポイント

| endpoint | permission | 返却フィールド | 実値 | status |
| --- | --- | --- | --- | --- |
| `GET /api/profiles/<username>/` （`temples/api/urls.py:148` → `temples/api/views/public_profile.py:26`） | `AllowAny` | `username`, `nickname`, `website`, `icon_url`, `bio`, **`birthday`**, `location`, `is_public` | `website` / `icon_url` / `location` は **モデルに存在しない属性**を `getattr(..., None)` で読むため常に `None`。実際に出るのは `username` / `nickname` / `bio` / **`birthday`** / `is_public` | CONFIRMED |
| `GET /api/_debug/whoami/` （`shrine_project/urls.py:88`） | `AllowAny` | `is_authenticated`, `username`, `is_superuser` | 呼び出し元自身の情報のみ | CONFIRMED |
| `GET /api/goshuins/` （`temples/api/views/goshuin.py:28`） | `AllowAny` | 公開御朱印。`UserProfile` は含まない | — | CONFIRMED |

### 9-2. ゲートと既定値

- ゲートは `UserProfile.is_public` のみ（`public_profile.py:35-37`、非公開なら 404）。
- `is_public` の既定値は **`True`**: モデル既定（`users/models.py:12`）、signal 既定（`users/apps.py:23` `ensure_profile`）、`MeView.get` の遅延生成既定（`users/api/views.py:80-83`）の**3箇所すべてで True**。
- したがって **新規登録ユーザーは全員、既定で `birthday` が未認証公開の対象になる**（値が入力されていれば）。status: **CONFIRMED**
- `birth_time` / `birth_place` は公開エンドポイントに含まれない。status: **CONFIRMED**

### 9-3. frontend 側の断線

- `apps/web/src/lib/api/publicProfile.ts:16` は `/public/profile/<username>/` を叩く。backend の path は `/api/profiles/<username>/`、`app/api/public/` 配下に該当 BFF route も存在しない（あるのは `goshuins` と `shrines`）。加えて `apiGet` は `baseURL: "/api"` の相対 URL で、Server Component からは解決できない（`app/users/[username]/page.tsx:20` は SSR 実行）。
- 結果として `/users/<username>` は `notFound()` に落ちる。
- **frontend が断線していても backend endpoint は到達可能であり、`birthday` の未認証取得は成立する。** status: **CONFIRMED**

### 9-4. Active 契約との照合

`docs/core/runtime-security-baseline.md`（Status: Active）:
- §6 Logging Security Policy は **生年月日** を「production runtime のログへ出力してはならない」機微情報として明示列挙している。
- §7 Public Response Security Policy の禁止列挙は `_debug` / raw exception / filesystem path / DB情報 / migration状態 / secret / 相談本文 / credential-adjacent であり、**PII・生年月日を含まない**。

→ §9-1 の露出は §7 の literal violation ではない。しかし**同一フィールドが §6 では機微、public response では無制限**という非対称が存在する。§10 M5 として扱う。

---

## 10. Contract mismatches

| ID | Mismatch | Active 契約側 | Runtime 側 | status |
| --- | --- | --- | --- | --- |
| **M1** | Premium 階層の正本が2つある | `docs/product/premium-experience.md` が Free/Premium 境界を管理、`docs/product/billing-paywall.md`「判定ロジックの一元化 — 画面ごとに重複実装しない。共通の実装に集約し、画面間で判定結果が食い違わない状態を保つ」 | backend `shrine_meaning_composer.py:839-851` の `access` タグと frontend `lib/premium/cardVisibility.ts` の23カード表が独立に存在し、相互参照ゼロ。backend の宣言は誰にも読まれない | CONFIRMED |
| **M2** | backend が access 階層を宣言しながら強制しない | 同上 | `shrine_meaning.py:13` `AllowAny` + `compose_shrine_meaning_payload(shrine)` に user 引数なし | CONFIRMED |
| **M3** | Free の利用制限が「当日」ではなく「累積」 | `docs/product/billing-paywall.md`「Free ユーザーは、**当日の**利用回数が上限に達するまで利用できる」 | `FeatureUsage` に日付フィールドがなく（`models_usage.py:8-33`）、`get_used_count` が `max(累積, 当日)` を返すため（`quota_service.py:148-160`）**リセットされない**。実効は生涯5回 | CONFIRMED |
| **M4** | Premium の「保存上限拡張」が実装されていない | `docs/product/premium-experience.md`「Premium 対象にできるもの: 御朱印・訪問記録・メモの保存上限拡張」「マイページ Free: 最小限の保存・管理 / Premium: 保存上限…」 | `goshuin_limit.py::get_my_goshuin_limit(user)` は `user` を無視して 10 固定。favorite は上限なし。`QUOTA_POLICY` の該当エントリは呼び出し元ゼロ | CONFIRMED |
| **M5** | 生年月日の機微度が文書内で非対称 | `docs/core/runtime-security-baseline.md` §6 が 生年月日 をログ禁止の機微情報に列挙。§7 の public response 禁止列挙には PII が無い | `public_profile.py:44` が `is_public=True`（既定）の全ユーザーの `birthday` を未認証へ返す | CONFIRMED |
| **M6** | My Page が Premium 価値を提示していない | `docs/product/premium-experience.md`「マイページ = Premium の継続価値を見せる画面」 | `MyPageView.tsx` / `MyPageScreen.tsx` に billing / premium 参照 0件 | CONFIRMED |
| **M7** | backend 内に生年月日の canonical value が2つある | `concierge_input_contract.py:311-316` が自ら「Documented Current Gap」と申告 | `api_views_concierge.py:551` (scoring) と `:564,570-572` (direction) が別 precedence | CONFIRMED |
| **M8** | 方位計算が3実装 | `docs/core/direction-response-contract.md` / `docs/product/compass-mvp-runtime-contract.md` が方位契約を管理 | `lib/profile/derivedProfile.ts::buildDirectionProfile`(front) / `temples/domain/kyusei.py`(Concierge) / `temples/services/compass_runtime.py`(Compass) が別方式 | CONFIRMED |
| **M9** | frontend の型が live serializer と不一致 | `docs/core/authentication-flow.md` が `/api/users/me/` を live 正本と規定 | `lib/auth/types.ts::AuthUser` の top-level `nickname` / `birthday` は `UserMeSerializer`（`users/api/serializers.py:52-57`）に存在せず常に undefined。`ConciergeClientFull.tsx:529,538` がこれを読んでいる | CONFIRMED |
| **M10** | Save CTA の意味と backend 挙動の不一致 | `docs/core/auth-flow.md` が「Concierge保存…からの復帰導線」を規定（保存が認証行為である前提） | 匿名の相談も無条件で永続化済み（`api_views_concierge.py:918-947`）、ログイン済みの「保存」は no-op（`ConciergeClientFull.tsx:1558-1560`） | CONFIRMED |
| **M11** | 到達不能な `AllowAny` 実装の放置 | `docs/core/runtime-security-baseline.md` §9「到達不能（unreachable / dead code）と確認された endpoint 実装であっても、`AllowAny` のまま放置せず、再配線時に上記方針へ従わせる」 | §5-2 の A1〜A7 が未整理のまま残存 | CONFIRMED |

---

## 11. D1-D14 分類

先行audit `docs/audit/user-account-mypage-free-premium-audit.md` §7 の番号を保持する。D15-D17 は本再監査で新規に確認された事項（件数合わせのための追加ではない）。

| ID | Issue | Evidence | Category | Current State | What remains unresolved |
| --- | --- | --- | --- | --- | --- |
| **D1** | 保存 `UserProfile.birthday` を Compass に使うか | `features/compass/CompassClient.tsx:89,175`（フォームのみ）／`api_views_compass.py:54`（body から受ける）／`AuthProvider.tsx:79-101`（`/compass` でも me は取得済み） | **MOTHER_SHIP_DECISION** | 非接続。技術的前提（ログイン必須化不要・データは client 手元）は**充足済み** — `CONFIRMED` | 「毎回入力」と「保存値の任意再利用」のどちらを Compass の体験とするか |
| **D2** | Concierge の precedence（セッション入力 > 保存値）を正とするか | `buildConciergeRequestPayload.ts:66`／`ConciergeClientFull.tsx:971-972`（重複実装） | **MOTHER_SHIP_DECISION** | 現行順序は `CONFIRMED`。食い違い時の test は `NOT_FOUND` | どちらを優先するかの製品判断（＋ P3 の birthday/birthTime 分離をどう扱うか） |
| **D3** | backend の二重 precedence（方位のみ profile_context 優先）を統一するか | `concierge_input_contract.py:299-317`／`api_views_concierge.py:551,564,570-572` | **CONTRACT_MISMATCH**（M7） | 実装が自ら Gap と申告 | 統一すると既存の方位計算結果が変わる。どちらへ寄せるか |
| **D4** | Premium 境界を backend で enforce するか | §7 表全体／`api_views_concierge.py:321-374`／`shrine_meaning.py:13` | **MOTHER_SHIP_DECISION** | Premium 本文は未認証にも配信されている — `CONFIRMED`。`billing-paywall.md` の「利用可否はサーバー側」条項は quota で充足済みであり、本文フィルタは**未規定** | 本文フィルタを契約に加えるか、UI 差分のままとするか |
| **D5** | `access` タグ（backend）と `cardVisibility.ts`（frontend）のどちらを正本とするか | `shrine_meaning_composer.py:839-851`／`lib/premium/cardVisibility.ts`／`payloadV2.ts:18,89`（唯一の参照が型定義） | **CONTRACT_MISMATCH**（M1・M2） | 二重宣言・相互参照ゼロ | 正本の一本化先 |
| **D6** | `QUOTA_POLICY` の未使用エントリ（favorite / goshuin_upload / shrine_search）を実装するか削除するか | `quota_policy.py:8-26`／`grep check_quota` は1箇所／`goshuin_limit.py` | **CONTRACT_MISMATCH**（M4）＋ 残余は decision | `premium-experience.md` が保存上限拡張を Premium 対象と規定する一方、runtime は全プラン同一 | 上限値そのもの（何件を Premium にするか）は製品判断 |
| **D7** | 本番の `BILLING_PROVIDER` 実値と、stub 時に checkout / webhook / DB が一切効かない挙動 | `billing_state.py:26-28,52-58`／`billing_checkout.py:38-46`／`stripe_webhook.py:256-378`／`.env.example`（BILLING キー **不在**）／`settings.py`（同キー不在、`os.getenv` 直読み） | **FACT_VERIFICATION** | 既定 `stub` では、checkout は決済なしで success へ遷移し、webhook の DB 更新は読まれない — `CONFIRMED`。**本番実値はリポジトリに存在せず、デプロイ環境で確認する以外にない** — `UNRESOLVED` | デプロイ環境の env 実値の確認（製品判断ではない） |
| **D8** | `is_staff` を無条件 premium 扱いすることを許容するか | `billing_state.py:130-138` | **MOTHER_SHIP_DECISION** | 事実は `CONFIRMED` | 運用アカウントを計測・課金からどう扱うか |
| **D9** | My Page を専用面として維持するか | §2 全体。`/mypage` への技術的依存 0件、favorites は `/favorites` に既に独立実装あり | **MOTHER_SHIP_DECISION** | **技術的依存の有無は本再監査で決着（依存なし、`CONFIRMED`）**。先行audit で `UNRESOLVED` としていた技術面は解消 | 存廃・再配置は製品判断。加えて「プロフィール書き込みUIをどこへ置くか」が実装課題として残る |
| **D10** | 御朱印機能の扱い（凍結中） | `MyPageView.tsx:18,33-37`（UI到達不能）／`temples/api/views/goshuin.py`（backend 生存）／`users/api/urls.py`（icon 未ルーティング） | **MOTHER_SHIP_DECISION** | 状態は `CONFIRMED` | 凍結解除 / 削除 / 現状維持 |
| **D11** | 公開プロフィールで `birthday` を未認証公開してよいか。`is_public` 既定 `True` を維持するか | `public_profile.py:35-44`／`users/models.py:12`, `apps.py:23`, `api/views.py:80-83`（既定 True が3箇所）／`runtime-security-baseline.md` §6 vs §7 | **CONTRACT_MISMATCH**（M5）＋ 残余は decision | backend は公開する。frontend は path 不一致で断線中（§9-3）。**断線は露出を無効化しない** | 公開範囲の製品判断。断線の修正は公開可否を決めてから |
| **D12** | 匿名相談を無条件永続化する挙動と「保存」CTA の意味 | `api_views_concierge.py:918-947`／`ConciergeClientFull.tsx:1558-1560`／`actionGuards.ts:16-21`／claim 経路 `NOT_FOUND` | **CONTRACT_MISMATCH**（M10）＋ 残余は decision | 匿名 thread は永久に orphan。「保存」は no-op | 匿名データの保持方針、claim を実装するか、Save の product 定義 |
| **D13** | 到達不能な実装（`config/urls.py` / `users/urls.py` + `views.py` + `serializers.py` / `accounts/` / `favorites/` / `<goshuin_app>/` / `withAuth.tsx` / `app/api/me` / axios interceptor / `setCookie` / `updateMe`）を削除するか | §5-2 A1〜A12 | **FACT_VERIFICATION**（＋ M11 が整理を要求） | 全件 `CONFIRMED`。`runtime-security-baseline.md` §9 が放置を明示的に禁じている | 製品判断は不要。削除範囲と PR 分割のみ |
| **D14** | `middleware.ts` の保護対象を `/mypage` のみとするか | `apps/web/middleware.ts:8-22`（cookie の存在のみ判定） | **FACT_VERIFICATION** | 事実は `CONFIRMED`。ただし**実害は限定的** — 全ての実データは BFF → Django の `IsAuthenticated` で守られており、middleware は UX 上のリダイレクトにすぎない | 技術判断（middleware をどう位置づけるか）。製品判断ではない |
| **D15** *(new)* | Free の Concierge 上限が 5 であり、かつ日次ではなく**累積で恒久的に枯れる** | `settings.py:16`／`quota_service.py:196-198,108-170`／`models_usage.py:8-33`／`test_concierge_chat_response_matrix_contract.py:142` | **CONTRACT_MISMATCH**（M3） | `billing-paywall.md`「当日の利用回数」と runtime が不一致 | 日次リセットを実装するか、契約側を「累積」に改めるか |
| **D16** *(new)* | 匿名で 3 回使い切った後に登録すると quota がリセットされ +5 回得られる | `quota_service.py:113-134`（scope が anonymous → user で別行） | **FACT_VERIFICATION** | 事実は `CONFIRMED` | 意図された導線（登録インセンティブ）か抜け穴かの確認。仕様化するなら製品判断へ昇格 |
| ↳ | **D16 は §15 で D16-A / D16-B へ分割済み。** 上記行は分割前の記述として保持する（履歴保存） | §15 | — | — | §15 参照 |
| **D17** *(new)* | `AuthUser.nickname` / `AuthUser.birthday`（top-level）が live serializer に存在せず、表示名解決が縮退している | `users/api/serializers.py:52-57`／`lib/auth/types.ts:7-8,30-35`／`ConciergeClientFull.tsx:529,538`／`resolveDisplayName.ts` | **CONTRACT_MISMATCH**（M9） | 常に undefined、`toProfileState` は呼び出し元 0件 | serializer を合わせるか型を落とすか（実装判断） |

### 11-1. 分類サマリ

- `FACT_VERIFICATION`: **D7, D13, D14, D16**（4件）— うち D7 のみリポジトリ外（デプロイ環境）の確認を要する
- `CONTRACT_MISMATCH`: **D3, D5, D15, D17**（純粋）＋ **D6, D11, D12**（mismatch + 製品判断の残余）
- `MOTHER_SHIP_DECISION`: **D1, D2, D4, D8, D9, D10**（純粋）＋ D6 / D11 / D12 の残余

---

## 12. Mother Ship decisions only

コードからは決められず、製品判断を要するものだけを抜き出す。**本書はいずれも選択していない。**

| ID | 決めること | 決めないと動けない後続 |
| --- | --- | --- |
| D1 | Compass が保存生年月日を任意再利用するか（する場合、匿名利用は維持する前提でよいか） | Compass の入力体験、D2 の precedence 設計 |
| D2 | Concierge の生年月日 precedence（セッション入力優先 / 保存値優先）と、birthday だけ差し替わったとき birth_time 等をどう扱うか | P1・P3 の仕様化、テスト追加 |
| D4 | Premium 本文を backend でフィルタする契約を持つか、UI 差分のままとするか | D5 の正本一本化、`billing-paywall.md` の改訂要否 |
| D6-残余 | Free / Premium の保存上限（favorite / 御朱印 / 訪問記録）を何件にするか | D6 の実装、`premium-experience.md` との整合 |
| D8 | `is_staff` を premium 扱いし続けるか（計測から除外するか） | 課金 KPI の定義 |
| D9 | My Page を維持 / 分解 / 再配置のどれにするか。プロフィール書き込みUIの置き場所 | 画面設計全般 |
| D10 | 御朱印機能を解凍 / 削除 / 凍結継続のどれにするか | D6 の御朱印上限、ストレージ上限 |
| D11-残余 | 公開プロフィールで生年月日を公開するか。`is_public` 既定を True のままにするか | §9-3 の断線修正の可否 |
| D12-残余 | 匿名相談の保持期間、登録時の claim を実装するか、「保存」を何の行為として定義するか | Save CTA の再設計、D15 と併せた Free 体験の設計 |
| D15-残余 | Free の上限を日次に戻すか、累積を正として契約を改めるか。上限値 5 を維持するか | `billing-paywall.md` の改訂、課金導線の説得力 |
| D16-残余 | 登録による quota リセットを仕様とするか塞ぐか | 登録導線の設計 |

---

## 13. Recommended implementation PR boundaries（実装はしない）

依存関係の順に並べる。各 PR は独立に revert 可能な粒度を意図している。

| # | PR 境界 | 含むもの | 前提となる決定 | リスク |
| --- | --- | --- | --- | --- |
| **P0** | **環境実値の確認（コード変更なし）** | デプロイ環境の `BILLING_PROVIDER` / `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE` / `STRIPE_*` を確認し、`docs/` に記録 | なし（D7 = FACT_VERIFICATION） | なし。**他の全 billing 系 PR の前提** |
| **P1** | **dead code 除去（backend）** | `backend/config/urls.py`、`backend/users/urls.py` + `views.py` + `serializers.py`、`accounts/`、`<goshuin_app>/`、`favorites/` アプリ | D13。`users/tests/test_views_no_sensitive_logging.py` は削除対象を直接 import しているため同時に整理が要る | 低。ただし `favorites` アプリは migration を持つため schema 影響の切り分けが必要（本 PR では**削除せず INSTALLED_APPS からの扱いだけ判断**するのが安全） |
| **P2** | **dead code 除去（frontend）** | `lib/auth/withAuth.tsx`、`app/api/me/route.ts`、`lib/api/authTokens.ts::setCookie`、`lib/api/users.ts::updateMe`、`lib/api/client.ts` の Authorization interceptor（HttpOnly により常に no-op） | D13 | 低。interceptor 削除は「今も効いていない」ことの確認込みで行う |
| **P3** | **型と live serializer の整合** | `lib/auth/types.ts` の top-level `nickname` / `birthday` を削除、`ConciergeClientFull.tsx:529,538` を `user?.profile?.nickname` に寄せる、`toProfileState` の扱いを決める | D17 | 低〜中。表示名が「あなた」から実際の nickname に変わる = **ユーザーに見える挙動変化**。単独 PR にする |
| **P4** | **quota の意味の確定** | `FeatureUsage` に期間概念を入れる or `billing-paywall.md` を「累積」に改訂。`CONCIERGE_DAILY_FREE_LIMIT` の命名整理。`ConciergeUsage` との二重カウンタ解消 | **D15 の決定が必須** | 高。既存ユーザーの残回数が変わる。migration を伴う可能性 |
| **P5** | **quota policy の一本化** | `QUOTA_POLICY` の未使用エントリを実装 or 削除。`goshuin_limit.py` を plan 対応に | **D6 / D10 の決定が必須**。P4 の後 | 中 |
| **P6** | **Premium 正本の一本化** | `access` タグと `cardVisibility.ts` のどちらかへ寄せる。backend フィルタを入れるなら `compose_shrine_meaning_payload` に access 引数を追加 | **D4 / D5 の決定が必須** | 高。Premium 体験の見え方が変わる。分析イベント（`lib/analytics/cardEvents.ts` の `accessLevel`）にも波及 |
| **P7** | **公開プロフィールの露出整理** | `public_profile.py` の返却フィールドを決定に従って絞る。存在しない属性（`website` / `icon_url` / `location`）の除去。`is_public` 既定値の扱い。frontend の path 不一致（`publicProfile.ts:16`）はここで初めて修正可能 | **D11 の決定が必須** | 中。既定 True の変更は既存ユーザーへの影響あり |
| **P8** | **Save / 匿名データの再定義** | Save CTA の意味付け、`actionGuards.ts` と backend の整合、必要なら claim 実装、匿名 thread の保持ポリシー | **D12 の決定が必須**。D16 とも連動 | 高。データ移行を伴いうる |
| **P9** | **Concierge precedence の統一** | frontend の重複実装（`buildConciergeRequestPayload.ts:66` と `ConciergeClientFull.tsx:971-972`）を1本化、backend の二重 chain を統一、P1/P3/P5 のテストを追加 | **D2 / D3 の決定が必須** | 高。既存の推薦・方位結果が変わる。ゴールデンテストが要る |
| **P10** | **方位計算の正本化** | front `buildDirectionProfile` / Concierge `kyusei.py` / Compass `compass_runtime.py` の3実装の関係を確定 | D3 の後。Compass 契約（`compass-mvp-runtime-contract.md`）との調整必須 | 高 |
| **P11** | **profile 書き込みUIの再配置 / My Page の扱い** | プロフィール編集をどこへ置くか、My Page の分解 or 維持 | **D9 の決定が必須**。P3 の後 | 中〜高。**技術的ブロッカーはない**（§Main Question） |
| **P12** | **icon 経路の決着** | `POST /api/users/me/icon/` を live URLConf へ配線する or BFF route と `ProfileIconCard` ごと削除 | D9 / D10 と連動 | 低 |

**順序の要点**: P0 は他の全 billing 系より先。P1〜P3 は決定を待たずに着手できる唯一のグループ。P4 以降はすべて Mother Ship 決定待ちであり、決定前に着手すると手戻りになる。

---

## 14. UNRESOLVED 一覧

| # | 項目 | 理由 |
| --- | --- | --- |
| U1 | 本番環境の `BILLING_PROVIDER` / `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE` / `STRIPE_SECRET_KEY` / `STRIPE_PREMIUM_PRICE_ID` | いずれもリポジトリ内に存在しない（`.env.example` にキーごと不在、`settings.py` でも `os.getenv` 直読み）。**リポジトリから推測してはならない**ため、デプロイ環境での確認が必要（D7 / P0）<br>**［訂正: §16-1］** 「`.env.example` にキーごと不在」は**ルートの `.env.example` についてのみ正しい**。`backend/.env.example` には `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE` / `STRIPE_*` のキーが存在する（値は空またはローカル用）。結論（本番値は UNRESOLVED_EXTERNAL）は変わらない |
| U2 | Concierge の precedence 食い違い時（P1）および birthday/birthTime 分離（P3）の実挙動 | コード上の順序は `CONFIRMED` だが、該当 test が存在せず、実行検証もしていない |
| U3 | 本書が引用した全 test の pass/fail | テスト環境未構築（`node_modules` 未インストール、Django 未インストール）。assertion の存在のみ確認済み |
| U4 | `backend/favorites/` アプリの migration が本番 DB に適用済みか | `INSTALLED_APPS` にあるため適用されている可能性が高いが、DB 実体は未確認。P1 の削除範囲判断に影響 |

---

## 15. D16 Classification

> 追記日: 2026-09-04（同 commit `f9ff610` の runtime code に対する再確認）。
> §11 の D16 行は分割前の記述として保持している（silent rewrite を避けるため削除していない）。

### 15-1. D16-A — FACT_VERIFICATION

**Question**: 匿名の利用実績は、signup 後も登録ユーザーの利用実績と分離されたままか。

**Status: CONFIRMED**

| 検証項目 | 実装 | 結果 |
| --- | --- | --- |
| 匿名の usage identifier | `backend/temples/services/anonymous_id.py` — cookie `concierge_anon_id`（`ANONYMOUS_ID_COOKIE_NAME:16`）に `django.core.signing` で署名した UUID（`issue_anonymous_id:53`）。`plan_service.py::resolve_plan_context:40-48` が `PlanContext(plan="anonymous", user_id=None, anon_id=…)` を組む | `FeatureUsage.anon_id`（文字列） |
| 認証済みの usage identifier | `plan_service.py:25-38` が `PlanContext(plan="premium"\|"free", user_id=user.id, anon_id=None)` を組む | `FeatureUsage.user_id`（FK） |
| storage model | `backend/temples/models_usage.py::FeatureUsage:8-52` — `scope`(`"anonymous"`/`"user"`), `user`(FK, null可), `anon_id`(CharField), `feature`, `count`。**日付フィールドなし**。UniqueConstraint は `(user, feature) where scope="user"` と `(anon_id, feature) where scope="anonymous"` の**2本が独立** | 匿名行と user 行は別レコード |
| lookup logic | `backend/temples/services/quota_service.py::get_used_count:108-146` — `plan_context.plan == "anonymous"` なら `get_or_create(scope="anonymous", anon_id=…, feature=…)`、それ以外は `get_or_create(scope="user", user_id=…, feature=…)`。**anon_id を user 行へ持ち込む分岐は存在しない** | 完全分離 |
| write logic | `quota_service.py::consume_quota:224-262` — 同じ2分岐で `count += 1` | 同上 |
| signup flow | `backend/users/api/views.py::SignupView.post:108-123` → `SignupSerializer.create`（`users/api/serializers.py:20-26`）→ `User.objects.create_user()` のみ。**quota / FeatureUsage / anon_id に一切触れない**。副作用は `users/apps.py::ensure_profile:19-23`（`UserProfile` を作るだけ） | usage 移行なし |
| BFF signup | `apps/web/src/app/api/auth/register/route.ts` — body を `/api/users/signup/` へ転送するだけ。cookie 操作なし。`concierge_anon_id` の削除・転送・読み取りいずれもなし | usage 移行なし |
| migration / claim code の探索 | `grep -rniE "anon.*(migrat\|transfer\|merge\|claim\|reconcil\|adopt\|inherit\|takeover)\|…" --include=*.py backend/`（`/migrations/` 除外）→ **該当0件**。`FeatureUsage` の全参照は `quota_service.py` / `models_usage.py` / `models.py:13` のみ。login / signup / webhook のいずれにも移行処理なし | **NOT_FOUND** |
| frontend 側の関連処理 | `ConciergeClientFull.tsx::clearAnonymousSnapshot:251-257` は `sessionStorage` のキー1つを消すだけで、`concierge_anon_id` cookie（HttpOnly）にも DB にも触れない | usage 移行なし |

**帰結**: 匿名で上限（`QUOTA_POLICY["anonymous"]["concierge"]["limit"] = 3`、`quota_policy.py:9`）に達した後に登録すると、`PlanContext.plan` が `anonymous` → `free` に変わり、`get_used_count` の参照先が `FeatureUsage(scope="anonymous", anon_id=…)` から `FeatureUsage(scope="user", user_id=…)` の**新規行（count=0）**へ切り替わる。結果として `settings.CONCIERGE_DAILY_FREE_LIMIT = 5`（`shrine_project/settings.py:16`、`quota_service.py:196-198`）の枠が丸ごと新規に付与される。

**test 状況**: 匿名→登録の usage 継続／リセットを assert するテストは **NOT_FOUND**（`grep -rl "check_quota\|quota" backend/temples/tests backend/tests` の該当ファイルに signup を跨ぐケースなし）。個別の quota 挙動は `temples/tests/api/test_concierge_rate_limit_message_contract.py` / `test_concierge_chat_response_matrix_contract.py:142` が扱うが、いずれも単一 scope 内。**本項の CONFIRMED は静的トレースに基づく（テスト未実行、`CONFIRMED (static)`）。**

### 15-2. D16-B — MOTHER_SHIP_DECISION

D16-A が CONFIRMED であるため、以下の製品判断が未解決として残る。**本書は A / B のいずれも選択しない。**

> **未解決の製品判断（D16-B）**
>
> 匿名利用者が登録した時点で、それまでの匿名利用実績を
>
> **A. 意図的にリセットする**（登録インセンティブとして扱い、登録直後に Free 枠を満額付与する）
>
> **B. 認証済みユーザーの利用実績へ引き継ぐ**（匿名分を合算し、登録によって上限が回復しないようにする）
>
> のいずれとして扱うか。

決定に伴って波及する範囲（決定そのものではなく、影響先の記録）:

- A を採る場合 — 現行実装が既に A の挙動であるため**コード変更は不要**。ただし「意図した仕様」であることを `docs/product/billing-paywall.md` 側へ明記する必要がある（現状は仕様記述がなく、実装だけが存在する）。加えて D15（Free 上限が日次ではなく累積である件、M3）との整合が必要 — 累積のままだと「登録で1回だけ枠が回復し、その後は恒久的に枯れる」という体験になる。
- B を採る場合 — `consume_quota` / `get_used_count` の外側に移行処理が必要になり、`concierge_anon_id` cookie（HttpOnly、`sameSite=None`、90日、`anonymous_id.py:72-83`）を signup 応答時に読める経路の設計が要る。現行の signup は BFF `app/api/auth/register/route.ts` が cookie を扱わないため、**BFF と backend の双方に新規責務が発生する**。
- いずれの場合も D12（匿名 `ConciergeThread` の claim 経路が存在しない）と設計が連動する。usage だけ引き継いで履歴を引き継がない／その逆は、ユーザーから見て一貫しない。

---

## 16. Production Billing Environment Gate

### 16-1. 先行記述の訂正（履歴保存）

| 訂正 | 先行記述（§14 U1 / §11 D7） | 実際 | 結論への影響 |
| --- | --- | --- | --- |
| E1 | 「`.env.example` にキーごと不在」 | **ルート `/.env.example`** には確かに BILLING / STRIPE キーが存在しない。しかし **`backend/.env.example` には存在する** — `BILLING_STUB_PLAN=free`（`:34`）、`BILLING_STUB_ACTIVE=0`（`:35`）、`STRIPE_SECRET_KEY=` / `STRIPE_PRICE_ID=` / `STRIPE_WEBHOOK_SECRET=`（`:38-40`、いずれも空値）。ただし **`BILLING_PROVIDER` はどちらの `.env.example` にも存在しない** | **なし**。`.env.example` は本番値の証拠として採用できない（本監査の検証ルール）。本番値は依然 `UNRESOLVED_EXTERNAL` |
| E2 | 「`settings.py` でも `os.getenv` 直読み」（BILLING 系） | 正確には **`settings.py` に `BILLING_*` の定義は一切なく**、`billing_state.py` が `os.getenv` を直接呼ぶ。一方 `STRIPE_*` は `settings.py:384-388` に定義がある | なし（記述の精密化のみ） |

### 16-2. Provider 解決パス（repository verification）

**fallback / default を決定する唯一の symbol**:

```
backend/temples/services/billing_state.py:26-28

    def provider() -> str:
        p = (os.getenv("BILLING_PROVIDER", "stub") or "stub").strip().lower()
        return p if p in PROVIDER_CHOICES else "unknown"
```

- setting 名: `BILLING_PROVIDER`（環境変数のみ。Django settings には**存在しない**）
- **repository default: `"stub"`** — `os.getenv` の第2引数、かつ空文字列も `or "stub"` で `"stub"` に落ちる
- 許容値: `PROVIDER_CHOICES = ("stub", "stripe", "revenuecat", "unknown")`（`billing_state.py:13`）。**リストにない値（打ち間違い含む）は `"unknown"` に縮退し、エラーにならない**

**stub 挙動**: `billing_state.py::_status_from_stub_env:85-122`
- `BILLING_STUB_PLAN`（既定 `"free"`）／`BILLING_STUB_ACTIVE`（既定 `"0"`、真値集合 `{1,true,yes,y,on}`）を正本とする
- `:101` — `plan=="premium"` かつ `BILLING_STUB_ACTIVE` が**未設定**（`"0"` ではなく `None`）なら `active=True` に強制
- `:106-108` — `plan=="premium"` かつ `prov=="stub"` のとき、返す `provider` を `"stripe"` に**書き換える**。`backend/README.md`「`provider` は表示・デバッグ用途とし、UI分岐の根拠には使用しません」により機能影響はないが、レスポンスは実態と異なる provider 名を返す
- **stub 判定は user 引数を見ない**（`get_billing_status:56-58`）。認証済みでも `UserProfile` を読まない
- **stub plan は全ユーザー共通のグローバル値**。個別ユーザーの premium 化はできない

**non-stub 挙動**: `billing_state.py::get_billing_status:59-83`
- `prov != "stub"` かつ user が authenticated → `UserProfile.subscription_status` / `current_period_end` を読み、`users/services/billing.py::is_subscription_active:12-28` で判定（`current_period_end` があれば期限優先、無ければ `status in {"active","trialing"}`）
- 未認証 → `_status_from_stub_env`（`:82`）

**checkout の provider 選択**: `backend/temples/services/billing_checkout.py::create_checkout_session:38-46`
- 条件は `provider() != "stripe"` → stub セッション（`session_id = f"stub_checkout_{user.pk}"`、`checkout_url = success_url + ?checkout_session_id=...`）を返し、**Stripe を呼ばず決済なしで success へ遷移させる**
- `"stripe"` のときのみ `STRIPE_SECRET_KEY` + `STRIPE_PREMIUM_PRICE_ID`(または `STRIPE_PRICE_ID`) を要求し、欠落なら `RuntimeError("stripe checkout is not configured")` → `CheckoutUnavailable`(503)（`temples/api/views/billing.py:28-31, 105-106`）

**⚠ status と checkout の分岐条件が非対称**: status は `prov == "stub"` で分岐、checkout は `prov != "stripe"` で分岐する。したがって `BILLING_PROVIDER=revenuecat` または打ち間違いによる `"unknown"` では、**認証済みユーザーの status は DB を読む一方、checkout は決済なしの stub 成功を返す**。status: **CONFIRMED**

**webhook 挙動**: `temples/api/views/billing.py::BillingStripeWebhookView:120-146`
- `permission_classes = [AllowAny]`, `authentication_classes = []`, `csrf_exempt`
- **`provider()` を参照しない**。`STRIPE_WEBHOOK_SECRET` と `stripe` SDK があれば署名検証し（`users/services/stripe_webhook.py::construct_stripe_event:58-88`、未設定なら 503）、`apply_stripe_event` が `UserProfile` を更新する
- → **`BILLING_PROVIDER=stub` のままでも webhook は `UserProfile` を書き込む。その値は `get_billing_status` に読まれない**（書き込み先と読み取り元が切断される）。status: **CONFIRMED**

**UserProfile billing フィールド**: `backend/users/models.py:22-32` — `stripe_customer_id`(webhook 書き / checkout 読み) / `stripe_subscription_id`(write-only) / `stripe_price_id`(write-only) / `subscription_status`(webhook 書き、non-stub 時のみ読み) / `current_period_end`(同左)。いずれも API serializer に非収載（§1 参照）

**環境ドキュメント**: `backend/README.md:113-131`「Billing運用契約」が `BILLING_PROVIDER=stub` → 環境変数が正本、`=stripe` → `UserProfile` が正本と規定。**runtime と一致している**（mismatch なし）。`docs/infra/env_policy.md`（Status: Active）は「実際の環境変数定義および既定値は `backend/.env.example` を正本とする」と述べるが、**本番実値は同書にも記載がない**

**Stripe 依存**: `backend/requirements.txt:17` `stripe>=15.3.1,<16.0.0` — SDK は本番にインストールされている（`StripeWebhookNotConfigured("stripe sdk is not installed")` 経路には落ちない）。status: **CONFIRMED**

### 16-3. 本番値の検証

**`PRODUCTION_VALUE = UNRESOLVED_EXTERNAL`**

リポジトリに本番環境の設定ソースが存在しないことを確認した:

| 探索対象 | 結果 |
| --- | --- |
| `render.yaml` / `render.yml` / `Procfile` / `fly.toml` / `app.yaml` | **存在しない**（`find` 実行、`.git` 除外） |
| `backend/start.sh`（Render の起動スクリプト、`docs/infra/render-startup.md` が参照） | `PORT` / `WEB_CONCURRENCY` を export するのみ。**`BILLING_*` / `STRIPE_*` を設定しない** |
| `.github/workflows/`（`deploy.yml.disabled` 含む） | `BILLING` / `STRIPE` の記述 **0件** |
| `infra/README.md` | Render の Environment に設定すべき変数として `DATABASE_URL` / `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` 等を列挙するのみ。**BILLING 系の記載なし** |
| リポジトリ内の `BILLING_*` 出現箇所 | `Makefile:12`（ローカル dev target）、`backend/pytest.ini:29-30`（テスト）、`backend/.env.example:34-35`（ローカル例）、`backend/README.md`（仕様説明）、`billing_state.py`（実装）、各 test の `monkeypatch.setenv`。**いずれも本番設定ソースではない** |
| 本監査セッションのコンテナ環境変数 | `BILLING_PROVIDER` / `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE` / `BILLING_STUB_CANCEL_AT_PERIOD_END` / `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_ID` / `STRIPE_PREMIUM_PRICE_ID` すべて **ABSENT**、かつ `RENDER` / `RENDER_SERVICE_ID` も **ABSENT** → **本監査環境は本番環境ではない**。値の代替根拠にはならない |

検証ルールに従い、default・`.env.example`・ローカル `.env`・テスト・README 例・デプロイ手順書のいずれも本番値の根拠として採用していない。

#### 外部で確認すべき事項（Render Dashboard → Web Service → Environment）

| キー | 必要性 | 確認内容（**値そのものは記録しない。present / absent / 実配置値の分類のみ**） |
| --- | --- | --- |
| **`BILLING_PROVIDER`** | **必須** | 未設定か、`stub` / `stripe` / `revenuecat` / その他（→ `unknown` に縮退）か。provider 解決の唯一の入力 |
| `BILLING_STUB_PLAN` | provider が `stub` に解決される場合のみ意味を持つ | `free` / `premium` / 未設定。`premium` なら**全ユーザーが premium** になる |
| `BILLING_STUB_ACTIVE` | 同上 | `0` / 真値 / **未設定**。`BILLING_STUB_PLAN=premium` かつ**未設定**だと `active=True` に強制される（`billing_state.py:101`）ため、`0` と未設定の区別が必要 |
| `BILLING_STUB_CANCEL_AT_PERIOD_END` | stub 時の表示のみ。機能影響なし | present / absent |
| `STRIPE_SECRET_KEY` | provider が `stripe` の場合、checkout 成立に必須 | **present / absent のみ** |
| `STRIPE_PREMIUM_PRICE_ID` または `STRIPE_PRICE_ID` | 同上（`settings.py:387` で前者優先、無ければ後者） | **present / absent のみ** |
| `STRIPE_WEBHOOK_SECRET` | provider を問わず webhook 受信に必須（`construct_stripe_event`）。未設定なら webhook は 503 | **present / absent のみ** |

**秘匿値は出力しない。** 上表は present / absent の分類のみを記録する運用とする。

### 16-4. Production Billing Matrix

現行コードのみに基づく。`user` は認証済みユーザーを指す。

| Condition | Billing status source | Checkout behavior | DB UserProfile used? |
| --- | --- | --- | --- |
| **provider = stub**（`BILLING_PROVIDER=stub`、または空文字列） | `BILLING_STUB_PLAN` / `BILLING_STUB_ACTIVE`（環境変数）。**認証済みでも user を見ない**（`billing_state.py:56-58`）。全ユーザー共通のグローバル値 | **Stripe を呼ばない**。`session_id="stub_checkout_<pk>"` と `success_url?checkout_session_id=…` を返し、決済なしで `/billing/success` へ遷移（`billing_checkout.py:40-46`） | **No**（status 判定では未使用）。ただし webhook が届けば `UserProfile` は**書き込まれる**（読まれない） |
| **provider = stripe**（production provider） | 認証済み: `UserProfile.subscription_status` + `current_period_end` → `is_subscription_active`（`billing_state.py:59-80`）／未認証: stub env（`:82`） | `STRIPE_SECRET_KEY` + price id 必須。欠落時 503（`CheckoutUnavailable`）。揃っていれば `stripe.checkout.Session.create`（mode=`subscription`、`client_reference_id=user.pk`、`metadata.user_id`）→ 実 checkout URL | **Yes**（認証済みの場合） |
| **provider unset**（`BILLING_PROVIDER` 未設定） | **`provider()` が `"stub"` を返す**（`os.getenv("BILLING_PROVIDER","stub")`）→ 1行目と完全に同一 | 1行目と同一（stub 短絡） | 1行目と同一（**No**） |
| *(参考)* **provider = revenuecat / 未知の値（→ `"unknown"`）** | 認証済み: `UserProfile` を読む（2行目と同じ経路）／未認証: stub env | **stub 短絡**（`provider() != "stripe"` のため）。決済なしで success へ遷移 | **Yes**（認証済みの場合）。**status と checkout の分岐が非対称**（§16-2） |

いずれの行でも `is_premium_for_user`（`billing_state.py:130-138`）は `user.is_staff` を無条件に premium とする（D8）。

### 16-5. 後続 Billing 作業への影響

- **P0（環境実値の確認）は依然として未完了。** `BILLING_PROVIDER` が `stub` に解決される限り、checkout → webhook → `UserProfile` → plan 判定のループは閉じておらず、**Premium は製品フロー上で到達不能**（`is_staff` と `BILLING_STUB_PLAN=premium` を除く）。
- D7 の分類は **FACT_VERIFICATION のまま変更なし**。ただし「リポジトリ内に手がかりが一切ない」から「**リポジトリ内には仕様（`backend/README.md`）と実装（`billing_state.py`）が揃っており、欠けているのは本番の env 実値のみ**」へ、記述の精度を上げた（§16-1 E1 / E2）。
- P4（quota の意味の確定）、P5（quota policy 一本化）、P6（Premium 正本一本化）、P11（My Page 再配置）は、いずれも P0 の結果に依存しない**が**、P6 の「backend フィルタを入れるか」は Premium が実際に到達可能かどうか（= P0）を前提とするため、**P0 → P6 の順序は維持する**。
- 本節の確認によってアプリケーション挙動は一切変更していない。missing な本番設定を補うためのコード変更も行っていない。
