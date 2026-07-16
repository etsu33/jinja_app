# Phase7 Implementation Scope Audit

## 1. Purpose

Phase7では、KAMI MUSUBIの体験を「相談して終わり」から「相談、参拝、振り返り、継続利用」へ接続する。

この監査では、既存のPhase7設計ドキュメントを実装へ落とす前に、変更対象となるWeb、Backend、API、Analytics、Billing関連ファイルを分類し、PR単位で安全に実装できる範囲を整理する。

本ドキュメントは実装方針の整理であり、このPRではコード変更を行わない。

---

## 2. Phase7実装計画時点の設計資料

Phase7実装計画を作成した時点では、以下の設計ドキュメントを前提としていた。

現在のPremium関連仕様については、`docs/product/pricing.md`、`docs/product/premium-experience.md`、`docs/product/billing-paywall.md`および`docs/product/monetization-flow-design.md`を参照する。

| Document                                 | Role                                 |
| ---------------------------------------- | ------------------------------------ |
| `docs/audit/phase7-ux-monetization-roadmap.md` | 旧Phase7全体ロードマップの履歴       |
| `docs/product/shrine-detail-v3-design.md`        | 神社詳細画面v3のUX設計               |
| `docs/visit-flow-design.md`              | 参拝前、参拝中、参拝後の行動導線設計 |
| `docs/product/reflection-timeline-design.md`     | 参拝後の振り返りとタイムライン設計   |
| `docs/product/pricing.md`                        | Premium提供価値と価格説明の現行正本  |
| `docs/product/premium-experience.md`             | Premium体験境界の現行正本            |
| `docs/product/billing-paywall.md`                | 課金状態とPaywall判定の現行正本      |
| `docs/product/monetization-flow-design.md`       | 課金導線とPremium遷移・計測の設計    |
| `docs/audit/premium-plan-design.md`      | Premium長期構想の履歴                |

---

## 3. Implementation Principle

Phase7の実装では、以下の順序を守る。

1. Shrine Detail v3を起点に、ユーザーが次に取る行動を明確にする
2. Visit Flowで「参拝しました」導線を自然に扱う
3. Reflection Timelineで参拝後の記録を継続利用へ接続する
4. Premiumは体験拡張として差し込み、先に売り込みすぎない
5. Analytics / ActionEventは行動変化と収益導線の計測基盤として扱う

Phase7では、推薦ロジックそのものを大きく変更しない。優先するのは、推薦結果を見た後の行動導線、記録導線、継続導線の改善である。

---

## 4. Shrine Detail v3 Scope

### Goal

神社詳細画面を、情報閲覧ページから「次の行動を決めるページ」へ変更する。

ユーザーが詳細画面に来た時点で迷いやすい行動は以下である。

- なぜこの神社が合うのかを理解する
- 保存する
- ルートを開く
- 実際に行くか判断する
- 参拝後に記録する

### Primary Files

| File                                                | Role                           |
| --------------------------------------------------- | ------------------------------ |
| `apps/web/src/app/shrines/[id]/page.tsx`            | Shrine Detail本体              |
| `apps/web/src/app/api/shrines/[id]/route.ts`        | 詳細取得API proxy              |
| `apps/web/src/lib/api/shrines.ts`                   | Shrine API client              |
| `apps/web/src/lib/api/shrines.client.ts`            | Client側 Shrine API helper     |
| `apps/web/src/lib/api/shrines.server.ts`            | Server側 Shrine API helper     |
| `apps/web/src/lib/api/shrineInteractions.ts`        | 保存・閲覧などの行動API helper |
| `apps/web/src/app/api/shrine-interactions/route.ts` | shrine interaction API proxy   |
| `apps/web/src/lib/auth/actionGuards.ts`             | ログイン必須行動の制御         |

### Related UI Files

| File                                                           | Role                               |
| -------------------------------------------------------------- | ---------------------------------- |
| `apps/web/src/components/shrines/ShrineCard.tsx`               | 一覧・推薦カードの基準UI           |
| `apps/web/src/components/shrines/ShrineCardCompact.tsx`        | 小型カード                         |
| `apps/web/src/components/shrines/ShrineCardLite.tsx`           | 軽量カード                         |
| `apps/web/src/components/shrines/ShrineConciergeCard.tsx`      | Concierge結果内の神社カード        |
| `apps/web/src/features/concierge/detailHref.ts`                | Conciergeから詳細ページへのURL生成 |
| `apps/web/src/features/concierge/__tests__/detailHref.test.ts` | 詳細URL生成テスト                  |

### Implementation Notes

Shrine Detail v3では、以下の順序で情報を出す。

1. 神社名、所在地、概要
2. この相談とどうつながるか
3. 推薦理由
4. 今日できる行動提案
5. 保存、ルート、参拝しましたのCTA
6. 参拝後の振り返り導線

詳細画面では、Premiumの訴求を主役にしない。まずは「行く理由」と「次の一手」を明確にする。

---

## 5. Visit Flow Scope

### Goal

「参拝しました」を、ユーザーにとって自然なタイミングで押せる導線として整理する。

参拝前は行動予定、参拝中は邪魔しない、参拝後は振り返りへつなぐ。

### Primary Files

| File                                                     | Role                      |
| -------------------------------------------------------- | ------------------------- |
| `apps/web/src/app/api/shrines/[id]/visit/route.ts`       | 神社単位のvisit API proxy |
| `apps/web/src/app/api/visits/route.ts`                   | visit一覧・作成API proxy  |
| `apps/web/src/lib/api/visits.ts`                         | Visit API client          |
| `backend/temples/api/serializers/visit.py`               | Visit serializer          |
| `backend/temples/api/views/visit.py`                     | Visit API view            |
| `backend/temples/tests/api/test_journey_timeline_api.py` | Timeline連携APIテスト     |

### Related Backend Files

| File                                                                   | Role                     |
| ---------------------------------------------------------------------- | ------------------------ |
| `backend/temples/services/journey_timeline.py`                         | 行動履歴タイムライン生成 |
| `backend/temples/tests/services/test_journey_timeline.py`              | Timeline service test    |
| `backend/temples/services/action_completion_observation.py`            | 行動完了の観測           |
| `backend/temples/tests/services/test_action_completion_observation.py` | 行動完了観測テスト       |

### Implementation Notes

Visit Flowでは、GPSや日時を必須にしない。MVPでは、ユーザーが自分で押す「軽い記録」を正本とする。

将来的には、GPSや日時を補助情報として扱えるが、参拝体験を監視されている感覚にしないことを優先する。

---

## 6. Reflection Timeline Scope

### Goal

参拝後の振り返りを、単発のメモではなく、次回相談やPremium体験につながる履歴資産として扱う。

### Primary Files

| File                                                      | Role                           |
| --------------------------------------------------------- | ------------------------------ |
| `apps/web/src/app/api/shrines/[id]/reflection/route.ts`   | 神社単位のreflection API proxy |
| `apps/web/src/lib/api/reflections.ts`                     | Reflection API client          |
| `apps/web/src/lib/api/__tests__/reflections.test.ts`      | Reflection API client test     |
| `backend/temples/api/serializers/reflection.py`           | Reflection serializer          |
| `backend/temples/api/views/reflection.py`                 | Reflection API view            |
| `backend/temples/tests/api/test_shrine_reflection_api.py` | Reflection API test            |

### Related Files

| File                                                                          | Role                       |
| ----------------------------------------------------------------------------- | -------------------------- |
| `backend/temples/services/reflection_state_change.py`                         | 振り返りから状態変化を抽出 |
| `backend/temples/tests/services/test_reflection_state_change.py`              | 状態変化抽出テスト         |
| `backend/temples/tests/services/test_reflection_hint_observation_contract.py` | 振り返りヒント観測契約     |
| `docs/product/reflection-timeline-design.md`                                          | UI / 体験設計              |
| `docs/analytics/reflection-next-recommendation-design.md`                     | 次回推薦との接続設計       |

### Implementation Notes

Reflection Timelineでは、最初から重い入力フォームにしない。

MVPでは、以下のような軽い入力を優先する。

- 行ってみてどうだったか
- 気持ちは少し変わったか
- 次に意識したいことは何か

Premiumでは、過去の振り返りをもとに深掘り質問や状態変化の比較を提供する。

---

## 7. Premium / Billing Scope

### Goal

Premiumは、無料体験の途中で無理に差し込むのではなく、振り返りや履歴活用を深めたいタイミングで提示する。

Phase7のPremium訴求は、以下の3価値に寄せる。

- 振り返りをもっと深くする
- 履歴をもっと活用できる
- AIとの継続性を高める

### Primary Web Files

| File                                                | Role                 |
| --------------------------------------------------- | -------------------- |
| `apps/web/src/app/billing/page.tsx`                 | Billing top          |
| `apps/web/src/app/billing/upgrade/page.tsx`         | Upgrade page         |
| `apps/web/src/app/billing/success/page.tsx`         | Checkout success     |
| `apps/web/src/app/billing/cancel/page.tsx`          | Checkout cancel      |
| `apps/web/src/app/billing/manage/page.tsx`          | Billing management   |
| `apps/web/src/features/billing/hooks/useBilling.ts` | Billing state hook   |
| `apps/web/src/lib/api/billing.ts`                   | Client billing API   |
| `apps/web/src/lib/api/billing.server.ts`            | Server billing API   |
| `apps/web/src/api/conciergePlan.ts`                 | Concierge plan state |

### Primary Backend Files

| File                                           | Role                 |
| ---------------------------------------------- | -------------------- |
| `backend/temples/api/views/billing.py`         | Billing API view     |
| `backend/temples/services/billing_checkout.py` | Checkout session生成 |
| `backend/temples/services/billing_state.py`    | Billing state判定    |
| `backend/users/services/billing.py`            | User billing service |

### Premium UI Files

| File                                                                   | Role                      |
| ---------------------------------------------------------------------- | ------------------------- |
| `apps/web/src/features/concierge/components/PremiumStateDeltaCard.tsx` | Premium向け状態差分カード |
| `apps/web/src/lib/premium/accessLevel.ts`                              | Premium access判定        |
| `apps/web/src/lib/premium/cardVisibility.ts`                           | Premium card visibility   |
| `docs/product/pricing.md`                                                      | Premium提供価値境界       |
| `docs/product/premium-experience.md`                                           | Premium体験境界           |
| `docs/product/billing-paywall.md`                                              | 課金状態・Paywall判定     |
| `docs/product/monetization-flow-design.md`                                     | 収益導線・継続計測設計    |

### Implementation Notes

Premium導線は、詳細画面の最上部ではなく、以下のような文脈で出す。

- 振り返り保存後
- 過去の相談との差分を見たい時
- 参拝履歴が複数件たまった時
- AIに継続相談したい時

購入前に価値を説明しすぎるより、無料体験で価値の種を見せる。

---

## 8. Analytics / ActionEvent Scope

### Goal

Phase7の改善判断を、感覚ではなく行動データで行えるようにする。

優先するKPIは以下である。

| KPI                     | Meaning                       |
| ----------------------- | ----------------------------- |
| detail_view_rate        | 推薦から詳細へ進んだ割合      |
| save_rate               | 詳細から保存した割合          |
| route_open_rate         | ルートを開いた割合            |
| visit_done_rate         | 参拝しましたを押した割合      |
| reflection_saved_rate   | 振り返りを保存した割合        |
| premium_click_rate      | Premium導線をクリックした割合 |
| checkout_start_rate     | 決済開始率                    |
| premium_conversion_rate | 課金転換率                    |

### Primary Files

| File                                                               | Role                             |
| ------------------------------------------------------------------ | -------------------------------- |
| `apps/web/src/lib/analytics/actionEvents.ts`                       | ActionEvent logging helper       |
| `apps/web/src/lib/analytics/billing.ts`                            | Billing analytics helper         |
| `apps/web/src/lib/analytics/conciergeDecisionSummary.ts`           | Concierge意思決定分析            |
| `apps/web/src/app/api/shrine-interactions/route.ts`                | Shrine interaction logging route |
| `backend/temples/api/serializers/action_event.py`                  | ActionEvent serializer           |
| `backend/temples/api/views/action_event.py`                        | ActionEvent API view             |
| `backend/temples/services/action_suggestion_builder.py`            | 行動提案生成                     |
| `backend/temples/services/action_suggestions.py`                   | 行動提案service                  |
| `backend/temples/tests/api/test_action_event_api.py`               | ActionEvent API test             |
| `backend/temples/tests/services/test_action_suggestion_builder.py` | Action suggestion builder test   |
| `backend/temples/tests/services/test_action_suggestions.py`        | Action suggestions service test  |

### Implementation Notes

Analyticsは、UI実装と同時に最低限入れる。ただし、最初から複雑なダッシュボードを作らない。

Phase7前半では、イベントが安全に記録できる状態を優先する。

---

## 9. Concierge Connection Scope

### Goal

Conciergeの推薦結果から、Shrine Detail v3、Visit Flow、Reflection Timelineへ自然に接続する。

### Primary Files

| File                                                                            | Role                              |
| ------------------------------------------------------------------------------- | --------------------------------- |
| `apps/web/src/app/concierge/page.tsx`                                           | Concierge入口                     |
| `apps/web/src/app/concierge/ConciergeClientFull.tsx`                            | Concierge main client             |
| `apps/web/src/features/concierge/components/PrimaryRecommendationCard.tsx`      | 主要推薦カード                    |
| `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx` | Top recommendation hero           |
| `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`      | 推薦セクション表示                |
| `apps/web/src/features/concierge/sectionsBuilder.ts`                            | セクション構築                    |
| `apps/web/src/features/concierge/types/unified.ts`                              | 統合推薦型                        |
| `apps/web/src/viewmodels/conciergeResultItem.ts`                                | Concierge result view model       |
| `apps/web/src/viewmodels/conciergeToShrineList.ts`                              | Concierge結果から神社一覧への変換 |

### Implementation Notes

Concierge側では、詳細ページに渡す情報を増やしすぎない。

詳細ページは、`shrine_id` と必要最小限のcontextをもとに、詳細情報と行動導線を構成する。URLに推薦理由全文やAction
Suggestion全文を持たせない方針は維持する。

---

## 10. Deprecated / Legacy Scope

以下のファイルはPhase7実装の直接対象にしない。削除判断は別PRで扱う。

| File                                                                             | Status |
| -------------------------------------------------------------------------------- | ------ |
| `backend/temples/_deprecated/concierge_api_views.py`                             | 保留   |
| `backend/temples/_deprecated/concierge_django_views.py`                          | 保留   |
| `apps/web/src/features/concierge/components/legacy/RecommendationSwitchList.tsx` | 保留   |
| `apps/web/src/features/concierge/components/legacy/RecommendationUnit.tsx`       | 保留   |

これらはPhase7実装中に参照されていないことを確認できた場合、別途 cleanup PR で削除検討する。

---

## 11. Proposed PR Order

Phase7は以下の順序で実装する。

### PR1: Shrine Detail v3 UI Structure

詳細画面の情報構造とCTA優先順位を整理する。

対象:

- `apps/web/src/app/shrines/[id]/page.tsx`
- `apps/web/src/lib/api/shrines.ts`
- `apps/web/src/lib/api/shrineInteractions.ts`
- 必要に応じて関連テスト

主な変更:

- 推薦理由エリアの整理
- 行動提案エリアの配置
- 保存、ルート、参拝CTAの優先順位整理
- Reflection導線の仮置き

### PR2: Visit Flow CTA Integration

詳細画面からVisit APIへの導線を整理する。

対象:

- `apps/web/src/app/api/shrines/[id]/visit/route.ts`
- `apps/web/src/app/api/visits/route.ts`
- `apps/web/src/lib/api/visits.ts`
- `backend/temples/api/views/visit.py`
- `backend/temples/api/serializers/visit.py`

主な変更:

- 参拝しましたCTA
- 参拝記録後のUI状態
- Reflectionへの接続

### PR3: Reflection Timeline Entry

参拝後の振り返り入口を整理する。

対象:

- `apps/web/src/app/api/shrines/[id]/reflection/route.ts`
- `apps/web/src/lib/api/reflections.ts`
- `backend/temples/api/views/reflection.py`
- `backend/temples/api/serializers/reflection.py`
- `backend/temples/services/journey_timeline.py`

主な変更:

- 振り返り入力導線
- 参拝履歴との接続
- Timeline表示の初期構造

### PR4: Premium Teaser Placement

Premiumの訴求位置を無料体験の流れに合わせて配置する。

対象:

- `apps/web/src/app/billing/upgrade/page.tsx`
- `apps/web/src/features/billing/hooks/useBilling.ts`
- `apps/web/src/features/concierge/components/PremiumStateDeltaCard.tsx`
- `apps/web/src/lib/premium/accessLevel.ts`
- `apps/web/src/lib/premium/cardVisibility.ts`

主な変更:

- Reflection後のPremium teaser
- 過去履歴活用のPremium説明
- 無料ユーザー向け表示制御

### PR5: Monetization Analytics

課金導線と行動導線のイベント計測を追加する。

対象:

- `apps/web/src/lib/analytics/actionEvents.ts`
- `apps/web/src/lib/analytics/billing.ts`
- `backend/temples/api/views/action_event.py`
- `backend/temples/api/serializers/action_event.py`

主な変更:

- premium_click
- checkout_start
- visit_done
- reflection_saved
- route_open
- save

---

## 12. Non Goals

Phase7前半では以下を行わない。

- 推薦スコアの大幅変更
- Score v3 active化
- Premium限定推薦ロジックの追加
- GPS必須化
- 参拝中通知の実装
- 複雑な分析ダッシュボードの追加
- legacy / deprecated ファイル削除

---

## 13. Completion Definition

この監査PRの完了条件は以下とする。

- Phase7関連ファイルが分類されている
- 実装PR順序が明確になっている
- どのPRで何を触るかが整理されている
- 削除対象と保留対象が混ざっていない
- このPRではコード変更を行っていない

---

## 14. Phase7実装計画時点のRecommendation

本監査時点では、次の実装PRを `Shrine Detail v3 UI Structure` としていた。

理由は、Phase7全体の体験が詳細画面を起点に接続される構成だったためである。

```text
Concierge
↓
Shrine Detail v3
↓
Save / Route / Visit
↓
Reflection
↓
Timeline / Premium
```

この実装順序は監査時点の記録であり、現在の次タスクや開発優先順位を決定するものではない。現在の開発順序は`docs/core/roadmap.md`、GitHub Issueおよびマージ済みPRを参照する。
