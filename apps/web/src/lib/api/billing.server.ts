import { cookies } from "next/headers";

import type { BillingStatus } from "@/lib/api/billing";

const FALLBACK_BILLING_STATUS: BillingStatus = {
  plan: "free",
  is_active: false,
  provider: "unknown",
  current_period_end: null,
  trial_ends_at: null,
  cancel_at_period_end: false,
};

export async function getBillingStatusServer(): Promise<BillingStatus> {
  try {
    const cookieStore = await cookies();
    const cookieHeader = cookieStore.toString();

    const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL ?? ""}/api/billings/status/`, {
      cache: "no-store",
      headers: cookieHeader ? { cookie: cookieHeader } : {},
    });

    if (!res.ok) return FALLBACK_BILLING_STATUS;
    return (await res.json()) as BillingStatus;
  } catch {
    return FALLBACK_BILLING_STATUS;
  }
}
