# Mobile Journey Timeline Device Check

## 1. Goal

## 2. Test Environment

## 3. Checklist

- [ ] 記録 → ご縁の歩み 導線確認
- [ ] 未ログイン時の表示確認
- [ ] ログイン済み・イベント0件のEmpty確認
- [ ] 相談後に consultation_created が表示されるか確認
- [ ] 提案後に recommendation_shown が表示されるか確認
- [ ] 参拝記録後に visit_completed が表示されるか確認
- [ ] 振り返り保存後に reflection_created が表示されるか確認
- [ ] Pull to refresh 確認
- [ ] 実機表示崩れ確認

## 4. Findings

## 5. Fix Candidates

## 6. Decision

# Mobile Journey Timeline Device Check

## 1. Goal

Journey Timeline の mobile 実機確認結果を記録する。

今回の確認対象は、`記録 → ご縁の歩み` の導線と、`GET /api/journeys/timeline/` から返る JourneyEvent が mobile 画面上で意図通り表示されるかどうかに限定する。

この audit では修正作業は行わない。発見した詰まりは Findings に記録し、修正が必要な場合は別 feature ブランチへ切り出す。

## 2. Test Environment

- Branch: `audit/mobile-journey-timeline-device-check`
- App: `apps/mobile`
- API endpoint: `GET /api/journeys/timeline/`
- Device:
  - [ ] iOS Simulator
  - [ ] Android Emulator
  - [ ] Physical iPhone
  - [ ] Physical Android
- Auth state:
  - [ ] 未ログイン
  - [ ] ログイン済み
- Backend:
  - [ ] Local backend
  - [ ] Staging / Preview backend
  - [ ] Production backend

## 3. Checklist

### Navigation

- [ ] 記録 → ご縁の歩み 導線確認
- [ ] ご縁の歩み → 記録へ戻る 導線確認

### Auth / State UI

- [ ] 未ログイン時の表示確認
- [ ] ログイン済み・イベント0件の Empty 確認
- [ ] Loading UI 確認
- [ ] Error UI 確認

### JourneyEvent Display

- [ ] 相談後に `consultation_created` が表示されるか確認
- [ ] 提案後に `recommendation_shown` が表示されるか確認
- [ ] 参拝記録後に `visit_completed` が表示されるか確認
- [ ] 振り返り保存後に `reflection_created` が表示されるか確認

### Timeline Behavior

- [ ] 日付グループが表示されるか確認
- [ ] `occurred_at` 降順で表示されるか確認
- [ ] EventCard の表示崩れがないか確認
- [ ] Pull to refresh 確認

### Visual Check

- [ ] ヘッダー文言が自然か確認
- [ ] StateCard の余白・色が既存画面と揃っているか確認
- [ ] EventCard の余白・文字サイズが過密でないか確認
- [ ] 実機表示崩れ確認

## 4. Findings

### Finding 1

- Status: `未確認`
- Screen:
- Condition:
- Expected:
- Actual:
- Severity: `low | medium | high`
- Notes:

## 5. Fix Candidates

### Candidate 1

- Target:
- Fix type: `docs | mobile | backend | design`
- Branch candidate:
- Notes:

## 6. Decision

- [ ] このまま次フェーズへ進む
- [ ] 軽微な mobile 修正を別 feature ブランチで行う
- [ ] backend 側の修正を別 feature ブランチで行う
- [ ] Journey Timeline UI の追加設計を docs 化する

## 7. Next Step

実機確認後、問題がなければ Journey Timeline は Phase1 完了とする。

修正が必要な場合は、この audit ブランチでは修正せず、Finding ごとに別 feature ブランチへ切り出す。
