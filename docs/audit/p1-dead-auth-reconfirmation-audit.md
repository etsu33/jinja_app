# P1 Dead Auth Reconfirmation Audit

> **Status: Audit / Historical（`develop` = `324250bfc00552bc6a115faba46760ba8bd379cc`、2026-09-04）**
>
> 証拠収集のみ。**削除・修正・refactor・URL変更・settings変更・serializer変更・frontend変更・test書き換え・挙動変更のいずれも行っていない。**
> P2 / P3（AuthUser contract）とは結合していない。Billing / Quota / My Page / Compass / Concierge の挙動には触れていない。
> 判定は runtime routing / import / app configuration のみを根拠とし、**ファイル名・ディレクトリ名から liveness を推定していない。**

---

## 0. Start State

| 項目 | 値 |
| --- | --- |
| 監査対象 commit（`develop`） | **`324250bfc00552bc6a115faba46760ba8bd379cc`** |
| 対象 commit の件名 | `chore: 到達不能な旧認証実装を削除 (#2698)` |
| `develop` == `origin/develop` | **MATCH**（`git rev-parse` 一致を確認） |
| 監査時の作業ブランチ | `claude/user-account-audit-3fuyxt`（`origin/develop` へ rebase 済み。差分は `docs/` の3ファイルのみ、`git diff --name-only origin/develop HEAD` で確認） |
| working tree | **clean**（`git status --short` 空） |
| 直前の2 commit | `3cbb5379` / `996a9bf8` |

**注意（clone 深度）**: 監査開始時点のローカル clone は shallow（52 commits、`.git/shallow` あり）で、全ファイルが `4d7685f`(2026-08-30) の 2023-file commit を「初出」と報告していた。§7 の履歴調査のために `git fetch --unshallow origin` を実行し、**3669 commits の完全履歴**を取得した（read-only 操作、作業ツリー変更なし）。以降の履歴記述はすべて unshallow 後の実データに基づく。

### 0-1. 先行監査からの重大な変化

**先行監査（`docs/audit/userprofile-mypage-decision-gate-audit.md` §5-2、対象 `996a9bf`）が挙げた P1 候補のうち5件は、本監査対象の HEAD commit `324250b` (#2698) で既に削除済みである。**

`git show --stat 324250b`:

| 削除されたファイル | 行数 | 先行監査の候補ID |
| --- | ---: | --- |
| `backend/config/urls.py` | −15 | A1 |
| `backend/users/urls.py` | −17 | A2 |
| `backend/users/views.py` | −101 | A2 |
| `backend/users/serializers.py` | −120 | A3 |
| `backend/users/tests/test_views_no_sensitive_logging.py` | −88 | （A2 に付随するテスト） |
| **計** | **−341** | |

→ **先行監査の A1 / A2 / A3 は本監査時点で「候補」ではなく「完了済み」。** 本書はその事実を記録し、**残余候補のみ**を再分類する。

---

## 1. ROOT_URLCONF

### 1-1. 実効 Django settings

| entry point | 設定値 |
| --- | --- |
| `backend/manage.py:9` | `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")` |
| `backend/shrine_project/wsgi.py:14` | 同上 |
| `backend/asgi.py:14` | 同上 |
| `backend/pytest.ini:2` / `pytest.ini:2` / `apps/web/pytest.ini:2` | `DJANGO_SETTINGS_MODULE = shrine_project.settings` |
| `scripts/django.sh:4` | `export DJANGO_SETTINGS_MODULE=shrine_project.settings` |
| `backend/scripts/check_reverse.py:5` | 同上 |

`backend/shrine_project/` の内容は `__init__.py / cache_keys.py / context_processors.py / settings.py / storage_backends.py / urls.py / views.py / wsgi.py` のみ。**代替 settings モジュール（`settings_prod.py` 等）は存在しない。** status: **CONFIRMED**

### 1-2. 実効 ROOT_URLCONF

```
backend/shrine_project/settings.py:299
    ROOT_URLCONF = "shrine_project.urls"
```

status: **CONFIRMED**

### 1-3. root から到達可能な include() の全件

`backend/shrine_project/urls.py` の `include()` は **2件のみ**:

| 行 | include | 対象モジュール |
| --- | --- | --- |
| `:86` | `path("api/", include(("users.api.urls", "users"), namespace="users_api"))` | `backend/users/api/urls.py` |
| `:87` | `path("api/", include(("temples.api.urls", "temples"), namespace="temples"))` | `backend/temples/api/urls.py` |

`temples/api/urls.py` 内の include は `:167` の `path("", include(router.urls))`（DRF router、外部モジュールを取り込まない）のみ。

その他の root エントリは直付け（`include` なし）: `:85` `api/users/me/`、`:88` `api/concierge/plan/`、`:89` `api/_debug/whoami/`、`:91-93` JWT 3件、`:109-118` schema 系、`:121` `api/shrine-submissions/`、`:126-128` media。

### 1-4. backend 内の全 URL モジュールと到達可否

`find backend -name "urls.py" -o -name "api_urls.py"` の全件:

| モジュール | ROOT から到達可能か | 根拠 |
| --- | --- | --- |
| `backend/shrine_project/urls.py` | — （ROOT 本体） | `ROOT_URLCONF` |
| `backend/users/api/urls.py` | **YES** | `shrine_project/urls.py:86` |
| `backend/temples/api/urls.py` | **YES** | `shrine_project/urls.py:87` |
| `backend/favorites/urls.py` | **NO** | include 元 0件（§5-2） |
| `backend/temples/api_urls.py` | **NO** | include 元 0件。中身は `from temples.api.urls import urlpatterns` の互換エイリアス |
| `backend/temples/urls.py` | **NO** | include 元 0件 |
| `backend/config/urls.py` | **存在しない**（#2698 で削除） | `ls backend/config` → No such file or directory |
| `backend/users/urls.py` | **存在しない**（#2698 で削除） | `ls backend/users` に無し |

**「別の同名モジュールが active だから dead」という推定は行っていない。** 上表は各モジュールについて include 元を個別に grep した結果である。

---

## 2. Active User API

`/api/users/me/` の live chain（`324250b` 時点）:

```
ROOT_URLCONF = shrine_project.urls
  └─ shrine_project/urls.py:85   path("api/users/me/", ApiMeView.as_view(), name="users-me")
        ↑ import: shrine_project/urls.py:26  from users.api.views import MeView as ApiMeView
  （重複登録）
  └─ shrine_project/urls.py:86   include(("users.api.urls","users"), namespace="users_api")
        └─ users/api/urls.py:5   path("users/me/", views.MeView.as_view(), name="me")
```

| 項目 | 値 |
| --- | --- |
| root include | `shrine_project/urls.py:86`（および `:85` の直付け。**同一 view class が2経路で登録されている**） |
| 中間 URL モジュール | `backend/users/api/urls.py` |
| endpoint path | `/api/users/me/`（`users/tests/test_smoke_me.py:6` が `reverse("users_api:me") == "/api/users/me/"` を assert） |
| live view | `backend/users/api/views.py::MeView`（`APIView`、`get` / `patch`） |
| live serializer | read: `UserMeSerializer` ／ write: `UserProfileUpdateSerializer`（いずれも `backend/users/api/serializers.py`。同ファイルのクラスは `SignupSerializer` / `UserProfileSerializer` / `UserMeSerializer` / `UserProfileUpdateSerializer` の4つ） |
| authentication class | `[JWTAuthentication]`（`users/api/views.py:70`） |
| permission class | `[IsAuthenticated]`（`users/api/views.py:71`） |
| parser classes | `[JSONParser, MultiPartParser, FormParser]`（`:72`） |

**結論: live chain は依然として `users/api/views.py::MeView` に解決する。develop 上で変更されていない。** status: **CONFIRMED**

`users/api/urls.py` の他エントリ: `users/me/storage/`(`MeStorageView`)、`users/signup/`(`SignupView`)、`stripe/webhook/`(`stripe_webhook`)。

---

## 3. Signup / Login Runtime Paths

| Concern | Browser | Next.js BFF | Django URL | View | Serializer |
| --- | --- | --- | --- | --- | --- |
| **signup / register** | `app/signup/SignupForm.tsx` → `lib/api/auth.ts::signup`（fetch） | `app/api/auth/register/route.ts`（`djFetch` を使わず `BACKEND_BASE_URL` へ直 fetch） | `POST /api/users/signup/`（`users/api/urls.py:7`） | `users/api/views.py::SignupView`（`AllowAny`） | `SignupSerializer`（`users/api/serializers.py:12-26`） |
| **login** | `app/login/LoginForm.tsx` → `lib/api/auth.ts::login` | `app/api/auth/login/route.ts` → `djFetch("/api/auth/jwt/create/")`、`access_token` / `refresh_token` を HttpOnly Cookie へ | `POST /api/auth/jwt/create/`（`shrine_project/urls.py:91`） | SimpleJWT `TokenObtainPairView` | SimpleJWT 既定 |
| **refresh** | （明示的な client 呼び出しなし） | `lib/server/bffFetch.ts::refreshAccessViaBackend` が `/api/auth/jwt/refresh/` を呼ぶ（事前 refresh + 401/403 時の再試行）。`app/api/concierge/chat/route.ts` も独自に refresh する | `POST /api/auth/jwt/refresh/`（`shrine_project/urls.py:92`） | SimpleJWT `TokenRefreshView` | SimpleJWT 既定 |
| **logout** | `AuthProvider.logout` → `POST /api/auth/logout` | `app/api/auth/logout/route.ts` — **Cookie を削除するだけで Django を呼ばない** | （なし） | （なし） | （なし） |
| **`/api/users/me/`** | `lib/auth/AuthProvider.tsx::fetchMe`（GET）／`lib/api/users.ts::updateUser`（PATCH） | `app/api/users/me/route.ts` → `bffFetchWithAuthFromReq` | `GET\|PATCH /api/users/me/` | `users/api/views.py::MeView` | `UserMeSerializer` / `UserProfileUpdateSerializer` |
| *(verify)* | — | — | `POST /api/auth/jwt/verify/`（`shrine_project/urls.py:93`） | SimpleJWT `TokenVerifyView` | — |

frontend の route ディレクトリは develop 上でも `app/api/auth/{login,logout,register}`、`app/api/users/me`（+`icon`）、`app/api/me`、`app/{login,signup,auth/login,auth/register}` が存在する（`ls` で確認）。**本監査では frontend を変更していない。**

---

## 4. INSTALLED_APPS

`backend/shrine_project/settings.py:227-248`（実効値）:

```
django.contrib.{admin,auth,contenttypes,sessions,messages,staticfiles,postgres}
django_filters, rest_framework, rest_framework_simplejwt,
rest_framework_simplejwt.token_blacklist, corsheaders, drf_spectacular,
users, favorites, temples.apps.TemplesConfig, storages
```

読み込み後の変更は `:252-261` のみで、`django.contrib.gis` の挿入／削除だけ（`USE_GIS` に依存）。**auth / profile 系アプリを条件付きで追加・削除する分岐は存在しない。**

| アプリ | INSTALLED_APPS | 判定 |
| --- | --- | --- |
| `users` | **あり** | LIVE |
| `favorites` | **あり** | **INSTALLED**（§8 / §9 参照。routing は dead だが app 登録は live） |
| `temples.apps.TemplesConfig` | あり | LIVE |
| `accounts` | **なし** | 未登録 |
| `<goshuin_app>`（`backend/<goshuin_app>/`） | **なし** | 未登録 |

### 4-1. `accounts` — 未登録に加えて直接 import があるか

**直接 import は 0件。** リポジトリ全体の `.py` を grep した結果、`accounts` に言及するのは以下のみ:

| 参照 | 種別 | 判定 |
| --- | --- | --- |
| `accounts/views.py:11,46` (`template_name="accounts/register.html"` 等) | **self-reference** | 生存の根拠にならない |
| `accounts/apps.py:6` (`name = "accounts"`) | **self-reference** | 同上 |
| `accounts/urls.py:1,18` | **self-reference / コメント** | 同上 |
| `backend/users/migrations/0001_initial.py:77` | Django 標準 `is_active` の **help_text 英文**（"instead of deleting accounts"） | 無関係 |
| `backend/temples/tests/test_route_view.py:19` | `self.assertIn("/accounts/login/", resp["Location"])` | **要注意。§4-2 参照** |

**`settings.py` / `.coveragerc` / `pytest.ini` に `accounts` の記述は 0件**（grep 実行済み）。

### 4-2. `/accounts/login/` は `accounts` アプリの証拠ではない

`backend/shrine_project/settings.py` に **`LOGIN_URL` の定義がない** → Django の既定値 `"/accounts/login/"` が使われる。

- `backend/temples/api/views/route.py:187` の `@method_decorator(login_required)` は **live な endpoint**（`temples/api/urls.py` の `shrines/<int:pk>/route/`）に付いており、未認証時に `/accounts/login/?next=…` へリダイレクトする。
- `backend/temples/tests/test_route_view.py:16-21` はそのリダイレクト先文字列を assert している。
- しかし `accounts.urls` は ROOT から include されていないため、**`/accounts/login/` はどの URL パターンにも解決しない（404 になる）**。
- **`accounts` アプリを削除しても `LOGIN_URL` 既定値は変わらず、このテストの挙動も変わらない。** 逆に、このテストの存在は `accounts` アプリが live である証拠には**ならない**。

status: **CONFIRMED**

### 4-3. `accounts` のテンプレート探索可否

`settings.py:282` `"DIRS": [BASE_DIR / "templates"]`、`BASE_DIR = Path(settings.py).resolve().parent.parent` = **`backend/`**。`backend/templates/` は**存在しない**（`ls` で確認）。`APP_DIRS: True` は installed app の `templates/` のみを見る。

→ リポジトリ root の `templates/accounts/*`（8ファイル）と `templates/registration/login.html` は、**DIRS にも APP_DIRS にも載らず、テンプレート探索路上に存在しない。** status: **CONFIRMED**

### 4-4. `accounts` のスキーマ影響

`accounts/models.py` は `# Create your models here.` の1行のみ。`accounts/migrations/` は `__init__.py` のみ。**DB テーブルを持たない** → 削除しても migration は不要。status: **CONFIRMED**

---

## 5. Import / Reference Search

参照の種別を分離して記録する。**docs での言及は liveness の根拠にしない。**

### 5-1. `backend/users/views_me.py`（先行監査が見落としていた新規候補）

内容: `@api_view(["GET"]) @permission_classes([IsAuthenticated]) def me(request)` — `id` / `username` / `email` を返す。

| 探索 | 結果 |
| --- | --- |
| リポジトリ全体の `views_me` 参照 | **2件のみ**: `.coveragerc:28`（`backend/temples/views_me.py`）、`.coveragerc:30`（`backend/users/views_me.py`） — いずれも**カバレッジ除外設定**であって runtime consumer ではない |
| import | **0件**（`users.views_me` / `from .views_me` の grep で現行ツリーにヒットなし） |
| URL 登録 | **0件** |
| tests | **0件** |
| management commands / scripts | **0件** |
| migrations | 無関係 |

**#2698 は `users/urls.py` / `views.py` / `serializers.py` を削除したが、`views_me.py` を残した。** 唯一の routing だった `backend/users/urls.py` が削除されたため、現在は完全に orphan。status: **CONFIRMED_DEAD**

### 5-2. `backend/favorites/`（アプリ）

| 探索 | 結果 | 種別 |
| --- | --- | --- |
| `settings.py:245` `"favorites"` | INSTALLED_APPS に登録 | **runtime（app registry / migrations）** |
| `settings.py:325` `"favorites": "30/min"` | DRF throttle scope 名 | **文字列一致のみ**。実際に `throttle_scope = "favorites"` を使うのは `backend/temples/api/views/favorite.py:26,53,86`（temples 側）であり、`favorites` アプリとは無関係 |
| `backend/shrine_project/views.py:13` `"favorites": "/api/favorites/"` | index view が返す JSON のリンク集 | **文字列のみ** |
| `favorites/urls.py` の include 元 | **0件** | dead routing |
| `favorites/views.py::FavoriteViewSet` の import 元 | `favorites/urls.py:3` のみ（= self-reference chain） | dead |
| `favorites/permissions.py::IsOwnerOrReadOnly` の import 元 | `backend/temples/tests/test_favorites_permissions.py:7` | **test-only consumer** |
| `favorites/models.py::Favorite` の import 元 | `favorites/views.py`, `favorites/serializers.py`（self-reference chain）のみ | dead code だが **DB テーブルは存在**（`favorites/migrations/` あり、INSTALLED_APPS 登録済み） |
| live な favorites API | `temples/api/urls.py:53,102` → `temples.api_views.FavoriteViewSet`（別実装） | **LIVE** |
| related_name 衝突 | なし（`favorites.Favorite.user.related_name="favorites"` vs `temples.Favorite.user.related_name="favorite_shrines"`） | — |

### 5-3. `backend/<goshuin_app>/`

| 探索 | 結果 |
| --- | --- |
| ディレクトリ内容 | `api_views_public.py` 1ファイルのみ（`__init__.py` すら無い → **Python パッケージとして import 不可能**） |
| 文字列 `goshuin_app` のリポジトリ全体 grep | **0件**（ディレクトリ名以外にどこにも現れない） |
| INSTALLED_APPS | 未登録（履歴上も一度も登録されたことがない、§7） |

### 5-4. `accounts/`

§4-1 のとおり self-reference のみ。**production/runtime consumer 0件。**

### 5-5. 隣接候補（auth スコープ外・参考記録）

| モジュール | 状態 | scope |
| --- | --- | --- |
| `backend/temples/api_urls.py` | include 元 0件。中身は `from temples.api.urls import urlpatterns` の互換エイリアス。参照は自身の docstring と tests のコメントのみ | **auth 外**。P1 に含めない |
| `backend/temples/urls.py` | include 元 0件。参照は `test_nearby_api.py:35-36` の**コメント**のみ。`temples/views.py` の `shrine_list` / `shrine_detail` 等を import しており、それらのテンプレート `temples/templates/temples/{detail,list}.html` は `{% extends "base.html" %}` するが `base.html` は探索路上にない（§4-3）→ 仮に routing しても `TemplateDoesNotExist` になる | **auth 外**。P1 に含めない |
| `.coveragerc:52-54` | **#2698 で削除済みの** `backend/users/serializers.py` / `backend/users/urls.py` を omit に列挙したまま。`backend/users/views.py`(`:29`) も同様 | **stale config**。§10 参照 |

---

## 6. Tests

| test path | 対象 | 現在の live path を通るか | 分類 |
| --- | --- | --- | --- |
| `backend/users/tests/test_smoke_me.py::test_me_url_resolves` | `reverse("users_api:me") == "/api/users/me/"` | **YES**（live URL name） | live runtime path |
| `backend/users/tests/test_users_me_api.py`（`test_me_requires_auth` / `test_me_get_returns_profile_like_payload` / `test_me_patch_updates_nickname` / `test_me_patch_persists_birth_profile_fields_and_get_restores_them` / `test_me_patch_rejects_invalid_or_future_birthday`） | `users_api:me` 経由で live `MeView` + live serializer | **YES** | live runtime path |
| `backend/users/tests/test_views_no_sensitive_logging.py` | 旧 `users/views.py::MeView` / `MeIconUploadView` を URL routing 迂回で直接呼ぶ legacy テスト | — | **#2698 で削除済み**（現ツリーに存在しない） |
| `backend/temples/tests/test_favorites_permissions.py` | `from favorites.permissions import IsOwnerOrReadOnly` を import して permission クラス単体を検証 | **NO**（live な favorites API は `temples.api_views.FavoriteViewSet` で、`IsOwnerOrReadOnly` を使っていない） | **dead legacy code を直接テストしている** |
| `backend/temples/tests/test_route_view.py::test_requires_login_redirects_to_login` | live な `temples:shrine_route` が `/accounts/login/` へリダイレクトすることを検証 | **YES**（live endpoint の挙動）。ただし検証しているのは Django 既定 `LOGIN_URL` であり `accounts` アプリではない（§4-2） | live runtime path（`accounts` とは無関係） |
| `backend/temples/tests/test_nearby_api.py:35-36` | `temples/urls.py` への言及は**コメントのみ** | — | 参照ではない |
| `accounts/` を対象とするテスト | **存在しない**（grep 0件） | — | — |
| `<goshuin_app>` を対象とするテスト | **存在しない** | — | — |
| `backend/users/views_me.py` を対象とするテスト | **存在しない** | — | — |

**本監査ではテストを一切削除・変更していない。**

**実行状況**: 本監査環境に Django は未インストール（`python3 -c "import django"` が ImportError）。したがって `manage.py check` / `pytest` は実行していない。上記は静的読解による分類である。なお #2698 の PR 記述は「users/tests: 6 passed」「`python manage.py check`: PASS」を報告している（**PR 記述であり本監査の一次証拠ではない**）。

---

## 7. Git History

unshallow 後の完全履歴（3669 commits）に基づく。

| 候補 | 導入 | 置換実装の追加 | 明示的な移行 | 復活の有無 |
| --- | --- | --- | --- | --- |
| `accounts/` | `2b9461bb` 2025-08-17 `chore: add Django project files and fix unclosed block` — Django プロジェクト雛形の一部として追加 | — | — | **一度も INSTALLED_APPS に入ったことがない**（`git log -S'"accounts"' -- settings.py` → **0件**）。**`accounts.urls` が include されたこともない**（`git log -S'accounts.urls' -- shrine_project/urls.py config/urls.py` → **0件**）。最終変更は `698e5524` 2025-09-24（テスト整理の巻き込み）。全9 commits | なし |
| `backend/favorites/` | `09efa35a` 2025-09-14 `feat(web): search page SSR + favorites/ranking wiring + backend routes` | `temples.api_views.FavoriteViewSet`（live） | **あり**。`b2165f9e` 2025-10-15 (#186) で `favorites.urls` 導入 → `4eeb84c1` 2025-11-13 (#327) の url refactor で外れる → `d20e9600` 2025-11-13 (#328) `fix(api): restore /api/favorites/ endpoint after url refactor` で復活 → **`4d5491f6` 2026-01-06 (#593) `Feat/concierge save unification` が `path("api/", include("favorites.urls"))` を削除し、同 commit で `temples/api/urls.py` に favorites route を追加（+3行）** | #593 以降、復活していない |
| `backend/users/views_me.py` | `687269ca` 2025-09-05 `feat(mobile): MVP batch 1 …`（`/api/auth/me` 系の系譜、初出は `25104201` 2025-09-01 `feat(auth): minimal login + /api/me endpoint`） | `users/api/views.py::MeView`（live） | **あり**。`c7f7c037` 2025-11-02 が `backend/users/urls.py` から `from .views_me import me` を削除（de-routing）。その `users/urls.py` 自体を `324250b` (#2698) が削除 | なし |
| `backend/<goshuin_app>/` | `16f42ce5` 2025-12-23 `Feat/goshuin min (#507)` — **この1 commit のみ** | live な御朱印 API は `temples/api/views/goshuin.py` | INSTALLED_APPS に**一度も登録されていない**（`git log -S'goshuin_app' -- settings.py` → 0件） | なし |
| `backend/temples/api_urls.py` *(参考)* | `7838ad5d` 2025-09-03 | `temples/api/urls.py` | `4d5491f6` 2026-01-06 (#593) で 56行 → 互換エイリアス9行へ縮退 | なし |

**深掘りはここまでに留めた**（置換／廃止の確認に必要な範囲のみ）。

---

## 8. Duplicate Authentication / User Implementations

`324250b` 時点の実装マップ。

| Concern | Implementation | Runtime status |
| --- | --- | --- |
| User me endpoint | `backend/users/api/views.py::MeView`（`/api/users/me/`、JWT + IsAuthenticated） | **LIVE** |
| User me endpoint（旧・別実装） | `backend/users/views.py::MeView` / `CurrentUserView` | **削除済み**（#2698） |
| User me endpoint（旧・関数版） | `backend/users/views_me.py::me` | **DEAD**（残存） |
| User me serializer | `backend/users/api/serializers.py::UserMeSerializer` / `UserProfileSerializer` | **LIVE** |
| User me serializer（旧） | `backend/users/serializers.py::MeSerializer` / `UserProfileSerializer` | **削除済み**（#2698） |
| Profile update serializer | `backend/users/api/serializers.py::UserProfileUpdateSerializer` | **LIVE** |
| Signup API | `backend/users/api/views.py::SignupView` + `SignupSerializer`（`/api/users/signup/`） | **LIVE** |
| Signup（Django テンプレート版） | `accounts/views.py::RegisterView`（`UserCreationForm` + `accounts/register.html`） | **DEAD**（未登録・未 include・テンプレート探索外） |
| Login | SimpleJWT `TokenObtainPairView`（`/api/auth/jwt/create/`）＋ BFF `app/api/auth/login/route.ts` | **LIVE** |
| Login（Django セッション版） | `accounts/views.py::MyLoginView`（`LoginView` + `templates/registration/login.html`） | **DEAD** |
| Logout | BFF `app/api/auth/logout/route.ts`（Cookie 削除のみ） | **LIVE** |
| Logout（Django セッション版） | `accounts/views.py::MyLogoutView` | **DEAD** |
| Password reset | — | **未実装**（live 側に無い） |
| Password reset（Django 版） | `accounts/urls.py` の `auth_views.PasswordResetView` + `templates/accounts/password_reset_*` 6ファイル | **DEAD** |
| My Page（Django テンプレート版） | `accounts/views.py::mypage` + `templates/accounts/mypage.html` | **DEAD** |
| Icon upload | `backend/users/views.py::MeIconUploadView` | **削除済み**（#2698）。**BFF `app/api/users/me/icon/route.ts` は残存し、upstream が 404**（P2 スコープ） |
| Profile icon 書き込み（live 代替） | `UserProfileUpdateSerializer` の `icon` フィールド（multipart PATCH） | LIVE（ただし BFF が JSON 固定のため到達不可。P2 スコープ） |
| Favorites API | `backend/temples/api_views.py::FavoriteViewSet`（`temples/api/urls.py:102`） | **LIVE** |
| Favorites API（旧アプリ） | `backend/favorites/views.py::FavoriteViewSet` + `favorites/urls.py` | **DEAD routing / INSTALLED app** |
| Favorites permission | `temples` 側は permission クラスを使わず `IsAuthenticated` のみ | LIVE |
| Favorites permission（旧） | `backend/favorites/permissions.py::IsOwnerOrReadOnly` / `IsStaffOrReadOnly` | **DEAD**（test-only consumer） |
| Root URLConf | `backend/shrine_project/urls.py` | **LIVE** |
| Root URLConf（旧） | `backend/config/urls.py` | **削除済み**（#2698） |
| API urls | `backend/temples/api/urls.py` | **LIVE** |
| API urls（互換エイリアス） | `backend/temples/api_urls.py` | DEAD（auth 外） |
| API urls（旧テンプレート系） | `backend/temples/urls.py` | DEAD（auth 外） |
| 公開御朱印 API | `backend/temples/api/views/goshuin.py::PublicGoshuinViewSet` | LIVE |
| 公開御朱印 API（旧） | `backend/<goshuin_app>/api_views_public.py` | **DEAD** |

---

## 9. Candidate Classification

| Candidate | File / Symbol | ROOT_URL reachable? | Imported? | Installed? | Tests | Git history | Classification |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| **C1** | `accounts/` アプリ一式（`urls.py` / `views.py`(`RegisterView`,`MyLoginView`,`MyLogoutView`,`mypage`) / `apps.py` / `admin.py` / `models.py`(空) / `migrations/`(空)） | **NO** — `accounts.urls` の include 0件 | **NO** — self-reference のみ。`/accounts/login/` は Django 既定 `LOGIN_URL` であって当アプリ参照ではない（§4-2） | **NO** — INSTALLED_APPS に不在、履歴上も一度もなし | 対象テスト 0件 | 2025-08-17 雛形として追加、以後一度も配線されず | **CONFIRMED_DEAD** |
| **C2** | `templates/accounts/`（8ファイル）＋ `templates/registration/login.html` | **NO** | **NO** — 参照元は `accounts/views.py` と `accounts/urls.py` のみ | **NO** — `TEMPLATES.DIRS = [backend/templates]`（不存在）、`APP_DIRS` は accounts 未登録のため無効（§4-3） | 0件 | C1 と同時導入 | **CONFIRMED_DEAD** |
| **C3** | `backend/users/views_me.py::me` | **NO** — routing 0件 | **NO** — 参照は `.coveragerc:30` の omit 設定のみ | （app `users` は installed だがこのモジュールは未 import） | 0件 | 2025-11-02 `c7f7c037` で de-route 済み、routing 元 `users/urls.py` は #2698 で削除 | **CONFIRMED_DEAD** |
| **C4** | `backend/<goshuin_app>/api_views_public.py`（ディレクトリごと。`__init__.py` 無し） | **NO** | **NO** — 文字列 `goshuin_app` の参照 0件。パッケージ化されておらず import 不能 | **NO** | 0件 | 2025-12-23 `16f42ce5` の1 commit のみ、以後未使用 | **CONFIRMED_DEAD** |
| **C5** | `backend/favorites/urls.py`, `backend/favorites/views.py::FavoriteViewSet`, `backend/favorites/serializers.py` | **NO** — include 0件 | self-reference chain のみ | app は **INSTALLED** | 直接テスト 0件 | 2026-01-06 #593 で include 削除、live は `temples.api_views.FavoriteViewSet` へ移行済み | **CONFIRMED_DEAD**（routing / view 層のみ） |
| **C6** | `backend/favorites/permissions.py`（`IsOwnerOrReadOnly` / `IsStaffOrReadOnly`） | **NO** | **YES（test のみ）** — `backend/temples/tests/test_favorites_permissions.py:7` | app は INSTALLED | legacy code を直接テスト | C5 と同時 | **CONFIRMED_DEAD**（ただし削除にはテスト整理が伴う） |
| **C7** | `backend/favorites/models.py::Favorite` + `backend/favorites/migrations/` + `INSTALLED_APPS` の `"favorites"` | — | self-reference のみ | **INSTALLED** | 0件 | 同上 | **UNRESOLVED** — **本番 DB に `favorites_favorite` テーブルが存在するか、レコードが残っているかを確認していない。** アプリ登録を外すと migration state に影響し、データ喪失リスクがある。別監査が必要 |
| **C8** | `backend/temples/api_urls.py` | **NO** | 自身の docstring と test コメントのみ | — | 0件 | #593 で互換エイリアスに縮退 | **CONFIRMED_DEAD**（ただし **auth スコープ外**。P1 の対象外として扱う） |
| **C9** | `backend/temples/urls.py`（＋それのみが import する `temples/views.py` の一部、`temples/views/admin_seed.py`, `temples/views/places.py`） | **NO** | test の**コメント**のみ | — | 0件 | — | **UNRESOLVED** — `temples/views.py` は `.coveragerc` にもあり、他から部分的に import される可能性を精査していない。**auth スコープ外**。別監査が必要 |
| **C10** | `.coveragerc:29,52,54` の stale entry（`backend/users/views.py` / `backend/users/serializers.py` / `backend/users/urls.py`） | — | — | — | — | #2698 が対象ファイルを削除したが `.coveragerc` は未更新 | **CONFIRMED_DEAD**（設定の残骸。挙動影響なし） |
| — | `backend/config/urls.py` | — | — | — | — | — | **既に削除済み（#2698）**。候補ではない |
| — | `backend/users/urls.py` / `views.py` / `serializers.py` | — | — | — | — | — | **既に削除済み（#2698）**。候補ではない |
| — | `backend/users/api/*`, `backend/users/models.py`, `backend/users/apps.py`, `backend/users/signals.py`, `backend/users/services/*`, `backend/users/admin.py` | YES | YES | YES | live テストあり | — | **STILL_LIVE — 触れてはならない** |
| — | `backend/temples/api_views.py::FavoriteViewSet` | YES | YES | YES | — | — | **STILL_LIVE** |
| — | `backend/temples/api/views/route.py::RouteView`（`login_required`） | YES | YES | YES | `test_route_view.py` | — | **STILL_LIVE** |

---

## 10. Cleanup Boundary（提案のみ。削除は行わない）

### 10-1. Safe deletion candidates（P1 で削除可能）

| # | 対象 | 付随作業 |
| --- | --- | --- |
| 1 | `accounts/` ディレクトリ一式（C1） | settings 変更 **不要**（元々未登録）。migration **不要**（モデル・migration なし） |
| 2 | `templates/accounts/`（8ファイル）＋ `templates/registration/login.html`（C2） | 1 と同時に削除。`templates/base.html` / `templates/home.html` / `templates/components/` は**別問題**なので触らない |
| 3 | `backend/users/views_me.py`（C3） | `.coveragerc:30` の omit 行も同時に削除（設定 cleanup） |
| 4 | `backend/<goshuin_app>/`（C4） | なし |
| 5 | `backend/favorites/urls.py` / `views.py` / `serializers.py`（C5） | **`favorites/models.py`・`migrations/`・INSTALLED_APPS は残す**（C7 が UNRESOLVED のため）。`favorites/views.py` 削除により `favorites/urls.py` の import が消えるので同時削除が必須 |
| 6 | `.coveragerc` の stale entry（C10） | `backend/users/views.py` / `backend/users/serializers.py` / `backend/users/urls.py` の omit 行を削除 |

**この範囲は ROOT_URLCONF・INSTALLED_APPS・live serializer・live view・DB schema のいずれにも触れない。**

### 10-2. 別監査が必要な候補（P1 に含めない）

| # | 対象 | 必要な追加確認 |
| --- | --- | --- |
| 7 | `backend/favorites/` の model / migration / INSTALLED_APPS 登録（C7） | 本番 DB の `favorites_favorite` テーブル有無とレコード件数。データ移行の要否。migration 削除は squash / `--fake` 判断を伴う |
| 8 | `backend/favorites/permissions.py`（C6） | 削除に伴い `backend/temples/tests/test_favorites_permissions.py` の扱い（削除 or live permission への付け替え）を決める必要がある。**本監査ではテストを変更しない方針のため P1 外** |
| 9 | `backend/temples/api_urls.py`（C8）・`backend/temples/urls.py`（C9）・それらが import する `temples/views.py` / `temples/views/*` | **auth スコープ外**。`temples/views.py` の部分的な live 参照の有無を精査する別監査が必要 |

### 10-3. 触れてはならない live code

`backend/shrine_project/urls.py` / `settings.py`、`backend/users/api/`（`urls.py` / `views.py` / `serializers.py`）、`backend/users/models.py` / `apps.py` / `signals.py` / `admin.py` / `services/`、`backend/users/tests/`（2ファイルとも live path を検証）、`backend/temples/api/urls.py`、`backend/temples/api_views.py::FavoriteViewSet`、`backend/temples/api/views/route.py`、frontend の `app/api/auth/*` / `app/api/users/me/*`（**P2 スコープ**）。

### 10-4. 削除時に必要になる付随変更の種別

| 種別 | 必要か | 内容 |
| --- | --- | --- |
| import cleanup | **一部必要** | `favorites/urls.py` → `favorites/views.py` の import chain。C5 は3ファイル同時削除が前提 |
| test removal / update | **P1 範囲では不要** | 10-1 の6項目はいずれも既存テストを壊さない。C6（permissions）だけがテスト整理を伴うため 10-2 へ回した |
| docs update | **必要** | 本書・`docs/audit/user-account-mypage-free-premium-audit.md` §2/§5-2・`docs/audit/userprofile-mypage-decision-gate-audit.md` §5-2 は削除前の状態を記述した時点付き監査。**書き換えず、削除 PR 側で「§5-2 A4/A5/A6 は解消済み」と追記するのが整合的** |
| settings cleanup | **不要（10-1 の範囲では）** | `accounts` は元々未登録。`favorites` の INSTALLED_APPS 除去は C7（UNRESOLVED）に含まれるため P1 外。`.coveragerc` は settings ではないが同種の設定 cleanup として 10-1 #6 に含めた |
| migration | **不要（10-1 の範囲では）** | `accounts` はモデル・migration なし。`favorites` の migration は残す |

---

## 11. Unresolved

| # | 項目 | 理由 |
| --- | --- | --- |
| U1 | `backend/favorites/` の model / migration / INSTALLED_APPS（C7） | 本番 DB のテーブル有無・レコード件数を確認していない。`INSTALLED_APPS` から外すと migration state に影響する。**dead / live のどちらにも断定しない** |
| U2 | `backend/temples/urls.py` と、それが import する `temples/views.py` / `temples/views/admin_seed.py` / `temples/views/places.py`（C9） | routing は到達不能だが、`temples/views.py` 内の symbol が他の live モジュールから部分 import されていないかを精査していない。**auth スコープ外** |
| U3 | 本書の分類の実行検証 | 本監査環境に Django 未インストール（`import django` が ImportError）のため、`manage.py check` / `pytest` / `show_urls` を実行していない。全判定は静的読解（routing / import / app registry の grep）による |
| U4 | frontend 側の dead auth（`lib/auth/withAuth.tsx`、`app/api/me/route.ts`、`lib/api/client.ts` の Authorization interceptor、`app/api/users/me/icon/route.ts`） | **P2 スコープ**。本監査（P1 = backend dead auth）では扱っていない。ただし #2698 が backend の icon endpoint を削除したことで、BFF `app/api/users/me/icon/route.ts` の upstream 404 が確定した点のみ記録する |

---

## 12. 変更なしの確認

本監査でのアプリケーションコード変更は **0**。

- 追加したのは本ファイル（`docs/audit/p1-dead-auth-reconfirmation-audit.md`）1件のみ
- `git diff --name-only origin/develop HEAD` は `docs/` 配下のみを返す
- source 削除・refactor・URL 変更・settings 変更・serializer 変更・frontend 変更・test 書き換え・挙動変更のいずれも行っていない
- `git fetch --unshallow` は read-only 操作であり、作業ツリーに影響しない
