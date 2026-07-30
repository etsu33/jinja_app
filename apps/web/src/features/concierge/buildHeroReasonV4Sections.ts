// apps/web/src/features/concierge/buildHeroReasonV4Sections.ts
import type { RecommendationReasonV4Detail } from "@/lib/api/concierge";
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import { pickReasonV4FactText } from "./reasonV4FactPriority";

export type HeroReasonV4Sections = {
  factText: string | null;
  interpretationText: string | null;
  actionText: string | null;
  hasStructured: boolean;
  fallbackText: string | null;
};

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const s = value.trim();
  return s.length ? s : null;
}

function pickFirst(...values: unknown[]): string | null {
  for (const v of values) {
    const s = clean(v);
    if (s) return s;
  }
  return null;
}

// 方位・断定表現の除外は既存のbuildRecommendationReasonDisplayに委譲する(Frontendで新規フィルタを作らない)
function safeText(value: string | null): string | null {
  if (!value) return null;
  return buildRecommendationReasonDisplay({ matchReason: null, reason: value, directionReference: null }).reason;
}

/**
 * Backendのrecommendation_reason_v4_detail(fact/interpretation/action)から
 * Hero Recommendation Card表示用の最小モデルを組み立てる。
 *
 * 優先順位:
 * 1. 構造化fact / interpretation / action
 * 2. recommendation_reason_v4_detail.reason_text
 * 3. recommendation_reason_v4(文字列)
 * 4. reason(旧文字列)
 *
 * 構造化セクションが1つ以上表示できる場合はfallbackTextを返さない(重複表示防止)。
 */
export function buildHeroReasonV4Sections(params: {
  detail?: RecommendationReasonV4Detail | null;
  recommendationReasonV4?: string | null;
  reason?: string | null;
}): HeroReasonV4Sections {
  const detail = params.detail ?? null;

  // 優先順位の実体はreasonV4FactPriority.tsに集約する(Hero/Shrine Detailで共通)。
  const factText = safeText(detail ? pickReasonV4FactText(detail.fact) : null);
  const interpretationText = safeText(detail ? clean(detail.interpretation?.text) : null);
  const actionText = safeText(detail ? clean(detail.action?.text) : null);

  const hasStructured = Boolean(factText || interpretationText || actionText);

  const fallbackText = hasStructured
    ? null
    : safeText(pickFirst(detail?.reason_text, params.recommendationReasonV4, params.reason));

  return { factText, interpretationText, actionText, hasStructured, fallbackText };
}
