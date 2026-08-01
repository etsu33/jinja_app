# Shrine Knowledge Real Data Pilot #1

## Status
Completed

## Pilot対象
- Shrine: 明治神宮
- Existing Shrine recordを再利用
- 実施日: 2026-08-01

## 目的
Shrine Knowledge Model Foundationが実在神社・実在Sourceで成立するか検証する。

## Source検証
- Source type: shrine_official
- Title: 明治神宮 公式サイト「明治神宮とは」
- Publisher: 明治神宮
- URL: https://www.meijijingu.or.jp/about/
- verification_status: source_confirmed
- confidence: high

## Deity検証
- 明治天皇
  - role: enshrined
  - sort_order: 0
  - source_confirmed
  - confidence: high
- 昭憲皇太后
  - role: enshrined
  - sort_order: 1
  - source_confirmed
  - confidence: high

### 結果
- 1 Shrineに複数Deityを登録可能
- 同一Sourceを複数Deityから参照可能
- 保存後もSource Relationを保持

## History検証
- history_type: official_origin
- title: 明治神宮の創建
- content: 明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。
- period_text: 大正9年（1920）
- event_date: 未設定
- verification_status: source_confirmed
- confidence: high
- Source: 明治神宮公式Source（Deityと同一Sourceを共有）

### 結果
- ShrineHistoryを実データ登録可能
- HistoryからSourceを追跡可能
- Deityと同一のSourceを共有して参照可能
- 保存後もSource Relationを保持

## Admin QA
- URLありSource保存
- URLなしSource保存
- source_confirmed時のverified_at必須Validation
- Search
- source_type filter
- verification_status filter
- 再編集
- Admin変更履歴（History）確認

## 成功した要件
- ShrineKnowledgeSource / ShrineDeity / ShrineHistoryの3Modelとも、実神社データを用いてAdminから作成・保存できた
- 1 Shrineに複数Deityを登録でき、同一SourceをDeity・History間で共有できた
- 保存後に編集画面を再度開いても、Deity/HistoryとSourceのRelationが保持されていた
- verification_status=source_confirmed時にverified_at必須のValidationが機能した
- Admin標準機能（Search／source_typeフィルタ／verification_statusフィルタ／再編集／変更履歴確認）が実データに対して問題なく動作した
- URLの有無にかかわらずSourceを登録できた（URL必須ではない情報源を保存できる設計が実データで機能した）
- 一連の操作でBlockingは確認されなかった

## Blocking
なし

## Improvement
- verified_at入力UIが分かりづらい
- verification_statusを選び忘れやすい
- Help Textが不足
- Source数増加時の選択UIは今後再評価が必要

## 未検証事項
- 性質の異なる実在神社（祭神数が多い、由緒が複雑、伝承と史実が混在する等）でのPilotは未実施
- 複数Source間で情報が一致しない（内容が矛盾する）ケースの検証は未実施（今回は単一Sourceのみ使用）
- official_originとtraditionを別ShrineHistoryレコードとして分離保持するケースの検証は未実施（今回登録したのはofficial_originのみ）
- Shrine Detail API（`/api/shrines/{id}/`）のレスポンスに今回登録したdeities/historiesが実際に反映されることの確認は本Pilotの対象外（Admin入力側のみ検証した）
- URL以外の出典属性（書籍・論文・パンフレット・現地案内板等）を用いた実データ登録は未実施（今回はWeb URLのみ）
- 105件全体へ横展開した場合の入力コスト・運用性は未検証（明治神宮1社のみで検証）

## Foundation残り5%完了条件

今回の明治神宮1社のみのPilotをもってFoundationを100%完了とは判断しない。以下を完了条件とする。

1. 性質の異なる実在神社でPilot #2を実施すること
2. Source間で情報が一致しないケースを1件以上検証すること
3. official_originとtraditionを分離して保持できるケースを検証すること
4. Pilot #1・#2の両方でBlockingが確認されないこと

上記4条件を満たした場合でも、Foundation 100%の最終判定は母艦判断へ差し戻す。

## Pilot #2条件

Pilot #2は以下を満たす神社・データで実施する。

- 明治神宮とは性質の異なる実在神社を対象とする（例: 祭神が多数、由緒に複数の伝承がある、創建年代が確定していない等）
- 内容が一致しない複数のSourceを1件以上登録する（Evidence Gate自体は未実装のため、今回はKnowledge Model側でのデータ保持のみを検証対象とする）
- official_origin（確定した由緒）とtradition（伝承）を別ShrineHistoryレコードとして分離登録できることを確認する
- Pilot #1と同様にAdmin QA（保存・検索・フィルタ・再編集・変更履歴）を実施し、Blockingの有無を確認する

## 結論

Shrine Knowledge Model Foundationは、明治神宮という実在の1神社・実データを用いたPilot #1において、Model作成・Source共有・保存後のRelation維持・Admin標準機能のいずれについてもBlockingなく動作することを確認した。一方、性質の異なる神社でのPilotや、Source間の不一致、official_origin/traditionの分離保持といった、より複雑なケースの検証は行っていない。

したがって本Pilot #1の結果のみをもってFoundationの100%完了とはせず、Pilot #2の実施と本文書に定義した完了条件の充足を前提とし、最終的な100%判定は母艦判断に委ねる。
