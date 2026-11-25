import { beforeEach, describe, expect, it, vi } from "vitest";

const getRefreshTokenMock = vi.fn();
const getAuthMock = vi.fn();
const patchAuthMock = vi.fn();

vi.mock("../authTokens", () => ({
  getRefreshToken: (...args: unknown[]) => getRefreshTokenMock(...args),
}));

vi.mock("../http", async () => {
  const actual = await vi.importActual<typeof import("../http")>("../http");
  return {
    ...actual,
    getAuth: (...args: unknown[]) => getAuthMock(...args),
    patchAuth: (...args: unknown[]) => patchAuthMock(...args),
  };
});

import { HttpError, UnauthenticatedError } from "../http";
import { pullBirthdayFromServer, pushBirthdayToServer, syncBirthdayWithServer } from "../birthdaySync";

describe("birthdaySync", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ログインしていなければサーバーに送らない", async () => {
    getRefreshTokenMock.mockResolvedValue(null);
    expect(await pushBirthdayToServer("1990-07-15")).toBe("skipped");
    expect(patchAuthMock).not.toHaveBeenCalled();
    expect(await pullBirthdayFromServer()).toBeNull();
    expect(getAuthMock).not.toHaveBeenCalled();
  });

  it("ログイン中は PATCH /users/me/ に生年月日を送る", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    patchAuthMock.mockResolvedValue({});
    expect(await pushBirthdayToServer("1990-7-5")).toBe("saved");
    expect(patchAuthMock).toHaveBeenCalledWith("/users/me/", { birthday: "1990-07-05" });
  });

  it("不正な日付は送らない", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    expect(await pushBirthdayToServer("不正")).toBe("skipped");
    expect(await pushBirthdayToServer("2999-01-01")).toBe("skipped");
    expect(patchAuthMock).not.toHaveBeenCalled();
  });

  it("送信に失敗しても例外を投げない", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    patchAuthMock.mockRejectedValue(new HttpError(500, "HTTP 500", ""));
    expect(await pushBirthdayToServer("1990-07-15")).toBe("failed");
    patchAuthMock.mockRejectedValue(new UnauthenticatedError());
    expect(await pushBirthdayToServer("1990-07-15")).toBe("skipped");
  });

  it("サーバーに値があり端末と違えば、サーバーの値を端末に入れる", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    getAuthMock.mockResolvedValue({ profile: { birthday: "1985-01-02" } });
    const setLocal = vi.fn();
    expect(await syncBirthdayWithServer({ localBirthday: "1990-07-15", setLocalBirthday: setLocal })).toBe("pulled");
    expect(setLocal).toHaveBeenCalledWith("1985-01-02");
    expect(patchAuthMock).not.toHaveBeenCalled();
  });

  it("サーバーに値が無く端末にあれば、端末の値を送る", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    getAuthMock.mockResolvedValue({ profile: { birthday: null } });
    patchAuthMock.mockResolvedValue({});
    const setLocal = vi.fn();
    expect(await syncBirthdayWithServer({ localBirthday: "1990-07-15", setLocalBirthday: setLocal })).toBe("pushed");
    expect(setLocal).not.toHaveBeenCalled();
    expect(patchAuthMock).toHaveBeenCalledWith("/users/me/", { birthday: "1990-07-15" });
  });

  it("同じ値なら何もしない", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    getAuthMock.mockResolvedValue({ profile: { birthday: "1990-07-15" } });
    const setLocal = vi.fn();
    expect(await syncBirthdayWithServer({ localBirthday: "1990-07-15", setLocalBirthday: setLocal })).toBe("unchanged");
    expect(setLocal).not.toHaveBeenCalled();
    expect(patchAuthMock).not.toHaveBeenCalled();
  });
});
