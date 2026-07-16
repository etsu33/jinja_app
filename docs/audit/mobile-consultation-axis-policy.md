

# Mobile Consultation Axis Policy Audit

## 目的

Mobileで `consultation_axis` をどう扱うべきかを整理する。

本監査では、すぐにUI実装へ入るのではなく、以下を明確にする。

- Mobileで `consultation_axis` / `consultationAxis` を現在使っているか
- UI表示に使うべきか
- analytics / context として保持すべきか
- 今後の実装候補をどこに置くか

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

`consultation_axis` はBackend / Web側では公開Contractとして整理済み。

一方で、Mobile側ではまだ利用方針が未確定のため、本監査で扱いを決める。

## 現在地

### Mobile利用状況

確認コマンド:

```bash
grep -R "consultation_axis\|consultationAxis" -n apps/mobile/app apps/mobile/lib | head -160
```

結果:

```text
該当なし
```

つまり、Mobileでは現時点で `consultation_axis` / `consultationAxis` を使用していない。

## Backend / Web側の状態

### Backend

`consultation_axis` は推薦APIの公開Contractとして整理済み。

主な役割:

- 相談内容の軸を表す
- `recommendation_reason_v4` の解釈材料になる
- `_need` / `_signals` / recommendation item に含まれる
- API Contract Testで保持されている

### Web

Webでは `consultation_axis` を以下の用途で扱っている。

- payload meta
- recommendation item
- analytics context
- ConciergeSectionsRenderer のイベントpayload

Webでは主に **表示そのもの** というより、analytics / context として利用している。

## Mobileでの選択肢

### A. UIに表示する

例:

```text
相談軸: 仕事の整理
相談軸: 気持ちの回復
```

メリット:

- ユーザーが「どう解釈されたか」を見られる
- 推薦の透明性が上がる

デメリット:

- Mobileカードの情報量が増える
- `recommendation_reason_v4` / `reason_facts` と意味が重複しやすい
- 軸名が抽象的だと、ユーザーにとって分かりにくい
- 画面がAPIレスポンスの展示場になりがち

判断:

現時点では採用しない。

### B. analytics / contextとして保持する

例:

- Concierge送信イベント
- Recommendation表示イベント
- Detail遷移イベント
- Save / Route Open / Visit Done との相関分析

メリット:

- UIを重くせず、推薦改善に使える
- consultation_axisごとの行動差分を見られる
- Score v3 / v4の改善判断に使える

デメリット:

- 実装にはanalytics設計が必要
- 既存Mobile analyticsとの接続確認が必要

判断:

将来候補として有効。
ただし、このPRでは実装しない。

### C. 完全に未使用のままにする

メリット:

- 実装が増えない
- UIが重くならない
- 現在の体験を壊さない

デメリット:

- consultation_axis別の行動分析ができない
- MobileとWebのanalytics粒度に差が残る

判断:

短期では許容。
中期ではanalytics / contextとして保持する方針を検討する。

## 判断

Mobileでは、現時点で `consultation_axis` をUI表示しない。

理由:

- Mobileでは該当利用がない
- すでに `recommendation_reason_v4` がユーザー向け説明を担っている
- `reason_facts` が根拠表示を担っている
- `consultation_axis` を表示すると情報量が増えやすい
- 軸名はユーザー向けコピーとしてそのまま出すには抽象度が高い

一方で、`consultation_axis` は将来的に analytics / context として保持する価値がある。

したがって方針は以下とする。

```text
UI表示: しない
analytics利用: 将来候補
context保持: 将来候補
現PRでの実装: なし
```

## 今回のPRでやること

- Mobileで `consultation_axis` が未使用であることを文書化する
- UI表示しない判断を記録する
- 将来的にanalytics / contextとして扱う候補を整理する
- 次PR候補を明確にする

## 今回のPRでやらないこと

- Mobile UIに `consultation_axis` を表示しない
- `RecommendationApiCard` に `consultation_axis` を追加しない
- `RecommendationCard` に `consultationAxis` を追加しない
- analytics実装はしない
- API Contractは変更しない

## 将来実装する場合の最小案

### 型追加候補

```ts
consultation_axis?: string | null;
consultationAxis?: string | null;
```

### ViewModel追加候補

```ts
consultationAxis?: string | null;
```

### normalize候補

```ts
const consultationAxis = asTrimmedString(item.consultation_axis ?? item.consultationAxis);
```

### 利用候補

```text
- Recommendation impression analytics
- Detail open analytics
- Save analytics
- Route open analytics
- Visit done analytics
```

## 次PR候補

### 1. Concierge First UI全体レビュー

ブランチ候補:

`audit/concierge-first-ui-overall-review`

目的:

- Web / Mobile のConcierge First UIを横断レビューする
- Phase4の完了判断を行う
- Phase5へ進む前の残課題を整理する

対象候補:

- docsのみ
- 実装なし

### 2. Mobile consultation axis analytics

ブランチ候補:

`refactor/mobile-consultation-axis-analytics`

目的:

- Mobileで `consultation_axis` をanalytics / contextとして保持する
- consultation_axisごとの行動分析に備える

対象候補:

- `apps/mobile/app/concierge/index.tsx`
- analytics helperがあれば該当ファイル

### 3. Score v3 / v4 行動分析設計

ブランチ候補:

`docs/score-behavior-axis-analysis-plan`

目的:

- `consultation_axis` と行動指標を突合する分析設計を整理する
- save / detail / route_open / visit_done / reflection_saved と軸を結びつける

対象候補:

- docsのみ

## 推奨判断

次PRは **Concierge First UI全体レビュー** が安全。

理由:

- `consultation_axis` のMobile表示は現時点で不要
- analytics実装は、全体レビュー後に必要性を判断した方がよい
- Phase4の締めとして、Web / Mobile / Detail / Ranking / Map / Shrine List を横断して確認する方が自然

## TODO

```markdown
# Mobile Consultation Axis Policy Audit

- [x] develop最新版化
- [x] audit/mobile-consultation-axis-policy 作成
- [x] Mobileのconsultation_axis利用状況確認
- [x] UI表示方針整理
- [x] analytics / context方針整理
- [x] 現PRで実装しない判断
- [x] 次PR候補整理
- [ ] docs/audit/mobile-consultation-axis-policy.md をコミット
- [ ] PR作成
```

## 完了条件

- Mobileで `consultation_axis` をUI表示しない方針が文書化されている
- 将来的なanalytics / context利用候補が整理されている
- Phase4締めの次PR候補が明確になっている
