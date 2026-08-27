// apps/web/src/features/compass/resolveCompassSupplementaryFactText.ts
//
// Fills ShrineCardCompact's existing `explanationOnlyFactText` slot for
// Compass. Pure presentation-layer composition ONLY -- this module never
// scores, matches, or decides candidates; it only reads two signals ALREADY
// produced by the shared ranking path (backend/temples/services/
// concierge_chat_ranking.py, the same functions Concierge uses) and already
// present on the raw recommendation dict Compass's response returns:
//
//   - reason_facts[].type === "history_theme": a Derived Meaning (KAMI
//     MUSUBI's own interpretation of the shrine's history theme), only
//     present when it actually boosted this candidate's rank
//     (resolve_history_theme_candidate_boost() > 0 -- see
//     concierge_chat_ranking._build_reason_facts). Never presented as an
//     official Fact.
//   - breakdown.matched_need_tags: whether the requested purpose itself
//     matched this specific candidate (GID/text evidence). When it did not,
//     ShrineCardCompact's existing `reason` text alone can read like an
//     unexplained pick (Direction + Distance only) -- this names the actual
//     reason (Filter Context) instead of implying a purpose match that
//     Ranking never made.
//
// Returns null when neither signal is available -- never a placeholder, and
// never fabricates a purpose match `purpose` param is unknown (undefined),
// so every existing caller that does not pass `purpose` renders unchanged.
import type { CompassRecommendation } from "./types";

function findHistoryThemeLabel(rec: CompassRecommendation): string | null {
  const facts = Array.isArray(rec.reason_facts) ? rec.reason_facts : [];
  for (const fact of facts) {
    if (fact && typeof fact === "object" && fact.type === "history_theme") {
      const label = typeof fact.label === "string" ? fact.label.trim() : "";
      if (label) return label;
    }
  }
  return null;
}

function isPurposeMatched(rec: CompassRecommendation, purpose: string): boolean {
  const matched = rec.breakdown && Array.isArray(rec.breakdown.matched_need_tags) ? rec.breakdown.matched_need_tags : [];
  return matched.includes(purpose);
}

export function resolveCompassSupplementaryFactText(
  rec: CompassRecommendation,
  purpose: string | null | undefined,
): string | null {
  const historyThemeLabel = findHistoryThemeLabel(rec);
  if (historyThemeLabel) {
    return `${historyThemeLabel}という文脈（KAMI MUSUBIの解釈）`;
  }

  if (purpose && !isPurposeMatched(rec, purpose)) {
    return "今回の方向・距離の条件に合う候補です";
  }

  return null;
}
