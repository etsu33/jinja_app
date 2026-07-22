// Mobile CTA/Button Component Sizeの正本 (docs/design/design-token.md Migration方針 5)。
// design-token.mdの5カテゴリには属さないComponent Token (Phase 6監査のButton優先領域)
// だが、shrines/[id].tsx・premium/index.tsx・components/ui/Button.tsx から参照される。
// lib/tokens/buttons.ts (buttonTokens) はキー構成が全く異なる別系統の未使用定義であり、
// 本ファイルの代替にはならない。
export const ctaSizes = {
  primaryHeight: 52,
  primaryRadius: 16,
  mediumHeight: 48,
  mediumRadius: 12,
  smallHeight: 44,
  smallRadius: 10,
  pillPaddingX: 12,
  pillPaddingY: 6,
  pillPaddingXSm: 10,
  pillPaddingYSm: 6,
  fabPaddingX: 8,
  fabPaddingY: 4,
  hitSlopSm: 8,
} as const;
