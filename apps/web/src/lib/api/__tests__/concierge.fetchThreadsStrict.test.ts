import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  default: { get: vi.fn() },
}));

import api from "../client";
import { ConciergeThreadsResponseError, fetchThreads, fetchThreadsStrict } from "../concierge";

describe("fetchThreadsStrict", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("{ results: [...] } を返す", async () => {
    (api.get as any).mockResolvedValue({ data: { results: [{ id: 89 }] } });
    await expect(fetchThreadsStrict()).resolves.toEqual([{ id: 89 }]);
    expect(api.get).toHaveBeenCalledWith("/concierge-threads/");
  });

  it("配列 body もそのまま返す", async () => {
    (api.get as any).mockResolvedValue({ data: [{ id: 89 }] });
    await expect(fetchThreadsStrict()).resolves.toEqual([{ id: 89 }]);
  });

  it("空の results は空配列（履歴なし）として返す", async () => {
    (api.get as any).mockResolvedValue({ data: { results: [] } });
    await expect(fetchThreadsStrict()).resolves.toEqual([]);
  });

  it("2xx で HTML 文字列が返ったら [] に丸めず throw する", async () => {
    (api.get as any).mockResolvedValue({ data: "<!DOCTYPE html><html>...</html>" });
    await expect(fetchThreadsStrict()).rejects.toBeInstanceOf(ConciergeThreadsResponseError);
  });

  it("results が配列でない object も throw する", async () => {
    (api.get as any).mockResolvedValue({ data: { detail: "x" } });
    await expect(fetchThreadsStrict()).rejects.toBeInstanceOf(ConciergeThreadsResponseError);
  });

  it("既存 fetchThreads は従来どおり想定外 body を [] に丸める（挙動不変）", async () => {
    (api.get as any).mockResolvedValue({ data: "<html></html>" });
    await expect(fetchThreads()).resolves.toEqual([]);
  });
});
