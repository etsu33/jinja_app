import api from "./client";
import type { Shrine } from "./shrines";

export type Visit = {
  id: number;
  shrine: Shrine | number;
  shrine_name?: string;
  shrine_address?: string;
  thread_id?: number | null;
  visited_at: string;
  note?: string;
  status?: string;
};

// 参拝チェックイン（トグル）
// threadIdを渡すと、参拝のきっかけとなった相談スレッドとして紐付ける（本人のスレッドのみ有効）。
export async function addVisit(shrineId: number, threadId?: string | number | null) {
  const numericThreadId = threadId != null ? Number(threadId) : undefined;
  const hasThreadId = numericThreadId != null && Number.isFinite(numericThreadId);

  const res = hasThreadId
    ? await api.post(`/shrines/${shrineId}/visit`, { thread_id: numericThreadId })
    : await api.post(`/shrines/${shrineId}/visit`);
  return res.data;
}

// 参拝履歴一覧
export async function getVisits(): Promise<Visit[]> {
  const res = await api.get("/visits/");
  const data = res.data;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;

  return [];
}
