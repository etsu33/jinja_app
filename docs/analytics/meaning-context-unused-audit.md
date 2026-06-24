# Meaning Context 未使用監査

## 目的

`buildMeaningNarrative.ts` 内で生成されている `meaningContext` の利用実態を確認し、今後の扱いを整理する。

---

## 現状

`meaningContext` は `buildMeaningNarrative.ts` 内で生成・返却されているが、現UIでは表示されていない。

確認済みの参照範囲:

- `apps/web/src/lib/concierge/buildMeaningNarrative.ts`
  - `MeaningNarrative.meaningContext`
  - `const meaningContext = \`\${whyNow}\${actionRole}\`;`
  - return payload
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
  - 表示しているのは `reasonVm.detail.shrineMeaning`
  - 補助表示は `reasonVm.detail.actionMeaning`
- `apps/web/src/lib/concierge/__tests__/buildRecommendationReasonViewModel.test.ts`
  - `detail.shrineMeaning` は1文であることを検証
  - `detail.shrineMeaning` に「今は、」が含まれないことを検証

---

## 問題

`meaningContext` を構成する `buildWhyNow` / `buildActionRole` には、ユーザー状態を強く推測する表現が残っている。

例:

- 感覚がぶれやすい
- 判断が散りやすい
- 優先順位が崩れやすい
- 何を切り替えるかが見えにくくなる
- 自分の受け取り方が揺れやすい
- 順番が崩れやすい
- 集中の軸がぶれやすい
- 動けなくなりやすい

ただし、現UIでは `meaningContext` が使われていないため、現時点のユーザー表示には影響していない。

---

## 分類

### 事実

- `args.need`
- `args.mode`
- `args.primary.key`
- `args.context.ritual`

### 推測

- 判断が散りやすい
- 優先順位が崩れやすい
- 感覚がぶれやすい
- 見えにくくなる
- 動けなくなりやすい

### 解釈 / 行動意味

- 節目として向き合いやすい
- 整え直す
- 見直す
- 切り替える
- 受け止め直す

---

## 判断

このPRでは `meaningContext` の削除や再設計は行わない。

理由:

- 現UIでは未使用であり、表示上の緊急度が低い
- `MeaningNarrative` の返却型に含まれており、将来利用・後方互換の可能性がある
- いきなり削除すると、別導線や将来のPremium表示で使う余地を消す可能性がある

---

## 今後の選択肢

### 1. 削除する

`meaningContext` / `buildWhyNow` / `buildActionRole` が今後も未使用なら削除候補。

### 2. Premium用に再設計する

Premium向けの深い意味づけとして使う場合は、状態断定を弱める。

例:

- Before: `次の一手を急ぐほど優先順位が崩れやすい今は、`
- After: `仕事や次の一手を整理したい相談では、`

### 3. `actionMeaning` に統合する

問いとして表示する `actionMeaning` に役割を寄せ、説明文としての `meaningContext` を廃止する。

---

## 次に実装する場合の対象ファイル

- `apps/web/src/lib/concierge/buildMeaningNarrative.ts`
- `apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/lib/concierge/__tests__/buildRecommendationReasonViewModel.test.ts`
- `apps/web/src/lib/concierge/__tests__/__snapshots__/buildRecommendationReasonViewModel.test.ts.snap`

---

## 結論

`meaningContext` は現状では未使用の返却値であり、即時修正対象ではない。

ただし、将来UIに再接続する場合は、`buildWhyNow` の状態推測表現を弱め、相談事実と行動意味を分離してから使う。
