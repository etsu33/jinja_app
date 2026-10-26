// @vitest-environment node
/**
 * WS-04（MD-2 = C）: BFF の HMAC 署名付き client identity。
 * Backend 側の検証は backend/tests/test_throttle_client_identity.py。署名ベクタは両方で同じ値を固定する。
 */
import { createHmac } from "node:crypto";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import {
  CLIENT_IP_HEADER,
  CLIENT_SIG_HEADER,
  CLIENT_TS_HEADER,
  clientIdentityHeaders,
  signClientIdentity,
  trustedClientIp,
} from "@/lib/server/clientIdentity";
import { djFetch } from "@/lib/server/backend";
import { __resetRefreshInFlightForTest, bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const NOW_MS = 1_700_000_000_000;

function reqWith(headers: Record<string, string>, cookies: Record<string, string> = {}) {
  const lower = Object.fromEntries(Object.entries(headers).map(([k, v]) => [k.toLowerCase(), v]));
  return {
    method: "POST",
    headers: new Headers(lower),
    nextUrl: { protocol: "https:" },
    cookies: { get: (name: string) => (name in cookies ? { value: cookies[name] } : undefined) },
  } as any;
}

function headerValue(init: RequestInit | undefined, name: string): string | null {
  return new Headers(init?.headers as HeadersInit).get(name);
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  vi.stubEnv("DJANGO_ORIGIN", "https://backend.test");
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  __resetRefreshInFlightForTest();
});

describe("signClientIdentity", () => {
  it("matches the backend signing vector", () => {
    expect(signClientIdentity(SECRET, "1700000000", "post", "/api/concierge/chat/", CLIENT)).toBe(
      "39ca396bfa3550aa1d1a17da0df2b6dd866f339d7e47c5db9aade26fbca84857",
    );
  });
});

describe("trustedClientIp", () => {
  it("reads the Vercel-provided x-forwarded-for only on Vercel", () => {
    expect(trustedClientIp(reqWith({ "x-forwarded-for": CLIENT }))).toBe(CLIENT);
    expect(trustedClientIp(reqWith({ "x-forwarded-for": "2001:db8::1" }))).toBe("2001:db8::1");

    vi.stubEnv("VERCEL", "");
    expect(trustedClientIp(reqWith({ "x-forwarded-for": CLIENT }))).toBeNull();
  });

  it.each(["", "203.0.113.10, 10.0.0.1", "203.0.113.10 10.0.0.1", "203.0.113.10:443", "example.com", "999.1.1.1", "fe80::1%eth0"])(
    "rejects %j",
    (value) => {
      expect(trustedClientIp(reqWith({ "x-forwarded-for": value }))).toBeNull();
    },
  );

  it("does not fall back to other client-controlled headers", () => {
    expect(trustedClientIp(reqWith({ "x-real-ip": CLIENT, "cf-connecting-ip": CLIENT }))).toBeNull();
  });
});

describe("clientIdentityHeaders", () => {
  it("signs timestamp, method, path（without query）and ip", () => {
    const headers = clientIdentityHeaders(
      reqWith({ "x-forwarded-for": CLIENT }),
      "get",
      "https://backend.test/api/compass/recommendations/?limit=3",
    );
    const ts = String(NOW_MS / 1000);
    expect(headers).toEqual({
      [CLIENT_IP_HEADER]: CLIENT,
      [CLIENT_TS_HEADER]: ts,
      [CLIENT_SIG_HEADER]: createHmac("sha256", SECRET)
        .update(`${ts}\nGET\n/api/compass/recommendations/\n${CLIENT}`)
        .digest("hex"),
    });
  });

  it.each([
    ["not on Vercel", { VERCEL: "" }],
    ["no secret", { KM_CLIENT_IDENTITY_SECRET: "" }],
    ["short secret", { KM_CLIENT_IDENTITY_SECRET: "x".repeat(31) }],
  ])("adds nothing when %s", (_label, env) => {
    for (const [k, v] of Object.entries(env)) vi.stubEnv(k, v);
    expect(clientIdentityHeaders(reqWith({ "x-forwarded-for": CLIENT }), "GET", "/api/x/")).toEqual({});
  });

  it("adds nothing without a request or a valid client ip", () => {
    expect(clientIdentityHeaders(null, "GET", "/api/x/")).toEqual({});
    expect(clientIdentityHeaders(reqWith({ "x-forwarded-for": "a, b" }), "GET", "/api/x/")).toEqual({});
  });
});

describe("djFetch", () => {
  it("forwards the signed identity and never the secret", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const log = vi.spyOn(console, "log").mockImplementation(() => {});

    await djFetch(reqWith({ "x-forwarded-for": CLIENT }), "/api/concierge/chat/", { method: "POST", body: "{}" });

    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(headerValue(init, CLIENT_IP_HEADER)).toBe(CLIENT);
    expect(headerValue(init, CLIENT_SIG_HEADER)).toBe(
      signClientIdentity(SECRET, String(NOW_MS / 1000), "POST", "/api/concierge/chat/", CLIENT),
    );
    const logged = JSON.stringify(log.mock.calls);
    expect(logged).not.toContain(SECRET);
    expect(logged).not.toContain(CLIENT);
    expect(logged).not.toContain(headerValue(init, CLIENT_SIG_HEADER));
  });

  it("signs path-only calls through clientIdentityFrom without forwarding credentials", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(console, "log").mockImplementation(() => {});

    const req = reqWith({ "x-forwarded-for": CLIENT, authorization: "Bearer secret-token", cookie: "a=b" });
    await djFetch("/api/places/find/", { method: "POST", body: "{}", clientIdentityFrom: req });

    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(headerValue(init, CLIENT_IP_HEADER)).toBe(CLIENT);
    expect(headerValue(init, "authorization")).toBeNull();
    expect(headerValue(init, "cookie")).toBeNull();
    expect(init).not.toHaveProperty("clientIdentityFrom");
  });

  it("sends no identity headers outside Vercel", async () => {
    vi.stubEnv("VERCEL", "");
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(console, "log").mockImplementation(() => {});

    await djFetch(reqWith({ "x-forwarded-for": CLIENT }), "/api/concierge/chat/", { method: "POST" });

    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(headerValue(init, CLIENT_IP_HEADER)).toBeNull();
    expect(headerValue(init, CLIENT_SIG_HEADER)).toBeNull();
  });
});

describe("bffFetchWithAuthFromReq", () => {
  it("signs the upstream request and the token refresh", async () => {
    const fetchMock = vi.fn(async (url: string) =>
      String(url).includes("/api/auth/jwt/refresh/")
        ? new Response(JSON.stringify({ access: "new-access" }), { status: 200 })
        : new Response("{}", { status: 200, headers: { "content-type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(console, "log").mockImplementation(() => {});

    const req = reqWith({ "x-forwarded-for": CLIENT }, { refresh_token: "r-1" });
    await bffFetchWithAuthFromReq(req, "/api/compass/recommendations/?limit=3", { method: "GET" });

    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][];
    const ts = String(NOW_MS / 1000);
    const refresh = calls.find(([url]) => url.includes("/api/auth/jwt/refresh/"))!;
    const upstream = calls.find(([url]) => url.includes("/api/compass/recommendations/"))!;
    expect(headerValue(refresh[1], CLIENT_SIG_HEADER)).toBe(
      signClientIdentity(SECRET, ts, "POST", "/api/auth/jwt/refresh/", CLIENT),
    );
    expect(headerValue(upstream[1], CLIENT_SIG_HEADER)).toBe(
      signClientIdentity(SECRET, ts, "GET", "/api/compass/recommendations/", CLIENT),
    );
    expect(headerValue(upstream[1], "authorization")).toBe("Bearer new-access");
  });
});
