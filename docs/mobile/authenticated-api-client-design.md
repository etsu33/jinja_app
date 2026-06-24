

# Mobile Authenticated API Client Design

## 目的

mobile / Expo 側から backend の認証必須 API を安全に呼び出せるようにする。

Score v3 の UI route_open 確認では、mobile 詳細画面の「地図で経路を確認する」クリックが `ShrineInteractionLog` に保存されていないことを確認した。

原因は、mobile 側に JWT 保存・Authorization ヘッダー付与の仕組みがなく、backend の `IsAuthenticated` API に到達できないためと考えられる。

## 現状

### backend

- JWT 発行 API は存在する
  - `POST /api/auth/jwt/create/`
- 行動ログ API は認証必須
  - `POST /api/shrine-interactions/`
- route_open / detail_view は `ShrineInteractionLog` に保存される
- manual curl では保存確認済み

### web

- Next.js BFF 経由で backend API を呼び出す構成
- `apps/web/src/app/api/shrine-interactions/route.ts` が存在する
- `apps/web/src/components/shrine/GoogleMapRouteLink.tsx` は `trackShrineInteraction` を呼び出す

### mobile

- Expo / mobile web は `localhost:8081` で動作する
- `apps/mobile/lib/http.ts` は `BASE_URL` に対して `get` / `post` を行うだけ
- `Authorization` ヘッダー付与は未実装
- JWT access / refresh token の保存箇所は未確認、現状ほぼ未実装
- AsyncStorage 利用は birthday / recently-viewed などのローカル保存用途に限られる

## 課題

mobile から以下の API を呼び出すには認証が必要。

- `POST /api/shrine-interactions/`
- `POST /api/favorites/`
- `POST /api/shrines/{id}/visit/`
- `POST /api/shrines/{id}/reflection/`

現状の `http.ts` では JWT を付与できないため、mobile UI から route_open を保存しようとしても `401 Unauthorized` になる可能性が高い。

## 方針

### 1. token storage を分離する

mobile 専用の token storage を追加する。

想定ファイル:

- `apps/mobile/lib/authTokens.ts`

役割:

- access token の保存
- refresh token の保存
- token の取得
- token の削除

保存先:

- MVP では `AsyncStorage` を利用する
- 将来的には `expo-secure-store` への移行を検討する

理由:

- まず route_open / save / visit_done / reflection_saved の実測を進める
- token保存の責務を `http.ts` に混ぜない
- 後で SecureStore に差し替えやすくする

### 2. authenticated request helper を追加する

`apps/mobile/lib/http.ts` に認証付き helper を追加する。

想定関数:

- `getAuth<T>(path: string, init?: RequestInit): Promise<T>`
- `postAuth<T>(path: string, body: unknown, init?: RequestInit): Promise<T>`

方針:

- `authTokens.ts` から access token を取得する
- token がある場合のみ `Authorization: Bearer <access>` を付与する
- token がない場合は明示的に `Unauthenticated` エラーを返す
- 既存の `get` / `post` は非認証 API 用として維持する

### 3. refresh は次フェーズに分離する

初期実装では refresh token 自動更新を必須にしない。

理由:

- 現在の目的は UI 行動ログの保存確認
- refresh 実装まで含めるとスコープが肥大化する
- JWT の短命問題は確認済みだが、まず MVP の最小認証導線を作る

ただし、将来的には以下を追加する。

- access token 期限切れ時に refresh token で再発行
- refresh 失敗時に token を削除
- ログイン画面へ誘導

## route_open 保存の実装順序

### Step 1: auth token storage

- `authTokens.ts` を追加
- access / refresh の保存・取得・削除を実装

### Step 2: authenticated http helper

- `http.ts` に `getAuth` / `postAuth` を追加
- Authorization ヘッダーを付与
- token 未保存時のエラーを定義

### Step 3: interaction API helper

- `apps/mobile/lib/shrineInteractions.ts` を追加
- `postShrineInteraction` を定義
- `action_type` は backend と同じ値を使う
  - `detail_view`
  - `route_open`
  - `shrine_card_click`

### Step 4: shrine detail に route_open 保存を追加

対象:

- `apps/mobile/app/shrines/[id].tsx`

方針:

- `openDirections` の中で `route_open` を送信する
- 送信成功 / 失敗に関係なく地図は開く
- ログ保存失敗で参拝導線を止めない

保存 payload 例:

```json
{
  "shrine_id": 17,
  "action_type": "route_open",
  "source": "mobile_shrine_detail",
  "thread_id": null,
  "metadata": {
    "event": "route_open",
    "routeTarget": "google_maps",
    "platform": "mobile"
  }
}
```

### Step 5: detail_view 保存を追加

route_open と同じ仕組みで、詳細画面表示時に `detail_view` を保存する。

ただし二重送信防止のため、`useRef` などで1画面1回に制限する。

## 実装制約

- route_open 保存失敗で Google Maps 起動を止めない
- 認証未設定時は silent fail ではなく、開発中に検知できるログを出す
- `http.ts` に token保存責務を持たせない
- refresh token 自動更新は別PRに分離する
- backend の `IsAuthenticated` は変更しない
- 匿名 route_open 記録はこのPRでは扱わない

## 検証手順

### 事前確認

- mobileでログインし、access token が保存されていること
- `getAuth` / `postAuth` が Authorization ヘッダーを付与すること

### route_open確認

1. `apps/mobile` を起動する
2. `/shrines/17` を開く
3. 「地図で経路を確認する」を押す
4. backend DB を確認する

確認コマンド:

```bash
cd backend && python manage.py shell -c "from temples.models import ShrineInteractionLog; print(list(ShrineInteractionLog.objects.filter(shrine_id=17, action_type='route_open').values('id','source','metadata','created_at').order_by('-id')[:10]))"
```

期待値:

- `source=mobile_shrine_detail` の `route_open` が増える

### dashboard確認

```bash
curl -s http://127.0.0.1:8000/api/concierge/score-v3/dashboard/ -H "Authorization: Bearer $ACCESS" | python -m json.tool
```

期待値:

- `route_open_rate` に反映される

## 完了条件

- mobile 側で JWT access token を保存・取得できる
- mobile HTTP helper が Authorization ヘッダーを付与できる
- mobile shrine detail の route_open が DB に保存される
- dashboard API に route_open が反映される
- route_open 保存失敗時も地図起動は止まらない

## 次PR候補

- `feature/mobile-authenticated-api-client`
- `feature/mobile-route-open-interaction-log`
- `feature/mobile-detail-view-interaction-log`

## TODO

```markdown
- [ ] authTokens.ts を追加
- [ ] access / refresh token の保存・取得・削除を実装
- [ ] http.ts に getAuth / postAuth を追加
- [ ] shrineInteractions.ts を追加
- [ ] route_open を mobile 詳細画面から送信
- [ ] detail_view を mobile 詳細画面から送信
- [ ] route_open DB保存確認
- [ ] dashboard反映確認
```
