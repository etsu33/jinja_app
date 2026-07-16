> **Status: Reference**
>
> 本ドキュメントは、Concierge ResultにおけるCard VisibilityとRenderer責務の分離方針を記録した設計補足資料である。
>
> 現行の表示可否、Access LevelおよびCard構成は、関連するProduct文書、Frontend実装およびテストを最終的な正本とする。
# Card Visibility Renderer Split

最終更新: 2026-05-18  
対象: ConciergeResult / card visibility / Premium 表示境界

---

## 目的

本ドキュメントは、`visible / teaser / partial / hidden` の描画責務を固定し、
ConciergeResult の JSX 条件分岐を増やしすぎないための設計メモである。

Premium 差分は「文章量」ではなく、**整理ブロック数**で表現する。

そのため、renderer は単に表示・非表示を切り替えるだけではなく、
card の表示状態ごとに「何を見せるか / 何を見せないか」を制御する責務を持つ。

---

## 前提

以下はすでに定義済みである。

- `AccessLevel`
  - `anonymous`
  - `free`
  - `premium`
- `CardVisibilityState`
  - `visible`
  - `teaser`
  - `partial`
  - `hidden`
- `CardVisibilityPolicy`
- `getVisibilityForCard(cardId, accessLevel)`
- card analytics event

---

## 基本方針

### やること

- visibility ごとの renderer 責務を固定する
- `hidden` は原則描画しない
- `teaser` は Premium 価値の入口だけを見せる
- `partial` は Free 向けに冒頭または hint のみ見せる
- `visible` は通常カードとして表示する
- Premium 差分を block count で表現する
- JSX 内の accessLevel 判定を減らす

### やらないこと

- このPRで新しい UI を増やさない
- このPRでカード本文を大きく書き換えない
- `if premium` を JSX 内に増やさない
- 「続きを読む」導線を復活させない
- hidden card の analytics view を送らない
- Premium を長文表示として扱わない

---

## Renderer 責務一覧

| visibility | renderer責務 | 表示方針 | analytics |
|---|---|---|---|
| visible | 通常表示 | card の主内容を表示 | `card_view` |
| teaser | 入口表示 | 価値予告 + CTA のみ | `card_teaser_view` |
| partial | 部分表示 | 冒頭 / hint / 1ブロックのみ | `card_partial_view` |
| hidden | 非表示 | DOMにも出さない | 発火しない |

---

## visible renderer の責務

### ゴール

対象カードの本来の価値をそのまま表示する。

### 表示するもの

- card の主内容
- 必要な補足説明
- 通常CTA
- analytics payload に必要な識別情報

### 表示しないもの

- Premium誘導の過剰な説明
- Free向けの制限文言
- teaser専用コピー

### 例

```tsx
renderVisibleCard(cardId, props)
```

---

## teaser renderer の責務

### ゴール

Premium で増える整理ブロックの存在を伝え、次の行動へつなげる。

### 表示するもの

- 何が整理できるようになるか
- 短い価値予告
- 「整理する」系CTA
- Premium導線

### 表示しないもの

- 本文の途中まで
- 長文の続き
- 詳細比較
- 履歴変化の具体内容

### 禁止CTA

- 続きを読む
- もっと読む
- 詳細を読む

### 採用CTA

- 整理する
- 今の状態を整理する
- Premiumで整理を続ける

### 例

```tsx
renderTeaserCard(cardId, props)
```

---

## partial renderer の責務

### ゴール

Free ユーザーに、整理体験の入口だけを見せる。

### 表示するもの

- 冒頭の1ブロック
- hint
- 短い要約
- 次に整理できる内容の予告

### 表示しないもの

- 詳細比較
- 深い意味整理
- 履歴変化
- 複数ブロックの連続表示

### partial の原則

partial は「読ませかけ」ではなく、
Freeでも成立する最小の整理ブロックとして扱う。

---

## hidden renderer の責務

### ゴール

対象カードを完全に描画対象から外す。

### 方針

- DOMに出さない
- `card_view` を送らない
- CTAも出さない
- hidden理由をUIに出さない

### 注意

hidden は「存在を隠している」状態であり、
teaser とは異なる。

Premium訴求したい場合は hidden ではなく teaser を使う。

---

## ConciergeResult render flow

### 目的

ConciergeResult は、payload を直接 JSX に流し込むのではなく、
cardId と visibility を決めてから描画する。

### 推奨flow

```txt
payload
↓
accessLevel 解決
↓
cardId 決定
↓
visibility 決定
↓
hidden を除外
↓
visible / teaser / partial renderer に振り分け
↓
analytics payload を付与
↓
描画
```

---

## render route の考え方

将来的には以下のような route に寄せる。

```ts
type CardRenderRoute = {
  cardId: CardId;
  visibility: CardVisibilityState;
  props: Record<string, unknown>;
};
```

ただし、このPRでは route 実装までは行わない。

---

## block count による Premium 差分

### 方針

Premium 差分は「文章量」ではなく、整理ブロック数で表現する。

### Free

Free は、相談から推薦までの基本体験と、状態整理の入口を担う。

```txt
Free block count:
1. 神社候補
2. 神社詳細導線
3. 保存導線
4. 状態整理の入口
5. Premium preview
```

### Premium

Premium は、同じ相談結果に対して整理ブロックを増やす。

```txt
Premium block count:
1. 状態整理
2. 神社意味
3. 行動意味
4. 前回比較
5. 履歴変化
6. 深掘り整理
```

### 禁止

```txt
Free: 短文
Premium: 長文
```

この設計は採用しない。

---

## policy 接続順

### Phase 1: 接続済み

```markdown
- [x] PremiumPreviewCard
- [x] SavePromptCard
```

### Phase 2: 接続済み

```markdown
- [x] ConsultationSummaryCard
- [x] ShrineMeaningCard
- [x] ActionMeaningCard
```

### Phase 3: 一部接続済み / 次に分離

```markdown
- [x] PreviousComparisonCard
- [ ] HistoryShiftCard
- [ ] DeepReflectionCard
```

### Phase 4: ShrineDetail 側 / 未接続

```markdown
- [ ] ContextReasonCard
- [ ] PersonalMeaningCard
- [ ] SavedRecordCard
```

### 現在の接続状況

```markdown
- [x] ConciergeResult: premium_preview
- [x] ConciergeResult: save_prompt
- [x] ConciergeResult: consultation_summary
- [x] ConciergeResult: shrine_meaning
- [x] ConciergeResult: action_meaning
- [x] ConciergeResult: previous_comparison
- [ ] ConciergeResult: history_shift
- [ ] ConciergeResult: deep_reflection
- [ ] ShrineDetail: context_reason
- [ ] ShrineDetail: personal_meaning
- [ ] ShrineDetail: saved_record
```

### 注意

`PreviousComparisonCard` は `PremiumStateDeltaCard` として接続済みである。

ただし、`history_shift` と `deep_reflection` は同じ state delta 系の内部ブロックとして扱える可能性があるため、別PRで分離方針を決める。

---

## card別 renderer 方針

| cardId | anonymous | free | premium | 方針 |
|---|---|---|---|---|
| consultation_summary | hidden | partial | visible | Freeは冒頭整理のみ |
| shrine_meaning | hidden | partial | visible | Freeは短い理由のみ |
| action_meaning | hidden | teaser | visible | Freeは行動意味の入口 |
| previous_comparison | hidden | hidden | visible | Premiumのみ |
| history_shift | hidden | hidden | visible | Premiumのみ |
| deep_reflection | hidden | hidden | visible | Premiumのみ |
| premium_preview | visible | visible | hidden | Premiumでは非表示 |
| save_prompt | teaser | visible | visible | anonymousはログイン誘導 |

---

## 実装対象を増やさない制約

この設計PRでは以下を行わない。

```markdown
- [ ] 新規カードUIを作らない
- [ ] ConsultationSummary の表示文言を変えない
- [ ] ShrineMeaning の本文生成を変えない
- [ ] ActionMeaning の本文生成を変えない
- [ ] Premium判定ロジックを変更しない
- [ ] PostHog / GA 接続をしない
- [ ] 課金導線を増やさない
```

---

## 次PRの実装候補

### 候補A: HistoryShift / DeepReflection 分離方針整理

次に安全。

```markdown
- [ ] PremiumStateDeltaCard 内の summary / combinationChange / transitionNarrative を棚卸し
- [ ] previous_comparison / history_shift / deep_reflection の責務を分ける
- [ ] 表示分離するか analytics 分離だけにするか判断する
- [ ] 実装はまだ増やさない
```

### 候補B: ShrineDetail 側 policy 接続

中程度。

```markdown
- [ ] ShrineDetail 側の表示カードを洗い出す
- [ ] context_reason / personal_meaning / saved_record の対応UIを確認する
- [ ] cardId と visibility を接続する
```

### 候補C: render route helper 作成

重い。

```markdown
- [ ] CardRenderRoute 型を追加
- [ ] buildConciergeCardRoutes を作る
- [ ] JSX分岐を減らす
```

---

## 完了条件

- teaser / partial / hidden / visible の責務が説明できる
- Premium差分を block count で説明できる
- policy接続順が固定されている
- 接続済みカードと未接続カードが判断できる
- 次PRでどのcardから接続するか判断できる

---

## TODO

```markdown
- [x] teaser renderer の責務を定義
- [x] partial renderer の責務を定義
- [x] hidden renderer の責務を定義
- [x] visible renderer の責務を定義
- [x] ConciergeResult の card render flow を整理
- [x] block count でPremium差分を定義
- [x] policy接続順を定義
- [x] card policy接続済み一覧を更新
```
