> **Status: Reference**
>
> 本ドキュメントは、Concierge結果画面のCard Tree、Props、Renderer、Visibility State別の表示原則およびSection Routingの責務を整理した設計補足資料である。`docs/product/card-visibility-renderer-split.md`（Archive）の内容を統合済み。
>
> 現行の表示構造と物理実装は、関連するFrontend実装およびテストを最終的な正本とする。

# Concierge Card Architecture

最終更新: 2026-05-18  
対象: Concierge 結果画面 / ConciergeSectionsRenderer / card routing

---

## 目的

本ドキュメントは、Concierge 結果画面における card tree、props 責務、renderer 責務、section routing を固定するための設計メモである。

Concierge 結果画面は、検索結果一覧ではなく、ユーザーの相談を整理し、神社提案から次の行動へつなげる体験である。

そのため、カードは「情報を詰め込む箱」ではなく、以下の順序を支える整理ブロックとして扱う。

1. 状態を整理する
2. 神社候補を提示する
3. なぜ合うのかを説明する
4. 行動の意味を作る
5. 保存・比較・継続利用へつなげる

---

## 基本方針

### やること

- ConciergeResult の card tree を固定する
- Props の責務を整理する
- Renderer の責務を section routing に限定する
- accessLevel による表示制御を親側へ寄せる
- card 内部の条件分岐を最小化する
- analytics event を card 単位で発火できる構造にする

### やらないこと

- `ConciergeSectionsRenderer` に UI 表示ロジックを詰め込まない
- 各 card 内で billing 判定を直接呼ばない
- card 内で API response 全体を解釈しない
- Free / Premium の出し分けを JSX inline の複雑な条件式にしない
- 「続きを読む」導線を前提にしない

---

## 用語定義

```ts
type AccessLevel = "anonymous" | "free" | "premium";

type CardVisibilityState = "visible" | "teaser" | "partial" | "hidden";
```

| 用語 | 意味 |
|---|---|
| accessLevel | 未ログイン / Free / Premium の利用状態 |
| visibility | card の表示状態 |
| section | API payload 由来の意味単位 |
| card | UI上の表示単位 |
| renderer | section を card に割り当てる routing 層 |

---

## ConciergeResult Card Tree

```txt
ConciergeResult
├─ ConsultationSummaryCard
├─ ShrineHeroCard
├─ ShrineMeaningCard
├─ ActionMeaningCard
├─ PreviousComparisonCard
├─ HistoryShiftCard
├─ OtherShrinesList
│  └─ ShrineCompactCard
├─ SavePromptCard
└─ PremiumPreviewCard
```

---

## Mobile First 表示順

### Anonymous

```txt
1. ShrineHeroCard
2. ShrineDetailLinkCard
3. OtherShrinesList
4. SavePromptCard(teaser)
5. LoginPromptCard
6. PremiumPreviewCard
```

### Free

```txt
1. ConsultationSummaryCard(partial)
2. ShrineHeroCard
3. ShrineMeaningCard(partial)
4. ActionMeaningCard(teaser)
5. ComparisonHintCard(partial)
6. OtherShrinesList
7. SavePromptCard
8. PremiumPreviewCard
```

### Premium

```txt
1. ConsultationSummaryCard
2. ShrineHeroCard
3. ShrineMeaningCard
4. ActionMeaningCard
5. PreviousComparisonCard
6. HistoryShiftCard
7. OtherShrinesList
8. SavePromptCard
```

---

## Card 責務一覧

| Card | 責務 | やらないこと |
|---|---|---|
| ConsultationSummaryCard | 入力内容・相談状態を整理して表示する | 神社詳細情報を表示しない |
| ShrineHeroCard | 推薦1位の神社を主役として表示する | 複数候補の比較をしない |
| ShrineMeaningCard | なぜこの神社が今回の相談に合うかを説明する | 前回比較や履歴分析をしない |
| ActionMeaningCard | 参拝・保存・行動の意味を整理する | 経路検索や外部地図責務を持たない |
| PreviousComparisonCard | 前回相談との差分を表示する | 初回ユーザーに無理に表示しない |
| HistoryShiftCard | 状態変化・履歴の流れを表示する | 単発相談の理由説明に使わない |
| OtherShrinesList | 2位以下の候補を補助的に表示する | Hero と同等の情報量にしない |
| ShrineCompactCard | 2位以下候補の短い理由を表示する | 深い解釈や比較を入れない |
| SavePromptCard | 保存・振り返りへの導線を置く | Premium の詳細説明を詰め込まない |
| PremiumPreviewCard | Premium で増える整理ブロックを予告する | Free を不完全版のように見せない |
| LoginPromptCard | 未ログインユーザーに保存・履歴化の価値を伝える | Premium訴求と混ぜない |

---

## Props 責務

### 原則

Props は、card が表示に必要な最小情報だけを受け取る。

card に API response 全体を渡さない。
card 内部で payload の構造解釈をしない。

---

## 共通 Props

```ts
type ConciergeCardBaseProps = {
  accessLevel: AccessLevel;
  visibility: CardVisibilityState;
  source: "concierge_result";
  onCardView?: (payload: CardAnalyticsPayload) => void;
  onCardCtaClick?: (payload: CardAnalyticsPayload) => void;
};
```

---

## ConsultationSummaryCard Props

```ts
type ConsultationSummaryCardProps = ConciergeCardBaseProps & {
  summary: string;
  detectedNeeds?: string[];
  userInput?: string;
};
```

### 責務

- 今回の相談内容を短く整理する
- Free の場合は partial 表示を許可する
- Premium の場合は full 表示する

### 禁止

- 神社候補の rank を表示しない
- Premium への直接 checkout 誘導を主目的にしない

---

## ShrineHeroCard Props

```ts
type ShrineHeroCardProps = ConciergeCardBaseProps & {
  shrine: {
    id: number | string;
    name: string;
    imageUrl?: string | null;
    address?: string | null;
    distanceLabel?: string | null;
  };
  rankReason?: string;
  primaryReason?: string;
  detailHref: string;
};
```

### 責務

- 推薦1位の神社を主役として表示する
- 詳細導線を置く
- 相談内容との基本的な一致理由を短く示す

### 禁止

- Premium 専用の履歴比較を混ぜない
- 他候補との差分比較を長く表示しない

---

## ShrineMeaningCard Props

```ts
type ShrineMeaningCardProps = ConciergeCardBaseProps & {
  shrineId: number | string;
  meaningSummary: string;
  primaryReason?: string;
  secondaryReason?: string;
};
```

### 責務

- 今回の相談と神社の意味を接続する
- Free では partial 表示を許可する
- Premium では full 表示する

### 禁止

- 前回相談との差分を扱わない
- 行動後の記録分析を扱わない

---

## ActionMeaningCard Props

```ts
type ActionMeaningCardProps = ConciergeCardBaseProps & {
  actionMeaning: string;
  suggestedAction?: string;
  ctaLabel: "整理する" | "保存して振り返る" | "Premiumで整理を続ける";
};
```

### 責務

- 参拝・保存・振り返りの意味を整理する
- Free では teaser として出せる
- Premium では行動意味を表示する

### 禁止

- 「続きを読む」導線を出さない
- 外部地図APIの責務を持たない

---

## PreviousComparisonCard Props

```ts
type PreviousComparisonCardProps = ConciergeCardBaseProps & {
  currentSummary: string;
  previousSummary?: string | null;
  comparisonText: string;
};
```

### 責務

- 前回相談との差分を表示する
- Premium の継続価値を担う

### 表示条件

- accessLevel が premium
- previousSummary または比較可能な履歴が存在する

### 禁止

- 履歴がないユーザーに無理に空表示しない

---

## HistoryShiftCard Props

```ts
type HistoryShiftCardProps = ConciergeCardBaseProps & {
  shifts: Array<{
    label: string;
    description: string;
  }>;
};
```

### 責務

- 過去相談・保存・参拝記録から状態変化を表示する
- Premium の継続利用価値を支える

### 禁止

- 単発の推薦理由カードとして使わない

---

## OtherShrinesList Props

```ts
type OtherShrinesListProps = ConciergeCardBaseProps & {
  shrines: ShrineCompactCardProps["shrine"][];
};
```

### 責務

- 2位以下の候補を補助的に表示する
- TOP候補との情報量差を明確にする

### 禁止

- Hero と同じ表示密度にしない
- 複雑な比較を入れない

---

## ShrineCompactCard Props

```ts
type ShrineCompactCardProps = ConciergeCardBaseProps & {
  shrine: {
    id: number | string;
    name: string;
    address?: string | null;
    distanceLabel?: string | null;
    tagLabel?: string | null;
    shortReason?: string | null;
    detailHref: string;
  };
};
```

### 責務

- 候補の存在と短い理由を伝える
- 詳細へ進める

### 禁止

- whyTop を表示しない
- secondaryReason を表示しない
- comparison を表示しない

---

## SavePromptCard Props

```ts
type SavePromptCardProps = ConciergeCardBaseProps & {
  canSave: boolean;
  isSaved?: boolean;
  ctaLabel: "保存する" | "ログインして保存" | "保存して振り返る";
};
```

### 責務

- 保存導線を置く
- 未ログインでは login 導線にする
- Free / Premium では保存状態を表示する

### 禁止

- Premium の詳細比較を説明しない

---

## PremiumPreviewCard Props

```ts
type PremiumPreviewCardProps = ConciergeCardBaseProps & {
  previewBlocks: Array<{
    title: string;
    description: string;
  }>;
  ctaLabel: "整理する" | "Premiumで整理を続ける";
};
```

### 責務

- Premium で増える整理ブロックを予告する
- Free を不完全版として見せず、次にできる整理として提示する

### 禁止

- 長文の続きを隠す構造にしない
- 「続きを読む」を出さない

---

## Renderer 責務

`ConciergeSectionsRenderer` は、API payload を UI card に割り当てる routing 層である。

### やること

- payload から表示に必要な section を取り出す
- accessLevel を受け取る
- visibility policy を適用する
- card の表示順を決める
- card に最小 props を渡す
- hidden card を描画対象から外す

### やらないこと

- card 内部UIを直接持たない
- billing API を直接呼ばない
- 保存 API を直接呼ばない
- analytics のイベント名を inline に散らさない
- 複雑な JSX 条件分岐を増やさない

---

## Visibility State別の表示原則

visibilityごとに、rendererが何を見せるか・見せないかを固定する。

| visibility | ゴール | 表示するもの | 表示しないもの |
|---|---|---|---|
| visible | カード本来の価値をそのまま表示する | 主内容、必要な補足説明、通常CTA | Premium誘導の過剰な説明、Free向け制限文言、teaser専用コピー |
| teaser | Premiumで増える整理ブロックの存在を伝える | 何が整理できるようになるか、短い価値予告、Premium導線 | 本文の途中まで、長文の続き、詳細比較、履歴変化の具体内容 |
| partial | Freeユーザーに整理体験の入口だけを見せる | 冒頭の1ブロック、hint、短い要約、次に整理できる内容の予告 | 詳細比較、深い意味整理、履歴変化、複数ブロックの連続表示 |
| hidden | 対象カードを完全に描画対象から外す | （何も表示しない） | DOMに出さない、Event送信をしない、CTAも出さない、hidden理由をUIに出さない |

partialは「読ませかけ」ではなく、Freeでも成立する最小の整理ブロックとして扱う。

hiddenは「存在を隠している」状態であり、teaserとは異なる。Premium訴求したい場合はhiddenではなくteaserを使う。

### CTA文言の方針

teaserでは、以下のCTAを使用しない。

- 続きを読む
- もっと読む
- 詳細を読む

代わりに、以下のような「整理する」方向のCTAを使用する。

- 整理する
- 今の状態を整理する
- Premiumで整理を続ける

Premium差分は「文章量」ではなく「整理ブロック数」で表現する。Free / Premiumの差を長文 / 短文で表現する設計は採用しない。

---

## Card別 Visibility Policy

accessLevelごとの各Cardのvisibilityは以下のとおりとする。

| Card | anonymous | free | premium | 方針 |
|---|---|---|---|---|
| ConsultationSummaryCard | hidden | partial | visible | Freeは冒頭整理のみ |
| ShrineMeaningCard | hidden | partial | visible | Freeは短い理由のみ |
| ActionMeaningCard | hidden | teaser | visible | Freeは行動意味の入口 |
| PreviousComparisonCard | hidden | hidden | visible | Premiumのみ |
| HistoryShiftCard | hidden | hidden | visible | Premiumのみ |
| PremiumPreviewCard | visible | visible | hidden | Premiumでは非表示 |
| SavePromptCard | teaser | visible | visible | anonymousはログイン誘導 |

---

## Section Routing

### 入力

```ts
type ConciergeResultPayload = {
  consultation?: unknown;
  recommendations?: unknown[];
  interpretation?: unknown;
  comparison?: unknown;
  history?: unknown;
  actions?: unknown;
};
```

### 出力

```ts
type ConciergeCardRoute = {
  cardId: string;
  visibility: CardVisibilityState;
  props: Record<string, unknown>;
};
```

---

## Section to Card Mapping

| section | card | 備考 |
|---|---|---|
| consultation | ConsultationSummaryCard | 相談整理 |
| recommendations[0] | ShrineHeroCard | TOP候補 |
| recommendations[1..] | OtherShrinesList / ShrineCompactCard | 他候補 |
| interpretation.shrineMeaning | ShrineMeaningCard | 神社意味 |
| interpretation.actionMeaning | ActionMeaningCard | 行動意味 |
| comparison.previous | PreviousComparisonCard | 前回比較 |
| history.shifts | HistoryShiftCard | 履歴変化 |
| saveState | SavePromptCard | 保存導線 |
| premiumPreview | PremiumPreviewCard | Premium予告 |

---

## Routing 擬似コード

```ts
function buildConciergeCardRoutes(params: {
  payload: ConciergeResultPayload;
  accessLevel: AccessLevel;
}): ConciergeCardRoute[] {
  const routes: ConciergeCardRoute[] = [];

  // 1. consultation summary
  // 2. hero shrine
  // 3. shrine meaning
  // 4. action meaning
  // 5. comparison / history
  // 6. other shrines
  // 7. save prompt
  // 8. premium preview

  return routes.filter((route) => route.visibility !== "hidden");
}
```

### 注意

実装時はこの関数を小さく保ち、card props の整形が肥大化する場合は mapper を分離する。

---

## Visibility Policy 適用順

1. cardId を決定する
2. accessLevel を見る
3. 履歴や比較データの有無を見る
4. visibility を決定する
5. hidden を除外する
6. teaser / partial / visible に応じて props を整形する
7. card に渡す

---

## Analytics 責務

analytics は card 単位で扱う。

Renderer は、cardId / visibility / accessLevel / source を props として渡す。
card は表示時・CTAクリック時に共通 handler を呼ぶ。

```ts
type CardAnalyticsPayload = {
  cardId: string;
  accessLevel: AccessLevel;
  visibility: CardVisibilityState;
  source: "concierge_result";
  shrineId?: number | string;
  recommendationRank?: number;
};
```

### 発火イベント

| event | 発火場所 |
|---|---|
| card_view | visible card 表示時 |
| card_partial_view | partial card 表示時 |
| card_teaser_view | teaser card 表示時 |
| card_cta_click | card 内CTAクリック時 |
| premium_preview_view | PremiumPreviewCard 表示時 |
| premium_preview_click | PremiumPreviewCard CTAクリック時 |
| save_prompt_click | SavePromptCard CTAクリック時 |

---

## 実装TODO

```markdown
- [ ] ConciergeResult 用 card tree を固定
- [ ] card props の最小単位を定義
- [ ] ConciergeSectionsRenderer の責務を routing に限定
- [ ] section to card mapping を定義
- [ ] visibility policy の適用順を固定
- [ ] hidden card を描画しない実装にする
- [ ] teaser / partial / visible の props 整形方針を決める
- [ ] card analytics payload を共通化
- [ ] 「続きを読む」CTAを出さない
- [ ] 「整理する」導線へ統一
```

---

## 完了条件

- ConciergeResult の card tree が説明できる
- 各 card の責務が重複していない
- Props に API payload 全体を渡さない方針が固定されている
- Renderer が section routing のみを担う
- accessLevel による表示差が visibility policy で表現できる
- analytics を card 単位で追加できる
- 「続きを読む」導線を使わず、「整理する」導線へ統一できる
