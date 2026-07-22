> **Status: Active / Contract**

# 方位分析イベント契約

Webとモバイルは`packages/shared/directionAnalytics.ts`を正本とし、既存のPostHog Providerだけを使用する。イベント名・属性・意味は両者で共通であり、`platform`だけが異なる。

| Event | 発火条件 | 許可する属性 | 重複の単位 |
|---|---|---|---|
| `direction_visit_date_set` | 空でない参拝予定日を設定・変更する操作 | `platform` | 日付変更ごと。日付値は送らない |
| `direction_origin_result` | 現在地取得結果、または出発地点種別の選択 | `platform`, `origin_type`, `result` | 操作結果ごと |
| `direction_condition_submitted` | 方位条件を含み得る相談送信 | `platform`, `has_visit_date`, `has_origin` | 送信試行ごと |
| `direction_match_impression` | Backendの`direction_reference`付き候補を初めて表示 | `platform`, `matched`, `recommendation_rank` | 表示カードのマウントごとに1回 |
| `direction_match_detail_opened` | 方位一致候補から詳細を開く | `platform`, `matched`, `recommendation_rank` | クリックごと |
| `direction_match_route_clicked` | 方位一致候補に紐づく既存経路導線の明示操作 | `platform`, `matched`, `recommendation_rank`, `candidate_position` | クリックごと |

`origin_type`は`device | station | address | prefecture | disabled`、`result`は`success | denied | failed | selected`、`candidate_position`は`hero | other`だけを許可する。共有serializerはイベント別allowlist以外を破棄するため、型を迂回した呼び出しでも余分な値をProviderへ渡さない。

## 禁止属性

次の値はイベント名を問わず送信しない。

- 緯度・経度、住所、駅名、都道府県名、検索語
- 生年月日、相談文、プロフィール入力
- 実際の方位、吉凶、予定日そのもの
- shrine名、個別ユーザーを方位評価する属性

`has_visit_date`と`has_origin`は値そのものではなく有無だけを表す。`matched`は候補単位のUI条件であり、利用者個人の吉凶判定やセグメント作成には使わない。

## Web／モバイル監査結果

- 6イベントは共有型から送信され、名前と属性の意味は一致している。
- 方位参考情報の表示は一致・不一致とも送り、Web／モバイルとも表示カードのマウント中に1回だけ送る。再相談で同じ候補が再表示された場合は新しい表示として送る。
- 詳細クリックは両方で取得でき、順位も共通属性として送る。
- Webの推薦結果には直接の経路ボタンはなく、Hero／その他候補の詳細導線と詳細画面の既存「Googleマップで経路案内」が実在する。契約上有効な`direction_reference`を持つ候補だけ、`matched`と`candidate_position`の分類値を詳細URLへ引き継ぐ。
- Webは詳細画面の既存経路リンクを利用者が明示操作した時だけ送る。描画、再描画、フォーカス、詳細遷移では送らない。URL、候補、神社、方位カードの内容は渡さない。
- `direction_match_route_clicked`は既存契約どおり一致候補（`matched=true`）を対象とする。不一致候補の通常の`route_open`は維持するが、方位経路イベントには含めない。
- `candidate_position`はWebでは`hero | other`を送る。既存モバイル実装は`recommendation_rank`を継続し、属性欠落を0やunknownへ置換しない。
- 相談送信後に一致候補が出ない場合は「不一致」「根拠不足」「通信エラー」「離脱」をこのイベント群だけでは分離できない。既存の一般エラー監視と併記し、0件をエラーと断定しない。

## 変更ルール

イベント追加より既存属性による集計を優先する。追加が必要な場合は、目的、発火箇所、重複単位、保持期間、禁止属性検査、Web／モバイル差を先に本書へ追記する。日盤・時盤の値はこの契約に追加しない。
