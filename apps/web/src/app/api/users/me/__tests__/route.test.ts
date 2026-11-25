import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest, NextResponse } from "next/server";

const { bffFetchWithAuthFromReqMock } = vi.hoisted(() => ({
  bffFetchWithAuthFromReqMock: vi.fn(),
}));

vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: bffFetchWithAuthFromReqMock,
}));

import { DELETE } from "../route";

function makeDeleteRequest(origin?: string) {
  const headers = new Headers({
    cookie: "access_token=test-access; refresh_token=test-refresh",
  });

  if (origin !== undefined) {
    headers.set("origin", origin);
  }

  return new NextRequest("http://localhost/api/users/me", {
    method: "DELETE",
    headers,
  });
}

describe("DELETE /api/users/me BFF", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("同一Originの場合はBackend DELETEを呼ぶ", async () => {
    const req = makeDeleteRequest("http://localhost");

    bffFetchWithAuthFromReqMock.mockResolvedValue(new NextResponse(null, { status: 204 }));

    const res = await DELETE(req);

    expect(res.status).toBe(204);
    expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledTimes(1);
    expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledWith(req, "/api/users/me/", { method: "DELETE" });
  });

  it("異なるOriginの場合は403を返してBackendを呼ばない", async () => {
    const req = makeDeleteRequest("https://evil.example");

    const res = await DELETE(req);

    expect(res.status).toBe(403);
    expect(bffFetchWithAuthFromReqMock).not.toHaveBeenCalled();
    expect(res.headers.get("set-cookie")).toBeNull();
  });

  it("不正なOriginの場合は403を返してBackendを呼ばない", async () => {
    const req = makeDeleteRequest("not-a-valid-origin");

    const res = await DELETE(req);

    expect(res.status).toBe(403);
    expect(bffFetchWithAuthFromReqMock).not.toHaveBeenCalled();
    expect(res.headers.get("set-cookie")).toBeNull();
  });

  it("Originが無い場合はBackend DELETEを呼ぶ", async () => {
    const req = makeDeleteRequest();

    bffFetchWithAuthFromReqMock.mockResolvedValue(new NextResponse(null, { status: 204 }));

    const res = await DELETE(req);

    expect(res.status).toBe(204);
    expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledTimes(1);
    expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledWith(req, "/api/users/me/", { method: "DELETE" });
  });

  it("Backendが204の場合だけaccess / refresh Cookieを削除する", async () => {
    const req = makeDeleteRequest("http://localhost");

    bffFetchWithAuthFromReqMock.mockResolvedValue(new NextResponse(null, { status: 204 }));

    const res = await DELETE(req);

    expect(res.status).toBe(204);

    const setCookie = res.headers.get("set-cookie") ?? "";
    const normalized = setCookie.toLowerCase();

    expect(normalized).toContain("access_token=");
    expect(normalized).toContain("refresh_token=");
    expect(normalized).toContain("max-age=0");
  });

  it.each([401, 500, 503])("Backendが%dの場合はresponseを変更せずCookie削除もしない", async (status) => {
    const req = makeDeleteRequest("http://localhost");

    const upstream = NextResponse.json({ detail: "failed" }, { status });

    bffFetchWithAuthFromReqMock.mockResolvedValue(upstream);

    const res = await DELETE(req);

    expect(res).toBe(upstream);
    expect(res.status).toBe(status);
    expect(res.headers.get("set-cookie")).toBeNull();
  });
});
