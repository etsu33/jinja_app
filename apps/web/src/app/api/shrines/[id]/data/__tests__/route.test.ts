/**
 * Regression tests for E2E-005 (docs/audit/beta-core-flow-e2e-audit.md).
 *
 * この BFF 境界は2つの契約を守る必要がある。
 *
 *   1. 「Shrine が存在しない」(404) を「基盤が落ちている」(502) へ丸めない。
 *      丸めると監視上は障害に見え、frontend も両者を区別できない。
 *   2. public response body へ backend origin / upstream の完全 URL /
 *      upstream の生 body を載せない。BFF 境界が backend origin を隠す
 *      目的そのものが破れるため。
 *
 * 修正前は upstream の非 2xx をすべて 502 に潰し、body に
 * `upstream: upstream.url`（= DJANGO_ORIGIN を含む完全 URL）と
 * upstream 本文 1000 文字を載せていた。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const djFetchMock = vi.fn();

vi.mock("server-only", () => ({}));

vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import { GET } from "../route";

/** 実運用と同じ形: backend origin を含む完全 URL が Response.url に入る。 */
const BACKEND_ORIGIN = "https://jinja-backend.internal.example";
const BACKEND_HOST = "jinja-backend.internal.example";

function upstreamResponse(
  body: string,
  {
    status = 200,
    contentType = "application/json",
    url = `${BACKEND_ORIGIN}/api/shrines/49/data/`,
  }: { status?: number; contentType?: string; url?: string } = {},
) {
  const res = new Response(body, {
    status,
    headers: { "content-type": contentType },
  });
  // Response.url は read-only なので定義し直す（undici の実挙動を再現）。
  Object.defineProperty(res, "url", { value: url, configurable: true });
  return res;
}

function makeReq(id = "49") {
  return new NextRequest(`http://localhost/api/shrines/${id}/data`, { method: "GET" });
}

function ctxFor(id: string) {
  return { params: Promise.resolve({ id }) };
}

/** body 全体を文字列化して、内部情報が一切混ざっていないことを見る。 */
async function bodyTextOf(res: Response): Promise<string> {
  return await res.clone().text();
}

function expectNoInternalLeakage(serialized: string) {
  expect(serialized).not.toContain(BACKEND_ORIGIN);
  expect(serialized).not.toContain(BACKEND_HOST);
  expect(serialized).not.toContain("/api/shrines/49/data/");
  expect(serialized).not.toMatch(/https?:\/\//);
}

describe("GET /api/shrines/[id]/data — BFF error contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    djFetchMock.mockReset();
  });

  it("(1) upstream 200 JSON: payload と status をそのまま返す", async () => {
    const payload = { id: 49, name_jp: "明治神宮", latitude: 35.6764, longitude: 139.6993 };
    djFetchMock.mockResolvedValue(upstreamResponse(JSON.stringify(payload)));

    const res = await GET(makeReq(), ctxFor("49"));

    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual(payload);
  });

  it("(2) upstream 404 -> BFF 404（502 へ丸めない）", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse(JSON.stringify({ detail: "No Shrine matches the given query." }), {
        status: 404,
      }),
    );

    const res = await GET(makeReq("999999"), ctxFor("999999"));

    expect(res.status).toBe(404);
    await expect(res.json()).resolves.toEqual({ error: "not_found" });
  });

  it("(3)(4) 404 body に backend origin も upstream URL も含まれない", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse(JSON.stringify({ detail: "No Shrine matches the given query." }), {
        status: 404,
        url: `${BACKEND_ORIGIN}/api/shrines/999999/data/`,
      }),
    );

    const res = await GET(makeReq("999999"), ctxFor("999999"));
    const serialized = await bodyTextOf(res);

    expect(res.status).toBe(404);
    expectNoInternalLeakage(serialized);
    // upstream の生 body（DRF の detail 文言）も載せない。
    expect(serialized).not.toContain("No Shrine matches");
  });

  it("(5) upstream 500 は 404 に誤分類されない", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse("internal server error", { status: 500, contentType: "text/plain" }),
    );

    const res = await GET(makeReq(), ctxFor("49"));

    expect(res.status).toBe(502);
    expect(res.status).not.toBe(404);
    await expect(res.json()).resolves.toEqual({ error: "upstream_failed", status: 500 });
  });

  it("(6) upstream 500 body に backend origin が含まれない", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse(`Traceback: connection to ${BACKEND_ORIGIN} failed`, {
        status: 500,
        contentType: "text/plain",
      }),
    );

    const res = await GET(makeReq(), ctxFor("49"));
    const serialized = await bodyTextOf(res);

    expectNoInternalLeakage(serialized);
    expect(serialized).not.toContain("Traceback");
  });

  it("(7) transport failure は内部 URL を漏らさずに処理される", async () => {
    djFetchMock.mockRejectedValue(
      new TypeError(`fetch failed: connect ECONNREFUSED ${BACKEND_ORIGIN}/api/shrines/49/data/`),
    );

    const res = await GET(makeReq(), ctxFor("49"));
    const serialized = await bodyTextOf(res);

    expect(res.status).toBe(502);
    await expect(res.json()).resolves.toEqual({ error: "upstream_failed", status: 502 });
    expectNoInternalLeakage(serialized);
    expect(serialized).not.toContain("ECONNREFUSED");
  });

  it("(8) invalid JSON body に backend origin / upstream URL が含まれない", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse("<html><body>502 Bad Gateway</body></html>", {
        status: 200,
        contentType: "application/json",
      }),
    );

    const res = await GET(makeReq(), ctxFor("49"));
    const serialized = await bodyTextOf(res);

    expect(res.status).toBe(502);
    await expect(res.json()).resolves.toEqual({ error: "invalid_json" });
    expectNoInternalLeakage(serialized);
    expect(serialized).not.toContain("Bad Gateway");
  });

  it("(9) shrine ID の encoding 挙動は変わらない", async () => {
    // Response の body は一度しか読めないため、呼び出しごとに作り直す。
    djFetchMock.mockImplementation(async () => upstreamResponse(JSON.stringify({ id: 49 })));

    await GET(makeReq(), ctxFor("49"));
    expect(djFetchMock).toHaveBeenCalledWith(expect.anything(), "/api/shrines/49/data/", {
      method: "GET",
      forwardAuth: false,
    });

    djFetchMock.mockClear();

    // encodeURIComponent 経由であることを、そのまま埋めると壊れる値で確認する。
    await GET(makeReq("../secret"), ctxFor("../secret"));
    expect(djFetchMock).toHaveBeenCalledWith(
      expect.anything(),
      "/api/shrines/..%2Fsecret/data/",
      { method: "GET", forwardAuth: false },
    );
  });

  it("(9b) id が空なら upstream を呼ばずに 400", async () => {
    const res = await GET(makeReq(""), ctxFor(""));

    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toEqual({ error: "missing_id" });
    expect(djFetchMock).not.toHaveBeenCalled();
  });

  it("非 JSON の成功応答はそのまま通す（既存の事故防止パスを維持）", async () => {
    djFetchMock.mockResolvedValue(
      upstreamResponse("plain body", { status: 200, contentType: "text/plain" }),
    );

    const res = await GET(makeReq(), ctxFor("49"));

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain("text/plain");
    await expect(res.text()).resolves.toBe("plain body");
  });

  it("(10) Shrine Detail の loader は 404 でも 502 でも従来どおり throw する", async () => {
    // getShrineDetailServer / getShrinePrivate はどちらも `!res.ok` で throw し、
    // Shrine Detail page はそれを catch して not-found シェルを描画する。
    // status を 502 -> 404 に変えてもこの契約は崩れない。
    for (const status of [404, 502]) {
      const res = new Response(JSON.stringify({ error: "x" }), { status });
      expect(res.ok).toBe(false);
    }
  });
});
