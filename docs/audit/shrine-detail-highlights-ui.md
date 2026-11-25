# Shrine Detail Highlights UI（PR-5）

> Status: Audit — PR-5 実装記録。
> 日付: 2026-11-21 JST
> Branch: `feature/shrine-detail-highlights-ui`（`feature/highlights-detail-api` の上に積む）
> 設計: プロジェクト文書 `claude/highlights-detail-integration-plan.md`

## 目的

Story（伝承）・History（由緒・歴史）を読んだ人が、「ここに行けばこれが見られる」と分かるようにする。

## 画面

- 「神社について」（`ShrineFactSection`）のすぐ下、解釈レイヤーの前に「ここで見られるもの」（`ShrineHighlightSection`）を置く。Fact と同じく Premium で隠さない
- 由緒・歴史が無い神社でも、見どころがあれば単独で出す
- 1件のカード：カテゴリー・名前・場所の目安・説明・「この見どころが伝える歴史」・「由緒・歴史を読む」リンク・「◯年◯月◯日に現地で確認」・出典
- 並びは API の `sort_order`（参道の順番）。節の冒頭に「参道の順に並べています」と書くため、データ入力では `sort_order` を参道の順番で付ける
- 空の項目は見出しごと出さない。未知のカテゴリーは内部の英語キーを出さず、カテゴリー名を省く

## 由緒・歴史との行き来

- 由緒・歴史のカードに `id="shrine-history-{id}"`、見どころのカードに `id="shrine-highlight-{id}"` をつけ、ページ内リンクで行き来する
- 由緒・歴史の側：「現地で見られる場所：◯◯」→ 見どころへ
- 見どころの側：「由緒・歴史を読む：◯◯」→ 由緒・歴史へ
- リンクは `buildShrineHighlightSection` で、Fact Section に実際に出ている由緒・歴史だけに絞る（リンク切れを作らない）。`attachHighlightLinksToFactSection` は元の Fact Section を書き換えず新しいオブジェクトを返す

## 計測（PostHog、`trackSearchEvent`）

| イベント | いつ | 送る値 |
|---|---|---|
| `shrine_highlights_view` | 節が半分以上画面に入ったとき1回（IntersectionObserver が無い環境では表示時） | `source: "shrine_detail"`, `shrineId`, `highlightCount` |
| `shrine_highlight_link_click` | 行き来のリンクを押したとき | `source`, `shrineId`, `highlightId`, `linkDirection`（`history_to_highlight` / `highlight_to_history`） |

本文・名前などの文章は送らない。

## 変更ファイル

- `src/lib/api/types.ts`：`ShrineHighlight` 型、`ShrineBase.highlights`
- `src/components/shrine/detail/types.ts`：`DetailHighlightSection` / `DetailHighlightItem` / リンク型、`DetailFactHistoryItem.highlightLinks`
- `src/lib/shrine/buildShrineHighlightSection.ts`（新規）
- `src/lib/shrine/buildShrineDetailModel.ts`：`highlightSection` を返し、Fact Section にリンクを足す
- `src/components/shrine/detail/ShrineHighlightSection.tsx` / `ShrineHighlightAnchorLink.tsx`（新規）
- `src/components/shrine/detail/ShrineFactSection.tsx`：アンカー id と「現地で見られる場所」、`SourceList` を共有のため export
- `src/components/shrine/detail/ShrineDetailArticle.tsx`：節の配置
- `src/lib/analytics/searchEvents.ts`：イベント名と送る値

## 確認

- `pnpm typecheck` 成功、変更ファイルの ESLint 成功
- Vitest 全体 251ファイル・2453件成功（新規：`buildShrineHighlightSection.test.ts`、`ShrineHighlightSection.test.tsx`、`buildShrineDetailModel.test.ts` と `ShrineDetailArticle.test.tsx` に追加）
- ブラウザでの見た目は未確認（本番データに公開済みの見どころがまだ無いため、データ入力後にプレビューで確認する）
