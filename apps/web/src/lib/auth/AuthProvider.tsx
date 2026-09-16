"use client";
// apps/web/src/lib/auth/AuthProvider.tsx

import { createContext, useContext, useEffect, useState } from "react";
import type { AuthState, AuthUser } from "@/lib/auth/types";
import { markLoggedIn, markLoggedOut, maybeLoggedIn } from "@/lib/auth/loggedInMarker";

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

/**
 * `/api/users/me/` の結果分類。
 *
 * 「認証されていないことが確定した」と「確認できなかった」を必ず区別する。
 * これを一緒くたに null へ潰すと、一過性の失敗で logged-in マーカーが消え、
 * `shouldAutoFetchMe()` の除外 route（`/`・`/shrines/*`・`/concierge*`）では
 * 二度と `/me` を叩かないため、認証済みユーザーが Guest に固着する
 * （docs/audit/beta-core-flow-e2e-audit.md E2E-004）。
 */
type MeResult =
  | { kind: "authenticated"; user: AuthUser }
  | { kind: "unauthenticated" }
  | { kind: "indeterminate" };

/**
 * `/api/users/me/` を1回だけ問い合わせ、結果を分類する。
 *
 * 401 のみを「session 無効の確定シグナル」として扱う。Backend の
 * `MeView` は `JWTAuthentication` + `IsAuthenticated` で、
 * `JWTAuthentication.authenticate_header()` が非空を返すため DRF の
 * 401→403 coercion が起きない。つまりこの endpoint が認証理由で 403 を
 * 返す経路は存在せず、401 以外の失敗はすべて「確認できなかった」である。
 *
 * この関数はマーカーを書き換えない。状態遷移は applyMeResult() に一本化する。
 */
async function fetchMe(): Promise<MeResult> {
  let res: Response;

  try {
    res = await fetch("/api/users/me/", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    // transport failure（offline / DNS / abort / timeout）。session の有効性は不明。
    return { kind: "indeterminate" };
  }

  if (res.status === 401) {
    return { kind: "unauthenticated" };
  }

  // 5xx / 502 / 504 / その他の非 2xx。Backend や BFF が落ちているだけで、
  // session が無効になったことの証拠にはならない。
  if (!res.ok) {
    return { kind: "indeterminate" };
  }

  try {
    const json = await res.json();
    const data = (json as any)?.user ?? json;
    if (!data) return { kind: "indeterminate" };
    return { kind: "authenticated", user: data as AuthUser };
  } catch {
    // 200 だが JSON として読めない（proxy の差し込み等）。判定不能。
    return { kind: "indeterminate" };
  }
}

/**
 * MeResult を AuthState とマーカーへ反映する唯一の場所。
 *
 * - authenticated : マーカーを貼り直す。除外 route で marker だけが失われた
 *                   ケース（storage の eviction 等）から自己回復させるため。
 *                   Backend の 200 が根拠なので認証を捏造することはない。
 * - unauthenticated: マーカーを消し、stale な identity を残さず Guest へ。
 * - indeterminate  : マーカーを触らない。= 次のマウント / refreshMe() で
 *                    再試行できる。認証済みとしては描画しない（fail-closed）。
 */
function applyMeResult(result: MeResult): AuthState {
  if (result.kind === "authenticated") {
    markLoggedIn();
    return { status: "authenticated", user: result.user, isHydrating: false };
  }

  if (result.kind === "unauthenticated") {
    markLoggedOut();
    return { status: "guest", user: null, isHydrating: false };
  }

  return { status: "unknown", user: null, isHydrating: false };
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
    setAuthState(applyMeResult(await fetchMe()));
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

      const result = await fetchMe();

      if (!cancelled) {
        setAuthState(applyMeResult(result));
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
