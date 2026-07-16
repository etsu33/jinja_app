> **Status: Archive**
>
> 本ドキュメントは、旧Phase 5においてBehavior Funnelと推薦品質の計測方針を整理した作業計画である。
>
> 記載されたPhase番号、TODO、PR候補、計測対象および実装状態は当時のスナップショットであり、現行の開発順序やAnalytics契約の判断には使用しない。
>
> 現在の参照先は以下とする。
>
> - 全体開発順序：`docs/core/roadmap.md`
> - Visit / Reflection契約：`docs/product/visit-reflection-flow.md`
> - Reflection Funnel：`docs/product/reflection-funnel-dashboard.md`
> - 実装整合性監査：`docs/audit/visit-reflection-implementation-consistency.md`
> - Cross-platform Event契約：`docs/audit/cross-platform-event-contract.md`

# Phase5 Behavior Measurement Plan

## 目的

本書は、旧Phase 4で整備されたConcierge Firstの導線と表示が、ユーザー行動へつながっているかを確認するために作成された行動計測計画である。

当時は新しいUIを先に追加するのではなく、既存の行動ログを利用して、以下を判断する方針としていた。

- 推薦結果が詳細閲覧につながっているか
- 詳細閲覧が経路表示や保存につながっているか
- 行動提案が実行・記録につながっているか
- Score v3 / v4の改善判断に利用できる行動データがあるか
- 収益化に向けたFunnelの弱点がどこにあるか

---

## 当時確認されていたログ基盤

### Backend Model

当時、行動計測に利用する候補として以下のModelが確認されていた。

- `ShrineInteractionLog`
  - `detail_view`
  - `route_open`
- `ActionEvent`
  - Action Suggestion関連Event
- `ConciergeRecommendationLog`
  - Concierge推薦結果Log
- `ConciergeRecommendationClickLog`
  - Concierge推薦Click Log
- `RankingLog`
  - Ranking集計関連Log

### API・Test

当時、行動計測と関連するものとして以下のTest・APIが確認されていた。

- `test_behavior_funnel_debug_api.py`
- `test_score_v3_dashboard_api.py`
- `test_shrine_interaction_api.py`
- `test_behavior_funnel.py`
- `test_score_v3_feature_flag.py`
- `test_recommendation_algorithm_v3.py`

当時のTestでは、以下の指標が扱われていた。

- `detail_view_count`
- `route_open_count`
- `save_count`
- `visit_done_count`
- `reflection_saved_count`
- `route_open_rate`
- `save_rate`
- `visit_done_rate`
- `reflection_saved_rate`

現在のModel・API・Event・指標は、実装コードと関連する現行文書を正本とする。

---

## 当時定義したKPI

### Detail View Rate

推薦結果が、ユーザーの「詳しく見たい」という行動につながっているかを確認するための指標として定義した。

```text
detail_view_rate = detail_view_count / recommendation_impression_count
```

当時想定していた確認観点は以下である。

- Concierge結果カードから詳細画面へ遷移しているか
- WebとMobileで差があるか
- Recommendation Reasonの改善後に変化があるか

### Route Open Rate

神社詳細の閲覧が、地図や経路確認などの参拝に近い行動へつながっているかを確認するための指標として定義した。

```text
route_open_rate = route_open_count / detail_view_count
```

当時想定していた確認観点は以下である。

- 詳細を閲覧したユーザーが地図・経路を開いているか
- 詳細表示が参拝意欲につながっているか
- 距離や地域による差があるか

### Save Rate

推薦された神社が、保存や再訪の候補として認識されているかを確認するための指標として定義した。

```text
save_rate = save_count / detail_view_count
```

当時想定していた確認観点は以下である。

- 保存したくなる推薦になっているか
- 推薦理由や根拠表示が保存行動へ影響しているか
- WebとMobileで保存率に差があるか

### Visit Done Rate

詳細閲覧後に、実際の参拝完了記録へ進んでいるかを確認するための指標として定義した。

```text
visit_done_rate = visit_done_count / detail_view_count
```

当時想定していた確認観点は以下である。

- 詳細閲覧後に参拝完了記録が発生しているか
- Route Open後のVisit Done率を分けて確認する必要があるか
- 参拝記録までの導線に詰まりがないか

### Reflection Saved Rate

参拝後の体験が、振り返りや記録へつながっているかを確認するための指標として定義した。

```text
reflection_saved_rate = reflection_saved_count / visit_done_count
```

当時想定していた確認観点は以下である。

- 参拝後に記録・内省へ進んでいるか
- Action Suggestionが振り返りへ影響しているか
- Reflection入力導線に改善余地があるか

---

## 推薦品質と行動の突合

旧Phase 5では、単純な行動件数だけではなく、推薦品質とユーザー行動の関係を確認する方針としていた。

### 当時の突合候補

- recommendation_reason_v4
- reason_facts.primary_axis
- reason_facts.shrine_feature
- reason_facts.shrine_benefit
- reason_facts.visit_fit
- action_suggestion_v4_preview.preview
- consultation_axis
- history_theme
- distance_m
- popular_score
- rank

### 当時想定していた問い

- 理由が具体的な推薦ほどdetail_view_rateは高くなるか
- reason_factsがある候補ほどsave_rateは高くなるか
- action_suggestion_v4_previewがある候補ほどreflection_saved_rateは高くなるか
- distance_mが短いほどroute_open_rateは高くなるか
- consultation_axisごとに行動差分があるか

これらは当時の検証仮説であり、現在の因果関係やAnalytics契約を確定するものではない。

---

## Web・Mobile比較

旧Phase 5では、WebとMobileでユーザー行動に差があるかを比較する方針としていた。

### 当時の比較対象

- Web Home → Concierge → Detail
- Mobile Home → Concierge → Detail
- Web Detail → Route Open / Save
- Mobile Detail → Route Open / Save / Records

### 当時の比較指標

- detail_view_rate
- route_open_rate
- save_rate
- visit_done_rate
- reflection_saved_rate
- Action Suggestionの表示・Click・完了

### 当時の判断観点

- Mobileの方が参拝行動に近いか
- Webは比較・探索に利用されやすいか
- 神社詳細の情報量が離脱へ影響していないか
- Mobile DetailのAction Suggestionが記録導線へ影響しているか

現在のWeb・Mobile共通Event契約は、`docs/audit/cross-platform-event-contract.md`および実装コードを参照する。

---

## 当時想定していた計測期間

少数の行動データだけで改善判断を行わないため、旧Phase 5では最低条件と推奨条件を定義していた。

### 最低条件

- 最低30セッション
- 最低7日間

### 推奨条件

- 推奨100セッション
- 推奨14日間

### 判断保留条件

以下の場合は改善判断を保留する方針としていた。

- セッション数が30未満
- detail_view_countが10未満
- route_open_countが5未満
- save_countが5未満
- visit_done_countが3未満

これらの数値は当時の暫定基準であり、現在のAnalytics判断基準として使用しない。

---

## 当時の改善判断ルール

### Detail View Rateが低い場合

当時想定していた仮説は以下である。

- 推薦カードの説明が弱い
- 神社名・地域・距離などの判断材料が不足している
- 詳細画面へのCTAが弱い

当時の改善候補は以下である。

- 推薦カードのCopy改善
- reason_factsの表示調整
- 詳細画面へのCTA改善

### Route Open Rateが低い場合

当時想定していた仮説は以下である。

- 詳細を閲覧しても参拝意欲が高まっていない
- 地図・経路導線が弱い
- 距離やAccess情報が不足している

当時の改善候補は以下である。

- 経路CTAの配置調整
- Access情報の表示改善
- 参拝前の行動提案との接続改善

### Save Rateが低い場合

当時想定していた仮説は以下である。

- 保存する理由が弱い
- 後から見返す価値が伝わっていない
- 保存CTAが見つけにくい

当時の改善候補は以下である。

- 保存CTAのCopy改善
- 「あとで参拝候補にする」という文脈の追加
- Favorite導線の配置調整

### Visit Done Rateが低い場合

当時想定していた仮説は以下である。

- 実際の参拝完了記録までつながっていない
- 記録導線が弱い
- Route Open後の復帰導線が弱い

当時の改善候補は以下である。

- 参拝後記録CTAの改善
- DetailからRecordsへの導線改善
- Visit Done入力の簡略化

### Reflection Saved Rateが低い場合

当時想定していた仮説は以下である。

- 振り返りの価値が伝わっていない
- 記録入力が重い
- Action Suggestionとの接続が弱い

当時の改善候補は以下である。

- Reflection Promptの表示改善
- 記録入力の簡略化
- 参拝前の問いを記録画面へ引き継ぐ

---

## 本書が保持するもの

- 旧Phase 5におけるBehavior Funnel設計の背景
- 当時利用を想定していた行動指標
- 推薦品質とユーザー行動を突合する考え方
- Web・Mobileを比較する観点
- 少数Dataだけで判断しない方針
- 指標低下時の改善仮説

---

## 本書が扱わないもの

- 現在の開発Phase
- 現在のAnalytics Event契約
- 現在のPayload契約
- 現在のFunnel定義
- 現在のModel・API構成
- 現在のKPI目標値
- 現在の実装状態
- TODO
- PR候補
- 実装計画
- 作業進捗

---

## 更新ルール

- 本書は旧Phase 5における行動計測設計の記録を保持するArchive文書である
- 現在のRoadmap・Analytics契約・実装状況は関連する正本文書を参照する
- 現行仕様や実装変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- 本書へ新しい仕様・TODO・PR計画・作業進捗は追記しない
