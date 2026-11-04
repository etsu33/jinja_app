import { beforeEach, describe, expect, it, vi } from "vitest";

const getAccessTokenMock = vi.fn();
const getRefreshTokenMock = vi.fn();
const isExpiringSoonMock = vi.fn();
const setAccessTokenMock = vi.fn();
const clearTokensMock = vi.fn();
const clearLocalUserDataMock = vi.fn();

vi.mock("../authTokens", () => ({
  getAccessToken: (...args: unknown[]) => getAccessTokenMock(...args),
  getRefreshToken: (...args: unknown[]) => getRefreshTokenMock(...args),
  isExpiringSoon: (...args: unknown[]) => isExpiringSoonMock(...args),
  setAccessToken: (...args: unknown[]) => setAccessTokenMock(...args),
  clearTokens: (...args: unknown[]) => clearTokensMock(...args),
}));

vi.mock("../localUserData", () => ({
  clearLocalUserData: (...args: unknown[]) => clearLocalUserDataMock(...args),
}));

import { ACCOUNT_DELETION_MESSAGES, deleteAccount } from "../accountDeletion";

function response(status: number, body = ""): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => {
      throw new Error("json() must not be called");
    },
    text: async () => body,
  } as unknown as Response;
}

describe("deleteAccount", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getAccessTokenMock.mockResolvedValue("access-token");
    isExpiringSoonMock.mockReturnValue(false);
  });

  it("204: DELETE /users/me/ を呼び、トークンと端末内データを消去してokを返す", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(response(204));

    const result = await deleteAccount();

    expect(result).toEqual({ ok: true });
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toMatch(/\/users\/me\/$/);
    expect(init?.method).toBe("DELETE");
    expect((init?.headers as Record<string, string>).Authorization).toBe("Bearer access-token");
    expect(clearTokensMock).toHaveBeenCalledTimes(1);
    expect(clearLocalUserDataMock).toHaveBeenCalledTimes(1);
  });

  it("204: 端末内データの消去に失敗しても退会完了として扱う", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(204));
    clearLocalUserDataMock.mockRejectedValueOnce(new Error("storage failure"));

    await expect(deleteAccount()).resolves.toEqual({ ok: true });
  });

  it("503: 失敗メッセージを返し、ログイン状態(トークン・端末データ)を維持する", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(503, "unavailable"));

    const result = await deleteAccount();

    expect(result).toEqual({ ok: false, message: ACCOUNT_DELETION_MESSAGES.failed });
    expect(clearTokensMock).not.toHaveBeenCalled();
    expect(clearLocalUserDataMock).not.toHaveBeenCalled();
  });

  it("その他のエラー(500): 503と同じ扱い", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(500));

    await expect(deleteAccount()).resolves.toEqual({ ok: false, message: ACCOUNT_DELETION_MESSAGES.failed });
    expect(clearTokensMock).not.toHaveBeenCalled();
  });

  it("ネットワークエラー: 503と同じ扱い", async () => {
    vi.spyOn(global, "fetch").mockRejectedValueOnce(new TypeError("Network request failed"));

    await expect(deleteAccount()).resolves.toEqual({ ok: false, message: ACCOUNT_DELETION_MESSAGES.failed });
    expect(clearTokensMock).not.toHaveBeenCalled();
    expect(clearLocalUserDataMock).not.toHaveBeenCalled();
  });

  it("確認文言: 取り消せない旨とPremium購読も停止される旨を含む", () => {
    expect(ACCOUNT_DELETION_MESSAGES.confirmBody).toContain("元に戻すことはできません");
    expect(ACCOUNT_DELETION_MESSAGES.finalConfirmBody).toContain("取り消せません");
    expect(ACCOUNT_DELETION_MESSAGES.finalConfirmBody).toContain("Premiumの購読も停止");
  });
});
