// apps/web/src/lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts
//
// PremiumMeaningContext Existing API Mapping (PR-B).
//
// Fail-safe mapping from the existing, stable Concierge Response shape
// (ConciergeRecommendation / ConciergeNeed, as already typed in
// @/lib/api/concierge) into a PremiumMeaningContext (see
// ./premiumMeaningContext.ts). This module reads already-typed Frontend
// Client fields only -- it does not touch raw/untyped response JSON, does
// not read the `_debug` envelope, and never throws on missing or empty
// input.
//
// Explicitly NOT in scope here (PR-C+):
// - Deep Recommendation Reason / Personal Meaning / Action Meaning
//   generation.
// - Any Relevance judgment (`relevantToConsultation` / `relevantToVisit`)
//   -- both are fixed to null by this mapping; no logic infers Relevance
//   from Shrine Evidence presence, and none exists anywhere else in the
//   codebase to source from (see the Backend Readiness Gap Audit).
// - `interpretedContext` -- fixed to null. The only candidate source,
//   `interpret_consultation()` / InterpretationProfile, reaches the API
//   response solely under the `_debug` envelope (stripped by default,
//   only conditionally re-added), which is not a stable Contract field.
//   This mapping intentionally does not read `_debug` for this or any
//   other field.

import type { ConciergeNeed, ConciergeReasonFact, ConciergeRecommendation } from "@/lib/api/concierge";
import type { PremiumMeaningContext, PremiumMeaningReasonFact } from "./premiumMeaningContext";
import { computePremiumMeaningValidity } from "./premiumMeaningContext";

export type MapConciergeResponseParams = {
  rec?: ConciergeRecommendation | null;
  need?: ConciergeNeed | null;
  mode?: string | null;
};

function clean(value?: string | null): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function resolveShrineId(rec?: ConciergeRecommendation | null): number | null {
  if (!rec) return null;
  const candidates = [rec.shrine_id, rec.id];
  for (const candidate of candidates) {
    if (typeof candidate === "number" && Number.isFinite(candidate)) return candidate;
  }
  return null;
}

function toReasonFact(fact: ConciergeReasonFact | null | undefined): PremiumMeaningReasonFact | null {
  const type = clean(fact?.type);
  const label = clean(fact?.label);
  if (!type || !label) return null;
  const evidence = Array.isArray(fact?.evidence) ? fact.evidence.filter((item): item is string => typeof item === "string") : [];
  return { type, label, evidence };
}

function mapConsultation(need: ConciergeNeed | null | undefined, mode: string | null | undefined): PremiumMeaningContext["consultation"] {
  const tags = Array.isArray(need?.tags) ? need.tags.map(clean).filter((tag): tag is string => Boolean(tag)) : [];

  return {
    primaryNeed: tags[0] ?? null,
    secondaryNeed: tags[1] ?? null,
    mode: clean(mode ?? undefined),
    // Fixed per PR-B scope: the only candidate source (interpret_consultation()
    // / InterpretationProfile) is debug-only, not a stable Contract field.
    interpretedContext: null,
  };
}

function mapRecommendationEvidence(
  reasonFacts: ConciergeRecommendation["reason_facts"],
): PremiumMeaningContext["recommendationEvidence"] {
  const facts = Array.isArray(reasonFacts) ? reasonFacts : [];

  const primaryRaw = facts.find((fact) => fact?.is_primary === true) ?? null;
  const primaryReasonFact = toReasonFact(primaryRaw);

  const secondaryReasonFacts = facts
    .filter((fact) => fact !== primaryRaw)
    .map((fact) => toReasonFact(fact))
    .filter((fact): fact is PremiumMeaningReasonFact => fact !== null);

  return { primaryReasonFact, secondaryReasonFacts };
}

function mapShrineEvidence(shrineId: number, rec: ConciergeRecommendation): PremiumMeaningContext["shrineEvidence"] {
  const fact = rec.recommendation_reason_v4_detail?.fact ?? null;
  const trustMetadata = rec.trust_metadata ?? null;

  const goriyakuLabel = clean(fact?.goriyaku ?? null);

  return {
    shrineId,
    deity: clean(fact?.deity ?? null),
    history: clean(fact?.shrine_history ?? null),
    historyTheme: clean(fact?.history_theme ?? null),
    placeContext: clean(fact?.place_context ?? null),
    goriyaku: goriyakuLabel ? [goriyakuLabel] : null,
    originSummary: clean(trustMetadata?.origin_summary ?? null),
    culturalStatus: Array.isArray(trustMetadata?.cultural_status) ? trustMetadata.cultural_status : null,
    lineage: clean(trustMetadata?.lineage ?? null),
    // No stable Concierge Response field exposes tradition or per-source
    // verification metadata individually (Source of Truth unconfirmed,
    // see Backend Readiness Gap Audit) -- not sourced in PR-B.
    tradition: null,
    verificationMetadata: null,
    // Fixed per PR-B scope: no Relevance judgment logic exists to source
    // from, and Relevance must never be inferred from Evidence presence.
    relevantToConsultation: null,
    relevantToVisit: null,
  };
}

/**
 * Maps the existing, stable Concierge Response shape into a
 * PremiumMeaningContext. Never throws: missing/empty `rec`, `need`, or
 * `mode` all resolve to null-filled fields rather than an exception. When
 * no shrineId can be resolved (no `rec`, or `rec` without `shrine_id`/`id`),
 * there is nothing to attach Evidence to, so this returns `null` rather
 * than fabricate a Context.
 *
 * `personalization` is intentionally left empty ({}): none of its fields
 * (birthdate / astroElement / profileContext / direction) are part of this
 * PR-B's scope (_need/mode, reason_facts, recommendation_reason_v4_detail,
 * trust_metadata only) -- populating them is deferred, not invented here.
 */
export function mapConciergeResponseToPremiumMeaningContext(
  params: MapConciergeResponseParams,
): PremiumMeaningContext | null {
  const rec = params.rec ?? null;
  const shrineId = resolveShrineId(rec);
  if (shrineId === null || !rec) return null;

  const consultation = mapConsultation(params.need, params.mode);
  const recommendationEvidence = mapRecommendationEvidence(rec.reason_facts);
  const shrineEvidence = mapShrineEvidence(shrineId, rec);

  const validity = computePremiumMeaningValidity({ consultation, recommendationEvidence, shrineEvidence });

  return {
    shrineId,
    consultation,
    recommendationEvidence,
    shrineEvidence,
    personalization: {},
    validity,
  };
}
