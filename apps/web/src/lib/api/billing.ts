import type { BillingPassType } from "@/lib/billing/passes";

export type BillingStatus = {
  plan: "free" | "premium";
  is_active: boolean;
  provider: "stub" | "stripe" | "revenuecat" | "unknown";
  current_period_end: string | null;
  trial_ends_at: string | null;
  /** 月額の自動更新を廃止したため、いつも false（backend の互換のために残っている項目）。 */
  cancel_at_period_end: boolean;
};

export type BillingCheckoutSession = {
  session_id: string;
  checkout_url: string;
};


export async function getBillingStatus(): Promise<BillingStatus> {
  const res = await fetch("/api/billings/status/", {
    cache: "no-store",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`billing status ${res.status}`);
  return (await res.json()) as BillingStatus;
}

/** 買い切りの旅行パス（1日・7日・14日）の購入を始める。 */
export async function startBillingCheckout(passType: BillingPassType): Promise<BillingCheckoutSession> {
  const res = await fetch("/api/billings/checkout", {
    method: "POST",
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ pass_type: passType }),
  });

  if (!res.ok) throw new Error(`billing checkout ${res.status}`);

  const data = (await res.json()) as BillingCheckoutSession;
  if (!data.checkout_url) throw new Error("checkout url missing");
  return data;
}
