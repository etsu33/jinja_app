> **Status: Active / Quality Contract**

# 方位分析イベント データ品質契約と運用手順

`packages/shared/directionAnalytics.ts`の機械可読ルールと`directionAnalyticsQuality.ts`を正本とし、固定イベント列から重複・欠損・契約違反・プライバシー違反を検出する。品質判定のために本番payload、イベント名、ユーザー識別子は増やさない。

## Web／モバイル発火箇所

| Event | Web | Mobile | 品質上の差 |
|---|---|---|---|
| `direction_visit_date_set` | Concierge予定日変更 | Concierge予定日変更 | なし |
| `direction_origin_result` | device取得結果、手動・都道府県・無効化選択 | 同左 | なし |
| `direction_condition_submitted` | Concierge送信 | Concierge送信 | なし |
| `direction_match_impression` | `DirectionReferenceCard`初回表示 | `ResultCard`初回表示 | 一致・不一致とも許可 |
| `direction_match_detail_opened` | Hero／その他の詳細リンク | 結果カード詳細ボタン | 一致候補だけ。順位は任意 |
| `direction_match_route_clicked` | 詳細画面の既存Google Mapsリンク | 結果の`route_open` action | 一致候補だけ。Webは`candidate_position`必須、Mobileは欠落可 |

## 機械可読契約

全イベントの`requiredKeys`、`optionalKeys`、`allowedPlatforms`は`DIRECTION_EVENT_QUALITY_RULES`に定義する。serializerも同じallowlistを参照し、未知属性をProviderへ渡さない。

| Event | 必須 | 任意 |
|---|---|---|
| visit date | `platform` | なし |
| origin result | `platform`, `origin_type`, `result` | なし |
| condition submitted | `platform`, `has_visit_date`, `has_origin` | なし |
| impression | `platform`, `matched` | `recommendation_rank` |
| detail opened | `platform`, `matched` | `recommendation_rank` |
| route clicked | `platform`, `matched` | `recommendation_rank`, `candidate_position` |

## 組み合わせ

許可するorigin結果は`device + success|denied|failed`と`station|address|prefecture|disabled + selected`だけとする。impressionは`matched=true|false`を許可し、detail／routeは現行契約どおり`matched=true`だけを許可する。`candidate_position`はrouteだけで`hero|other`を許可する。

## 重複と欠損

- impressionは`sessionKey + attemptKey + candidateKey`が同一なら1回。再相談で`attemptKey`が変われば同じ候補でも別表示とする。
- detail／routeは明示操作なので回数だけで重複判定しない。ただし同じ固定列で先行impressionがなければエラーとする。
- device拒否後に相談送信まで進み、間にstation/addressのselectedがなければwarningとする。拒否後に終了しただけなら正当な離脱として警告しない。
- 品質検証用キーを本番イベントへ追加しない。

## Severity

- `error`: 未知イベント、必須属性欠落、不正platform・enum・組み合わせ、契約外／禁止属性、impression重複、先行表示なしの操作。
- `warning`: 拒否後に相談を続けた際の手動選択欠損、期間比較の異常値。warningだけならレポートの`valid`はtrueとする。

## プライバシー

禁止キーは`DIRECTION_ANALYTICS_FORBIDDEN_KEYS`で一元管理する。緯度経度、住所、駅名、都道府県名、神社名・住所、Place ID、経路URL、生年月日、予定日、相談文、推薦理由、検索語、方位文言を含めない。camelCase／snake_caseなどの表記揺れも正規化して検出する。

## 誤検知を避ける条件

- すべての利用が6段階を完走するとは限らないため、一般的な離脱をerrorにしない。
- detail／routeの複数クリックは実操作の可能性があるため、件数だけで重複としない。
- Mobileの`candidate_position`欠落を異常とせず、unknownで補完しない。
- 品質レポート用のsequence keyがない場合、表示順序を推測しない。
- 閾値超過は調査開始条件であり、機能の良否や因果を断定しない。

## CI

ローカルとCIの明示実行:

```bash
pnpm test:direction-analytics-quality
```

Web workflowは専用テストを実行し、既存のWeb／Mobile全テストも品質契約の回帰を収集する。外部PostHogや追加サービスへ接続しない。

## 障害調査・運用チェックリスト

- [ ] 集計期間、timezone、conversion windowを確認
- [ ] リリース前後と過去同曜日を比較
- [ ] Web／Mobileを分け、各母数を確認
- [ ] 未知イベント、必須属性、enum、組み合わせ違反を確認
- [ ] 禁止属性が0件であることを確認。1件でもあれば送信停止を含めて即時調査
- [ ] impression重複率と再相談のattempt境界を確認
- [ ] detail／routeに先行impressionがあるか確認
- [ ] device拒否後の手動移行率を確認し、正当な離脱と区別
- [ ] Web routeの`candidate_position`とMobileでの許容欠落を確認
- [ ] 障害、リリース、計測仕様変更の履歴を確認
- [ ] 調査日、担当、母数、判断、追加調査を記録
- [ ] 数値だけで機能の良否、吉凶、日盤実装を断定しない

## 記録テンプレート

| 確認日 | 担当 | 期間／timezone | Platform | 母数 | Issue code | 判断 | 次の調査 |
|---|---|---|---|---:|---|---|---|
| - | - | - | - | - | - | - | - |
