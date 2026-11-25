// Mobile Radius Primitiveの正本 (docs/design/design-token.md Migration方針 5)。
// 現行13画面以上・共通Component複数から実際に参照される。
// 注意: lib/tokens/radius.ts にも同名 `radius` exportが存在するが、
// 同じキー名 (sm/md/lg/xl) でも実値が異なり (例: md=16 vs 12, lg=18 vs 16, xl=20 vs 24)、
// 2026-07時点でアプリ内のどこからもimportされていない未使用の重複定義。
// 削除候補として記録するのみで、本PRでは削除・統合しない (design-token.mdの非対象)。
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

// docs/design/ios-ui-spec-v2.md 36節:
//   Selection Card 16〜20 / Photo Card 18〜20 / Modal 20〜24 / CTA 26〜28
export const semanticRadius: PlatformRadiusTheme = {
  control: radius.cardLg,
  card: radius.xl,
  panel: radius.lg,
  modal: radius.xxl,
  image: radius.lg,
  pill: radius.pill,
};
