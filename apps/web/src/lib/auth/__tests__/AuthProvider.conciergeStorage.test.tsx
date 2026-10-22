// login / logout の境界で、identity を含まない相談 state の browser storage を次の identity に残さない。
// docs/audit/concierge-thread-authorization-isolation-audit.md
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import { AuthProvider, useAuth } from "@/lib/auth/AuthProvider";
import {
  CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY,
  CONCIERGE_EVENTS_STORAGE_KEY,
} from "@/lib/concierge/conciergeLocalState";

function Consumer() {
  const { loading, login, logout } = useAuth();
  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <button type="button" onClick={() => void login("tester", "password123").catch(() => {})}>
        do-login
      </button>
      <button type="button" onClick={() => void logout()}>
        do-logout
      </button>
    </div>
  );
}

function seedConciergeStorage() {
  localStorage.setItem(CONCIERGE_EVENTS_STORAGE_KEY, JSON.stringify({ 88: [{ type: "assistant_state" }] }));
  sessionStorage.setItem(CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY, JSON.stringify({ version: 1 }));
}

describe("AuthProvider concierge storage boundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/api/auth/login" || url === "/api/auth/logout") {
          return { ok: true, status: 200, json: async () => ({}) } as Response;
        }
        if (url === "/api/users/me/") {
          return {
            ok: true,
            status: 200,
            json: async () => ({ user: { id: 1, username: "tester", email: "tester@example.com" } }),
          } as Response;
        }
        throw new Error(`unexpected fetch: ${url}`);
      }),
    );
  });

  it("logout は相談 thread cache と匿名相談 snapshot を消す", async () => {
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("ready"));
    seedConciergeStorage();

    await act(async () => {
      screen.getByRole("button", { name: "do-logout" }).click();
    });

    await waitFor(() => expect(localStorage.getItem(CONCIERGE_EVENTS_STORAGE_KEY)).toBeNull());
    expect(sessionStorage.getItem(CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY)).toBeNull();
  });

  it("login は前の identity の相談 thread cache を消し、同じタブの匿名相談 snapshot は残す", async () => {
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("ready"));
    seedConciergeStorage();

    await act(async () => {
      screen.getByRole("button", { name: "do-login" }).click();
    });

    await waitFor(() => expect(localStorage.getItem(CONCIERGE_EVENTS_STORAGE_KEY)).toBeNull());
    expect(sessionStorage.getItem(CONCIERGE_ANON_SNAPSHOT_STORAGE_KEY)).not.toBeNull();
  });
});
