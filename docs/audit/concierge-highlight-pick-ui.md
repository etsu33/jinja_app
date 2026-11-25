# Concierge Highlight Pick UI（見どころ単位の推薦 PR-3）

> Status: Audit — 実装記録
> 日付: 2026-11-22 JST
> Base: develop `26ca3a6`（PR #3510 推薦結果に highlight_pick を足す）
> Branch: `feature/concierge-highlight-pick-ui`
> 設計: プロジェクト文書 `claude/highlight-level-recommendation-plan.md`

## 目的

コンシェルジュの推薦カードに「ここで見る：〈見どころ〉」とアンサーの文を出し、押すと神社詳細の見どころの位置へ移れるようにする。出したカードと出さなかったカードを比べられるように計測する。

## 変更

### データ
- `features/concierge/highlightPick.ts`（新規）：`normalizeHighlightPick(recommendation, ctx)` は backend の `highlight_pick` を `{ highlightId, name, needTag, answerText, href }` に整える。backend が選んだものをそのまま使い、選び直さない。次のときは null（何も出さない）
  - 名前・アンサーの文・見どころの id・相談の種類のどれかが無い
  - 見どころの神社と推薦の神社が違う
  - 登録済みの神社でない（place_id だけの候補の詳細ページには見どころが無い）
- `features/concierge/detailHref.ts`：`highlightHrefFromRecommendation(item, highlightId, ctx)` を追加。神社の詳細リンクと同じ identity の決まり（`resolveShrineIdentity`）と `buildShrineHref` を使い、`/shrines/:id?ctx=…&tid=…#shrine-highlight-{id}` を作る。アンカー名は詳細ページと同じ関数（`shrineHighlightAnchorId`）
- `buildPayloadFromUnified.ts`・`sections/types.ts`：登録済みの推薦（`RegisteredShrineItem`）に `highlightPick` を足す。ダミーの候補には付けない

### 画面 `features/concierge/components/ConciergeHighlightPick.tsx`（新規）
- 第一候補（hero）：見出し「ここで見る」の節。由緒の文脈（history theme）の下、Premium の境目より上（無料の層）
- 2位以降（compact）：カードの下に小さく1〜2行
- 推薦理由の節（今回の相談との接点・history theme）の中には入れない。順位に寄与していない情報を推薦理由として見せないため（Faithful Explanation）
- 無料・有料で出し分けない（2026-11-22 決定）

### 計測（`lib/analytics/searchEvents.ts`）
- `concierge_result_impression` に `hasHighlightPick`・`highlightId`・`highlightNeedTag` を足す
- 新しいイベント `concierge_highlight_pick_click`：`shrineId`・`recommendationRank`・`highlightId`・`highlightNeedTag`・`resultSetId`・`recommendationInstanceId`。アンサーの文は送らない
- 比べ方：`hasHighlightPick` が true / false のカードで、`shrine_detail_transition`（同じ `resultSetId`・`shrineId`）の率を比べる

## 設計からの変更

- 設計案の `concierge_highlight_pick_shown` は作っていない。表示は既存の `concierge_result_impression` に `hasHighlightPick` を足して数える。出さなかったカードも同じイベントで数えられ、比べる母数がそろうため。別のイベントにすると、表示の数を二重に持つことになる

## 変えていないこと

- 順位・推薦理由・推薦文・Premium の出し分け
- 英語のページ（`features/concierge/travel/`）。英語のアンサーはまだ無いので、英語での表示は段階Cで扱う
- `resultSetId` の作り方（神社の id と順番だけで作るので、項目を足しても変わらない）

## テスト

- `features/concierge/__tests__/highlightPick.test.ts`（13件）：リンクの形、未登録・食い違い・欠けがあるときの null、payload への受け渡し
- `features/concierge/components/__tests__/ConciergeSectionsRenderer.highlightPick.test.tsx`（6件）：第一候補・2位以降の表示とリンク、推薦理由の節の外にあること、無いときは何も出さないこと、押したときの計測（文を送らない）、表示の計測の `hasHighlightPick`
- web の全テスト：253ファイル pass。型チェック・lint pass

## 本番への影響

- アンサーがまだ1件も無いので、マージしても画面は変わらない。花園神社のアンサーを入れる（PR-4）と、花園神社が推薦に入った相談で出る
