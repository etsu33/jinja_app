export const shadows = {
  card: {
    shadowColor: "#000",
    shadowOpacity: 0.28,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 7 },
    elevation: 4,
  },
  softCard: {
    shadowColor: "#000",
    shadowOpacity: 0.25,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 3,
  },
  goldCta: {
    shadowOpacity: 0.25,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  lightCard: {
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 3,
  },
  skeleton: {
    elevation: 2,
  },
} as const;

// Design Token v1 定義基盤: Semantic Shadow/Elevation契約
// 正本: docs/design/design-token.md
// 既存の shadows (上記) は変更せず、その値を再利用してSemantic層を構成する。
export const SEMANTIC_SHADOW_KEYS = ["none", "low", "medium", "high", "brand"] as const;

export type SemanticShadowKey = (typeof SEMANTIC_SHADOW_KEYS)[number];

export type ShadowStyle = {
  shadowColor?: string;
  shadowOpacity?: number;
  shadowRadius?: number;
  shadowOffset?: { width: number; height: number };
  elevation: number;
};

export type PlatformShadowTheme = Record<SemanticShadowKey, ShadowStyle>;

export const semanticShadow: PlatformShadowTheme = {
  none: { elevation: 0 },
  low: shadows.lightCard,
  medium: shadows.softCard,
  high: shadows.card,
  brand: shadows.goldCta,
};
