> **Status: Active**

# 方位条件分析イベント

Webとモバイルは`packages/shared/directionAnalytics.ts`をイベント契約の正本とし、既存の分析Providerを使用する。

- `direction_visit_date_set`: 参拝予定日を設定（値は送らない）
- `direction_origin_result`: 出発地点種別と成功・拒否・失敗・選択
- `direction_condition_submitted`: 予定日・確定地点の有無
- `direction_match_impression`: Backendが`matched: true`を返した候補の初回表示
- `direction_match_detail_opened`: 一致候補から詳細へ遷移
- `direction_match_route_clicked`: 一致候補の経路行動

緯度・経度、住所、駅名、都道府県名、生年月日、相談文、検索語は送信しない。表示イベントは候補キーで重複排除する。
方位は相談内容に対する補助情報であり、推薦の主理由として扱わない。
