import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";

function TestConsumer() {
  const { user, loading, isLoggedIn, login } = useAuth();

  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <div data-testid="logged-in">{isLoggedIn ? "yes" : "no"}</div>
      <div data-testid="username">{user?.username ?? "__NONE__"}</div>
      <button
        type="button"
        onClick={() => {
          void login("tester", "password123").catch(() => {});
        }}
      >
        do-login
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);

        if (url === "/api/auth/login") {
          return {
            ok: true,
            status: 200,
            json: async () => ({}),
          } as Response;
        }

        if (url === "/api/users/me/") {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              user: {
                id: 1,
                username: "tester",
                email: "tester@example.com",
              },
            }),
          } as Response;
        }

        throw new Error(`unexpected fetch: ${url} ${init?.method ?? "GET"}`);
      }),
    );
  });

  it("login 成功後に /api/users/me/ を再取得して auth state を更新する", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });

    expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    expect(screen.getByTestId("username")).toHaveTextContent("__NONE__");

    await act(async () => {
      screen.getByRole("button", { name: "do-login" }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("logged-in")).toHaveTextContent("yes");
    });

    expect(screen.getByTestId("username")).toHaveTextContent("tester");

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "tester", password: "password123" }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/users/me/",
      expect.objectContaining({
        method: "GET",
        credentials: "same-origin",
        cache: "no-store",
      }),
    );
  });

  it("login 失敗時は auth state を更新しない", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);

        if (url === "/api/auth/login") {
          return {
            ok: false,
            status: 401,
            json: async () => ({}),
          } as Response;
        }

        if (url === "/api/users/me/") {
          return {
            ok: false,
            status: 401,
            json: async () => ({}),
          } as Response;
        }

        throw new Error(`unexpected fetch: ${url}`);
      }),
    );

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });

    await act(async () => {
      screen.getByRole("button", { name: "do-login" }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("logged-in")).toHaveTextContent("no");
    });

    expect(screen.getByTestId("username")).toHaveTextContent("__NONE__");

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });
});
