/**
 * Regression tests for E2E-004 (docs/audit/beta-core-flow-e2e-audit.md).
 *
 * `/api/users/me/` の失敗には2種類ある。
 *
 *   - 確定した未認証（401）          -> Guest へ遷移し、marker を消す
 *   - 確認できなかった失敗（5xx /    -> marker を保持する。消してしまうと
 *     transport error / 非 JSON）       `shouldAutoFetchMe()` の除外 route
 *                                       （`/`・`/shrines/*`・`/concierge*`）
 *                                       では二度と `/me` を叩かないため、
 *                                       認証済みユーザーが Guest に固着する
 *
 * 修正前はこの2つが `fetchMe()` 内で `markLoggedOut(); return null;` に
 * 潰されており、一過性の失敗が恒久的な Guest 状態を作っていた。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";
import { markLoggedIn, maybeLoggedIn } from "@/lib/auth/loggedInMarker";
import { login as canonicalLogin } from "@/lib/api/auth";

const ME_URL = "/api/users/me/";

function AuthProbe() {
  const { isLoggedIn, loading, user, refreshMe, logout } = useAuth();
  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <div data-testid="logged-in">{isLoggedIn ? "yes" : "no"}</div>
      <div data-testid="username">{user?.username ?? "__NONE__"}</div>
      <button type="button" onClick={() => void refreshMe()}>
        retry
      </button>
      <button type="button" onClick={() => void logout()}>
        do-logout
      </button>
    </div>
  );
}

/** AuthProvider はマウント時の pathname を読む。 */
function setPathname(pathname: string) {
  window.history.replaceState({}, "", pathname);
}

type MeOutcome = "ok" | "unauthorized" | "server-error" | "network-error" | "bad-json";

function meResponseFor(outcome: MeOutcome): Response | Promise<never> {
  switch (outcome) {
    case "ok":
      return {
        ok: true,
        status: 200,
        json: async () => ({ user: { id: 42, username: "returning" } }),
      } as unknown as Response;
    case "unauthorized":
      return { ok: false, status: 401, json: async () => ({}) } as unknown as Response;
    case "server-error":
      return { ok: false, status: 500, json: async () => ({}) } as unknown as Response;
    case "bad-json":
      return {
        ok: true,
        status: 200,
        json: async () => {
          throw new SyntaxError("Unexpected token < in JSON");
        },
      } as unknown as Response;
    case "network-error":
      return Promise.reject(new TypeError("Failed to fetch"));
  }
}

/**
 * `/me` の結果を呼び出しごとに順番に返す stub。
 * 末尾の値は以降ずっと使われる（リロード相当の再マウントでも同じ挙動）。
 */
function stubMeSequence(...outcomes: MeOutcome[]) {
  let call = 0;

  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url === ME_URL) {
      const outcome = outcomes[Math.min(call, outcomes.length - 1)];
      call += 1;
      return meResponseFor(outcome);
    }

    if (url === "/api/auth/logout" || url === "/api/auth/login") {
      return { ok: true, status: 200, text: async () => "", json: async () => ({}) } as unknown as Response;
    }

    throw new Error(`unexpected fetch: ${url}`);
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function mountProvider() {
  return render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>,
  );
}

async function waitForReady() {
  await waitFor(() => {
    expect(screen.getByTestId("loading")).toHaveTextContent("ready");
  });
}

describe("E2E-004: /me failure classification and auth recovery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    localStorage.clear();
    setPathname("/mypage");
  });

  it("(1) valid marker + /me 200 -> authenticated", async () => {
    markLoggedIn();
    stubMeSequence("ok");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    expect(screen.getByTestId("username")).toHaveTextContent("returning");
    expect(maybeLoggedIn()).toBe(true);
  });

  it("(2) valid marker + /me 401 -> Guest and the marker is removed", async () => {
    markLoggedIn();
    stubMeSequence("unauthorized");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(screen.getByTestId("username")).toHaveTextContent("__NONE__");
    // 401 は「session 無効」の確定シグナルなので marker は消えるのが正しい。
    expect(maybeLoggedIn()).toBe(false);
  });

  it("(3) valid marker + /me 500 -> the marker is preserved", async () => {
    markLoggedIn();
    stubMeSequence("server-error");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(maybeLoggedIn()).toBe(true);
  });

  it("(4) valid marker + network rejection -> the marker is preserved", async () => {
    markLoggedIn();
    stubMeSequence("network-error");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(maybeLoggedIn()).toBe(true);
  });

  it("(4b) valid marker + 200 with unparseable body -> the marker is preserved", async () => {
    markLoggedIn();
    stubMeSequence("bad-json");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(maybeLoggedIn()).toBe(true);
  });

  it("(5) a temporary failure followed by a successful retry recovers to authenticated", async () => {
    markLoggedIn();
    stubMeSequence("server-error", "ok");

    mountProvider();
    await waitForReady();
    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");

    await act(async () => {
      screen.getByRole("button", { name: "retry" }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    });
    expect(screen.getByTestId("username")).toHaveTextContent("returning");
    expect(maybeLoggedIn()).toBe(true);
  });

  it("(6) reloading after a temporary failure still recovers", async () => {
    markLoggedIn();
    stubMeSequence("network-error", "ok");

    const first = mountProvider();
    await waitForReady();
    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    first.unmount();

    // 2回目のマウント = ページリロード。marker が残っているので /me を再度叩ける。
    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
  });

  // shouldAutoFetchMe() が false を返す route。E2E-004 が固着していた場所。
  describe.each([
    ["(7) /", "/"],
    ["(8) /shrines/:id", "/shrines/49"],
    ["(9) /concierge", "/concierge"],
    ["(9b) /concierge?tid=", "/concierge?tid=12"],
  ])("%s", (_label, pathname) => {
    it("a temporary /me failure does not lock the route into Guest", async () => {
      markLoggedIn();
      stubMeSequence("server-error", "ok");
      setPathname(pathname);

      const first = mountProvider();
      await waitForReady();
      // 失敗したこの表示では Guest 扱い（fail-closed）だが…
      expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
      // …marker は残っているので、この route でも再試行の余地がある。
      expect(maybeLoggedIn()).toBe(true);
      first.unmount();

      mountProvider();
      await waitForReady();

      expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
      expect(screen.getByTestId("username")).toHaveTextContent("returning");
    });

    it("a definitive 401 still transitions to Guest and clears the marker", async () => {
      markLoggedIn();
      stubMeSequence("unauthorized");
      setPathname(pathname);

      mountProvider();
      await waitForReady();

      expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
      expect(maybeLoggedIn()).toBe(false);
    });
  });

  it("(10) explicit logout still clears the marker", async () => {
    markLoggedIn();
    stubMeSequence("ok");

    mountProvider();
    await waitForReady();
    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");

    await act(async () => {
      screen.getByRole("button", { name: "do-logout" }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    });
    expect(maybeLoggedIn()).toBe(false);
  });

  it("(11) the signup/login marker behaviour from E2E-003 is unchanged", async () => {
    stubMeSequence("server-error");

    // PR #2859 の契約: canonical login 成功で marker が立つ。
    expect(maybeLoggedIn()).toBe(false);
    await canonicalLogin({ username: "returning", password: "password123" });
    expect(maybeLoggedIn()).toBe(true);

    // その直後に /me が一過性の失敗をしても、signup で確立した marker は残る。
    setPathname("/shrines/49");
    mountProvider();
    await waitForReady();

    expect(maybeLoggedIn()).toBe(true);
  });

  it("does not fetch /me at all when there is no marker on an excluded route", async () => {
    const fetchMock = stubMeSequence("ok");
    setPathname("/shrines/49");

    mountProvider();
    await waitForReady();

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(fetchMock).not.toHaveBeenCalledWith(ME_URL, expect.anything());
  });
});
