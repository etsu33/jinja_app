

# Recommendation v4 reason_facts Backend E2E Audit

## Goal

Recommendation v4 Phase2 における `reason_facts` の backend E2E 責務を整理する。

この監査では、`reason_facts` が ranking で生成され、recommendation record に保持され、explanation payload に渡り、最終的な explanation の根拠として利用される流れを確認する。

このPRでは新規ロジックを追加しない。
既存実装のデータフロー、責務、テスト範囲を固定する。

## Current Status

`reason_facts` は既存 recommendation pipeline の内部根拠データとして実装済みである。

生成箇所:

```text
backend/temples/services/concierge_chat_ranking.py
```

利用箇所:

```text
backend/temples/services/concierge_explanation_payload.py
backend/temples/services/concierge_explanations.py
```

既存テスト:

```text
backend/temples/tests/services/test_concierge_chat_observation.py
backend/temples/tests/services/test_concierge_explanations.py
```

## Responsibility

`reason_facts` は、推薦候補が上位に入った理由を構造化して保持する internal data である。

担当すること:

- 候補採用理由を構造化する
- primary reason を選べる形で保持する
- explanation payload の primary_reason / secondary_reasons の材料になる
- observation / debug で推薦理由を追跡可能にする

担当しないこと:

- 自然文を直接生成しない
- ranking logic を変更しない
- recommendation_reason_v4 の reason_text を生成しない
- action_suggestion_v4 の行動提案を生成しない
- ユーザー表示文の最終コピーにはならない

## Data Contract

`reason_facts` の1要素は以下の構造を持つ。

```json
{
  "type": "string",
  "label": "string",
  "label_ja": "string",
  "evidence": ["string"],
  "score": 0.0,
  "is_primary": false
}
```

### Field Responsibility

| Field | Responsibility |
|---|---|
| type | 理由の種類 |
| label | 内部ラベルまたは一致対象 |
| label_ja | 表示向けの日本語ラベル |
| evidence | 根拠になった入力・一致条件 |
| score | 理由の強さ・寄与度 |
| is_primary | primary_reason として採用されたか |

## Current E2E Flow

現行の E2E フローは以下。

```text
concierge_chat_ranking.py
  ↓
_build_reason_facts()
  ↓
_resolve_primary_reason()
  ↓
rec["_reason_facts"]
rec["_primary_reason_source"]
rec["_primary_reason_label"]
  ↓
concierge_explanation_payload.py
  ↓
_normalize_reason_facts()
  ↓
primary_reason
secondary_reasons
  ↓
concierge_explanations.py
  ↓
summary
reasons
```

## Generation Layer

### concierge_chat_ranking.py

主な関数:

```text
_build_reason_facts()
_resolve_primary_reason()
_attach_breakdown()
```

主な代入:

```python
rec["_reason_facts"] = reason_facts
rec["_primary_reason_source"] = str(primary_reason.get("type") or "")
rec["_primary_reason_label"] = str(primary_reason.get("label") or "")
```

### _build_reason_facts()

入力:

- matched_by_tag
- matched_by_gid
- matched_by_text
- matched_by_user_selected_gid
- goriyaku_tag_label_by_id
- text_score_by_tag
- score_element
- astro_bonus_enabled
- shrine_meaning_profile

出力:

- reason_facts list

生成される主な type:

```text
history_theme
culture_translation
user_selected_tag
need_tag
goriyaku_tag
text_hint
element
fallback
```

## Primary Reason Policy

`reason_facts` が存在する場合、`_resolve_primary_reason()` が primary reason を決める。

その後、該当する fact に `is_primary = True` が設定される。

```python
if reason_facts:
    for fact in reason_facts:
        if same_as_primary_reason:
            fact["is_primary"] = True
            break
else:
    reason_facts = [primary_reason]
```

保証したいこと:

```markdown
- [ ] reason_facts がある場合、原則1件だけ is_primary=True になる
- [ ] reason_facts がない場合、fallback primary_reason が入る
- [ ] _primary_reason_source と _primary_reason_label が rec に保存される
- [ ] user_selected_tag / need_tag / text_hint などの優先順位が意図通りである
```

## Payload Layer

### concierge_explanation_payload.py

主な関数:

```text
_normalize_reason_facts()
build_explanation_payload()
```

`build_explanation_payload()` は `rec["_reason_facts"]` を読み、以下へ変換する。

```python
reason_facts = _normalize_reason_facts(rec.get("_reason_facts"), limit=5)
primary_reason = next((x for x in reason_facts if x.get("is_primary")), None)
secondary_reasons = [x for x in reason_facts if not x.get("is_primary")]
```

payload 出力:

```json
{
  "primary_reason": {},
  "secondary_reasons": []
}
```

## Explanation Layer

### concierge_explanations.py

`primary_reason` は以下で使われる。

```text
_build_summary_from_primary_reason()
_build_reason_entry_from_primary_reason()
```

最終的に以下へ変換される。

```json
{
  "summary": "string",
  "reasons": []
}
```

## Relationship with Recommendation v4

### recommendation_reason_v4

現時点では `reason_facts` を直接読まない。

理由:

- recommendation_reason_v4 は preview 層
- fact / interpretation / action を分ける設計
- candidate_profile / meaning_translation / interpretation_profile を主入力にしている

今後の検討余地:

```markdown
- [ ] recommendation_reason_v4.fact.evidence に reason_facts を接続するか
- [ ] reason_facts の primary_reason を v4 fact layer に渡すか
- [ ] active 表示切替時に explanation v2 と reason_v4 の根拠を統合するか
```

### action_suggestion_v4

現時点では `reason_facts` を直接読まない。

理由:

- action_suggestion_v4 は行動提案の層
- reason_facts は推薦根拠の層
- 直接つなぐと「なぜ」と「次に何をするか」が混ざる

判断:

```text
reason_facts → explanation / recommendation reason
consultation_axis → action_suggestion
```

の分離を維持する。

## Current Tests

既存テストで確認されていること。

### test_build_reason_facts_generates_user_selected_tag_reason

確認内容:

- user selected tag から reason_fact が生成される
- type が `user_selected_tag` になる
- label_ja が日本語ラベルになる
- evidence に `requested_goriyaku_tag_ids` が入る

### test_resolve_primary_reason_prefers_need_tag_over_user_selected_tag

確認内容:

- 複数 fact の中から primary reason が選ばれる
- need_tag が user_selected_tag より優先されるケースを確認

### test_attach_breakdown_sets_user_selected_tag_as_primary_reason

確認内容:

- `_attach_breakdown()` 後に `_reason_facts` が rec に保存される
- `_primary_reason_source` が保存される
- `_primary_reason_label` が保存される
- `_reason_facts[0].is_primary` が True になる

## Missing E2E Coverage

現状で追加検討したい E2E は以下。

```markdown
- [ ] _attach_breakdown 後の _reason_facts が build_explanation_payload の primary_reason に入る
- [ ] _reason_facts の非primaryが secondary_reasons に入る
- [ ] _reason_facts が空の場合 fallback primary_reason が payload に入る
- [ ] visit_style_primary_reason が fallback primary_reason を置き換える
- [ ] explanation.reasons に primary_reason 由来の reason code が入る
```

このPRでは docs で監査結果を固定し、必要であれば次PRでテストを追加する。

## Current Judgment

現時点の実装は、E2E の主要経路として成立している。

判断:

```markdown
- [x] _build_reason_facts で reason_facts が生成される
- [x] _resolve_primary_reason で primary reason が選ばれる
- [x] rec["_reason_facts"] に保存される
- [x] explanation payload で normalize される
- [x] primary_reason / secondary_reasons に分離される
- [x] explanation の summary / reasons の材料になる
```

大きな実装修正は不要。

ただし、backend E2E としては payload への受け渡し確認テストを追加するとさらに安全。

## Test Scope

この監査後に実行するテスト。

```bash
USE_SQLITE=0 python -m pytest temples/tests/services/test_concierge_chat_observation.py -k "reason_facts or primary_reason"
```

```bash
USE_SQLITE=0 python -m pytest temples/tests/services/test_concierge_explanations.py
```

```bash
python -m py_compile temples/services/concierge_chat_ranking.py temples/services/concierge_explanation_payload.py temples/services/concierge_explanations.py temples/tests/services/test_concierge_chat_observation.py temples/tests/services/test_concierge_explanations.py
```

## TODO

```markdown
- [x] reason_facts 生成箇所確認
- [x] _resolve_primary_reason 確認
- [x] rec への _reason_facts 保存箇所確認
- [x] explanation payload への接続確認
- [x] primary_reason / secondary_reasons 分離確認
- [x] 既存テスト確認
- [x] Recommendation v4 各レイヤーとの責務境界整理
- [x] 大きな実装修正は不要と判断
- [ ] backend pytest
- [ ] py_compile
```

## Next Step

このPRでは、`reason_facts backend E2E` の監査docsを追加する。

次に進む対象:

```text
Recommendation v4 Preview 統合監査
Preview API Contract監査
```

確認対象:

```text
backend/temples/services/concierge_chat.py
backend/temples/tests/api/test_concierge_chat_response_body_contract.py
backend/temples/services/recommendation_reason_v4.py
backend/temples/services/action_suggestion_builder.py
```
