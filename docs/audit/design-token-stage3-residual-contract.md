> **Status: Reference**
>
> 本文書は、Design Token Migration Stage 3（`docs/design/design-token.md`のMigration方針 3. Recommendation画面適用）のPR-A/PR-B/PR-C1/PR-C2/PR-C3完了時点で残存する未決定カテゴリを一覧化し、各カテゴリの調査事実・候補案・判断材料を記録する。
>
> 本文書は決定記録ではない。各Phaseの「確認」項目は判断材料の提示に留め、Token実値・命名・Contract化の可否はいずれも母艦（Product判断）に委ねる。本文書の作成をもってどの項目も独断で確定しない。

# Design Token Stage 3 — Residual Contract（残存カテゴリ一覧）

## 背景

PR #2282（中立色統合方針・Message-own/Selection決定）、PR #2283（PR-A）、PR #2284（PR-B）、PR #2285（Dark Surface Contract）、PR #2286〜#2288（PR-C1/C2/C3）は全てmerge済みであり、Stage 3の対象範囲（Recommendation UI: `ConciergeEntryCard.tsx` / `ConciergeSectionsRenderer.tsx` / `ConciergeTopRecommendationHero.tsx` / `ConciergeCard.tsx` / `MessageList.tsx` / `ThreadListItem.tsx` / PR-A対象4ファイル）で既存Semantic Tokenとexact matchできる箇所は全て移行済みである。

`docs/design/design-token.md`・`docs/audit/design-token-stage3-neutral-semantic-decision.md`は、部分移行を`PARTIAL_MIGRATION_ALLOWED`として明示的に許容しつつ、「残存箇所は「TODO」ではなく「Blocked by Contract」として明記し、対象Migration PRは「DONE」と扱わない」と定めている。本文書はこの原則に従い、Stage 3を`STAGE3_PARTIALLY_DONE`として固定した上で、残る各カテゴリを次の実装（Stage 3の追加PRまたはStage 4）が同じ調査を繰り返さずに済むよう整理する。

## Phase 1 — Stage 3 Closure Snapshot

- PR-A（#2283）、PR-B（#2284）、Dark Surface Contract（#2285）、PR-C1（#2286）、PR-C2（#2287）、PR-C3（#2288）は全てmerge済み
- 既存Semantic Tokenでexact matchできる箇所（text-primary/secondary/muted、action-primary系、surface-default、background-subtle、border-default/strong、radius-*、shadow-medium/high、message-own系、selection系、surface-emphasis系）は対象5ファイル＋PR-A対象4ファイルで移行済み
- 残存literalは全て下記Phase 2〜8のいずれかのカテゴリに分類済みであり、「原因不明の取りこぼし」は次項Phase 7の1件（`ConciergeFilterPanel.tsx`）を除き確認されていない

## Phase 2 — Dark Surface Contract v2（判断材料）

### 調査事実

`--kt-color-surface-emphasis`（`slate-800`）/ `--kt-color-surface-emphasis-hover`（`slate-900`）は`ConciergeEntryCard.tsx`のログインボタン1箇所から値を採った。この値は他のGroup A（強調CTA）箇所とcomputed colorで一致しないことを実測済み（PR #2287・#2288で確認）。

repo横断のGroup A箇所を実測ベースで2クラスタに分類できる:

| クラスタ | 該当箇所 | 特徴 |
|---|---|---|
| slate系 | billing各画面（13箇所超）・`error.tsx`・`PlanView.tsx`・`ConciergeEntryCard.tsx`・`ConciergeClientFull.tsx`のLink・`ShrineDetailShell.tsx` | `lab()`のa/b軸が非0（わずかに青みがかった灰色） |
| neutral系 | `ConciergeSectionsRenderer.tsx`・`components/ConciergeCard.tsx` | `lab()`のa/b軸がほぼ0（無彩色に近い灰色） |

lightness（L値）はどちらのクラスタも近い値（L≈7.8前後）だが、色相（a/b軸）が明確に異なる。単純な「shadeの誤差」ではなく、パレット由来の系統的な色相差である。

### 判断材料（候補案、いずれも未決定）

1. **PLATFORM_THEME_VARIANT_REQUIRED**: 本プロジェクトの3層構造（Primitive/Semantic/Platform Theme）における「Platform Theme」はWeb/Mobile（および将来のlight/dark）の差を吸収する層として定義されている（`docs/design/design-token.md`「3層構造」節）。Web内の2コンポーネント間の差をPlatform Themeとして扱うのは、この定義の拡張を伴う。採用する場合はPlatform Themeの定義自体を見直すドキュメント変更が別途必要になる。
2. **MULTIPLE_SEMANTIC_VARIANTS_REQUIRED**: `color.surface.emphasis`とは別に、neutral系クラスタ用の第2 Variant（例: `color.surface.emphasis.neutral`）を新設する。実測で2クラスタが明確に分離しているため、値の面では最も無理のない選択肢だが、新Token追加を意味する。
3. **KEEP_PARTIAL_MIGRATION**: neutral系クラスタは今後もliteralのまま維持することを正式に認め、`surface-emphasis`はslate系クラスタ専用Tokenとして運用を続ける。新規Token追加を伴わない。

### 禁止事項（本文書内で遵守）

- 現行`--kt-color-surface-emphasis`/`-hover`の値は変更していない
- neutral→slateの機械統合は行っていない

## Phase 3 — Light Surface 100系（判断材料）

### 調査事実（用途別）

| 用途 | 該当箇所 | 例 |
|---|---|---|
| hover | `ConciergeEntryCard.tsx`（`hover:bg-stone-100`、`hover:bg-stone-100/30`×2）、`ConciergeSectionsRenderer.tsx`（`hover:bg-slate-100`） | ボタン・リンクのhover背景 |
| disabled | `ConciergeEntryCard.tsx`（`disabled:bg-stone-100`×2） | Phase 5参照 |
| badge/pill | `ConciergeSectionsRenderer.tsx`（`bg-slate-100`、trust label badge）、`ConciergeCard.tsx`（`bg-neutral-100/80`、バッジ背景） | タグ・ラベルの背景 |
| decorative | `ConciergeCard.tsx`（`bg-neutral-100`、icon-mark circle背景、および`from-neutral-100`画像プレースホルダのgradient起点） | 装飾要素の背景 |

### 判断材料

- 4用途（hover/disabled/badge/decorative）は同一パレット・同一shade（100番台）だが機能的責務が異なる。1つのSemantic Token（例: `color.surface.subtle.100`）に統合すると、Component側は「同じ意味だから同じToken」という前提で読むことになるが、実際には「hoverの一時的強調」「badge/pillの恒常的チップ背景」「純粋な装飾」という異なる意味を1つのTokenに押し込むことになる
- 一方、4つ全てを個別Token化するのはStage 3のスコープに対して過大（新Token 4個は「今回はtoken増やしすぎない」というPR-C2以降の方針と衝突する）
- 現時点でPR-C1〜C3はいずれも本カテゴリを`KEEP_LITERAL_FOR_NOW`として扱っており、これを正式方針として明文化するかどうかが本Phaseの論点

## Phase 4 — Guest Notice（判断材料）

### 調査事実

`ConciergeEntryCard.tsx`の未ログイン案内バナー（`border-amber-200/50 bg-amber-50/50 text-amber-800`）は、repo内で確認できる唯一の「Notice（警告・注意喚起、Premiumではない）」用途のamber使用である。`ConciergeSectionsRenderer.tsx`の`conciergeNoticeCardClass`（`border-amber-200 bg-amber-50`）も同じ「Notice≠Premium」責務だが、こちらは既にradius/shadowのみToken化され、color部分は同じ理由でliteral維持されている（該当コード内コメントで既に明記済み）。

Premiumではないことは、`ConciergeSectionsRenderer.tsx`の既存コードコメント（「本カードの意味は『Notice(警告・注意喚起)』でありPremiumではないため、意味の異なるTokenを流用しないよう非適用とする」）で確認済み。

### 判断材料

- 単一の意味カテゴリ（Notice）が repo内2箇所（`ConciergeEntryCard.tsx`・`ConciergeSectionsRenderer.tsx`）で色として重複使用されている。`Premium subtle ring`（`ring-amber-100`）の先例では「1箇所のみ」を理由に`KEEP_LITERAL_FOR_NOW`としたが、Noticeは既に2箇所で同じ値・同じ意味の重複が確認できており、先例の閾値（複数箇所での同一意味使用）に近い、または既に満たしている可能性がある
- Token化する場合の候補: `color.notice.warning.surface` / `color.notice.warning.border` / `color.notice.warning.text`

## Phase 5 — Disabled（判断材料）

### 調査事実

`ConciergeEntryCard.tsx`内で、`disabled:border-stone-200 disabled:bg-stone-100 disabled:text-stone-400`という3値セットが、テーマ選択チップ（157行目）とクリアボタン（183行目）の2箇所で完全に同一の組み合わせとして重複している。

### 判断材料

- 3値セット（surface/text/border）が2箇所で文字列レベルで一致しており、Eyebrowカテゴリ（Phase 6監査で8ファイル完全一致により最優先Token化候補とされた前例）と同種の「既に実質的な共通パターンとして存在する」根拠がある
- 一方、対象範囲はPR-C1（`ConciergeEntryCard.tsx`）1ファイル内に閉じており、他のPR-C対象ファイルに同種のdisabled 3点セットは確認されていない
- `color.disabled.surface` / `color.disabled.text` / `color.disabled.border`を独立Semanticとして新設するかどうかは、「1ファイル内の重複で十分か、複数ファイルでの重複を待つか」という閾値判断に帰着する

## Phase 6 — Action Border（判断材料）

### 調査事実

| 箇所 | 内容 |
|---|---|
| `ConciergeEntryCard.tsx:174` | `border-emerald-300 bg-emerald-50/50 text-emerald-800`（送信ボタン、outlineスタイル） |
| `ConciergeFilterPanel.tsx:181,214` | `border-emerald-600 bg-emerald-50`（タグ選択ボタン、outlineスタイル、×2箇所） |

いずれも「borderの色値がAction Token（`action-primary`=emerald-600、`border-focus`=emerald-300）と数値上一致するが、bgは異なる値（emerald-50等）」という、backgroundと同一値でないborder用途である。これは`ConciergeSectionsRenderer.tsx`で既にToken化済みの`border-emerald-600`（プリセットボタン、`bg-emerald-600`と同一値で「同一要素の塗りと縁が同じ色」というケース）とは性質が異なる。

### 判断材料

- `action-primary`をborder色として流用しない、`border-focus`をこの用途に流用しない、という既存方針（PR-C1〜C3で維持）は本Phaseでも維持する
- 新設候補: `color.action.primary.border`相当。ただし「塗りと縁が同一値のケース」（既にToken化済み）と「outlineスタイルでborderのみemerald」という2つの異なる責務がある可能性があり、1つのTokenで両方を表現してよいかは未検証
- 該当箇所は2ファイル・3インスタンスで、閾値としては中程度（Guest Noticeの2箇所よりやや多い、Eyebrowの8ファイルよりは少ない）

## Phase 7 — Accidental Remainder再確認

`ConciergeFilterPanel.tsx:181,214`の`border-emerald-600 bg-emerald-50`を再確認した。

**分類: `ACCIDENTAL_REMAINDER`**

理由:
- 本箇所を「意図的にBlocked by Contractとして残す」と明記したコードコメント・PR本文は存在しない
- `ConciergeFilterPanel.tsx`はPR-A（#2283）で一度Token化されているが、Dark Surface Contract以降のPR-C系の監査対象には含まれておらず、Action Borderという概念自体がPR-C1（#2286）以降に確立されたため、PR-A時点ではこの箇所が「Action Border」という名前のカテゴリに属することが認識されていなかったと考えられる
- `BLOCKED_BY_CONTRACT`ではない（明示的な決定文書上の言及がない）。`NO_SEMANTIC_MATCH`でもない（Phase 6で述べた通り、既存Action Tokenと値は一致しており、意味上の候補は存在する。ただし責務混同を避けるため現時点では未適用というのが正確な状態）

今回コードは修正しない。Action Border（Phase 6）の判断が下った場合に、本箇所も同時に対応することを推奨する。

## Phase 8 — Other Residuals（判断材料）

| カテゴリ | 該当箇所 | 再利用根拠 | 判断材料 |
|---|---|---|---|
| teal palette | `ConciergeTopRecommendationHero.tsx`（`border-teal-100`/`bg-teal-50/70`/`text-teal-700`、×2セット） | Hero内1ファイルに閉じる、他箇所での使用は未確認 | 根拠弱、`KEEP_LITERAL_FOR_NOW`が妥当な候補 |
| colored shadow pair | `ConciergeTopRecommendationHero.tsx`の`shadow-{size} shadow-{color}/{alpha}`全箇所（約6インスタンス） | Hero内のブランド別カード演出に紐づく、汎用化の要求は未確認。加えて`shadow-[var(--kt-shadow-X)]`へ置換すると`shadow-{color}`修飾との結合が崩れる技術的リスクも既に確認済み（PR #2287） | 根拠弱、technical riskもあるため`KEEP_LITERAL_FOR_NOW`が妥当な候補 |
| alpha surface | 全5ファイル横断で数十インスタンス（`bg-*-50/NN`、`border-*-200/NN`等） | 出現数は非常に多いが、ブロック理由は「意味不明」ではなく「`[var(--kt-color-x)]/NN`というarbitrary value + alpha修飾の組み合わせをこのリポジトリで検証した前例がない」という技術的検証課題である | 値決定の論点ではなく、Tailwind v4での動作検証が先に必要。検証が取れれば多数箇所が一括で解放される可能性がある |
| border-slate-100 | `ConciergeTopRecommendationHero.tsx`（×2） | Hero内1ファイルに閉じる。既存`border-default`(200)/`border-strong`(300)のどちらとも値が異なる中間shade | 根拠弱、`KEEP_LITERAL_FOR_NOW`が妥当な候補。複数ファイルでの再利用が確認されれば`color.border.subtle`相当を候補化 |

## Phase 9 — Stage 3 Exit Contract（判断材料）

### 候補A: `STAGE3_DONE_WITH_DOCUMENTED_LITERAL_EXCEPTIONS`

採用するには、`docs/design/design-token.md`・`docs/audit/design-token-stage3-neutral-semantic-decision.md`が明文化している既存ルール（「残存箇所は…Blocked by Contractとして明記し、対象Migration PRは『DONE』と扱わない」）そのものを改定する必要がある。これは個々のToken値・カテゴリの決定より上位の、Stage 3全体の完了基準（Governance）の変更であり、本文書はこれを提案するに留め、決定はしない。

改定する場合の代替DONE条件案（例、未決定）: 「未Token化のliteralが0件」ではなく「残存literaが全てPhase 2〜8のいずれかのカテゴリに分類され、BLOCKED_BY_CONTRACT／KEEP_LITERAL_FOR_NOW／NO_SEMANTIC_MATCHのいずれかとして文書化されていること」。本文書のPhase 1〜8は、この代替条件を採用する場合の材料として機能する。

### 候補B: `STAGE3_PARTIALLY_DONE`

既存の明文化されたルールをそのまま適用する。追加のGovernance変更を必要としない。前回監査（本文書と同一セッション内の直前ターン）で採用した状態と同じ。

### 本文書の立場

どちらを採用するかはGovernance変更を伴う判断であり、母艦の決定を要する。本文書はA/B双方の判断材料を提示するに留め、確定しない。

## Phase 10 — Stage 4 Handoff

Stage 4（Shrine Detail、`docs/design/design-token.md`のMigration方針 4.）着手時に、以下は既存決定として再利用可能（同じProduct判断を再実施しない）:

- **確定済みSemantic Token**: text（primary/secondary/muted/inverse）、border（default/strong/focus）、surface（default/elevated/background-subtle）、action（primary/hover/text/disabled）、premium（accent/surface/border）、status（success/warning/error/info）、message-own、selection、surface-emphasis（ただしPhase 2の通りGroup A全体はカバーしない）
- **確定済み方針**: 中立色統合Option B、`PARTIAL_MIGRATION_ALLOWED`、Blocked by Contract表記ルール

Stage 4側で改めて調査・判断が必要な、Stage 3で未解決のまま残るカテゴリ（本文書Phase 2〜8がそのまま該当）:

- Dark Surface Group A の2クラスタ問題（Stage 4にも同様のdark CTAパターンが存在する可能性がある。`docs/audit/design-token-phase6-audit.md`の当初調査でも billing/error等Recommendation外の画面が既に混在している）
- Light Surface 100系
- Guest Notice / warning系
- Disabled surface/text/border
- Action Border
- teal palette・colored shadow pair・alpha surface（技術検証）・border-slate-100

Stage 4のスコープ確定時に、上記カテゴリで新たにShrine Detail画面固有のインスタンスが見つかった場合は、本文書の該当Phaseへ追記する形で一元管理することを推奨する（Stage 4側で同じ調査を独立に行わない）。

## 関連文書

- `docs/design/design-token.md`（正本）
- `docs/audit/design-token-stage3-neutral-semantic-decision.md`
- `docs/audit/design-token-stage3-dark-surface-decision.md`

## 品質確認

- [x] 決定事項は含まない。全項目を判断材料として提示した
- [x] 既存Contract（中立色統合Option B、Dark Surface Group A限定方針、Message-own/Selection方針）と矛盾する記述はない
- [x] Component・`tokens.css`への変更は行っていない
- [x] `git diff --check`
