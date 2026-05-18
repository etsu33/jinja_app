import { cookies, headers as nextHeaders } from "next/headers";

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
    const headers = cookieHeader ? { Cookie: cookieHeader } : undefined;

    const requestHeaders = await nextHeaders();
    const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host");
    const proto = requestHeaders.get("x-forwarded-proto") ?? "http";
    const envOrigin = process.env.NEXT_PUBLIC_APP_URL?.trim();
    const origin = envOrigin || (host ? `${proto}://${host}` : "");
    const statusUrl = `${origin}/api/billings/status/`;


    const res = await fetch(statusUrl, {
      cache: "no-store",
      headers,
    });

    const text = await res.text();


    if (!res.ok) return FALLBACK_BILLING_STATUS;
    return JSON.parse(text) as BillingStatus;
  } catch {
    return FALLBACK_BILLING_STATUS;
  }
}
