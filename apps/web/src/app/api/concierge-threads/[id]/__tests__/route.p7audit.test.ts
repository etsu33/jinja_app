// @vitest-environment node
/**
 * FU-2-P7 audit（behaviour is NOT changed）: BFF /api/concierge-threads/[id].
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

  // P7-F4: the decoded `id` param is interpolated into the upstream path without validation, and the URL parser
  // normalises dot segments, so a crafted id leaves /api/concierge-threads/. `it.fails` documents the gap:
  // once the route validates the id, this test starts failing and should become a plain `it`.
  it.fails("keeps a crafted id inside /api/concierge-threads/", async () => {
    await call("../../auth/users/me", "access_token=a.b.c");

    if (fetchMock.mock.calls.length === 0) return;
    expect(sent().url.pathname.startsWith("/api/concierge-threads/")).toBe(true);
  });
});
