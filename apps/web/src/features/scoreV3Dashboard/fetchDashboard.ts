import type { ScoreV3DashboardResponse } from "./types";

export type FetchDashboardResult =
  | { ok: true; data: ScoreV3DashboardResponse }
  | { ok: false; status: number; message: string };

export async function fetchScoreV3Dashboard(): Promise<FetchDashboardResult> {
  let res: Response;
  try {
    res = await fetch("/api/concierge/score-v3/dashboard/", {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    return { ok: false, status: 0, message: "ネットワークエラー" };
  }

  if (!res.ok) {
    const msgs: Record<number, string> = {
      401: "未認証です。ログインしてください。",
      403: "権限がありません（admin / superuser 専用）。",
    };
    return { ok: false, status: res.status, message: msgs[res.status] ?? `エラー (HTTP ${res.status})` };
  }

  const data = (await res.json()) as ScoreV3DashboardResponse;
  return { ok: true, data };
}
