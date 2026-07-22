> **Status: Proposed Dashboard Configuration / Implementation Active**

# 方位機能 分析ダッシュボード

この文書は既存の方位イベントから、個人情報を使わずに利用状況と改善箇所を把握するための指標・ファネル・PostHog設定案を定義する。外部ダッシュボード自体はこのPRでは変更せず、母艦で設定・レビューする。

## 分析単位と共通条件

- 期間: まず直近28日、比較期間はその直前28日
- 集計: ユニークセッションを基本、操作品質はイベント回数も併記
- 比較軸: `platform = web | mobile`、`origin_type`、`recommendation_rank`
- Web／モバイルの母数は混ぜず、全体値は各platform値を併記してから表示する
- 少数データから個人を推測しない。少数セルは非表示または期間を延長する
- `matched`を利用者属性として保存・cohort化しない

## 推奨ファネル

| Step | Event / filter | 備考 |
|---|---|---|
| 1. 参拝予定日を設定 | `direction_visit_date_set` | 日付値は取得しない |
| 2. 出発地点を選択 | `direction_origin_result`, `result in (success, selected)`, `origin_type != disabled` | device成功または明示選択 |
| 3. 方位条件付き相談を送信 | `direction_condition_submitted`, `has_visit_date=true`, `has_origin=true` | ファネルの基準母数 |
| 4. 方位参考情報を表示 | `direction_match_impression` | 一致候補の後続率は`matched=true`で絞る |
| 5. 候補詳細を開く | `direction_match_detail_opened`, `matched=true` | 順位別も確認 |
| 6. 経路を確認 | `direction_match_route_clicked`, `matched=true` | 現状はモバイルのみ比較可能 |

厳密順序、同一セッション、推奨コンバージョン窓24時間で作成する。結果の再送信を別試行として分析したい場合はイベント回数ビューを補助的に使う。

## 指標定義

| 指標 | 分子 | 分母 | 注意 |
|---|---|---|---|
| 方位条件付き相談率 | submitで`has_visit_date=true AND has_origin=true` | 全`direction_condition_submitted` | 日付だけ／地点だけは含めない |
| 現在地取得成功率 | device + success | deviceのsuccess + denied + failed | `selected`を混ぜない |
| 位置情報拒否率 | device + denied | deviceのsuccess + denied + failed | OS拒否のみ |
| 現在地取得失敗率 | device + failed | deviceのsuccess + denied + failed | 拒否と技術失敗を分離 |
| 手動入力への移行率 | denied後にstation/address selected | device denied | 同一セッション、24時間以内、順序あり |
| 駅名・住所選択率 | station/address + selected | disabledを除く全selectedとdevice success | 地名は収集しない |
| 都道府県選択率 | prefecture + selected | disabledを除く全selectedとdevice success | 都道府県名は収集しない |
| 方位情報無効化率 | disabled + selected | 出発地点方法の全選択結果 | device結果の再試行による重複に注意 |
| 方位参考情報の表示率 | match impressionのあるセッション | 方位条件付き相談セッション | matched true/falseを含む |
| 方位一致候補表示率 | matched=trueのmatch impressionがあるセッション | 方位条件付き相談セッション | 不一致を分子に含めない |
| 詳細表示率 | matched=trueのmatch detail openedがあるセッション | matched=trueのmatch impressionがあるセッション | Web／mobile、rank別 |
| 経路クリック率 | matched=trueのmatch route clickedがあるセッション | matched=trueのmatch impressionがあるセッション | 現状mobileのみ有効 |

`direction_match_impression`は名前を維持しつつ、`direction_reference`表示時に`matched=true/false`を送る。`direction_reference`欠落時は送らないため、情報なしを不一致へ含めない。

## PostHog設定手順（母艦への設定案）

1. Dashboard「Direction feature health」を1つ作成する。
2. Date rangeをLast 28 days、comparisonをPrevious periodにする。
3. 上記6段階をStrict order / Unique sessions / 24 hour windowでFunnel insightへ登録する。
4. Funnel breakdownは`platform`だけを既定表示にする。`origin_type`と`recommendation_rank`は別Insightに分離する。
5. Trendsで現在地取得結果を`direction_origin_result`の`result`別に積み上げ表示する。filterは`origin_type=device`。
6. 手動移行は`direction_origin_result(result=denied, origin_type=device)`から`direction_origin_result(result=selected, origin_type in station,address)`の2段階ファネルにする。
7. 出発地点構成比はsuccess/selectedのみを対象に`origin_type`でbreakdownする。
8. 一致表示→詳細、一致表示→経路を別Funnelにし、後者は`platform=mobile`を固定する。
9. Dashboard descriptionへ本書、イベント契約、欠測条件、最終レビュー日を記載する。
10. 作成後に本番ではない固定テストイベントが混ざっていないことを確認してから共有する。

新しい分析サービス、Person property、住所系プロパティ、個別ユーザーcohortは作成しない。

## 異常値の確認基準

次を「調査開始の目安」とし、機能の良否や因果を断定しない。

- イベント件数が過去4週の同曜日中央値から±30%以上、かつ50セッション以上の差
- 現在地取得成功率が前期間比10ポイント以上低下
- deniedまたはfailedが前期間比5ポイント以上増加
- 手動入力への移行率が前期間比10ポイント以上低下
- Step間CVRが前期間比10ポイント以上低下
- Web／モバイル差が20ポイント以上で、各platform 100セッション以上
- 同一セッション・同一候補のimpressionが複数回観測される
- 禁止属性または契約外属性が1件でも見つかる（即時停止・調査）

確認順は、リリース・障害・母数変化、イベント欠損／重複、platform差、UI導線、初めて最後に利用傾向とする。

## 日盤検討へ進む判断材料

日盤実装の可否はダッシュボードだけで決めない。少なくとも連続2期間（各28日）で以下を満たした場合に、ユーザー調査と技術設計を始める候補とする。

- 方位条件付き相談が各期間500セッション以上
- 方位条件付き相談率が20%以上
- 一致表示→詳細率が全相談の詳細率と比べて継続的に低くない
- モバイル一致表示→経路率が10%以上
- 拒否後の手動移行率が30%以上で、代替導線が機能している
- 技術失敗率が5%未満で、現行年盤・月盤の品質問題が先に残っていない
- 定性調査で「日単位の判断」が実際の課題として確認される

満たしても日盤の有効性は確定しない。時盤は別の利用課題・精度・説明責任を要するため、この判断に含めない。

## 運用チェックリスト

- [ ] Dashboard期間・timezone・conversion windowを確認
- [ ] Web／mobileを分け、経路率はmobile限定であることを表示
- [ ] イベント名と属性が契約通りかLive Eventsで標本確認
- [ ] 緯度経度、住所、駅名、都道府県名、生年月日、相談文、検索語がない
- [ ] impression重複とsubmit欠損を確認
- [ ] 拒否と技術失敗を混同していない
- [ ] 不一致・情報なし・エラー・離脱を推測で分解していない
- [ ] 少数セルから個人を推測できない表示になっている
- [ ] 前期間差の母数とリリース履歴を確認
- [ ] 数値だけで機能の良否や日盤実装を断定していない
- [ ] 確認日、担当、判断、追加調査をDashboard descriptionへ記録

## 関連資料

- `docs/analytics/direction-events.md`
- `packages/shared/directionAnalytics.ts`
- `docs/analytics/recommendation-funnel-analysis.md`
