import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import NewShrinePage from "../page";
import { useAuth } from "@/lib/auth/AuthProvider";

const pushMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/features/shrine-submission/components/ShrineSubmissionForm", () => ({
  ShrineSubmissionForm: ({
    onSubmitted,
    onRequireAuth,
  }: {
    onSubmitted: (submission: { status: string; name: string }) => void;
    onRequireAuth: () => void;
  }) => (
    <div>
      <button
        type="button"
        onClick={() =>
          onSubmitted({
            status: "pending",
            name: "未登録テスト神社20260419",
          })
        }
      >
        submit-success
      </button>
      <button type="button" onClick={onRequireAuth}>
        require-auth
      </button>
    </div>
  ),
}));

const mockedUseAuth = vi.mocked(useAuth);

describe("/shrines/new page", () => {
  const originalWindowLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search: "",
      },
    });
  });

  it("submit成功時にreturnToへsubmitted/status/name付きで戻る", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search:
          "?returnTo=%2Fshrines%3Fq%3D%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      },
    });

    mockedUseAuth.mockReturnValue({
      isLoggedIn: true,
      loading: false,
    } as ReturnType<typeof useAuth>);

    render(<NewShrinePage />);

    fireEvent.click(screen.getByRole("button", { name: "submit-success" }));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith(
        "/shrines?q=未登録テスト神社20260419&submitted=1&status=pending&name=%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      );
    });
  });

  it("mypage起点のsubmit成功時はsubmissionsタブへ戻る", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search: "?returnTo=%2Fmypage%3Ftab%3Dgoshuin",
      },
    });

    mockedUseAuth.mockReturnValue({
      isLoggedIn: true,
      loading: false,
    } as ReturnType<typeof useAuth>);

    render(<NewShrinePage />);

    fireEvent.click(screen.getByRole("button", { name: "submit-success" }));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith(
        "/mypage?tab=submissions&submitted=1&status=pending&name=%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      );
    });
  });

  it("未ログインならreturnToを保持したままログインへ飛ばす", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search: "?returnTo=%2Fshrines%3Fq%3Dtest",
      },
    });

    mockedUseAuth.mockReturnValue({
      isLoggedIn: false,
      loading: false,
    } as ReturnType<typeof useAuth>);

    render(<NewShrinePage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenLastCalledWith(
        "/auth/login?returnTo=%2Fshrines%2Fnew%3FreturnTo%3D%2Fshrines%3Fq%3Dtest",
      );
    });
  });
});
