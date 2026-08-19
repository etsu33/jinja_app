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
        recommendationInstanceId: null,
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

  it("ctx=compassの場合、favorite_click / shrine_decisionともにsource=compassを送る（PR-C）", async () => {
    const toggleMock = vi.fn().mockResolvedValue(undefined);

    useFavoriteMock.mockImplementation(() => ({
      fav: false,
      busy: false,
      toggle: toggleMock,
    }));

    render(
      <ShrineSaveButton
        shrineId={17}
        ctx="compass"
        tid={null}
        nextPath="/shrines/17?ctx=compass"
        guestMode={false}
        recommendationInstanceId="rid-compass-1"
        initial={{ fav: false, favorite_id: null }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "あとで見返すために保存" }));

    await waitFor(() => {
      expect(trackMock).toHaveBeenCalledWith(
        "favorite_click",
        expect.objectContaining({ source: "compass", ctx: "compass", recommendationInstanceId: "rid-compass-1" }),
      );
    });
    expect(trackMock).toHaveBeenCalledWith(
      "shrine_decision",
      expect.objectContaining({ source: "compass", action: "save", recommendationInstanceId: "rid-compass-1" }),
    );
  });

  it("ctx未指定（直接遷移）の場合、Compass由来のsourceは漏れずshrine_detailのままになる（PR-C）", async () => {
    const toggleMock = vi.fn().mockResolvedValue(undefined);

    useFavoriteMock.mockImplementation(() => ({
      fav: false,
      busy: false,
      toggle: toggleMock,
    }));

    render(
      <ShrineSaveButton
        shrineId={17}
        nextPath="/shrines/17"
        guestMode={false}
        initial={{ fav: false, favorite_id: null }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "あとで見返すために保存" }));

    await waitFor(() => {
      expect(trackMock).toHaveBeenCalledWith("favorite_click", expect.objectContaining({ source: "shrine_detail" }));
    });

    const [, favoritePayload] = trackMock.mock.calls.find(([eventName]) => eventName === "favorite_click") ?? [];
    expect(favoritePayload?.source).not.toBe("compass");
  });

  it("favorite_click / shrine_decisionのペイロードにbirthdate・座標・生の位置情報テキストを含めない（PR-C PIIチェック）", async () => {
    const toggleMock = vi.fn().mockResolvedValue(undefined);

    useFavoriteMock.mockImplementation(() => ({
      fav: false,
      busy: false,
      toggle: toggleMock,
    }));

    render(
      <ShrineSaveButton
        shrineId={17}
        ctx="compass"
        nextPath="/shrines/17?ctx=compass"
        guestMode={false}
        recommendationInstanceId="rid-compass-1"
        initial={{ fav: false, favorite_id: null }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "あとで見返すために保存" }));

    await waitFor(() => expect(trackMock).toHaveBeenCalled());

    for (const [, payload] of trackMock.mock.calls) {
      const serialized = JSON.stringify(payload);
      expect(payload).not.toHaveProperty("birthdate");
      expect(payload).not.toHaveProperty("latitude");
      expect(payload).not.toHaveProperty("longitude");
      expect(serialized).not.toMatch(/\d{4}-\d{2}-\d{2}/);
    }
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

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("未保存時、defaultバリアントがradius-panel / border-strong / surface-default / text-primaryを参照する", () => {
      useFavoriteMock.mockImplementation(() => ({
        fav: false,
        busy: false,
        toggle: vi.fn(),
      }));

      render(<ShrineSaveButton shrineId={17} nextPath="/shrines/17" guestMode={false} />);

      const button = screen.getByRole("button", { name: "あとで見返すために保存" });
      expect(button.className).toContain("rounded-[var(--kt-radius-panel)]");
      expect(button.className).toContain("border-[var(--kt-color-border-strong)]");
      expect(button.className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(button.className).toContain("text-[var(--kt-color-text-primary)]");
    });

    it("エラー表示がstatus-errorを参照する", async () => {
      useFavoriteMock.mockImplementation(() => ({
        fav: true,
        busy: false,
        toggle: vi.fn().mockRejectedValue(new Error("failed")),
      }));

      render(
        <ShrineSaveButton
          shrineId={17}
          nextPath="/shrines/17"
          guestMode={false}
          initial={{ fav: true, favorite_id: 1 }}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "保存しました" }));

      const errorText = await screen.findByText("保存の更新に失敗しました");
      expect(errorText.className).toContain("text-[var(--kt-color-status-error)]");
    });
  });
});
