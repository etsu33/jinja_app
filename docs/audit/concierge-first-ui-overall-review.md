
# Concierge First UI Overall Review

## 目的

Phase4 Concierge First UI の最終レビューとして、Web / Mobile / Detail / Ranking / Map / Shrine List の導線と情報設計を横断確認する。

本レビューでは、以下を判断する。

- Concierge First の主導線が成立しているか
- 補助導線が主導線を邪魔していないか
- 推薦理由・根拠・行動提案の表示がWeb / Mobileで破綻していないか
- Phase4を完了扱いにしてよいか
- Phase5へ進む前に残すべき課題は何か

## 前提

以下は完了済み。

- 主要Contract固定
  - `reason_facts`
  - `recommendation_reason_v4`
  - `action_suggestion_v4_preview`
  - `consultation_axis`
  - `explanation`
- Normalize Cleanup
  - Web `_reason_facts` fallback削減
  - Web `_explanation_payload.original_reason` 依存削減
  - Mobile `_reason_facts` fallback削減
- Web / Mobile 表示差分監査
- `action_suggestions` Contract監査
- `primary_reason` Contract監査
- Phase4 Concierge First Readiness監査
- Concierge First Route Design監査
- Home Ranking 補助導線化
- Home Nearby Section 文脈整理
- Mobile Concierge First route audit
- Mobile Shrine Detail `action_suggestion_v4_preview` 表示
- Mobile Concierge `explanation.summary` 表示検討
- Mobile `consultation_axis` 利用方針整理

## 横断確認結果

### Web Home

対象:

- `apps/web/src/features/home/components/HomeHero.tsx`
- `apps/web/src/features/home/components/HomeHeroConsultationInput.tsx`
- `apps/web/src/features/home/components/HomeMainClient.tsx`
- `apps/web/src/features/home/components/HomeNearbySection.tsx`
- `apps/web/src/features/home/components/HomeRankingSection.tsx`

確認結果:

- HomeHero は相談起点になっている
- HomeHeroConsultationInput から `/concierge?theme=...` へ遷移できる
- 条件追加時は `openFilter=1` を渡せる
- HomeNearbySection は「相談のあと」の補助導線として成立している
- Shrine一覧は補助導線として扱われている
- Rankingは「参考にしたい人気の神社」として補助文脈に調整済み

判断:

Web Home は Concierge First の主導線として成立している。

### Web Concierge

対象:

- `apps/web/src/app/concierge/ConciergeClientFull.tsx`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`
- `apps/web/src/viewmodels/conciergeToShrineList.ts`

確認結果:

- `recommendation_reason_v4` を扱える
- `reason_facts` を扱える
- `action_suggestion_v4_preview` を扱える
- `consultation_axis` をmeta / item / analytics contextとして扱える
- `explanation` を扱える
- snake_case正本を優先するContract Testが追加済み

判断:

Web Concierge はContract反映済みで、推薦理由・根拠・行動提案の表示土台が成立している。

### Web Shrine Detail

対象:

- `apps/web/src/app/shrines/[id]/page.tsx`
- `apps/web/src/lib/concierge/pickExplanationPayloadFromThread.ts`
- `apps/web/src/lib/concierge/pickReasonFromThread.ts`
- `apps/web/src/lib/concierge/pickBreakdownFromThread.ts`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`

確認結果:

- Concierge経由の文脈をDetail側で拾える
- 推薦理由・根拠・explanationをDetail文脈に接続できる
- `_reason_facts` fallback は削減済み
- `_explanation_payload.original_reason` 依存は削減済み
- `primary_reason` / `action_suggestions` は内部構造として保留判断済み

判断:

Web Detail は、Concierge結果からの文脈表示に対応している。

### Mobile Home

対象:

- `apps/mobile/app/index.tsx`

確認結果:

- 相談入力欄がある
- 相談テーマチップがある
- 条件追加ヒントがある
- 主CTAは「この相談からご縁を見る」
- `/concierge?q=...&theme=...` へ遷移できる

判断:

Mobile Home も Concierge First の主導線として成立している。

### Mobile Concierge

対象:

- `apps/mobile/app/concierge/index.tsx`

確認結果:

- `/concierge/chat/` を呼び出せる
- `recommendation_reason_v4` を表示に使える
- `reason_facts` を表示に使える
- `action_suggestion_v4_preview` を表示できる
- Detail遷移時に以下を引き継げる
  - `recommendationReasonV4`
  - `reasonFacts`
  - `recommendationReasonDetail`
  - `actionSuggestionV4Preview`

判断:

Mobile Concierge は推薦結果表示とDetail連携が成立している。

### Mobile Shrine Detail

対象:

- `apps/mobile/app/shrines/[id].tsx`

確認結果:

- `recommendationReasonV4` を受け取れる
- `reasonFacts` を受け取れる
- `recommendationReasonDetail` を受け取れる
- `actionSuggestionV4Preview` を受け取れる
- 推薦理由と選定ポイントを表示できる
- `action_suggestion_v4_preview` をDetail側でも表示できる
- 記録導線として `/records` へ遷移できる

判断:

Mobile Detail は、Concierge結果からの意味情報と行動提案の引き継ぎに対応している。

### Ranking / Map / Shrine List

対象:

- Web Ranking
- Web Map
- Web Shrine List
- Mobile Ranking
- Mobile Search
- Mobile Favorites
- Mobile Recently Viewed

確認結果:

- Rankingは補助導線として整理済み
- Map / Nearby は相談後の場所確認として整理済み
- Shrine List / Search は神社名・地域から探す補助導線
- Favorites / Recently Viewed は再訪・確認導線

判断:

補助導線は Concierge First の主導線を邪魔していない。

## Contract反映状況

| Contract | Backend | Web | Mobile | 判断 |
|---|---|---|---|---|
| `recommendation_reason_v4` | 固定済み | 表示済み | 表示済み | OK |
| `reason_facts` | 固定済み | 表示済み | 表示済み | OK |
| `action_suggestion_v4_preview` | 固定済み | 表示済み | Concierge / Detail表示済み | OK |
| `consultation_axis` | 固定済み | analytics / context | UI表示なし・将来analytics候補 | OK |
| `explanation` | 固定済み | 表示済み | Detail表示・Concierge表示は保留 | OK |
| `primary_reason` | 内部構造扱い | 一部利用あり | 直接利用なし | 保留OK |
| `action_suggestions` | `_explanation_payload` 内部扱い | 一部利用あり | 直接利用なし | 保留OK |

## 情報設計の判断

### 主導線

```text
Home相談入力 → Concierge結果 → Shrine Detail → 記録 / 参拝行動
```

この流れは Web / Mobile ともに成立している。

### 補助導線

```text
Ranking / Map / Shrine List / Search / Favorites / Recently Viewed
```

これらは「探す」「確認する」「再訪する」ための導線として残す。
ただし、主導線ではない。

### 表示責務

```text
recommendation_reason_v4: ユーザー向けの主説明
reason_facts: 選定根拠
action_suggestion_v4_preview: 次の行動提案
explanation: 詳細説明・意味づけ
consultation_axis: 表示ではなくanalytics / context候補
```

この責務分離は妥当。

## 残課題

### 1. Mobile `consultation_axis` analytics

現時点ではUI表示しない判断済み。
将来的にはanalytics / contextとして保持する候補。

優先度:

```text
中
```

### 2. Mobile Concierge `explanation.summary` fallback

現時点では表示追加しない判断済み。
将来的に `card.reason` が空のときだけfallbackとして使う余地はある。

優先度:

```text
低〜中
```

### 3. `primary_reason` 公開Contract化

現時点では内部構造として保留。
将来的にユーザー向け表示やanalyticsに使うなら公開Contract化を検討する。

優先度:

```text
低
```

### 4. `action_suggestions` 公開Contract化

現時点では `action_suggestion_v4_preview` を公開正本として扱う。
旧 `action_suggestions` は内部構造として保留。

優先度:

```text
低
```

## Phase4完了判断

Phase4 Concierge First UI は完了扱いでよい。

理由:

- Web Homeの相談起点導線が成立している
- Mobile Homeの相談起点導線が成立している
- Web / MobileともにConcierge結果表示が成立している
- Web / MobileともにDetail連携が成立している
- `recommendation_reason_v4` / `reason_facts` / `action_suggestion_v4_preview` がUIに反映されている
- Ranking / Map / Shrine List は補助導線として整理済み
- `consultation_axis` / `explanation.summary` のMobile利用方針も保留判断済み

## 今回のPRでやること

- Phase4の横断レビューを文書化する
- Web / Mobile / Detail / 補助導線の状態を整理する
- Contract反映状況を一覧化する
- Phase4完了判断を記録する
- Phase5へ残す課題を整理する

## 今回のPRでやらないこと

- UI実装は変更しない
- API Contractは変更しない
- analytics実装はしない
- Mobile `consultation_axis` は実装しない
- Mobile `explanation.summary` は実装しない

## Phase5候補

### 1. 行動ログ・分析フェーズ

目的:

- `save`
- `detail_view`
- `route_open`
- `visit_done`
- `reflection_saved`

などの行動指標を元に、推薦精度とUI効果を検証する。

候補ブランチ:

`docs/phase5-behavior-measurement-plan`

### 2. Mobile consultation_axis analytics

目的:

- Mobileでも `consultation_axis` をanalytics contextとして保持する
- axis別の行動差分を分析できる状態にする

候補ブランチ:

`refactor/mobile-consultation-axis-analytics`

### 3. Concierge First UI 実機レビュー

目的:

- 実機でHome → Concierge → Detail → Records の流れを確認する
- 情報量・CTA・スクロール負荷を確認する

候補ブランチ:

`audit/concierge-first-ui-device-review`

## 推奨される次フェーズ

次は **Phase5 Behavior Measurement Plan** が有力。

理由:

- Phase4でUIとContractの整合性はかなり整った
- これ以上UIを足すより、行動データで改善判断する段階に入れる
- アプリ収益化に向けても、保存率・詳細閲覧率・経路表示率・記録率の把握が必要
- Score v3 / v4 のactive判断にも行動データが必要

## TODO

```markdown
# Concierge First UI Overall Review

- [x] develop最新版化
- [x] audit/concierge-first-ui-overall-review 作成
- [x] Web Home確認
- [x] Web Concierge確認
- [x] Web Detail確認
- [x] Mobile Home確認
- [x] Mobile Concierge確認
- [x] Mobile Detail確認
- [x] Ranking / Map / Shrine List確認
- [x] Contract反映状況整理
- [x] 残課題整理
- [x] Phase4完了判断
- [x] Phase5候補整理
- [ ] docs/audit/concierge-first-ui-overall-review.md をコミット
- [ ] PR作成
```

## 完了条件

- Phase4 Concierge First UI の完了判断が文書化されている
- Web / Mobile の主導線と補助導線が整理されている
- Contract反映状況が一覧化されている
- Phase5へ進むための候補が整理されている