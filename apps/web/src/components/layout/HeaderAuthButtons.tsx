"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { useAuth } from "@/lib/auth/AuthProvider";

export function HeaderAuthButtons() {
  const { isLoggedIn } = useAuth();
  const pathname = usePathname();
  const sp = useSearchParams();

  const current = pathname + (sp.toString() ? `?${sp.toString()}` : "");
  const loginHref = `/login?next=${encodeURIComponent(current)}`;

  // TODO: 御朱印帳リンクはバックエンド実装完了後に復活予定
  // const goshuinBookHref = "/mypage?tab=goshuin";

  return (
    <div className="flex items-center gap-2">
      {/* 
        TODO: 御朱印帳リンクはバックエンド実装完了後に復活
        <Link href={goshuinBookHref} className="rounded-full border border-border/50 bg-card px-3 py-1.5 text-xs font-medium text-foreground/70 transition-colors hover:bg-secondary hover:text-foreground">
          御朱印帳
        </Link>
      */}

      {!isLoggedIn && (
        <Link 
          href={loginHref} 
          className="rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
        >
          ログイン
        </Link>
      )}
    </div>
  );
}
