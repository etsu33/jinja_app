import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

const getRefreshTokenMock = vi.fn();
const postMock = vi.fn();
const postAuthMock = vi.fn();

vi.mock("../authTokens", () => ({
  getRefreshToken: (...args: unknown[]) => getRefreshTokenMock(...args),
}));

vi.mock("../http", async () => {
  const actual = await vi.importActual<typeof import("../http")>("../http");
  return {
    ...actual,
    post: (...args: unknown[]) => postMock(...args),
    postAuth: (...args: unknown[]) => postAuthMock(...args),
  };
});

import { HttpError, UnauthenticatedError } from "../http";
import { postConciergeChat } from "../conciergeChatRequest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const body = { version: 1, mode: "need", query: "仕事の迷いを整理したい" };

describe("postConciergeChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ログインしていなければ、ログイン情報を付けずに送る", async () => {
    getRefreshTokenMock.mockResolvedValue(null);
    postMock.mockResolvedValue({ ok: true });
    expect(await postConciergeChat(body)).toEqual({ ok: true });
    expect(postMock).toHaveBeenCalledWith("/concierge/chat/", body);
    expect(postAuthMock).not.toHaveBeenCalled();
  });

  it("ログイン中は、ログイン情報を付けて送る", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    postAuthMock.mockResolvedValue({ ok: true, plan: "premium" });
    expect(await postConciergeChat(body)).toEqual({ ok: true, plan: "premium" });
    expect(postAuthMock).toHaveBeenCalledWith("/concierge/chat/", body);
    expect(postMock).not.toHaveBeenCalled();
  });

  it("トークンが使えないときだけ、付けずに送り直す", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    postAuthMock.mockRejectedValue(new UnauthenticatedError());
    postMock.mockResolvedValue({ ok: true });
    expect(await postConciergeChat(body)).toEqual({ ok: true });
    expect(postMock).toHaveBeenCalledTimes(1);
  });

  it("ほかの失敗は送り直さずに投げる", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    postAuthMock.mockRejectedValue(new HttpError(500, "HTTP 500", ""));
    await expect(postConciergeChat(body)).rejects.toBeInstanceOf(HttpError);
    expect(postMock).not.toHaveBeenCalled();
  });

  it("コンシェルジュの画面はこの関数で送る", () => {
    const screen = readFileSync(resolve(mobileRoot, "app/(tabs)/concierge/index.tsx"), "utf8");
    expect(screen).toContain("await postConciergeChat<ConciergeChatResponse>(payload)");
    expect(screen).not.toContain('post<ConciergeChatResponse>("/concierge/chat/"');
  });
});
