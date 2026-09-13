import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  updateUser: vi.fn(),
  refreshMe: vi.fn(),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => mocks.useAuth(),
}));

vi.mock("@/lib/api/users", () => ({
  updateUser: mocks.updateUser,
}));

import { useSharedBirthdayPersistence } from "@/lib/profile/useSharedBirthdayPersistence";

function setAuth({
  isLoggedIn,
  birthday,
  plan,
}: {
  isLoggedIn: boolean;
  birthday?: string | null;
  // 保存境界は plan を見ない。Premium分岐が紛れ込んでいないことを示すためだけに受ける。
  plan?: "free" | "premium";
}) {
  mocks.useAuth.mockReturnValue({
    user: isLoggedIn
      ? {
          id: 1,
          username: "tarou",
          email: "tarou@example.com",
          plan: plan ?? "free",
          profile: { nickname: "太郎", is_public: false, birthday: birthday ?? null },
        }
      : null,
    isLoggedIn,
    loading: false,
    refreshMe: mocks.refreshMe,
    login: vi.fn(),
    logout: vi.fn(),
  });
}

describe("useSharedBirthdayPersistence", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setAuth({ isLoggedIn: false });
  });

  it("Guestではbirthdayを永続化しない", () => {
    const { result } = renderHook(() => useSharedBirthdayPersistence());

    act(() => result.current.persistBirthday("1990-01-01"));

    expect(mocks.updateUser).not.toHaveBeenCalled();
  });

  it("保存済みbirthdayと同じ値ならPATCHしない", () => {
    setAuth({ isLoggedIn: true, birthday: "1984-05-15" });
    const { result } = renderHook(() => useSharedBirthdayPersistence());

    act(() => result.current.persistBirthday("1984-05-15"));

    expect(mocks.updateUser).not.toHaveBeenCalled();
  });

  it("ログイン中に有効な別birthdayを使った場合だけPATCHし、Authを再同期する", async () => {
    setAuth({ isLoggedIn: true, birthday: "1984-05-15" });
    mocks.updateUser.mockResolvedValue({
      id: 1,
      username: "tarou",
      email: "tarou@example.com",
      profile: { nickname: "太郎", is_public: false, birthday: "1990-01-01" },
    });
    mocks.refreshMe.mockResolvedValue(undefined);

    const { result } = renderHook(() => useSharedBirthdayPersistence());

    act(() => result.current.persistBirthday("1990-01-01"));

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: "1990-01-01" }));
    await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
  });

  // birthday は Premium専用データではない。ログインしていれば Free でも保存する。
  // 将来 plan による分岐が紛れ込んだらここで落ちる。
  it.each(["free", "premium"] as const)(
    "%s プランでも、ログイン中なら同じ条件でbirthdayを保存する",
    async (plan) => {
      setAuth({ isLoggedIn: true, birthday: null, plan });

      const { result } = renderHook(() => useSharedBirthdayPersistence());
      act(() => {
        result.current.persistBirthday("1990-01-01");
      });

      await waitFor(() =>
        expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: "1990-01-01" }),
      );
      expect(mocks.updateUser).toHaveBeenCalledTimes(1);
    },
  );

  it("不正なbirthdayは保存しない", () => {
    setAuth({ isLoggedIn: true, birthday: null });
    const { result } = renderHook(() => useSharedBirthdayPersistence());

    act(() => result.current.persistBirthday("not-a-date"));

    expect(mocks.updateUser).not.toHaveBeenCalled();
  });

  it("Profile保存失敗を外へthrowせず、次回の保存を再試行できる", async () => {
    setAuth({ isLoggedIn: true, birthday: null });
    mocks.updateUser
      .mockRejectedValueOnce(new Error("updateUser failed: 500"))
      .mockResolvedValueOnce({
        id: 1,
        username: "tarou",
        email: "tarou@example.com",
        profile: { nickname: "太郎", is_public: false, birthday: "1990-01-01" },
      });
    mocks.refreshMe.mockResolvedValue(undefined);

    const { result } = renderHook(() => useSharedBirthdayPersistence());

    expect(() => {
      act(() => result.current.persistBirthday("1990-01-01"));
    }).not.toThrow();

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledTimes(1));
    await act(async () => {
      await Promise.resolve();
    });

    act(() => result.current.persistBirthday("1990-01-01"));

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledTimes(2));
  });
});
