import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import SignupForm from "../SignupForm";

const signupMock = vi.fn();
const loginApiMock = vi.fn();

vi.mock("@/lib/api/auth", () => ({
  signup: (...args: unknown[]) => signupMock(...args),
  login: (...args: unknown[]) => loginApiMock(...args),
}));

describe("SignupForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    signupMock.mockReset();
    loginApiMock.mockReset();
  });

  it("signup + loginApi 成功時に両方の API を正しい引数で呼ぶ", async () => {
    signupMock.mockResolvedValue(undefined);
    loginApiMock.mockResolvedValue(undefined);

    const { container } = render(<SignupForm returnTo="/shrines/1?ctx=concierge" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[1], { target: { value: "tester@example.com" } });
    fireEvent.change(inputs[2], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
        email: "tester@example.com",
      });
    });

    expect(loginApiMock).toHaveBeenCalledWith({
      username: "tester",
      password: "password123",
    });
  });

  it("returnTo 未指定でも signup + loginApi を呼ぶ", async () => {
    signupMock.mockResolvedValue(undefined);
    loginApiMock.mockResolvedValue(undefined);

    const { container } = render(<SignupForm />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[2], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
        email: undefined,
      });
    });

    expect(loginApiMock).toHaveBeenCalledWith({
      username: "tester",
      password: "password123",
    });
  });

  it("password が短い時は API を呼ばない", () => {
    const { container } = render(<SignupForm returnTo="/mypage?tab=favorites" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[2], { target: { value: "short" } });
    fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

    expect(signupMock).not.toHaveBeenCalled();
    expect(loginApiMock).not.toHaveBeenCalled();
    expect(screen.getByText("ユーザー名と8文字以上のパスワードを入力してください")).toBeInTheDocument();
  });

  it("signup 失敗時は loginApi を呼ばずエラー表示を出す", async () => {
    signupMock.mockRejectedValue({
      response: {
        status: 409,
      },
    });

    const { container } = render(<SignupForm returnTo="/mypage?tab=favorites" />);

    const inputs = container.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "tester" } });
    fireEvent.change(inputs[2], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        username: "tester",
        password: "password123",
        email: undefined,
      });
    });

    expect(loginApiMock).not.toHaveBeenCalled();
    expect(await screen.findByText("そのユーザー名は既に使われています。")).toBeInTheDocument();
  });
});
