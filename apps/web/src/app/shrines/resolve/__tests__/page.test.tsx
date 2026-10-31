import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn((url: string) => {
  throw new Error(`REDIRECT:${url}`);
});

vi.mock("next/navigation", () => ({
  redirect: (url: string) => redirectMock(url),
}));
vi.mock("next/headers", () => ({
  headers: async () => new Headers({ cookie: "" }),
}));
vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrlFromHeaders: () => "http://bff.local",
}));

import ResolvePage from "../page";
import { buildGoogleMapsPlaceHref } from "../UnregisteredPlaceView";

function mockResolveResponse(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } })),
  );
}

describe("/shrines/resolve", () => {
  beforeEach(() => {
    redirectMock.mockClear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
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
