import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import FavoritesListClient from "../FavoritesListClient";
import { useAuth } from "@/lib/auth/AuthProvider";

const pushMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/features/mypage/components/FavoriteShrineCard", () => ({
  FavoriteShrineCard: ({ favorite }: { favorite: { id: number } }) => <div>favorite-{favorite.id}</div>,
}));

const mockedUseAuth = vi.mocked(useAuth);

describe("FavoritesListClient auth boundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("認証確認中はempty stateを出さない", () => {
    mockedUseAuth.mockReturnValue({ isLoggedIn: false, loading: true } as ReturnType<typeof useAuth>);
    render(<FavoritesListClient initialFavorites={[]} />);
    expect(screen.getByText("認証状態を確認しています...")).toBeInTheDocument();
    expect(screen.queryByText("お気に入りの神社はまだありません")).not.toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("GuestはreturnTo付きLoginへ送る", async () => {
    mockedUseAuth.mockReturnValue({ isLoggedIn: false, loading: false } as ReturnType<typeof useAuth>);
    render(<FavoritesListClient initialFavorites={[]} />);
    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/auth/login?returnTo=%2Ffavorites"));
    expect(screen.queryByText("お気に入りの神社はまだありません")).not.toBeInTheDocument();
  });

  it("Login済み0件だけempty stateを表示する", () => {
    mockedUseAuth.mockReturnValue({ isLoggedIn: true, loading: false } as ReturnType<typeof useAuth>);
    render(<FavoritesListClient initialFavorites={[]} />);
    expect(screen.getByText("お気に入りの神社はまだありません")).toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("Login済みでFavoriteがあれば既存一覧を表示する", () => {
    mockedUseAuth.mockReturnValue({ isLoggedIn: true, loading: false } as ReturnType<typeof useAuth>);
    render(<FavoritesListClient initialFavorites={[{ id: 1 } as never]} />);
    expect(screen.getByText("favorite-1")).toBeInTheDocument();
    expect(screen.queryByText("お気に入りの神社はまだありません")).not.toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
