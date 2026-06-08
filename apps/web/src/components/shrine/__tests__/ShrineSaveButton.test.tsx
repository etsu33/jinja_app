import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ShrineSaveButton from "../ShrineSaveButton";

const pushMock = vi.fn();
const useAuthMock = vi.fn();
const useFavoriteMock = vi.fn();
const trackMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@/hooks/useFavorite", () => ({
  useFavorite: (args: unknown) => useFavoriteMock(args),
}));

vi.mock("@/lib/analytics/track", () => ({
  track: (...args: unknown[]) => trackMock(...args),
}));

describe("ShrineSaveButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthMock.mockReturnValue({
      isLoggedIn: true,
      loading: false,
    });
  });

  it("解除後表示が `保存する` に戻る", async () => {
    const toggleMock = vi.fn().mockResolvedValue(undefined);

    useFavoriteMock.mockImplementation(() => ({
      fav: true,
      busy: false,
      toggle: toggleMock,
    }));

    const { rerender } = render(
      <ShrineSaveButton
        shrineId={17}
        ctx="concierge"
        tid="thread-123"
        nextPath="/shrines/17?ctx=concierge"
        guestMode={false}
        initial={{
          fav: true,
          favorite_id: 123,
        }}
      />,
    );

    expect(screen.getByRole("button", { name: "保存しました" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "保存しました" }));

    expect(toggleMock).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(trackMock).toHaveBeenCalledWith("favorite_click", {
        shrineId: 17,
        ctx: "concierge",
        tid: "thread-123",
        nextFav: false,
        source: "shrine_detail",
        cardId: "saved_record",
        accessLevel: "free",
      });
    });

    useFavoriteMock.mockImplementation(() => ({
      fav: false,
      busy: false,
      toggle: toggleMock,
    }));

    rerender(
      <ShrineSaveButton
        shrineId={17}
        ctx="concierge"
        tid="thread-123"
        nextPath="/shrines/17?ctx=concierge"
        guestMode={false}
        initial={{
          fav: true,
          favorite_id: 123,
        }}
      />,
    );

    expect(screen.getByRole("button", { name: "あとで見返すために保存" })).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("解除失敗時にエラー表示を出す", async () => {
    useFavoriteMock.mockImplementation(() => ({
      fav: true,
      busy: false,
      toggle: vi.fn().mockRejectedValue(new Error("remove failed")),
    }));

    render(
      <ShrineSaveButton
        shrineId={17}
        nextPath="/shrines/17?ctx=concierge"
        guestMode={false}
        initial={{
          fav: true,
          favorite_id: 123,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "保存しました" }));

    expect(await screen.findByText("保存の更新に失敗しました")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
    expect(trackMock).not.toHaveBeenCalled();
  });
});
