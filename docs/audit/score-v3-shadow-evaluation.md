

# Score v3 Shadow Evaluation

## 目的

Score v3 の shadow 評価フェーズとして、既存ランキングを変更せずに Score v2 / Score v3 の差分、active 化条件、behavior funnel との突合経路を確認する。

この監査では重み変更や active 化は行わず、実測ログを蓄積する前段階として、評価可能な状態になっているかを確認する。

## 対象範囲

- Score v3 dashboard API
- Score v3 AB observation 集計
- Score v2 / Score v3 差分評価
- active / rollback 判定
- behavior funnel との突合
- 30セッション以上のログ取得方法

## 確認した実装

### Dashboard API

Score v3 評価用の管理者向け API が存在する。

- path: `/api/concierge/score-v3/dashboard/`
- view: `backend/temples/api/views/score_v3_dashboard.py`
- permission: `IsAdminUser`
- query params:
  - `from`
  - `to`

この API は `build_score_v3_dashboard_summary()` を呼び出し、Score v3 summary / behavior funnel / decision を返す。

## 集計経路

### Score v3 observation 集計

実装箇所:

- `backend/temples/services/concierge_observability.py`
- `summarize_score_v3_ab_observations()`

集計対象:

- `result_state._score_v3_debug.score_v3_ab_observation`

集計項目:

- `count`
- `top1_changed_rate_avg`
- `activation_candidate_rate`
- `avg_delta`
- `max_abs_delta_avg`
- `max_abs_delta_max`

## Score v2 / Score v3 差分分析

Score v3 は shadow mode で既存ランキングを変更せず、以下の差分を観測する。

- 既存 top1 と Score v3 top1 が変わったか
- Score v2 系スコアと Score v3 の差分
- 平均差分
- 最大絶対差分

確認指標:

- `top1_changed_rate_avg`
- `avg_delta`
- `max_abs_delta_avg`
- `max_abs_delta_max`

## Active 化条件

active 化判断は Dashboard API の `decision.active_candidate` で確認する。

現状の判断材料:

- `activation_candidate_rate`
- `top1_changed_rate_avg`
- `avg_delta`
- `max_abs_delta_max`

テスト確認:

- `backend/temples/tests/api/test_score_v3_dashboard_api.py`
- `test_active_candidate_true_when_criteria_met`
- `test_rollback_required_true_when_criteria_met`

## Rollback 条件

rollback 判断は Dashboard API の `decision.rollback_required` で確認する。

主な判断材料:

- `top1_changed_rate_avg` が高い
- `avg_delta` が大きい
- `max_abs_delta_max` が大きい
- `activation_candidate_rate` が低い

## Behavior Funnel との突合

Score v3 summary は behavior funnel と突合される。

実装箇所:

- `backend/temples/services/behavior_funnel.py`
- `build_score_v3_funnel_correlation_summary()`
- `get_behavior_funnel_metrics()`

確認指標:

- `route_open_rate`
- `save_rate`
- `visit_done_rate`
- `reflection_saved_rate`

行動ログの主な参照元:

- `ShrineInteractionLog`
  - `detail_view`
  - `route_open`
- Favorite
  - save 相当
- `ActionEvent`
  - `action_started`
  - `action_completed`
- `ShrineReflection`
  - reflection saved 相当

## 30セッション以上のログ取得方法

Score v3 評価は `ConciergeRecommendationLog` に保存された `result_state._score_v3_debug.score_v3_ab_observation` を集計する。

実測評価に進む条件:

- 最低 30 セッション
- 推奨 100 セッション
- 最低 7 日間の shadow mode 運用

Dashboard API で期間指定して確認する。

```bash
curl -s "http://127.0.0.1:8000/api/concierge/score-v3/dashboard/" -H "Authorization: Bearer $ACCESS" | python -m json.tool
```

期間指定例:

```bash
curl -s "http://127.0.0.1:8000/api/concierge/score-v3/dashboard/?from=2026-07-01T00:00:00%2B09:00&to=2026-07-08T00:00:00%2B09:00" -H "Authorization: Bearer $ACCESS" | python -m json.tool
```

## Weight 調整方針

現段階では weight 変更は行わない。

理由:

- 評価経路は整っている
- ただし実測セッション数が不足している
- 実データなしで weight を変更すると、改善ではなく推測による調整になる

実測後の判断方針:

- `top1_changed_rate_avg` が高い場合
  - state / history / behavior の重みを再確認する
- `max_abs_delta_max` が大きい場合
  - direction / action / reflection など補助シグナルの重みを下げる候補にする
- `activation_candidate_rate` が安定して高い場合
  - active 化検討に進む
- funnel が悪化している場合
  - active 化は見送る

## Active 化判断

現時点では active 化しない。

判断:

- Score v3 は shadow mode として評価可能
- Dashboard API と集計経路は存在する
- behavior funnel との突合も可能
- ただし、30セッション以上の実測ログがまだ判断材料として必要

## 結論

Score v3 は shadow 評価に必要な実装が揃っている。

現時点で追加実装や weight 変更は不要。

次フェーズでは、最低30セッション以上の実測ログを蓄積し、Dashboard API で以下を確認する。

- `top1_changed_rate_avg`
- `activation_candidate_rate`
- `avg_delta`
- `max_abs_delta_max`
- `route_open_rate`
- `save_rate`
- `visit_done_rate`
- `reflection_saved_rate`

実測値を確認した後に、Score v3 active 化、weight 調整、または shadow 継続を判断する。
