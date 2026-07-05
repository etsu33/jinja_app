

# Phase5 Behavior Measurement Plan

## 目的

Phase4 Concierge First UI で整えた導線と表示が、実際にユーザー行動につながっているかを計測する。

Phase5では、追加UIを先に作るのではなく、既存の行動ログを使って以下を判断できる状態を作る。

- 推薦結果が詳細閲覧につながっているか
- 詳細閲覧が経路表示や保存につながっているか
- 行動提案が実行・記録につながっているか
- Score v3 / v4 の改善判断に使える行動データがあるか
- 収益化に向けたファネルの弱点がどこか

## 前提

以下は完了済み。

- Phase4 Concierge First UI完了
- Web / Mobileの主導線整理
- Web / Mobileの補助導線整理
- `recommendation_reason_v4` 表示
- `reason_facts` 表示
- `action_suggestion_v4_preview` 表示
- Mobile Detailへの行動提案引き継ぎ
- `consultation_axis` のMobile利用方針整理
- Concierge First UI全体レビュー

## 現在のログ基盤

### Backend Model

既存の行動ログ系モデル候補:

- `ShrineInteractionLog`
  - `detail_view`
  - `route_open`
- `ActionEvent`
  - action suggestion系イベント
- `ConciergeRecommendationLog`
  - Concierge推薦結果ログ
- `ConciergeRecommendationClickLog`
  - Concierge推薦クリックログ
- `RankingLog`
  - ランキング集計系

### 既存API / Test

確認されたテスト・API候補:

- `test_behavior_funnel_debug_api.py`
- `test_score_v3_dashboard_api.py`
- `test_shrine_interaction_api.py`
- `test_behavior_funnel.py`
- `test_score_v3_feature_flag.py`
- `test_recommendation_algorithm_v3.py`

既存テスト上、以下の指標はすでに扱われている。

- `detail_view_count`
- `route_open_count`
- `save_count`
- `visit_done_count`
- `reflection_saved_count`
- `route_open_rate`
- `save_rate`
- `visit_done_rate`
- `reflection_saved_rate`

## Phase5で見るべきKPI

### 1. Detail View Rate

目的:

推薦結果が「詳しく見たい」と思われているかを確認する。

定義:

```text
detail_view_rate = detail_view_count / recommendation_impression_count
```

見ること:

- Concierge結果カードから詳細へ進んでいるか
- Web / Mobileで差があるか
- `recommendation_reason_v4` の表示改善後に上がるか

### 2. Route Open Rate

目的:

詳細閲覧が実際の参拝行動に近づいているかを確認する。

定義:

```text
route_open_rate = route_open_count / detail_view_count
```

見ること:

- 詳細を見た人が地図・経路を開いているか
- 参拝意欲につながっているか
- 神社距離や地域による差があるか

### 3. Save Rate

目的:

推薦結果が保存・再訪候補になっているかを確認する。

定義:

```text
save_rate = save_count / detail_view_count
```

見ること:

- 保存したくなる候補になっているか
- 推薦理由や根拠表示が保存に効いているか
- Web / Mobileで保存率に差があるか

### 4. Visit Done Rate

目的:

実際の参拝完了に近い行動が発生しているかを確認する。

定義:

```text
visit_done_rate = visit_done_count / detail_view_count
```

見ること:

- 詳細閲覧後に参拝完了記録が発生しているか
- Route Open後のVisit Done率を見る必要があるか
- 参拝導線に詰まりがないか

### 5. Reflection Saved Rate

目的:

参拝後の振り返りまでつながっているかを確認する。

定義:

```text
reflection_saved_rate = reflection_saved_count / visit_done_count
```

見ること:

- 参拝後に記録・内省へ進んでいるか
- `action_suggestion_v4_preview` が振り返りに効いているか
- 記録導線の改善余地があるか

## 推薦品質と行動の突合

Phase5では、単純な行動数だけではなく、推薦品質と行動の相関を見る。

### 突合したい項目

- `recommendation_reason_v4`
- `reason_facts.primary_axis`
- `reason_facts.shrine_feature`
- `reason_facts.shrine_benefit`
- `reason_facts.visit_fit`
- `action_suggestion_v4_preview.preview`
- `consultation_axis`
- `history_theme`
- `distance_m`
- `popular_score`
- `rank`

### 見たい問い

```text
- 理由が具体的な推薦ほどdetail_view_rateは上がるか
- reason_factsがある候補ほどsave_rateは上がるか
- action_suggestion_v4_previewがある候補ほどreflection_saved_rateは上がるか
- distance_mが近いほどroute_open_rateは上がるか
- consultation_axisごとに行動差分があるか
```

## Web / Mobile比較

### 比較対象

- Web Home → Concierge → Detail
- Mobile Home → Concierge → Detail
- Web Detail → Route Open / Save
- Mobile Detail → Route Open / Save / Records

### 見るべき差分

```text
- detail_view_rate
- route_open_rate
- save_rate
- visit_done_rate
- reflection_saved_rate
- action suggestion click / completion
```

判断軸:

- Mobileの方が参拝行動に近いか
- Webは比較・探索向きか
- Detailで情報量が多すぎて離脱していないか
- Mobile Detailに追加したaction suggestionが記録導線に効いているか

## 計測期間

### 最低条件

```text
最低 30 セッション
最低 7 日間
```

### 推奨条件

```text
推奨 100 セッション
推奨 14 日間
```

### 判断保留条件

以下の場合は、改善判断を保留する。

- セッション数が30未満
- detail_view_countが10未満
- route_open_countが5未満
- save_countが5未満
- visit_done_countが3未満

人類は少ない数字から壮大な結論を出しがちなので、ここは機械的に止める。

## Phase5の優先順位

### Priority A: 既存ログの確認

目的:

現在のログでどこまで計測できるか確認する。

TODO:

```markdown
- [ ] ShrineInteractionLogの記録対象確認
- [ ] ConciergeRecommendationLogの記録対象確認
- [ ] ConciergeRecommendationClickLogの記録対象確認
- [ ] ActionEventの記録対象確認
- [ ] save / visit_done / reflection_saved の記録箇所確認
- [ ] Web / Mobileでログ差分があるか確認
```

### Priority B: Funnel Dashboard確認

目的:

既存のdashboard / debug APIで見られる数値を整理する。

TODO:

```markdown
- [ ] behavior_funnel_debug_api のレスポンス確認
- [ ] score_v3_dashboard_api のレスポンス確認
- [ ] detail_view_count確認
- [ ] route_open_count確認
- [ ] save_count確認
- [ ] visit_done_count確認
- [ ] reflection_saved_count確認
```

### Priority C: 欠落ログの特定

目的:

Phase5で足りないログを洗い出す。

TODO:

```markdown
- [ ] recommendation_impression が取れているか確認
- [ ] recommendation click が取れているか確認
- [ ] action_suggestion_v4_preview の表示・クリックが取れているか確認
- [ ] Mobile consultation_axis がanalyticsに入っていない問題を確認
- [ ] Detail遷移元がConcierge / Ranking / Searchで分けられるか確認
```

### Priority D: 改善判断ルール化

目的:

数値を見たあとに、何を改善するかの判断基準を作る。

TODO:

```markdown
- [ ] detail_view_rateが低い場合の改善候補整理
- [ ] route_open_rateが低い場合の改善候補整理
- [ ] save_rateが低い場合の改善候補整理
- [ ] visit_done_rateが低い場合の改善候補整理
- [ ] reflection_saved_rateが低い場合の改善候補整理
```

## 改善判断ルール

### detail_view_rate が低い場合

仮説:

- 推薦カードの説明が弱い
- 神社名・地域・距離などの判断材料が足りない
- CTAが弱い

改善候補:

- 推薦カードのコピー改善
- `reason_facts` の見せ方調整
- 「詳しく見る」CTA改善

### route_open_rate が低い場合

仮説:

- 詳細を見ても参拝意欲が上がっていない
- 地図導線が弱い
- 距離やアクセス情報が不足している

改善候補:

- 経路CTAの位置調整
- アクセス情報の見せ方改善
- 参拝前行動提案との接続改善

### save_rate が低い場合

仮説:

- 保存する理由が弱い
- あとで見返す価値が伝わっていない
- 保存CTAが見つけにくい

改善候補:

- 保存CTAのコピー改善
- 「あとで参拝候補にする」文脈追加
- お気に入り導線の位置調整

### visit_done_rate が低い場合

仮説:

- 実際の参拝完了記録までつながっていない
- 記録導線が弱い
- Route Open後の戻り導線が弱い

改善候補:

- 参拝後記録CTAの改善
- DetailからRecordsへの導線改善
- Visit DoneのUIを軽くする

### reflection_saved_rate が低い場合

仮説:

- 振り返りの価値が伝わっていない
- 記録入力が重い
- action suggestionとの接続が弱い

改善候補:

- reflection promptの表示改善
- 記録入力を軽くする
- 参拝前の問いを記録画面へ引き継ぐ

## 今回のPRでやること

- Phase5の計測目的を文書化する
- 既存ログ基盤を整理する
- KPI定義を整理する
- Web / Mobile比較軸を整理する
- 改善判断ルールを整理する
- 次PR候補を明確にする

## 今回のPRでやらないこと

- 新規ログ実装はしない
- API変更はしない
- Dashboard実装はしない
- UI改善はしない
- Score v3 / v4 active化はしない

## 次PR候補

### 1. Behavior Funnel Current State Audit

ブランチ候補:

`audit/behavior-funnel-current-state`

目的:

- 現在のbackend / web / mobileで、どの行動ログが実際に記録されているか確認する

対象候補:

- docsのみ
- 必要に応じて軽いテスト確認

### 2. Mobile Action Suggestion Event Audit

ブランチ候補:

`audit/mobile-action-suggestion-event`

目的:

- Mobileで `action_suggestion_v4_preview` の表示・クリック・記録導線が計測可能か確認する

対象候補:

- docsのみ
- 必要なら後続で実装PR

### 3. Score v3 Dashboard Review

ブランチ候補:

`audit/score-v3-dashboard-review`

目的:

- `score_v3_dashboard_api` でPhase5に必要な指標が見られるか確認する

対象候補:

- docsのみ

## 推奨判断

次PRは **Behavior Funnel Current State Audit** が安全。

理由:

- 既存ログ基盤はあるが、Web / Mobileでどこまで実際に記録されているかは未確定
- いきなり新規実装するより、欠落ログを特定する方が事故が少ない
- 行動データの正本を確認してからDashboardや改善に進むべき

## TODO

```markdown
# Phase5 Behavior Measurement Plan

- [x] develop最新版化
- [x] docs/phase5-behavior-measurement-plan 作成
- [x] 既存ログ基盤の棚卸し
- [x] KPI定義整理
- [x] Web / Mobile比較軸整理
- [x] 推薦品質と行動の突合方針整理
- [x] 改善判断ルール整理
- [x] 次PR候補整理
- [ ] docs/phase5-behavior-measurement-plan.md をコミット
- [ ] PR作成
```

## 完了条件

- Phase5で見るべきKPIが明確になっている
- 既存ログ基盤の利用方針が整理されている
- 行動データに基づく改善判断ルールが文書化されている
- 次に監査すべきPR単位が明確になっている
