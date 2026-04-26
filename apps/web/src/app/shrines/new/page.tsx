"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/AuthProvider";
import { ShrineSubmissionForm } from "@/features/shrine-submission/components/ShrineSubmissionForm";

import { sanitizeReturnTo } from "@/lib/nav/login";

function normalizeSubmissionReturnTo(value: string): string {
  if (!value.startsWith("/mypage")) return value;

  const [path, query = ""] = value.split("?");
  const params = new URLSearchParams(query);
  params.set("tab", "submissions");
  const qs = params.toString();

  return qs ? `${path}?${qs}` : `${path}?tab=submissions`;
}

export default function NewShrinePage() {
  const router = useRouter();
  const { isLoggedIn, loading } = useAuth();
  const [returnTo, setReturnTo] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const rawReturnTo = params.get("returnTo");
    const nextReturnTo = sanitizeReturnTo(rawReturnTo) ?? "/shrines";
    setReturnTo(nextReturnTo);

    if (rawReturnTo !== nextReturnTo) {
      const next = new URLSearchParams(params.toString());
      next.set("returnTo", nextReturnTo);
      const qs = next.toString();
      router.replace(qs ? `/shrines/new?${qs}` : "/shrines/new");
    }
  }, [router]);

  useEffect(() => {
    if (loading || returnTo === null) return;
    if (!isLoggedIn) {
      router.replace(`/auth/login?returnTo=${encodeURIComponent(`/shrines/new?returnTo=${returnTo}`)}`);
    }
  }, [isLoggedIn, loading, returnTo, router]);

  if (loading || returnTo === null || !isLoggedIn) {
    return <div className="mx-auto max-w-2xl px-4 py-10 text-sm text-slate-500">認証状態を確認しています...</div>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs text-emerald-700">Shrine Submission</p>
        <h1 className="mt-2 text-base font-semibold text-slate-900">神社を追加する</h1>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          投稿内容は確認後、公開検索や神社データに反映されます。住所・ご利益タグ・補足文があると、他の人にも見つけてもらいやすくなります。
        </p>
      </div>

      <ShrineSubmissionForm
        onSubmitted={(submission) => {
          const next = new URLSearchParams();
          next.set("submitted", "1");
          next.set("status", submission.status);
          next.set("name", submission.name);
          const safeReturnTo = normalizeSubmissionReturnTo(sanitizeReturnTo(returnTo) ?? "/shrines");
          router.replace(`${safeReturnTo}${safeReturnTo.includes("?") ? "&" : "?"}${next.toString()}`);
        }}
        onRequireAuth={() => {
          const safeReturnTo = sanitizeReturnTo(returnTo) ?? "/shrines";
          router.replace(`/auth/login?returnTo=${encodeURIComponent(`/shrines/new?returnTo=${safeReturnTo}`)}`);
        }}
      />
    </div>
  );
}
