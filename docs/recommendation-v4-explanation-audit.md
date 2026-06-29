

# Recommendation v4 Explanation Audit

## Goal

Recommendation v4 Phase2 における `explanation` レイヤーの責務、入力、出力、`recommendation_reason_v4` / `action_suggestion_v4` / `reason_facts` との境界を整理する。

この監査では、`explanation_v4` を新規実装しない。
現行の `explanation v2` を維持しつつ、Recommendation v4 の各レイヤーと矛盾しない責務境界を固定する。

## Current Status

`explanation_v4` という専用実装は現時点では存在しない。

現行の explanation 系は以下の2層で構成されている。

```text
backend/temples/services/concierge_explanation_payload.py
backend/temples/services/concierge_explanations.py
```

### concierge_explanation_payload.py

責務:

- explanation 用の構造化 payload を作る
- `_reason_facts` を正規化する
- `primary_reason` を決める
- `secondary_reasons` を作る
- `gogyou_context` を作る
- `history_context` を作る
- `action_suggestions` を history_theme から取得する
- score / score_v2 を payload に含める

主な関数:

```text
build_explanation_payload()
attach_explanation_payload()
_normalize_reason_facts()
_build_history_context()
_build_gogyou_context()
_build_visit_style_primary_reason()
```

### concierge_explanations.py

責務:

- `_explanation_payload` から自然文を生成する
- chat 用 explanation を作る
- plan 用 explanation を作る
- summary を作る
- reasons を作る
- disclaimer を付ける

主な関数:

```text
build_explanation_for_chat_rec()
build_explanation_for_plan_rec()
attach_explanations_for_chat()
attach_explanations_for_plan()
_build_summary_from_primary_reason()
_build_reason_entry_from_primary_reason()
_build_history_alignment_text()
```

## Current Output Contract

現行 explanation は以下の構造を返す。

```json
{
  "version": 2,
  "summary": "string",
  "reasons": [
    {
      "code": "string",
      "label": "string",
      "text": "string",
      "strength": "high | mid | low",
      "evidence": {}
    }
  ],
  "disclaimer": "string"
}
```

## Responsibility

Explanation Layer は、推薦結果に対して「なぜこの候補が提示されたか」を表示用に説明する層である。

担当すること:

- `primary_reason` をもとに summary を生成する
- `reason_facts` を reasons として自然文に変換する
- history_theme と need の整合を説明する
- gogyou_context を補助理由として扱う
- visit_style / highlights / area / wish / extra_condition を補助理由として扱う
- disclaimer を付ける

担当しないこと:

- ranking logic を変更しない
- score weight を変更しない
- `recommendation_reason_v4.reason_text` を置き換えない
- `action_suggestion_v4.primary_action` を生成しない
- ユーザーの心理状態を断定しない
- 神社に行けば結果が出るとは言い切らない

## Layer Boundary

### recommendation_reason_v4

役割:

```text
相談文脈と神社側の事実を、fact / interpretation / action に分けて説明する preview 層
```

主な出力:

- reason_text
- fact
- interpretation
- action
- source

境界:

- Recommendation v4 の新しい理由生成レイヤー
- preview / debug 用
- `fact / interpretation / action` を明示的に分ける

### explanation v2

役割:

```text
既存レスポンスで使われる表示用 explanation 層
```

主な出力:

- summary
- reasons
- disclaimer

境界:

- 既存 UI / API contract を維持する
- `_explanation_payload` をもとに自然文を生成する
- v4 preview ではなく現行表示の主説明

### action_suggestion_v4

役割:

```text
次に取れる小さな行動を提示する preview 層
```

主な出力:

- primary_action
- secondary_action
- reflection_prompt
- action_source

境界:

- Explanation ではなく行動提案
- summary や reasons を生成しない
- ユーザーが押せる導線に近い文面を扱う

## reason_facts Relationship

`reason_facts` は Recommendation v4 以前から存在する推薦理由の根拠データである。

生成箇所:

```text
backend/temples/services/concierge_chat_ranking.py
```

主な関数・代入:

```text
_build_reason_facts()
rec["_reason_facts"] = reason_facts
```

利用箇所:

```text
backend/temples/services/concierge_explanation_payload.py
```

主な処理:

```text
_normalize_reason_facts()
primary_reason = next((x for x in reason_facts if x.get("is_primary")), None)
secondary_reasons = [x for x in reason_facts if not x.get("is_primary")]
```

判断:

- `reason_facts` は explanation の根拠として重要
- `recommendation_reason_v4` は現時点で `reason_facts` を直接読まない
- `action_suggestion_v4` も `reason_facts` を直接読まない
- E2E では `_reason_facts` が ranking から explanation payload へ渡ることを確認する必要がある

## Current Flow

現行の説明生成フローは以下。

```text
concierge_chat_ranking.py
  ↓
_build_reason_facts()
  ↓
rec["_reason_facts"]
  ↓
concierge_explanation_payload.py
  ↓
build_explanation_payload()
  ↓
rec["_explanation_payload"]
  ↓
concierge_explanations.py
  ↓
build_explanation_for_chat_rec()
  ↓
rec["explanation"]
```

Recommendation v4 preview 系は別系統で追加される。

```text
consultation_interpreter.py
  ↓
meaning_translation.py
  ↓
recommendation_reason_v4.py
  ↓
action_suggestion_builder.py
```

## Current Problem

現行 explanation は安定しているが、責務が広い。

主な懸念:

- summary 生成条件が多い
- gogyou_context と history_context が同じ summary 内で混ざる
- reason_facts / primary_reason / original_reason / highlights の優先順位が複雑
- action_suggestions を payload 内で持っているため、action_suggestion_v4 と責務が近く見える
- `explanation_v4` という名前が未実装なので、v4移行範囲が曖昧になりやすい

## Copy Audit

### 良い点

- `summary` と `reasons` が分離されている
- `disclaimer` が必ず付く
- `reason_facts` を正規化して扱っている
- `history_context` と `gogyou_context` が構造化されている
- `VISIT_STYLE_MATCH` など reason code がある
- `original_reason` fallback がある

### 注意点

- `金運を整えつつ` など、結果保証に近く見える表現に注意する
- `背中を押される` など抽象表現が増えやすい
- `生年月日から見た今の巡り` は補助情報であることを明示し続ける
- `summary` が recommendation_reason_v4.reason_text と重複しないようにする
- `action_suggestions` は explanation payload に含まれるが、v4以降は action_suggestion_v4 と責務分離を意識する

## explanation_v4 Policy

現時点では `explanation_v4` を新規実装しない。

理由:

- 現行 explanation v2 が既存 API / UI contract を担っている
- `recommendation_reason_v4` が preview として別途存在する
- `action_suggestion_v4` も preview として存在する
- explanation を v4 化すると影響範囲が広い

今後 `explanation_v4` を検討する条件:

```markdown
- [ ] recommendation_reason_v4 を active 表示へ移行する方針が決まる
- [ ] action_suggestion_v4 を active 表示へ移行する方針が決まる
- [ ] explanation.summary と recommendation_reason_v4.reason_text の重複率が高い
- [ ] explanation payload の version 3 以上が必要になる
- [ ] UI側で explanation / reason / action を明確に分ける設計が決まる
```

## Recommended Boundary

現時点の推奨境界は以下。

| Layer | Role | Active/Preview | Main Output |
|---|---|---|---|
| explanation v2 | 既存表示説明 | Active | summary / reasons |
| recommendation_reason_v4 | v4理由生成 | Preview | fact / interpretation / action |
| action_suggestion_v4 | v4行動提案 | Preview | primary_action / reflection_prompt |
| reason_facts | 推薦根拠データ | Internal | _reason_facts |

## Test Scope

この監査後に実行するテスト。

```bash
USE_SQLITE=0 python -m pytest temples/tests/services/test_concierge_explanations.py temples/tests/services/test_concierge_explanations_contract.py
```

```bash
python -m py_compile temples/services/concierge_explanation_payload.py temples/services/concierge_explanations.py temples/tests/services/test_concierge_explanations.py temples/tests/services/test_concierge_explanations_contract.py
```

必要に応じて API contract を確認する。

```bash
USE_SQLITE=0 python -m pytest temples/tests/api/test_concierge_chat_need_breakdown_contract.py -k explanation
```

## TODO

```markdown
- [x] concierge_explanation_payload.py の責務確認
- [x] concierge_explanations.py の責務確認
- [x] explanation_v4 は未実装と確認
- [x] reason_facts との関係を整理
- [x] recommendation_reason_v4 との責務境界を整理
- [x] action_suggestion_v4 との責務境界を整理
- [x] explanation_v4 は今回新規実装しないと判断
- [ ] backend pytest
- [ ] py_compile
```

## Next Step

このPRでは、`explanation_v4` の新規実装ではなく、現行 explanation v2 の責務監査を追加する。

次に進む対象:

```text
reason_facts backend E2E
```

確認対象:

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/services/concierge_explanation_payload.py
backend/temples/tests/services/test_concierge_chat_observation.py
backend/temples/tests/services/test_concierge_explanations.py
```
