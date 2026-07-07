

# Mobile Concierge Auth / Condition Flow Audit

## 1. Goal

Mobile の Concierge 画面における、未ログイン相談後の認証導線と、条件追加UIの payload 反映状況を確認する。

今回の audit では実装修正は行わない。発見した詰まりは Findings に記録し、修正が必要な場合は別 feature ブランチへ切り出す。

## 2. Background

Journey Timeline は `GET /api/journeys/timeline/` を認証必須APIとして実装済み。

一方で、Mobile の Concierge は未ログインでも相談できるため、以下の断絶が発生する可能性がある。

```txt
未ログイン相談
↓
神社提案は表示される
↓
参拝記録 / 保存 / ご縁の歩み は認証必須
↓
しかしログイン導線が出ない場合、ユーザーが詰まる
```

また、条件追加UIは画面上に存在するが、入力内容が chat payload や backend の推薦条件に反映されているかは未確認。

## 3. Scope

### 対象

- Mobile Concierge 画面
- 未ログイン相談後の導線
- 記録 / 参拝 / 保存前のログイン誘導
- 条件追加UI
- chat payload
- backend log 上の条件反映

### 対象外

- backend API の仕様変更
- Journey Timeline API の変更
- 課金導線の変更
- UIデザインの大幅変更
- 条件推薦ロジックの調整

## 4. Test Environment

- Branch: `audit/mobile-concierge-auth-condition-flow`
- App: `apps/mobile`
- API base:
  - [ ] Local backend
  - [ ] Staging / Preview backend
  - [ ] Production backend
- Device:
  - [ ] iOS Simulator
  - [ ] Android Emulator
  - [ ] Physical iPhone
  - [ ] Physical Android
- Auth state:
  - [ ] 未ログイン
  - [ ] ログイン済み

## 5. Checklist

### Auth Flow

- [ ] 未ログイン状態で Concierge 画面を開ける
- [ ] 未ログイン状態で相談を送信できる
- [ ] 未ログイン相談後に神社提案が表示される
- [ ] 未ログイン相談後にログイン導線が表示されるか確認
- [ ] 神社詳細へ遷移できるか確認
- [ ] 神社詳細で保存操作前にログイン導線が出るか確認
- [ ] 神社詳細で参拝記録前にログイン導線が出るか確認
- [ ] ご縁の歩みを開いたとき、未ログイン時の表示が自然か確認
- [ ] 未ログイン時の 401 がユーザーに不自然な Error として見えないか確認

### Logged-in Flow

- [ ] ログイン済み状態で Concierge 画面を開ける
- [ ] ログイン済み状態で相談を送信できる
- [ ] ログイン済み相談が user に紐づくか確認
- [ ] Journey Timeline に `consultation_created` が出るか確認
- [ ] Journey Timeline に `recommendation_shown` が出るか確認
- [ ] 参拝記録後に `visit_completed` が出るか確認
- [ ] 振り返り保存後に `reflection_created` が出るか確認

### Condition UI

- [ ] 「条件を追加」を開ける
- [ ] 条件UIの入力項目を確認する
- [ ] 相談テーマ選択と条件UIの関係を確認する
- [ ] 条件を入力後、画面上で保持されるか確認する
- [ ] 条件を閉じても入力値が消えないか確認する
- [ ] 条件を変更した状態で相談送信できるか確認する

### Chat Payload

- [ ] 条件追加内容が chat request payload に入るか確認
- [ ] `profile_context` が送信されるか確認
- [ ] `birthdate` が送信されるか確認
- [ ] `gender` または同等の属性が送信されるか確認
- [ ] `goriyaku_tag_ids` が送信されるか確認
- [ ] `visit_style_tags` が送信されるか確認
- [ ] `extra_condition` / `raw_extra` 相当が送信されるか確認

### Backend Log

- [ ] backend log で `profile_context received=Y` になるか確認
- [ ] backend log で `user_profile=Y` になるか確認
- [ ] backend log で `derived_profile=Y` になるか確認
- [ ] backend log で `has_extra=True` になるか確認
- [ ] backend log で `raw_extra` が入るか確認
- [ ] backend log で `visit_style` が反映されるか確認
- [ ] backend log で `goriyaku_tag_ids` が反映されるか確認

## 6. Expected Behavior

### 未ログイン

- 相談と神社提案までは可能
- 保存 / 参拝記録 / ご縁の歩みはログインが必要
- 認証必須操作では、ただの Error ではなくログイン導線を表示する

### ログイン済み

- 相談が user に紐づく
- Journey Timeline に相談・提案・参拝・振り返りが表示される
- 条件追加内容が推薦条件として反映される

## 7. Findings

### Finding 1

- Status: `未確認`
- Screen:
- Auth state: `anonymous | logged-in`
- Condition:
- Expected:
- Actual:
- Severity: `low | medium | high`
- Notes:

### Finding 2

- Status: `未確認`
- Screen:
- Auth state: `anonymous | logged-in`
- Condition:
- Expected:
- Actual:
- Severity: `low | medium | high`
- Notes:

## 8. Fix Candidates

### Candidate A: 未ログイン時ログイン導線追加

- Target:
  - `apps/mobile/app/concierge/index.tsx`
  - `apps/mobile/app/journey/index.tsx`
  - `apps/mobile/app/shrines/[id].tsx`
- Fix type: `mobile`
- Branch candidate: `feature/mobile-concierge-auth-prompt`
- Notes:
  - 401 を単なる Error として見せず、ログイン誘導に変換する
  - 保存 / 参拝 / ご縁の歩みの前にログイン導線を出す

### Candidate B: 条件追加 payload 接続

- Target:
  - `apps/mobile/app/concierge/index.tsx`
  - `apps/mobile/lib/conciergeContext.ts`
- Fix type: `mobile`
- Branch candidate: `feature/mobile-concierge-condition-payload`
- Notes:
  - 条件UI state を chat payload に接続する
  - backend log で反映確認する

### Candidate C: Journey Timeline 未ログイン表示改善

- Target:
  - `apps/mobile/app/journey/index.tsx`
- Fix type: `mobile`
- Branch candidate: `feature/mobile-journey-auth-state-ui`
- Notes:
  - 認証切れ / 未ログイン時は Error ではなくログイン導線を表示する

## 9. Decision

- [ ] 修正なしで次フェーズへ進む
- [ ] auth 導線を先に修正する
- [ ] 条件 payload を先に修正する
- [ ] auth 導線と条件 payload を別 feature ブランチに分ける

## 10. Next Step

監査後、修正が必要な場合は以下の順で分ける。

```markdown
1. `feature/mobile-concierge-auth-prompt`
2. `feature/mobile-concierge-condition-payload`
3. `feature/mobile-journey-auth-state-ui`
```

同一PRで auth / condition / Journey 表示改善をまとめない。
