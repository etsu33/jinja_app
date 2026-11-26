/**
 * AuthProvider とログインユーザーの識別（identify / reset）の結び付き。
 *
 * - identify に渡すのは内部ユーザーIDの文字列だけ（メール・表示名・ユーザー名は渡さない）
 * - logout、および 401 で Guest に戻ったときは reset する
 * - 判定不能（5xx 等）のときは identify も reset もしない
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import { setAnalyticsProvider, type AnalyticsProvider } from "@/lib/analytics/providers";
import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";
import { markLoggedIn } from "@/lib/auth/loggedInMarker";

const ME_URL = "/api/users/me/";

const PII_USER = {
  id: 42,
  username: "taro_yamada",
  email: "taro@example.com",
  profile: { nickname: "たろう", birthday: "1990-01-01", birth_place: "東京都" },
};

type MeResponder = () => Response | Promise<Response>;

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function AuthProbe() {
  const { isLoggedIn, loading, refreshMe, logout, login } = useAuth();
  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <div data-testid="logged-in">{isLoggedIn ? "yes" : "no"}</div>
      <button type="button" onClick={() => void refreshMe()}>
        refresh
      </button>
      <button type="button" onClick={() => void logout()}>
        do-logout
      </button>
      <button type="button" onClick={() => void login("u", "p").catch(() => {})}>
        do-login
      </button>
    </div>
  );
}

describe("AuthProvider analytics identity", () => {
  let identify: ReturnType<typeof vi.fn<(userId: string) => void>>;
  let reset: ReturnType<typeof vi.fn<() => void>>;
  let meResponder: MeResponder;

  beforeEach(() => {
    localStorage.clear();
    // "/" は shouldAutoFetchMe() の除外 route で /me を叩かないため、自動取得する route で描画する。
    window.history.replaceState(null, "", "/mypage");
    identify = vi.fn<(userId: string) => void>();
    reset = vi.fn<() => void>();
    const provider: AnalyticsProvider = { track: vi.fn(), identify, reset };
    setAnalyticsProvider(provider);

    meResponder = () => jsonResponse(200, { user: PII_USER });

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === ME_URL) return meResponder();
        if (url === "/api/auth/login") return jsonResponse(200, {});
        if (url === "/api/auth/logout") return jsonResponse(200, {});
        throw new Error(`unexpected fetch: ${url}`);
      }),
    );
  });

  afterEach(() => {
    setAnalyticsProvider(null);
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  async function renderReady() {
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("ready"));
  }

  it("認証済みになったら、内部ユーザーIDの文字列だけで identify する（個人情報を渡さない）", async () => {
    await renderReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    // 認証状態の描画と analytics identify は別の effect。
    // 描画直後に同期的に検証すると、並列テスト実行時に競合することがある。
    await waitFor(() => expect(identify).toHaveBeenCalledTimes(1));
    expect(identify.mock.calls[0]).toEqual(["42"]);

    const serializedArgs = JSON.stringify(identify.mock.calls);
    for (const pii of ["taro_yamada", "taro@example.com", "たろう", "1990-01-01", "東京都"]) {
      expect(serializedArgs).not.toContain(pii);
    }
  });

  it("同じユーザーで refreshMe しても identify を重ねない", async () => {
    await renderReady();

    await act(async () => {
      screen.getByRole("button", { name: "refresh" }).click();
    });

    expect(identify).toHaveBeenCalledTimes(1);
  });

  it("logout で reset し、再ログインすると改めて identify する", async () => {
    await renderReady();

    await act(async () => {
      screen.getByRole("button", { name: "do-logout" }).click();
    });

    await waitFor(() => expect(screen.getByTestId("logged-in")).toHaveTextContent("no"));
    expect(reset).toHaveBeenCalledTimes(1);

    await act(async () => {
      screen.getByRole("button", { name: "do-login" }).click();
    });

    await waitFor(() => expect(screen.getByTestId("logged-in")).toHaveTextContent("yes"));
    // identify は描画のあとの useEffect で呼ばれる（AuthProvider.tsx）。「yes」が出た時点では
    // まだ呼ばれていないことがあるため、呼ばれるまで待つ。
    await waitFor(() => expect(identify).toHaveBeenCalledTimes(2));
    expect(identify.mock.calls[1]).toEqual(["42"]);
  });

  it("別のユーザーに切り替わったら、前の識別を reset してから identify する", async () => {
    await renderReady();

    meResponder = () => jsonResponse(200, { user: { ...PII_USER, id: 7 } });
    await act(async () => {
      screen.getByRole("button", { name: "refresh" }).click();
    });

    expect(reset).toHaveBeenCalledTimes(1);
    expect(identify.mock.calls).toEqual([["42"], ["7"]]);
    expect(reset.mock.invocationCallOrder[0]).toBeLessThan(identify.mock.invocationCallOrder[1]);
  });

  it("識別済みのユーザーが 401 で Guest に戻ったら reset する", async () => {
    await renderReady();

    meResponder = () => jsonResponse(401, {});
    await act(async () => {
      screen.getByRole("button", { name: "refresh" }).click();
    });

    await waitFor(() => expect(screen.getByTestId("logged-in")).toHaveTextContent("no"));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("直近ログインしていたブラウザで、読み込み時に 401 なら reset する（セッション切れ）", async () => {
    markLoggedIn();
    meResponder = () => jsonResponse(401, {});

    await renderReady();

    expect(reset).toHaveBeenCalledTimes(1);
    expect(identify).not.toHaveBeenCalled();
  });

  it("最初から匿名の Guest（marker なし）で 401 のときは reset しない", async () => {
    meResponder = () => jsonResponse(401, {});

    await renderReady();

    expect(reset).not.toHaveBeenCalled();
    expect(identify).not.toHaveBeenCalled();
  });

  it("判定不能（5xx）のときは identify も reset もしない", async () => {
    markLoggedIn();
    meResponder = () => jsonResponse(503, {});

    await renderReady();

    expect(identify).not.toHaveBeenCalled();
    expect(reset).not.toHaveBeenCalled();
  });

  it("analytics が例外を投げても認証の流れは止まらない", async () => {
    identify.mockImplementation(() => {
      throw new Error("analytics failed");
    });
    reset.mockImplementation(() => {
      throw new Error("analytics failed");
    });

    await renderReady();
    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");

    await act(async () => {
      screen.getByRole("button", { name: "do-logout" }).click();
    });
    await waitFor(() => expect(screen.getByTestId("logged-in")).toHaveTextContent("no"));
  });
});
