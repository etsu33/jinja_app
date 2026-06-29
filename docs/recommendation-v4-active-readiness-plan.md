

# Recommendation v4 Active Readiness Plan

## Goal

Recommendation v4 / Score v3 を Active 化する前に、Shadow Mode の実測、CVR計測、重み調整、Active化条件を固定する。

この計画は、Recommendation v4 をすぐ本番表示へ切り替えるためのものではない。
Preview / Debug で集めたデータをもとに、Active化してよいかを判断するための準備資料である。

## Current Status

Recommendation v4 Phase2 では以下が完了している。

```markdown
- [x] Recommendation Reason v4 監査
- [x] Action Suggestion v4 監査
- [x] Explanation Layer 監査
- [x] reason_facts backend E2E
- [x] Recommendation v4 Preview 統合監査
- [x] Preview API Contract監査
```

現在の Recommendation v4 は preview / debug として接続済みである。

Active化前に見るべき対象は以下。

```markdown
- Shadow Modeの実測
- CVR計測
- 重み調整
- Score v3 Active化
- Recommendation v4 Active化
```

## Non Goals

このPRでは以下を行わない。

```markdown
- Score v3 を Active 化しない
- Recommendation v4 を Active 表示に切り替えない
- ranking logic を変更しない
- score weight を変更しない
- UI layout を変更しない
- 課金導線を変更しない
```

## Recommended Order

Active化までの順番は以下。

```text
1. Shadow Modeの実測
2. CVR計測
3. 重み調整
4. Score v3 Active化
5. Recommendation v4 Active化
```

理由:

- Score v3 は ranking に影響するため、先に shadow 実測が必要
- Recommendation v4 は表示文言に影響するため、ユーザー行動との相関を見る必要がある
- CVRが見えない状態で Active 化すると、改善か悪化か判断できない
- weight 調整は実データなしに行うと主観になる

## 1. Shadow Mode Measurement

### Goal

Score v3 / Recommendation v4 preview が、現行推薦と比べてどの程度違うかを観測する。

### Current Location

関連箇所:

```text
backend/temples/services/concierge_chat.py
backend/temples/services/recommendation_algorithm_v3.py
backend/temples/services/recommendation_reason_v4.py
backend/temples/services/action_suggestion_builder.py
```

### Metrics

```markdown
- top1_changed_rate
- top3_changed_rate
- avg_score_delta
- max_abs_delta
- score_v3_final_score_distribution
- reason_v4_preview_generated_rate
- action_suggestion_v4_preview_generated_rate
```

### Minimum Observation Volume

```markdown
- 最低 30 セッション
- 推奨 100 セッション
- 最低 7日間
```

### Pass Criteria

```markdown
- top1_changed_rate が極端に高すぎない
- top3 の候補品質が目視で破綻していない
- preview payload が欠落しない
- debug payload が既存 contract を壊していない
```

目安:

```markdown
- top1_changed_rate: 20〜50%以内なら要レビュー
- top1_changed_rate: 70%以上なら Active 化は保留
- reason_v4_preview_generated_rate: 95%以上
- action_suggestion_v4_preview_generated_rate: 95%以上
```

## 2. CVR Measurement

### Goal

Recommendation v4 / Score v3 が、ユーザー行動にどの程度つながっているかを測る。

### Primary Funnel

```text
recommendation_view
↓
detail_open
↓
save
↓
route_open
↓
visit_done
↓
reflection_saved
```

### KPI

```markdown
- detail_open_rate
- save_rate
- route_open_rate
- visit_done_rate
- reflection_saved_rate
```

### Secondary KPI

```markdown
- action_suggestion_click_rate
- action_started_rate
- premium_preview_click_rate
- checkout_started_rate
- premium_active_rate
```

### Segment

以下の単位で見る。

```markdown
- need_tag
- consultation_axis
- history_theme
- source: current / score_v3_shadow
- user type: anonymous / free / premium
- device: mobile / web
```

## 3. Weight Adjustment

### Goal

Score v3 の重みを、実測行動に合わせて調整する。

### Current Candidate Weights

初期候補:

```markdown
- state_match_score
- meaning_match_score
- shrine_profile_score
- behavior_score
- history_score
- final_score
```

### Adjustment Policy

重み調整は、単発の主観で行わない。

以下の順で判断する。

```text
1. Shadow Modeで差分を見る
2. 行動CVRと突合する
3. 明確に悪いセグメントを抽出する
4. 1回の調整幅を小さくする
5. 再度Shadow Modeで観測する
```

### Guardrail

```markdown
- 1回のweight変更は ±0.05 以内を基本にする
- top1_changed_rate が70%以上になる変更は避ける
- 特定needだけ極端に強くしない
- history_theme だけで推薦が決まらないようにする
- behavior_score は実データが十分になるまで強くしすぎない
```

## 4. Score v3 Active化条件

### Goal

Score v3 を実際の ranking に適用してよいか判断する。

### Required Conditions

```markdown
- [ ] Shadow Mode で最低30セッション観測済み
- [ ] 推奨100セッション以上の観測がある
- [ ] top1_changed_rate が許容範囲内
- [ ] top3候補に明確な品質劣化がない
- [ ] detail_open_rate が現行比で悪化していない
- [ ] save_rate が現行比で悪化していない
- [ ] route_open_rate が現行比で悪化していない
- [ ] 異常なneed偏りがない
- [ ] backend tests が通っている
- [ ] rollback plan がある
```

### Active化判断

Score v3 Active化は以下のいずれかを満たす場合に検討する。

```markdown
- detail_open_rate が現行比 +5%以上
- save_rate が現行比 +3%以上
- route_open_rate が現行比 +3%以上
- reflection_saved_rate が現行比 +3%以上
```

明確な改善がない場合は Active 化しない。

## 5. Recommendation v4 Active化条件

### Goal

Recommendation v4 の reason / action / explanation preview を、実際の表示に切り替えてよいか判断する。

### Required Conditions

```markdown
- [ ] reason_v4_preview が安定生成されている
- [ ] action_suggestion_v4_preview が安定生成されている
- [ ] explanation v2 との責務境界が維持されている
- [ ] reason_text に内部キーが出ていない
- [ ] action_suggestion が具体的な実行単位になっている
- [ ] 医療・宗教・占術的な断定がない
- [ ] result guarantee 表現がない
- [ ] detail_open_rate / save_rate / route_open_rate が悪化していない
- [ ] API Contract test が通っている
- [ ] UI側の表示位置が確定している
```

### Active化判断

Recommendation v4 Active化は、Score v3 Active化より後に行う。

理由:

```markdown
- Ranking が安定しないと、表示文言の良し悪しを判断できない
- Recommendation v4 は説明層なので、まず候補選定の安定が必要
- 表示改善は ranking 改善と分けて測るべき
```

## 6. Measurement Design

### Event Candidates

```markdown
- recommendation_view
- recommendation_card_view
- recommendation_reason_v4_preview_view
- action_suggestion_v4_preview_view
- detail_open
- save_click
- route_open
- visit_done
- reflection_saved
- premium_preview_view
- premium_preview_click
- checkout_started
- premium_active
```

### Required Event Properties

```markdown
- session_id
- thread_id
- shrine_id
- rank
- source
- need_tags
- consultation_axis
- history_theme
- score_v2_total
- score_v3_final_score
- score_v3_shadow_rank
- current_rank
- reason_v4_preview_present
- action_suggestion_v4_preview_present
- user_type
```

## 7. Rollback Plan

Active化する場合は、必ず rollback できる状態にする。

### Required Flags

```markdown
- SCORE_V3_ACTIVE
- RECOMMENDATION_REASON_V4_ACTIVE
- ACTION_SUGGESTION_V4_ACTIVE
- RECOMMENDATION_V4_DEBUG_ENABLED
```

### Rollback Rule

以下のいずれかが出た場合、即 rollback を検討する。

```markdown
- detail_open_rate が現行比 -10%以上
- save_rate が現行比 -10%以上
- route_open_rate が現行比 -10%以上
- error rate が増える
- preview payload 欠落が増える
- UI表示で重大な崩れが出る
```

## 8. Implementation Plan

### Phase A: Readiness Docs

```markdown
- [x] Recommendation v4 Phase2 完了
- [ ] Active化判断基準docs作成
- [ ] Shadow Mode KPI固定
- [ ] CVR計測KPI固定
- [ ] Rollback Plan固定
```

### Phase B: Measurement

```markdown
- [ ] Shadow Mode 集計方法確認
- [ ] CVR event の保存箇所確認
- [ ] dashboard で見る指標を整理
- [ ] 30セッション観測
- [ ] 100セッション観測
```

### Phase C: Decision

```markdown
- [ ] Score v3 Active化可否判断
- [ ] Recommendation v4 Active化可否判断
- [ ] weight調整案作成
- [ ] rollback plan確認
```

## 9. Final Decision Rule

Active化は以下の順で行う。

```text
Score v3 Shadow Mode
↓
Score v3 Active化判断
↓
Score v3 Active化
↓
Recommendation v4 Preview継続観測
↓
Recommendation v4 Active化判断
↓
Recommendation v4 Active化
```

最終判断は、単一指標ではなく以下の組み合わせで行う。

```markdown
- 候補品質
- detail_open_rate
- save_rate
- route_open_rate
- reflection_saved_rate
- internal key leakage
- safety copy quality
- rollback可能性
```

## TODO

```markdown
- [x] Recommendation v4 Phase2完了
- [x] Shadow Modeで見るKPIを固定
- [x] Score v3 Active化条件を定義
- [x] Recommendation v4 Active化条件を定義
- [x] CVR計測対象を整理
- [x] 重み調整の判断ルールを定義
- [x] Rollback Planを定義
- [ ] backend pytest
- [ ] py_compile
```

## Next Step

このdocsを追加した後、次は実装ではなく計測確認に進む。

確認対象:

```text
backend/temples/services/recommendation_algorithm_v3.py
backend/temples/services/concierge_chat.py
backend/temples/services/behavior_funnel.py
backend/temples/tests/api/test_score_v3_dashboard_api.py
```
