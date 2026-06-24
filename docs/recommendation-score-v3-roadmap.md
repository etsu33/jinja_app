

# Recommendation Score v3 Roadmap

## 目的

Recommendation Score v3 を、いきなり本実装せず、行動・プロフィール・方位・参拝・振り返りの順に段階実装する。

推薦順位を大きく揺らすのではなく、既存の相談内容ベースの推薦を維持しながら、補助シグナルを安全に積み上げる。

---

## Phase1: Behavior Profile

### ゴール

軽い行動シグナルを推薦補助に使える状態にする。

### 対象シグナル

- save
- detail_view
- route_open

### 実装方針

- 行動ログから Behavior Profile を生成する
- visit_done / reflection_saved はここでは扱わない
- breakdown に behavior_signal を追加する
- スコア影響は中程度に留める

### 完了条件

- [ ] Behavior Profile の型を定義
- [ ] save / detail_view / route_open を集計
- [ ] behavior_signal を breakdown に追加
- [ ] concierge 系テストが通る

---

## Phase2: DerivedProfile

### ゴール

UserProfile から生成した派生プロフィールを、推薦補助シグナルとして安定利用する。

### 対象シグナル

- 九星気学
- 五行
- ライフパス

### 実装方針

- 既存の DerivedProfile を利用する
- 占術要素だけで順位を決めない
- profile_signal は最大 +0.03 程度に抑える

### 完了条件

- [ ] DerivedProfile を Recommendation Score v3 の入力に含める
- [ ] profile_signal の重みを明文化
- [ ] breakdown に profile_signal を保持
- [ ] concierge 系テストが通る

---

## Phase3: DirectionProfile

### ゴール

吉方位を補助シグナルとして扱える状態にする。

### 対象シグナル

- luckyDirection

### 実装方針

- DirectionProfile を Recommendation Score v3 の入力に含める
- 方位だけで順位を決めない
- 現時点では placeholder / 簡易計算を許容する
- スコア影響は最大 +0.01〜0.02 に抑える

### 完了条件

- [ ] DirectionProfile を Score v3 入力に含める
- [ ] direction_signal を breakdown に追加
- [ ] 方位情報がない神社では加点しない
- [ ] concierge 系テストが通る

---

## Phase4: visit_done

### ゴール

「実際に参拝した」行動を強い行動シグナルとして扱う。

### 対象シグナル

- visit_done

### 実装方針

- Behavior Profile とは分離する
- 参拝済み神社への過剰な再推薦を避ける
- 同じテーマで再訪に意味がある場合のみ補助する

### 完了条件

- [ ] visit_done を Action Profile として定義
- [ ] visit_signal を breakdown に追加
- [ ] 参拝済み神社の扱いを定義
- [ ] concierge 系テストが通る

---

## Phase5: reflection_saved

### ゴール

参拝後の振り返りを、行動変化の質として推薦に反映する。

### 対象シグナル

- reflection_saved

### 実装方針

- Reflection Profile として Behavior Profile から分離する
- reflection 内容の意味解析は別フェーズにする
- まずは保存有無をシグナル化する

### 完了条件

- [ ] reflection_saved を Reflection Profile として定義
- [ ] reflection_signal を breakdown に追加
- [ ] reflection 内容の解析は未実装として明示
- [ ] concierge 系テストが通る

---

## Phase6: Score v3 完成

### ゴール

User State Profile / Behavior Profile / DerivedProfile / DirectionProfile / Action Profile / Reflection Profile を統合した Recommendation Score v3 を完成させる。

### Score v3 入力

- User State Profile
- Behavior Profile
- DerivedProfile
- DirectionProfile
- Action Profile
- Reflection Profile

### 計算式ドラフト

```text
score_v3 =
  state_signal
  + history_signal
  + distance_signal
  + behavior_signal
  + profile_signal
  + direction_signal
  + action_signal
  + reflection_signal
```

### 実装方針

- User State Profile を主シグナルにする
- Behavior / Action / Reflection を行動学習として扱う
- DerivedProfile / DirectionProfile は補助シグナルに留める
- breakdown を必ず残し、順位変動の説明可能性を担保する

### 完了条件

- [ ] Score v3 の統合関数を実装
- [ ] breakdown に各シグナルを保持
- [ ] 既存推薦より大きく劣化しない
- [ ] concierge 系テストが通る
- [ ] 代表ケースで順位変動を確認

---

---

## Activate 準備方針

### Shadow Observation の確認

`_debug.score_v3_shadow_observation.summary` で以下を確認する。

| 指標 | 条件 | 意味 |
|---|---|---|
| `top1_changed_rate` | 0.0（top1 が変わらない）| 既存 ranking と乖離がない |
| `max_abs_delta` | 0.5 未満 | 個別スコアの変動が小さい |
| `activation_candidate` | `true` | 上記2条件 + score_v3 が全件計算済み |

ログ確認例:

```
[score_v3_shadow_summary] top1_changed=False avg_delta=-0.12 max_abs_delta=0.25 activation_candidate=True
```

### Active Mode 準備（実装済み）

`concierge_chat_ranking.py` に以下の helper を追加済み。

- `resolve_score_v3_mode()` — 現在は `"shadow"` 固定。将来は環境変数 `SCORE_V3_ACTIVE=1` で `"active"` に切り替える（別 PR）
- `resolve_score_sort_key(rec, *, score_v3_mode)` — sort_key の切替口。`"active"` 時は `breakdown.score_v3`、それ以外は `rec["_score_total"]` を返す

`concierge_chat.py` の `_sort_chat_recommendations()` は `resolve_score_sort_key()` 経由でソートする。
`_debug["score_v3_mode"]` に現在のモードを記録する。

### Active 化の手順

1. shadow observation を複数セッションにわたって確認する
2. `activation_candidate` が安定して `true` になることを確認する
3. 環境変数 `SCORE_V3_ACTIVE=1` を `resolve_score_v3_mode()` に組み込む（別 PR）
4. `_score_total` の sort_key を score_v3 に切り替えることで active 化する
5. デフォルトは shadow のまま維持する

### 有効化手順

1. shadow observation ログで `activation_candidate` が安定して `true` になることを確認する
   - `top1_changed_rate` が 0.0
   - `max_abs_delta` が 0.5 未満
2. 環境変数を設定して active にする

   ```bash
   # Render / .env
   SCORE_V3_MODE=active
   ```

3. 不正値・未設定は自動的に `shadow` にフォールバックする
4. Rollback は `SCORE_V3_MODE=shadow` に戻すだけ（コード変更不要）

### active モード時のテスト注意

順位固定を前提とした eval テスト（`test_concierge_eval_queries` 等）は `SCORE_V3_MODE=active` 時に skip される。  
これは active モードで score_v3 によって順位が変わることが**正しい動作**であるため。

```bash
# shadow（本番デフォルト）: 298 passed
pytest -k concierge

# active smoke: 264 passed / 34 skipped（順位固定テストが skip）
SCORE_V3_MODE=active pytest -k concierge
```

### 重み調整基準

shadow observation の `summary` を見て以下を判断する。

| 指標 | 対応 |
|---|---|
| `top1_changed_rate` が高い | `state` weight を上げる（need スコアの影響を強くする）|
| `max_abs_delta` が大きい | `profile` / `direction` / `action` / `reflection` の補助重みを下げる |
| `activation_candidate` が不安定 | active 化を延期し、shadow observation を継続する |
| active 化後も top1 変動が多い | `SCORE_V3_MODE=shadow` に戻して原因調査 |

activation_candidate = true の目安:
- `top1_changed_rate = 0.0`（複数セッションで継続）
- `max_abs_delta < 0.5`
- `score_v3_available_count == recommendation_count`

active 化後も shadow observation を維持する（`_debug.score_v3_shadow_observation` は常に出力される）。

### やらないこと（この段階）

- `score_total` を変更しない
- `_score_total`（sort key）を変更しない
- `mode="active"` をデフォルトにしない
- DB 変更・migration しない
- ranking.py のスコア計算ロジックを変更しない

### PostHog 対応 TODO

PostHog 送信 helper が未実装のため、以下をイベントとして送ることを検討する（別 PR）。

```
イベント名: score_v3_ab_observed
properties:
  - mode
  - top1_changed_rate
  - avg_delta
  - max_abs_delta
  - activation_candidate
```

---

## Weight Optimization 準備

### 集計 helper

`summarize_score_v3_ab_observations(observations)` で複数レスポンスの `score_v3_ab_observation` を集計する。

```python
from temples.services.concierge_observability import summarize_score_v3_ab_observations

summary = summarize_score_v3_ab_observations([
    {"mode": "shadow", "top1_changed_rate": 0.0, "avg_delta": -0.12,
     "max_abs_delta": 0.25, "activation_candidate": True},
    ...
])
# {
#   "count": N,
#   "top1_changed_rate_avg": 0.1,
#   "activation_candidate_rate": 0.8,
#   "avg_delta": -0.05,
#   "max_abs_delta_avg": 0.2,
#   "max_abs_delta_max": 0.45,
# }
```

### 重み調整基準

集計結果をもとに以下を判断する。

| 指標 | 閾値 | 対応 |
|---|---|---|
| `top1_changed_rate_avg` | > 0.1 | `state` weight を上げる（need スコアの影響を強める）|
| `max_abs_delta_max` | > 0.5 | `profile` / `direction` / `action` / `reflection` の補助 weight を下げる |
| `activation_candidate_rate` | < 0.8 | active 化を延期し、shadow 観測を継続する |
| `avg_delta` | 負方向に大きい | score_v3 が score_total より体系的に低い → behavior weight を調整 |

### behavior_funnel との突合

`route_open` / `save` / `visit_done` / `reflection_saved` の発生率と  
`avg_delta` / `max_abs_delta` を突合し、行動シグナルの効き具合を確認する。

```python
from temples.services.concierge_observability import correlate_score_v3_with_funnel
from temples.services.behavior_funnel import get_behavior_funnel_metrics
import dataclasses

funnel = dataclasses.asdict(get_behavior_funnel_metrics())
result = correlate_score_v3_with_funnel(
    score_v3_observations=[...],  # _debug["score_v3_ab_observation"] のリスト
    funnel=funnel,
)
# {
#   "score_v3": {
#     "top1_changed_rate_avg": 0.1,
#     "activation_candidate_rate": 0.8,
#     "avg_delta": -0.05,
#     "max_abs_delta_max": 0.45,
#   },
#   "funnel": {
#     "route_open_rate": 0.3,
#     "save_rate": 0.2,
#     "visit_done_rate": 0.1,
#     "reflection_saved_rate": 0.05,
#   },
#   "analysis_hint": "compare_score_v3_delta_with_behavior_funnel",
# }
```

#### 突合による判断基準

| 状況 | 判断 |
|---|---|
| `top1_changed_rate` 低 ＋ funnel 改善（route_open / save 増）| score_v3 の重みは有望、active 化を検討 |
| `top1_changed_rate` 高 ＋ funnel 悪化 | 補助シグナルの重みを弱める、active 化を延期 |
| `max_abs_delta` 大 ＋ `visit_done_rate` 低 | action_signal の weight を下げる |
| `activation_candidate_rate` 低 ＋ `reflection_saved_rate` 高 | reflection_signal が score_v3 に強く出すぎている可能性 |

active 化の最終判断には funnel 指標を必ず含める。`activation_candidate_rate` だけで判断しない。

### 重み変更の手順（別 PR）

1. `summarize_score_v3_ab_observations` で集計・判断
2. `_SCORE_V3_WEIGHTS` の定数を変更（`concierge_chat_ranking.py`）
3. shadow observation で再度 `activation_candidate_rate` を確認
4. 安定したら active 化（`SCORE_V3_MODE=active`）

**本 PR では score_v3 の重みを変更しない。**

---

### PostHog 連携方針

#### 現時点の方針

PostHog 送信 helper は**未実装**。Score v3 の一次観測は以下を正本とする。

| 正本 | 用途 |
|---|---|
| recommendation log（`_debug.score_v3_ab_observation`） | セッション単位の生観測値 |
| dashboard API（`GET /api/concierge/score-v3/dashboard/`） | 集計値・判定結果 |

PostHog への送信は、将来 helper を追加した場合のみ行う。現時点では実装しない。

#### 将来実装する場合の event 定義

```
イベント名: score_v3_ab_observed

properties:
  mode                  # "shadow" | "active"
  top1_changed_rate     # セッション内の top1 変動率
  activation_candidate  # bool — セッション単位の activation_candidate
  avg_delta             # score_v3 - score_total の平均差分
  max_abs_delta         # セッション内の max_abs_delta
  route_open_rate       # funnel: route_open 発生率
  save_rate             # funnel: save 発生率
  visit_done_rate       # funnel: visit_done 発生率
  reflection_saved_rate # funnel: reflection_saved 発生率
```

#### dashboard との整合確認方針

- PostHog の各 property 値は dashboard API のレスポンス値と一致させる
- 不一致が生じた場合は dashboard API の値を正本とする
- PostHog は可視化・時系列分析用途に限定し、active 化 / rollback の判断には使わない

| 用途 | 使用するデータ源 |
|---|---|
| active 化 / rollback 判断 | dashboard API |
| 重み調整判断 | dashboard API + recommendation log |
| 時系列トレンド可視化 | PostHog（将来） |
| アラート・通知 | PostHog（将来） |

---

## やらないこと

- 占術だけで順位を決める
- 吉方位だけで順位を決める
- 人気ランキング化する
- 状態や人生を断定する
- 特定の神社を絶対視する
- breakdown なしでスコアを変更する

---

## 最終データフロー

```text
UserProfile
↓
DerivedProfile生成
↓
DirectionProfile生成
↓
ConciergeContext
↓
Recommendation Score v3
↓
推薦
↓
save / detail_view / route_open
↓
visit_done
↓
reflection_saved
↓
Behavior Profile 更新
↓
次回推薦
```
---

---

## Score v3 Dashboard Design

### 目的

Score v3 の shadow / active 観測結果と behavior funnel を突合し、active 化判断と rollback 判断に使える dashboard を設計する。

### 保存元

- `result_state._score_v3_debug`
- `_debug.score_v3_ab_observation`
- `_debug.dashboard_summary.score_v3`
- behavior funnel metrics

### Dashboard API 出力案

- top1_changed_rate
- activation_candidate_rate
- avg_delta
- max_abs_delta
- route_open_rate
- save_rate
- visit_done_rate
- reflection_saved_rate

### Active 判定レポート

- active 化してよいか
- rollback 条件に触れていないか
- funnel 指標が現行以上か
- score_v3 の delta が大きすぎないか

### 実装フェーズ

1. dashboard API 設計
2. backend 集計 API 実装
3. admin / debug 表示
4. active 判定レポート生成
5. PostHog / 外部 dashboard 連携

## Recommendation Score v3 Final Criteria

### Active 化条件

以下を複数期間で満たした場合のみ active 化を許可する。

| 指標 | 条件 |
|---|---|
| top1_changed_rate_avg | 0.10 以下 |
| activation_candidate_rate | 0.80 以上 |
| max_abs_delta_max | 0.50 未満 |
| route_open_rate | 現行以上 |
| save_rate | 現行以上 |
| visit_done_rate | 現行以上 |
| reflection_saved_rate | 現行以上 |

### Rollback 条件

以下のいずれかを満たした場合は `SCORE_V3_MODE=shadow` に戻す。

| 指標 | 条件 |
|---|---|
| top1_changed_rate_avg | 0.20 超 |
| max_abs_delta_max | 1.00 超 |
| route_open_rate | 悪化 |
| visit_done_rate | 悪化 |
| reflection_saved_rate | 悪化 |
| activation_candidate_rate | 0.50 未満 |

### Weight 調整ルール

| 状況 | 対応 |
|---|---|
| top1_changed_rate が高い | state weight を上げる |
| max_abs_delta が大きい | 補助シグナル weight を下げる |
| route_open が改善しない | behavior weight を見直す |
| visit_done が改善しない | action weight を見直す |
| reflection_saved が改善しない | reflection weight を見直す |

### Score v3 Final Weight

```text
state       = 0.45
behavior    = 0.25
profile     = 0.05
direction   = 0.02
action      = 0.02
reflection  = 0.01
history     = 0.10
distance    = 0.10
```

---

## Score v3 Dashboard API

### エンドポイント

`GET /api/concierge/score-v3/dashboard/`

### 権限

| 権限 | ステータス |
|---|---|
| 未認証 | 401 Unauthorized |
| 認証済み・非 staff | 403 Forbidden |
| admin / superuser | 200 OK |

権限クラス: `IsAdminUser`

### Response 例

```json
{
  "score_v3": {
    "top1_changed_rate_avg": 0.05,
    "activation_candidate_rate": 0.92,
    "avg_delta": -0.08,
    "max_abs_delta_max": 0.31
  },
  "funnel": {
    "route_open_rate": 0.34,
    "save_rate": 0.22,
    "visit_done_rate": 0.11,
    "reflection_saved_rate": 0.06
  },
  "decision": {
    "active_candidate": true,
    "rollback_required": false,
    "reasons": []
  }
}
```

### `active_candidate` 判定条件

以下をすべて満たす場合に `true`。

| 指標 | 条件 |
|---|---|
| `top1_changed_rate_avg` | 0.10 以下 |
| `activation_candidate_rate` | 0.80 以上 |
| `max_abs_delta_max` | 0.50 未満 |
| `route_open_rate` | ベースライン以上 |
| `save_rate` | ベースライン以上 |
| `visit_done_rate` | ベースライン以上 |
| `reflection_saved_rate` | ベースライン以上 |

いずれか1つでも満たさない場合は `false`。`reasons` にどの条件が未達かを文字列リストで返す。

### `rollback_required` 判定条件

以下のいずれかを満たす場合に `true`。

| 指標 | 条件 |
|---|---|
| `top1_changed_rate_avg` | 0.20 超 |
| `max_abs_delta_max` | 1.00 超 |
| `route_open_rate` | ベースラインより悪化 |
| `visit_done_rate` | ベースラインより悪化 |
| `reflection_saved_rate` | ベースラインより悪化 |
| `activation_candidate_rate` | 0.50 未満 |

`rollback_required = true` の場合、`reasons` に該当条件を列挙する。


## Score v3 Data Collection Plan

### 目的

Score v3 を active 化する前に、十分な推薦ログと行動ファネルを蓄積し、active 化判断をデータで行う。

### 観測期間

- 最低 30 セッション
- 推奨 100 セッション
- 最低 7 日間は shadow mode で観測する

### 観測指標

- top1_changed_rate
- activation_candidate_rate
- avg_delta
- max_abs_delta

### Funnel Correlation

以下の行動指標と突合する。

- route_open_rate
- save_rate
- visit_done_rate
- reflection_saved_rate

### Weight Optimization

以下の weight を実測値で検証する。

- state = 0.45
- behavior = 0.25
- profile = 0.05
- direction = 0.02
- action = 0.02
- reflection = 0.01

### Final Decision

active 化は以下を満たした場合のみ検討する。

- top1_changed_rate_avg <= 0.10
- activation_candidate_rate >= 0.80
- max_abs_delta_max < 0.50
- funnel 指標が悪化していない
- rollback 手順が確認済み


### やらないこと

- 実データなしで weight を変更しない
- dashboard を見ずに active 化しない
- `SCORE_V3_MODE=active` をデフォルトにしない


### Observation Report Template

Score v3 の active 化判断では、以下の形式で観測結果を記録する。

```markdown
# Score v3 Observation Report

## 観測期間

- 開始日:
- 終了日:
- 観測セッション数:
- 観測モード: shadow

## Dashboard API Snapshot

- top1_changed_rate_avg:
- activation_candidate_rate:
- avg_delta:
- max_abs_delta_max:

## Funnel Snapshot

- route_open_rate:
- save_rate:
- visit_done_rate:
- reflection_saved_rate:

## Active 化判定

- active_candidate:
- rollback_required:
- 判定理由:

## Weight Review

- state weight 0.45:
- behavior weight 0.25:
- profile weight 0.05:
- direction weight 0.02:
- action weight 0.02:
- reflection weight 0.01:

## Rollback 確認

- `SCORE_V3_MODE=shadow` へ戻せること:
- rollback_required 条件に該当していないこと:
- active 化後も dashboard API で継続観測できること:

## Final Decision

- active 化する / 延期する:
- 理由:
- 次の対応:
```


### Observation Report: 2026-06-24 Local Dashboard Snapshot

#### 観測期間

- 開始日: 2026-06-24
- 終了日: 2026-06-24
- 観測セッション数: dashboard API 集計値に依存
- 観測モード: shadow
- 環境: local

#### Dashboard API Snapshot

```json
{
  "score_v3": {
    "top1_changed_rate_avg": 0.083333,
    "activation_candidate_rate": 0.916667,
    "avg_delta": 0.18,
    "max_abs_delta_max": 0.36
  },
  "funnel": {
    "route_open_rate": 0.0,
    "save_rate": 0.0,
    "visit_done_rate": 0.0,
    "reflection_saved_rate": 0.0
  },
  "decision": {
    "active_candidate": true,
    "rollback_required": false,
    "reasons": [
      "funnel_degradation_check_pending: no baseline to compare"
    ]
  }
}
```

#### Active 化判定

- active_candidate: true
- rollback_required: false
- 判定理由:
  - top1_changed_rate_avg は 0.10 以下
  - activation_candidate_rate は 0.80 以上
  - max_abs_delta_max は 0.50 未満
  - rollback 条件には該当していない

#### Funnel Snapshot

- route_open_rate: 0.0
- save_rate: 0.0
- visit_done_rate: 0.0
- reflection_saved_rate: 0.0

#### 保留事項

- funnel 指標はすべて 0.0 のため、行動ファネルの改善・悪化は未判定
- dashboard API は `funnel_degradation_check_pending: no baseline to compare` を返している
- 本番 active 化の前に、route_open / save / visit_done / reflection_saved の実測値を追加で観測する

#### Final Decision

- local / staging active: 可
- production active: 延期
- 理由:
  - Score v3 の順位変動指標は active 条件を満たしている
  - ただし、funnel baseline が未取得のため、本番 active 化の根拠としては不足
- 次の対応:
  - local または staging で `SCORE_V3_MODE=active` を確認する
  - funnel event が記録される状態で追加観測する
  - production active は funnel baseline 取得後に再判断する

### Rollback Checklist

active 化前に以下を確認する。

- [ ] `SCORE_V3_MODE=shadow` に戻すだけで rollback できる
- [ ] rollback_required の条件が dashboard API で確認できる
- [ ] active 化後も `_debug.score_v3_ab_observation` が出力される
- [ ] top1_changed_rate_avg が 0.20 を超えた場合の対応が決まっている
- [ ] max_abs_delta_max が 1.00 を超えた場合の対応が決まっている
- [ ] funnel 指標が悪化した場合は active 化を停止する

### Observation TODO

- [ ] dashboard API の現在レスポンスを確認
- [ ] 30〜100セッション観測する
- [ ] Observation Report Template に実測値を記録する
- [ ] active 化判定レポートを作成する
- [ ] rollback 条件を確認する
- [ ] `SCORE_V3_MODE=active` の適用可否を判断する
