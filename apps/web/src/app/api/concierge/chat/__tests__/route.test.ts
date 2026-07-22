

import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

const djFetchMock = vi.fn();

vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import { POST } from "../route";

function makeReq(body: unknown, cookie = "") {
  return new NextRequest("http://localhost/api/concierge/chat", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(cookie ? { cookie } : {}),
    },
    body: JSON.stringify(body),
  });
}

function getSetCookies(res: Response): string[] {
  const h = res.headers as Headers & {
    getSetCookie?: () => string[];
    raw?: () => Record<string, string[]>;
  };

  if (typeof h.getSetCookie === "function") return h.getSetCookie();

  const raw = typeof h.raw === "function" ? h.raw() : null;
  if (raw?.["set-cookie"]) return raw["set-cookie"];

  const sc = res.headers.get("set-cookie");
  return sc ? [sc] : [];
}

function responseWithSetCookies(body: unknown, setCookies: string[], init: ResponseInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("content-type", headers.get("content-type") ?? "application/json");

  for (const cookie of setCookies) {
    headers.append("set-cookie", cookie);
  }

  return new Response(JSON.stringify(body), {
    ...init,
    headers,
  });
}

describe("/api/concierge/chat BFF contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("normal: upstream 200 をそのまま返す", async () => {
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true, data: { recommendations: [] } }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const req = makeReq({ query: "仕事運" });
    const res = await POST(req);

    expect(djFetchMock).toHaveBeenCalledTimes(1);
    expect(djFetchMock).toHaveBeenCalledWith(req, "/api/concierge/chat/", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ query: "仕事運" }),
    });
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ ok: true, data: { recommendations: [] } });
  });

  it("normal: _anon_cookie_value があれば concierge_anon_id を set-cookie する", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true, _anon_cookie_value: "anon-cookie-value" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ query: "仕事運" }));
    const cookies = getSetCookies(res).join("\n");

    expect(res.status).toBe(200);
    expect(cookies).toContain("concierge_anon_id=anon-cookie-value");
    expect(cookies).toContain("HttpOnly");
    expect(cookies).toContain("Path=/");
    expect(cookies).toMatch(/SameSite=None/i);
    expect(cookies).toMatch(/Secure/i);
    expect(JSON.stringify(log.mock.calls)).not.toContain("anon-cookie-value");
    expect(log).toHaveBeenCalledWith("[BFF_ANON_COOKIE_SET_RESULT]", { phase: "normal", attached: true });
    log.mockRestore();
  });

  it("refresh success: 初回401後にrefreshし、再chat結果とauth cookieを返す", async () => {
    djFetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "token expired" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ access: "NEXT_ACCESS", refresh: "NEXT_REFRESH" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true, _anon_cookie_value: "next-anon" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );

    const req = makeReq({ query: "仕事運" }, "access_token=OLD_ACCESS; refresh_token=OLD_REFRESH");
    const res = await POST(req);
    const cookies = getSetCookies(res).join("\n");

    expect(djFetchMock).toHaveBeenCalledTimes(3);
    expect(djFetchMock).toHaveBeenNthCalledWith(1, req, "/api/concierge/chat/", {
      method: "POST",
      headers: { "content-type": "application/json", Authorization: "Bearer OLD_ACCESS" },
      body: JSON.stringify({ query: "仕事運" }),
    });
    expect(djFetchMock).toHaveBeenNthCalledWith(2, req, "/api/auth/jwt/refresh/", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh: "OLD_REFRESH" }),
    });
    expect(djFetchMock).toHaveBeenNthCalledWith(3, req, "/api/concierge/chat/", {
      method: "POST",
      headers: { "content-type": "application/json", Authorization: "Bearer NEXT_ACCESS" },
      body: JSON.stringify({ query: "仕事運" }),
    });

    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({ ok: true, _anon_cookie_value: "next-anon" });
    expect(cookies).toContain("access_token=NEXT_ACCESS");
    expect(cookies).toContain("refresh_token=NEXT_REFRESH");
    expect(cookies).toContain("concierge_anon_id=next-anon");
  });

  it("refresh fail: 初回401後にrefresh失敗なら初回401を返し access_token を削除する", async () => {
    djFetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "token expired" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "refresh failed" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      );

    const res = await POST(makeReq({ query: "仕事運" }, "access_token=OLD_ACCESS; refresh_token=OLD_REFRESH"));
    const cookies = getSetCookies(res).join("\n");

    expect(djFetchMock).toHaveBeenCalledTimes(2);
    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toEqual({ detail: "token expired" });
    expect(cookies).toContain("access_token=");
    expect(cookies).toMatch(/Expires=Thu, 01 Jan 1970 00:00:00 GMT/i);
  });

  it("multiple set-cookie: upstream の複数 set-cookie を relay する", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    djFetchMock.mockResolvedValue(
      responseWithSetCookies(
        { ok: true },
        ["upstream_a=1; Path=/; HttpOnly", "upstream_b=2; Path=/; HttpOnly"],
        { status: 200 },
      ),
    );

    const res = await POST(makeReq({ query: "仕事運" }));
    const cookies = getSetCookies(res).join("\n");

    expect(res.status).toBe(200);
    expect(cookies).toContain("upstream_a=1");
    expect(cookies).toContain("upstream_b=2");
    expect(JSON.stringify(log.mock.calls)).not.toMatch(/upstream_[ab]=[12]/);
    log.mockRestore();
  });

  it("upstream 500 passthrough: backend 500を同じstatus/bodyで返す", async () => {
    djFetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "backend failed" }), {
        status: 500,
        headers: { "content-type": "application/json" },
      }),
    );

    const res = await POST(makeReq({ query: "仕事運" }));

    expect(res.status).toBe(500);
    await expect(res.json()).resolves.toEqual({ detail: "backend failed" });
  });
});
