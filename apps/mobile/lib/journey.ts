import { getAuth } from "./http";

export type JourneyEventType =
  | "consultation_created"
  | "recommendation_shown"
  | "visit_completed"
  | "reflection_created";

export type JourneyEvent = {
  id: string;
  event_type: JourneyEventType;
  occurred_at: string;
  title: string;
  description: string;
  thread_id: number | null;
  shrine_id: number | null;
  shrine_name: string | null;
  metadata: Record<string, unknown>;
};

// --- recommendation_shown の metadata 契約 ---
// backend/temples/services/journey_timeline.py の _extract_* 群が付与する構造に対応する。
// 欠損・不正な値でも例外を投げず null/空配列にフォールバックする。

export type JourneyActionItem = {
  label: string;
  description: string;
};

export type JourneyReflectionPromptMeta = {
  question: string;
};

export type JourneyActionSourceMeta = {
  source: string;
  reason: string;
};

export type JourneyActionSuggestionMeta = {
  primary_action: JourneyActionItem | null;
  secondary_action: JourneyActionItem | null;
  reflection_prompt: JourneyReflectionPromptMeta | null;
  action_source: JourneyActionSourceMeta | null;
};

export type JourneyReasonFact = {
  type?: string;
  label?: string;
  label_ja?: string;
  evidence?: string[];
  score?: number;
  is_primary?: boolean;
};

export type JourneyRecommendationMetadata = {
  history_theme: string;
  reason: string;
  reason_facts: JourneyReasonFact[];
  matched_benefits: string[];
  action_suggestion: JourneyActionSuggestionMeta | null;
};

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asActionItem(value: unknown): JourneyActionItem | null {
  const record = asRecord(value);
  if (!record) return null;
  const label = asString(record.label);
  const description = asString(record.description);
  if (!label && !description) return null;
  return { label, description };
}

function asReflectionPromptMeta(value: unknown): JourneyReflectionPromptMeta | null {
  const record = asRecord(value);
  if (!record) return null;
  const question = asString(record.question);
  return question ? { question } : null;
}

function asActionSourceMeta(value: unknown): JourneyActionSourceMeta | null {
  const record = asRecord(value);
  if (!record) return null;
  const source = asString(record.source);
  const reason = asString(record.reason);
  if (!source && !reason) return null;
  return { source, reason };
}

function asActionSuggestionMeta(value: unknown): JourneyActionSuggestionMeta | null {
  const record = asRecord(value);
  if (!record) return null;
  const primary_action = asActionItem(record.primary_action);
  const secondary_action = asActionItem(record.secondary_action);
  const reflection_prompt = asReflectionPromptMeta(record.reflection_prompt);
  const action_source = asActionSourceMeta(record.action_source);
  if (!primary_action && !secondary_action && !reflection_prompt && !action_source) return null;
  return { primary_action, secondary_action, reflection_prompt, action_source };
}

function asReasonFacts(value: unknown): JourneyReasonFact[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is JourneyReasonFact => !!item && typeof item === "object");
}

export function parseRecommendationMetadata(
  metadata: Record<string, unknown> | null | undefined,
): JourneyRecommendationMetadata {
  const source = metadata ?? {};
  return {
    history_theme: asString(source.history_theme),
    reason: asString(source.reason),
    reason_facts: asReasonFacts(source.reason_facts),
    matched_benefits: asStringArray(source.matched_benefits),
    action_suggestion: asActionSuggestionMeta(source.action_suggestion),
  };
}

type PaginatedResponse<T> = {
  results: T[];
};

export async function listJourneyEvents(): Promise<JourneyEvent[]> {
  const data = await getAuth<JourneyEvent[] | PaginatedResponse<JourneyEvent>>("/journeys/timeline/");
  return Array.isArray(data) ? data : (data.results ?? []);
}

// --- Visit × Reflection の体験単位ペアリング (v1, 暫定) ---
//
// ペアリングルール:
// - visit_completed を基準にする
// - 同じ shrine_id のみ対象
// - reflection_created.occurred_at が visit_completed.occurred_at 以降
// - 最大7日以内
// - 最も近い Reflection を1件だけ割り当てる（Reflection の重複割り当てはしない）
// - 未結合の Reflection は単独イベントとして残す

const REFLECTION_PAIRING_WINDOW_MS = 7 * 24 * 60 * 60 * 1000;

export type JourneyTimelineItem =
  | { kind: "event"; occurredAt: string; event: JourneyEvent }
  | { kind: "visit_experience"; occurredAt: string; visit: JourneyEvent; reflection: JourneyEvent | null };

function toTime(value: string): number {
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
}

function pairVisitsWithReflections(
  visits: JourneyEvent[],
  reflections: JourneyEvent[],
): { reflectionByVisitId: Map<string, JourneyEvent>; usedReflectionIds: Set<string> } {
  const candidates: { visit: JourneyEvent; reflection: JourneyEvent; diffMs: number }[] = [];

  for (const visit of visits) {
    if (visit.shrine_id == null) continue;

    for (const reflection of reflections) {
      if (reflection.shrine_id !== visit.shrine_id) continue;

      const diffMs = toTime(reflection.occurred_at) - toTime(visit.occurred_at);
      if (diffMs < 0 || diffMs > REFLECTION_PAIRING_WINDOW_MS) continue;

      candidates.push({ visit, reflection, diffMs });
    }
  }

  // 最も近いペアから優先的に確定させることで、1 Reflection が複数 Visit に割り当たらないようにする
  candidates.sort((a, b) => a.diffMs - b.diffMs);

  const reflectionByVisitId = new Map<string, JourneyEvent>();
  const usedVisitIds = new Set<string>();
  const usedReflectionIds = new Set<string>();

  for (const candidate of candidates) {
    if (usedVisitIds.has(candidate.visit.id) || usedReflectionIds.has(candidate.reflection.id)) continue;

    usedVisitIds.add(candidate.visit.id);
    usedReflectionIds.add(candidate.reflection.id);
    reflectionByVisitId.set(candidate.visit.id, candidate.reflection);
  }

  return { reflectionByVisitId, usedReflectionIds };
}

export function buildJourneyTimeline(events: JourneyEvent[]): JourneyTimelineItem[] {
  const visits = events.filter((event) => event.event_type === "visit_completed");
  const reflections = events.filter((event) => event.event_type === "reflection_created");
  const others = events.filter(
    (event) => event.event_type !== "visit_completed" && event.event_type !== "reflection_created",
  );

  const { reflectionByVisitId, usedReflectionIds } = pairVisitsWithReflections(visits, reflections);

  const items: JourneyTimelineItem[] = [
    ...others.map((event) => ({ kind: "event" as const, occurredAt: event.occurred_at, event })),
    ...visits.map((visit) => ({
      kind: "visit_experience" as const,
      occurredAt: visit.occurred_at,
      visit,
      reflection: reflectionByVisitId.get(visit.id) ?? null,
    })),
    ...reflections
      .filter((reflection) => !usedReflectionIds.has(reflection.id))
      .map((event) => ({ kind: "event" as const, occurredAt: event.occurred_at, event })),
  ];

  return items.sort((a, b) => toTime(b.occurredAt) - toTime(a.occurredAt));
}
