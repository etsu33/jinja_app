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
