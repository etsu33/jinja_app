# Backend Recommendation Contract Audit

## 目的

推薦結果における backend の正本を整理し、Web / Mobile が同じ意味で表示できるように API 返却 Contract の基準を固定する。

この監査では実装変更は行わず、現在の返却値・表示側の参照キー・今後の統一方針を記録する。

## 現在地

backend 側では Recommendation Reason v4 / reason_facts / explanation / action_suggestion_v4_preview / consultation_axis / score_v3 などの推薦補助情報が生成されている。

一方で、Web / Mobile 側では互換性維持のために複数キーを fallback で参照している。

## Backend 正本候補

### Top Level

- `consultation_axis`

### recommendations[]

- `consultation_axis`
- `explanation`
- `reason_facts`
- `recommendation_reason_v4`
- `recommendation_reason_quality`
- `action_suggestion_v4_preview`
- `rank_explanation`

### Debug / Internal

- `_debug`
- `_explanation_payload`
- `_reason_facts`
- `breakdown.score_v3_detail`

## 現在の生成経路

### Recommendation Core

- `backend/temples/services/concierge_chat.py`
- `backend/temples/services/concierge_chat_ranking.py`

### Reason Facts

- `backend/temples/services/concierge_chat_ranking.py`
  - `_build_reason_facts()`
  - `rec["_reason_facts"]`

### Explanation Payload

- `backend/temples/services/concierge_explanation_payload.py`
  - `attach_explanation_payload()`
  - `rec["_explanation_payload"]`

### Explanation

- `backend/temples/services/concierge_explanations.py`
  - `attach_explanations_for_chat()`
  - `rec["explanation"]`

### Recommendation Reason v4

- `backend/temples/services/recommendation_reason_v4.py`
- `backend/temples/services/concierge_chat.py`
  - `_attach_recommendation_reason_quality()`

### Action Suggestion v4

- `backend/temples/services/action_suggestion_builder.py`
  - `attach_action_suggestion_v4_preview()`
  - `rec["action_suggestion_v4_preview"]`

### Consultation Axis

- `backend/temples/services/concierge_chat.py`
  - `recs["consultation_axis"]`
  - `rec["consultation_axis"]`

### Score v3

- `backend/temples/services/concierge_chat_ranking.py`
  - `breakdown.score_v3`
  - `breakdown.score_v3_detail`

## Web側の現状

Web は以下を参照している。

- `explanation`
- `_explanation_payload`
- `reason_facts`
- `_reason_facts`
- `action_suggestion_v4_preview`
- `actionSuggestionV4Preview`
- `consultation_axis`
- `consultationAxis`
- `_need.consultation_axis`
- `_signals.consultation_axis`
- `_signals.result_state.consultation_axis`

### 課題

- `consultation_axis` の取得元が多い
- snake_case / camelCase が混在している
- `_reason_facts` を表示側が直接参照している
- `_explanation_payload` を表示側が直接参照している
- backend の正本と frontend のfallback境界が曖昧

## Mobile側の現状

Mobile は以下を参照している。

- `recommendation_reason_v4`
- `recommendationReasonV4`
- `reason_facts`
- `reasonFacts`
- `_reason_facts`
- `action_suggestion_v4_preview`
- `actionSuggestionV4Preview`
- `explanation`

### 課題

- `reason_facts` / `reasonFacts` / `_reason_facts` が混在
- `recommendation_reason_v4` / `recommendationReasonV4` が混在
- `action_suggestion_v4_preview` / `actionSuggestionV4Preview` が混在
- 詳細画面への navigation params でも `reasonFacts` / `recommendationReasonV4` を引き回している

## Contract 方針

### 正本として残す

backend API の正本は snake_case とする。

#### Top Level

- `consultation_axis`

#### recommendations[]

- `consultation_axis`
- `explanation`
- `reason_facts`
- `recommendation_reason_v4`
- `recommendation_reason_quality`
- `action_suggestion_v4_preview`
- `rank_explanation`

### 内部用として扱う

以下は backend 内部・debug・互換用途として扱い、表示側の正本にはしない。

- `_debug`
- `_signals`
- `_need`
- `_reason_facts`
- `_explanation_payload`
- `actionSuggestionV4Preview`
- `reasonFacts`
- `recommendationReasonV4`
- `consultationAxis`

## 移行方針

### Phase1

- backend正本を docs に固定
- Web / Mobile の参照状況を監査
- 既存表示は壊さない

### Phase2

- frontend/mobile の normalize 層で snake_case 正本を camelCase view model に変換する
- 画面コンポーネントは view model のみ参照する

### Phase3

- `_reason_facts` / `_explanation_payload` 直接参照を減らす
- fallback取得元を縮小する
- tests で正本キー優先を固定する

### Phase4

- Web / Mobile 表示差分監査
- 同じ推薦データで同じ意味が表示されるか確認する

## 優先順位

1. `consultation_axis`
   - 取得元が多すぎるため最優先で正本化する

2. `reason_facts`
   - `_reason_facts` 直接参照をやめ、表示用は `reason_facts` に寄せる

3. `recommendation_reason_v4`
   - Mobile / Web ともに正本を揃える

4. `action_suggestion_v4_preview`
   - v4 preview の表示契約を固定する

5. `explanation`
   - `_explanation_payload` は内部用に寄せる

## 結論

backend の推薦正本は snake_case の API response に固定する。

Web / Mobile は backend の raw response を直接解釈せず、normalize / view model 層で吸収する。

次フェーズでは、まず `consultation_axis` と `reason_facts` を中心に、Web / Mobile の表示差分監査へ進む。
