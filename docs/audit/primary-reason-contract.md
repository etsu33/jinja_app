

# Primary Reason Contract Audit

## 目的

推薦APIの `primary_reason` まわりについて、公開Contract化すべきか、内部payloadとして残すべきかを整理する。

本監査では、実装修正ではなく以下を優先する。

- `primary_reason` の生成元を確認する
- `primary_reason` の利用箇所を整理する
- `reason_facts` との責務差分を明確にする
- 公開Contract化するべきかを判断する
- 次PRで扱うべき対象を切り分ける

## 前提

推薦APIの主要Contractはすでに以下を公開正本として整理済み。

- `reason_facts`
- `recommendation_reason_v4`
- `action_suggestion_v4_preview`
- `consultation_axis`
- `explanation`

このうち、推薦根拠の公開正本は `reason_facts` とする。

`primary_reason` は現在 `_explanation_payload.primary_reason` として存在している。

## 監査対象

### 公開Contract

| Contract | 役割 | 状態 |
|---|---|---|
| `reason_facts` | 推薦根拠の構造化情報 | 公開正本 |

### 内部payload

| Field | 役割 | 状態 |
|---|---|---|
| `_explanation_payload.primary_reason` | explanation生成 / 表示補助用の主理由 | 内部payload |
| `_primary_reason_source` | primary_reason生成元の内部観測値 | 内部値 |
| `_primary_reason_label` | primary_reasonラベルの内部観測値 | 内部値 |

## Backend 状況

主な参照箇所:

- `backend/temples/services/concierge_chat_ranking.py`
- `backend/temples/services/concierge_explanation_payload.py`
- `backend/temples/services/concierge_explanations.py`
- `backend/temples/services/concierge_chat_observation.py`

### `concierge_chat_ranking.py`

`_resolve_primary_reason()` により、推薦候補ごとの主理由を決定している。

その結果は以下に保存される。

- `reason_facts[].is_primary`
- `_primary_reason_source`
- `_primary_reason_label`

主な役割:

- 推薦候補の主な根拠を決める
- rank_explanation / observation 用の補助情報に使う
- `reason_facts` のうち、どれが主根拠かを示す

### `concierge_explanation_payload.py`

`_explanation_payload.primary_reason` を生成している。

主な役割:

- `reason_facts` から `is_primary` の理由を拾う
- visit style の理由が必要な場合は補正する
- `_primary_reason_source` / `_primary_reason_label` からfallbackする
- explanation生成用の中間payloadとして保持する

### `concierge_explanations.py`

`_explanation_payload.primary_reason` をもとに、以下を生成している。

- `explanation.summary`
- `explanation.reasons`
- reason entry
- 表示用の説明文

つまり、`primary_reason` は最終表示Contractというより、`explanation` を作るための中間情報として機能している。

### `concierge_chat_observation.py`

`primary_reason_source` / `primary_reason_label` は観測・監査用に使われている。

主な役割:

- どの理由が主理由として選ばれたかを観測する
- primary_reason_source_counts を集計する
- 推薦根拠の偏りを確認する

## Frontend 状況

### Web

主な参照箇所:

- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/app/shrines/[id]/page.tsx`
- `apps/web/src/lib/concierge/pickExplanationPayloadFromThread.ts`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`

Webでは `_explanation_payload.primary_reason` を以下の用途で参照している。

- 推薦カードの短句生成
- 詳細ページの説明補助
- 前回相談summaryの補助
- Shrine Detail model の説明生成

ただし、通常の推薦根拠表示はすでに `reason_facts` を正本としている。

### Mobile

Mobileでは、現時点で `primary_reason` を直接参照していない。

Mobileは以下を主に利用している。

- `recommendation_reason_v4`
- `reason_facts`
- `action_suggestion_v4_preview`
- `explanation`

## `reason_facts` との責務差分

| 項目 | reason_facts | primary_reason |
|---|---|---|
| 状態 | 公開Contract | 内部payload |
| 役割 | 推薦根拠の正本 | explanation生成 / 表示補助 |
| 複数理由 | 持てる | 基本は1つ |
| 主理由 | `is_primary` で表現 | 主理由そのもの |
| Web通常表示 | 使用 | 一部で補助利用 |
| Mobile通常表示 | 使用 | 未使用 |
| 公開すべきか | すでに公開 | 現時点では非推奨 |

## 判断

現時点では `primary_reason` を公開Contract化しない。

理由:

- `reason_facts` がすでに推薦根拠の公開正本として存在する
- `reason_facts.is_primary` により主理由は表現できる
- `primary_reason` を公開すると、推薦根拠が2系統になり責務が曖昧になる
- `primary_reason` は `explanation` 生成の中間情報としての性格が強い
- Mobileでは直接利用しておらず、公開Contract化の必要性が低い

したがって、今後の方針は以下とする。

```text
公開Contract: reason_facts
主理由表現: reason_facts[].is_primary
内部payload: _explanation_payload.primary_reason
内部観測値: _primary_reason_source / _primary_reason_label
```

## 今回のPRでやること

- `primary_reason` の責務を文書化する
- `reason_facts` との責務差分を整理する
- `primary_reason` を今すぐ公開Contract化しない判断を記録する
- 次PR候補を整理する

## 今回のPRでやらないこと

- `_explanation_payload.primary_reason` を削除しない
- `primary_reason` を公開Contract化しない
- `reason_facts` のschema変更はしない
- Web / Mobile の表示変更はしない
- `_primary_reason_source` / `_primary_reason_label` を削除しない

## 次PR候補

### 1. Web primary_reason 依存整理

目的:

- Webで `_explanation_payload.primary_reason.label` を参照している箇所を整理する
- `reason_facts.is_primary` から代替できるか確認する

対象候補:

- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/app/shrines/[id]/page.tsx`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`

### 2. reason_facts primary schema固定強化

目的:

- `reason_facts` に必ず `is_primary` が含まれるかをContract Testで固定する
- フロントが `reason_facts.is_primary` を信頼できる状態にする

対象候補:

- `backend/temples/tests/api/test_concierge_chat_response_body_contract.py`
- `backend/temples/tests/services/test_concierge_chat_observation.py`
- `backend/temples/services/concierge_chat_ranking.py`

### 3. explanation payload内部化の段階整理

目的:

- `_explanation_payload` のうち、通常表示で不要になった依存を段階的に減らす
- 削除せず、まずは参照先を公開Contractへ寄せる

対象候補:

- `_explanation_payload.primary_reason`
- `_explanation_payload.action_suggestions`

## TODO

```markdown
# Primary Reason Contract Audit

- [x] develop最新版化
- [x] audit/primary-reason-contract 作成
- [x] primary_reason の生成元確認
- [x] _primary_reason_source / _primary_reason_label の用途確認
- [x] Backend参照箇所確認
- [x] Web参照箇所確認
- [x] Mobile参照箇所確認
- [x] reason_facts との責務差分整理
- [x] 公開Contract化しない判断を記録
- [x] 次PR候補整理
- [ ] docs/audit/primary-reason-contract.md をコミット
- [ ] PR作成
```

## 完了条件

- `primary_reason` を内部payloadとして扱う方針が文書化されている
- `reason_facts` を推薦根拠の公開正本とする方針が維持されている
- 次に整理すべきWeb依存箇所が明確になっている
