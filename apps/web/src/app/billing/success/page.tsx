"use client";

import { Suspense, useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useBilling } from "@/features/billing/hooks/useBilling";
import {
  parseBillingFunnelSource,
  parseBillingFunnelStep,
  trackBillingEvent,
  type BillingFunnelSource,
  type BillingFunnelStep,
} from "@/lib/analytics/billing";

const UPGRADE_ENTRY_CONTEXT_STORAGE_KEY = "upgrade:entry-context";

type UpgradeEntryContext = {
  entryPoint?: BillingFunnelSource | null;
  entryStep?: BillingFunnelStep | null;
  entryCardId?: string | null;
  entryHistoryTheme?: string | null;
};

type BillingAnalyticsAttribution = {
  source?: BillingFunnelSource | null;
  funnelStep?: BillingFunnelStep | null;
  cardId?: string | null;
  historyTheme?: string | null;
};

function readUpgradeEntryContext(): UpgradeEntryContext {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.sessionStorage.getItem(UPGRADE_ENTRY_CONTEXT_STORAGE_KEY);
    if (!raw) return {};

    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return {};

    return {
      entryPoint: typeof parsed.entryPoint === "string" ? parseBillingFunnelSource(parsed.entryPoint) : null,
      entryStep: typeof parsed.entryStep === "string" ? parseBillingFunnelStep(parsed.entryStep) : null,
      entryCardId: typeof parsed.entryCardId === "string" ? parsed.entryCardId : null,
      entryHistoryTheme: typeof parsed.entryHistoryTheme === "string" ? parsed.entryHistoryTheme : null,
    };
  } catch {
    return {};
  }
}

function toBillingAnalyticsAttribution(entryContext: UpgradeEntryContext): BillingAnalyticsAttribution {
  return {
    source: entryContext.entryPoint ?? null,
    funnelStep: entryContext.entryStep ?? null,
    cardId: entryContext.entryCardId ?? null,
    historyTheme: entryContext.entryHistoryTheme ?? null,
  };
}

function BillingSuccessContent() {
  const searchParams = useSearchParams();
  const billing = useBilling();
  const sessionId = searchParams.get("checkout_session_id") ?? searchParams.get("session_id");
  const isPremiumActive = billing.status?.plan === "premium" && billing.status.is_active === true;
  const checkoutSuccessTrackedRef = useRef(false);
  const premiumActiveTrackedRef = useRef(false);

  useEffect(() => {
    if (checkoutSuccessTrackedRef.current) return;
    checkoutSuccessTrackedRef.current = true;
    const funnelAttribution = toBillingAnalyticsAttribution(readUpgradeEntryContext());
    trackBillingEvent("checkout_success", {
      checkoutSessionId: sessionId,
      ...funnelAttribution,
    });
  }, [sessionId]);

  useEffect(() => {
    if (!isPremiumActive || premiumActiveTrackedRef.current) return;
    premiumActiveTrackedRef.current = true;
    const funnelAttribution = toBillingAnalyticsAttribution(readUpgradeEntryContext());
    trackBillingEvent("premium_active", {
      checkoutSessionId: sessionId,
      ...funnelAttribution,
    });
  }, [isPremiumActive, sessionId]);

  if (!sessionId) {
    return (
      <div className="mx-auto w-full max-w-md px-4 py-6">
        <h1 className="text-xl font-semibold text-slate-900">決済セッションを確認できません</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">もう一度プレミアム登録を開始してください。</p>
        <Link
          href="/billing/upgrade"
          className="mt-6 inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
        >
          プレミアム登録へ戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-semibold text-slate-900">
        {isPremiumActive ? "プレミアムが有効になりました" : "決済結果を確認しています"}
      </h1>

      {billing.loading ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">プラン状況を再取得しています…</p>
      ) : isPremiumActive ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">現在のプランに反映されています。</p>
      ) : (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          決済完了後の反映待ちです。少し時間をおいてからプラン状況を再確認してください。
        </div>
      )}

      {billing.error ? <p className="mt-3 text-sm text-red-600">{billing.error}</p> : null}

      <div className="mt-6 flex flex-col gap-2">
        <button
          type="button"
          onClick={() => void billing.refresh()}
          className="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
        >
          プラン状況を再確認する
        </button>
        <Link
          href={isPremiumActive ? "/billing" : "/billing/upgrade"}
          className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
        >
          {isPremiumActive ? "プラン状況を見る" : "もう一度登録を開始する"}
        </Link>
      </div>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto w-full max-w-md px-4 py-6">
          <p className="text-sm leading-6 text-slate-600">課金状態を確認しています...</p>
        </main>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  );
}
