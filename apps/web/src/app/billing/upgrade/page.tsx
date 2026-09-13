"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";
import { startBillingCheckout } from "@/lib/api/billing";
import {
  parseBillingFunnelSource,
  parseBillingFunnelStep,
  trackBillingEvent,
  type BillingFunnelSource,
  type BillingFunnelStep,
} from "@/lib/analytics/billing";
import { useAuth } from "@/lib/auth/AuthProvider";

import { buildLoginHref } from "@/lib/nav/login";

const UPGRADE_ENTRY_CONTEXT_STORAGE_KEY = "upgrade:entry-context";

// 「今できること」だけを書く。将来予定・拡張予定はここに入れない。
const PREMIUM_VALUES = [
  "何度でも相談できる",
  "なぜ今、この神社なのかを深く知る",
  "前回からの自分の変化を振り返る",
] as const;

type UpgradeEntryContext = {
  entryPoint: BillingFunnelSource | null;
  entryStep: BillingFunnelStep | null;
  entryCardId: string | null;
  entryHistoryTheme: string | null;
};

function saveUpgradeEntryContext(entryContext: UpgradeEntryContext) {
  try {
    window.sessionStorage.setItem(
      UPGRADE_ENTRY_CONTEXT_STORAGE_KEY,
      JSON.stringify(entryContext),
    );
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[billing attribution]", error);
    }
  }
}

function BillingUpgradeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const auth = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const upgradeClickTrackedRef = useRef(false);
  const checkoutStartedTrackedRef = useRef(false);
  const source = parseBillingFunnelSource(searchParams.get("source"));
  const funnelStep = parseBillingFunnelStep(searchParams.get("funnelStep"));
  const cardId = searchParams.get("cardId");
  const historyTheme = searchParams.get("historyTheme");

  const startCheckout = async () => {
    if (auth.loading) return;

    const entryContext = {
      entryPoint: source,
      entryStep: funnelStep,
      entryCardId: cardId,
      entryHistoryTheme: historyTheme,
    };

    saveUpgradeEntryContext(entryContext);

    if (!upgradeClickTrackedRef.current) {
      upgradeClickTrackedRef.current = true;
      trackBillingEvent("upgrade_click", {
        source,
        funnelStep,
        cardId,
        historyTheme,
      });
    }

    if (!auth.isLoggedIn) {
      const currentPath = `/billing/upgrade${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
      router.push(buildLoginHref(currentPath));
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const session = await startBillingCheckout();
      if (!checkoutStartedTrackedRef.current) {
        checkoutStartedTrackedRef.current = true;
        trackBillingEvent("checkout_started", {
          checkoutSessionId: session.session_id,
          source,
          funnelStep,
          cardId,
          historyTheme,
        });
      }
      window.location.assign(session.checkout_url);
    } catch {
      setError("決済画面を開始できませんでした。時間をおいて再度お試しください。");
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <section className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-900">KAMI MUSUBI Premium</h1>
        <p className="text-sm leading-6 text-slate-600">
          一度の答えではなく、変化を重ねていくために。
        </p>
      </section>

      <section className="mt-6 rounded-2xl border bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Premiumでできること</h2>
        <ul className="mt-3 space-y-3 text-sm text-slate-700">
          {PREMIUM_VALUES.map((value) => (
            <li key={value} className="flex gap-2">
              <span aria-hidden="true" className="mt-[2px] text-[var(--kt-color-premium-accent)]">
                ●
              </span>
              <span>{value}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4 rounded-2xl border bg-white p-4 shadow-sm">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--kt-color-premium-accent)]">
          β Early User価格
        </p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">780円 / 月</p>
        <p className="mt-1 text-xs leading-5 text-slate-600">β期間中の初期ユーザー向け価格です。</p>
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
          {submitting ? "決済画面を準備中…" : "Premiumを始める"}
        </button>
        <p className="text-xs leading-5 text-slate-600">
          プランはStripeの管理画面から変更・解約できます。
        </p>
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

export default function BillingUpgradePage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto w-full max-w-md px-4 py-6">
          <p className="text-sm leading-6 text-slate-600">プレミアム登録画面を準備しています...</p>
        </main>
      }
    >
      <BillingUpgradeContent />
    </Suspense>
  );
}
