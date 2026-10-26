// @vitest-environment node
/**
 * WS-04 認証成功・失敗の回帰監査（PR #3354）: BFF の Shrine meaning / Billing status。
 * upstream はすべて mock。本番アカウント・課金データは使わない。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { GET as billingGET } from "@/app/api/billings/status/route";
import { GET as meaningGET } from "@/app/api/shrines/[id]/meaning/route";
import { signClientIdentity } from "@/lib/server/clientIdentity";
import { __resetRefreshInFlightForTest } from "@/lib/server/bffFetch";

const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const BACKEND = "https://backend.test";
const NOW_MS = 1_700_000_000_000;
const NOW_S = NOW_MS / 1000;
const MEANING_PATH = "/api/shrines/42/meaning/";
const BILLING_PATH = "/api/billings/status/";
const REFRESH_PATH = "/api/auth/jwt/refresh/";

function jwt(sub: string, expOffsetSec: number): string {
  const enc = (v: unknown) => Buffer.from(JSON.stringify(v)).toString("base64url");
  return `${enc({ alg: "HS256", typ: "JWT" })}.${enc({ sub, exp: NOW_S + expOffsetSec })}.sig-${sub}`;
}

const ACCESS_VALID = jwt("access-valid", 3600);
const ACCESS_EXPIRED = jwt("access-expired", -3600);
const REFRESH = "refresh-token-value-ws04";
const NEW_ACCESS = jwt("access-new", 3600);

function makeReq(path: string, cookies: Record<string, string> = {}, extra: Record<string, string> = {}) {
  const cookieHeader = Object.entries(cookies)
    .map(([k, v]) => `${k}=${v}`)
    .join("; ");
  const headers = new Headers({ "x-forwarded-for": CLIENT, ...extra, ...(cookieHeader ? { cookie: cookieHeader } : {}) });
  return {
    method: "GET",
    url: `https://web.test${path}`,
    headers,
    nextUrl: { protocol: "https:", pathname: path },
    cookies: { get: (name: string) => (name in cookies ? { value: cookies[name] } : undefined) },
  } as any;
}

type Upstream = (url: string, init: RequestInit) => Response | Promise<Response>;
let fetchMock: ReturnType<typeof vi.fn>;
let logs: unknown[][];

function useUpstream(handler: Upstream) {
  fetchMock = vi.fn(async (url: string, init: RequestInit) => handler(String(url), init));
  vi.stubGlobal("fetch", fetchMock);
}

function calls(pathPart: string): [string, RequestInit][] {
  return (fetchMock.mock.calls as unknown as [string, RequestInit][]).filter(([u]) => u.includes(pathPart));
}

function hdr(init: RequestInit, name: string) {
  return new Headers(init.headers as HeadersInit).get(name);
}

function json(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
}

const meaningCtx = { params: Promise.resolve({ id: "42" }) };
const BILLING_BODY = {
  plan: "premium",
  is_active: true,
  provider: "stripe",
  current_period_end: "2026-11-24T00:00:00Z",
  trial_ends_at: null,
  cancel_at_period_end: false,
};

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  vi.stubEnv("DJANGO_ORIGIN", BACKEND);
  vi.stubEnv("NEXT_PUBLIC_FORCE_BILLING_PLAN", "");
  logs = [];
  for (const level of ["log", "info", "warn", "error", "debug"] as const) {
    vi.spyOn(console, level).mockImplementation((...args: unknown[]) => {
      logs.push(args);
    });
  }
  __resetRefreshInFlightForTest();
});

afterEach(() => {
  // W8: どのケースでも token・署名・secret・client IP をログに出さない
  const text = JSON.stringify(logs);
  for (const value of [ACCESS_VALID, ACCESS_EXPIRED, NEW_ACCESS, REFRESH, SECRET, CLIENT]) {
    expect(text).not.toContain(value);
  }
  for (const [, init] of (fetchMock?.mock.calls ?? []) as unknown as [string, RequestInit][]) {
    const sig = hdr(init, "X-KM-Client-Sig");
    if (sig) expect(text).not.toContain(sig);
  }
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe.each([
  ["meaning", MEANING_PATH],
  ["billing", BILLING_PATH],
] as const)("%s", (name, upstreamPath) => {
  it("W1: forwards a valid access token and the signed client identity", async () => {
    useUpstream(() => json(name === "meaning" ? { ok: true } : BILLING_BODY));
    const res = await call(name, { access_token: ACCESS_VALID });

    expect(res.status).toBe(200);
    const [[url, init]] = calls(upstreamPath);
    expect(url).toBe(`${BACKEND}${upstreamPath}`);
    expect(hdr(init, "authorization")).toBe(`Bearer ${ACCESS_VALID}`);
    expect(hdr(init, "X-KM-Client-IP")).toBe(CLIENT);
    expect(hdr(init, "X-KM-Client-Sig")).toBe(signClientIdentity(SECRET, String(NOW_S), "GET", upstreamPath, CLIENT));
    expect(calls(REFRESH_PATH)).toHaveLength(0);
    // W8 の検査対象になるログが実際に取れていること
    expect(JSON.stringify(logs)).toContain("BFF_UPSTREAM");
  });

  it("W2: an expired access token with a valid refresh token uses the refresh path", async () => {
    useUpstream((url, init) => {
      if (url.includes(REFRESH_PATH)) return json({ access: NEW_ACCESS });
      return hdr(init, "authorization") === `Bearer ${NEW_ACCESS}`
        ? json(name === "meaning" ? { ok: true } : BILLING_BODY)
        : json({ code: "token_not_valid" }, 401);
    });
    const res = await call(name, { access_token: ACCESS_EXPIRED, refresh_token: REFRESH });

    expect(res.status).toBe(200);
    const refresh = calls(REFRESH_PATH);
    expect(refresh).toHaveLength(1);
    expect(hdr(refresh[0][1], "X-KM-Client-Sig")).toBe(
      signClientIdentity(SECRET, String(NOW_S), "POST", REFRESH_PATH, CLIENT),
    );
    const upstream = calls(upstreamPath);
    expect(upstream).toHaveLength(1);
    expect(hdr(upstream[0][1], "authorization")).toBe(`Bearer ${NEW_ACCESS}`);

    const setCookie = res.headers.get("set-cookie") ?? "";
    if (name === "meaning") {
      expect(setCookie).toContain("access_token=");
    } else {
      // 既存挙動（PR #3354 以前から）: billing route は新しい NextResponse を作り直すため、
      // refresh した access_token の Set-Cookie をブラウザへ返さない。
      expect(setCookie).not.toContain("access_token=");
    }
  });

  it("W3: a failed refresh never yields an authenticated principal", async () => {
    useUpstream((url, init) => {
      if (url.includes(REFRESH_PATH)) return json({ detail: "invalid" }, 401);
      return hdr(init, "authorization") ? json({ code: "token_not_valid" }, 401) : json({ ok: "anonymous" });
    });
    const res = await call(name, { access_token: ACCESS_EXPIRED, refresh_token: REFRESH });

    for (const [, init] of calls(upstreamPath)) {
      expect(hdr(init, "authorization")).toBe(`Bearer ${ACCESS_EXPIRED}`);
    }
    expect(res.headers.get("set-cookie") ?? "").not.toContain("access_token=");
    // 既存挙動: 事前 refresh の失敗後、upstream 401 でもう一度 refresh を試みる（計 2 回）
    expect(calls(REFRESH_PATH)).toHaveLength(2);
    if (name === "meaning") {
      expect(res.status).toBe(401);
    } else {
      expect(res.status).toBe(200);
      expect(res.headers.get("x-billing-stub")).toBe("1");
      expect(await res.json()).toMatchObject({ plan: "free", is_active: false, provider: "stub" });
    }
  });

  it("W4: client-supplied X-KM headers are never forwarded as identity", async () => {
    useUpstream(() => json(name === "meaning" ? { ok: true } : BILLING_BODY));
    const forged = { "x-km-client-ip": "198.51.100.77", "x-km-client-ts": String(NOW_S), "x-km-client-sig": "f".repeat(64) };

    await call(name, {}, forged);
    let [[, init]] = calls(upstreamPath);
    expect(hdr(init, "X-KM-Client-IP")).toBe(CLIENT);
    expect(hdr(init, "X-KM-Client-Sig")).not.toBe("f".repeat(64));

    vi.stubEnv("VERCEL", "");
    fetchMock.mockClear();
    await call(name, {}, forged);
    [[, init]] = calls(upstreamPath);
    expect(hdr(init, "X-KM-Client-IP")).toBeNull();
    expect(hdr(init, "X-KM-Client-Sig")).toBeNull();
  });

  it("W5: upstream 401", async () => {
    useUpstream(() => json({ code: "token_not_valid" }, 401));
    const res = await call(name, { access_token: ACCESS_VALID });

    expect(calls(REFRESH_PATH)).toHaveLength(0);
    if (name === "meaning") {
      expect(res.status).toBe(401);
      expect(await res.json()).toEqual({ code: "token_not_valid" });
    } else {
      // 既存挙動: 401 を HTTP 200 の free stub に置き換える（x-billing-stub: 1 のみが手掛かり）
      expect(res.status).toBe(200);
      expect(res.headers.get("x-billing-stub")).toBe("1");
      expect(await res.json()).toMatchObject({ plan: "free", provider: "stub" });
    }
  });

  it("W6: upstream 429", async () => {
    useUpstream(() => json({ detail: "Request was throttled." }, 429, { "retry-after": "17" }));
    const res = await call(name, {});

    if (name === "meaning") {
      expect(res.status).toBe(429);
      expect(await res.json()).toEqual({ detail: "Request was throttled." });
      // 既存挙動: bffFetch は content-type と set-cookie だけを写すため Retry-After は落ちる
      expect(res.headers.get("retry-after")).toBeNull();
    } else {
      // 既存挙動: 429 も HTTP 200 の free stub に置き換える
      expect(res.status).toBe(200);
      expect(res.headers.get("x-billing-stub")).toBe("1");
    }
  });
});

describe("billing status fallback (W7)", () => {
  it.each([
    [500, "server error"],
    [503, "unavailable"],
  ])("upstream %i is reported only through x-billing-stub", async (status) => {
    useUpstream(() => json({ detail: "boom" }, status));
    const res = await billingGET(makeReqFor(BILLING_PATH));
    expect(res.status).toBe(200);
    expect(res.headers.get("x-billing-stub")).toBe("1");
    expect(await res.json()).toEqual({
      plan: "free",
      is_active: false,
      provider: "stub",
      current_period_end: null,
      trial_ends_at: null,
      cancel_at_period_end: false,
    });
  });

  it("a non-JSON 200 also becomes the stub", async () => {
    useUpstream(() => new Response("<html>", { status: 200, headers: { "content-type": "text/html" } }));
    const res = await billingGET(makeReqFor(BILLING_PATH));
    expect(res.status).toBe(200);
    expect(res.headers.get("x-billing-stub")).toBe("1");
  });

  it("a successful upstream is passed through without the stub marker", async () => {
    useUpstream(() => json(BILLING_BODY));
    const res = await billingGET(makeReqFor(BILLING_PATH));
    expect(res.headers.get("x-billing-stub")).toBeNull();
    expect(await res.json()).toEqual(BILLING_BODY);
  });
});

let pendingCookies: Record<string, string> = {};
let pendingExtra: Record<string, string> = {};

function makeReqFor(path: string) {
  return makeReq(path, pendingCookies, pendingExtra);
}

async function call(name: string, cookies: Record<string, string>, extra: Record<string, string> = {}) {
  pendingCookies = cookies;
  pendingExtra = extra;
  return name === "meaning" ? meaningGET(makeReqFor(MEANING_PATH), meaningCtx) : billingGET(makeReqFor(BILLING_PATH));
}
