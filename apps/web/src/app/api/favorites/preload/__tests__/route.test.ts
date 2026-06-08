import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "../route";

vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: vi.fn(),
}));

import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

function createRequest(body: any) {
  return {
    json: async () => body,
  } as any;
}

describe("POST /api/favorites/preload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("正常系: shrine_ids -> map", async () => {
    (bffFetchWithAuthFromReq as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        { id: 10, shrine_id: 1 },
      ],
    });

    const res = await POST(createRequest({ shrine_ids: [1, 2] }));
    const json = await res.json();

    expect(json.by_shrine_id["1"].fav).toBe(true);
    expect(json.by_shrine_id["2"].fav).toBe(false);
  });

  it("guest (401) -> 空map", async () => {
    (bffFetchWithAuthFromReq as any).mockResolvedValue({
      ok: false,
      status: 401,
    });

    const res = await POST(createRequest({ shrine_ids: [1] }));
    const json = await res.json();

    expect(json).toEqual({ by_shrine_id: {} });
  });

  it("upstream error -> 空map", async () => {
    (bffFetchWithAuthFromReq as any).mockResolvedValue({
      ok: false,
      status: 500,
    });

    const res = await POST(createRequest({ shrine_ids: [1] }));
    const json = await res.json();

    expect(json).toEqual({ by_shrine_id: {} });
  });
});
