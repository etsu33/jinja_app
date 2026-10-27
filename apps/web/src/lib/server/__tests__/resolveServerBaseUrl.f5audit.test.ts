// @vitest-environment node
/**
 * FU-2-P7-F5 audit（behaviour is NOT changed）: SSR callers of resolveServerBaseUrl that forward credentials.
 * docs/audit/fu2-p7-f5-ssr-trusted-origin-2026-10-27.md
 *
 * Without WEB_BASE_URL / PLAYWRIGHT_BASE_URL the destination host comes from x-forwarded-host / host and the protocol
 * from x-forwarded-proto（default http）. The `it.fails` cases state the desired property and flip once a trusted-origin
 * policy is implemented.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const headersMock = vi.fn();
const cookiesMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock(), cookies: () => cookiesMock() }));
vi.mock("next/navigation", () => ({
  redirect: (to: string) => {
    throw new Error(`NEXT_REDIRECT:${to}`);
  },
}));

import { resolveServerBaseUrlFromHeaders } from "@/lib/server/resolveServerBaseUrl";
import { getConciergeThreadServer, getConciergeThreadsServer } from "@/lib/api/concierge.server";
import { getFavoritesServer } from "@/lib/api/favorites.server";
import { getShrineFavoriteInitialState } from "@/lib/server/favorites.server";
import { fetchShrineMeaningPayloadV2Server } from "@/lib/api/shrineMeaning.server";
import ResolvePage from "@/app/shrines/resolve/page";

const ATTACKER = "attacker.example";
const CREDENTIAL_COOKIE = "access_token=AT; refresh_token=RT; concierge_anon_id=ANON";

let fetchMock: ReturnType<typeof vi.fn>;

function cookieStore(raw: string) {
  const pairs = raw ? raw.split("; ").map((p) => p.split("=") as [string, string]) : [];
  return {
    has: (name: string) => pairs.some(([k]) => k === name),
    get: (name: string) => {
      const hit = pairs.find(([k]) => k === name);
      return hit ? { name, value: hit[1] } : undefined;
    },
    toString: () => raw,
  };
}

function page(h: Record<string, string>, cookie = CREDENTIAL_COOKIE) {
  headersMock.mockResolvedValue(new Headers({ ...h, ...(cookie ? { cookie } : {}) }));
  cookiesMock.mockResolvedValue(cookieStore(cookie));
}

/** Every request sent to a host other than the expected trusted one, with its credentials. */
function credentialsSentTo(host: string) {
  return fetchMock.mock.calls
    .map(([url, init]) => ({ url: new URL(String(url)), headers: new Headers((init as RequestInit | undefined)?.headers) }))
    .filter(({ url }) => url.host === host)
    .filter(({ headers }) => headers.get("cookie") || headers.get("authorization"));
}

beforeEach(() => {
  for (const name of ["WEB_BASE_URL", "PLAYWRIGHT_BASE_URL", "VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_URL"]) {
    vi.stubEnv(name, "");
  }
  vi.stubEnv("DJANGO_ORIGIN", "https://backend.test");
  vi.spyOn(console, "log").mockImplementation(() => undefined);
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  fetchMock = vi.fn(async () => new Response("{}", { status: 404, headers: { "content-type": "application/json" } }));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  headersMock.mockReset();
  cookiesMock.mockReset();
});

describe("resolveServerBaseUrlFromHeaders precedence（current）", () => {
  it("prefers WEB_BASE_URL over request headers", () => {
    vi.stubEnv("WEB_BASE_URL", "https://configured.test/");
    expect(resolveServerBaseUrlFromHeaders(new Headers({ host: ATTACKER, "x-forwarded-host": ATTACKER }))).toBe(
      "https://configured.test",
    );
  });

  it("uses x-forwarded-host over host, and defaults the protocol to http", () => {
    expect(resolveServerBaseUrlFromHeaders(new Headers({ host: "web.test", "x-forwarded-host": ATTACKER }))).toBe(
      `http://${ATTACKER}`,
    );
  });

  it("follows a downgraded x-forwarded-proto", () => {
    expect(resolveServerBaseUrlFromHeaders(new Headers({ host: "web.test", "x-forwarded-proto": "http" }))).toBe(
      "http://web.test",
    );
  });

  it("uses the request host before VERCEL_PROJECT_PRODUCTION_URL / VERCEL_URL", () => {
    vi.stubEnv("VERCEL_PROJECT_PRODUCTION_URL", "prod.test");
    vi.stubEnv("VERCEL_URL", "deploy.test");
    expect(resolveServerBaseUrlFromHeaders(new Headers({ host: ATTACKER }))).toBe(`http://${ATTACKER}`);
  });
});

// F5: what each credential-forwarding caller does with a malicious host when no trusted origin is configured.
describe.each([
  ["x-forwarded-host", { host: "web.test", "x-forwarded-host": ATTACKER, "x-forwarded-proto": "https" }],
  ["host", { host: ATTACKER, "x-forwarded-proto": "https" }],
])("malicious %s, no WEB_BASE_URL", (_label, h) => {
  const callers: Array<[string, () => Promise<unknown>]> = [
    ["Concierge thread detail（P7）", () => getConciergeThreadServer("105")],
    ["Concierge thread list（P8）", () => getConciergeThreadsServer()],
    ["favorites list", () => getFavoritesServer()],
    ["shrine favorite initial state", () => getShrineFavoriteInitialState(7)],
    ["shrine meaning（auth branch → BFF）", () => fetchShrineMeaningPayloadV2Server(7)],
    [
      "place resolution page",
      () => ResolvePage({ searchParams: Promise.resolve({ place_id: "abc" }) }).catch(() => undefined),
    ],
  ];

  it.each(callers)("%s: currently sends credentials to the request-derived host", async (_name, run) => {
    page(h);
    await run();
    expect(credentialsSentTo(ATTACKER).length).toBeGreaterThan(0);
  });

  it.fails.each(callers)("%s: never sends credentials to an untrusted host（desired）", async (_name, run) => {
    page(h);
    await run();
    expect(credentialsSentTo(ATTACKER)).toEqual([]);
  });

  it.each(callers)("%s: WEB_BASE_URL keeps credentials on the configured origin", async (_name, run) => {
    vi.stubEnv("WEB_BASE_URL", "https://configured.test");
    page(h);
    await run();
    expect(credentialsSentTo(ATTACKER)).toEqual([]);
    expect(credentialsSentTo("configured.test").length).toBeGreaterThan(0);
  });
});

describe("anonymous visitors（no auth cookie）", () => {
  it("favorites and shrine meaning send nothing to the request host; Concierge still forwards concierge_anon_id", async () => {
    page({ host: ATTACKER, "x-forwarded-proto": "https" }, "concierge_anon_id=ANON");

    await getShrineFavoriteInitialState(7);
    await fetchShrineMeaningPayloadV2Server(7);
    expect(credentialsSentTo(ATTACKER)).toEqual([]);

    await getConciergeThreadServer("105");
    expect(credentialsSentTo(ATTACKER).map(({ headers }) => headers.get("cookie"))).toEqual(["concierge_anon_id=ANON"]);
  });
});
