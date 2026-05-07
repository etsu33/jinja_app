"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { startBillingCheckout } from "@/lib/api/billing";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";

export default function BillingUpgradePage() {
  const router = useRouter();
  const auth = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCheckout = async () => {
    if (auth.loading) return;

    if (!auth.isLoggedIn) {
      router.push(buildLoginHref("/billing/upgrade"));
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const session = await startBillingCheckout();
      window.location.assign(session.checkout_url);
    } catch {
      setError("決済画面を開始できませんでした。時間をおいて再度お試しください。");
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <section className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-900">もっと自分に合う神社提案を受け取りたい方へ</h1>
        <p className="text-sm leading-6 text-slate-600">
          プレミアムでは、より継続的にコンシェルジュ体験を使いやすくしていく予定です。
        </p>
      </section>

      <section className="mt-6 rounded-2xl border bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">無料プランとの違い</h2>
        <div className="mt-3 space-y-3 text-sm text-slate-700">
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="font-medium text-slate-900">無料</p>
            <p className="mt-1 text-slate-600">
              まずは気軽にコンシェルジュを試したい方向け。基本的な神社提案を利用できます。
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="font-medium text-slate-900">プレミアム</p>
            <p className="mt-1 text-slate-600">
              継続的に使いたい方向け。より自分に合った提案体験や、今後の拡張機能を使いやすくしていく予定です。
            </p>
          </div>
        </div>
      </section>

      {error ? (
        <section role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </section>
      ) : null}

      <div className="mt-6 flex flex-col gap-2">
        <button
          type="button"
          onClick={startCheckout}
          disabled={auth.loading || submitting}
          className="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
        >
          {submitting ? "決済画面を準備中…" : "プレミアムにする"}
        </button>
        <Link
          href="/billing"
          className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
        >
          プラン状況を確認する
        </Link>
      </div>
    </div>
  );
}
