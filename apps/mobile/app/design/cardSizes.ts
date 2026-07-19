// Mobile Card Component Sizeの正本 (docs/design/design-token.md Migration方針 5)。
// design-token.mdの5カテゴリ(Color/Typography/Spacing/Radius/Shadow)には属さない
// Component Token (Phase 6監査のCard優先領域) だが、現行13画面以上から実際に
// 参照される。lib/tokens/cards.ts (cardTokens) はキー構成が全く異なる別系統の
// 未使用定義であり、本ファイルの代替にはならない。
export const cardSizes = {
  borderWidth: 1,
  carouselWidth: 220,
  carouselWidthLg: 256,
  imageSm: 64,
  cardPaddingSm: 12,
  cardPaddingMd: 14,
  cardPaddingLg: 18,
  rankBadgeSize: 32,
  skeletonWidth: 160,
  skeletonRadius: 14,
  shimmerRadius: 8,
} as const;
