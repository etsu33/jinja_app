// Mobile Shadow/Elevation Primitiveの正本 (docs/design/design-token.md Migration方針 5)。
// lib/tokens/*には対応する重複定義は存在しない。
// 2026-07時点で card / softCard / goldCta が app/index.tsx・app/concierge/index.tsx から
// 実際に参照されている。lightCard / skeleton は現時点でどこからも未参照。
// 2026-11-19: 明基調への切り替えに合わせて影を引き締めた。
// 旧値は暗基調向けで opacity 0.25〜0.28。近黒の地では見えなかったが、
// 生成りの地にそのまま出すと黒く濁る。明地では弱い影がよく効く。
export const shadows = {
  card: {
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  softCard: {
    shadowColor: "#000",
    shadowOpacity: 0.07,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 5 },
    elevation: 3,
  },
  // 主CTAの下に落とす色付きの影。shadowColor は呼び出し側が朱を渡す。
  goldCta: {
    shadowOpacity: 0.28,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 5 },
    elevation: 4,
  },
  lightCard: {
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
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
