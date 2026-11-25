> **Status: Reference**
>
> 本文書は、Design Token Migration Stage 3（`docs/design/design-token.md`のMigration方針 3. Recommendation画面適用）のPR-C（主要Recommendation UI適用）着手前調査で発見した、「強調ダークサーフェス（Dark Surface）」の用途分類・新設Semantic Token決定を記録する。
>
> 本文書はStage 3 PR-C着手前の意思決定記録であり、Token実値・最終命名の確定はこの後の実装PR（PR-C1/C2/C3、またはToken定義基盤PR）で行う。本文書の決定をもって直ちにPR-C実装を開始してよいわけではない（詳細は「実装ルール」節）。

# Design Token Stage 3 — Dark Surface Contract決定

## 背景

`docs/audit/design-token-stage3-neutral-semantic-decision.md`（Message-own/Selection Semantic Token新設の決定記録）は、`MessageList.tsx`の`bg-gray-900`について、「チャット固有の概念ではなく、billing各画面・error画面・`ConciergeCard.tsx`等が独立にslate-900/neutral-900/stone-950で似た『強調ダークサーフェス』を実装している repo横断的な不統一パターンの一インスタンス」であると指摘していた。この repo横断パターン自体への決定は当時保留されていた。

PR-C（`ConciergeEntryCard.tsx`・`ConciergeSectionsRenderer.tsx`・`ConciergeTopRecommendationHero.tsx`・`components/ConciergeCard.tsx`）の再監査で、この保留パターンがPR-C対象範囲内に少なくとも2箇所（`ConciergeSectionsRenderer.tsx`・`components/ConciergeCard.tsx`）存在することを確認した。本文書はこの「強調ダークサーフェス」パターンの用途分類調査と決定事項を記録する。

## 調査事実

### 1. 用途別の分類（3群）

`bg-slate-900` / `bg-neutral-900` / `hover:bg-neutral-800` / `bg-stone-950`のrepo横断的な使用箇所を、実際の用途（要素の役割）に基づき分類した。パレット名が同じでも役割が異なる場合は別群として扱った。

**Group A（強調CTA / interactive dark surface）**: ボタン・リンク等の操作要素の背景として、濃色背景＋反転文字色（white/inverse）を用いる用途。

| ファイル | 内容 |
|---|---|
| `apps/web/src/app/error.tsx` | 再試行ボタン |
| `apps/web/src/app/plan/PlanView.tsx` | 検索実行ボタン |
| `apps/web/src/app/billing/page.tsx` | プレミアム登録・プラン管理リンク（2箇所） |
| `apps/web/src/app/billing/cancel/page.tsx` | プレミアム登録へ戻るリンク |
| `apps/web/src/app/billing/upgrade/page.tsx` | 決済開始ボタン |
| `apps/web/src/app/billing/success/page.tsx` | 登録へ戻る・再確認リンク（2箇所） |
| `apps/web/src/app/billing/manage/page.tsx` | プラン状況へ戻るリンク |
| `apps/web/src/features/concierge/components/ConciergeEntryCard.tsx` | ログインボタン（`bg-slate-800 hover:bg-slate-900`） |
| `apps/web/src/app/concierge/ConciergeClientFull.tsx`（1298行目付近） | 「/map」へのLink-as-buttonのみ（同ファイル内の`<pre>`出力はGroup B、後述） |
| `apps/web/src/components/shrine/ShrineDetailShell.tsx` | CTAリンク。文字色は既に`text-[var(--kt-color-text-inverse)]`を採用済みで、背景のみリテラル |
| `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`（PR-C2対象） | フィルタークリアボタン（`bg-neutral-900`） |
| `apps/web/src/components/ConciergeCard.tsx`（PR-C3対象） | 詳細リンクボタン（`bg-neutral-900 hover:bg-neutral-800`） |

**Group B（debug / code output panel、対象外）**: JSON等のデバッグ出力を表示する`<pre>`ブロックの背景。操作要素ではなく、Group Aとは責務が異なる。

- `apps/web/src/app/concierge/ConciergeClientFull.tsx`の`<pre>`ブロック4箇所（`bg-slate-900`、いずれも`JSON.stringify`結果の表示用）

**Group C（別カテゴリ、対象外）**: パレット名が近くても実際は既存の別カテゴリに属する箇所。

- `apps/web/src/features/mypage/components/GoshuinDetailModal.tsx`の`bg-stone-950/35`は`Dialog.Overlay`（モーダルの半透明オーバーレイ）であり、`docs/design/design-token.md`のColorカテゴリ表に既存する「Overlay」（`bg-black/50`と`bg-stone-950/35`が不統一、と既に記載済み）に属する。Dark Surfaceとして扱わない。

### 2. 文字色の既存Token状況

Group A内の`ShrineDetailShell.tsx`は、背景はリテラル（`bg-slate-900`）のまま、文字色のみ既存の`--kt-color-text-inverse`（`docs/design/design-token.md`のSemantic Token: text、Web実装: `apps/web/src/styles/tokens.css`）を先行採用していた。Group A全体で見ても、文字色は白系（`text-white`または`text-inverse`相当）で統一されており、既存の`text-inverse`が意味的に過不足なく対応することを確認した。

### 3. Group A内の実値不一致

Group A内でも、`slate-900`（billing系・error・PlanView等）と`neutral-900`（`ConciergeSectionsRenderer.tsx`・`ConciergeCard.tsx`）とでpalette名が分かれている。これは`docs/audit/design-token-stage3-neutral-semantic-decision.md`が採用したOption B（palette名をSemantic Token名にせず、意味が同じなら同じSemantic Tokenへ吸収し、実色差はPlatform Theme層で吸収する）の対象パターンと一致するが、Dark Surfaceについて実値をどちらかへ統一するかはOption Bの一般方針だけでは機械的に決定できない。統一により見た目が変化するため、Product判断なしに独断で統一しない。

### 4. Mobile対応

`apps/mobile/design/theme.ts`を確認したが、Mobile側の基調テーマ（`kamimusubiDark`）自体が既にdarkであるため、「light UI内での強調dark面」というWeb側の概念に対応する既存実装は存在しない。Mobile側のCTA強調はAction Token（`kamimusubiDark.gold`）が担っており、Dark Surfaceとは責務が異なる。

## 決定事項

母艦（Product判断）による確定。

| 項目 | 決定 |
|---|---|
| Dark Surface Semantic Tokenの新設 | **追加する（Group Aのみ）**。候補名: `color.surface.emphasis` / `color.surface.emphasis.hover`（Web実装候補: `--kt-color-surface-emphasis` / `--kt-color-surface-emphasis-hover`）。実値・最終命名は実装PR側で確定する |
| 文字色Token | **新設しない**。既存の`color.text.inverse`（Web: `--kt-color-text-inverse`）を再利用する |
| 対象範囲 | Group A（強調CTA / interactive dark surface）のみ。Group B（debug/output panel）・Group C（Overlay）は対象外とし、既存の別カテゴリ（またはliteral）のまま維持する |
| Group A内の実値不一致（slate-900 vs neutral-900） | 本文書では機械的に統一しない。実装PR側で個々の置換箇所ごとにvisual差が発生しないか確認し、統一が必要な場合は改めてProduct判断を仰ぐ |
| Light Surface 100系（`bg-slate-100`/`bg-stone-100`/`bg-neutral-100`） | 今回Contract化しない。hover/disabled/badge/decorative等の責務混在が確認されており、`KEEP_LITERAL_FOR_NOW` |
| Guest Notice amber（`ConciergeEntryCard.tsx`の未ログイン案内） | 今回Contract化しない。Premium Tokenと値が近いが責務が異なるため流用せず、`KEEP_LITERAL_FOR_NOW` |
| Action Border（`border-emerald-300`/`border-emerald-600`） | 今回Contract化しない。既存の`action-primary`・`border-focus`の流用はしない。`KEEP_LITERAL_FOR_NOW` |
| Disabled surface / Badge・decorative neutral surface | 今回Contract化しない。`KEEP_LITERAL_FOR_NOW` |

## PR-C Split（再確認）

`docs/audit/design-token-stage3-neutral-semantic-decision.md`のSub-PR再設計を踏襲し、以下の3分割（`SPLIT_SHARED_CARD`）を正式採用する。

- **PR-C1**: `ConciergeEntryCard.tsx`
- **PR-C2**: `ConciergeTopRecommendationHero.tsx`、`ConciergeSectionsRenderer.tsx`
- **PR-C3**: `apps/web/src/components/ConciergeCard.tsx`

`components/ConciergeCard.tsx`はStage 3スコープに残す（Shrine Detail画面への本番トラフィックが現状ないことを確認済み。Shrine関連の命名を持つ利用箇所は、デバッグ専用ルート経由のみ、または未使用コードであり、本番のShrine Detail画面からは到達しない）。

## 実装ルール

- 本Contract（本文書のマージ）が完了して初めて、PR-C1/C2/C3の実装に着手できる。
- PR-C1/C2/C3では以下を行う: (a) 既存Semantic Tokenでexact matchできる箇所のToken化、(b) Dark Surface該当箇所（Group Aのみ）の新Tokenへの移行、(c) `text-slate-950`の`text-primary`への統合。
- 上記「決定事項」でDeferredとした箇所（Light Surface 100系・Guest Notice amber・Action Border・Disabled surface・Badge/decorative neutral surface・Overlay・Debug/output dark surface）はliteralのまま維持し、「Blocked by Contract」と明記する。
- Stage 3は本Contract決定後も`PARTIAL_MIGRATION_ALLOWED`のまま進める。

## 関連文書

- `docs/design/design-token.md`（本決定を反映して更新）
- `docs/audit/design-token-stage3-neutral-semantic-decision.md`（Message-own/Selection決定、Sub-PR再設計の前提）

## 品質確認

- [x] 決定事項は全て母艦（Product判断）による確定であり、本文書側で独断していない
- [x] Group B（debug/output panel）・Group C（Overlay）をGroup A（Dark Surface候補）と混同していない
- [x] Group A内の実値不一致（slate-900 vs neutral-900）を本文書で機械的に統一していない
- [x] Mobile実値を本文書で独断決定していない
- [x] Token実値・最終命名は本文書で確定させず、実装PR側に委ねた
- [x] `git diff --check`
