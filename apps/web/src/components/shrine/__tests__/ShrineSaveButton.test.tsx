import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";

// router mock
const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// auth mock
let authState = { isLoggedIn: false, loading: false };
vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => authState,
}));

// favorites API mock
const post = vi.fn();
vi.mock("@/lib/api/client", () => ({
  default: {
    post,
    delete: vi.fn(),
    get: vi.fn(),
  },
}));

import ShrineSaveButton from "../ShrineSaveButton";

describe("ShrineSaveButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState = { isLoggedIn: false, loading: false };
  });

  it("未ログイン時はクリックで login に遷移し API は呼ばれない", async () => {
    render(<ShrineSaveButton shrineId={1} />);

    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(push).toHaveBeenCalled();
    });

    expect(post).not.toHaveBeenCalled();
  });

  it("ログイン済み時は保存 API が呼ばれ、状態が切り替わる", async () => {
    authState = { isLoggedIn: true, loading: false };
    post.mockResolvedValue({ data: { id: 10 } });

    render(<ShrineSaveButton shrineId={1} />);

    const btn = screen.getByRole("button", { name: "保存する" });

    fireEvent.click(btn);

    await waitFor(() => {
      expect(post).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByRole("button")).toHaveTextContent("保存しました");
    });
  });
});
