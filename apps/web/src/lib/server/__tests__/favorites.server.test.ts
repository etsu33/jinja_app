import { beforeEach, describe, expect, it, vi } from "vitest";

const headersMock = vi.fn();
const cookiesMock = vi.fn();
const resolveServerBaseUrlFromHeadersMock = vi.fn();

vi.mock("server-only", () => ({}));

vi.mock("next/headers", () => ({
  headers: headersMock,
  cookies: cookiesMock,
}));

vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrlFromHeaders: resolveServerBaseUrlFromHeadersMock,
}));

describe("getShrineFavoriteInitialState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resolveServerBaseUrlFromHeadersMock.mockReturnValue("http://localhost:3000");
  });

  it("auth context が無いとき guestMode=true を返す", async () => {
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue(null),
    });

    cookiesMock.mockResolvedValue({
      toString: () => "",
    });

    const fetchSpy = vi.spyOn(global, "fetch");

    const { getShrineFavoriteInitialState } = await import(
      "@/lib/server/favorites.server"
    );

    const result = await getShrineFavoriteInitialState(47);

    expect(result).toEqual({
      fav: false,
      favorite_id: null,
      guestMode: true,
    });
    expect(fetchSpy).not.toHaveBeenCalled();

    fetchSpy.mockRestore();
  });

  it("/api/favorites/ が 401 のとき guestMode=true を返す", async () => {
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue(null),
    });

    cookiesMock.mockResolvedValue({
      toString: () => "access_token=dummy",
    });

    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 401,
      ok: false,
      json: vi.fn(),
    } as unknown as Response);

    const { getShrineFavoriteInitialState } = await import(
      "@/lib/server/favorites.server"
    );

    const result = await getShrineFavoriteInitialState(47);

    expect(result).toEqual({
      fav: false,
      favorite_id: null,
      guestMode: true,
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:3000/api/favorites/",
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          cookie: "access_token=dummy",
        }),
      }),
    );

    fetchSpy.mockRestore();
  });

  it("200 で shrineId 一致時に fav=true / favorite_id を返す", async () => {
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue("Bearer token"),
    });

    cookiesMock.mockResolvedValue({
      toString: () => "access_token=dummy; refresh_token=dummy2",
    });

    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 200,
      ok: true,
      json: vi.fn().mockResolvedValue([
        {
          id: 4,
          target_type: "shrine",
          shrine_id: 47,
        },
      ]),
    } as unknown as Response);

    const { getShrineFavoriteInitialState } = await import(
      "@/lib/server/favorites.server"
    );

    const result = await getShrineFavoriteInitialState(47);

    expect(result).toEqual({
      fav: true,
      favorite_id: 4,
      guestMode: false,
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:3000/api/favorites/",
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          cookie: "access_token=dummy; refresh_token=dummy2",
          authorization: "Bearer token",
        }),
      }),
    );

    fetchSpy.mockRestore();
  });

  it("target_type !== 'shrine' は無視する", async () => {
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue("Bearer token"),
    });

    cookiesMock.mockResolvedValue({
      toString: () => "access_token=dummy",
    });

    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 200,
      ok: true,
      json: vi.fn().mockResolvedValue([
        {
          id: 9,
          target_type: "place",
          shrine_id: 47,
        },
      ]),
    } as unknown as Response);

    const { getShrineFavoriteInitialState } = await import(
      "@/lib/server/favorites.server"
    );

    const result = await getShrineFavoriteInitialState(47);

    expect(result).toEqual({
      fav: false,
      favorite_id: null,
      guestMode: false,
    });

    fetchSpy.mockRestore();
  });

  it("upstream error 時に fav=false / favorite_id=null / guestMode=false を返す", async () => {
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue("Bearer token"),
    });

    cookiesMock.mockResolvedValue({
      toString: () => "access_token=dummy",
    });

    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 500,
      ok: false,
      json: vi.fn(),
    } as unknown as Response);

    const { getShrineFavoriteInitialState } = await import(
      "@/lib/server/favorites.server"
    );

    const result = await getShrineFavoriteInitialState(47);

    expect(result).toEqual({
      fav: false,
      favorite_id: null,
      guestMode: false,
    });

    fetchSpy.mockRestore();
  });
});
