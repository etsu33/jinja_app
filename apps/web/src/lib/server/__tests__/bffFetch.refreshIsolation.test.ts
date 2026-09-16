/**
 * Regression tests for the BFF token-refresh identity boundary.
 *
 * These pin the guarantees introduced by PR-A (auth refresh isolation) against
 * the findings recorded in docs/audit/beta-core-flow-e2e-audit.md:
 *
 *   E2E-001  in-flight refresh dedup must be scoped per refresh token, so two
 *            concurrent users never share a refresh result, an Authorization
 *            header, or a Set-Cookie value.
 *   E2E-002  refreshed auth cookies must carry the same attribute contract as
 *            /api/auth/login, including `Secure`.
 *   E2E-023  an upstream 403 is an authorization decision, not an expired
 *            token, so it must not trigger refresh + retry.
 *
 * The suite deliberately imports `bffFetch` ONCE at module scope: the bug being
 * guarded against lives in module-scope state, so every test must share the
 * same module instance for these assertions to mean anything.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

vi.mock("@/lib/server/backend", () => ({
  getDjangoOrigin: () => "http://backend.test",
}));

import { __resetRefreshInFlightForTest, bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

const REFRESH_URL = "/api/auth/jwt/refresh/";

type CookieJar = Record<string, string>;

function makeReq(cookies: CookieJar, extraHeaders: Record<string, string> = {}) {
  const cookieHeader = Object.entries(cookies)
    .map(([k, v]) => `${k}=${v}`)
    .join("; ");

  const headers: Record<string, string> = {
    ...(cookieHeader ? { cookie: cookieHeader } : {}),
    ...extraHeaders,
  };

  return {
    headers: {
      get: (name: string) => headers[name.toLowerCase()] ?? null,
    },
    nextUrl: { protocol: "http:" },
    cookies: {
      get: (name: string) => (name in cookies ? { value: cookies[name] } : undefined),
      has: (name: string) => name in cookies,
    },
  } as any;
}

/** A JWT whose `exp` is already in the past, so the pre-refresh path is taken. */
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

function isRefreshCall(url: unknown): boolean {
  return String(url).includes(REFRESH_URL);
}

function readRefreshTokenFromCall(init: any): string {
  return JSON.parse(String(init.body)).refresh;
}

/** Explicit release gates so the concurrency window is deterministic, not timing-based. */
function createGate() {
  let release!: () => void;
  const promise = new Promise<void>((resolve) => {
    release = resolve;
  });
  return { promise, release };
}

describe("bffFetchWithAuthFromReq — refresh identity isolation", () => {
  beforeEach(() => {
    __resetRefreshInFlightForTest();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("E2E-001: two concurrent users never share a refresh result, header, or cookie", async () => {
    const gate = createGate();

    const upstreamAuthByToken = new Map<string, string | null>();

    const fetchMock = vi.fn(async (url: string, init: any) => {
      if (isRefreshCall(url)) {
        // Hold both refreshes open at the same time: this is exactly the window
        // in which the old module-scope singleton handed A's token to B.
        await gate.promise;
        const refresh = readRefreshTokenFromCall(init);
        return jsonResponse({ access: `ACCESS_FOR_${refresh}` });
      }

      const auth = init?.headers?.Authorization ?? null;
      // Correlate each upstream call back to the caller via its own cookie header.
      const cookie = String(init?.headers?.Cookie ?? "");
      const owner = cookie.includes("REFRESH_USER_A") ? "A" : "B";
      upstreamAuthByToken.set(owner, auth);
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

    gate.release();
    const [resA, resB] = await Promise.all([userA, userB]);

    // Each identity performed its own refresh round-trip.
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => isRefreshCall(url));
    expect(refreshCalls).toHaveLength(2);
    expect(refreshCalls.map(([, init]) => readRefreshTokenFromCall(init)).sort()).toEqual([
      "REFRESH_USER_A",
      "REFRESH_USER_B",
    ]);

    // Each upstream call carried its own access token.
    expect(upstreamAuthByToken.get("A")).toBe("Bearer ACCESS_FOR_REFRESH_USER_A");
    expect(upstreamAuthByToken.get("B")).toBe("Bearer ACCESS_FOR_REFRESH_USER_B");

    // Each response Set-Cookie carried its own access token, and only its own.
    const setCookieA = resA.headers.get("set-cookie") ?? "";
    const setCookieB = resB.headers.get("set-cookie") ?? "";

    expect(setCookieA).toContain("access_token=ACCESS_FOR_REFRESH_USER_A");
    expect(setCookieA).not.toContain("ACCESS_FOR_REFRESH_USER_B");

    expect(setCookieB).toContain("access_token=ACCESS_FOR_REFRESH_USER_B");
    expect(setCookieB).not.toContain("ACCESS_FOR_REFRESH_USER_A");
  });

  it("keeps same-identity dedup: concurrent requests sharing one refresh token refresh once", async () => {
    const gate = createGate();

    const fetchMock = vi.fn(async (url: string) => {
      if (isRefreshCall(url)) {
        await gate.promise;
        return jsonResponse({ access: "SHARED_NEW_ACCESS" });
      }
      return jsonResponse({ ok: true });
    });

    vi.stubGlobal("fetch", fetchMock);

    const first = bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );
    const second = bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/favorites/",
    );

    gate.release();
    const [resFirst, resSecond] = await Promise.all([first, second]);

    expect(fetchMock.mock.calls.filter(([url]) => isRefreshCall(url))).toHaveLength(1);
    expect(resFirst.headers.get("set-cookie") ?? "").toContain("access_token=SHARED_NEW_ACCESS");
    expect(resSecond.headers.get("set-cookie") ?? "").toContain("access_token=SHARED_NEW_ACCESS");
  });

  it("a failed refresh for one identity does not contaminate another identity", async () => {
    const gate = createGate();

    const fetchMock = vi.fn(async (url: string, init: any) => {
      if (isRefreshCall(url)) {
        await gate.promise;
        const refresh = readRefreshTokenFromCall(init);
        // USER-A's refresh token is revoked; USER-B's is healthy.
        if (refresh === "REFRESH_USER_A") return jsonResponse({ detail: "token_not_valid" }, 401);
        return jsonResponse({ access: "ACCESS_FOR_USER_B" });
      }

      const auth = init?.headers?.Authorization ?? null;
      if (!auth) return jsonResponse({ detail: "unauthenticated" }, 401);
      return jsonResponse({ ok: true, auth });
    });

    vi.stubGlobal("fetch", fetchMock);

    const userA = bffFetchWithAuthFromReq(
      makeReq({ refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );
    const userB = bffFetchWithAuthFromReq(
      makeReq({ refresh_token: "REFRESH_USER_B" }),
      "/api/users/me/",
    );

    gate.release();
    const [resA, resB] = await Promise.all([userA, userB]);

    // A has no usable token: it stays unauthenticated and is never handed B's.
    expect(resA.status).toBe(401);
    expect(resA.headers.get("set-cookie") ?? "").not.toContain("ACCESS_FOR_USER_B");

    // B is unaffected by A's failure.
    expect(resB.status).toBe(200);
    expect(resB.headers.get("set-cookie") ?? "").toContain("access_token=ACCESS_FOR_USER_B");
  });

  it("does not cache a failed refresh: the same identity retries on the next request", async () => {
    let refreshAttempts = 0;

    const fetchMock = vi.fn(async (url: string) => {
      if (isRefreshCall(url)) {
        refreshAttempts += 1;
        if (refreshAttempts === 1) return jsonResponse({ detail: "upstream hiccup" }, 503);
        return jsonResponse({ access: "RECOVERED_ACCESS" });
      }
      return jsonResponse({ ok: true });
    });

    vi.stubGlobal("fetch", fetchMock);

    const failed = await bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );
    expect(failed.headers.get("set-cookie") ?? "").not.toContain("access_token=");

    const recovered = await bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );

    expect(refreshAttempts).toBe(2);
    expect(recovered.headers.get("set-cookie") ?? "").toContain("access_token=RECOVERED_ACCESS");
  });
});

describe("bffFetchWithAuthFromReq — refreshed cookie contract", () => {
  beforeEach(() => {
    __resetRefreshInFlightForTest();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  function stubRefreshOk() {
    const fetchMock = vi.fn(async (url: string) => {
      if (isRefreshCall(url)) return jsonResponse({ access: "NEW_ACCESS" });
      return jsonResponse({ ok: true });
    });
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("E2E-002: production + https refresh emits Secure, matching /api/auth/login", async () => {
    vi.stubEnv("NODE_ENV", "production");
    stubRefreshOk();

    const res = await bffFetchWithAuthFromReq(
      makeReq(
        { access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" },
        { "x-forwarded-proto": "https" },
      ),
      "/api/users/me/",
    );

    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("access_token=NEW_ACCESS");
    expect(setCookie).toMatch(/;\s*Secure/i);
    expect(setCookie).toMatch(/;\s*HttpOnly/i);
    expect(setCookie).toMatch(/;\s*SameSite=lax/i);
    expect(setCookie).toContain("Path=/");
    expect(setCookie).toContain(`Max-Age=${60 * 60}`);
  });

  it("stays non-Secure outside production, so local http development still works", async () => {
    stubRefreshOk();

    const res = await bffFetchWithAuthFromReq(
      makeReq({ access_token: expiredJwt("user-a"), refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );

    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("access_token=NEW_ACCESS");
    expect(setCookie).not.toMatch(/;\s*Secure/i);
    expect(setCookie).toMatch(/;\s*HttpOnly/i);
  });
});

describe("bffFetchWithAuthFromReq — retry policy", () => {
  beforeEach(() => {
    __resetRefreshInFlightForTest();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("keeps 401 -> refresh -> retry intact", async () => {
    let upstreamCalls = 0;

    const fetchMock = vi.fn(async (url: string, init: any) => {
      if (isRefreshCall(url)) return jsonResponse({ access: "RETRY_ACCESS" });

      upstreamCalls += 1;
      if (upstreamCalls === 1) return jsonResponse({ detail: "token expired" }, 401);
      return jsonResponse({ ok: true, auth: init?.headers?.Authorization ?? null });
    });

    vi.stubGlobal("fetch", fetchMock);

    // A live access token, so the pre-refresh path is skipped and the retry is
    // driven purely by the upstream 401.
    const stillValid = `${Buffer.from(JSON.stringify({ alg: "HS256" })).toString("base64url")}.${Buffer.from(
      JSON.stringify({ sub: "user-a", exp: Math.floor(Date.now() / 1000) + 3600 }),
    ).toString("base64url")}.sig`;

    const res = await bffFetchWithAuthFromReq(
      makeReq({ access_token: stillValid, refresh_token: "REFRESH_USER_A" }),
      "/api/users/me/",
    );

    expect(upstreamCalls).toBe(2);
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toMatchObject({ auth: "Bearer RETRY_ACCESS" });
    expect(res.headers.get("set-cookie") ?? "").toContain("access_token=RETRY_ACCESS");
  });

  it("E2E-023: an upstream 403 does not trigger refresh or retry", async () => {
    let upstreamCalls = 0;

    const fetchMock = vi.fn(async (url: string) => {
      if (isRefreshCall(url)) return jsonResponse({ access: "SHOULD_NOT_BE_ISSUED" });

      upstreamCalls += 1;
      return jsonResponse({ detail: "permission denied" }, 403);
    });

    vi.stubGlobal("fetch", fetchMock);

    const stillValid = `${Buffer.from(JSON.stringify({ alg: "HS256" })).toString("base64url")}.${Buffer.from(
      JSON.stringify({ sub: "user-a", exp: Math.floor(Date.now() / 1000) + 3600 }),
    ).toString("base64url")}.sig`;

    const res = await bffFetchWithAuthFromReq(
      makeReq({ access_token: stillValid, refresh_token: "REFRESH_USER_A" }),
      "/api/concierge/score-v3/dashboard/",
    );

    expect(upstreamCalls).toBe(1);
    expect(fetchMock.mock.calls.filter(([url]) => isRefreshCall(url))).toHaveLength(0);
    expect(res.status).toBe(403);
    expect(res.headers.get("set-cookie") ?? "").not.toContain("access_token=");
  });
});
