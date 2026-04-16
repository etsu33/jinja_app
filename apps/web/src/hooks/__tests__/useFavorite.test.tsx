import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";

import { __resetFavoritesCacheForTest } from "@/lib/favoritesCache";

// global fetch spy
const fetchSpy = vi.fn();

describe("useFavorite 認証分岐", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    __resetFavoritesCacheForTest();
    // @ts-ignore
    global.fetch = fetchSpy;
  });

  it("未ログイン時は /api/favorites/ を叩かない", async () => {
    const { result } = renderHook(() =>
      require("@/hooks/useFavorite").useFavorite({ shrineId: 1, guestMode: true }),
    );

    expect(result.current.isGuest).toBe(true);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
