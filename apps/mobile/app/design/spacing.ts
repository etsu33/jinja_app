// Mobile Spacing Primitiveの正本 (docs/design/design-token.md Migration方針 5)。
// 現行14画面以上・共通Component複数から実際に参照される。
// 注意: lib/tokens/spacing.ts にも同名 `spacing` exportが存在するが、
// キー構成・値ともに別系統 (xs/sm/md/lg/xl/xxl/xxxl の汎用数値スケール) で、
// 2026-07時点でアプリ内のどこからもimportされていない未使用の重複定義。
// 削除候補として記録するのみで、本PRでは削除・統合しない (design-token.mdの非対象)。
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
