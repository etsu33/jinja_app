import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn((url: string) => {
  throw new Error(`REDIRECT:${url}`);
});

vi.mock("next/navigation", () => ({
  redirect: (url: string) => redirectMock(url),
}));
let incomingHeaders = new Headers({ cookie: "access_token=secret", "x-forwarded-for": "203.0.113.7" });
vi.mock("next/headers", () => ({
  headers: async () => incomingHeaders,
}));

const djFetchMock = vi.fn();
vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import ResolvePage from "../page";
import { buildGoogleMapsPlaceHref } from "../UnregisteredPlaceView";

function mockResolveResponse(body: unknown, status = 200) {
  djFetchMock.mockImplementation(
    async () => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }),
  );
}

describe("/shrines/resolve", () => {
  beforeEach(() => {
    redirectMock.mockClear();
    djFetchMock.mockReset();
    incomingHeaders = new Headers({ cookie: "access_token=secret", "x-forwarded-for": "203.0.113.7" });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("Django を直接呼び、利用者の x-forwarded-for を client identity の元にする（認証は転送しない）", async () => {
    mockResolveResponse({ id: 42, shrine_id: 42, place_id: "PID_REG", candidate_id: 2 });

    await expect(ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_REG" }) })).rejects.toThrow(
      /REDIRECT:\/shrines\/42/,
    );

    expect(djFetchMock).toHaveBeenCalledTimes(1);
    const [path, init] = djFetchMock.mock.calls[0] as [string, RequestInit & { clientIdentityFrom?: Request }];
    expect(path).toBe("/api/places/resolve/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ place_id: "PID_REG" });
    expect(init.clientIdentityFrom?.headers.get("x-forwarded-for")).toBe("203.0.113.7");
    expect(init.clientIdentityFrom?.headers.get("cookie")).toBeNull();
    expect(new Headers(init.headers).get("cookie")).toBeNull();
    expect(new Headers(init.headers).get("authorization")).toBeNull();
  });

  it("x-forwarded-for が無いときは identity ヘッダ元を空にする（署名されず fail-safe）", async () => {
    incomingHeaders = new Headers();
    mockResolveResponse({ id: 42, shrine_id: 42, place_id: "PID_REG", candidate_id: 2 });

    await expect(ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_REG" }) })).rejects.toThrow(/REDIRECT/);

    const [, init] = djFetchMock.mock.calls[0] as [string, RequestInit & { clientIdentityFrom?: Request }];
    expect(init.clientIdentityFrom?.headers.get("x-forwarded-for")).toBeNull();
  });

  it("throttle で 429 のときは従来どおり resolve_failed へ戻す", async () => {
    mockResolveResponse({ detail: "Request was throttled." }, 429);

    await expect(ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_X" }) })).rejects.toThrow(
      /REDIRECT:\/\?toast=resolve_failed/,
    );
  });

  it("未登録の Place は Shrine を作らずに場所の情報だけを表示する", async () => {
    mockResolveResponse({
      id: null,
      shrine_id: null,
      place_id: "PID_UNREG",
      candidate_id: 1,
      registered: false,
      name_jp: "未登録の場所",
      address: "北海道どこか1-1",
      lat: 43,
      lng: 141,
    });

    const el = await ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_UNREG" }) });
    render(el);

    expect(redirectMock).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "未登録の場所" })).toBeInTheDocument();
    expect(screen.getByText("北海道どこか1-1")).toBeInTheDocument();
    expect(screen.getByText(/まだ神社として登録されていません/)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: "Google マップで見る" });
    expect(link.getAttribute("href")).toContain("query_place_id=PID_UNREG");
  });

  it("登録済みの Place は従来どおり神社詳細へ redirect する", async () => {
    mockResolveResponse({ id: 42, shrine_id: 42, place_id: "PID_REG", candidate_id: 2 });

    await expect(
      ResolvePage({ searchParams: Promise.resolve({ place_id: "PID_REG", ctx: "concierge" }) }),
    ).rejects.toThrow(/REDIRECT:\/shrines\/42/);
  });

  it("buildGoogleMapsPlaceHref は名称を検索語に、place_id を query_place_id に使う", () => {
    const href = buildGoogleMapsPlaceHref({ place_id: "PID_X", name_jp: "八幡宮", address: "東京都" });
    const u = new URL(href);
    expect(u.searchParams.get("query")).toBe("八幡宮");
    expect(u.searchParams.get("query_place_id")).toBe("PID_X");
    expect(u.searchParams.get("api")).toBe("1");
  });
});
