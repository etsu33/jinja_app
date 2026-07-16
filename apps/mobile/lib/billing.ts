import { get, getAuth, isUnauthenticatedError, postAuth } from "./http";

export type BillingPlan = "free" | "premium";
export type BillingProvider = "stub" | "stripe" | "revenuecat" | "unknown";

export type BillingStatus = {
  plan: BillingPlan;
  is_active: boolean;
  provider: BillingProvider;
  current_period_end: string | null;
  trial_ends_at: string | null;
  cancel_at_period_end: boolean;
};

export type BillingCheckoutSession = {
  session_id: string;
  checkout_url: string;
};

export type CreateBillingCheckoutSessionParams = {
  successUrl: string;
  cancelUrl: string;
};

export class InvalidCheckoutResponseError extends Error {
  constructor(message = "Checkout response is invalid") {
    super(message);
    this.name = "InvalidCheckoutResponseError";
  }
}

const BILLING_PLAN_VALUES: readonly BillingPlan[] = ["free", "premium"];
const BILLING_PROVIDER_VALUES: readonly BillingProvider[] = ["stub", "stripe", "revenuecat", "unknown"];

const DEFAULT_BILLING_STATUS: BillingStatus = {
  plan: "free",
  is_active: false,
  provider: "unknown",
  current_period_end: null,
  trial_ends_at: null,
  cancel_at_period_end: false,
};

// --- APIレスポンスの防御的な型変換 ---
// backend/temples/api/views/billing.py の BillingStatusSerializer / CheckoutResponseSerializer に対応する。
// 想定外の型・欠損値が来ても例外を投げず、安全な既定値にフォールバックする。

function asPlan(value: unknown): BillingPlan {
  return typeof value === "string" && (BILLING_PLAN_VALUES as string[]).includes(value)
    ? (value as BillingPlan)
    : "free";
}

function asProvider(value: unknown): BillingProvider {
  return typeof value === "string" && (BILLING_PROVIDER_VALUES as string[]).includes(value)
    ? (value as BillingProvider)
    : "unknown";
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asNullableIsoString(value: unknown): string | null {
  if (typeof value !== "string" || !value.trim()) return null;
  return Number.isNaN(new Date(value).getTime()) ? null : value;
}

function parseBillingStatus(value: unknown): BillingStatus {
  const record = value && typeof value === "object" ? (value as Record<string, unknown>) : {};

  return {
    plan: asPlan(record.plan),
    is_active: asBoolean(record.is_active, false),
    provider: asProvider(record.provider),
    current_period_end: asNullableIsoString(record.current_period_end),
    trial_ends_at: asNullableIsoString(record.trial_ends_at),
    cancel_at_period_end: asBoolean(record.cancel_at_period_end, false),
  };
}

function isValidHttpUrl(value: unknown): value is string {
  if (typeof value !== "string" || !value.trim()) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

// --- 不正なCheckoutレスポンスのエラー処理 ---
// session_id / checkout_url が欠損・不正な場合は InvalidCheckoutResponseError を投げる。
// Checkoutはユーザー操作の結果なので、ここでは失敗を握りつぶさず呼び出し元に伝播させる。
function parseCheckoutSession(value: unknown): BillingCheckoutSession {
  const record = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const sessionId = typeof record.session_id === "string" ? record.session_id.trim() : "";

  if (!sessionId) {
    throw new InvalidCheckoutResponseError("Checkout response is missing session_id");
  }
  if (!isValidHttpUrl(record.checkout_url)) {
    throw new InvalidCheckoutResponseError("Checkout response is missing a valid checkout_url");
  }

  return { session_id: sessionId, checkout_url: record.checkout_url as string };
}

// --- Billing Status取得 (未認証可、AllowAny) ---
// 未ログイン時はstub/既定の課金状態を返すエンドポイントのため、通信失敗時もfreeの既定値にフォールバックする。
export async function getBillingStatus(): Promise<BillingStatus> {
  try {
    const data = await get<unknown>("/billings/status/");
    return parseBillingStatus(data);
  } catch (error) {
    if (__DEV__) {
      console.warn("[getBillingStatus] failed", error);
    }
    return { ...DEFAULT_BILLING_STATUS };
  }
}

// --- 認証付きBilling Status取得 ---
// ログインユーザー自身の正確な課金状態を取得する。未認証エラーは呼び出し元に伝播させる。
export async function getAuthenticatedBillingStatus(): Promise<BillingStatus | null> {
  try {
    const data = await getAuth<unknown>("/billings/status/");
    return parseBillingStatus(data);
  } catch (error) {
    if (isUnauthenticatedError(error)) throw error;
    if (__DEV__) {
      console.warn("[getAuthenticatedBillingStatus] failed", error);
    }
    return null;
  }
}

// --- Checkout Session作成 ---
// 認証必須。success_url / cancel_url は呼び出し元(画面)が組み立てて渡す。
export async function createBillingCheckoutSession({
  successUrl,
  cancelUrl,
}: CreateBillingCheckoutSessionParams): Promise<BillingCheckoutSession> {
  const data = await postAuth<unknown>("/billings/checkout/", {
    success_url: successUrl,
    cancel_url: cancelUrl,
  });

  return parseCheckoutSession(data);
}

// --- Free / Premium判定 ---
// backend の is_premium_for_user と同じ条件(plan === "premium" かつ is_active)で判定する。
export function isPremiumStatus(status: BillingStatus | null | undefined): boolean {
  return status?.plan === "premium" && status.is_active === true;
}

export function isFreeStatus(status: BillingStatus | null | undefined): boolean {
  return !isPremiumStatus(status);
}
