

# Mobile Release Readiness Audit

> **Status: Archive**
>
> 本ドキュメントは、Mobile Release前提のチェックリストと進捗を記録した時点監査である。
>
> EAS・実機・API・認証のRelease条件は、現行の実装・運用ドキュメントを正本とする。

## 目的

神社_APP のモバイル版を本番配布へ進める前に、主要導線・API接続・認証・EAS移行準備の未完了項目を整理する。

この監査は「すぐストア申請するため」ではなく、EAS preview build と内部テストへ進めるための前提条件を明確にするために行う。

## 現在地

- フロントエンドは mobile 実装フェーズ
- 神社詳細 v3 の Web / Mobile 表示順は整理済み
- 振り返り履歴一覧・タイムライン・詳細表示は実装済み
- 相談履歴タイムライン v1 は実装済み
- 本番配布準備は未着手に近い

## 本番移行までの大きな流れ

```markdown
1. 体験導線を完成させる
2. 実機で詰まりを潰す
3. production API URL / env を整える
4. EAS preview build
5. 内部テスト
6. ストア申請
```

## 主要導線チェックリスト

### Home → Concierge

- [ ] Home の相談入力から Concierge へ遷移できる
- [ ] 相談文が Concierge 画面に引き継がれる
- [ ] 未入力時の表示が破綻しない
- [ ] CTA 文言が「相談する」目的と一致している

### Concierge → 神社詳細

- [ ] 推薦結果カードから神社詳細へ遷移できる
- [ ] 神社IDが正しく渡る
- [ ] 推薦理由が詳細画面でも表示される
- [ ] consultationSummary / shrineMeaning / actionMeaning が欠けても表示崩れしない
- [ ] 再提案導線が迷子にならない

### 神社詳細 → 行動記録

- [ ] 参拝記録を保存できる
- [ ] 振り返りを保存できる
- [ ] 保存後の成功表示がある
- [ ] 未ログイン時の挙動が破綻しない
- [ ] 保存失敗時の Error 表示がある

### 記録 → 各履歴画面

- [ ] 記録画面からお気に入りへ遷移できる
- [ ] 記録画面から御朱印へ遷移できる
- [ ] 記録画面から参拝履歴へ遷移できる
- [ ] 記録画面から振り返り履歴へ遷移できる
- [ ] 記録画面から相談履歴へ遷移できる
- [ ] 最近見た神社へ遷移できる

### 相談履歴タイムライン

- [ ] `/api/concierge-threads/` を取得できる
- [ ] title が表示される
- [ ] last_message が表示される
- [ ] message_count が表示される
- [ ] last_message_at / updated_at / created_at の日付表示が崩れない
- [ ] 日付ごとのグルーピングが表示される
- [ ] EmptyState が表示される
- [ ] Loading が表示される
- [ ] Error が表示される
- [ ] Pull to Refresh が動作する

### 振り返り履歴タイムライン

- [ ] `/api/reflections/` を取得できる
- [ ] 神社名が表示される
- [ ] history_theme が表示される
- [ ] answer が表示される
- [ ] state_change_summary が表示される
- [ ] state_change_direction が表示される
- [ ] next_need_hint が表示される
- [ ] タップで詳細Modalが開く
- [ ] prompt / answer / mood_before / mood_after が詳細表示される
- [ ] 閉じるボタンが動作する
- [ ] EmptyState / Loading / Error が表示される
- [ ] Pull to Refresh が動作する

## API接続チェック

### mobile env

- [ ] `EXPO_PUBLIC_API_BASE_URL` が development / production で切り替え可能
- [ ] local default が `http://localhost:8000/api` になっている
- [ ] production では Render の API URL を参照する
- [ ] trailing slash の有無でAPIが壊れない

### backend API

- [ ] `GET /api/concierge-threads/`
- [ ] `GET /api/concierge-threads/{id}/`
- [ ] `GET /api/reflections/`
- [ ] `POST /api/shrines/{id}/reflection/`
- [ ] `GET /api/visits/`
- [ ] `POST /api/shrines/{id}/visit/`
- [ ] `POST /api/concierge/chat/`
- [ ] `POST /api/shrine-interactions/`
- [ ] `POST /api/action-events/`

### APIエラー時の表示

- [ ] 401 / 403 時に画面が落ちない
- [ ] 404 時に案内表示が出る
- [ ] 500 時に Error 表示が出る
- [ ] ネットワークエラー時に再読み込みできる

## 認証チェック

- [ ] access token が保存される
- [ ] refresh token が保存される
- [ ] access token 期限切れ時に refresh される
- [ ] refresh 失敗時に未ログイン扱いになる
- [ ] ログイン切れで記録系APIが落ちない
- [ ] ログイン必須導線で案内表示が出る
- [ ] user ごとの相談履歴だけ取得される
- [ ] user ごとの振り返り履歴だけ取得される

## EAS移行前チェック

### Expo設定

- [ ] Expo アカウントを確認
- [ ] `app.json` または `app.config.ts` を確認
- [ ] アプリ名を確認
- [ ] icon / splash を確認
- [ ] iOS bundle identifier を設定
- [ ] Android package name を設定
- [ ] version / buildNumber / versionCode を整理

### EAS設定

- [ ] `eas.json` を作成
- [ ] preview profile を作成
- [ ] production profile を作成
- [ ] `EXPO_PUBLIC_API_BASE_URL` を build profile ごとに設定
- [ ] EAS Build preview を作成
- [ ] EAS Submit は内部テスト後に実施

### ストア前提

- [ ] TestFlight 用の内部テスト導線を決める
- [ ] Google Play 内部テスト導線を決める
- [ ] プライバシーポリシーURLを用意
- [ ] サポートURLを用意
- [ ] スクリーンショットを用意
- [ ] ストア説明文を用意
- [ ] 課金導線が未実装の場合、課金表現を出さない

## 実機UX確認

### iOS

- [ ] Home 表示
- [ ] Concierge 相談
- [ ] 神社詳細表示
- [ ] 参拝記録保存
- [ ] 振り返り保存
- [ ] 振り返り履歴確認
- [ ] 相談履歴確認
- [ ] Pull to Refresh
- [ ] Modal 表示
- [ ] 戻る導線

### Android

- [ ] Home 表示
- [ ] Concierge 相談
- [ ] 神社詳細表示
- [ ] 参拝記録保存
- [ ] 振り返り保存
- [ ] 振り返り履歴確認
- [ ] 相談履歴確認
- [ ] Pull to Refresh
- [ ] Modal 表示
- [ ] 戻る導線

## リスク

- 認証切れ時の挙動が未確認
- production API URL の設定が未確定
- 実機での表示崩れが未確認
- ストア申請に必要な文言・画像・URLが未整備
- 決済機能は最終フェーズのため、現時点では有料訴求を避ける必要がある

## 今回の完了条件

- [ ] 本監査ドキュメントが作成されている
- [ ] 本番移行前の未完了項目が一覧化されている
- [ ] EAS移行前に確認すべき項目が整理されている
- [ ] 主要導線の実機確認項目が整理されている

## 次PR候補

```markdown
- feature/mobile-release-flow-audit-fixes
- feature/mobile-auth-expired-state
- feature/mobile-production-env-config
- chore/expo-eas-preview-setup
```

## 進捗メモ

- MVP機能実装進捗: 75%
- 本番配布準備進捗: 15%
- 次の優先: 主要導線の実機確認
