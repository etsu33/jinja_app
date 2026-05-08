

# 本番BFF耐性チェックリスト

## 目的

本番環境でBFF経由のAPIエラーが発生したときに、原因層をすばやく切り分けるための運用チェックリスト。

対象は Next.js BFF から Django backend へ中継する `/api/*` route とする。

## 前提

- Web から backend 直URLは叩かない
- フロントは `/api/*` のBFF経由で通信する
- 認証が絡むRoute Handlerは原則 `bffFetchWithAuthFromReq` を使う
- 単純中継や特殊処理は `djFetch` を使う
- routeごとの独自fetch実装は最小化する

## 本番確認の優先順位

1. ブラウザ Network で現在の status を確認する
2. Vercel Function Logs でBFF routeの状態を見る
3. Render backend logs でDjango側の状態を見る
4. Cookie / Authorization / refresh の状態を確認する
5. backend直で再現するか確認する

## ブラウザ Network 確認

### 見る項目

- Request URL
- Method
- Status Code
- Request Headers
- Response Headers
- Response body preview
- Cookie送信有無

### 判断

| 状態 | 判断 |
|---|---|
| `/api/*` が 200 | BFF経由は成功 |
| `/api/*` が 401 | 認証cookie / refresh / login状態を確認 |
| `/api/*` が 403 | permission / plan / CSRF相当を確認 |
| `/api/*` が 500 | Vercel Logs と Render Logs を確認 |
| Networkに出ない | UIイベント / router / client fetch を確認 |

## Cookie確認項目

### Application > Cookies

確認対象:

- `access_token`
- `refresh_token`
- `concierge_anon_id`

### 確認する属性

| Cookie | httpOnly | SameSite | Secure | path | 用途 |
|---|---|---|---|---|---|
| access_token | true | lax | 本番では必要に応じてtrue | / | backend認証 |
| refresh_token | true | lax | 本番では必要に応じてtrue | / | access更新 |
| concierge_anon_id | true | none | true | / | 匿名concierge quota |

### 注意

- `SameSite=None` には `Secure=true` が必要
- production domain と preview domain でcookie挙動が変わる可能性がある
- cookieが存在しても、BFFがAuthorizationへ変換できているとは限らない
- access token期限切れ時は refresh path のログを見る

## Vercel Function Logs 確認

### 検索対象

- Request Path
- Status Code
- 該当API path

例:

```text
/api/my/goshuins
/api/shrine-submissions
/api/concierge/chat
/api/billings/checkout
```

### 見るべきログキー

```text
[BFF_THREAD_UPSTREAM_REQUEST]
[BFF_FETCH_URL]
[BFF_UPSTREAM]
[DJ_FETCH]
[DJ_FETCH_RESPONSE]
[DJ_FETCH_RESPONSE_HEADERS]
[BFF_CHAT_ENTRY]
[BFF_CHAT_PROXY]
[BFF_CHAT_REFRESH_FLOW]
[BFF_CHAT_REFRESH]
[BFF_CHAT_REFRESH_JSON]
[BFF_ANON_COOKIE_FROM_BODY]
[BFF_ANON_COOKIE_SET_RESULT]
[BFF_CHAT_RETURN]
```

### 判断

| Vercel Log | 判断 |
|---|---|
| BFF route自体が例外 | Next.js route実装を確認 |
| upstream status 500 | Render backend logs を確認 |
| upstream status 401 | cookie / Authorization / refresh を確認 |
| upstream status 200 だがUIで失敗 | frontend parse / UI state を確認 |
| bodyPreview がHTML 500 | Django未ハンドル例外の可能性 |

## Render backend logs 確認

### 検索語

```text
Traceback
ERROR
ProgrammingError
OperationalError
IntegrityError
AttributeError
KeyError
DoesNotExist
relation does not exist
column does not exist
/api/my/goshuins/
/api/shrine-submissions/
/api/concierge/chat/
/api/billings/checkout/
```

### 判断

| Render Log | 判断 |
|---|---|
| `relation does not exist` | migration / table欠損 |
| `column does not exist` | migration履歴と実DB列の差分 |
| `AttributeError` | serializer / view / model field参照 |
| `KeyError` | request body / response shaping |
| `IntegrityError` | DB constraint / duplicate / null制約 |
| OpenAI系例外 | `CONCIERGE_USE_LLM` とAPI key設定を確認 |

## backend直確認

BFF経由だけで落ちるか、backend単体でも落ちるかを分ける。

### backend直で確認する項目

- 対象viewが200を返すか
- serializerが実データで落ちないか
- DB列が揃っているか
- env設定が想定通りか

### 例

```bash
python manage.py check
```

```bash
python manage.py migrate --plan
```

```bash
python manage.py shell -c "from django.db import connection; print(connection.introspection.table_names())"
```

## 原因分類表

| API | Browser | Vercel | Render | backend直 | 判断 |
|---|---|---|---|---|---|
| /api/my/goshuins/ | 未確認 | 未確認 | 未確認 | 未確認 | 未確定 |
| /api/shrine-submissions/ | 未確認 | 未確認 | 未確認 | 未確認 | 未確定 |
| /api/concierge/chat/ | 未確認 | 未確認 | 未確認 | 未確認 | 未確定 |
| /api/billings/checkout | 未確認 | 未確認 | 未確認 | 未確認 | 未確定 |

## 修正PR分離ルール

- BFF auth / cookie修正と backend serializer修正は混ぜない
- docs更新と実装修正は原則分ける
- migration repair は単独PRにする
- concierge/chat のBFF共通化は別PRにする
- contract test追加は本番挙動整理後に別PRで行う

## 次PR候補

### 1. BFF contract test追加

対象:

- refresh success path
- refresh fail path
- multiple set-cookie relay
- anon cookie relay
- upstream 500 passthrough

### 2. concierge/chat BFF共通化検討

対象:

- `bffFetchWithAuthFromReq` へ寄せられる責務
- `djFetch` に残すべき責務
- anon cookie処理の共通helper化

### 3. production smoke checklist追加

対象:

- login
- `/api/users/me/`
- `/api/my/goshuins/`
- `/api/shrine-submissions/`
- `/api/concierge/chat/`
- `/api/billings/status/`
- `/api/billings/checkout`

## 完了条件

- 本番でエラー発生時に Browser / Vercel / Render / backend直 のどこを見るか迷わない
- status 401 / 403 / 500 の分類基準が明文化されている
- cookie / refresh / set-cookie の確認項目が明文化されている
- 次PRで追加するcontract testの候補が明文化されている
