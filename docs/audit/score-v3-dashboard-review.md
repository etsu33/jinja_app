


# Score v3 Dashboard Review

## 目的

Phase5の締めとして、現状の Score v3 Dashboard が active / rollback 判断と Behavior Funnel分析に十分な情報を表示できているかを監査する。

本監査では、以下を確認する。

- Score v3 Dashboard API が何を返しているか
- Web Debug Dashboard が何を表示しているか
- Behavior Funnelの分母・件数が見えるか
- ActionEvent系の指標が見えるか
- Mobile欠落ログの影響を判断できるか
- Score v3 active判断に必要な注意点が明示されているか

## 前提

以下は完了済み。

- Phase5 Behavior Measurement Plan
- Behavior Funnel Current State Audit
- Mobile Action Suggestion Event Audit
- Backend `ScoreV3DashboardView` 実装済み
- Web `/debug/score-v3-dashboard` 実装済み
- `behavior_funnel` service実装済み
- `score_v3_dashboard_api` test実装済み

## 現在のDashboard構成

### Backend API

対象:

- `backend/temples/api/views/score_v3_dashboard.py`

現在の状態:

```text
GET /api/concierge/score-v3/dashboard/
```

権限:

```text
IsAdminUser
```

返却元:

```python
build_score_v3_dashboard_summary(from_dt=from_dt, to_dt=to_dt)
```

判断:

管理者限定のDebug Dashboard APIとしては妥当。

## Backend summary

対象:

- `backend/temples/services/concierge_observability.py`

現在返している構造:

```python
return {
    "score_v3": correlation["score_v3"],
    "funnel": correlation["funnel"],
    "decision": _build_decision(correlation["score_v3"]),
}
```

返却内容:

```text
score_v3
funnel
decision
```

判断:

Score v3の基本観測と判定は返せている。

## Web Dashboard

対象:

- `apps/web/src/app/debug/score-v3-dashboard/ScoreV3DashboardClient.tsx`
- `apps/web/src/features/scoreV3Dashboard/fetchDashboard.ts`
- `apps/web/src/features/scoreV3Dashboard/types.ts`

表示されているもの:

### Score v3 観測値

```text
top1_changed_rate_avg
activation_candidate_rate
avg_delta
max_abs_delta_max
```

### Behavior Funnel

```text
route_open_rate
save_rate
visit_done_rate
reflection_saved_rate
```

### Decision

```text
active_candidate
rollback_required
reasons
```

判断:

Score v3の基本状態とファネルrateは見える。
ただし、Phase5の判断には不足がある。

## Behavior Funnel Serviceの現在地

対象:

- `backend/temples/services/behavior_funnel.py`

`BehaviorFunnelMetrics` は以下を持っている。

```python
@dataclass(frozen=True)
class BehaviorFunnelMetrics:
    detail_view_count: int
    route_open_count: int
    save_count: int
    visit_count: int
    reflection_count: int
    save_to_visit_cvr: float
    visit_to_reflection_cvr: float
```

つまり、backend内部では以下を取得できる。

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
save_to_visit_cvr
visit_to_reflection_cvr
```

## Dashboardで欠落しているもの

### 1. Funnel count

現在Dashboardに表示されているのはrateのみ。

表示なし:

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
```

問題:

rateだけでは分母の信頼性が分からない。

例:

```text
detail_view_count = 1
route_open_rate = 100%
```

これは改善判断としては弱い。

判断:

Dashboardにはcount表示が必要。

### 2. CVR系

backend内部では以下を持っている。

```text
save_to_visit_cvr
visit_to_reflection_cvr
```

しかし、Dashboardレスポンス / UIには出ていない。

問題:

- save後にvisitへ進んだかが見えない
- visit後にreflectionへ進んだかが見えない
- `reflection_saved_rate` が detail_view 分母であることの補助指標がない

判断:

`visit_to_reflection_cvr` は特にDashboardへ出す価値がある。

### 3. ActionEvent系

Backendには以下がある。

```text
ActionEvent
action_started
action_completed
action_completion_observation
```

しかしDashboardには以下がない。

```text
action_started_count
action_completed_count
started_to_completed_rate
```

問題:

- `action_suggestion_v4_preview` の効果がDashboardで見えない
- WebはActionEvent送信済みだが、Dashboard上で活用されていない
- MobileはActionEvent送信が未実装なので、欠落影響を可視化できない

判断:

ActionEvent指標は後続Dashboard改善候補。

### 4. Mobile欠落ログの注意

Behavior Funnel Current State Auditで、Mobileは以下が欠落候補と整理済み。

```text
save
visit_done
reflection_saved
action_started
action_completed
```

しかしDashboardには、この注意が表示されていない。

問題:

Dashboardの `save_rate` / `visit_done_rate` / `reflection_saved_rate` は、Mobile分が過小評価されている可能性がある。

判断:

Dashboard UIまたはdocsに注意書きが必要。

### 5. reflection_saved_rateの上限超過可能性

`reflection_saved_rate` は `reflection_count / detail_view_count` で計算される。

そのため、1つのdetail_viewに対して複数reflectionが保存されると、1.0を超える可能性がある。

既存docsにも注意あり:

- `docs/audit/score-v3-shadow-mode-readiness.md`

問題:

Dashboard UIにはこの注意が見えていない。

判断:

`reflection_saved_rate` は単独判断に使わず、`visit_to_reflection_cvr` と併用する必要がある。

## 現状まとめ

| 項目 | Backend | Dashboard API | Web UI | 判断 |
|---|---|---|---|---|
| Score v3 metrics | あり | あり | あり | OK |
| Decision | あり | あり | あり | OK |
| Funnel rate | あり | あり | あり | OK |
| Funnel count | あり | なし | なし | 不足 |
| save_to_visit_cvr | あり | なし | なし | 不足 |
| visit_to_reflection_cvr | あり | なし | なし | 不足 |
| ActionEvent count | あり | なし | なし | 不足 |
| Mobile欠落ログ注意 | docsあり | なし | なし | 不足 |
| reflection rate注意 | docsあり | なし | なし | 不足 |

## Score v3 active判断への影響

現状Dashboardだけでactive判断するのはまだ弱い。

理由:

- rateの分母件数が見えない
- Mobile後段ログが欠落候補
- Action Suggestion効果がDashboardに出ていない
- reflection_saved_rateは上限超過し得る

ただし、Score v3の基本監視としては有効。

```text
Score v3 shadow modeの粗い安全確認: 可能
Phase5の行動改善判断: 不十分
active化の最終判断: Dashboard単体では不十分
```

## 改善候補

### Priority A: Funnel countをDashboardに追加

目的:

rateの信頼性を判断できるようにする。

追加候補:

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
```

候補ブランチ:

`feature/score-v3-dashboard-funnel-counts`

### Priority B: CVRをDashboardに追加

目的:

後段ファネルの質を見る。

追加候補:

```text
save_to_visit_cvr
visit_to_reflection_cvr
```

候補ブランチ:

`feature/score-v3-dashboard-cvr-metrics`

### Priority C: Dashboardに注意書きを追加

目的:

Mobile欠落ログとreflection rateの誤読を防ぐ。

追加候補:

```text
- Mobileのsave / visit / reflection / action eventは未接続候補
- reflection_saved_rateはdetail_view_count分母のため1.0超過可能性あり
- active判断ではcount / CVR / Mobile欠落状況と併用する
```

候補ブランチ:

`refactor/score-v3-dashboard-notes`

### Priority D: ActionEvent metricsをDashboardに追加

目的:

Action Suggestion効果を見る。

追加候補:

```text
action_started_count
action_completed_count
started_to_completed_rate
completed_with_reflection_count
completed_to_reflection_rate
```

候補ブランチ:

`feature/score-v3-dashboard-action-event-metrics`

## 推奨判断

次は **Score v3 Dashboard Funnel Counts** を先に進めるのが安全。

理由:

- rateの分母が見えない問題が最も基礎的
- backend内部にはcountがすでにある
- UI追加も小さく切れる
- ActionEventより先に、既存funnelの信頼性を上げるべき

ただし、最終判断は母艦に差し戻す。

## 今回のPRでやること

- Score v3 Dashboardの現状を文書化する
- Backend / API / Web UIの表示状況を整理する
- Dashboardの不足項目を整理する
- active判断への影響を整理する
- 次PR候補を整理する

## 今回のPRでやらないこと

- Dashboard APIは変更しない
- Web UIは変更しない
- ActionEvent集計は追加しない
- Mobileログ接続はしない
- Score v3 active化はしない

## 次PR候補

### 1. Score v3 Dashboard Funnel Counts

ブランチ候補:

`feature/score-v3-dashboard-funnel-counts`

対象候補:

- `backend/temples/services/behavior_funnel.py`
- `backend/temples/services/concierge_observability.py`
- `backend/temples/tests/api/test_score_v3_dashboard_api.py`
- `apps/web/src/features/scoreV3Dashboard/types.ts`
- `apps/web/src/app/debug/score-v3-dashboard/ScoreV3DashboardClient.tsx`

目的:

- Dashboard API / UIへfunnel countを追加する

### 2. Score v3 Dashboard Notes

ブランチ候補:

`refactor/score-v3-dashboard-notes`

対象候補:

- `apps/web/src/app/debug/score-v3-dashboard/ScoreV3DashboardClient.tsx`

目的:

- Mobile欠落ログとreflection rate注意をUIに表示する

### 3. Score v3 Dashboard Action Event Metrics

ブランチ候補:

`feature/score-v3-dashboard-action-event-metrics`

対象候補:

- `backend/temples/services/action_completion_observation.py`
- `backend/temples/services/concierge_observability.py`
- `backend/temples/tests/api/test_score_v3_dashboard_api.py`
- `apps/web/src/features/scoreV3Dashboard/types.ts`
- `apps/web/src/app/debug/score-v3-dashboard/ScoreV3DashboardClient.tsx`

目的:

- action_started / completed 系の指標をDashboardへ追加する

## TODO

```markdown
# Score v3 Dashboard Review

- [x] develop最新版化
- [x] audit/score-v3-dashboard-review 作成
- [x] Dashboard API確認
- [x] Dashboard summary確認
- [x] Web Dashboard確認
- [x] Behavior Funnel Service確認
- [x] API Test確認
- [x] 表示済み指標整理
- [x] 欠落指標整理
- [x] active判断への影響整理
- [x] 次PR候補整理
- [x] docs/audit/score-v3-dashboard-review.md を復旧
```

## 完了条件

- Score v3 Dashboardの現状が文書化されている
- Dashboardで見える指標 / 見えない指標が整理されている
- Phase5監査としてactive判断に足りないものが明確になっている
- 次に改善すべきDashboard PR候補が明確になっている
