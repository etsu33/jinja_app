import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import SignupForm from "../SignupForm";

const signupMock = vi.fn();
const loginApiMock = vi.fn();

vi.mock("@/lib/api/auth", () => ({
  signup: (...args: unknown[]) => signupMock(...args),
  login: (...args: unknown[]) => loginApiMock(...args),
}));

/** `@/lib/api/auth` の SignupRequestError と同じ形（status / data）を持つ失敗。 */
function signupFailure(status: number | null, data: unknown = null) {
  return Object.assign(new Error(`signup failed: ${status}`), { status, data });
}

function fillForm(
  container: HTMLElement,
  { username = "tester", email = "tester@example.com", password = "password123" } = {},
) {
  const inputs = container.querySelectorAll("input");
  fireEvent.change(inputs[0], { target: { value: username } });
  fireEvent.change(inputs[1], { target: { value: email } });
  fireEvent.change(inputs[2], { target: { value: password } });
}

function submit() {
  fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));
}

describe("SignupForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    signupMock.mockReset();
    loginApiMock.mockReset();
  });

  it("正常値では signup + loginApi を正しい引数で呼ぶ", async () => {
    signupMock.mockResolvedValue(undefined);
    loginApiMock.mockResolvedValue(undefined);

    const { container } = render(<SignupForm returnTo="/shrines/1?ctx=concierge" />);
    fillForm(container);
    submit();

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
        email: "tester@example.com",
      });
    });

    await waitFor(() => {
      expect(loginApiMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
      });
    });
  });

  it("signup response の正規化済み username を login に使う", async () => {
    signupMock.mockResolvedValue({
      id: 10,
      username: "qaテスト999",
    });
    loginApiMock.mockResolvedValue(undefined);

    const { container } = render(<SignupForm />);

    fillForm(container, {
      username: "qaテスト９９９",
      email: "tester@example.com",
      password: "password123",
    });

    submit();

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "qaテスト９９９",
        password: "password123",
        email: "tester@example.com",
      });
    });

    await waitFor(() => {
      expect(loginApiMock).toHaveBeenCalledWith({
        username: "qaテスト999",
        password: "password123",
      });
    });
  });

  it("returnTo 未指定でも signup + loginApi を呼ぶ", async () => {
    signupMock.mockResolvedValue(undefined);
    loginApiMock.mockResolvedValue(undefined);

    const { container } = render(<SignupForm />);
    fillForm(container);
    submit();

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
        email: "tester@example.com",
      });
    });

    await waitFor(() => {
      expect(loginApiMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
      });
    });
  });

  it("username 未入力では API を呼ばない", () => {
    const { container } = render(<SignupForm />);
    fillForm(container, { username: "" });
    submit();

    expect(signupMock).not.toHaveBeenCalled();
    expect(loginApiMock).not.toHaveBeenCalled();
    expect(screen.getByText("ユーザー名を入力してください")).toBeInTheDocument();
  });

  it("email 未入力では API を呼ばない", () => {
    const { container } = render(<SignupForm />);
    fillForm(container, { email: "" });
    submit();

    expect(signupMock).not.toHaveBeenCalled();
    expect(loginApiMock).not.toHaveBeenCalled();
    expect(screen.getByText("メールアドレスを入力してください")).toBeInTheDocument();
  });

  it("email 形式が不正では API を呼ばない", () => {
    const { container } = render(<SignupForm />);
    fillForm(container, { email: "not-an-email" });
    submit();

    expect(signupMock).not.toHaveBeenCalled();
    expect(loginApiMock).not.toHaveBeenCalled();
    expect(screen.getByText("メールアドレスの形式が正しくありません")).toBeInTheDocument();
  });

  it("password が 8 文字未満では API を呼ばない", () => {
    const { container } = render(<SignupForm returnTo="/mypage?tab=favorites" />);
    fillForm(container, { password: "short" });
    submit();

    expect(signupMock).not.toHaveBeenCalled();
    expect(loginApiMock).not.toHaveBeenCalled();
    expect(screen.getByText("パスワードは8文字以上で入力してください")).toBeInTheDocument();
  });

  it("Backend の validation error（400）は内容をそのまま表示する", async () => {
    signupMock.mockRejectedValue(
      signupFailure(400, {
        email: ["有効なメールアドレスを入力してください。"],
        username: ["この項目は必須です。"],
      }),
    );

    const { container } = render(<SignupForm />);
    fillForm(container);
    submit();

    expect(await screen.findByText(/有効なメールアドレスを入力してください。/)).toBeInTheDocument();
    expect(screen.getByText(/この項目は必須です。/)).toBeInTheDocument();
    expect(screen.queryByText("通信に失敗しました。")).not.toBeInTheDocument();
    expect(loginApiMock).not.toHaveBeenCalled();
  });

  it("400 で body が空でも generic な通信エラーにはしない", async () => {
    signupMock.mockRejectedValue(signupFailure(400, null));

    const { container } = render(<SignupForm />);
    fillForm(container);
    submit();

    expect(await screen.findByText("入力内容をご確認ください。")).toBeInTheDocument();
    expect(screen.queryByText("通信に失敗しました。")).not.toBeInTheDocument();
  });

  it("409 は username 重複として表示する", async () => {
    signupMock.mockRejectedValue(signupFailure(409));

    const { container } = render(<SignupForm returnTo="/mypage?tab=favorites" />);
    fillForm(container);
    submit();

    expect(await screen.findByText("そのユーザー名は既に使われています。")).toBeInTheDocument();
    expect(loginApiMock).not.toHaveBeenCalled();
  });

  it("server failure（502）は generic なサーバーエラーにする", async () => {
    signupMock.mockRejectedValue(
      signupFailure(502, { detail: "バックエンドに接続できません", code: "backend_unreachable" }),
    );

    const { container } = render(<SignupForm />);
    fillForm(container);
    submit();

    expect(await screen.findByText("サーバーエラーが発生しました。")).toBeInTheDocument();
  });

  it("network failure（status=null）は generic な通信エラーにする", async () => {
    signupMock.mockRejectedValue(signupFailure(null));

    const { container } = render(<SignupForm />);
    fillForm(container);
    submit();

    expect(await screen.findByText("通信に失敗しました。")).toBeInTheDocument();
  });
});
