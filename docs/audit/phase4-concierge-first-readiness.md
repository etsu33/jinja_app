

# Phase4 Concierge First Readiness Audit

## 目的

主要Contract統一とNormalize Cleanup完了後、Phase4として Concierge First UI / Mobile UI 改善へ戻れる状態かを確認する。

本監査では、すぐにUI実装へ入るのではなく、以下を整理する。

- 現在のHome / Concierge導線
- Web / Mobile の推薦表示の現在地
- Concierge Firstへ戻る前に確認すべき前提
- 次PRで扱うべき実装単位

## 前提

以下は完了済み。

- 主要Contract固定
  - `reason_facts`
  - `recommendation_reason_v4`
  - `action_suggestion_v4_preview`
  - `consultation_axis`
  - `explanation`
- Web fallback削減
  - `_reason_facts` fallback削減
  - `_explanation_payload.original_reason` 依存削減
- Web / Mobile 表示差分監査
- Mobile `_reason_facts` fallback削減
- `action_suggestions` Contract監査
- `primary_reason` Contract監査

これにより、推薦APIの意味情報はかなり整理され、UI改善へ戻れる土台はできている。

## 現在地

### Web

主な導線:

- `apps/web/src/app/concierge/page.tsx`
- `apps/web/src/app/concierge/full/page.tsx`
- `apps/web/src/app/concierge/ConciergeClientFull.tsx`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/app/shrines/page.tsx`
- `apps/web/src/app/ranking/page.tsx`

現状:

- Concierge画面は独立導線として存在している
- Shrine一覧 / Ranking も別導線として残っている
- Concierge結果はSectionsRendererで表示される
- 推薦理由 / 根拠 / 行動提案 / 相談軸のContractは整理済み

### Mobile

主な導線:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`

現状:

- Mobile Conciergeは推薦理由・根拠・行動提案previewを表示できる
- Mobile Shrine Detailは推薦理由・根拠・explanationを表示できる
- `consultation_axis` はMobileでは未使用
- `action_suggestion_v4_preview` はMobile Shrine Detailでは未使用

## 判断

Phase4 Concierge First UIへ戻ることは可能。

ただし、いきなりHome統合や大規模UI変更へ入るのはまだ早い。

理由:

- Web / Mobile の表示粒度にはまだ差分がある
- Mobile側のUI改善対象が複数残っている
- Concierge First化はHome導線・検索導線・Ranking導線の優先順位変更を伴う
- 1PRで触る範囲が広がると、Contract整理後の安定性を崩す可能性がある

したがって、次は「大改修」ではなく、以下のどちらかを選ぶのが安全。

```text
A. Concierge First UI readiness docsを作成し、次PR単位を切る
B. Mobile Concierge / Shrine Detail の表示差分を小さく埋める
```

## 優先順位

### 優先A: Mobile表示差分の最小改善

目的:

- Web / Mobile の推薦体験差分を小さくする
- 既存Contractを活かして、Mobile側の表示を少しだけ強化する

候補:

- Mobile Shrine Detailに `action_suggestion_v4_preview` 表示を追加するか検討
- Mobile Conciergeで `explanation.summary` を表示するか検討
- Mobileで `consultation_axis` をanalytics用に保持するか検討

### 優先B: Concierge First導線監査

目的:

- Home / Concierge / Shrine一覧 / Ranking の優先順位を整理する
- Conciergeをトップ主導線に戻す前に、画面責務を明確にする

候補:

- Homeを「相談開始」中心に寄せる
- Shrine一覧をサブ導線にする
- Rankingを補助導線にする
- 参拝スタイル / 誕生日 / ご利益タグを条件追加へ寄せる

### 優先C: Web UI改善

目的:

- Concierge結果画面のカード表示をより分かりやすくする
- Recommendation Reason v4 / reason_facts / action_suggestion_v4_preview を見せ方として整える

候補:

- TopRecommendationHeroの情報密度調整
- 根拠カードの見せ方整理
- action suggestionのCTA整理

## 今回のPRでやること

- Phase4に戻る前提を文書化する
- Home / Concierge / Mobile の現状を整理する
- 次PR候補を優先順位つきで整理する

## 今回のPRでやらないこと

- Home統合はしない
- Mobile UI実装はしない
- Web UI実装はしない
- 新しいContractは追加しない
- 既存Contractのschema変更はしない

## 次PR候補

### 1. Mobile Shrine Detail action suggestion preview

ブランチ候補:

`feature/mobile-shrine-detail-action-suggestion-preview`

目的:

- Mobile Shrine Detailにも `action_suggestion_v4_preview` を表示できるか検証する
- Concierge結果から詳細へ遷移した後も、次の行動が分かる状態にする

変更候補:

- `apps/mobile/app/shrines/[id].tsx`
- route paramsまたはAPIレスポンス経由で `action_suggestion_v4_preview` を受ける設計確認
- 表示は最小カード1つに限定

### 2. Mobile Concierge explanation summary

ブランチ候補:

`feature/mobile-concierge-explanation-summary`

目的:

- Mobile Conciergeで `explanation.summary` を表示するか検証する
- Webとの表示差分を縮める

変更候補:

- `apps/mobile/app/concierge/index.tsx`
- `RecommendationApiCard` の `explanation` 型追加
- summary表示の最小追加

### 3. Concierge First route audit

ブランチ候補:

`audit/concierge-first-route-design`

目的:

- Home / Concierge / Shrine一覧 / Ranking の導線優先順位を整理する
- Concierge First UI実装前に画面責務を固定する

変更候補:

- `docs/audit/concierge-first-route-design.md`
- 実装なし

## 推奨判断

次PRは **Mobile Shrine Detail action suggestion preview** よりも、まず **Concierge First route audit** が安全。

理由:

- 現在はUI実装へ戻る分岐点にいる
- 先に導線設計を固定した方が、Mobile / Web の実装PRがぶれにくい
- Home統合・Concierge First化は画面責務の変更を伴う
- 実装前に「何を主導線にするか」を明文化した方が再現性が高い

ただし、短期で見た目の変化を出したい場合は、Mobile Shrine Detail の行動提案preview追加が最小実装として有効。

## TODO

```markdown
# Phase4 Concierge First Readiness

- [x] develop最新版化
- [x] audit/phase4-concierge-first-readiness 作成
- [x] Home / Concierge導線の該当箇所確認
- [x] Web表示の現在地整理
- [x] Mobile表示の現在地整理
- [x] Phase4へ戻る前提整理
- [x] 次PR候補整理
- [x] 推奨判断整理
- [ ] docs/audit/phase4-concierge-first-readiness.md をコミット
- [ ] PR作成
```

## 完了条件

- Phase4 Concierge Firstへ戻る前提が文書化されている
- 次PR候補が実装単位で分かれている
- 実装に入る前の判断材料が揃っている
