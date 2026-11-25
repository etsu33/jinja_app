// @vitest-environment node
/**
 * BFF の意味の窓口: 相談と一致したご利益の名前（引数 benefits）だけを Backend へ渡す。
 */
import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const bffFetchWithAuthFromReqMock = vi.fn();
vi.mock("@/lib/server/bffFetch", () => ({
  bffFetchWithAuthFromReq: (...args: unknown[]) => bffFetchWithAuthFromReqMock(...args),
}));

import { GET } from "../route";

const ctx = { params: Promise.resolve({ id: "42" }) };

async function upstreamPathFor(query: string): Promise<string> {
  await GET(new NextRequest(`https://web.test/api/shrines/42/meaning/${query}`), ctx);
  expect(bffFetchWithAuthFromReqMock).toHaveBeenCalledTimes(1);
  return bffFetchWithAuthFromReqMock.mock.calls[0][1] as string;
}

beforeEach(() => {
  bffFetchWithAuthFromReqMock.mockReset();
  bffFetchWithAuthFromReqMock.mockResolvedValue(new Response("{}", { status: 200 }));
});

describe("GET /api/shrines/[id]/meaning", () => {
  it("引数が無いときは、今までどおりの道で Backend を呼ぶ", async () => {
    expect(await upstreamPathFor("")).toBe("/api/shrines/42/meaning/");
  });

  it("benefits を、並び順のまま Backend へ渡す", async () => {
    const path = await upstreamPathFor("?benefits=%E5%8E%84%E9%99%A4%E3%81%91&benefits=%E5%AE%B6%E5%86%85%E5%AE%89%E5%85%A8");

    const url = new URL(path, "https://backend.invalid");
    expect(url.pathname).toBe("/api/shrines/42/meaning/");
    expect(url.searchParams.getAll("benefits")).toEqual(["厄除け", "家内安全"]);
  });

  it("benefits 以外の引数は渡さない", async () => {
    const path = await upstreamPathFor("?plan=premium&benefits=%E5%8E%84%E9%99%A4%E3%81%91&x=1");

    const url = new URL(path, "https://backend.invalid");
    expect([...url.searchParams.keys()]).toEqual(["benefits"]);
    expect(url.searchParams.get("plan")).toBeNull();
  });

  it("benefits 以外の引数だけのときは、引数を付けない", async () => {
    expect(await upstreamPathFor("?plan=premium")).toBe("/api/shrines/42/meaning/");
  });
});
