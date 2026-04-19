import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import LoginForm from "../LoginForm";

const loginMock = vi.fn();

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => ({
    login: loginMock,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    loginMock.mockReset();
  });

  it("login 成功時に login を正しい引数で呼ぶ", async () => {
    loginMock.mockResolvedValue(undefined);

    const { container } = render(<LoginForm next="/shrines/1?ctx=concierge" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[1], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("tester", "password123");
    });
  });

  it("next 未指定でも login を正しい引数で呼ぶ", async () => {
    loginMock.mockResolvedValue(undefined);

    const { container } = render(<LoginForm />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[1], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("tester", "password123");
    });
  });

  it("register link に returnTo が含まれる", () => {
    render(<LoginForm next="/shrines/1?ctx=concierge" />);

    expect(screen.getByRole("link", { name: "新規登録はこちら" })).toHaveAttribute(
      "href",
      "/auth/register?returnTo=%2Fshrines%2F1%3Fctx%3Dconcierge",
    );
  });

  it("username/password 未入力では login を呼ばない", () => {
    render(<LoginForm next="/shrines/1" />);

    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    expect(loginMock).not.toHaveBeenCalled();
    expect(screen.getByText("ユーザー名とパスワードを入力してください")).toBeInTheDocument();
  });

  it("前後空白入り入力ではエラーを出す", () => {
    const { container } = render(<LoginForm next="/shrines/1" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: " tester " } });
    fireEvent.change(inputs[1], { target: { value: " password123 " } });
    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    expect(loginMock).not.toHaveBeenCalled();
    expect(screen.getByText("ユーザー名/パスワードの前後に空白が入っています")).toBeInTheDocument();
  });

  it("login 失敗時はエラー表示を出す", async () => {
    loginMock.mockRejectedValue(new Error("login failed"));

    const { container } = render(<LoginForm next="/shrines/1?ctx=concierge" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[1], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("tester", "password123");
    });
    await waitFor(() => {

      expect(screen.getByText("ログインに失敗しました。")).toBeInTheDocument();
    
    });
  });
});
