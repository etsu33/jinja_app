# Action Suggestions Contract Audit

## 目的

推薦APIの行動提案まわりについて、`action_suggestion_v4_preview` と `_explanation_payload.action_suggestions` の責務を整理する。

本監査では、実装修正ではなく以下を優先する。

- 現在の公開Contractを確認する
- 内部payloadとして残っている `action_suggestions` の役割を整理する
- 公開Contract化すべきかを判断する
- 次PRで扱うべき対象を切り分ける

## 前提

推薦APIの主要Contractはすでに以下を公開正本として整理済み。

- `reason_facts`
- `recommendation_reason_v4`
- `action_suggestion_v4_preview`
- `consultation_axis`
- `explanation`

行動提案については、すでに `action_suggestion_v4_preview` が公開Contractとして存在する。

そのため、本監査では `_explanation_payload.action_suggestions` を追加で公開Contract化すべきかを確認する。

## 監査対象

### 公開Contract

| Contract | 役割 | 状態 |
|---|---|---|
| `action_suggestion_v4_preview` | 推薦結果に対する主要な行動提案preview | 公開正本 |

### 内部payload

| Field | 役割 | 状態 |
|---|---|---|
| `_explanation_payload.action_suggestions` | history_theme 由来の旧行動提案 / 補助提案 | 内部payload |

## Backend 状況

主な参照箇所:

- `backend/temples/services/concierge_explanation_payload.py`
- `backend/temples/services/action_suggestion_builder.py`
- `backend/temples/services/action_suggestions.py`

### `_explanation_payload.action_suggestions`

`_explanation_payload.action_suggestions` は `concierge_explanation_payload.py` で生成される。

主な役割:

- `history_theme` に応じた行動候補を生成する
- `explanation_payload` 内に保持する
- 旧UI / 補助UIで参照できる形にする

### `action_suggestion_v4_preview`

`action_suggestion_v4_preview` は `action_suggestion_builder.py` で生成される。

主な役割:

- 推薦理由 v4 / meaning / action_context などをもとに行動提案を組み立てる
- `primary_action`
- `secondary_action`
- `reflection_prompt`
- `action_source`
- `preview`
- `version`
- `source_keys`

を持つ公開Contractとして返す。

## Frontend 状況

### Web

主な参照箇所:

- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`
- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`

Webでは以下の2系統が残っている。

```text
1. action_suggestion_v4_preview
   - 公開Contract
   - トップ推薦 / 行動提案previewで利用

2. _explanation_payload.action_suggestions
   - 内部payload
   - 旧actionSuggestionsとして一部で利用
```

### Mobile

主な参照箇所:

- `apps/mobile/app/concierge/index.tsx`

Mobile Conciergeでは `action_suggestion_v4_preview` を利用している。

一方で、Mobile Shrine Detailでは `action_suggestion_v4_preview` はまだ利用していない。

## 判断

現時点では `_explanation_payload.action_suggestions` を公開Contract化しない。

理由:

- すでに `action_suggestion_v4_preview` が公開Contractとして存在する
- `_explanation_payload.action_suggestions` を昇格すると、行動提案が2系統になり責務が曖昧になる
- Webの一部で旧導線として使われているが、通常表示の正本にするには設計整理が必要
- `action_suggestion_v4_preview` と表示目的が重複する

したがって、今後の方針は以下とする。

```text
公開Contract: action_suggestion_v4_preview
内部payload: _explanation_payload.action_suggestions
```

## 今回のPRでやること

- `action_suggestion_v4_preview` と `_explanation_payload.action_suggestions` の責務を文書化する
- `_explanation_payload.action_suggestions` を今すぐ公開Contract化しない判断を記録する
- 次PR候補を整理する

## 今回のPRでやらないこと

- `_explanation_payload.action_suggestions` を削除しない
- `_explanation_payload.action_suggestions` を公開Contract化しない
- `action_suggestion_v4_preview` のschema変更はしない
- Web / Mobile の表示追加はしない

## 次PR候補

### 1. Web actionSuggestions 旧導線整理

目的:

- Webで `_explanation_payload.action_suggestions` を参照している箇所を整理する
- `action_suggestion_v4_preview` に寄せられる表示は寄せる

対象候補:

- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`

### 2. Mobile Shrine Detail action_suggestion_v4_preview 表示検討

目的:

- Mobile Shrine Detailでも行動提案を表示するか判断する
- 表示する場合は `action_suggestion_v4_preview` を正本として使う

対象候補:

- `apps/mobile/app/shrines/[id].tsx`

### 3. action_suggestion_v4_preview schema固定強化

目的:

- API Contract Testで `action_suggestion_v4_preview` のschemaをより厳密に固定する
- Web / Mobileが期待するshapeと一致させる

対象候補:

- `backend/temples/tests/api/test_concierge_chat_response_body_contract.py`
- `backend/temples/tests/services/test_action_suggestion_builder.py`

## TODO

```markdown
# Action Suggestions Contract Audit

- [x] develop最新版化
- [x] audit/action-suggestions-contract 作成
- [x] action_suggestion_v4_preview の公開Contract確認
- [x] _explanation_payload.action_suggestions の内部payload確認
- [x] Backend参照箇所確認
- [x] Web参照箇所確認
- [x] Mobile参照箇所確認
- [x] 公開Contract化しない判断を記録
- [x] 次PR候補整理
- [ ] docs/audit/action-suggestions-contract.md をコミット
- [ ] PR作成
```

## 完了条件

- `action_suggestion_v4_preview` を公開正本とする方針が文書化されている
- `_explanation_payload.action_suggestions` を内部payloadとして残す判断が記録されている
- 次に整理すべき旧導線が明確になっている
