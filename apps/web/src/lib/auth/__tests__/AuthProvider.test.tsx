import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// pathname を制御
let mockPathname = "/shrines/123";
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

// API モック
const getCurrentUser = vi.fn();
vi.mock("@/lib/api/users", () => ({
  getCurrentUser,
}));

import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";

function Probe() {
  const { loading, isLoggedIn } = useAuth();
  return (
    <div
      data-testid="probe"
      data-loading={String(loading)}
      data-logged-in={String(isLoggedIn)}
    />
  );
}

describe("AuthProvider 認証分岐", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("未ログイン + shrine 詳細では users/me を叩かない", async () => {
    mockPathname = "/shrines/123";

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("probe")).toHaveAttribute("data-loading", "false");
    });

    expect(getCurrentUser).not.toHaveBeenCalled();
    expect(screen.getByTestId("probe")).toHaveAttribute("data-logged-in", "false");
  });
});
