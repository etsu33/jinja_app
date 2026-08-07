> **Status: Reference**
>
> 本文書は、Stage 4 D3（Shrine Detail残存component群）着手前調査で発見した4件の判断事項（`FAVORITE_LABELS.saved`のsaved-text適用可否、Reflection成功文言のshade差、Emerald Tag/Chipパターン、Reflection送信ボタンのshade差）について、母艦（Product判断）による正式決定を記録する。
>
> あわせてD3の実装分割（D3-1/D3-2）とD3-1の実装ルールを記録する。本文書は決定記録であり、Component・`tokens.css`の変更は含まない。実装は別PR（D3-1）で行う。

# Design Token Stage 4 D3 — Semantic Decisions

## 背景

`docs/audit/design-token-stage4-mother-ship-decisions.md`（PR #2292）は、Stage 4着手前に発見した4カテゴリ（Saved/Favorite・Dark Surface hover方向差・Light Surface 100系・Rose palette）を決定した。PR-D1（#2293）・PR-D2（#2294）でこれらのうちSaved/FavoriteのToken基盤（`--kt-color-saved-background`/`-text`/`-border`）を導入した後、D3対象component群の監査で、既存Contractではカバーされない4件の新規論点を発見した。本文書はこれらを決定する。

## Decision 1: `FAVORITE_LABELS.saved`（`ShrineDetailArticle.tsx`）

### 調査事実

- `ShrineDetailArticle.tsx`が`{FAVORITE_LABELS.saved}`を`text-emerald-700`で表示している（`ShrineSaveButton.tsx`のフックを直接呼ばず、渡された状態を表示するのみ）。
- 表示内容はSaved/Favoriteの永続的な状態を表すラベルであり、一時的な成功通知（transient success）ではない。
- Selection responsibility（`docs/audit/design-token-selection-divergence-decision.md`）とも異なる。
- `--kt-color-saved-text`は`emerald-700`であり、値が完全一致する。

### 決定: `SAVED_TEXT_EXACT_MATCH`

`--kt-color-saved-text`を`ShrineDetailArticle.tsx`の当該表示テキストへ適用してよい。`--kt-color-saved-text`はボタン専用Tokenとして限定せず、Saved/Favorite状態を示す表示テキスト全般に利用可能とする。

## Decision 2: Reflection成功文言（`ShrineReflectionPrompt.tsx`、`status === "saved"`）

### 調査事実

- 振り返り保存成功時に表示される一時的なfeedbackメッセージ（`status === "saved"`）が`text-emerald-700`を使用している。
- 意味はStatus Success責務と一致する（一時的な成功通知）が、既存`--kt-color-status-success-text`は`emerald-800`であり、実値が一致しない（`emerald-700` vs `emerald-800`）。
- Saved/Favoriteの永続状態（Decision 1）とは責務が異なる。

### 決定: `STATUS_SUCCESS_SHADE_GAP_KEEP_LITERAL`

`status-success-text`への強制置換は行わない。Option B（意味が同じなら実色差をPlatform Theme層で吸収する）を根拠に色差を機械的に潰さない。新しいStatus Success variant Tokenも今回は追加しない。`text-emerald-700`はliteralのまま維持する。

## Decision 3: Emerald Tag / Chip パターン

### 調査事実

`bg-emerald-50 text-emerald-700`の組み合わせが、`ShrineSupplementSection.tsx`（1箇所）・`ShrineDetailArticle.tsx`（2箇所）の計3箇所で、Saved/Favoriteとは無関係な汎用タグ・チップ表示として確認された。SavedでもStatusでもSelectionでもない。

### 決定: `TAG_CHIP_CONTRACT_CANDIDATE`（ただし今回は`KEEP_LITERAL_FOR_NOW`）

再利用根拠（3箇所）は確認できたが、Stage 4 D3の途中で新しいComponent/Semantic体系（Badge/Tag）を増設する判断は行わない。`docs/design/design-token.md`のComponent Token優先順位でもBadge/TagはP1領域として別途整理される予定であり、そちらのTrackでまとめて扱う方が適切と判断した。今回は3箇所ともliteralのまま維持する。

## Decision 4: Reflection送信ボタン（`ShrineReflectionPrompt.tsx`、`bg-emerald-700 hover:bg-emerald-800`）

### 調査事実

- 振り返り送信ボタンがAction CTA責務でありながら、既存`--kt-color-action-primary`（`emerald-600`）/`--kt-color-action-primary-hover`（`emerald-700`）より1 shade濃い値（`emerald-700`/`emerald-800`）を使用している。
- exact matchではない。

### 決定: `ACTION_VARIANT_KEEP_LITERAL_FOR_NOW`

`action-primary`への寄せ替えは行わない。`action-strong`等の新variant Tokenも今回は追加しない。Product側が意図して設計した視覚的階層（通常のAction Primaryより強調した送信ボタン）である可能性があるため、literalのまま維持する。

## D3 Split（正式採用）

**`SPLIT_BY_COMPONENT_RESPONSIBILITY`**

### D3-1: Exact Match Closure

以下の既存Semantic Tokenとexact matchする箇所のみを対象とする。

- `ShrineDetailShell.tsx`: `hover:bg-slate-50`のみ（`background-subtle`）
- `ShrineCloseLink.tsx`: `text-slate-700`のみ（`text-secondary`）
- `DetailDisclosureBlock.tsx`: `hover:bg-slate-50`のみ（`background-subtle`）
- `ShrineActionSection.tsx`: exact match可能な残存箇所
- `ShrineDetailArticle.tsx`: `FAVORITE_LABELS.saved`表示テキストのみ（`saved-text`、Decision 1）

変更しないもの: Dark Surface（`ShrineDetailShell.tsx`のCTA）、Light Surface 100系、amber hover、emerald Tag/Chip（Decision 3）、`ShrineReflectionPrompt.tsx`全体（Decision 2・4）、`ShrineDetailArticle.tsx`の`border-emerald-200`クラスタのその他スタイル。

### D3-2: Deferred / High-risk

以下は今回実装しない。

- `ShrineReflectionPrompt.tsx`（Decision 2・4が共にliteral維持のため、当面変更対象なし）
- `ShrineDetailArticle.tsx`の残存クラスタ（`border-emerald-200`まわりの装飾スタイル）
- `ShrineSupplementSection.tsx`（Decision 3によりliteral維持）
- `ShrineJudgeSection.tsx`（item-key駆動の5variant、既存Tokenとexact matchする箇所が現状ない）

## D3-1 Implementation Rules

変更可能: 既存Semantic Tokenへの置換のみ（`saved-text`のexact match、既存radius/shadowのexact match）。

禁止: `tokens.css`変更、新Semantic Token追加、`status-success-text`へのshade違い置換、`action-primary`へのshade違い置換、Tag/Chip Token新設、Dark Surface変更、Light Surface 100変更、Copy変更、state logic変更、API変更、Analytics変更。

## Stage 3/既存Contractとの連続性

- Decision 1は`docs/audit/design-token-stage4-mother-ship-decisions.md`のSaved/Favorite Decisionを継承し、適用範囲を「ボタン限定」から「Saved/Favorite状態を示す表示テキスト全般」へ明確化した
- Decision 2・4は、既存Option B方針（`docs/audit/design-token-stage3-neutral-semantic-decision.md`）を「意味が同じなら実色差を無条件に吸収する」ものとして拡大解釈しないことを確認した事例である
- Decision 3は、`docs/design/design-token.md`のComponent Token優先順位（P1: Badge/Tag）と整合させ、Stage 4のスコープ外として明示的に切り離した

## 関連文書

- `docs/design/design-token.md`（正本）
- `docs/audit/design-token-stage4-mother-ship-decisions.md`
- `docs/audit/design-token-selection-divergence-decision.md`

## 品質確認

- [x] Decision 1〜4は母艦による正式決定として記録した
- [x] Decision 2・4はOption Bの拡大解釈による機械的な色統合を行っていない
- [x] Decision 3は新Semantic Token・新Component体系を今回追加していない
- [x] D3-1/D3-2のスコープに重複がない
- [x] Component・`tokens.css`の変更は行っていない（実装は別PR）
- [x] `git diff --check`
