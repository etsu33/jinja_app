import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import { preloadFavoritesByShrineIds } from "../favorites";

describe("preloadFavoritesByShrineIds", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("正常系: by_shrine_id map を返す", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({
        by_shrine_id: {
          "1": { fav: true, favorite_id: 10 },
          "2": { fav: false, favorite_id: null },
        },
      }),
    } as any);

    const originalFetch = global.fetch;
    global.fetch = mockFetch as any;

    const result = await preloadFavoritesByShrineIds([1, 2, 2]);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/favorites/preload/",
      expect.objectContaining({
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shrine_ids: [1, 2] }),
      }),
    );
    expect(result).toEqual({
      "1": { fav: true, favorite_id: 10 },
      "2": { fav: false, favorite_id: null },
    });

    global.fetch = originalFetch;
  });

  it("401 のときは空 map を返す", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
    } as any);

    const originalFetch = global.fetch;
    global.fetch = mockFetch as any;

    const result = await preloadFavoritesByShrineIds([1]);

    expect(result).toEqual({});
    expect(mockFetch).toHaveBeenCalledTimes(1);

    global.fetch = originalFetch;
  });

  it("empty ids のときは fetch しない", async () => {
    const mockFetch = vi.fn();

    const originalFetch = global.fetch;
    global.fetch = mockFetch as any;

    const result = await preloadFavoritesByShrineIds([]);

    expect(result).toEqual({});
    expect(mockFetch).not.toHaveBeenCalled();

    global.fetch = originalFetch;
  });
});
