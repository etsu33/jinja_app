import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchScoreV3Dashboard } from "../fetchDashboard";
import type { ScoreV3DashboardResponse } from "../types";

const mockResponse: ScoreV3DashboardResponse = {
  score_v3: {
    top1_changed_rate_avg: 0.05,
    activation_candidate_rate: 0.92,
    avg_delta: -0.08,
    max_abs_delta_max: 0.31,
  },
  funnel: {
    route_open_rate: 0.34,
    save_rate: 0.22,
    visit_done_rate: 0.11,
    reflection_saved_rate: 0.06,
  },
  decision: {
    active_candidate: true,
    rollback_required: false,
    reasons: [],
  },
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe("fetchScoreV3Dashboard", () => {
  it("200 のとき ok: true でデータを返す", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      }),
    );

    const result = await fetchScoreV3Dashboard();
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.decision.active_candidate).toBe(true);
      expect(result.data.score_v3.top1_changed_rate_avg).toBe(0.05);
    }
  });

  it("401 のとき ok: false、status 401 を返す", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401 }),
    );

    const result = await fetchScoreV3Dashboard();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(401);
      expect(result.message).toContain("未認証");
    }
  });

  it("403 のとき ok: false、status 403 を返す", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 403 }),
    );

    const result = await fetchScoreV3Dashboard();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(403);
      expect(result.message).toContain("権限");
    }
  });

  it("ネットワークエラーのとき ok: false、status 0 を返す", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network error")),
    );

    const result = await fetchScoreV3Dashboard();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(0);
    }
  });
});
