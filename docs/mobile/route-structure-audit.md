# Mobile Route Structure Audit

## 方針

- apps/mobile/app を Expo Router の正本候補とする
- apps/mobile/src/app は削除せず、移設候補として扱う
- 今回の監査PRでは削除・移設はしない

## app 側に存在する画面

- app/index.tsx
- app/concierge/index.tsx
- app/favorites/index.tsx
- app/mypage/index.tsx
- app/ranking/index.tsx
- app/records/index.tsx
- app/_layout.tsx

## src/app 側にしかない重要画面

- src/app/index.tsx
- src/app/concierge/index.tsx
- src/app/shrines/[id].tsx
- src/app/goshuin/index.tsx
- src/app/goshuin/upload.tsx
- src/app/search/index.tsx
- src/app/profile/index.tsx

## 移設必須候補

- src/app/index.tsx → app/index.tsx
- src/app/concierge/index.tsx → app/concierge/index.tsx
- src/app/shrines/[id].tsx → app/shrines/[id].tsx

## 移設候補

- src/app/goshuin/index.tsx → app/goshuin/index.tsx
- src/app/goshuin/upload.tsx → app/goshuin/upload.tsx
- src/app/search/index.tsx → app/search/index.tsx
- src/app/profile/index.tsx → app/profile/index.tsx

## 削除保留

- apps/mobile/src/app
- 理由: 現役実装が残っているため

## 次PR候補

- app 側へ画面移設
- _layout.tsx の正本整理
- src/app 削除判断

## 整理の優先順位

1. app を正本にする
2. src/app にしかない現役画面を app 側へ移設する
3. 重複している app / src/app の画面差分を統合する
4. app 側で動作確認する
5. src/app は最後に削除判断する

## 移設順序

### Phase 1: 主要導線

- src/app/index.tsx → app/index.tsx
- src/app/concierge/index.tsx → app/concierge/index.tsx
- src/app/shrines/[id].tsx → app/shrines/[id].tsx

### Phase 2: 記録・プロフィール系

- src/app/goshuin/index.tsx → app/goshuin/index.tsx
- src/app/goshuin/upload.tsx → app/goshuin/upload.tsx
- src/app/profile/index.tsx → app/profile/index.tsx

### Phase 3: 探索系

- src/app/search/index.tsx → app/search/index.tsx

### Phase 4: 重複・削除判断

- src/app/_layout.tsx の差分確認
- src/app/favorites/page.tsx と app/favorites/index.tsx の差分確認
- src/app 削除可否を判断

## 作業ルール

- 1PRで移設する画面は最大3画面まで
- src/app は移設完了まで削除しない
- 既存の app/design と app/theme.ts を正本として参照する
- import path は移設後に必ず確認する
- 画面移設後は該当ルートを実機確認する

## 次に作るブランチ候補

- chore/mobile-route-main-screens-migration

## 次PR TODO

- [ ] develop 最新化
- [ ] chore/mobile-route-main-screens-migration 作成
- [ ] app/index.tsx を src/app/index.tsx の実装で置き換える
- [ ] app/concierge/index.tsx を src/app/concierge/index.tsx の実装で置き換える
- [ ] app/shrines/[id].tsx を作成する
- [ ] import path を app 配下基準に修正する
- [ ] app/_layout.tsx の表示タブと移設画面の整合を確認する
- [ ] typecheck
- [ ] 実機確認
