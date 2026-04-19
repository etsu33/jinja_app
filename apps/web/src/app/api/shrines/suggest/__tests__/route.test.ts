import { describe, it, expect, beforeEach, vi } from "vitest";
import { NextRequest } from "next/server";

const djFetchMock = vi.fn();

vi.mock("@/lib/server/backend", () => ({
  djFetch: (...args: unknown[]) => djFetchMock(...args),
}));

import { GET } from "../route";

function makeReq(search = "") {
  return new NextRequest(`http://localhost/api/shrines/suggest${search}`, {
    method: "GET",
  });
}

describe("/api/shrines/suggest route", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("name が 2 文字未満なら空配列を返し upstream を呼ばない", async () => {
    const res = await GET(makeReq("?name=%E7%A5%9E"));

    expect(djFetchMock).not.toHaveBeenCalled();
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({
      count: 0,
      results: [],
    });
  });

  it("公開検索を djFetch で中継し 3 件までの最小 DTO に整形する", async () => {
    djFetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          count: 5,
          results: [
            { id: 1, name_jp: "東京大神宮", address: "東京都千代田区富士見2-4-1", extra: "x" },
            { id: 2, name: "神田神社（神田明神）", address: "東京都千代田区外神田2-16-2" },
            { id: 3, name_jp: "日枝神社", address: "東京都千代田区永田町2-10-5" },
            { id: 4, name_jp: "明治神宮", address: "東京都渋谷区代々木神園町1-1" },
          ],
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      ),
    );

    const req = makeReq("?name=%20%E6%9D%B1%E4%BA%AC%20");
    const res = await GET(req);

    expect(djFetchMock).toHaveBeenCalledWith(
      req,
      "/api/shrines/?q=%E6%9D%B1%E4%BA%AC&limit=3",
      { method: "GET", forwardAuth: false },
    );
    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({
      count: 3,
      results: [
        { id: 1, name: "東京大神宮", address: "東京都千代田区富士見2-4-1" },
        { id: 2, name: "神田神社（神田明神）", address: "東京都千代田区外神田2-16-2" },
        { id: 3, name: "日枝神社", address: "東京都千代田区永田町2-10-5" },
      ],
    });
  });
});
