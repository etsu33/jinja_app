> **Status: Reference**
>
> 本ドキュメントは、Recommendation Reason v4の`quality` payloadに関するBackend / Web / PostHog / Mobile間の責務境界の設計背景を記録した参照資料である。
>
> 本書のTODOチェックリストは策定時点のものであり、現行の実装状況は関連する実装コードおよびテストを最終的な正本とする。`recommendation_quality` Eventの正確な送信状況は`docs/audit/cross-platform-event-contract.md`を参照する。

# Recommendation Quality Analytics Boundary

## 目的

Recommendation Reason v4 の `quality` payload を、Backend / Web / PostHog / Mobile のどこで扱うかを整理する。

このドキュメントでは、実装変更は行わず、以下を固定する。

- `quality` payload の正本
- analytics event schema の正本
- PostHog の責務
- Mobile の追従方針
- 本番送信前の local / dev 確認方針

---

## 結論

`quality` payload の正本は Backend とする。

Web は Backend から受け取った `quality` を analytics event schema に変換し、PostHog へ送信する。

PostHog は保存・可視化・行動指標との相関分析の場であり、quality の計算ロジックは持たない。

Mobile は Web の event schema が安定した後に、同じ schema に追従する。

---

## 全体フロー

```text
Backend
recommendation_reason_v4.quality を生成

↓

Web
quality を受け取り analytics event schema に変換

↓

PostHog
保存・可視化・行動指標との相関分析

↓

改善判断
consultation_axis / action_intent / shrine data を改善

↓

Mobile
Web schema 安定後に追従
```

---

## Boundary

### Backend

#### ゴール

推薦理由の品質指標を計算し、API response / 保存payload に含められる状態にする。

#### 責務

- `recommendation_reason_v4.quality` を生成する
- `shrine_data_rate` を計算する
- `consultation_reflection_rate` を計算する
- `fallback_reason_rate` を計算する
- `evidence_rate` を計算する
- `action_grounding_rate` を計算する
- `is_ai_inference_only` を判定する
- `fallback_source` を返す

#### やらないこと

- PostHog へ直接送信しない
- dashboard の集計ロジックを持たない
- Web / Mobile の event schema を直接決めない
- quality score を推薦順位へまだ反映しない

#### 正本

```text
backend/temples/services/recommendation_reason_v4.py
```

---

### Web

#### ゴール

Backend から受け取った `quality` を、analytics event として送信できる形に変換する。

#### 責務

- Concierge result payload から `recommendation_reason.quality` を受け取る
- analytics event schema を固定する
- `trackRecommendationQuality` を設計する
- `threadId` / `shrineId` / `rank` / `source` と quality を紐づける
- local / dev で payload を確認する

#### やらないこと

- quality 指標を再計算しない
- Backend と違う定義で rate を作らない
- 本番送信を最初から有効化しない

#### 正本候補

```text
apps/web/src/lib/analytics/
apps/web/src/features/concierge/
apps/web/src/app/concierge/
```

---

### PostHog

#### ゴール

推薦品質とユーザー行動の相関を見る。

#### 責務

- `recommendation_quality` event を保存する
- quality 指標を dashboard で可視化する
- save / route_open / visit_done / reflection_saved と相関を見る
- 日別・週別で quality の推移を見る

#### やらないこと

- quality を計算しない
- Backend payload の意味を変更しない
- UI 表示文言を決めない

---

### Mobile

#### ゴール

Web の analytics event schema が安定した後、同じ quality event を送れるようにする。

#### 責務

- Web と同じ event name を使う
- Web と同じ payload schema を使う
- Mobile 固有の source のみ追加する

#### やらないこと

- Web より先に schema を独自拡張しない
- Backend quality を再計算しない
- PostHog 側で Mobile 専用の別指標を増やさない

---

## quality payload

Backend が生成する `quality` payload は以下を正本とする。

```ts
type RecommendationReasonQuality = {
  shrine_data_rate: number;
  consultation_reflection_rate: number;
  fallback_reason_rate: number;
  evidence_rate: number;
  action_grounding_rate: number;
  is_ai_inference_only: boolean;
  fallback_source: string | null;
};
```

### 指標定義

| 指標 | 意味 | 主な用途 |
|---|---|---|
| `shrine_data_rate` | deity / shrine_history / place_context / goriyaku / history_theme の利用率 | 神社固有情報の厚みを見る |
| `consultation_reflection_rate` | consultation_axis / need_profile / state_profile / historical_interpretation の利用率 | 相談内容の反映度を見る |
| `fallback_reason_rate` | fallback 由来かどうか | fallback 依存率を見る |
| `evidence_rate` | evidence の充足率 | 根拠の明示率を見る |
| `action_grounding_rate` | action_context / reflection_question_seed / action_intent の利用率 | 行動提案の根拠を見る |
| `is_ai_inference_only` | 神社データがない推測のみの文章か | 信頼性リスク検知 |
| `fallback_source` | fallback の発生元 | 改善対象の特定 |

---

## analytics event schema

Web から PostHog へ送信する event schema は以下を候補とする。

```ts
type RecommendationQualityEvent = {
  event: "recommendation_quality";
  source: "concierge_result" | "shrine_detail" | "mobile_concierge_result";
  threadId?: string;
  shrineId?: string | number;
  recommendationRank?: number;
  resultSetId?: string;
  accessLevel?: "anonymous" | "free" | "premium";
  quality: RecommendationReasonQuality;
};
```

### event name

```text
recommendation_quality
```

### 最低限必要なpayload

```markdown
- source
- shrineId
- recommendationRank
- quality.shrine_data_rate
- quality.consultation_reflection_rate
- quality.fallback_reason_rate
- quality.evidence_rate
- quality.action_grounding_rate
- quality.is_ai_inference_only
```

---

## local / dev 確認方針

本番送信前に、local / dev で以下を確認する。

```markdown
- [ ] Backend response に recommendation_reason.quality が含まれる
- [ ] Web 側で quality を型として受け取れる
- [ ] recommendation_quality event payload を console / dev provider で確認できる
- [ ] PostHog 本番送信は feature flag または env で制御する
- [ ] 本番送信前に event name と payload schema を固定する
```

### 本番送信の条件

```markdown
- [ ] local で payload が確認済み
- [ ] dev / preview 環境で event が確認済み
- [ ] event name が固定済み
- [ ] payload schema が固定済み
- [ ] 個人情報を含まないことを確認済み
```

---

## 分析観点

### Quality × Save率

目的:

`shrine_data_rate` や `evidence_rate` が高い推薦ほど、保存されやすいかを見る。

見る指標:

```markdown
- recommendation_quality
- save_prompt_click
- favorite_created
```

---

### Quality × Route Open率

目的:

`consultation_reflection_rate` や `action_grounding_rate` が高い推薦ほど、経路確認されやすいかを見る。

見る指標:

```markdown
- recommendation_quality
- route_open
```

---

### Quality × Visit Done率

目的:

quality が実際の訪問行動につながっているかを見る。

見る指標:

```markdown
- recommendation_quality
- visit_done
```

---

### Quality × Reflection Saved率

目的:

quality が参拝後の振り返り保存につながっているかを見る。

見る指標:

```markdown
- recommendation_quality
- reflection_saved
```

---

## Backend確認TODO

```markdown
- [ ] recommendation_reason_v4.quality の response 露出箇所を確認
- [ ] Concierge response に quality が含まれるか確認
- [ ] thread 保存時に quality が保持されるか確認
- [ ] 保存済み thread 再表示時に quality が再計算されないか確認
```

---

## Web確認TODO

```markdown
- [ ] quality を受け取る型を確認
- [ ] Concierge result payload の型に quality を追加するか確認
- [ ] trackRecommendationQuality event を設計
- [ ] dev provider / console で送信payloadを確認
- [ ] PostHog送信は dev 環境から開始
```

---

## PostHog確認TODO

```markdown
- [ ] recommendation_quality event を定義
- [ ] shrine_data_rate dashboard を作成
- [ ] evidence_rate dashboard を作成
- [ ] fallback_reason_rate dashboard を作成
- [ ] quality × save_rate を確認
- [ ] quality × route_open_rate を確認
- [ ] quality × visit_done_rate を確認
```

---

## Mobile確認TODO

```markdown
- [ ] Web schema 安定後に対応
- [ ] Web と同じ event name を使う
- [ ] Mobile 固有 source を追加する
- [ ] Mobile 側で quality を再計算しない
```

---

## 今回のスコープ外

```markdown
- [ ] PostHog送信実装
- [ ] dashboard作成
- [ ] recommendation rankingへのquality反映
- [ ] Mobile実装
- [ ] quality scoreによる出し分け
```

---

## TODO

```markdown
# Setup
- [x] develop最新化
- [x] docs/recommendation-quality-analytics-boundary 作成

# Boundary
- [x] Backend / Web / PostHog / Mobile の責務を整理
- [x] quality payload の正本を backend に固定
- [x] analytics event schema の正本を web に固定
- [x] PostHog は保存・可視化の場として定義
- [x] Mobile は Web schema 追従にする
- [x] 本番送信前に local/dev で payload確認する方針を記録

# Backend
- [ ] recommendation_reason_v4.quality のresponse露出箇所を確認
- [ ] thread保存時のquality保持有無を確認

# Web
- [ ] qualityを受け取る型を確認
- [ ] trackRecommendationQuality event設計
- [ ] PostHog送信は dev環境から開始

# PostHog
- [ ] recommendation_quality event定義
- [ ] quality × save_rate
- [ ] quality × route_open_rate
- [ ] quality × visit_done_rate

# Mobile
- [ ] Web schema安定後に対応
```
