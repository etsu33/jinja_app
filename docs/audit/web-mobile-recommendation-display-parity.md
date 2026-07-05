

# Web / Mobile Recommendation Display Parity Audit

## 目的

推薦APIの主要Contract統一後、Web / Mobile が同じ推薦情報を同じ意味で表示できているかを監査する。

本監査では、実装修正よりも以下を優先する。

- backend が公開正本として返すフィールドを確認する
- Web / Mobile が参照している表示フィールドを整理する
- 表示差分を明示する
- 次PRで扱うべき修正対象を切り分ける

## 前提

以下の主要Contractはすでに公開正本として整理済み。

- `reason_facts`
- `recommendation_reason_v4`
- `action_suggestion_v4_preview`
- `consultation_axis`
- `explanation`

また、以下の内部fallbackは削減済み。

- Web の `_reason_facts` fallback
- Web の `_explanation_payload.original_reason` fallback

## 監査対象

### Backend 公開正本

| Contract | 役割 | 状態 |
|---|---|---|
| `reason_facts` | 推薦根拠の構造化情報 | 公開正本 |
| `recommendation_reason_v4` | 推薦理由本文 | 公開正本 |
| `action_suggestion_v4_preview` | 行動提案preview | 公開正本 |
| `consultation_axis` | 相談軸 | 公開正本 |
| `explanation` | 表示用説明summary / reasons | 公開正本 |

## Web 表示状況

### Concierge result / list

主な参照箇所:

- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`

使用している主なContract:

- `recommendation_reason_v4`
- `reason_facts`
- `action_suggestion_v4_preview`
- `consultation_axis`
- `explanation`

### Web の現状

- `recommendation_reason_v4` を推薦理由の優先表示元として利用している
- `reason_facts` を推薦根拠として利用している
- `action_suggestion_v4_preview` をトップ推薦表示で利用している
- `consultation_axis` をanalytics / sectionsで利用している
- `explanation.summary` をsummary表示に利用している

### Web の残課題

以下はまだ内部payloadへの依存が残る。

- `_explanation_payload.action_suggestions`
- `_explanation_payload.primary_reason.label`

ただし、現時点では表示生成に使われているため、今回の監査PRでは削除しない。

## Mobile 表示状況

### Mobile Concierge

主な参照箇所:

- `apps/mobile/app/concierge/index.tsx`

使用している主なContract:

- `recommendation_reason_v4`
- `reason_facts`
- `action_suggestion_v4_preview`

現状:

- `recommendation_reason_v4` を推薦理由として利用している
- `reason_facts` を根拠表示として利用している
- `action_suggestion_v4_preview` を行動提案表示として利用している
- `consultation_axis` は未使用
- `explanation` の直接表示は薄い

### Mobile Shrine Detail

主な参照箇所:

- `apps/mobile/app/shrines/[id].tsx`

使用している主なContract:

- `recommendation_reason_v4`
- `reason_facts`
- `explanation`

現状:

- `recommendation_reason_v4` を推薦理由として利用している
- `reason_facts` を選定ポイント表示に利用している
- `explanation` は構造化object / stringの両方を受け取り、summary または reason text に正規化して表示している
- `action_suggestion_v4_preview` は未使用
- `consultation_axis` は未使用

## Web / Mobile 表示差分

| 項目 | Web | Mobile Concierge | Mobile Shrine Detail | 判定 |
|---|---|---|---|---|
| `recommendation_reason_v4` | 使用 | 使用 | 使用 | 概ね一致 |
| `reason_facts` | 使用 | 使用 | 使用 | 概ね一致 |
| `action_suggestion_v4_preview` | 使用 | 使用 | 未使用 | 差分あり |
| `consultation_axis` | 使用 | 未使用 | 未使用 | 差分あり |
| `explanation` | 使用 | 薄い | 使用 | 一部差分あり |

## 判断

現時点で、推薦理由と推薦根拠の表示は Web / Mobile でかなり揃っている。

一方で、以下はまだ完全一致ではない。

- `consultation_axis` はWeb中心で、Mobileでは未使用
- `action_suggestion_v4_preview` はWeb / Mobile Conciergeでは使われているが、Mobile Shrine Detailでは未使用
- `explanation` はWebではカードsummary、Mobile Shrine Detailでは説明本文として使われており、表示粒度が異なる

そのため、現段階で「Web / Mobile 表示完全一致」とは言い切らない。
ただし、主要Contractは揃っており、次PR以降で表示方針を合わせられる状態にはなっている。

## 今回のPRでやること

- Web / Mobile の推薦表示Contract使用状況を記録する
- 表示差分を明示する
- 次PRの候補を整理する

## 今回のPRでやらないこと

- Mobile に `consultation_axis` 表示を追加しない
- Mobile Shrine Detail に `action_suggestion_v4_preview` を追加しない
- `_explanation_payload.primary_reason` を削除しない
- `_explanation_payload.action_suggestions` を削除しない

## 次PR候補

### 1. Mobile normalize整理

目的:

- Mobile側の camelCase fallback / `_reason_facts` fallback を整理する
- snake_case 正本を優先する方針を明確化する

対象候補:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`

### 2. action_suggestions 公開Contract化検討

目的:

- `_explanation_payload.action_suggestions` を通常表示から外せるか検討する
- 必要であれば `action_suggestions` を公開Contractとして昇格する

対象候補:

- `backend/temples/services/concierge_explanation_payload.py`
- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`

### 3. primary_reason 公開Contract化検討

目的:

- `_explanation_payload.primary_reason.label` 依存を削減する
- `reason_facts.is_primary` または新規公開Contractで代替可能か確認する

対象候補:

- `backend/temples/services/concierge_explanation_payload.py`
- `backend/temples/services/concierge_explanations.py`
- `apps/web/src/viewmodels/conciergeToShrineList.ts`

## TODO

```markdown
# Web / Mobile Recommendation Display Parity Audit

- [x] develop最新版化
- [x] audit/web-mobile-recommendation-display-parity 作成
- [x] Web表示フィールド確認
- [x] Mobile Concierge表示フィールド確認
- [x] Mobile Shrine Detail表示フィールド確認
- [x] Web / Mobile 表示差分整理
- [x] 今回のPRでやらないことを明記
- [x] 次PR候補整理
- [ ] docs/audit/web-mobile-recommendation-display-parity.md をコミット
- [ ] PR作成
```

## 完了条件

- Web / Mobile の推薦表示差分が文書化されている
- 次に実装すべきNormalize対象が明確になっている
- 実装変更なしでPR化できる
