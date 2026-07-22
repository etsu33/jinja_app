# Testing Policy

## テスト種別
- Unit: ロジック保証
- Integration: API契約
- Contract: Web↔Backend整合

## 外部API
- 原則モック
- 実コールは禁止（コスト事故防止）

## CI失敗時の判断
- lint/format → 必ず直す
- flaky test → 原因記録して再実行可

## Web E2E

- Playwright ChromiumをCIで実行する。
- 相談API、ジオコード、認証、課金、タグ取得はブラウザrouteで固定レスポンス化する。
- 実Backend、外部ジオコードAPI、本番データへ接続しない。
- CIは2 worker、失敗時2 retryとし、traceは最初のretryで保存する。
- 方位条件の正本は `apps/web/e2e/05_direction_flow.spec.ts` とする。

### 方位条件の検証範囲

- 位置情報許可 → 予定日設定 → 相談送信 → Backendの方位参考情報表示
- 位置情報拒否 → 駅名・住所候補の明示選択 → 相談送信
- 都道府県の概算表示と概算注記の維持
- 方位情報を使用しない場合の `location` 省略、方位カード非表示、相談継続
- 根拠不足時の `direction_reference` 非表示
- 方位計算の故障注入時に通常推薦を維持
- malformed／未知方式の `direction_reference` 非表示
- ジオコード500・タイムアウト後の通常相談継続
- 分析例外と不正地図URLの安全な縮退
- 一致・不一致文言、方位一致表示イベントの一回送信
- 分析payloadに緯度・経度、住所、駅名、都道府県、生年月日、相談文を含めない

方位加点 `+0.02` と根拠不足時のBackend契約は、Backend service/API testで検証する。年盤・月盤のみを対象とし、日盤・時盤は混在させない。
