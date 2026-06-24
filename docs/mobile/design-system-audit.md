# Mobile Design System Audit

## 現在の token 構成

- apps/mobile/app/design/spacing.ts
- apps/mobile/app/design/cardSizes.ts
- apps/mobile/app/design/ctaSizes.ts
- apps/mobile/app/design/shadow.ts
- apps/mobile/app/design/radius.ts
- apps/mobile/app/theme.ts

## 責務整理

### spacing.ts

責務:
- 画面横余白
- セクション余白
- 要素間 gap
- bottom spacing

維持:
- screenX / screenXWide / contentX
- sectionY / sectionTop / sectionTopSm
- tightGap / inlineGap / smGap / mdGap / lgGap / xlGap

### cardSizes.ts

責務:
- カード幅
- 画像サイズ
- カード padding
- ranking / skeleton などカード系サイズ

課題:
- radius 系が含まれている
- borderWidth が含まれている

今後:
- radius 系は radius.ts に寄せる
- borderWidth は現状 cardSizes.borderWidth を継続利用
- 必要になったら border.ts を検討

### ctaSizes.ts

責務:
- CTA高さ
- CTA角丸
- pill padding
- fab padding
- hitSlop

課題:
- CTA角丸は radius.ts と重複する可能性あり

今後:
- まずは現状維持
- 将来 ctaSizes の radius は radius.ts 参照へ寄せる候補

### shadow.ts

責務:
- card shadow
- softCard shadow
- goldCta shadow
- lightCard shadow
- skeleton elevation

維持:
- shadow定義の正本として継続

### radius.ts

責務:
- 角丸値の正本
- pill / circle / card radius の共通化

今後:
- cardSizes 内の radius 系を段階的に移行
- ctaSizes 内の radius 系も段階的に移行

### theme.ts

責務:
- light系 colors
- dark theme colors
- semantic color

維持:
- colors: light / home / common 用
- kamimusubiDark: dark UI 用

課題:
- colors.text と colors.textDark が同じ値
- colors.primary と colors.favorite が同じ値
- ただし意味が違うため、現状は許容

## 次PR候補

### chore/mobile-card-radius-cleanup

- [ ] cardSizes.radiusSm を radius.xs へ置換
- [ ] cardSizes.radiusMd を radius.md へ置換
- [ ] cardSizes.radiusLg を radius.xl へ置換
- [ ] cardSizes.pillRadius を radius.pill へ置換
- [ ] cardSizes.imageRadius を radius.xs へ置換
- [ ] skeletonRadius / shimmerRadius の扱いを判断

### chore/mobile-cta-radius-cleanup

- [ ] ctaSizes.primaryRadius を radius.md へ寄せるか判断
- [ ] ctaSizes.mediumRadius を radius.xs へ寄せるか判断
- [ ] ctaSizes.smallRadius の扱いを判断

## 方針

- tokenを増やすより、既存tokenの責務を明確化する
- radius.ts を角丸の正本にする
- cardSizes.ts はカード固有サイズに寄せる
- ctaSizes.ts はCTA固有サイズに寄せる
- theme.ts は色の正本として維持
