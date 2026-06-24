

# Premium Card Matrix

最終更新: 2026-05-18  
対象: Concierge結果画面 / Shrine詳細画面 / Premium導線

---

## 目的

本ドキュメントは、KAMI MUSUBI におけるカード表示の責務と、
未ログイン / Free / Premium の表示境界を固定するための設計メモである。

Premium差分は「文章量」ではなく、**整理ブロック数**で表現する。

つまり Premium は、長い説明を読む権利ではなく、
自分の状態・行動・履歴・比較をより多面的に整理できる権利として扱う。

---

## 基本方針

### やること

- 未ログイン / Free / Premium の表示差を card 単位で定義する
- card ごとの責務を明確にする
- teaser / partial / hidden の扱いを固定する
- Props による表示制御の前提を作る
- analytics event を card 単位で設計できる状態にする

### やらないこと

- 「続きを読む」導線で Premium 差分を作らない
- 同じカード内で Free / Premium の責務を混ぜない
- 神社詳細の公開情報を Premium 化しない
- Map / Search の基本機能を Premium 価値の中心にしない
- Premium を単なる長文表示にしない

---

## accessLevel 定義

```ts
type AccessLevel = "anonymous" | "free" | "premium";
```

| accessLevel | 状態 | 説明 |
|---|---|---|
| anonymous | 未ログイン | 相談・推薦閲覧は可能。保存・履歴・個人比較は不可 |
| free | ログイン済み Free | 基本推薦、保存入口、状態整理の入口を表示 |
| premium | Premium | 状態整理、意味整理、比較、履歴変化を表示 |

---

## 表示状態の定義

| 表示状態 | 意味 | UI方針 |
|---|---|---|
| visible | 全文表示 | 通常カードとして表示 |
| teaser | Premium価値の予告 | 中身は見せすぎず、「整理する」導線を置く |
| partial | 冒頭またはhintのみ表示 | 体験の入口だけ見せる |
| hidden | 表示しない | DOM上も原則出さない |

---

## CTA方針

### 採用するCTA

- 整理する
- 今の状態を整理する
- 保存して振り返る
- 前回と比べる
- Premiumで整理を続ける

### 採用しないCTA

- 続きを読む
- もっと読む
- 詳細を読む

理由:
KAMI MUSUBI は読ませるサービスではなく、状態整理から行動へつなげるサービスである。

---

## Card Matrix

| Card | Anonymous | Free | Premium | 主責務 |
|---|---|---|---|---|
| ShrineHeroCard | visible | visible | visible | 最上位候補の神社を提示する |
| ShrineCompactCard | visible | visible | visible | 2位以下の候補を比較用に提示する |
| ShrineDetailLinkCard | visible | visible | visible | 神社詳細への導線を置く |
| LoginPromptCard | visible | hidden | hidden | ログインして保存・変化確認へ進める |
| SavePromptCard | teaser | visible | visible | 相談結果や神社を保存する導線 |
| ConsultationSummaryCard | hidden | partial | visible | 今回の相談・状態を整理する |
| StateTeaserCard | hidden | visible | hidden | Free向けに状態整理の入口を見せる |
| PremiumPreviewCard | visible | visible | hidden | Premiumで増える整理ブロックを予告する |
| ShrineMeaningCard | hidden | partial | visible | なぜこの神社が合うのかを説明する |
| ActionMeaningCard | hidden | teaser | visible | 参拝行動の意味を整理する |
| ComparisonHintCard | hidden | partial | hidden | Free向けに比較価値のhintを出す |
| PreviousComparisonCard | hidden | hidden | visible | 前回相談との差分を整理する |
| HistoryShiftCard | hidden | hidden | visible | 履歴・状態変化を表示する |
| DeepReflectionCard | hidden | hidden | visible | 深掘りの自己整理を行う |

---

## Anonymous 表示方針

### ゴール

未ログインでも、KAMI MUSUBI の基本価値を体験できる状態にする。

### 現在地

未ログインは、相談から神社候補を見るところまでは許可する。
一方で、保存・履歴・比較・深い状態整理は表示しない。

### 表示する

- ShrineHeroCard
- ShrineCompactCard
- ShrineDetailLinkCard
- LoginPromptCard
- PremiumPreviewCard

### teaser

- SavePromptCard

### hidden

- ConsultationSummaryCard
- ShrineMeaningCard
- ActionMeaningCard
- PreviousComparisonCard
- HistoryShiftCard
- DeepReflectionCard

### 次の一手

未ログイン用の preview は、保存・履歴・比較ではなく、
「ログインすると今の変化を保存できる」ことを伝える。

---

## Free 表示方針

### ゴール

基本推薦に加えて、状態整理の入口を体験させる。

### 現在地

Free は神社候補・詳細・保存入口を使える。
ただし、比較・履歴変化・深い意味整理は Premium 側に置く。

### 表示する

- ShrineHeroCard
- ShrineCompactCard
- ShrineDetailLinkCard
- SavePromptCard
- StateTeaserCard
- PremiumPreviewCard

### partial

- ConsultationSummaryCard
- ShrineMeaningCard
- ComparisonHintCard

### teaser

- ActionMeaningCard

### hidden

- PreviousComparisonCard
- HistoryShiftCard
- DeepReflectionCard

### 次の一手

Free では「全部読めない」ではなく、
「整理を続けると、前回比較や行動意味まで見られる」と伝える。

---

## Premium 表示方針

### ゴール

相談結果を、状態・意味・行動・履歴の複数ブロックで整理する。

### 現在地

Premium は、Free の基本導線に加えて、
個人文脈・前回比較・状態変化・深掘り整理を表示する。

### 表示する

- ShrineHeroCard
- ShrineCompactCard
- ShrineDetailLinkCard
- SavePromptCard
- ConsultationSummaryCard
- ShrineMeaningCard
- ActionMeaningCard
- PreviousComparisonCard
- HistoryShiftCard
- DeepReflectionCard

### hidden

- LoginPromptCard
- StateTeaserCard
- PremiumPreviewCard
- ComparisonHintCard

### 次の一手

Premium では「文章量を増やす」のではなく、
以下の整理ブロックを増やす。

1. 状態整理
2. 神社意味
3. 行動意味
4. 前回比較
5. 履歴変化
6. 深掘り整理

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

### Renderer責務

`ConciergeSectionsRenderer` は payload を受け取り、
card の表示順と表示条件を決める routing 層に限定する。

card 内部で accessLevel 判定を増やしすぎない。

---

## ShrineDetail Card Tree

```txt
ShrineDetail
├─ ShrinePublicInfoCard
├─ ShrineAccessCard
├─ ShrineGoriyakuCard
├─ ShrineGoshuinPreviewCard
├─ ContextReasonCard
├─ PersonalMeaningCard
├─ SavedRecordCard
└─ PremiumPreviewCard
```

### ShrineDetail の境界

神社詳細は、神社そのものを理解するための画面である。

Free / Premium に関係なく見せるもの:

- 神社名
- 所在地
- 由緒
- ご利益
- 公開御朱印
- 基本導線

Premium にできるもの:

- コンシェルジュ由来の個人向け補足理由
- 保存済み相談との比較
- 訪問記録や御朱印記録との接続
- 再訪・振り返り提案

---

## Visibility Policy

表示制御は card 単位で行う。

```ts
type CardVisibilityState = "visible" | "teaser" | "partial" | "hidden";

type CardVisibilityPolicy = {
  cardId: string;
  anonymous: CardVisibilityState;
  free: CardVisibilityState;
  premium: CardVisibilityState;
};
```

### 原則

- accessLevel は親コンポーネントから渡す
- card 内部では表示内容の最小分岐に留める
- Premium判定は billing state を正本とする
- hidden の card は analytics view を送らない
- teaser / partial は専用 event を送る

---

## Analytics Event 方針

analytics は page 単位ではなく card 単位で設計する。

| event | 発火条件 |
|---|---|
| card_view | card が visible 表示された |
| card_teaser_view | card が teaser 表示された |
| card_partial_view | card が partial 表示された |
| card_cta_click | card 内CTAが押された |
| premium_preview_view | PremiumPreviewCard が表示された |
| premium_preview_click | Premium導線が押された |
| save_prompt_click | 保存導線が押された |

### event payload 案

```ts
type CardAnalyticsPayload = {
  cardId: string;
  accessLevel: AccessLevel;
  visibility: CardVisibilityState;
  source: "concierge_result" | "shrine_detail";
  shrineId?: number | string;
  recommendationRank?: number;
};
```

---

## Mobile First Order

### ConciergeResult

1. ConsultationSummaryCard
2. ShrineHeroCard
3. ShrineMeaningCard
4. ActionMeaningCard
5. PreviousComparisonCard / ComparisonHintCard
6. OtherShrinesList
7. SavePromptCard
8. PremiumPreviewCard

### ShrineDetail

1. ShrinePublicInfoCard
2. ContextReasonCard
3. ShrineAccessCard
4. ShrineGoriyakuCard
5. PersonalMeaningCard
6. SavedRecordCard
7. PremiumPreviewCard

---

## Card Height 方針

| Card | 目安 |
|---|---|
| teaser card | 160〜220px |
| partial card | 180〜260px |
| summary card | 最大260px目安 |
| hero card | 内容に応じて可変 |
| comparison card | 最大240px目安 |
| history card | 最大280px目安 |

### 原則

- mobile で1カードが画面全体を占有しすぎない
- teaser は短く、価値予告に徹する
- Premium の深い整理カードは、カード分割で読みやすくする

---

## 実装TODO

```markdown
- [ ] 未ログイン / Free / Premium の card matrix を docs 化
- [ ] card責務一覧を定義
- [ ] ConciergeResult 用 card tree を定義
- [ ] ShrineDetail 用 card tree を定義
- [ ] cardごとの visibility policy を定義
- [ ] cardごとの analytics event を定義
- [ ] 「続きを読む」CTAを削除
- [ ] 「整理する」CTAへ統一
- [ ] Premium teaser の責務を固定
- [ ] mobile first の card order を固定
- [ ] card高さの最大値を決定
- [ ] Propsで accessLevel 制御を分離
- [ ] Premium差分を block count で固定
- [ ] analytics schema を card単位へ分離
```

---

## 完了条件

- cardごとの責務が説明できる
- accessLevel ごとの表示差が matrix で確認できる
- teaser / partial / hidden の使い分けが固定されている
- 「続きを読む」導線が設計上不要になっている
- Premium差分が文章量ではなく整理ブロック数で説明できる
- 実装時に Props と analytics event へ落とし込める
