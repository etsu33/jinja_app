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
| その他の失敗 | error（`network`） |

- 所有確認に thread 詳細 API（`/api/concierge-threads/<id>/`）は使わない。詳細 API は
  `user IS NULL AND anonymous_id = cookie` の thread にも 200 を返すため、ユーザー履歴に載っていない
  匿名 thread を「保存済み」と誤報告しうる。
- 確認中はボタンを `disabled` にし、hook 側でも in-flight / 確認済み thread への再リクエストを抑止する。
- 成功時は「保存済み」＋「履歴で見返す」（`/mypage/history/<tid>`）を表示する。
- thread が切り替わったら状態をリセットする。

## 既知の制約

- 一覧 API は最新 50 件のみ返す。51 件目以降の古い thread を開いて保存を押すと、保存済みであっても
  `not_owned` として表示される（成功の誤報告ではなく、確認不能の表示）。
- 匿名で相談した後にログインしても、匿名 thread を user に移す（claim する）経路は存在しない
  （`docs/audit/userprofile-mypage-decision-gate-audit.md` §8）。その thread は `not_owned` になる。
  claim の導入は本変更の範囲外。

## 変更していないもの

推薦・ランキング・課金・analytics（`save_prompt_click` の `trackCardEvent` / `conciergeLog`）の契約。
