

# Mobile Concierge First Route Design Audit

## 目的

Phase4 Concierge First UIへ戻る流れの中で、Mobile側の Home / Concierge / Shrine Detail 導線が、相談起点の体験として成立しているかを確認する。

本監査では、実装修正ではなく以下を整理する。

- Mobile Home の相談開始導線
- Mobile Concierge の推薦結果導線
- Mobile Shrine Detail への引き継ぎ情報
- Ranking / Search / Favorites などの補助導線との関係
- 次PRで扱うべき実装単位

## 前提

以下は完了済み。

- 主要Contract固定
  - `reason_facts`
  - `recommendation_reason_v4`
  - `action_suggestion_v4_preview`
  - `consultation_axis`
  - `explanation`
- Normalize Cleanup
  - Web `_reason_facts` fallback削減
  - Web `_explanation_payload.original_reason` 依存削減
  - Mobile `_reason_facts` fallback削減
- Web / Mobile 表示差分監査
- `action_suggestions` Contract監査
- `primary_reason` Contract監査
- Phase4 Concierge First Readiness監査
- Concierge First Route Design監査
- Home Ranking 補助導線化
- Home Nearby Section 文脈整理

これにより、Mobile側も導線設計を確認し、次のUI実装へ進める状態になっている。

## 監査対象

### Mobile Home

対象ファイル:

- `apps/mobile/app/index.tsx`

現状:

- 相談入力欄がある
- 相談テーマチップがある
- 条件追加ヒントがある
- 主CTAは「この相談からご縁を見る」
- `openConcierge()` により `/concierge` へ遷移する
- 入力内容があれば `q` として渡す
- テーマ選択があれば `theme` として渡す

遷移:

```ts
router.push(query ? `/concierge?${query}` : "/concierge");
```

判断:

Mobile Home は Concierge First の主導線として成立している。

### Mobile Concierge

対象ファイル:

- `apps/mobile/app/concierge/index.tsx`

現状:

- `/concierge/chat/` を呼び出す
- 相談内容から推薦結果を取得する
- 推薦カードに以下を表示できる
  - `recommendation_reason_v4`
  - `reason_facts`
  - `action_suggestion_v4_preview`
- 推薦カードから Shrine Detail へ遷移する

詳細遷移時に渡している情報:

```ts
router.push({
  pathname: "/shrines/[id]",
  params: {
    id: card.shrineId,
    recommendationReasonV4: card.recommendationReasonV4 ?? "",
    reasonFacts: card.reasonFacts ? JSON.stringify(card.reasonFacts) : "",
    recommendationReasonDetail: card.recommendationReasonDetail ? JSON.stringify(card.recommendationReasonDetail) : "",
  },
});
```

判断:

Mobile Concierge は相談結果から Shrine Detail へ意味情報を引き継げている。

### Mobile Shrine Detail

対象ファイル:

- `apps/mobile/app/shrines/[id].tsx`

現状:

- `recommendationReasonV4` を受け取れる
- `reasonFacts` を受け取れる
- `recommendationReasonDetail` を受け取れる
- APIレスポンスから `recommendation_reason_v4` / `reason_facts` / `explanation` も扱える
- 推薦理由と選定ポイントを表示できる
- 記録導線として `/records` へ遷移できる

判断:

Mobile Shrine Detail は Concierge結果から来た場合の文脈表示に対応している。

ただし、`action_suggestion_v4_preview` はまだ Shrine Detail には引き継がれていない。

## 補助導線

### Ranking

対象ファイル:

- `apps/mobile/app/ranking/index.tsx`

現状:

- Rankingから Shrine Detail へ遷移できる
- 相談起点ではなく、人気順・参考導線として扱う

### Search

対象ファイル:

- `apps/mobile/app/search/index.tsx`

現状:

- Searchから Shrine Detail へ遷移できる
- 神社名・条件から探す補助導線として扱う

### Favorites / Recently Viewed

対象ファイル:

- `apps/mobile/app/favorites/index.tsx`
- `apps/mobile/app/recently-viewed/index.tsx`

現状:

- 保存済み / 最近見た神社から Shrine Detail へ遷移できる
- Concierge Firstの主導線ではなく、再訪・確認導線として扱う

## 導線優先順位

Mobile Concierge First の導線優先順位は以下とする。

```text
1. Mobile Home から相談開始
2. Mobile Concierge で推薦確認
3. Shrine Detail で推薦理由・根拠確認
4. Records で参拝後の記録
5. Ranking / Search / Favorites / Recently Viewed は補助導線
```

## Webとの整合性

WebとMobileのConcierge First思想は概ね一致している。

| 項目 | Web | Mobile | 判定 |
|---|---|---|---|
| Home相談入力 | あり | あり | 一致 |
| テーマチップ | あり | あり | 一致 |
| 条件追加ヒント | あり | あり | 一致 |
| Concierge結果表示 | あり | あり | 一致 |
| 詳細への推薦情報引き継ぎ | あり | あり | 概ね一致 |
| Ranking | 補助導線 | 補助導線 | 一致 |
| Search / Shrine一覧 | 補助導線 | 補助導線 | 一致 |

## 残課題

### 1. Mobile Shrine Detail への `action_suggestion_v4_preview` 引き継ぎ

現状、Mobile Conciergeでは `action_suggestion_v4_preview` を表示できる。
しかし、Shrine Detailにはまだ引き継いでいない。

検討ポイント:

- Detailでも行動提案を表示する必要があるか
- 表示する場合、route paramsで渡すか、APIレスポンス側で受けるか
- 最小カードとして表示するか

### 2. Mobileでの `consultation_axis` 利用

現状、Mobileでは `consultation_axis` をほぼ使っていない。

検討ポイント:

- 表示に使う必要があるか
- analytics用に保持するだけでよいか
- 今すぐ実装する必要はあるか

### 3. Mobile Concierge の `explanation.summary` 表示

現状、Mobile Shrine Detailでは `explanation` を扱える。
一方で、Mobile Conciergeカードでは `explanation.summary` の直接表示は薄い。

検討ポイント:

- 推薦カード上でsummaryを出すと情報過多にならないか
- `recommendation_reason_v4` と重複しないか
- Webとの表示差分をどこまで縮めるか

## 判断

Mobile Concierge First route は成立している。

理由:

- Mobile Homeが相談起点になっている
- `/concierge` へ自然に遷移できる
- Mobile Conciergeが推薦結果を表示できる
- Shrine Detailへ推薦理由・根拠を引き継げる
- Ranking / Search / Favorites は補助導線として整理できる

ただし、以下は次PR候補として残す。

- Mobile Shrine Detailへの `action_suggestion_v4_preview` 表示検討
- Mobileでの `consultation_axis` 利用方針
- Mobile Conciergeでの `explanation.summary` 表示検討

## 今回のPRでやること

- Mobile Home / Concierge / Shrine Detail の導線を文書化する
- Webとの整合性を整理する
- 補助導線の位置づけを整理する
- 次PR候補を明確にする

## 今回のPRでやらないこと

- Mobile UI実装は変更しない
- `action_suggestion_v4_preview` の引き継ぎ実装はしない
- `consultation_axis` のMobile利用は追加しない
- `explanation.summary` の表示追加はしない
- 新しいAPI Contractは追加しない

## 次PR候補

### 1. Mobile Shrine Detail action suggestion preview

ブランチ候補:

`feature/mobile-shrine-detail-action-suggestion-preview`

目的:

- Mobile Shrine Detailにも `action_suggestion_v4_preview` を表示するか検証する
- Concierge結果から詳細へ遷移した後も、次の行動が分かる状態にする

対象候補:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`

### 2. Mobile Concierge explanation summary

ブランチ候補:

`feature/mobile-concierge-explanation-summary`

目的:

- Mobile Conciergeで `explanation.summary` を表示するか検証する
- Webとの表示差分を縮める

対象候補:

- `apps/mobile/app/concierge/index.tsx`

### 3. Mobile consultation axis analytics

ブランチ候補:

`refactor/mobile-consultation-axis-analytics`

目的:

- Mobileで `consultation_axis` を表示ではなくanalytics / contextとして保持するか検討する

対象候補:

- `apps/mobile/app/concierge/index.tsx`

## 推奨判断

次PRは **Mobile Shrine Detail action suggestion preview** が有力。

理由:

- Mobile Home / Concierge / Detail の基本導線は成立済み
- Conciergeカード上では行動提案を表示できている
- Detailに遷移したあと、次の行動が消える点が体験差分として残っている
- 既存Contract `action_suggestion_v4_preview` を活かせる
- 実装範囲が比較的小さい

ただし、表示が重くなる場合はカード1つだけの最小表示に留める。

## TODO

```markdown
# Mobile Concierge First Route Design Audit

- [x] develop最新版化
- [x] audit/mobile-concierge-first-route-design 作成
- [x] Mobile Home導線確認
- [x] Mobile Concierge導線確認
- [x] Mobile Shrine Detail導線確認
- [x] 補助導線整理
- [x] Webとの整合性整理
- [x] 次PR候補整理
- [x] 推奨判断整理
- [ ] docs/audit/mobile-concierge-first-route-design.md をコミット
- [ ] PR作成
```

## 完了条件

- Mobile Concierge First導線が文書化されている
- Webとの思想差分が整理されている
- 次に実装すべきMobile UI改善候補が明確になっている
