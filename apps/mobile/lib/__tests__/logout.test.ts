import { beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

const clearTokensMock = vi.fn();
const clearLocalUserDataMock = vi.fn();
const getAuthMock = vi.fn();

vi.mock("../authTokens", () => ({
  clearTokens: (...args: unknown[]) => clearTokensMock(...args),
}));

vi.mock("../localUserData", () => ({
  clearLocalUserData: (...args: unknown[]) => clearLocalUserDataMock(...args),
}));

vi.mock("../http", () => ({
  getAuth: (...args: unknown[]) => getAuthMock(...args),
}));

import { setAnalyticsProvider, type AnalyticsPayload, type AnalyticsProvider } from "../analytics";
import {
  LOGOUT_MESSAGES,
  confirmLogout,
  fetchAccountUsername,
  logout,
  type LogoutAlertButton,
} from "../logout";

const trackedEvents: string[] = [];
const resetIdentityMock = vi.fn(async () => {});

class RecordingAnalyticsProvider implements AnalyticsProvider {
  track(eventName: string, _payload: AnalyticsPayload): void {
    trackedEvents.push(eventName);
  }
  resetIdentity(): Promise<void> {
    return resetIdentityMock();
  }
}

beforeEach(() => {
  clearTokensMock.mockReset();
  clearLocalUserDataMock.mockReset();
  getAuthMock.mockReset();
  resetIdentityMock.mockClear();
  trackedEvents.length = 0;
  setAnalyticsProvider(new RecordingAnalyticsProvider());
});

describe("logout", () => {
  it("ログインの印を消す(clearTokens を呼ぶ)", async () => {
    clearTokensMock.mockResolvedValue(undefined);

    await logout();

    expect(clearTokensMock).toHaveBeenCalledTimes(1);
  });

  it("PostHog の利用者の印は切り替えない(resetAnalyticsIdentity を呼ばない)", async () => {
    clearTokensMock.mockResolvedValue(undefined);

    await logout();

    expect(resetIdentityMock).not.toHaveBeenCalled();
  });

  it("ログアウトの印は PostHog に送らない", async () => {
    clearTokensMock.mockResolvedValue(undefined);

    await logout();

    expect(trackedEvents).toEqual([]);
  });

  it("端末内の利用者データ(clearLocalUserData)は消さない", async () => {
    clearTokensMock.mockResolvedValue(undefined);

    await logout();

    expect(clearLocalUserDataMock).not.toHaveBeenCalled();
  });

  it("バックエンドには何も送らない", async () => {
    clearTokensMock.mockResolvedValue(undefined);

    await logout();

    expect(getAuthMock).not.toHaveBeenCalled();
  });

  it("印の消去に失敗しても、例外を投げずにログアウトを終える", async () => {
    clearTokensMock.mockRejectedValue(new Error("storage unavailable"));

    await expect(logout()).resolves.toBeUndefined();
  });
});

describe("confirmLogout", () => {
  function captureAlert() {
    const calls: Array<{ title: string; message: string | undefined; buttons: LogoutAlertButton[] }> = [];
    const alert = (title: string, message: string | undefined, buttons: LogoutAlertButton[]) => {
      calls.push({ title, message, buttons });
    };
    return { alert, calls };
  }

  it("「ログアウトしますか？」の確認を出し、それだけでは何もしない", () => {
    const { alert, calls } = captureAlert();
    const onConfirm = vi.fn();

    confirmLogout(alert, onConfirm);

    expect(calls).toHaveLength(1);
    expect(calls[0].title).toBe("ログアウトしますか？");
    expect(calls[0].buttons.map((button) => button.text)).toEqual(["キャンセル", "ログアウト"]);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("「キャンセル」を選んでも何もしない", () => {
    const { alert, calls } = captureAlert();
    const onConfirm = vi.fn();

    confirmLogout(alert, onConfirm);
    calls[0].buttons.find((button) => button.text === LOGOUT_MESSAGES.cancel)?.onPress?.();

    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("「ログアウト」を選んだときだけ処理する", () => {
    const { alert, calls } = captureAlert();
    const onConfirm = vi.fn();

    confirmLogout(alert, onConfirm);
    calls[0].buttons.find((button) => button.text === LOGOUT_MESSAGES.confirmAction)?.onPress?.();

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("確認で「ログアウト」を選ばなければ、ログインの印は消えない", async () => {
    clearTokensMock.mockResolvedValue(undefined);
    const { alert, calls } = captureAlert();

    confirmLogout(alert, () => {
      void logout();
    });
    calls[0].buttons.find((button) => button.text === LOGOUT_MESSAGES.cancel)?.onPress?.();
    await Promise.resolve();

    expect(clearTokensMock).not.toHaveBeenCalled();
  });
});

describe("fetchAccountUsername", () => {
  it("GET /users/me/ の username を返す", async () => {
    getAuthMock.mockResolvedValue({ id: 1, username: "  etsuko  ", email: "x@example.com" });

    await expect(fetchAccountUsername()).resolves.toBe("etsuko");
    expect(getAuthMock).toHaveBeenCalledWith("/users/me/");
  });

  it.each([
    ["通信に失敗した", () => getAuthMock.mockRejectedValue(new Error("network"))],
    ["username が無い", () => getAuthMock.mockResolvedValue({ id: 1 })],
    ["username が空", () => getAuthMock.mockResolvedValue({ username: "   " })],
  ])("%sときは null(画面では「ログイン中」を出す)", async (_case, arrange) => {
    arrange();

    await expect(fetchAccountUsername()).resolves.toBeNull();
    expect(LOGOUT_MESSAGES.signedInFallbackName).toBe("ログイン中");
  });
});
