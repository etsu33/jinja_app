import api from "./client";
import type { Shrine } from "./shrines";

export type Visit = {
  id: number;
  shrine: Shrine | number;
  shrine_name?: string;
  shrine_address?: string;
  visited_at: string;
  note?: string;
  status?: string;
};

// 参拝チェックイン（トグル）
export async function addVisit(shrineId: number) {
  const res = await api.post(`/shrines/${shrineId}/visit`);
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
