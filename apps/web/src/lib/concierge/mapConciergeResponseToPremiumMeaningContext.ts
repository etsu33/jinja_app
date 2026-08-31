// apps/web/src/lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts
//
// PremiumMeaningContext Existing API Mapping (PR-B, updated PR-C).
//
// Fail-safe mapping from the existing, stable Concierge Response shape
// (ConciergeRecommendation / ConciergeNeed / ConsultationMeaning, as
// already typed in @/lib/api/concierge) into a PremiumMeaningContext (see
// ./premiumMeaningContext.ts). This module reads already-typed Frontend
// Client fields only -- it does not touch raw/untyped response JSON, does
// not read the `_debug` envelope, and never throws on missing or empty
// input.
//
// PR-C update: `consultation_meaning` (the stable API field produced by
// `consultation_meaning.py`, never `_debug`) is now mapped into
// situationSignals / desiredOutcomeSignals / explicitConstraintSignals,
// replacing the PR-B hardcoded-null `interpretedContext` placeholder.
//
// Explicitly NOT in scope here (PR-D+):
// - Deep Recommendation Reason / Personal Meaning / Action Meaning
//   generation.
// - Any Relevance judgment (`relevantToConsultation` / `relevantToVisit`)
//   -- both are fixed to null by this mapping; no logic infers Relevance
//   from Shrine Evidence presence, and none exists anywhere else in the
//   codebase to source from (see the Backend Readiness Gap Audit).

import type {
  ConciergeNeed,
  ConciergeReasonFact,
  ConciergeRecommendation,
  ConsultationMeaning,
} from "@/lib/api/concierge";
import type {
  DesiredOutcomeSignal,
  ExplicitConstraintSignal,
  PremiumMeaningContext,
  PremiumMeaningReasonFact,
  SituationSignal,
} from "./premiumMeaningContext";
import { computePremiumMeaningValidity } from "./premiumMeaningContext";

export type MapConciergeResponseParams = {
  rec?: ConciergeRecommendation | null;
  need?: ConciergeNeed | null;
  mode?: string | null;
  consultationMeaning?: ConsultationMeaning | null;
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

function mapSituationSignals(consultationMeaning?: ConsultationMeaning | null): SituationSignal[] {
  const raw = consultationMeaning?.situation_signals;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((s) => typeof s?.type === "string")
    .map((s) => ({
      type: s.type,
      evidence: Array.isArray(s.evidence)
        ? s.evidence.filter((e) => typeof e?.text === "string").map((e) => ({ text: e.text }))
        : [],
    }));
}

function mapDesiredOutcomeSignals(consultationMeaning?: ConsultationMeaning | null): DesiredOutcomeSignal[] {
  const raw = consultationMeaning?.desired_outcome_signals;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((s) => typeof s?.type === "string")
    .map((s) => ({
      type: s.type,
      evidence: Array.isArray(s.evidence)
        ? s.evidence.filter((e) => typeof e?.text === "string").map((e) => ({ text: e.text }))
        : [],
    }));
}

function mapExplicitConstraintSignals(consultationMeaning?: ConsultationMeaning | null): ExplicitConstraintSignal[] {
  const raw = consultationMeaning?.explicit_constraint_signals;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((s) => typeof s?.type === "string")
    .map((s) => ({
      type: s.type,
      evidence: Array.isArray(s.evidence)
        ? s.evidence.filter((e) => typeof e?.text === "string").map((e) => ({ text: e.text }))
        : [],
    }));
}

function mapConsultation(
  need: ConciergeNeed | null | undefined,
  mode: string | null | undefined,
  consultationMeaning: ConsultationMeaning | null | undefined,
): PremiumMeaningContext["consultation"] {
  const tags = Array.isArray(need?.tags) ? need.tags.map(clean).filter((tag): tag is string => Boolean(tag)) : [];

  return {
    // Recommendation-facing auxiliary use only -- see field docs on
    // PremiumMeaningConsultationContext. Never used for validity.
    primaryNeed: tags[0] ?? null,
    secondaryNeed: tags[1] ?? null,
    mode: clean(mode ?? undefined),
    // Consultation Meaning v1 (PR-C): mapped from the stable
    // `consultation_meaning` API field only. Missing/empty families map to
    // empty arrays -- never throws, never fabricates a signal.
    situationSignals: mapSituationSignals(consultationMeaning),
    desiredOutcomeSignals: mapDesiredOutcomeSignals(consultationMeaning),
    explicitConstraintSignals: mapExplicitConstraintSignals(consultationMeaning),
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
    // see Backend Readiness Gap Audit) -- not sourced here.
    tradition: null,
    verificationMetadata: null,
    // Fixed: no Relevance judgment logic exists to source from, and
    // Relevance must never be inferred from Evidence presence.
    relevantToConsultation: null,
    relevantToVisit: null,
  };
}

/**
 * Maps the existing, stable Concierge Response shape into a
 * PremiumMeaningContext. Never throws: missing/empty `rec`, `need`,
 * `mode`, or `consultationMeaning` all resolve to null/empty-filled fields
 * rather than an exception. When no shrineId can be resolved (no `rec`, or
 * `rec` without `shrine_id`/`id`), there is nothing to attach Evidence to,
 * so this returns `null` rather than fabricate a Context.
 *
 * `personalization` is intentionally left empty ({}): none of its fields
 * (birthdate / astroElement / profileContext / direction) are part of this
 * mapping's scope (_need/mode, reason_facts, recommendation_reason_v4_detail,
 * trust_metadata, consultation_meaning only) -- populating them is
 * deferred, not invented here.
 */
export function mapConciergeResponseToPremiumMeaningContext(
  params: MapConciergeResponseParams,
): PremiumMeaningContext | null {
  const rec = params.rec ?? null;
  const shrineId = resolveShrineId(rec);
  if (shrineId === null || !rec) return null;

  const consultation = mapConsultation(params.need, params.mode, params.consultationMeaning);
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
