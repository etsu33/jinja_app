"use client";

import Link from "next/link";
import { useMemo } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";

export function HeaderAuthButtons() {
  const { isLoggedIn, loading, logout } = useAuth();

  const pathname = usePathname();
  const sp = useSearchParams();

  const loginHref = useMemo(() => {
    const current = pathname + (sp?.toString() ? `?${sp.toString()}` : "");
    return buildLoginHref(current);
  }, [pathname, sp]);

  const myPageHref = "/mypage?tab=profile";

  return (
    <div className="flex items-center gap-2">
      <Link href={myPageHref} className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white">
        マイページ
      </Link>

      {!loading && isLoggedIn && (
        <button
          type="button"
          onClick={async () => {
            await logout();
            window.location.href = "/";
          }}
          className="rounded-md border border-stone-300 bg-white px-3 py-2 text-xs font-medium text-stone-700"
        >
          ログアウト
        </button>
      )}

      {!loading && !isLoggedIn && (
        <Link href={loginHref} className="rounded-md bg-orange-500 px-3 py-2 text-xs font-medium text-white">
          ログイン
        </Link>
      )}
    </div>
  );
}
