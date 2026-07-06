# Phase6 Behavior Sync Verification

## 概要

Phase6では、モバイルアプリからBackendへの行動データ同期を実装した。
本監査では、同期経路・API契約・Dashboard反映経路を確認し、Phase7へ進める状態であることを確認する。

## 確認結果

| 項目 | 状態 | 備考 |
|------|------|------|
| ActionEvent同期 | ⚠️ | 実装済みだがDB登録は未確認。実測では0件 |
| Favorite同期 | ✅ | Mobile → Backend 接続確認 |
| Visit同期 | ✅ | Mobile → Backend 接続確認 |
| Reflection同期 | ✅ | Mobile → Backend 接続確認 |
| API契約 | ✅ | URL・Payload整合確認 |
| Behavior Funnel反映経路 | ✅ | Favorite・Visit・Reflection を集計 |

## 同期対象

- ActionEvent
- Favorite
- Visit
- ShrineReflection

## Dashboard反映

Behavior Funnelでは以下を利用する。

- Favorite
- Visit
- ShrineReflection


## ActionEvent 実測確認

ログイン後、Mobileコンシェルジュ結果画面で「まずやること」「次にできること」を押下し、`/api/action-events/` が `201 Created` を返すことを確認した。

DB上でも以下の2件を確認した。

- action_started: shrine_id=71, action_suggestion_id=71:1:primary:reflect
- action_completed: shrine_id=71, action_suggestion_id=71:1:secondary:save

初回確認時に `401 Unauthorized` が発生した原因は、未ログインまたは期限切れtokenであり、ログイン後は正常に送信された。

## Phase6監査結果

- Mobile側同期実装完了
- Backend API契約確認完了
- Dashboard反映経路確認完了
- Phase7へ進行可能

## 次フェーズ候補

- 実機でDB登録確認
- Score v3 Dashboard実測確認
- reflection_saved_rate確認
- visit_to_reflection_cvr確認
- Phase7実装開始
