// @vitest-environment node
/**
 * FU-2-A2（P3）: 公開御朱印 SSR は自アプリ BFF を経由せず Django を直接呼び、ページ request の client identity を
 * WS-04 HMAC で署名する。表示用の正規化・件数・並び順・失敗時の [] は BFF 経由のときと同じ。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const headersMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock() }));

// 自アプリ BFF の URL 解決（request の Host / X-Forwarded-Host を使う）は呼ばれてはならない
const resolveServerBaseUrlMock = vi.fn(async () => {
  throw new Error("resolveServerBaseUrl must not be used");
});
vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrl: () => resolveServerBaseUrlMock(),
  resolveServerBaseUrlFromHeaders: () => {
    throw new Error("resolveServerBaseUrlFromHeaders must not be used");
  },
}));

import { fetchPublicGoshuinsForShrineServer } from "@/lib/api/publicGoshuins.server";
import { signClientIdentity } from "@/lib/server/clientIdentity";

const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const BACKEND = "https://jinja-backend.test";
const NOW_MS = 1_700_000_000_000;
const TS = String(NOW_MS / 1000);
const BACKEND_ENV_NAMES = ["DJANGO_ORIGIN", "BACKEND_ORIGIN", "DJANGO_API_BASE_URL", "BACKEND_BASE_URL", "BACKEND_URL"];

let fetchMock: ReturnType<typeof vi.fn>;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function lastFetch(): [string, RequestInit] {
  return fetchMock.mock.calls.at(-1) as unknown as [string, RequestInit];
}

function sentHeaders(): Headers {
  return new Headers(lastFetch()[1].headers as HeadersInit);
}

function pageHeaders(extra: Record<string, string> = {}): Headers {
  return new Headers({ "x-forwarded-for": CLIENT, host: "attacker.test", "x-forwarded-host": "attacker.test", ...extra });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  for (const name of [...BACKEND_ENV_NAMES, "NEXT_PUBLIC_API_BASE_URL", "WEB_BASE_URL"]) vi.stubEnv(name, "");
  vi.stubEnv("DJANGO_ORIGIN", BACKEND);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  headersMock.mockResolvedValue(pageHeaders());
  fetchMock = vi.fn(async () => jsonResponse([]));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  headersMock.mockReset();
  resolveServerBaseUrlMock.mockClear();
});

describe("destination", () => {
  it("calls the configured Django origin directly, not its own BFF or the request host", async () => {
    await fetchPublicGoshuinsForShrineServer(7);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = lastFetch();
    expect(url).toBe(`${BACKEND}/api/goshuins/?is_public=true&shrine=7`);
    expect(url).not.toContain("attacker.test");
    expect(url).not.toContain("/api/public/goshuins");
    expect(init.method).toBe("GET");
    expect(init.cache).toBe("no-store");
    expect(resolveServerBaseUrlMock).not.toHaveBeenCalled();
  });

  it("falls back to BACKEND_ORIGIN like the BFF route（getDjangoOrigin）", async () => {
    vi.stubEnv("DJANGO_ORIGIN", "");
    vi.stubEnv("BACKEND_ORIGIN", `${BACKEND}/`);

    await fetchPublicGoshuinsForShrineServer(7);

    expect(lastFetch()[0]).toBe(`${BACKEND}/api/goshuins/?is_public=true&shrine=7`);
    expect(sentHeaders().get("X-KM-Client-IP")).toBe(CLIENT);
  });

  it.each([0, Number.NaN])("does not call the Backend without a shrine id（%s）", async (id) => {
    await expect(fetchPublicGoshuinsForShrineServer(id)).resolves.toEqual([]);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("client identity", () => {
  it("signs the page request's Vercel client ip for the exact method and pathname Django receives", async () => {
    await fetchPublicGoshuinsForShrineServer(7);

    const [url] = lastFetch();
    const h = sentHeaders();
    const signedPath = new URL(url).pathname;
    expect(signedPath).toBe("/api/goshuins/");
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Ts")).toBe(TS);
    expect(h.get("X-KM-Client-Sig")).toBe(signClientIdentity(SECRET, TS, "GET", signedPath, CLIENT));
    expect(h.get("Accept")).toBe("application/json");
    expect(h.get("authorization")).toBeNull();
    expect(h.get("cookie")).toBeNull();
    expect(headersMock).toHaveBeenCalledTimes(1);
  });

  it.each([
    ["no x-forwarded-for", new Headers({ host: "web.test" })],
    ["a forwarded list", new Headers({ "x-forwarded-for": `${CLIENT}, 198.51.100.7` })],
    ["a value with a port", new Headers({ "x-forwarded-for": `${CLIENT}:443` })],
    ["a non-ip value", new Headers({ "x-forwarded-for": "not-an-ip" })],
  ])("sends no identity headers for %s, and still fetches", async (_label, h) => {
    headersMock.mockResolvedValue(h);

    await fetchPublicGoshuinsForShrineServer(7);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    for (const name of ["X-KM-Client-IP", "X-KM-Client-Ts", "X-KM-Client-Sig"]) expect(sentHeaders().get(name)).toBeNull();
  });

  it.each([
    ["off Vercel", { VERCEL: "" }],
    ["without a secret", { KM_CLIENT_IDENTITY_SECRET: "" }],
    ["with a short secret", { KM_CLIENT_IDENTITY_SECRET: "short" }],
    ["when the origin is not a configured Backend origin（local default）", { DJANGO_ORIGIN: "" }],
  ])("does not read headers() or sign %s", async (_label, env) => {
    for (const [k, v] of Object.entries(env)) vi.stubEnv(k, v);

    await fetchPublicGoshuinsForShrineServer(7);

    expect(headersMock).not.toHaveBeenCalled();
    expect(sentHeaders().get("X-KM-Client-Sig")).toBeNull();
  });

  it("continues unsigned when headers() is unavailable", async () => {
    headersMock.mockRejectedValue(new Error("outside request scope"));

    await fetchPublicGoshuinsForShrineServer(7);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sentHeaders().get("X-KM-Client-Sig")).toBeNull();
  });

  it("never forwards browser-supplied X-KM-* headers", async () => {
    const spoofed = {
      "x-km-client-ip": "192.0.2.99",
      "x-km-client-ts": "1",
      "x-km-client-sig": "f".repeat(64),
    };

    headersMock.mockResolvedValue(pageHeaders(spoofed));
    await fetchPublicGoshuinsForShrineServer(7);
    let h = sentHeaders();
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Ts")).toBe(TS);
    expect(h.get("X-KM-Client-Sig")).toBe(signClientIdentity(SECRET, TS, "GET", "/api/goshuins/", CLIENT));

    // 信頼できる x-forwarded-for が無いときも、偽装値は転送されない
    headersMock.mockResolvedValue(new Headers(spoofed));
    await fetchPublicGoshuinsForShrineServer(7);
    h = sentHeaders();
    for (const name of ["X-KM-Client-IP", "X-KM-Client-Ts", "X-KM-Client-Sig"]) expect(h.get(name)).toBeNull();
  });
});

describe("response handling（unchanged UI contract）", () => {
  it("keeps Backend order, the first 12 items and the existing item shape", async () => {
    const rows = Array.from({ length: 20 }, (_, i) => ({ id: 100 - i, title: `t${i}`, created_at: `2026-10-${10 + (i % 9)}`, image_url: `https://cdn.test/${i}.jpg` }));
    fetchMock.mockResolvedValueOnce(jsonResponse(rows));

    const items = await fetchPublicGoshuinsForShrineServer(7);

    expect(items).toHaveLength(12);
    expect(items.map((g) => g.id)).toEqual(rows.slice(0, 12).map((r) => r.id));
    expect(items[0]).toEqual({ id: 100, title: "t0", created_at: "2026-10-10", image_url: "https://cdn.test/0.jpg" });
  });

  it("normalizes relative and local Backend media URLs to the Backend origin", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse([
        { id: 1, image_url: "/media/a.jpg" },
        { id: 2, image_url: "http://127.0.0.1:8000/media/b.jpg" },
        { id: 3, image_url: "http://localhost:8000/media/c.jpg" },
        { id: 4, image_url: "https://cdn.test/d.jpg" },
        { id: 5, image_url: "  ", images: [{ image: "https://cdn.test/e.jpg" }] },
        { id: 6 },
      ]),
    );

    const items = await fetchPublicGoshuinsForShrineServer(7);

    expect(items.map((g) => g.image_url)).toEqual([
      `${BACKEND}/media/a.jpg`,
      `${BACKEND}/media/b.jpg`,
      `${BACKEND}/media/c.jpg`,
      "https://cdn.test/d.jpg",
      "https://cdn.test/e.jpg",
      null,
    ]);
    expect(items[5]).toEqual({ id: 6, title: null, created_at: null, image_url: null });
  });

  it("accepts a paginated { results } body and drops items without a numeric id", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ count: 3, results: [{ id: 1 }, { id: "x" }, { id: "3" }] }));

    const items = await fetchPublicGoshuinsForShrineServer(7);

    expect(items.map((g) => g.id)).toEqual([1, 3]);
  });

  it.each([
    ["an empty list", jsonResponse([])],
    ["an unexpected body", jsonResponse({ detail: "x" })],
    ["401", jsonResponse({ detail: "unauthorized" }, 401)],
    ["429", jsonResponse({ detail: "throttled" }, 429)],
    ["500", jsonResponse({ detail: "boom" }, 500)],
    ["a non-JSON body", new Response("<html>oops</html>", { status: 200, headers: { "content-type": "text/html" } })],
    ["invalid JSON", new Response("{not json", { status: 200, headers: { "content-type": "application/json" } })],
  ])("returns [] for %s", async (_label, response) => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.spyOn(console, "log").mockImplementation(() => {});
    fetchMock.mockResolvedValueOnce(response);

    await expect(fetchPublicGoshuinsForShrineServer(7)).resolves.toEqual([]);
  });

  it("returns [] on a network failure", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    await expect(fetchPublicGoshuinsForShrineServer(7)).resolves.toEqual([]);
  });
});

describe("logging", () => {
  it("never logs the secret, the client ip, the signature or the Backend URL", async () => {
    const logs: unknown[] = [];
    vi.spyOn(console, "log").mockImplementation((...args) => void logs.push(args));
    vi.spyOn(console, "error").mockImplementation((...args) => void logs.push(args));
    vi.spyOn(console, "warn").mockImplementation((...args) => void logs.push(args));

    fetchMock.mockResolvedValueOnce(jsonResponse([{ id: 1 }]));
    await fetchPublicGoshuinsForShrineServer(7);
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "throttled" }, 429));
    await fetchPublicGoshuinsForShrineServer(7);
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    await fetchPublicGoshuinsForShrineServer(7);

    const text = JSON.stringify(logs);
    expect(logs.length).toBeGreaterThan(0);
    const signature = signClientIdentity(SECRET, TS, "GET", "/api/goshuins/", CLIENT);
    for (const secretish of [SECRET, CLIENT, signature, BACKEND]) expect(text).not.toContain(secretish);
  });
});
