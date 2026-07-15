

# Recommendation Quality - Score v3 Audit

## 1. Purpose

Recommendation Quality Phase1 として、Score v3 の現在地を監査する。

本監査では、以下を確認する。

- Score v3 の実装ファイル
- Weight 設計と docs の整合
- `consultation_axis` の反映範囲
- `visit_style` の反映範囲
- `goriyaku` / `goriyaku_tag_ids` の反映範囲
- shadow mode / active 判定の現在地

このPRでは Score v3 の計算式・weight・active化は変更しない。

---

## 2. Scope

### 対象ファイル

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/services/score_v3_observer.py
backend/temples/services/score_v3_observation_summary.py
docs/recommendation-score-v3-design.md
docs/audit/recommendation-score-v3-roadmap.md
```

### 関連テスト

```text
backend/temples/tests/api/test_score_v3_dashboard_api.py
backend/temples/tests/services/test_score_v3_feature_flag.py
backend/temples/tests/services/test_score_v3_observer.py
backend/temples/tests/services/test_score_v3_observation_summary.py
backend/temples/tests/services/test_recommendation_algorithm_v3.py
```

---

## 3. Current Implementation Summary

Score v3 は `backend/temples/services/concierge_chat_ranking.py` 内で定義されている。

現在の weight は以下。

```python
_SCORE_V3_WEIGHTS = {
    "state": 0.45,
    "history": 0.10,
    "distance": 0.10,
    "behavior": 0.25,
    "profile": 0.05,
    "direction": 0.02,
    "action": 0.02,
    "reflection": 0.01,
}
```

Score v3 は `SCORE_V3_MODE=active` の場合のみ並び順に利用される。
未設定・不正値・`shadow` 指定時は既存の `_score_total` を使い、Score v3 は観測値としてのみ付与される。

```text
shadow mode: 既存rankingを維持
active mode: breakdown.score_v3 を sort key に利用
```

---

## 4. Weight Audit

### 実装値

| component | weight |
| --- | ---: |
| state | 0.45 |
| behavior | 0.25 |
| history | 0.10 |
| distance | 0.10 |
| profile | 0.05 |
| direction | 0.02 |
| action | 0.02 |
| reflection | 0.01 |

### docs設計値

`docs/recommendation-score-v3-design.md` では以下の設計になっている。

```text
0.45 × User State Profile
0.25 × Behavior Profile
0.10 × History Signal
0.10 × Distance Signal
0.05 × DerivedProfile
0.02 × DirectionProfile
0.02 × Visit
0.01 × Reflection
```

### Assessment

実装値と docs の設計値は一致している。

現時点では weight の数値変更は行わない。

理由:

- docs と実装の不一致はない
- Score v3 は shadow mode で既存rankingを壊さない設計になっている
- weight変更よりも、入力シグナルの網羅性確認を優先する方が安全

---

## 5. consultation_axis Audit

### Current State

`consultation_axis` は Score v3 の history signal に接続されている。

現時点で確認できる明示 mapping は以下。

```python
SCORE_V3_HISTORY_THEME_BY_AXIS = {
    "rest_healing": {
        "静寂": 1.0,
        "復興": 0.8,
        "守り": 0.6,
        "縁": 0.2,
        "勝負": 0.0,
    },
}
```

`resolve_score_v3_history_signal()` は `consultation_axis` と `history_theme` を受け取り、対応する値を返す。

### Assessment

`consultation_axis` の接続は存在するが、対応範囲は `rest_healing` に強く偏っている。

現時点では以下が弱点。

- `career_change`
- `relationship_love`
- `money_business`
- `study_focus`
- `challenge_courage`
- `protection_reset`

など、主要相談軸ごとの history_theme mapping がまだ薄い。

### Decision

このPRでは mapping を追加しない。

次フェーズで `consultation_axis` ごとの history_theme 対応表を設計する。

---

## 6. visit_style Audit

### Current State

`visit_style` は主に以下の経路で扱われる。

- Mobile / Web の条件UIから `visit_style_tags` として送信
- `extra_condition` から `visit_style` が抽出される
- 既存 ranking / profile signal の補助として使われる
- `profile_context.user_profile.worshipStyle` が `_score_profile_signal()` で参照される

`_score_profile_signal()` では、候補神社の以下を材料として worshipStyle を探索している。

```text
goriyaku
description
visit_style_tags
```

一致した場合、profile signal として +0.01 が加算される。

### Assessment

`visit_style` は Score v3 に接続されているが、主要 component ではなく profile signal 内の補助として扱われている。

この扱いは MVP としては安全。

理由:

- visit_style が need / state を上書きしない
- 一致候補が少ない場合でもランキングを壊しにくい
- `docs/audit/concierge-ranking-observation.md` でも、visit_style は hard filter ではなく補助ランキング軸として扱う方針が確認されている

### Decision

このPRでは visit_style weight を変更しない。

次フェーズでは以下を確認する。

- visit_style一致候補が候補poolに入っているか
- visit_style一致が top3 にどの程度反映されているか
- `breakdown.score_v3_detail` で visit_style 寄与が十分に観測できるか

---

## 7. goriyaku / goriyaku_tag_ids Audit

### Current State

`goriyaku` / `goriyaku_tag_ids` は以下の経路で推薦に影響している。

- frontend 条件UIで選択
- `goriyaku_tag_ids` として chat payload に送信
- backend で候補生成 / hard filter / reason_facts に接続
- `matched_user_selected_goriyaku_tag_ids` が reason fact に反映

ただし、Score v3 の明示 component として `goriyaku_signal` は存在しない。

### Assessment

`goriyaku` は推薦全体には効いているが、Score v3単体の独立componentとしては薄い。

現時点では、以下の分離が妥当。

```text
goriyaku_tag_ids: 候補生成・明示条件・reason_factsの材料
Score v3: 既存ranking後の補正・shadow観測
```

つまり、goriyaku を Score v3 の主weightへすぐ追加する必要はない。

### Decision

このPRでは `goriyaku_signal` は追加しない。

次フェーズで検討する場合は、以下の観測後に行う。

- goriyaku指定あり / なしで候補0件が発生していないか
- selected goriyaku が top3 に反映されているか
- reason_facts に user_selected_tag が十分出ているか

---

## 8. Shadow Mode / Active Readiness

### Current State

`score_v3_observer.py` では active候補判定として以下の閾値を持つ。

```python
ACTIVATION_TOP1_CHANGED_RATE_MAX = 0.35
ACTIVATION_AVG_DELTA_MAX = 0.25
ACTIVATION_MAX_ABS_DELTA_MAX = 0.75
```

`score_v3_observation_summary.py` では以下を観測する。

- top1_changed
- delta
- component_summary
- reason

### Assessment

Score v3 は shadow mode として観測可能な状態。

ただし、active化判断にはまだ以下が必要。

- 十分なセッション数
- top1_changed_rate
- avg_delta
- max_abs_delta
- behavior funnel との突合
- route_open / save / visit_done / reflection_saved との相関確認

### Decision

このPRでは active化しない。

---

## 9. Findings

### Confirmed

- Score v3 weight は docs と実装が一致している。
- Score v3 は shadow mode がデフォルト。
- active mode は `SCORE_V3_MODE=active` の場合のみ有効。
- `consultation_axis` は history signal に接続済み。
- `visit_style` は profile signal の補助として接続済み。
- `goriyaku_tag_ids` は候補生成・reason_facts には接続済み。

### Weak Points

- `consultation_axis` の history_theme mapping が `rest_healing` 中心。
- `visit_style` は Score v3 の独立componentではない。
- `goriyaku` は Score v3 の独立componentではない。
- active化には実測ログと行動ファネル突合が不足している。

### Current Risk

Score v3 の主要リスクは weight値そのものではなく、入力シグナルの網羅性不足である。

---

## 10. Decision

このPRでは以下を行わない。

- Score v3 weight変更
- Score v3 active化
- `consultation_axis` mapping追加
- `visit_style` weight変更
- `goriyaku_signal` 追加

まずは監査結果を記録し、次PRで小さく分けて改善する。

---

## 11. Next Actions

```markdown
- [x] Score v3関連ファイル洗い出し
- [x] Weight監査
- [x] consultation_axis対応範囲確認
- [x] visit_style反映確認
- [x] goriyaku反映確認
- [x] docsへ監査結果を記録
- [ ] consultation_axis x history_theme mapping設計
- [ ] visit_style反映の観測強化
- [ ] goriyaku指定あり推薦の観測強化
- [ ] shadow log比較
- [ ] active判定
```

---

## 12. Proposed Next PRs

### PR1: consultation_axis mapping audit

```text
docs/audit/score-v3-consultation-axis-history-theme-mapping.md
```

目的:

- consultation_axis ごとの history_theme 対応を整理
- `rest_healing` 以外の軸を追加する前に docs で固定

### PR2: visit_style observation audit

目的:

- visit_style一致候補が候補poolに入っているか確認
- top3への反映率を確認
- 必要なら observation payload を拡張

### PR3: goriyaku selected tag audit

目的:

- `goriyaku_tag_ids` 指定時に候補が適切に残るか確認
- `reason_facts.user_selected_tag` の出現率確認
- Score v3に入れるべきか、候補生成・Reason側に留めるべきか判断
```
