> **Status: Reference**
>
> 本文書は、Stage 4（Shrine Detail）Design Token移行の着手前調査で発見した4カテゴリ（Saved/Favorite・Dark Surface hover方向差・Light Surface 100系・Rose palette）について、母艦（Product判断）による正式決定を記録する。
>
> 本文書は決定記録である。ただし各Tokenの実値・最終命名はここでは確定させず、実装PR（PR-D1/D2/D3）側で確定する。

# Design Token Stage 4 — Mother Ship Decisions

## 背景

`docs/audit/design-token-stage3-residual-contract.md`のStage 4 Handoff節が予告した通り、Stage 4スコープの初期調査（Shrine Detail Inventory Audit）で、Stage 3から持ち越された既知カテゴリ（Dark Surface、Light Surface 100系）の再出現に加え、Stage 4固有の新規カテゴリ（Saved/Favorite、Rose palette）を発見した。本文書はこれら4カテゴリについて母艦が下した決定を記録する。

## Decision 1: Saved / Favorite

### 調査事実

- `ShrineSaveButton.tsx`の`fav`状態は非同期save/unsave処理（`busy`状態・エラーハンドリングを伴う）を経てサーバー側に永続化される。画面遷移をまたいで保持される点で、選択肢の中から一時的に選ぶSelectionとは性質が異なる（`docs/audit/design-token-selection-divergence-decision.md`で既に指摘済み）。
- Status successとの違い: `--kt-color-status-success`系トークンは「操作が成功した」という一時的な結果通知の意味で設計されている（`docs/design/design-token.md`のStatusカテゴリ定義）。Savedは「現在保存済みという永続的な状態」であり、値（emerald系）が近くても意味が異なる。
- Actionとの違い: Save/Unsaveのトリガーとなるボタン自体はAction相当だが、「現在保存されているかどうか」を表す視覚状態（背景・境界・文字色）はActionの範囲外。
- repo-wideの再利用実態: `favorite`/`isFavorite`/`favorite_id`/`toggleFav`相当のUIは`ShrineSaveButton.tsx`以外に少なくとも`apps/web/src/app/ranking/page.tsx`、`apps/web/src/features/mypage/components/FavoritesSection.tsx`、`apps/web/src/components/shrines/ShrineCard.tsx`、`apps/web/src/components/shrines/ShrineCardLite.tsx`、`apps/web/src/components/shrines/ShrineConciergeCard.tsx`で確認した（6箇所以上）。Stage 3で確認したGuest Notice（2箇所）・Disabledパターン（1ファイル内2箇所）より明確に強い再利用根拠である。
- `ShrineSaveButton.tsx`のon/off状態（2 variant）:

| variant | fav=true | fav=false |
|---|---|---|
| `subtle` | `border-emerald-200 bg-emerald-50 text-emerald-700` | `border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-muted)] hover:bg-slate-50 hover:text-slate-700` |
| default | `border-emerald-300 bg-emerald-50 text-emerald-700` | `border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)] hover:bg-slate-50` |

fav=falseは既にToken化済み。fav=true（saved状態）のみliteralが残存している。

### 決定

**`SAVED_FAVORITE_SEMANTIC_REQUIRED`**。Saved/Favoriteを独立したSemantic categoryとして新設する。SelectionまたはStatusへの統合は行わない。

候補名（実値・最終命名は実装PRで確定）:

- `color.saved.background`
- `color.saved.border`
- `color.saved.text`
- `color.saved.hover`

Web実装候補: `--kt-color-saved-background` / `--kt-color-saved-border` / `--kt-color-saved-text` / `--kt-color-saved-hover`

実値は`ShrineSaveButton.tsx`のfav=true状態（`emerald-200`/`emerald-300`のborder差はvariant別、bg=`emerald-50`、text=`emerald-700`）を起点に、実装PR側で確定する。現行visualを変えない。

## Decision 2: Dark Surface Hover Direction

### 調査事実

- `--kt-color-surface-emphasis`（`slate-800`）/ `--kt-color-surface-emphasis-hover`（`slate-900`）は、rest状態が明るく・hover状態が暗くなる方向（`ConciergeEntryCard.tsx`のログインボタンに由来）。
- `ShrineDetailShell.tsx`の参拝ルートCTA（`bg-slate-900 hover:bg-slate-800`）は同じslateパレットを使うが、rest状態が暗く・hover状態が明るくなる、逆方向の関係である。
- computed color実測（`lab()`値）でも、restのlightnessが異なる（`surface-emphasis`のrest=L16.1 vs `ShrineDetailShell.tsx`のrest=L7.8）ため、単純なToken差し替えは視覚変更を伴う。
- 同じ現象は`ConciergeCard.tsx`（`bg-neutral-900 hover:bg-neutral-800`、Stage 3で確認済み）でも発生しており、hover方向の不一致はパレット（slate/neutral）を問わず repo横断で起きている。

### 決定

既存`surface-emphasis`への無理な統合は行わない。hover方向（どちらが暗くどちらが明るいか）もSemanticの一部として扱う。Stage 4ではvisual equivalenceを優先し、exact matchしないdark CTAはliteralのまま維持する。新しいvariant Tokenの追加は今回行わない。

**判定: `DARK_SURFACE_VARIANT_DEFERRED`**

## Decision 3: Light Surface 100系

### 調査事実

Stage 3の`docs/audit/design-token-stage3-residual-contract.md`が確認したhover/disabled/badge・pill/decorativeの4用途分離は、Stage 4スコープ（`PublicGoshuinSection.tsx`の`bg-slate-100`）でも同じ形で再確認された。新しい用途や、単一Semanticへ統合できる根拠の追加は今回のStage 4監査では見つかっていない。

### 決定

引き続き`KEEP_LITERAL_FOR_NOW`。`background-subtle`への統合は行わない。1つのSemanticへまとめない。Stage 4進行中に新しい再利用根拠（同一用途が複数箇所で確認される等）が増えた場合のみ再評価する。

**判定: `LIGHT_SURFACE_100_KEEP_LITERAL`**

## Decision 4: Rose Palette

### 調査事実

`ShrineDetailArticle.tsx`・`ShrineReflectionPrompt.tsx`のrose系使用箇所を全件確認した。

| 箇所 | 内容 | 条件 |
|---|---|---|
| `ShrineReflectionPrompt.tsx:126` | `text-rose-700`「振り返りの保存に失敗しました。」 | `status === "error"` |
| `ShrineDetailArticle.tsx:716-717` | `border-rose-200`＋`text-rose-700`「参拝記録に失敗しました」 | `visitError`真値時のみ表示 |

両箇所とも、装飾・強調・コンテンツ分類ではなく、明確な**エラー状態の表示**である（`status === "error"`および`visitError`という状態変化に連動して条件表示される）。

### 決定

**`EXISTING_STATUS_MATCH`**（text部分のみ）。roseはpalette名が近いという理由ではなく、意味が既存Status Error（`--kt-color-status-error`、`red-600`系）と一致することを確認した上での判断である。

ただし現在`--kt-color-status-error`はtext用の単一値のみが定義されており、`border`/`surface`に対応するstatus-errorファミリーは存在しない（`status-success`系には`-text`/`-surface`/`-border`が揃っているが、`status-error`にはない）。したがって:

- `text-rose-700` → `--kt-color-status-error`が意味的に対応する（実装PR側でException適用）
- `border-rose-200` → 対応する`status-error`系トークンが存在しないため、現時点では`NO_CHANGE_NEEDED`（架空の一致を避けるため、border用のstatus-errorトークンをここで新設はしない）

palette名（rose）だけを理由にした機械的なStatus統合ではないことを明記する。

## Stage 3 Decisionとの連続性

- Decision 1（Saved/Favorite）は、`docs/audit/design-token-selection-divergence-decision.md`が「`ShrineSaveButton.tsx`のfavorite状態をSelection Emeraldクラスタへ機械的に含めない」とした判断を継承し、正式に別責務として独立させた
- Decision 2（Dark Surface）は、`docs/audit/design-token-stage3-dark-surface-decision.md`が「Group A内の実値不一致を機械的に統一しない」とした方針を継承し、hover方向という新しい不一致軸を追加で確認した
- Decision 3（Light Surface 100系）は、`docs/audit/design-token-stage3-residual-contract.md`のKEEP_LITERAL_FOR_NOW判断をStage 4スコープでも維持する
- Decision 4（Rose）は、Stage 3では確認されていなかった新規カテゴリであり、既存Statusカテゴリの定義（`docs/design/design-token.md`のColorカテゴリ表、Status行）とexact matchで検証した

## Stage 4 Implementation Boundaries

- 本文書はDecision 1〜4を確定するが、いずれもToken実値・最終命名は実装PR側で確定する
- PR-D1（低リスク・exact match）はSaved/Favorite・Dark Surface variant・Light Surface 100系・rose未確定箇所を含まない
- PR-D2（interactive state）はSaved/Favorite Contract（本文書）確定後に着手し、`--kt-color-saved-*`の実装を含む
- PR-D3（shared/high-visibility）はPR-D1のToken適用パターン実証、PR-D2のSaved/Favorite責務確定後に着手する

## Stop Conditions（Stage 4実装全体で維持）

- Saved/FavoriteとSelectionの意味が混ざる
- roseをpalette名だけの理由でStatusへ押し込む必要が出る
- dark hover方向を変更しないとToken化できない
- Light Surface 100系を統合しないと進められない
- shared componentの変更で他画面のvisualが変わる
- 既存Tokenで1:1表現できない
- 上記以外でProduct判断が必要になる

該当時は実装を停止し、母艦へ差し戻す。

## 関連文書

- `docs/design/design-token.md`（正本）
- `docs/audit/design-token-stage3-neutral-semantic-decision.md`
- `docs/audit/design-token-stage3-dark-surface-decision.md`
- `docs/audit/design-token-stage3-residual-contract.md`
- `docs/audit/design-token-selection-divergence-decision.md`

## 品質確認

- [x] Decision 1〜4は母艦による正式決定として記録した
- [x] Token実値・最終命名は確定していない
- [x] Component・`tokens.css`の変更は行っていない
- [x] Stage 3の既存Decisionと矛盾しない
- [x] roseをpalette名だけでStatusへ機械統合していない（text/borderで扱いを分けた）
- [x] `git diff --check`
