// @vitest-environment node
/** BFF: 英語の神社詳細に出す特徴語を、Backend の同じ道へ中継する。 */
import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const bffFetchWithAuthFromReqMock = vi.fn();
vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: (...args: unknown[]) => bffFetchWithAuthFromReqMock(...args),
}));

import { GET } from "../route";

beforeEach(() => {
  bffFetchWithAuthFromReqMock.mockReset();
  bffFetchWithAuthFromReqMock.mockResolvedValue(new Response("{}", { status: 200 }));
});

describe("GET /api/shrines/[id]/feature-words-en", () => {
  it("Backend の /api/shrines/{id}/feature-words-en/ を呼ぶ（引数は渡さない）", async () => {
    await GET(new NextRequest("https://web.test/api/shrines/42/feature-words-en/?x=1"), {
      params: Promise.resolve({ id: "42" }),
    });
    expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledTimes(1);
    expect(bffFetchWithAuthFromReqMock.mock.calls[0][1]).toBe("/api/shrines/42/feature-words-en/");
    expect(bffFetchWithAuthFromReqMock.mock.calls[0][2]).toMatchObject({ method: "GET" });
  });

  it("id はエンコードして渡す", async () => {
    await GET(new NextRequest("https://web.test/api/shrines/a%2Fb/feature-words-en/"), {
      params: Promise.resolve({ id: "a/b" }),
    });
    expect(bffFetchWithAuthFromReqMock.mock.calls[0][1]).toBe("/api/shrines/a%2Fb/feature-words-en/");
  });
});
