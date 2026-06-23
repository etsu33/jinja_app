

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
# behavior_funnel.py の集計と突合する想定（別 PR）
from temples.services.behavior_funnel import get_behavior_funnel_summary
```

### 重み変更の手順（別 PR）

1. `summarize_score_v3_ab_observations` で集計・判断
2. `_SCORE_V3_WEIGHTS` の定数を変更（`concierge_chat_ranking.py`）
3. shadow observation で再度 `activation_candidate_rate` を確認
4. 安定したら active 化（`SCORE_V3_MODE=active`）

**本 PR では score_v3 の重みを変更しない。**

---

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
