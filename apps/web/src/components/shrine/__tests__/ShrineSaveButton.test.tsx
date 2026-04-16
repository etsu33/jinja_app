import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

let authState = { isLoggedIn: false, loading: false };
vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => authState,
}));

const post = vi.fn();
const del = vi.fn();
vi.mock("@/lib/api/client", () => ({
  default: {
    post,
    delete: del,
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
    expect(del).not.toHaveBeenCalled();
  });

  it("initial=true なら初期表示が保存済みになる", () => {
    authState = { isLoggedIn: true, loading: false };

    render(<ShrineSaveButton shrineId={1} initial />);

    expect(screen.getByRole("button")).toHaveTextContent("保存しました");
  });

  it("ログイン済み時は保存 API が呼ばれ、状態が切り替わる", async () => {
    authState = { isLoggedIn: true, loading: false };
    post.mockResolvedValue({ data: { id: 10 } });

    render(<ShrineSaveButton shrineId={1} />);

    fireEvent.click(screen.getByRole("button", { name: "保存する" }));

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith("/favorites/", { shrine_id: 1 });
    });

    expect(screen.getByRole("button")).toHaveTextContent("保存しました");
  });

  it("保存する → 保存しました → もう一度で 保存する に戻る", async () => {
    authState = { isLoggedIn: true, loading: false };
    post.mockResolvedValue({ data: { id: 10 } });
    del.mockResolvedValue({});

    render(<ShrineSaveButton shrineId={1} />);

    fireEvent.click(screen.getByRole("button", { name: "保存する" }));

    await waitFor(() => {
      expect(screen.getByRole("button")).toHaveTextContent("保存しました");
    });

    fireEvent.click(screen.getByRole("button", { name: "保存しました" }));

    await waitFor(() => {
      expect(del).toHaveBeenCalledWith("/favorites/10/");
    });

    expect(screen.getByRole("button")).toHaveTextContent("保存する");
  });
});
