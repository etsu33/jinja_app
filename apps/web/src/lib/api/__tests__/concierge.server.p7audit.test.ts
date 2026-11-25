// @vitest-environment node
/**
 * FU-2-P7 audit（behaviour is NOT changed）: SSR thread fetch destination and forwarded credentials.
 * docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const headersMock = vi.fn();
vi.mock("next/headers", () => ({ headers: () => headersMock() }));

import { getConciergeThreadServer } from "@/lib/api/concierge.server";

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  for (const name of ["WEB_BASE_URL", "PLAYWRIGHT_BASE_URL"]) vi.stubEnv(name, "");
  fetchMock = vi.fn(async () =>
    new Response(JSON.stringify({ detail: "not found" }), { status: 404, headers: { "content-type": "application/json" } }),
  );
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  headersMock.mockReset();
});

describe("SSR getConciergeThreadServer（P7）", () => {
  it("goes through its own BFF and forwards the page request's whole Cookie header", async () => {
    headersMock.mockResolvedValue(
      new Headers({ host: "web.test", "x-forwarded-proto": "https", cookie: "access_token=a; refresh_token=r; concierge_anon_id=s" }),
    );

    await getConciergeThreadServer("105");

    const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
    expect(url).toBe("https://web.test/api/concierge-threads/105/");
    expect(new Headers(init.headers as HeadersInit).get("cookie")).toBe("access_token=a; refresh_token=r; concierge_anon_id=s");
  });

  it("P7-F5: without WEB_BASE_URL the destination host comes from the request's x-forwarded-host / host", async () => {
    headersMock.mockResolvedValue(new Headers({ host: "web.test", "x-forwarded-host": "other.test", cookie: "concierge_anon_id=s" }));

    await getConciergeThreadServer("105");

    expect(new URL((fetchMock.mock.calls.at(-1) as [string])[0]).host).toBe("other.test");
  });

  it("uses WEB_BASE_URL when it is set", async () => {
    vi.stubEnv("WEB_BASE_URL", "https://configured.test");
    headersMock.mockResolvedValue(new Headers({ host: "web.test", "x-forwarded-host": "other.test" }));

    await getConciergeThreadServer("105");

    expect((fetchMock.mock.calls.at(-1) as [string])[0]).toBe("https://configured.test/api/concierge-threads/105/");
  });

  it("encodes the tid as one path segment（the BFF route decodes it again; see P7-F4）", async () => {
    headersMock.mockResolvedValue(new Headers({ host: "web.test" }));

    await getConciergeThreadServer("../../x");

    expect((fetchMock.mock.calls.at(-1) as [string])[0]).toBe("http://web.test/api/concierge-threads/..%2F..%2Fx/");
  });

  it.each([401, 403, 404])("returns null for %s", async (status) => {
    headersMock.mockResolvedValue(new Headers({ host: "web.test" }));
    fetchMock.mockResolvedValueOnce(new Response("{}", { status }));

    await expect(getConciergeThreadServer("105")).resolves.toBeNull();
  });

  it("throws on 429（the shrine page catches it and drops the concierge sections）", async () => {
    headersMock.mockResolvedValue(new Headers({ host: "web.test" }));
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 429 }));

    await expect(getConciergeThreadServer("105")).rejects.toThrow("429");
  });
});
