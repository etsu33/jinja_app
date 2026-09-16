/**
 * Audit-only regression evidence for docs/audit/beta-core-flow-e2e-audit.md.
 *
 * These tests do NOT assert desired behaviour -- they pin the *current*
 * behaviour of `bffFetchWithAuthFromReq` so that the findings recorded in the
 * audit document are reproducible. They are expected to be rewritten (into
 * real assertions) by the follow-up fix PRs referenced in the audit.
 *
 * Covered findings:
 *   E2E-001: module-scope `refreshInFlight` mutex is not keyed by refresh
 *            token, so a concurrent request from another user receives (and
 *            gets Set-Cookie'd) the first user's freshly minted access token.
 *   E2E-002: the refreshed `access_token` cookie is written without `secure`,
 *            unlike /api/auth/login which sets it conditionally.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

vi.mock("@/lib/server/backend", () => ({
  getDjangoOrigin: () => "http://backend.test",
}));

type CookieJar = Record<string, string>;

function makeReq(cookies: CookieJar) {
  const cookieHeader = Object.entries(cookies)
    .map(([k, v]) => `${k}=${v}`)
    .join("; ");

  return {
    headers: {
      get: (name: string) => {
        const key = name.toLowerCase();
        if (key === "cookie") return cookieHeader || null;
        return null;
      },
    },
    cookies: {
      get: (name: string) => (name in cookies ? { value: cookies[name] } : undefined),
      has: (name: string) => name in cookies,
    },
  } as any;
}

/** A JWT whose `exp` is already in the past, forcing the pre-refresh path. */
function expiredJwt(sub: string): string {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(
    JSON.stringify({ sub, exp: Math.floor(Date.now() / 1000) - 3600 }),
  ).toString("base64url");
  return `${header}.${payload}.sig`;
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("bffFetchWithAuthFromReq (audit evidence)", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
  });

  it("E2E-001: a concurrent request from another user is served the first user's refreshed access token", async () => {
    const { bffFetchWithAuthFromReq } = await import("@/lib/server/bffFetch");

    let releaseRefresh: (() => void) | null = null;
    const refreshGate = new Promise<void>((resolve) => {
      releaseRefresh = resolve;
    });

    const authHeadersSeenUpstream: (string | null)[] = [];

    const fetchMock = vi.fn(async (url: string, init: any) => {
      if (String(url).includes("/api/auth/jwt/refresh/")) {
        // Only USER-A ever reaches the backend refresh endpoint; USER-B's call
        // is swallowed by the shared module-scope promise.
        await refreshGate;
        return jsonResponse({ access: "ACCESS_FOR_USER_A" });
      }

      authHeadersSeenUpstream.push(init?.headers?.Authorization ?? null);
      return jsonResponse({ ok: true });
    });

    vi.stubGlobal("fetch", fetchMock);

    const userA = bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );
    const userB = bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-b"), refresh_token: "REFRESH_USER_B" }),
      "/api/users/me/",
    );

    releaseRefresh!();
    const [, resB] = await Promise.all([userA, userB]);

    // Only one refresh round-trip happened, for USER-A's refresh token.
    const refreshCalls = fetchMock.mock.calls.filter(([url]) =>
      String(url).includes("/api/auth/jwt/refresh/"),
    );
    expect(refreshCalls).toHaveLength(1);
    expect(JSON.parse(String((refreshCalls[0][1] as any).body)).refresh).toBe("REFRESH_USER_A");

    // USER-B's upstream call carried USER-A's access token ...
    expect(authHeadersSeenUpstream).toContain("Bearer ACCESS_FOR_USER_A");

    // ... and USER-B's browser is handed USER-A's access token as a cookie.
    const setCookieB = resB.headers.get("set-cookie") ?? "";
    expect(setCookieB).toContain("access_token=ACCESS_FOR_USER_A");
  });

  it("E2E-002: the refreshed access_token cookie is written without the Secure attribute", async () => {
    const { bffFetchWithAuthFromReq } = await import("@/lib/server/bffFetch");

    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes("/api/auth/jwt/refresh/")) {
        return jsonResponse({ access: "NEW_ACCESS" });
      }
      return jsonResponse({ ok: true });
    });

    vi.stubGlobal("fetch", fetchMock);

    const res = await bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );

    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("access_token=NEW_ACCESS");
    expect(setCookie).toContain("HttpOnly");
    // Current (audited) behaviour: no Secure attribute is emitted.
    expect(setCookie.toLowerCase()).not.toContain("secure");
  });
});
