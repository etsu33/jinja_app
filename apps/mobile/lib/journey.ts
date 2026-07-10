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
