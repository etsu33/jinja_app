// @vitest-environment node
/**
 * /shrines/resolve → Django: end-to-end WS-04 signing through the real djFetch / clientIdentity（no mocks of either）.
 * The page signs only a single, valid address from the incoming request's x-forwarded-for, only on Vercel with the
 * secret configured, and never forwards cookie / Authorization.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
const headersMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock() }));
vi.mock("next/navigation", () => ({
  redirect: (to: string) => {
    throw new Error(`NEXT_REDIRECT:${to}`);
  },
}));

import ResolvePage from "@/app/shrines/resolve/page";
import {
  CLIENT_IP_HEADER,
  CLIENT_SIG_HEADER,
  CLIENT_TS_HEADER,
  signClientIdentity,
} from "@/lib/server/clientIdentity";

const SECRET = "k".repeat(48);
let fetchMock: ReturnType<typeof vi.fn>;

function incoming(h: Record<string, string>) {
  headersMock.mockResolvedValue(new Headers({ cookie: "access_token=AT; refresh_token=RT", ...h }));
}

async function sentHeaders(): Promise<Headers> {
  await ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_SIG" }) }).catch(() => undefined);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
  expect(new URL(url).toString()).toBe("https://backend.test/api/places/resolve/");
  return new Headers(init.headers);
}

beforeEach(() => {
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  vi.stubEnv("DJANGO_ORIGIN", "https://backend.test");
  vi.spyOn(console, "log").mockImplementation(() => undefined);
  fetchMock = vi.fn(
    async () =>
      new Response(JSON.stringify({ id: 1, shrine_id: 1, place_id: "PID_SIG", candidate_id: 1 }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  headersMock.mockReset();
});

describe("/shrines/resolve WS-04 signing", () => {
  it("signs the single client IP from x-forwarded-for, bound to POST and the Backend path", async () => {
    incoming({ "x-forwarded-for": "203.0.113.7" });

    const h = await sentHeaders();

    expect(h.get(CLIENT_IP_HEADER)).toBe("203.0.113.7");
    const ts = h.get(CLIENT_TS_HEADER)!;
    expect(h.get(CLIENT_SIG_HEADER)).toBe(signClientIdentity(SECRET, ts, "POST", "/api/places/resolve/", "203.0.113.7"));
    expect(h.get("cookie")).toBeNull();
    expect(h.get("authorization")).toBeNull();
  });

  it.each([
    ["multiple addresses", "203.0.113.7, 198.51.100.1"],
    ["address with port", "203.0.113.7:443"],
    ["hostname", "attacker.example"],
    ["out-of-range IPv4", "999.1.1.1"],
    ["IPv6 with zone id", "fe80::1%eth0"],
  ])("does not sign when x-forwarded-for is %s", async (_label, value) => {
    incoming({ "x-forwarded-for": value });

    const h = await sentHeaders();

    expect(h.get(CLIENT_IP_HEADER)).toBeNull();
    expect(h.get(CLIENT_SIG_HEADER)).toBeNull();
  });

  it("does not sign when x-forwarded-for is missing", async () => {
    incoming({});
    const h = await sentHeaders();
    expect(h.get(CLIENT_IP_HEADER)).toBeNull();
  });

  it("does not sign off Vercel even with a valid x-forwarded-for", async () => {
    vi.stubEnv("VERCEL", "");
    incoming({ "x-forwarded-for": "203.0.113.7" });
    const h = await sentHeaders();
    expect(h.get(CLIENT_IP_HEADER)).toBeNull();
  });

  it("does not sign without a sufficiently long secret", async () => {
    vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", "short");
    incoming({ "x-forwarded-for": "203.0.113.7" });
    const h = await sentHeaders();
    expect(h.get(CLIENT_IP_HEADER)).toBeNull();
  });
});
