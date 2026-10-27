// @vitest-environment node
/**
 * FU-2-P2: Shrine Meaning SSR。
 * - auth context（Authorization / access_token / refresh_token）が無い request だけ Django を直接呼び、Cookie / Authorization を
 *   付けず、ページ request の client identity を WS-04 HMAC で署名する。
 * - auth context がある request は従来どおり自アプリ BFF を経由する（Premium 判定は Backend のまま）。
 * - 検証・null fallback は従来どおり。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const headersMock = vi.fn();
const cookiesMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock(), cookies: () => cookiesMock() }));

const resolveServerBaseUrlMock = vi.fn();
vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrl: () => resolveServerBaseUrlMock(),
}));

import { fetchShrineMeaningPayloadV2Server } from "@/lib/api/shrineMeaning.server";
import { signClientIdentity } from "@/lib/server/clientIdentity";

const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const BACKEND = "https://jinja-backend.test";
const WEB = "https://web.test";
const NOW_MS = 1_700_000_000_000;
const TS = String(NOW_MS / 1000);
const PATH = "/api/shrines/7/meaning/";
const BACKEND_ENV_NAMES = ["DJANGO_ORIGIN", "BACKEND_ORIGIN", "DJANGO_API_BASE_URL", "BACKEND_BASE_URL", "BACKEND_URL"];

const VALID_PAYLOAD = {
  version: "v2",
  source: { shrineId: 7, nameJp: "例の神社", historyTheme: "再出発", interpretationProfile: null, translationResult: null },
  generated: {
    heroMeaningCopy: "hero",
    consultationSummary: "summary",
    shrineMeaning: "meaning",
    actionMeaning: "",
    historyContext: null,
  },
  display: { blocks: [{ id: "hero", title: "t", body: "b", access: "anonymous" }], fallbackMessage: null },
};

/** cookies() の最小実装（has / toString だけを使う）。 */
function cookieStore(raw: Record<string, string>) {
  return {
    has: (name: string) => Object.prototype.hasOwnProperty.call(raw, name),
    toString: () =>
      Object.entries(raw)
        .map(([k, v]) => `${k}=${v}`)
        .join("; "),
  };
}

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

function page(headers: Record<string, string> = {}, cookies: Record<string, string> = {}) {
  headersMock.mockResolvedValue(new Headers({ "x-forwarded-for": CLIENT, host: "attacker.test", ...headers }));
  cookiesMock.mockResolvedValue(cookieStore(cookies));
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  for (const name of [...BACKEND_ENV_NAMES, "NEXT_PUBLIC_API_BASE_URL"]) vi.stubEnv(name, "");
  vi.stubEnv("DJANGO_ORIGIN", BACKEND);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  resolveServerBaseUrlMock.mockResolvedValue(WEB);
  page();
  fetchMock = vi.fn(async () => jsonResponse(VALID_PAYLOAD));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  headersMock.mockReset();
  cookiesMock.mockReset();
  resolveServerBaseUrlMock.mockReset();
});

describe("anonymous request（no auth context）→ Django directly", () => {
  it("calls the configured Django origin, not its own BFF or the request host", async () => {
    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toEqual(VALID_PAYLOAD);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = lastFetch();
    expect(url).toBe(`${BACKEND}${PATH}`);
    expect(url).not.toContain("attacker.test");
    expect(init.method).toBe("GET");
    expect(init.cache).toBe("no-store");
    expect(resolveServerBaseUrlMock).not.toHaveBeenCalled();
  });

  it("signs the page request's client ip for exactly GET + the Django pathname", async () => {
    await fetchShrineMeaningPayloadV2Server(7);

    const h = sentHeaders();
    expect(new URL(lastFetch()[0]).pathname).toBe(PATH);
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Ts")).toBe(TS);
    expect(h.get("X-KM-Client-Sig")).toBe(signClientIdentity(SECRET, TS, "GET", PATH, CLIENT));
    expect(h.get("Accept")).toBe("application/json");
  });

  it("never forwards cookies or bearer tokens, even with unrelated cookies present", async () => {
    page({}, { concierge_anon_id: "signed-anon", _ga: "GA1.1", csrftoken: "c", sessionid: "s" });

    await fetchShrineMeaningPayloadV2Server(7);

    expect(lastFetch()[0]).toBe(`${BACKEND}${PATH}`);
    const h = sentHeaders();
    expect(h.get("cookie")).toBeNull();
    expect(h.get("authorization")).toBeNull();
  });

  it.each([
    ["no x-forwarded-for", { "x-forwarded-for": "" }],
    ["a forwarded list", { "x-forwarded-for": `${CLIENT}, 198.51.100.7` }],
    ["a value with a port", { "x-forwarded-for": `${CLIENT}:443` }],
    ["a non-ip value", { "x-forwarded-for": "not-an-ip" }],
  ])("sends no identity headers for %s and still fetches directly", async (_label, h) => {
    page(h);

    await fetchShrineMeaningPayloadV2Server(7);

    expect(lastFetch()[0]).toBe(`${BACKEND}${PATH}`);
    for (const name of ["X-KM-Client-IP", "X-KM-Client-Ts", "X-KM-Client-Sig"]) expect(sentHeaders().get(name)).toBeNull();
  });

  it.each([
    ["off Vercel", { VERCEL: "" }],
    ["without a secret", { KM_CLIENT_IDENTITY_SECRET: "" }],
    ["with a short secret", { KM_CLIENT_IDENTITY_SECRET: "short" }],
    ["when the origin is not a configured Backend origin（local default）", { DJANGO_ORIGIN: "" }],
  ])("does not sign %s", async (_label, env) => {
    for (const [k, v] of Object.entries(env)) vi.stubEnv(k, v);

    await fetchShrineMeaningPayloadV2Server(7);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sentHeaders().get("X-KM-Client-Sig")).toBeNull();
    expect(sentHeaders().get("cookie")).toBeNull();
  });

  it("ignores browser-supplied X-KM-* headers", async () => {
    const spoofed = { "x-km-client-ip": "192.0.2.99", "x-km-client-ts": "1", "x-km-client-sig": "f".repeat(64) };

    page(spoofed);
    await fetchShrineMeaningPayloadV2Server(7);
    let h = sentHeaders();
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Sig")).toBe(signClientIdentity(SECRET, TS, "GET", PATH, CLIENT));

    page({ ...spoofed, "x-forwarded-for": "" });
    await fetchShrineMeaningPayloadV2Server(7);
    h = sentHeaders();
    for (const name of ["X-KM-Client-IP", "X-KM-Client-Ts", "X-KM-Client-Sig"]) expect(h.get(name)).toBeNull();
  });
});

describe("auth context → existing BFF path, unchanged", () => {
  it.each([
    ["access_token", {}, { access_token: "a" }],
    ["refresh_token", {}, { refresh_token: "r" }],
    ["both tokens", {}, { access_token: "a", refresh_token: "r" }],
    ["Authorization header", { authorization: "Bearer x" }, {}],
  ])("uses the BFF and forwards the Cookie header for %s", async (_label, h, c) => {
    page(h, { ...c, concierge_anon_id: "signed-anon" });

    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toEqual(VALID_PAYLOAD);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = lastFetch();
    expect(url).toBe(`${WEB}${PATH}`);
    expect(init.method).toBeUndefined();
    const sent = sentHeaders();
    expect(sent.get("Accept")).toBe("application/json");
    const expectedCookie = cookieStore({ ...c, concierge_anon_id: "signed-anon" }).toString();
    expect(sent.get("Cookie")).toBe(expectedCookie);
    // SSR 側では署名しない（BFF route が自分の受けた request から決める。従来どおり）
    expect(sent.get("X-KM-Client-Sig")).toBeNull();
  });

  it("falls back to the BFF path when the auth context cannot be determined", async () => {
    headersMock.mockRejectedValueOnce(new Error("outside request scope"));
    cookiesMock.mockResolvedValue(cookieStore({}));

    await fetchShrineMeaningPayloadV2Server(7);

    expect(lastFetch()[0]).toBe(`${WEB}${PATH}`);
  });
});

describe("response handling（unchanged）", () => {
  it.each([
    ["401", jsonResponse({ detail: "x" }, 401)],
    ["404", jsonResponse({ detail: "not found" }, 404)],
    ["429", jsonResponse({ detail: "throttled" }, 429)],
    ["500", jsonResponse({ detail: "boom" }, 500)],
    ["invalid JSON", new Response("{nope", { status: 200, headers: { "content-type": "application/json" } })],
    ["a non-JSON body", new Response("<html/>", { status: 200, headers: { "content-type": "text/html" } })],
    ["a payload failing the type guard", jsonResponse({ version: "v1" })],
  ])("returns null for %s on the direct path", async (_label, response) => {
    fetchMock.mockResolvedValueOnce(response);
    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toBeNull();
  });

  it("returns null on a network failure", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toBeNull();
  });

  it("returns null for the same failures on the BFF path", async () => {
    page({}, { access_token: "a" });
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "x" }, 401));
    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toBeNull();
  });

  it("passes the Backend-shaped payload through untouched（entitlement stays in the Backend）", async () => {
    const premiumShaped = {
      ...VALID_PAYLOAD,
      generated: { ...VALID_PAYLOAD.generated, actionMeaning: "premium text" },
      display: { blocks: [{ id: "action_meaning", title: "t", body: "premium text", access: "premium" }], fallbackMessage: null },
    };
    page({}, { access_token: "a" });
    fetchMock.mockResolvedValueOnce(jsonResponse(premiumShaped));
    await expect(fetchShrineMeaningPayloadV2Server(7)).resolves.toEqual(premiumShaped);
  });

  it.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY])("does not fetch for an invalid shrine id（%s）", async (id) => {
    await expect(fetchShrineMeaningPayloadV2Server(id)).resolves.toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
