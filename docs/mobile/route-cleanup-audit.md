# Mobile Route Cleanup Audit

## 現在の app 構成

- app/_layout.tsx
- app/index.tsx
- app/concierge/index.tsx
- app/favorites/index.tsx
- app/goshuin/index.tsx
- app/goshuin/upload.tsx
- app/mypage/index.tsx
- app/profile/index.tsx
- app/ranking/index.tsx
- app/records/index.tsx
- app/search/index.tsx
- app/shrines/[id].tsx
- app/shrines/storage.ts
- app/design/*
- app/theme.ts

## 監査結果

- apps/mobile/app を Expo Router の正本として整理済み
- apps/mobile/src/app は削除済み
- app/design は spacing / cardSizes / ctaSizes の正本
- app/theme.ts は mobile UI theme の正本
- records / ranking / mypage / favorites は app 配下画面として維持

## 要見直し

### app/shrines/storage.ts

責務:
- 画面ではない
- local storage の favorite / recent を SHRINES と結合する表示用 helper

現在の参照:
- app/records/index.tsx
- app/favorites/index.tsx

課題:
- app 配下にあるため Expo Router のルート候補になりうる
- 現在は app/_layout.tsx で hidden 登録している
- 本来は lib 側へ移す方が自然

## 次PR候補

### chore/mobile-shrine-storage-helper-migration

- [ ] apps/mobile/lib/shrineStorage.ts を作成
- [ ] app/shrines/storage.ts の内容を移設
- [ ] app/records/index.tsx の import を修正
- [ ] app/favorites/index.tsx の import を修正
- [ ] app/_layout.tsx から shrines/storage hidden 設定を削除
- [ ] app/shrines/storage.ts を削除
- [ ] typecheck
- [ ] 実機確認
