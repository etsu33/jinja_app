export const radius = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  xxl: 22,
  cardLg: 24,
  pill: 999,
  circleSm: 25,
  circleMd: 27,
} as const;

// Design Token v1 定義基盤: Semantic Radius契約
// 正本: docs/design/design-token.md
// 既存の radius (上記) は変更せず、その値を再利用してSemantic層を構成する。
export const SEMANTIC_RADIUS_KEYS = ["control", "card", "panel", "modal", "image", "pill"] as const;

export type SemanticRadiusKey = (typeof SEMANTIC_RADIUS_KEYS)[number];
export type PlatformRadiusTheme = Record<SemanticRadiusKey, number>;

export const semanticRadius: PlatformRadiusTheme = {
  control: radius.md,
  card: radius.xl,
  panel: radius.lg,
  modal: radius.cardLg,
  image: radius.xs,
  pill: radius.pill,
};
