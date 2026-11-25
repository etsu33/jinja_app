import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "../route";

vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: vi.fn(),
}));

import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

function createRequest(body: unknown) {
  return {
    text: async () => JSON.stringify(body),
  } as any;
}

describe("POST /api/compass/recommendations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("正常系: bodyをそのままDjangoへ転送する", async () => {
    const mockResponse = { ok: true, status: 200, json: async () => ({ state: "recommendation_success" }) };
    (bffFetchWithAuthFromReq as any).mockResolvedValue(mockResponse);

    const body = { purpose: "career", origin: { lat: 35, lng: 135 }, birthdate: "1990-01-01" };
    const res = await POST(createRequest(body));

    expect(bffFetchWithAuthFromReq).toHaveBeenCalledWith(
      expect.anything(),
      "/api/compass/recommendations/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(body),
      }),
    );
    expect(res).toBe(mockResponse);
  });

  it("upstreamのエラーレスポンスもそのまま返す", async () => {
    const mockResponse = { ok: false, status: 400, json: async () => ({ state: "invalid_purpose" }) };
    (bffFetchWithAuthFromReq as any).mockResolvedValue(mockResponse);

    const res = await POST(createRequest({ purpose: "not_real" }));
    expect(res).toBe(mockResponse);
  });
});
