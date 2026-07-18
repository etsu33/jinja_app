> **Status: Archive**
>
> 本ドキュメントは、Recommendation Score v2の実出力と行動ファネルを接続して確認した時点監査である。
>
> 現行の実装・集計は関連する実装コードおよびテストを最終的な正本とする。

# Recommendation Score v2 Output Funnel Audit

## 目的

Recommendation Score v2 の実出力と、推薦後の行動ファネルを接続して監査する。

この監査では、単に推薦結果が生成されているかではなく、以下を確認する。

- representative case の実出力が状態整理型の提案になっているか
- recommendation ごとに save / route_open / visit_done / reflection_saved の差が出ているか
- score_v2.components と実行動に相関があるか
- 「検索結果」ではなく「次の行動につながる推薦」になっているか

---

## 監査対象

### 実出力

```text
ConciergeThread.recommendations_v2
```

主に見る項目:

```text
recommendations_v2[*].shrine_id
recommendations_v2[*].name
recommendations_v2[*].score_v2
recommendations_v2[*].score_v2.components
recommendations_v2[*].score_v2.signals
recommendations_v2[*].rank_explanation
recommendations_v2[*].rank_comparison
recommendations_v2[*]._explanation_payload
recommendations_v2[*].action_state
```

---

## 行動ファネル集計元

### detail_view / route_open

```text
ShrineInteractionLog
```

対象 action_type:

```text
detail_view
route_open
```

### save

```text
Favorite
```

### visit_done

```text
Visit(status="added")
```

### reflection_saved

```text
ShrineReflection
```

---

## 既存集計サービス

```text
backend/temples/services/behavior_funnel.py
```

既存関数:

```text
get_behavior_funnel_metrics
```

既存 API:

```text
GET /api/debug/behavior-funnel/
```

現状取得できる指標:

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
save_to_visit_cvr
visit_to_reflection_cvr
```

注意:

```text
現状は shrine_id 単位までは取得できる。
ただし recommendation rank / score_v2 / reason 別の集計は未実装。
```

---

## recommendation ごとの差分分析

### 接続キー

```text
recommendations_v2[*].shrine_id
```

fallback:

```text
recommendations_v2[*].id
```

### 分析単位

```text
thread_id
recommendation_rank
shrine_id
score_v2.total
score_v2.components.user_state_match
score_v2.components.shrine_meaning_match
score_v2.components.context_match
score_v2.components.behavior_signal
score_v2.components.capped_behavior_contribution
primary_reason
matched_need_tags
history_theme
```

### 行動指標

```text
detail_view_count
route_open_count
save_count
visit_count
reflection_count
detail_to_route_open_cvr
detail_to_save_cvr
route_open_to_visit_cvr
visit_to_reflection_cvr
```

---

## representative case

まずは以下の代表ケースで実出力を確認する。

| ケース | 入力例 | 見る観点 |
|---|---|---|
| 転職不安 | 転職が不安で、背中を押してほしい | career / mental / courage が出るか |
| 疲労回復 | 最近疲れていて、静かに落ち着きたい | mental / rest と静寂・復興が接続するか |
| 金運・事業 | 売上を伸ばしたい。事業の流れを良くしたい | money を結果保証にしていないか |
| 縁結び | 良縁がほしい。人との関係を見直したい | 縁を関係整理へ翻訳できるか |
| 学業 | 資格試験に合格したい。集中したい | study / focus と学びが接続するか |
| 厄除け | 最近流れが悪い。厄を落としたい | protection を不安煽りにしていないか |
| 旅行安全 | 出張前に安全に移動したい | travel_safe を移動前確認へ翻訳できるか |
| 開運 | 流れを変えたい。動き出すきっかけがほしい | courage を魔法化していないか |

---

## 判定基準

### 実出力品質

OK:

```text
ユーザー状態
↓
神社意味
↓
行動テーマ
```

NG:

```text
近い
人気
ご利益がある
有名
```

### 行動ファネル品質

見るべき指標:

```text
detail_view → route_open
detail_view → save
route_open → visit_done
visit_done → reflection_saved
save → visit_done
save → reflection_saved
```

---

## 現時点の判断

このPRでは、まず監査軸を固定する。

実装は次PR候補として分離する。

理由:

- 既存 behavior_funnel.py は全体 / shrine_id 単位の集計まで対応済み
- recommendation rank / score_v2 別集計は新規設計が必要
- 先に分析粒度を固定しないと、集計関数が散らばる

---

## 次PR候補

### PR1: recommendation output snapshot command

目的:

```text
representative case の実出力をCLIで保存する
```

候補:

```text
backend/temples/management/commands/audit_recommendation_outputs.py
```

### PR2: recommendation funnel metrics service

目的:

```text
recommendations_v2 と行動ログを shrine_id で接続して集計する
```

候補:

```text
backend/temples/services/recommendation_output_funnel.py
```

### PR3: debug API

目的:

```text
admin向けに recommendation ごとの行動差分を確認する
```

候補:

```text
GET /api/debug/recommendation-output-funnel/
```

---

## TODO

```markdown
- [x] develop に移動
- [x] develop 最新化
- [x] feature/recommendation-score-v2-output-funnel-audit 作成
- [x] 既存 behavior_funnel 集計サービスを確認
- [x] debug behavior funnel API の存在を確認
- [x] save / route_open / visit_done / reflection_saved の集計元を確認
- [x] ConciergeThread に recommendations_v2 が保存されることを確認
- [x] recommendations_v2 に score_v2 / rank_explanation / rank_comparison / _explanation_payload が含まれる経路を確認
- [x] representative case の実出力取得方針を整理
- [x] recommendationごとの行動差分分析方針を整理
- [x] docs/analytics/recommendation-score-v2-output-funnel-audit.md を作成
```
