# トップページに出発地の1行を置く

> Status: Audit — 実装記録
> 日付: 2026-11-23 JST
> Branch: `feature/home-origin-row`
> 決まり: `docs/product/concierge-input-architecture.md` の Addendum（2026-11-23）

## 何が起きていたか

本番のコンシェルジュの記録（2026-11-23）で、相談ごとに同じスレッドで「位置無し→位置有り」の2回送信が起きていた。

| 時刻 | 相談 | 位置 | 上位3件 |
|---|---|---|---|
| 11:18:17 | やり直したい | 無し | 三峯神社・乃木神社・九頭龍神社 |
| 11:18:31 | やり直したい | 有り | 花園神社・乃木神社・烏森神社 |
| 11:19:22 | 転職したい | 無し | 椿大神社（約310km）・乃木神社・建部大社 |
| 11:19:38 | 転職したい | 有り | 乃木神社・日枝神社・烏森神社 |

出発地の入力（`OriginSelector`）は `/concierge` の「条件を開く」の中にしかなく、トップページは相談文だけを渡していたため。1回目の位置無しの結果が「一瞬見える」原因になり、相談の回数も2回使っていた。

## 変更

- `features/home/components/HomeOriginRow.tsx`（新規）：相談の欄の下の1行（「📍 出発地を選ぶ（任意）」→ 選んだあとは「〇〇から」）。押すと下から既存の `OriginSelector` を出す（`CompassOriginSummary` と同じ形）。位置情報の許可は「現在地を使用」を押したときだけ聞く
- `features/home/components/HomeHeroConsultationInput.tsx`：出発地の状態を持ち、相談を始めるとき（「＋ 条件を追加する」を含む）に出発地を渡す。相談の欄を3行→2行に低くした
- `lib/concierge/homeOriginHandoff.ts`（新規）：出発地を URL に載せず、同じタブの sessionStorage で1回だけ渡す。10分より古い値・壊れた値は使わない。読んだら必ず消す
- `app/concierge/ConciergeClientFull.tsx`：開いたときに1回だけ受け取り、受け取ってから `?theme=` の自動送信をする

## 変えていないこと

- `/concierge` の入口の画面（出発地は今までどおり折りたたみの中）
- 送信する位置の形（`location: { lat, lng }`）とバックエンド
- モバイルアプリ（Expo）

## テスト

- `lib/concierge/__tests__/homeOriginHandoff.test.ts`（4件）
- `features/home/components/__tests__/HomeHeroConsultationInput.test.tsx`：1行の表示、押すと4つの選択肢、選ぶと表示が変わり相談開始で渡す（URL に位置を載せない）、選ばなければ前の値を残さない
- `app/concierge/__tests__/ConciergeClientFull.autoSubmitPending.test.tsx`：渡した出発地が1回目の送信に `location` として載り、受け取ったら消える／渡さなければ載らない
- web 全体：254ファイル pass、型チェック・lint pass
