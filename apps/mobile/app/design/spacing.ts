export const spacing = {
  screenX: 16,
  screenXWide: 24,
  contentX: 20,
  sectionY: 12,
  sectionTop: 20,
  sectionTopSm: 16,
  bottomSpace: 40,
  bottomSpaceLg: 48,
  tightGap: 4,
  inlineGap: 7,
  smGap: 8,
  mdGap: 10,
  lgGap: 12,
  xlGap: 16,
} as const;

// Design Token v1 定義基盤: Semantic Spacing契約
// 正本: docs/design/design-token.md
// 既存の spacing (上記) は変更せず、その値を再利用してSemantic層を構成する。
export const SEMANTIC_SPACING_KEYS = [
  "pageX",
  "sectionY",
  "card",
  "controlX",
  "controlY",
  "inlineGap",
  "stackGap",
] as const;

export type SemanticSpacingKey = (typeof SEMANTIC_SPACING_KEYS)[number];
export type PlatformSpacingTheme = Record<SemanticSpacingKey, number>;

export const semanticSpacing: PlatformSpacingTheme = {
  pageX: spacing.screenX,
  sectionY: spacing.sectionTop,
  card: spacing.lgGap,
  controlX: spacing.mdGap,
  controlY: spacing.smGap,
  inlineGap: spacing.inlineGap,
  stackGap: spacing.tightGap,
};
