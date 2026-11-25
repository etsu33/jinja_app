import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

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
import { setAnalyticsProvider, type AnalyticsPayload, type AnalyticsProvider } from "../analytics";

// 呼び出し順を1本の配列に記録し、「退会の印 → 解析用IDの作り直し → 端末データ消去」の順序を検証する
const callOrder: string[] = [];
const trackedEvents: Array<{ eventName: string; payload: AnalyticsPayload }> = [];
const resetIdentityMock = vi.fn(async () => {
  callOrder.push("resetIdentity");
});

class RecordingAnalyticsProvider implements AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload): void {
    callOrder.push(`track:${eventName}`);
    trackedEvents.push({ eventName, payload });
  }
  resetIdentity(): Promise<void> {
    return resetIdentityMock();
  }
}

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
    callOrder.length = 0;
    trackedEvents.length = 0;
    resetIdentityMock.mockImplementation(async () => {
      callOrder.push("resetIdentity");
    });
    clearTokensMock.mockImplementation(async () => {
      callOrder.push("clearTokens");
    });
    clearLocalUserDataMock.mockImplementation(async () => {
      callOrder.push("clearLocalUserData");
    });
    setAnalyticsProvider(new RecordingAnalyticsProvider());
  });

  afterEach(() => {
    setAnalyticsProvider(null);
  });

  it("204: account_deletedを送ってから解析用IDを作り直し、その後に端末データを消去する", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(204));

    await expect(deleteAccount()).resolves.toEqual({ ok: true });

    expect(callOrder).toEqual([
      "track:account_deleted",
      "resetIdentity",
      "clearTokens",
      "clearLocalUserData",
    ]);
  });

  it("204: account_deletedのpayloadにアカウントを特定できる値を含めない", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(204));

    await deleteAccount();

    expect(trackedEvents).toEqual([{ eventName: "account_deleted", payload: { platform: "mobile" } }]);
  });

  it("204: 解析用IDの作り直しに失敗しても退会完了として扱い、端末データは消去する", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(204));
    resetIdentityMock.mockRejectedValueOnce(new Error("posthog failure"));

    await expect(deleteAccount()).resolves.toEqual({ ok: true });
    expect(clearTokensMock).toHaveBeenCalledTimes(1);
    expect(clearLocalUserDataMock).toHaveBeenCalledTimes(1);
  });

  it("503: account_deletedを送らず、解析用IDも作り直さない", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response(503, "unavailable"));

    await deleteAccount();

    expect(trackedEvents).toEqual([]);
    expect(resetIdentityMock).not.toHaveBeenCalled();
  });

  it("ネットワークエラー: account_deletedを送らず、解析用IDも作り直さない", async () => {
    vi.spyOn(global, "fetch").mockRejectedValueOnce(new TypeError("Network request failed"));

    await deleteAccount();

    expect(trackedEvents).toEqual([]);
    expect(resetIdentityMock).not.toHaveBeenCalled();
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
