// apps/web/src/features/concierge/buildHeroReasonV4Sections.ts
import type { RecommendationReasonV4Detail } from "@/lib/api/concierge";
import { buildRecommendationReasonDisplay } from "../../../../../packages/shared/recommendationReasonDisplay";
import { isExplanationOnlyFactSource, pickReasonV4Fact } from "./reasonV4FactPriority";

export type HeroReasonV4Sections = {
  // Ranking-related fact only (goriyaku/history_theme won the pick) -- feeds Conclusion,
  // same meaning/behavior as before PR5.
  factText: string | null;
  // Explanation-only Knowledge fact only (deity/shrine_history won the pick) --
  // Signal Authority正本§8: Rank/Eligibilityに一切寄与しないKnowledge fact。Conclusionへは
  // 混ぜず、呼び出し元で「参考情報」等の従属的な別枠として表示する
  // (docs/product/recommendation-result-information-architecture.md §13/§15 PR5、Finding 9)。
  explanationOnlyFactText: string | null;
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
 *
 * Explanation-only Knowledge fact(deity/shrine_history)は「構造化されたRecommendation
 * 理由」としては数えない -- hasStructuredの判定からexplanationOnlyFactTextを除外している。
 * これはPriorityの再決定ではなく(採用されるfactは従来どおりreasonV4FactPriority.tsの
 * deity > shrine_history > goriyaku > history_themeで決まる)、「Explanation-onlyの情報
 * だけでRecommendationが相談に意味的一致したかのように見せない」というFallback Contract
 * (今回のPR5要件、Signal Authority正本§7/§10)をFrontend表示層で守るための分岐。
 * Explanation-only factが唯一の構造化要素だった場合、hasStructured=falseとなり
 * fallbackText(Backend確定済みのlegacy reason文字列)が代わりにConclusionへ使われる。
 */
export function buildHeroReasonV4Sections(params: {
  detail?: RecommendationReasonV4Detail | null;
  recommendationReasonV4?: string | null;
  reason?: string | null;
}): HeroReasonV4Sections {
  const detail = params.detail ?? null;

  // 優先順位の実体はreasonV4FactPriority.tsに集約する(Hero/Shrine Detailで共通)。
  const pickedFact = detail ? pickReasonV4Fact(detail.fact) : null;
  const isPickedFactExplanationOnly = pickedFact ? isExplanationOnlyFactSource(pickedFact.source) : false;
  const factText = safeText(!isPickedFactExplanationOnly ? (pickedFact?.text ?? null) : null);
  const explanationOnlyFactText = safeText(isPickedFactExplanationOnly ? (pickedFact?.text ?? null) : null);
  const interpretationText = safeText(detail ? clean(detail.interpretation?.text) : null);
  const actionText = safeText(detail ? clean(detail.action?.text) : null);

  const hasStructured = Boolean(factText || interpretationText || actionText);

  const fallbackText = hasStructured
    ? null
    : safeText(pickFirst(detail?.reason_text, params.recommendationReasonV4, params.reason));

  return { factText, explanationOnlyFactText, interpretationText, actionText, hasStructured, fallbackText };
}
