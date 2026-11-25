/**
 * Regression tests for E2E-003 (docs/audit/beta-core-flow-e2e-audit.md).
 *
 * After a successful signup the user is already authenticated by cookie, but
 * the client must ALSO enter the authenticated state — including on the routes
 * where `AuthProvider` deliberately skips the automatic `/api/users/me/` fetch
 * (`/`, `/shrines/*`, `/concierge*`). Before the fix, signup called
 * `@/lib/api/auth`'s `login()` directly, which did not set the logged-in
 * marker, so those routes rendered a freshly registered user as a Guest.
 *
 * The suite drives the real `login()` (not a mock) so it pins the actual
 * contract: "a successful canonical login establishes the client marker".
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";
import { maybeLoggedIn } from "@/lib/auth/loggedInMarker";
import { login as canonicalLogin, logout as canonicalLogout } from "@/lib/api/auth";

function AuthProbe() {
  const { isLoggedIn, loading, user } = useAuth();
  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <div data-testid="logged-in">{isLoggedIn ? "yes" : "no"}</div>
      <div data-testid="username">{user?.username ?? "__NONE__"}</div>
    </div>
  );
}

/** jsdom の location を書き換える。AuthProvider は mount 時の pathname を読む。 */
function setPathname(pathname: string) {
  window.history.replaceState({}, "", pathname);
}

function stubFetch(overrides: { meOk?: boolean; loginOk?: boolean } = {}) {
  const { meOk = true, loginOk = true } = overrides;

  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/auth/login") {
      return {
        ok: loginOk,
        status: loginOk ? 200 : 401,
        text: async () => "",
        json: async () => ({}),
      } as unknown as Response;
    }

    if (url === "/api/auth/logout") {
      return { ok: true, status: 200, json: async () => ({}) } as unknown as Response;
    }

    if (url === "/api/users/me/") {
      if (!meOk) {
        return { ok: false, status: 401, json: async () => ({}) } as unknown as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ user: { id: 7, username: "newcomer" } }),
      } as unknown as Response;
    }

    throw new Error(`unexpected fetch: ${url}`);
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/**
 * 「signup → 自動ログイン成功」までを再現する。
 * SignupForm は成功後に full reload するため、そのあとのページは
 * 「marker が立った状態で AuthProvider が新規マウントされる」状態になる。
 */
async function completeSignupLogin() {
  await canonicalLogin({ username: "newcomer", password: "password123" });
}

describe("E2E-003: signup establishes the canonical authenticated client state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    localStorage.clear();
    setPathname("/");
  });

  it("successful signup login sets the canonical logged-in marker", async () => {
    stubFetch();

    expect(maybeLoggedIn()).toBe(false);
    await completeSignupLogin();
    expect(maybeLoggedIn()).toBe(true);
  });

  it("a failed signup login does not mark the user authenticated", async () => {
    stubFetch({ loginOk: false });

    await expect(completeSignupLogin()).rejects.toThrow();
    expect(maybeLoggedIn()).toBe(false);
  });

  // `/`, `/shrines/*`, `/concierge*` は shouldAutoFetchMe() が false を返す
  // route であり、E2E-003 が実際に顕在化していた場所。
  it.each([
    ["/", "Home"],
    ["/shrines/49", "Shrine Detail"],
    ["/concierge", "Concierge entry"],
    ["/concierge?tid=12", "Concierge thread"],
  ])("signup -> %s (%s) renders as authenticated, not Guest", async (destination) => {
    stubFetch();

    await completeSignupLogin();

    // full reload 相当: marker だけが残った状態で AuthProvider を新規マウント。
    setPathname(destination);
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });

    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    expect(screen.getByTestId("username")).toHaveTextContent("newcomer");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith("/api/users/me/", expect.anything());
  });

  it("reloading the destination page does not regress to Guest", async () => {
    stubFetch();

    await completeSignupLogin();
    setPathname("/shrines/49");

    const first = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    });
    first.unmount();

    // 2回目のマウント = ページリロード。marker は localStorage に残る。
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });
    expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
  });

  it("without the marker the same route still renders as Guest (guards the marker's role)", async () => {
    stubFetch();

    // login を経由しない = marker 無し。修正前の signup 経路と同じ状態。
    setPathname("/shrines/49");
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(vi.mocked(fetch)).not.toHaveBeenCalledWith("/api/users/me/", expect.anything());
  });

  it("logout through the canonical auth API clears the marker", async () => {
    stubFetch();

    await completeSignupLogin();
    expect(maybeLoggedIn()).toBe(true);

    await canonicalLogout();
    expect(maybeLoggedIn()).toBe(false);
  });
});
