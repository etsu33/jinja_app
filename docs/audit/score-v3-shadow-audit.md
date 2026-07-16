# Score v3 Shadow Mode Audit

## 目的

Recommendation Score v3 が既存ランキングを壊さず、shadow mode として観測・保存・集計できているかを確認する。

## 監査結果

### Score v3 mode

- `resolve_score_v3_mode_detail()` が `SCORE_V3_MODE` を読む。
- 未設定時は `shadow`。
- 不正値も `shadow` に倒す。
- `SCORE_V3_MODE=active` の場合のみ `breakdown.score_v3` を sort key に使う。

### 計算経路

- `backend/temples/services/concierge_chat_ranking.py`
  - `build_recommendation_score_v3_breakdown()`
  - `resolve_score_v3_history_signal()`
  - `rec["breakdown"]["score_v3"]`
  - `rec["breakdown"]["score_v3_detail"]`

### shadow分離

- shadow時は既存の `rec["_score_total"]` を sort key に使う。
- Score v3は `breakdown.score_v3` / `score_v3_detail` として観測用に付与される。
- 既存 ranking には影響しない。

### 観測経路

- `backend/temples/services/concierge_chat.py`
  - `_build_score_v3_debug_payload()`
  - `_build_score_v3_observer_items()`
  - `score_v3_shadow_observation`
  - `score_v3_ab_observation`
  - `dashboard_summary`

### 保存経路

- `backend/temples/services/concierge_observability.py`
  - `save_concierge_recommendation_log()`
  - `result_state._score_v3_debug.score_v3_ab_observation`

### 集計経路

- `backend/temples/services/concierge_observability.py`
  - `summarize_score_v3_ab_observations()`
  - `build_score_v3_dashboard_summary()`

### Dashboard API

- `backend/temples/tests/api/test_score_v3_dashboard_api.py`
  - Score v3 summary
  - funnel correlation
  - admin access

### 行動ログ

- `ShrineInteractionLog`
  - `detail_view`
  - `route_open`
- Favorite
  - save相当
- `ActionEvent`
  - action_started
  - action_completed
- `ShrineReflection`
  - reflection_saved
- `behavior_funnel.py`
  - detail_view / route_open / save / visit_done / reflection_saved を集計

## 確認できたこと

- Score v3はshadow modeで観測可能。
- top1_changed_rate / avg_delta / max_abs_delta は生成・保存・集計経路がある。
- behavior funnel と突合する経路がある。
- active化は `SCORE_V3_MODE=active` に限定される。

## 注意点

- `resolve_score_sort_key()` のコメントに「現時点では shadow 固定」とあるが、実装上は `SCORE_V3_MODE=active` を許可している。
- コメントと実装の整合性は次PRで修正候補。
- active化判断は30セッション以上の観測後に行う。

## 結論

Score v3 は現時点で shadow mode として分離されており、既存ランキングを壊さずに観測できる状態。
次フェーズでは30セッション以上のログを収集し、Score v2との差分とbehavior funnelとの相関を確認する。
