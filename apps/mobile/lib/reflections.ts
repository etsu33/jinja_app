import { getAuth, postAuth } from "./http";

export type ShrineReflectionResponse = {
  id: number;
  shrine: number;
  shrine_name?: string | null;
  shrine_address?: string | null;
  history_theme: string;
  prompt: string;
  answer: string;
  mood_before: string;
  mood_after: string;
  created_at: string;
  state_change_direction?: string | null;
  state_change_summary?: string | null;
  next_need_hint?: string[];
  next_history_theme_hint?: string[];
};

export type CreateShrineReflectionParams = {
  shrineId: number | string;
  answer: string;
  prompt?: string | null;
  historyTheme?: string | null;
  moodBefore?: string | null;
  moodAfter?: string | null;
};

function normalizePositiveInt(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export async function createShrineReflection({
  shrineId,
  answer,
  prompt = null,
  historyTheme = null,
  moodBefore = null,
  moodAfter = null,
}: CreateShrineReflectionParams): Promise<ShrineReflectionResponse | null> {
  const normalizedShrineId = normalizePositiveInt(shrineId);
  const normalizedAnswer = answer.trim();

  if (!normalizedShrineId || !normalizedAnswer) return null;

  try {
    return await postAuth<ShrineReflectionResponse>(`/shrines/${normalizedShrineId}/reflection/`, {
      answer: normalizedAnswer,
      prompt: prompt ?? "",
      history_theme: historyTheme ?? "",
      mood_before: moodBefore ?? "",
      mood_after: moodAfter ?? "",
    });
  } catch (error) {
    if (__DEV__) {
      console.warn("[createShrineReflection] failed", error);
    }
    return null;
  }
}

type PaginatedResponse<T> = {
  results: T[];
};

export async function listShrineReflections(): Promise<ShrineReflectionResponse[]> {
  try {
    const data = await getAuth<ShrineReflectionResponse[] | PaginatedResponse<ShrineReflectionResponse>>(
      "/reflections/",
    );
    return Array.isArray(data) ? data : (data.results ?? []);
  } catch (error) {
    if (__DEV__) {
      console.warn("[listShrineReflections] failed", error);
    }
    return [];
  }
}
