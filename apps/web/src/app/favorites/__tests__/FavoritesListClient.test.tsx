import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import FavoritesListClient from "../FavoritesListClient";
import type { Favorite } from "@/lib/api/favorites";

const replaceMock = vi.fn();
const pushMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock, refresh: vi.fn() }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@/features/mypage/components/FavoriteShrineCard", () => ({
  FavoriteShrineCard: ({ favorite }: { favorite: Favorite }) => (
    <div data-testid="favorite-card">{String((favorite as { name?: string }).name ?? favorite.id)}</div>
  ),
}));

const FAVORITES: Favorite[] = [
  { id: 1, shrine: 109, name: "三輪神社" },
  { id: 2, shrine: 112, name: "烏森神社" },
] as unknown as Favorite[];

const EMPTY_STATE = "お気に入りの神社はまだありません";
const GUEST_STATE = "ログインするとお気に入りを表示できます";

describe("FavoritesListClient / Guest境界", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Auth loading中は認証確認状態を表示し、empty stateもredirectも出さない", () => {
    useAuthMock.mockReturnValue({ loading: true, isLoggedIn: false });

    render(<FavoritesListClient initialFavorites={[]} />);

    expect(screen.getByRole("status")).toHaveTextContent("ログイン状態を確認しています");
    expect(screen.queryByText(EMPTY_STATE)).not.toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("Guestは /auth/login?returnTo=%2Ffavorites へ遷移する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: false });

    render(<FavoritesListClient initialFavorites={[]} />);

    expect(replaceMock).toHaveBeenCalledWith("/auth/login?returnTo=%2Ffavorites");
  });

  it("Guestには「0件」ではなくLogin導線を表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: false });

    render(<FavoritesListClient initialFavorites={[]} />);

    // getFavoritesServer() は401でも [] を返すため、ここでempty stateを出すと
    // Guestが「お気に入り0件」と誤認する。
    expect(screen.queryByText(EMPTY_STATE)).not.toBeInTheDocument();
    expect(screen.getByText(GUEST_STATE)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ログインへ" })).toHaveAttribute(
      "href",
      "/auth/login?returnTo=%2Ffavorites",
    );
  });

  it("Login済み0件のときだけ既存のempty stateを表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });

    render(<FavoritesListClient initialFavorites={[]} />);

    expect(screen.getByText(EMPTY_STATE)).toBeInTheDocument();
    expect(screen.queryByText(GUEST_STATE)).not.toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
    expect(screen.getByRole("link", { name: "近くの神社を探す" })).toHaveAttribute("href", "/map");
  });

  it("Login済みでFavoriteがあるときは既存の一覧表示を維持する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });

    render(<FavoritesListClient initialFavorites={FAVORITES} />);

    expect(screen.getAllByTestId("favorite-card")).toHaveLength(2);
    expect(screen.queryByText(EMPTY_STATE)).not.toBeInTheDocument();
    expect(screen.queryByText(GUEST_STATE)).not.toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
