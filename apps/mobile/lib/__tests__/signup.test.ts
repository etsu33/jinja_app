import { beforeEach, describe, expect, it, vi } from "vitest";

const setTokensMock = vi.fn();

vi.mock("../authTokens", () => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  isExpiringSoon: vi.fn(),
  setAccessToken: vi.fn(),
  setTokens: (...args: unknown[]) => setTokensMock(...args),
}));

import {
  SIGNUP_MESSAGES,
  parseSignupFieldErrors,
  signupAndLogin,
  validateSignupInput,
} from "../signup";

function jsonResponse(status: number, body: unknown): Response {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => JSON.parse(text),
    text: async () => text,
  } as Response;
}

const input = { username: " alice ", email: " alice@example.com ", password: "password123" };

describe("signupAndLogin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("成功: signup → jwt/create の順に呼び、setTokens してokを返す", async () => {
    const fetchSpy = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(jsonResponse(201, { id: 1, username: "alice" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "acc", refresh: "ref" }));

    const result = await signupAndLogin(input);

    expect(result).toEqual({ ok: true, kind: "success" });
    expect(fetchSpy).toHaveBeenCalledTimes(2);

    const [signupUrl, signupInit] = fetchSpy.mock.calls[0];
    expect(String(signupUrl)).toMatch(/\/users\/signup\/$/);
    expect(signupInit?.method).toBe("POST");
    expect(JSON.parse(String(signupInit?.body))).toEqual({
      username: "alice",
      email: "alice@example.com",
      password: "password123",
    });

    const [loginUrl, loginInit] = fetchSpy.mock.calls[1];
    expect(String(loginUrl)).toMatch(/\/auth\/jwt\/create\/$/);
    expect(JSON.parse(String(loginInit?.body))).toEqual({ username: "alice", password: "password123" });

    expect(setTokensMock).toHaveBeenCalledWith("acc", "ref");
  });

  it("成功: Backendが正規化したusernameを返した場合はそれでログインする", async () => {
    const fetchSpy = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(jsonResponse(201, { username: "alice_normalized" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "acc", refresh: "ref" }));

    await signupAndLogin(input);

    expect(JSON.parse(String(fetchSpy.mock.calls[1][1]?.body)).username).toBe("alice_normalized");
  });

  it("400: フィールドエラーを項目ごとに返し、ログインは呼ばない", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(
      jsonResponse(400, {
        username: ["A user with that username already exists."],
        email: ["Enter a valid email address."],
      }),
    );

    const result = await signupAndLogin(input);

    expect(result).toEqual({
      ok: false,
      kind: "validation",
      errors: {
        username: "A user with that username already exists.",
        email: "Enter a valid email address.",
      },
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(setTokensMock).not.toHaveBeenCalled();
  });

  it("自動ログイン失敗: アカウント作成済みとしてautoLoginFailedを返し、トークンは保存しない", async () => {
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(jsonResponse(201, { username: "alice" }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: "No active account" }));

    const result = await signupAndLogin(input);

    expect(result).toEqual({ ok: false, kind: "autoLoginFailed", message: SIGNUP_MESSAGES.autoLoginFailed });
    expect(setTokensMock).not.toHaveBeenCalled();
  });

  it("409: ユーザー名重複のメッセージを返す", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse(409, ""));
    await expect(signupAndLogin(input)).resolves.toEqual({
      ok: false,
      kind: "conflict",
      message: SIGNUP_MESSAGES.conflict,
    });
  });

  it("500: サーバーエラーのメッセージを返す", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse(500, ""));
    await expect(signupAndLogin(input)).resolves.toMatchObject({ ok: false, kind: "server" });
  });

  it("ネットワークエラー: 通信失敗のメッセージを返す", async () => {
    vi.spyOn(global, "fetch").mockRejectedValueOnce(new TypeError("Network request failed"));
    await expect(signupAndLogin(input)).resolves.toEqual({
      ok: false,
      kind: "network",
      message: SIGNUP_MESSAGES.network,
    });
  });
});

describe("parseSignupFieldErrors", () => {
  it("項目外のキーはformにまとめる", () => {
    expect(parseSignupFieldErrors(JSON.stringify({ password: ["too short"], non_field_errors: ["x", "y"] }))).toEqual({
      password: "too short",
      form: "x y",
    });
  });

  it("JSONでない本文はそのままformに入れる", () => {
    expect(parseSignupFieldErrors("Bad Request")).toEqual({ form: "Bad Request" });
  });

  it("空の本文はフォールバック文言にする", () => {
    expect(parseSignupFieldErrors("")).toEqual({ form: SIGNUP_MESSAGES.validationFallback });
  });
});

describe("validateSignupInput", () => {
  it("未入力・形式不正・8文字未満を項目ごとに返す", () => {
    expect(validateSignupInput({ username: " ", email: "foo", password: "1234567" })).toEqual({
      username: SIGNUP_MESSAGES.usernameRequired,
      email: SIGNUP_MESSAGES.emailInvalid,
      password: SIGNUP_MESSAGES.passwordTooShort,
    });
  });

  it("正しい入力ではエラーなし", () => {
    expect(validateSignupInput({ username: "a", email: "a@b.co", password: "12345678" })).toEqual({});
  });
});
