"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/AuthProvider";
import { ShrineSubmissionForm } from "@/features/shrine-submission/components/ShrineSubmissionForm";

export default function NewShrinePage() {
  const router = useRouter();
  const { isLoggedIn, loading } = useAuth();
  const [returnTo, setReturnTo] = useState("/shrines");

  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const nextReturnTo = params.get("returnTo") || "/shrines";
    setReturnTo(nextReturnTo);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!isLoggedIn) {
      router.replace(`/auth/login?returnTo=${encodeURIComponent(`/shrines/new?returnTo=${returnTo}`)}`);
    }
  }, [isLoggedIn, loading, returnTo, router]);

  if (loading || !isLoggedIn) {
    return <div className="mx-auto max-w-2xl px-4 py-10 text-sm text-slate-500">認証状態を確認しています...</div>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs text-emerald-700">Shrine Submission</p>
        <h1 className="mt-2 text-base font-semibold text-slate-900">神社を追加する</h1>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          神社名・住所・ご利益タグ・補足文をもとに審査され、承認後に神社データへ反映されます。
        </p>
      </div>

      <ShrineSubmissionForm
        onSubmitted={(submission) => {
          const next = new URLSearchParams();
          next.set("submitted", "1");
          next.set("status", submission.status);
          next.set("name", submission.name);
          router.replace(`${returnTo}${returnTo.includes("?") ? "&" : "?"}${next.toString()}`);
        }}
        onRequireAuth={() =>
          router.replace(`/auth/login?returnTo=${encodeURIComponent(`/shrines/new?returnTo=${returnTo}`)}`)
        }
      />
    </div>
  );
}
