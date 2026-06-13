import api from "./client";

export type ShrineReflectionPayload = {
  history_theme?: string | null;
  prompt?: string;
  answer: string;
  mood_before?: string | null;
  mood_after?: string | null;
};

export type ShrineReflection = {
  id: number;
  user: number;
  shrine: number;
  shrine_name?: string;
  shrine_address?: string;
  history_theme: string;
  prompt: string;
  answer: string;
  mood_before: string;
  mood_after: string;
  created_at: string;
};

export async function createShrineReflection(
  shrineId: number | string,
  payload: ShrineReflectionPayload,
): Promise<ShrineReflection> {
  const res = await api.post(`/shrines/${shrineId}/reflection`, payload);
  return res.data;
}
