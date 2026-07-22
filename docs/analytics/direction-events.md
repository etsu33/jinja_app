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
| `direction_match_route_clicked` | 方位一致候補に紐づく経路行動 | `platform`, `matched`, `recommendation_rank` | クリックごと |

`origin_type`は`device | station | address | prefecture | disabled`、`result`は`success | denied | failed | selected`だけを許可する。共有serializerはイベント別allowlist以外を破棄するため、型を迂回した呼び出しでも余分な値をProviderへ渡さない。

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
- 経路クリックは現行モバイル結果の`route_open`でのみ方位一致との関連を保持できる。Web詳細画面へ遷移した後は方位一致コンテキストを保持していないため、Web値は欠測として扱う。
- 相談送信後に一致候補が出ない場合は「不一致」「根拠不足」「通信エラー」「離脱」をこのイベント群だけでは分離できない。既存の一般エラー監視と併記し、0件をエラーと断定しない。

## 変更ルール

イベント追加より既存属性による集計を優先する。追加が必要な場合は、目的、発火箇所、重複単位、保持期間、禁止属性検査、Web／モバイル差を先に本書へ追記する。日盤・時盤の値はこの契約に追加しない。
