> **Status: Reference**
>
> 本文書は、Design Token Migration Stage 3（`docs/design/design-token.md`のMigration方針 3. Recommendation画面適用）の着手前調査で発見した、中立色パレット（slate/gray/neutral/stone）の意味統合方針・未定義Semantic Token（own-message／selected-item）・Premium subtle ringのshade差について、調査事実と決定事項を記録する。
>
> 本文書はStage 3着手前の意思決定記録であり、Token名・実値の最終確定はこの後の実装PR（後述「Sub-PR再設計」）で行う。

# Design Token Stage 3 — 中立色統合方針・未定義Semantic Token決定

## 背景

`apps/web/src/features/concierge/`を対象としたStage 3のtoken適用監査で、低リスクと想定していたSub-PR A候補7ファイルが、いずれもslate以外の中立色パレット（neutral/gray/stone）を使用しており、既存の`tokens.css`のSemantic Token（border-default/text-primary等、いずれもslateベース）へ機械的に1:1置換できないことが判明した。これは`docs/design/design-token.md`が「保留事項」として明記していた中立色4系統（slate/stone/gray/neutral）の統合方針が未決定だったことに起因する。

あわせて、既存のSemantic Token体系に該当カテゴリが存在しない2箇所（チャット送信メッセージの背景色、リスト選択状態の色）と、Premium系トークンとの微小なshade差（`ring-amber-100` vs `--kt-color-premium-border: amber-200`）を発見した。

本文書はこれらの調査事実と、確定した決定事項を記録する。

## 調査事実

### 1. 中立色パレットの repo-wide 使用実態

`docs/audit/design-token-phase6-audit.md`（Status: Reference）の既存棚卸しを基礎とし、意味カテゴリ（TEXT/BORDER/SURFACE/DARK_SURFACE/DISABLED/INTERACTIVE/DECORATIVE）別にWeb（`apps/web/src`）全体を再調査した。

| パレット | 規模（phase6監査） | 主な意味カテゴリ |
|---|---|---|
| slate | 59ファイル・約400回 | TEXT（700/900）・BORDER（200/300）・SURFACE（50） |
| stone | 33ファイル・約400回 | TEXT/BORDER/SURFACE全般、INTERACTIVE(hover)の主力 |
| gray | 約90回 | 主にLogin/Signup等の旧フォーム系。DARK_SURFACE 1件（`MessageList.tsx:bg-gray-900`） |
| neutral | 約40回 | Concierge・共有`ConciergeCard.tsx`に散発。DARK_SURFACE複数件（`neutral-900/800`） |

**追加発見（DARK_SURFACEの repo横断的不統一）**: `bg-slate-900`（13箇所: billing各画面・`error.tsx`・`plan`・旧concierge debug UI）、`bg-gray-900`（`MessageList.tsx`）、`bg-neutral-900/800`（`ConciergeSectionsRenderer.tsx`・`components/ConciergeCard.tsx`）、`bg-stone-950`（`GoshuinDetailModal.tsx`・`tokens.css`自体）が、4つの異なるパレットで同じ「強調ダークサーフェス」役割を独立に実装していた。`MessageList.tsx`の送信メッセージ色は、チャット固有の概念ではなく、このrepo横断的な不統一パターンの一インスタンスであることを確認した。

### 2. own-message Semantic Tokenの要否

- Web: `bg-gray-900`（自分の発言バブル）
- Mobile: `apps/mobile/app/consultation-history/[id].tsx:379-384`の`messageBubbleUser`/`messageBubbleAssistant`は、専用色を持たず既存のSurface系（`theme.surfaceSoft`/`theme.surface`）を使い分けているのみ

### 3. selected-item Semantic Tokenの要否

- Web: `ThreadListItem.tsx`の`border-blue-500`/`bg-blue-50`（選択状態）
- Web内クロスチェック: 同じconcierge feature内の`OriginSelector.tsx`は、同じ「選択中」状態を既にemerald（`border-emerald-500 bg-emerald-50`、既存のAction Tokenと一致）で実装している。`ThreadListItem.tsx`のみblueを使用しており、Web内で選択状態の色表現が2系統に分裂していた
- Mobile: `apps/mobile/app/profile/index.tsx:222-224`の`chipSelected`は`borderColor: theme.gold`（Mobileの Action/Premiumブランド色）を使用。独立した選択専用色ではなく、既存のブランドAction色を再利用している

### 4. Premium subtle ring

`ring-amber-100`はrepo全体で`ModeBadge.tsx`の1箇所のみ（`ring-amber-*`使用は全体で2件、他方は文脈の異なる`OriginSelector.tsx`の`ring-amber-700`）。一方`--kt-color-premium-border`と一致する`border-amber-200`は13ファイルで反復使用される支配的パターン。

## 決定事項

母艦（Product判断）による確定。

| 項目 | 決定 |
|---|---|
| 中立色統合方針 | **Option B採用**: neutral/gray/stone/slateというpalette名をSemantic Token名にせず、意味（text-primary/secondary/muted, border-default, surface-default/subtle/emphasis, disabled, selected, message-own, premium-subtle）で分類し、実色差はPlatform Theme層で吸収する。Option A（slateへ機械統合）は見た目と意味を同時に潰すため不採用 |
| 移行時の暫定運用 | Option Cを移行中のFallbackとして許容する。既存Tokenで意味が一致する箇所は移行必須、Semantic Token未定義の箇所のみliteralを残してよい |
| own-message Semantic Token | **追加する**。候補名: `--kt-color-message-own-background`, `--kt-color-message-own-text`（実値・最終命名は実装PR側で確定）。根拠: gray-900は「濃いgray」ではなく「自分側メッセージ」という意味を持つため。Mobile側は既存Surfaceトークンの使い分けで表現しており独立トークンは持たないが、Web側で新設することを妨げない |
| selected-item Semantic Token | **追加する**。候補名: `--kt-color-selection-background`, `--kt-color-selection-border`, `--kt-color-selection-text`（実値・最終命名は実装PR側で確定）。`ThreadListItem.tsx`のblueをemeraldへ機械的に置換することはしない（意味の独断決定を避けるため、新規Selection Tokenとして切り出す） |
| premium subtle ring | **KEEP_LITERAL_FOR_NOW**。1箇所のみのため新規Token化を急がず、リテラル(`ring-amber-100`)のまま残す。複数箇所で同じ意味の使用が確認された時点で`--kt-color-premium-ring-subtle`を候補化する |
| Stage 3 スコープ | ディレクトリ基準（`apps/web/src/features/concierge/**`のみ）から、**Recommendation UI責務基準**へ再定義する。判定基準: (A) Recommendation画面の主要表示責務を持つ (B) Stage 3画面から直接使用される (C) Token未移行が画面全体の整合性に影響する。この基準により`components/ConciergeCard.tsx`（`PrimaryRecommendationCard.tsx`の委譲先で、Recommendation画面の主要カード表示責務を持つ）をStage 3スコープに含める |
| 部分移行の許容 | **PARTIAL_MIGRATION_ALLOWED**。Semantic Token未定義箇所のみliteral残存を許可する。既存Tokenで意味が一致する箇所は移行必須。残存箇所は「TODO」ではなく「Blocked by Contract」として明記する。Stage 3は本条件下でも「DONE」とは扱わない |

## Sub-PR再設計

前回（視覚リスク階層によるSub-PR A/B/C）の分割案は破棄し、以下の依存関係ベースの分類へ再設計する。

### PR-A: 既存Tokenでexact semantic matchできる箇所

新Token追加を待たずに着手可能。

- `ConciergeConsultationSummary.tsx`
- `ConciergeFilterPanel.tsx`
- `PremiumStateDeltaCard.tsx`
- `ModeBadge.tsx`（`ring-amber-100`はKEEP_LITERAL_FOR_NOWのためliteral残置＝Blocked by Contractと明記）
- `ConciergeSectionsRenderer.tsx`・`ConciergeTopRecommendationHero.tsx`のslate/emerald/amber部分（neutral-900等のDARK_SURFACE部分・`text-slate-950`部分は対象外、Blocked by Contractと明記）

### PR-B: 新Semantic Token追加後に移行できる箇所

`--kt-color-message-own-*`・`--kt-color-selection-*`の実装（`tokens.css`への追加）を前提PRとし、その後に以下を移行する。

- `MessageList.tsx`（own-message）
- `ThreadListItem.tsx`（selection）
- `ThreadList.tsx`（selection関連の可能性があるamber/premium部分はPR-A相当、`text-blue-600`のリンク色は別途Blocked by Contractとして記録し本PRの対象外）

中立色統合（Option B）の具体的なSemantic Token実装（`border-default`等が吸収する対象範囲の確定）も本PRの前提として必要。

- `BreakdownAccordion.tsx` / `MatchChips.tsx` / `NeedChips.tsx` / `DirectionReferenceCard.tsx` / `ChatInput.tsx` / `ChatPanel.tsx` / `ConciergeLayout.tsx` / `OriginSelector.tsx`（stone部分）

### PR-C: 主要Recommendation UI

画面の第一印象・複雑度が高く、最も慎重な視覚QAが必要な範囲。PR-A/PR-Bで確立したToken適用パターンを踏まえた上で最後に着手する。

- `ConciergeEntryCard.tsx`
- `ConciergeSectionsRenderer.tsx`（残り部分）
- `ConciergeTopRecommendationHero.tsx`（残り部分）
- `components/ConciergeCard.tsx`（Stage 3スコープ再定義により新規追加、`PrimaryRecommendationCard.tsx`の委譲先）

`ChatInput.tsx`の送信ボタン（`bg-indigo-500`）は、中立色問題とは別に、確立済みのAction Token（emerald）とのブランド不整合であることも判明している。この扱いは中立色統合とは別軸のProduct判断が必要であり、本文書の決定範囲には含めない。PR-B着手時に別途確認する。

## 関連文書

- `docs/design/design-token.md`（本決定を反映して更新）
- `docs/audit/design-token-phase6-audit.md`（本調査の基礎データ）

## 品質確認

- [x] 決定事項は全て母艦（Product判断）による確定であり、本文書側で独断していない
- [x] Token実値・最終命名は本文書で確定させず、実装PR側に委ねた
- [x] `git diff --check`
