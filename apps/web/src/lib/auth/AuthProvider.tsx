"use client";
// apps/web/src/lib/auth/AuthProvider.tsx

import { createContext, useContext, useEffect, useState } from "react";
import type { AuthState, AuthUser } from "@/lib/auth/types";

type AuthCtx = {
  user: AuthUser | null;
  loading: boolean;
  isLoggedIn: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

export const useAuth = () => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("AuthProvider is missing");
  return ctx;
};

const LS_AUTH = "auth:logged_in";

function markLoggedIn() {
  try {
    localStorage.setItem(LS_AUTH, "1");
  } catch {
    // ignore
  }
}

function markLoggedOut() {
  try {
    localStorage.removeItem(LS_AUTH);
  } catch {
    // ignore
  }
}

function maybeLoggedIn(): boolean {
  try {
    return localStorage.getItem(LS_AUTH) === "1";
  } catch {
    return false;
  }
}

async function fetchMe(): Promise<AuthUser | null> {
  
  try {
    const res = await fetch("/api/users/me/", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    });

    if (res.status === 401) {
      markLoggedOut();
      return null;
    }

    if (!res.ok) {
      throw new Error(`fetchMe failed: ${res.status}`);
    }

    const json = await res.json();
    const data = (json as any)?.user ?? json;
    return data as AuthUser;
  } catch {
    markLoggedOut();
    return null;
  }
}

function shouldAutoFetchMe(pathname: string | null): boolean {
  if (!pathname) return true;

  if (
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/auth/login" ||
    pathname === "/auth/register"
  ) {
    return false;
  }

  if (pathname === "/" || pathname.startsWith("/shrines/")) {
    return false;
  }

  if (pathname === "/concierge" || pathname.startsWith("/concierge/")) {
    return false;
  }

  if (pathname.startsWith("/concierge/full")) return true;

  return true;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    status: "unknown",
    user: null,
    isHydrating: true,
  });



  const refreshMe = async () => {
    const me = await fetchMe();

    setAuthState({
      status: me ? "authenticated" : "guest",
      user: me,
      isHydrating: false,
    });
  };

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      const initialPathname = window.location.pathname;
      const auto = shouldAutoFetchMe(initialPathname);
      const maybe = maybeLoggedIn();
      const shouldFetch = auto || maybe;

      if (!shouldFetch) {
        if (!cancelled) {
          setAuthState({
            status: "guest",
            user: null,
            isHydrating: false,
          });
        }
        return;
      }

      const me = await fetchMe();

      if (!cancelled) {
        setAuthState({
          status: me ? "authenticated" : "guest",
          user: me,
          isHydrating: false,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (username: string, password: string) => {
    const r = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!r.ok) throw new Error("login failed");

    markLoggedIn();
    await refreshMe();
  };

  const logout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    markLoggedOut();

    setAuthState({
      status: "guest",
      user: null,
      isHydrating: false,
    });
  };

  const user = authState.user;
  const loading = authState.isHydrating;
  const isLoggedIn = authState.status === "authenticated" && !!authState.user;

  return (
    <Ctx.Provider
      value={{
        user,
        loading,
        isLoggedIn,
        login,
        logout,
        refreshMe,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
