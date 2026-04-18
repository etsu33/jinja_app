import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useFavorite } from "../useFavorite";

const createFavoriteByShrineIdMock = vi.fn();
const removeFavoriteByPkMock = vi.fn();
const removeFavoriteByShrineIdMock = vi.fn();

const upsertFavoriteMock = vi.fn();
const removeFavoriteFromCacheByPkMock = vi.fn();
const removeFavoriteFromCacheByShrineIdMock = vi.fn();
const clearFavoritesInFlightMock = vi.fn();

vi.mock("@/lib/api/favorites", () => ({
  createFavoriteByShrineId: (...args: unknown[]) => createFavoriteByShrineIdMock(...args),
  removeFavoriteByPk: (...args: unknown[]) => removeFavoriteByPkMock(...args),
  removeFavoriteByShrineId: (...args: unknown[]) => removeFavoriteByShrineIdMock(...args),
}));

vi.mock("@/lib/favoritesCache", () => ({
  upsertFavorite: (...args: unknown[]) => upsertFavoriteMock(...args),
  removeFavoriteFromCacheByPk: (...args: unknown[]) => removeFavoriteFromCacheByPkMock(...args),
  removeFavoriteFromCacheByShrineId: (...args: unknown[]) => removeFavoriteFromCacheByShrineIdMock(...args),
  clearFavoritesInFlight: (...args: unknown[]) => clearFavoritesInFlightMock(...args),
}));

describe("useFavorite", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("解除成功時に fav=false へ戻り removeFavoriteByPk を呼ぶ", async () => {
    removeFavoriteByPkMock.mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useFavorite({
        shrineId: 17,
        guestMode: false,
        initial: {
          fav: true,
          favorite_id: 123,
        },
      }),
    );

    expect(result.current.fav).toBe(true);
    expect(result.current.busy).toBe(false);
    expect(result.current.isGuest).toBe(false);

    await act(async () => {
      await result.current.toggle();
    });

    await waitFor(() => {
      expect(result.current.fav).toBe(false);
    });

    expect(removeFavoriteByPkMock).toHaveBeenCalledTimes(1);
    expect(removeFavoriteByPkMock).toHaveBeenCalledWith(123);

    expect(removeFavoriteFromCacheByPkMock).toHaveBeenCalledTimes(1);
    expect(removeFavoriteFromCacheByPkMock).toHaveBeenCalledWith(123);

    expect(clearFavoritesInFlightMock).toHaveBeenCalledTimes(1);

    expect(removeFavoriteByShrineIdMock).not.toHaveBeenCalled();
    expect(createFavoriteByShrineIdMock).not.toHaveBeenCalled();
    expect(upsertFavoriteMock).not.toHaveBeenCalled();

    expect(result.current.busy).toBe(false);
  });

  it("解除失敗時に fav=true を維持し state を壊さない", async () => {
    const error = new Error("remove failed");
    removeFavoriteByPkMock.mockRejectedValue(error);

    const { result } = renderHook(() =>
      useFavorite({
        shrineId: 17,
        guestMode: false,
        initial: {
          fav: true,
          favorite_id: 123,
        },
      }),
    );

    expect(result.current.fav).toBe(true);
    expect(result.current.busy).toBe(false);

    await expect(
      act(async () => {
        await result.current.toggle();
      }),
    ).rejects.toThrow("remove failed");

    await waitFor(() => {
      expect(result.current.fav).toBe(true);
    });

    expect(removeFavoriteByPkMock).toHaveBeenCalledTimes(1);
    expect(removeFavoriteByPkMock).toHaveBeenCalledWith(123);

    expect(removeFavoriteFromCacheByPkMock).not.toHaveBeenCalled();
    expect(removeFavoriteFromCacheByShrineIdMock).not.toHaveBeenCalled();
    expect(clearFavoritesInFlightMock).not.toHaveBeenCalled();

    expect(removeFavoriteByShrineIdMock).not.toHaveBeenCalled();
    expect(createFavoriteByShrineIdMock).not.toHaveBeenCalled();
    expect(upsertFavoriteMock).not.toHaveBeenCalled();

    expect(result.current.busy).toBe(false);
  });
});
