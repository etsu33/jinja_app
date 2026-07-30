import { beforeEach, describe, expect, it, vi } from "vitest";

const headersMock = vi.fn();
const resolveServerBaseUrlFromHeadersMock = vi.fn();

vi.mock("next/headers", () => ({
  headers: headersMock,
}));

vi.mock("@/lib/server/resolveServerBaseUrl", () => ({
  resolveServerBaseUrlFromHeaders: resolveServerBaseUrlFromHeadersMock,
}));

describe("getConciergeThreadServer / getConciergeThreadsServer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resolveServerBaseUrlFromHeadersMock.mockReturnValue("http://localhost:3000");
    headersMock.mockResolvedValue({
      get: vi.fn().mockReturnValue(""),
    });
  });

  it("getConciergeThreadServer: 200のときThreadDetailを返す", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ id: 1, title: "相談", messages: [], recommendations: [] }),
    } as Response);

    const { getConciergeThreadServer } = await import("../concierge.server");
    const result = await getConciergeThreadServer("1");

    expect(result).toEqual({ id: 1, title: "相談", messages: [], recommendations: [] });
    fetchSpy.mockRestore();
  });

  // 回帰テスト: 401/403/404はいずれも例外を投げずnullへfallbackする(不正・存在しない・権限外tidを区別しない)。
  // History画面はこの関数だけに頼らず、Thread一覧取得の認証状態と合わせて判定すること。
  it.each([401, 403, 404])(
    "回帰テスト: getConciergeThreadServerはstatus=%iのとき例外を投げずnullを返す",
    async (status) => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        status,
        ok: false,
        json: async () => ({}),
      } as Response);

      const { getConciergeThreadServer } = await import("../concierge.server");
      const result = await getConciergeThreadServer("999");

      expect(result).toBeNull();
      fetchSpy.mockRestore();
    },
  );

  it("getConciergeThreadServerは401/403/404以外の異常ステータスでは例外を投げる", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 500,
      ok: false,
      json: async () => ({}),
    } as Response);

    const { getConciergeThreadServer } = await import("../concierge.server");

    await expect(getConciergeThreadServer("1")).rejects.toThrow(
      "getConciergeThreadServer failed: 500",
    );
    fetchSpy.mockRestore();
  });

  it("getConciergeThreadsServer: 200のときresultsを配列で返す", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ results: [{ id: 1, title: "相談", last_message: "本文", last_message_at: null, message_count: 1 }] }),
    } as Response);

    const { getConciergeThreadsServer } = await import("../concierge.server");
    const result = await getConciergeThreadsServer();

    expect(result).toHaveLength(1);
    fetchSpy.mockRestore();
  });

  // 回帰テスト: 未ログイン(401)と「本当に0件」を区別できない既知の制約。
  // docs/product/history-recommendation-navigation-design.md参照。History画面は
  // 認証状態を別途明示チェックしてから空状態メッセージを出し分けること。
  it.each([401, 403, 404])(
    "回帰テスト: getConciergeThreadsServerはstatus=%iのとき例外を投げず空配列を返す",
    async (status) => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        status,
        ok: false,
        json: async () => ({}),
      } as Response);

      const { getConciergeThreadsServer } = await import("../concierge.server");
      const result = await getConciergeThreadsServer();

      expect(result).toEqual([]);
      fetchSpy.mockRestore();
    },
  );

  it("getConciergeThreadsServerは401/403/404以外の異常ステータスでは例外を投げる", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      status: 500,
      ok: false,
      json: async () => ({}),
    } as Response);

    const { getConciergeThreadsServer } = await import("../concierge.server");

    await expect(getConciergeThreadsServer()).rejects.toThrow(
      "getConciergeThreadsServer failed: 500",
    );
    fetchSpy.mockRestore();
  });
});
