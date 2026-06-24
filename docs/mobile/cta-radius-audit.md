# CTA Radius Audit

## 対象

- apps/mobile/app/design/ctaSizes.ts
- apps/mobile/app/design/radius.ts

## 利用箇所

### ctaSizes.primaryRadius

- apps/mobile/app/shrines/[id].tsx

用途:
- 詳細画面の主要CTA

判断:
- CTA専用の角丸として維持

### ctaSizes.mediumRadius

- apps/mobile/components/ui/Button.tsx

用途:
- 共通Buttonコンポーネント

判断:
- Button専用の角丸として維持

### ctaSizes.smallRadius

- apps/mobile/components/home/MyPageCard.tsx

用途:
- 小型CTA

判断:
- 小型CTA専用の角丸として維持

## radius.ts との関係

radius.ts:
- 汎用的な角丸の正本
- card / pill / circle など画面共通の形状に使う

ctaSizes.ts:
- CTAの高さ
- CTAの角丸
- CTAのpadding
- hitSlop

## 結論

現時点では ctaSizes の radius 系は削除しない。

理由:
- CTAの角丸は高さ・paddingとセットで調整される
- radius.ts に寄せると、CTA専用設計の意味が薄れる
- 利用箇所が少なく、責務が明確

## 今後

CTAの見た目を全体統一するフェーズで、必要なら再検討する。
