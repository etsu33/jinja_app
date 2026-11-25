// @vitest-environment node
/**
 * WS-04 B-2: Shrine 詳細 SSR（getShrineDetailServer）の client identity。
 * - Django 直行かつ Vercel 上で secret があるときだけ、ページ request の IP を署名して付ける。
 * - 自アプリ BFF 経由の fallback・Vercel 外・信頼できる IP が無いときは何も付けず、fetch の形も従来どおり。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const headersMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock() }));

const resolveServerBaseUrlMock = vi.fn();
vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrl: () => resolveServerBaseUrlMock(),
}));

import { getShrineDetailServer } from "@/lib/api/shrines.server";
import { signClientIdentity } from "@/lib/server/clientIdentity";

const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const BACKEND = "https://jinja-backend.test";
const WEB = "https://web.test";
const NOW_MS = 1_700_000_000_000;

const BACKEND_ENV_NAMES = ["DJANGO_ORIGIN", "BACKEND_ORIGIN", "DJANGO_API_BASE_URL", "BACKEND_BASE_URL", "BACKEND_URL"];

let fetchMock: ReturnType<typeof vi.fn>;

function lastFetch(): [string, RequestInit] {
  return fetchMock.mock.calls.at(-1) as unknown as [string, RequestInit];
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  for (const name of [...BACKEND_ENV_NAMES, "NEXT_PUBLIC_API_BASE_URL"]) vi.stubEnv(name, "");
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  headersMock.mockResolvedValue(new Headers({ "x-forwarded-for": CLIENT }));
  resolveServerBaseUrlMock.mockResolvedValue(WEB);
  fetchMock = vi.fn(async () => new Response(JSON.stringify({ id: 42 }), { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  headersMock.mockReset();
  resolveServerBaseUrlMock.mockReset();
});

describe("getShrineDetailServer client identity", () => {
  it("signs the page request's Vercel client ip when calling Django directly", async () => {
    vi.stubEnv("DJANGO_API_BASE_URL", BACKEND);
    vi.stubEnv("DJANGO_ORIGIN", BACKEND);

    await expect(getShrineDetailServer(42)).resolves.toEqual({ id: 42 });

    const [url, init] = lastFetch();
    expect(url).toBe(`${BACKEND}/api/shrines/42/data/`);
    expect(init.cache).toBe("no-store");
    const h = new Headers(init.headers as HeadersInit);
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Ts")).toBe(String(NOW_MS / 1000));
    expect(h.get("X-KM-Client-Sig")).toBe(
      signClientIdentity(SECRET, String(NOW_MS / 1000), "GET", "/api/shrines/42/data/", CLIENT),
    );
    expect(h.get("authorization")).toBeNull();
    expect(h.get("cookie")).toBeNull();
  });

  it.each(BACKEND_ENV_NAMES)("recognises %s as a backend origin", async (name) => {
    // base は NEXT_PUBLIC_API_BASE_URL から取り、Backend と判定する根拠を `name` 1 つだけにする
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", BACKEND);
    vi.stubEnv(name, `${BACKEND}/`);

    await getShrineDetailServer(42);

    const [url, init] = lastFetch();
    expect(url).toBe(`${BACKEND}/api/shrines/42/data/`);
    expect(new Headers(init.headers as HeadersInit).get("X-KM-Client-IP")).toBe(CLIENT);
  });

  it("does not sign the fallback request to its own BFF and adds no recursion", async () => {
    vi.stubEnv("DJANGO_ORIGIN", BACKEND);

    await getShrineDetailServer(42);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(`${WEB}/api/shrines/42/data/`, { cache: "no-store" });
    expect(headersMock).not.toHaveBeenCalled();
  });

  it("does not sign a NEXT_PUBLIC_API_BASE_URL target that is not a configured backend origin", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://elsewhere.test");
    vi.stubEnv("DJANGO_ORIGIN", BACKEND);

    await getShrineDetailServer(42);

    expect(fetchMock).toHaveBeenCalledWith("https://elsewhere.test/api/shrines/42/data/", { cache: "no-store" });
    expect(headersMock).not.toHaveBeenCalled();
  });

  it.each([
    ["outside Vercel", { VERCEL: "" }],
    ["without a secret", { KM_CLIENT_IDENTITY_SECRET: "" }],
  ])("keeps the original request %s and never reads request headers", async (_label, env) => {
    vi.stubEnv("DJANGO_API_BASE_URL", BACKEND);
    for (const [k, v] of Object.entries(env)) vi.stubEnv(k, v);

    await getShrineDetailServer(42);

    expect(fetchMock).toHaveBeenCalledWith(`${BACKEND}/api/shrines/42/data/`, { cache: "no-store" });
    expect(headersMock).not.toHaveBeenCalled();
  });

  it.each([
    ["no forwarded ip", {}],
    ["a forwarded list", { "x-forwarded-for": `${CLIENT}, 10.0.0.1` }],
    ["a malformed value", { "x-forwarded-for": "unknown" }],
    ["only other client headers", { "x-real-ip": CLIENT, "cf-connecting-ip": CLIENT }],
  ])("does not invent an identity with %s", async (_label, incoming) => {
    vi.stubEnv("DJANGO_API_BASE_URL", BACKEND);
    headersMock.mockResolvedValue(new Headers(incoming as Record<string, string>));

    await getShrineDetailServer(42);

    expect(fetchMock).toHaveBeenCalledWith(`${BACKEND}/api/shrines/42/data/`, { cache: "no-store" });
  });

  it("keeps the existing error behaviour", async () => {
    vi.stubEnv("DJANGO_API_BASE_URL", BACKEND);
    fetchMock.mockResolvedValueOnce(new Response("boom", { status: 500 }));

    await expect(getShrineDetailServer(42)).rejects.toThrow("getShrineDetailServer failed: 500 body=boom");
  });
});
