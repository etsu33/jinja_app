# Concierge Save Action（「あとで見返すために保存」）

Status: Active

対象: Concierge 結果画面下部の save_prompt ボタン（`ConciergeSectionsRenderer.tsx`、`RendererAction` = `save_concierge_thread`）。
Hero 直下の同ラベルボタンは `ShrineSaveButton`（神社のお気に入り）であり、本書の対象外。

## Root cause（修正前）

- `ConciergeClientFull.tsx` の `save_concierge_thread` ハンドラは、未ログインならログインへ誘導するが、
  **ログイン済みでは何もせず return していた**（`// 現時点では server 保存API未接続。`）。
  ボタンを押しても成功・失敗いずれのフィードバックもなく、再訪導線も提示されなかった。
- 一方 backend は `/api/concierge/chat/` の全リクエストで `ConciergeThread` を永続化しており、
  認証済みリクエストでは `thread.user` に紐づく（`api_views_concierge.py` → `concierge_history.append_chat()`）。
  つまり「保存処理が無い」のではなく、「永続化済みであることを UI が確認・提示していない」状態だった。

## 判断: 明示的な bookmark state は導入しない

- ログイン済みユーザーの相談はすでにユーザー所有の履歴（`GET /api/concierge-threads/`、`/mypage/history/<tid>`）に載る。
  保存専用 API / bookmark カラムを追加すると同じ事実を二重に持つことになる（重複永続化）。
- したがって migration・backend 変更は行わない。

## 保存フロー（`features/concierge/useConciergeThreadSave.ts`）

| 条件 | 挙動 |
| --- | --- |
| 未ログイン（`isAuthRequiredForAction("save_concierge_thread")`） | API を呼ばず `/auth/login?returnTo=/concierge` へ（従来どおり） |
| ログイン済み・thread ID なし（0） | API を呼ばず error（`no_thread`） |
| ログイン済み | `GET /api/concierge-threads/` を 1 回呼び、対象 thread ID が含まれる場合のみ `saved` |
| 一覧に含まれない | error（`not_owned`）。成功表示はしない |
| 401 | error（`unauthenticated`） |
| 5xx（API 失敗。例: upstream 502 text/html） | error（`server_unavailable`） |
| 2xx だが `[]` / `{ results: [] }` 形式で読めない（parse 失敗） | error（`invalid_response`）。`not_owned` に丸めない |
| 応答なし（transport 失敗）・その他 | error（`network`） |

- 所有確認に thread 詳細 API（`/api/concierge-threads/<id>/`）は使わない。詳細 API は
  `user IS NULL AND anonymous_id = cookie` の thread にも 200 を返すため、ユーザー履歴に載っていない
  匿名 thread を「保存済み」と誤報告しうる。
- 確認中はボタンを `disabled` にし、hook 側でも in-flight / 確認済み thread への再リクエストを抑止する。
- 成功時は「保存済み」＋「履歴で見返す」（`/mypage/history/<tid>`）を表示する。
- thread が切り替わったら状態をリセットする。

一覧取得は `fetchThreadsStrict()`（`lib/api/concierge.ts`）を使う。既存の `fetchThreads()` は想定外の body を
`[]` に丸めるため、保存確認に使うと parse 失敗が「履歴に無い（not_owned）」と誤表示される。`fetchThreads()` 自体の挙動は変えていない。

いずれの error 状態でもボタンは再度押せる（確認済みではないため二重送信抑止の対象外）。

## 本番障害記録（2026-10-22, `/concierge?tid=89`）

Vercel runtime log（production, `dpl_8tvUGTt5n5UWpnAFUjPiP6P8R7Wz`）で確認した事実:

| 時刻 (UTC) | request | 結果 |
| --- | --- | --- |
| 04:17:04 | `GET /api/concierge-threads/`（画面ロード） | 200 JSON |
| 04:17:29 | `POST /api/concierge/chat/` | 200 JSON |
| 04:17:30 | `GET /api/concierge-threads/89/` | **502 `text/html`**（223036 bytes） |
| 04:17:30 | `GET /api/concierge-threads/85/` | 200 JSON |
| 04:17:39 | `GET /api/concierge-threads/`（保存クリック） | **502 `text/html`**（223036 bytes） |

- request 経路: browser axios `/api/concierge-threads/` → BFF `bffFetchWithAuthFromReq` → Django `/api/concierge-threads/`。
  `hasAuthorization: true`（`access_cookie`）で、認証ヘッダは付与されている。
- 失敗は **Django upstream が返した 502（API 失敗）**であり、frontend の parse 失敗ではない。axios が reject し、
  修正前は `network`（「保存を確認できませんでした」）として表示されていた。
- 03:47 にも同じ形（chat 200 の直後数秒、thread detail が 502 `text/html` 223036 bytes）が記録されている。
- thread 89 の所有者は、一覧・詳細ともに 502 のため**ログからは確認できていない**（DB 照会が必要）。
- **502 の発生原因（backend / Render 側）は未確定**。Vercel 側ログには upstream の status と body 長しか残らない。
  確定には Render の backend ログ（同時刻帯の gunicorn / Django 出力）の確認が必要。

## 既知の制約

- 一覧 API は最新 50 件のみ返す。51 件目以降の古い thread を開いて保存を押すと、保存済みであっても
  `not_owned` として表示される（成功の誤報告ではなく、確認不能の表示）。
- 匿名で相談した後にログインしても、匿名 thread を user に移す（claim する）経路は存在しない
  （`docs/audit/userprofile-mypage-decision-gate-audit.md` §8）。その thread は `not_owned` になる。
  claim の導入は本変更の範囲外。

## 変更していないもの

推薦・ランキング・課金・analytics（`save_prompt_click` の `trackCardEvent` / `conciergeLog`）の契約。
