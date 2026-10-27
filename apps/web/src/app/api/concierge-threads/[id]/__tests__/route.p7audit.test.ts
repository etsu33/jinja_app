// @vitest-environment node
/**
 * FU-2-P7: BFF /api/concierge-threads/[id]（audit tests + FU-2-P7-B id validation）.
 * docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md
 *
 * Ownership is decided only by Django. The BFF forwards the browser's whole Cookie header（including
 * concierge_anon_id）and a Bearer built from access_token, and relays the status/body verbatim.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

vi.mock("server-only", () => ({}));

import { GET } from "../route";

const BACKEND = "https://backend.test";
let fetchMock: ReturnType<typeof vi.fn>;

function call(id: string, cookie = "") {
  const req = new NextRequest(`https://web.test/api/concierge-threads/${encodeURIComponent(id)}`, {
    headers: cookie ? { cookie } : {},
  });
  return GET(req, { params: Promise.resolve({ id }) });
}

function sent(): { url: URL; headers: Headers } {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url: new URL(url), headers: new Headers(init.headers as HeadersInit) };
}

beforeEach(() => {
  vi.stubEnv("DJANGO_ORIGIN", BACKEND);
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", "");
  vi.spyOn(console, "log").mockImplementation(() => undefined);
  fetchMock = vi.fn(async () =>
    new Response(JSON.stringify({ detail: "not found" }), { status: 404, headers: { "content-type": "application/json" } }),
  );
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("BFF thread detail forwarding", () => {
  it("forwards the anonymous cookie only as part of the Cookie header and adds no Authorization", async () => {
    await call("105", "concierge_anon_id=signed-anon; _ga=GA1");

    const { url, headers } = sent();
    expect(url.href).toBe(`${BACKEND}/api/concierge-threads/105/`);
    expect(headers.get("cookie")).toBe("concierge_anon_id=signed-anon; _ga=GA1");
    expect(headers.get("authorization")).toBeNull();
  });

  it("forwards both identities when the browser holds an access token and an anonymous cookie", async () => {
    await call("105", "access_token=a.b.c; concierge_anon_id=signed-anon");

    const { headers } = sent();
    expect(headers.get("authorization")).toBe("Bearer a.b.c");
    expect(headers.get("cookie")).toContain("concierge_anon_id=signed-anon");
  });

  it("relays the Backend's uniform 404 verbatim", async () => {
    const res = await call("105", "concierge_anon_id=other");

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ detail: "not found" });
  });

  it("never logs cookie or token values", async () => {
    await call("105", "access_token=secret-access; concierge_anon_id=secret-anon");

    const logged = JSON.stringify((console.log as unknown as ReturnType<typeof vi.fn>).mock.calls);
    expect(logged).not.toContain("secret-access");
    expect(logged).not.toContain("secret-anon");
  });

  it("relays a refreshed access token and the owner's 200 for a valid id", async () => {
    const exp = Math.floor(Date.now() / 1000) - 60;
    const expired = `h.${Buffer.from(JSON.stringify({ exp })).toString("base64url")}.s`;
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({ access: "fresh.access.token" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 105 }), { status: 200, headers: { "content-type": "application/json" } }));

    const res = await call("105", `access_token=${expired}; refresh_token=r`);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(sent().url.href).toBe(`${BACKEND}/api/concierge-threads/105/`);
    expect(sent().headers.get("authorization")).toBe("Bearer fresh.access.token");
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ id: 105 });
    expect(res.headers.get("set-cookie")).toContain("access_token=fresh.access.token");
  });
});

// F4（FU-2-P7-B）: only canonical positive decimal ids within BigAutoField reach Django.
describe("thread id validation", () => {
  it.each(["1", "9", "105", "9223372036854775807"])("forwards the canonical id %s", async (id) => {
    await call(id, "concierge_anon_id=signed-anon");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sent().url.pathname).toBe(`/api/concierge-threads/${id}/`);
  });

  it.each([
    ["traversal", "../../auth/users/me"],
    ["a single dot segment", ".."],
    ["a decoded slash", "105/../../admin"],
    ["an encoded slash left encoded", "105%2F..%2Fadmin"],
    ["an encoded dot segment", "%2e%2e"],
    ["a backslash", "105\\..\\x"],
    ["a query", "105?x=1"],
    ["a fragment", "105#x"],
    ["zero", "0"],
    ["a leading zero", "0105"],
    ["a negative number", "-1"],
    ["a plus sign", "+1"],
    ["a decimal", "1.5"],
    ["an exponent", "1e3"],
    ["hex", "0x10"],
    ["whitespace", " 105"],
    ["a trailing newline", "105\n"],
    ["full-width digits", "１０５"],
    ["empty", ""],
    ["above BigAutoField", "9223372036854775808"],
    ["too many digits", "1".repeat(20)],
    ["letters", "abc"],
  ])("returns the uniform 404 for %s without contacting Django", async (_label, id) => {
    const res = await call(id, "access_token=a.b.c; refresh_token=r; concierge_anon_id=signed-anon");

    expect(fetchMock).not.toHaveBeenCalled();
    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ detail: "not found" });
    expect(res.headers.get("set-cookie")).toBeNull();
  });

  it("keeps a crafted id inside /api/concierge-threads/（was it.fails in the audit）", async () => {
    await call("../../auth/users/me", "access_token=a.b.c");

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
