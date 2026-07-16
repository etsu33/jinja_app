# Score v3 Shadow Mode Readiness Audit

## 目的

Recommendation Score v3 の shadow mode 実装・保存経路・dashboard反映・behavior funnel 接続状況を確認し、active化前に不足しているログや判断材料を整理する。

---

## behavior_funnel確認

- get_behavior_funnel_metrics は backend persisted records を正本にしている
- route_open は ShrineInteractionLog.route_open
- save は Favorite
- visit_done は Visit.status="added"
- reflection_saved は ShrineReflection
- Score v3 dashboard では detail_view_count を分母にして各rateを算出する

## 注意点

reflection_saved_rate は reflection_count / detail_view_count であるため、1つの detail_view に対して複数 reflection が保存されると 1.0 を超える可能性がある。

このため、active化判断では reflection_saved_rate を単独KPIにせず、visit_to_reflection_cvr と併用する。

---

## 次PR候補

- Score v3 dashboard の分母定義をdocsに追記
- reflection_saved_rate の上限超過可能性をUIまたは説明に明記
- active化判断では top1_changed_rate / activation_candidate_rate / route_open_rate / save_rate / visit_to_reflection_cvr を併用する
