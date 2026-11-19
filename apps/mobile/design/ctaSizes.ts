// Mobile CTA/Button Component Sizeの正本 (docs/design/design-token.md Migration方針 5)。
// design-token.mdの5カテゴリには属さないComponent Token (Phase 6監査のButton優先領域)
// だが、shrines/[id].tsx・premium/index.tsx・components/ui/Button.tsx から参照される。
// lib/tokens/buttons.ts (buttonTokens) はキー構成が全く異なる別系統の未使用定義であり、
// 本ファイルの代替にはならない。
// Radius は docs/design/ios-ui-spec-v2.md 19節・36節に合わせる。
// Primary CTA は 26〜28px の丸み。旧値(16/12/10)は角が立ちすぎていた。
export const ctaSizes = {
  primaryHeight: 54,
  primaryRadius: 27,
  mediumHeight: 48,
  mediumRadius: 24,
  smallHeight: 44,
  smallRadius: 22,
  pillPaddingX: 12,
  pillPaddingY: 6,
  pillPaddingXSm: 10,
  pillPaddingYSm: 6,
  fabPaddingX: 8,
  fabPaddingY: 4,
  hitSlopSm: 8,
} as const;
