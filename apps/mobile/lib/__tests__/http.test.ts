import { describe, expect, it, vi, beforeEach } from "vitest";

const getAccessTokenMock = vi.fn();
const getRefreshTokenMock = vi.fn();
const isExpiringSoonMock = vi.fn();
const setAccessTokenMock = vi.fn();

vi.mock("../authTokens", () => ({
  getAccessToken: (...args: unknown[]) => getAccessTokenMock(...args),
  getRefreshToken: (...args: unknown[]) => getRefreshTokenMock(...args),
  isExpiringSoon: (...args: unknown[]) => isExpiringSoonMock(...args),
  setAccessToken: (...args: unknown[]) => setAccessTokenMock(...args),
}));

import { HttpError, UnauthenticatedError, get, getAuth, isHttpError, isUnauthenticatedError } from "../http";

describe("http", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("get", () => {
    it("正常系: 200のときJSONを返す", async () => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ok: true }),
      } as Response);

      const result = await get<{ ok: boolean }>("/ping/");

      expect(result).toEqual({ ok: true });
      fetchSpy.mockRestore();
    });

    it("異常系: 404のときstatus=404のHttpErrorを投げる", async () => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        text: async () => "not found",
      } as Response);

      await expect(get("/missing/")).rejects.toMatchObject({ name: "HttpError", status: 404 });

      fetchSpy.mockRestore();
    });

    it("isHttpErrorはHttpErrorのみをtrueと判定する", async () => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Server Error",
        text: async () => "",
      } as Response);

      try {
        await get("/broken/");
        throw new Error("unreachable");
      } catch (error) {
        expect(isHttpError(error)).toBe(true);
        expect(isUnauthenticatedError(error)).toBe(false);
        expect(error).toBeInstanceOf(HttpError);
        expect(error).toBeInstanceOf(Error);
      }

      fetchSpy.mockRestore();
    });
  });

  describe("getAuth", () => {
    it("正常系: 有効なaccess tokenがあればBearerを付けて取得する", async () => {
      getAccessTokenMock.mockResolvedValue("valid-token");
      isExpiringSoonMock.mockReturnValue(false);

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ id: 1 }),
      } as Response);

      const result = await getAuth<{ id: number }>("/concierge-threads/1/");

      expect(result).toEqual({ id: 1 });
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/concierge-threads/1/"),
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer valid-token" }) }),
      );
      fetchSpy.mockRestore();
    });

    it("回帰テスト: access tokenもrefresh tokenも無い場合はUnauthenticatedErrorを投げる(fetchを呼ばない)", async () => {
      getAccessTokenMock.mockResolvedValue(null);
      getRefreshTokenMock.mockResolvedValue(null);

      const fetchSpy = vi.spyOn(global, "fetch");

      await expect(getAuth("/concierge-threads/")).rejects.toBeInstanceOf(UnauthenticatedError);
      expect(fetchSpy).not.toHaveBeenCalled();

      fetchSpy.mockRestore();
    });

    it("回帰テスト: 初回401後にrefresh成功したら新tokenで再試行する", async () => {
      getAccessTokenMock.mockResolvedValue("expiring-token");
      isExpiringSoonMock.mockReturnValue(false);
      getRefreshTokenMock.mockResolvedValue("refresh-token");

      const fetchSpy = vi
        .spyOn(global, "fetch")
        .mockResolvedValueOnce({ ok: false, status: 401, statusText: "Unauthorized", text: async () => "" } as Response)
        .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ access: "new-token" }) } as Response)
        .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ id: 2 }) } as Response);

      const result = await getAuth<{ id: number }>("/concierge-threads/2/");

      expect(result).toEqual({ id: 2 });
      expect(setAccessTokenMock).toHaveBeenCalledWith("new-token");
      expect(fetchSpy).toHaveBeenCalledTimes(3);
      fetchSpy.mockRestore();
    });

    it("回帰テスト: 初回401後にrefreshが失敗したらUnauthenticatedErrorを投げる", async () => {
      getAccessTokenMock.mockResolvedValue("expired-token");
      isExpiringSoonMock.mockReturnValue(false);
      getRefreshTokenMock.mockResolvedValue("refresh-token");

      const fetchSpy = vi
        .spyOn(global, "fetch")
        .mockResolvedValueOnce({ ok: false, status: 401, statusText: "Unauthorized", text: async () => "" } as Response)
        .mockResolvedValueOnce({ ok: false, status: 401, statusText: "Unauthorized", text: async () => "" } as Response);

      await expect(getAuth("/concierge-threads/")).rejects.toBeInstanceOf(UnauthenticatedError);
      fetchSpy.mockRestore();
    });

    it("異常系: 401以外の異常応答(403)はstatus=403のHttpErrorを投げる", async () => {
      getAccessTokenMock.mockResolvedValue("valid-token");
      isExpiringSoonMock.mockReturnValue(false);

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: false,
        status: 403,
        statusText: "Forbidden",
        text: async () => "forbidden",
      } as Response);

      await expect(getAuth("/concierge-threads/")).rejects.toMatchObject({ name: "HttpError", status: 403 });
      fetchSpy.mockRestore();
    });

    it("異常系: 404はstatus=404のHttpErrorを投げる", async () => {
      getAccessTokenMock.mockResolvedValue("valid-token");
      isExpiringSoonMock.mockReturnValue(false);

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        text: async () => "not found",
      } as Response);

      await expect(getAuth("/concierge-threads/999/")).rejects.toMatchObject({ name: "HttpError", status: 404 });
      fetchSpy.mockRestore();
    });
  });
});
