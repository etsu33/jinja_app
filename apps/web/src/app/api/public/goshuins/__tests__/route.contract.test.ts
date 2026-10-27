// @vitest-environment node
/**
 * FU-2-A2: SSR（publicGoshuins.server.ts）が Django 直行になっても、/api/public/goshuins の外部契約は変えない。
 * 既存の caller（ブラウザ等）向けの振る舞いを固定する regression test。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { GET } from "../route";
import { signClientIdentity } from "@/lib/server/clientIdentity";

const BACKEND = "https://jinja-backend.test";
const SECRET = "test-secret-0123456789abcdef-0123456789";
const CLIENT = "203.0.113.10";
const NOW_MS = 1_700_000_000_000;

let fetchMock: ReturnType<typeof vi.fn>;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW_MS);
  vi.stubEnv("DJANGO_ORIGIN", BACKEND);
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("KM_CLIENT_IDENTITY_SECRET", SECRET);
  fetchMock = vi.fn(async () => jsonResponse([]));
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(console, "log").mockImplementation(() => {});
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("GET /api/public/goshuins（contract unchanged by FU-2-A2）", () => {
  it("requires shrine", async () => {
    const res = await GET(new Request("https://web.test/api/public/goshuins?limit=12&offset=0"));
    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ error: "shrine is required" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("calls the same Django upstream and signs its own incoming request", async () => {
    await GET(new Request("https://web.test/api/public/goshuins?shrine=7", { headers: { "x-forwarded-for": CLIENT } }));

    const [url, init] = fetchMock.mock.calls.at(-1) as unknown as [string, RequestInit];
    expect(url).toBe(`${BACKEND}/api/goshuins/?is_public=true&shrine=7`);
    const h = new Headers(init.headers as HeadersInit);
    expect(h.get("X-KM-Client-IP")).toBe(CLIENT);
    expect(h.get("X-KM-Client-Sig")).toBe(
      signClientIdentity(SECRET, String(NOW_MS / 1000), "GET", "/api/goshuins/", CLIENT),
    );
  });

  it("keeps the paginated body, the 12-item default and image normalization", async () => {
    const rows = Array.from({ length: 15 }, (_, i) => ({ id: i + 1, is_public: true, image_url: i === 0 ? "/media/a.jpg" : null }));
    fetchMock.mockResolvedValueOnce(jsonResponse(rows));

    const res = await GET(new Request("https://web.test/api/public/goshuins?shrine=7"));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.results).toHaveLength(12);
    expect(body.results[0]).toEqual({ id: 1, is_public: true, image_url: `${BACKEND}/media/a.jpg` });
    expect(body.count).toBe(15);
    expect(body.previous).toBeNull();
    expect(body.next).toBe("/api/public/goshuins?limit=12&offset=12&shrine=7");
  });

  it("returns 502 when the upstream is not ok", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "throttled" }, 429));
    const res = await GET(new Request("https://web.test/api/public/goshuins?shrine=7"));
    expect(res.status).toBe(502);
  });
});
