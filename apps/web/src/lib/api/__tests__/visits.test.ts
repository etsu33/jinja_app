import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../client";
import { addVisit, getVisits } from "../visits";

vi.mock("../client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const apiMock = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe("visits api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("addVisit は末尾スラッシュなしの visit API を呼ぶ", async () => {
    apiMock.post.mockResolvedValueOnce({ data: { id: 1, created: true } });

    await expect(addVisit(17)).resolves.toEqual({ id: 1, created: true });

    expect(apiMock.post).toHaveBeenCalledWith("/shrines/17/visit");
  });

  it("threadIdを渡すとpayloadにthread_idを含めて送信する", async () => {
    apiMock.post.mockResolvedValueOnce({ data: { id: 1, created: true } });

    await addVisit(17, "42");

    expect(apiMock.post).toHaveBeenCalledWith("/shrines/17/visit", { thread_id: 42 });
  });

  it("threadIdがnullまたは数値変換不能な場合はpayloadを付けない", async () => {
    apiMock.post.mockResolvedValueOnce({ data: { id: 1, created: true } });
    await addVisit(17, null);
    expect(apiMock.post).toHaveBeenCalledWith("/shrines/17/visit");

    apiMock.post.mockResolvedValueOnce({ data: { id: 2, created: true } });
    await addVisit(17, "not-a-number");
    expect(apiMock.post).toHaveBeenCalledWith("/shrines/17/visit");
  });

  it("getVisits は配列レスポンスをそのまま返す", async () => {
    const visits = [{ id: 1, shrine: 17, visited_at: "2026-06-01T00:00:00+09:00" }];
    apiMock.get.mockResolvedValueOnce({ data: visits });

    await expect(getVisits()).resolves.toEqual(visits);
    expect(apiMock.get).toHaveBeenCalledWith("/visits/");
  });

  it("getVisits は pagination results を返す", async () => {
    const visits = [{ id: 2, shrine: 17, visited_at: "2026-06-01T01:00:00+09:00" }];
    apiMock.get.mockResolvedValueOnce({ data: { count: 1, results: visits } });

    await expect(getVisits()).resolves.toEqual(visits);
  });

  it("getVisits は不正形式なら空配列を返す", async () => {
    apiMock.get.mockResolvedValueOnce({ data: { count: 0 } });

    await expect(getVisits()).resolves.toEqual([]);
  });
});
