// Premium画面のAnalyticsイベント契約
// 画面(app/premium/index.tsx)からpayloadの組み立てを切り離し、送信するフィールドをここに集約する。
// track()自体がsession_id/sessionIdの除外・送信失敗の握り潰しを担うため、ここでは行わない。
import { track } from "./analytics";
import type { BillingStatus } from "./billing";

const SOURCE = "mobile_premium";

export type PremiumCheckoutFailureType = "unauthenticated" | "invalid_response" | "open_url_failed" | "unknown";

export function trackPremiumScreenView(): void {
  track("premium_screen_view", { source: SOURCE, platform: "mobile" });
}

export function trackPremiumStatusView(status: Pick<BillingStatus, "plan" | "is_active" | "provider">): void {
  track("premium_status_view", {
    plan: status.plan,
    isActive: status.is_active,
    provider: status.provider,
    source: SOURCE,
  });
}

export function trackPremiumUpgradeClick(): void {
  track("premium_upgrade_click", { plan: "free", source: SOURCE });
}

export function trackPremiumCheckoutStarted(): void {
  track("premium_checkout_started", { source: SOURCE });
}

export function trackPremiumCheckoutFailed(failureType: PremiumCheckoutFailureType): void {
  track("premium_checkout_failed", { source: SOURCE, failureType });
}

// Checkout(外部ブラウザ)からMobileへ復帰したタイミングで送信する。
// 決済成功を証明するものではなく、あくまで「復帰を検知した」計測。
export function trackPremiumCheckoutReturned(): void {
  track("premium_checkout_returned", { source: SOURCE });
}

// Billing Status再取得後、plan === "premium" && is_active === true の場合のみ送信する。
// ガードをここに置くことで、呼び出し側の条件分岐漏れによる誤送信を防ぐ。
export function trackPremiumActive(status: Pick<BillingStatus, "plan" | "is_active" | "provider">): void {
  if (status.plan !== "premium" || !status.is_active) return;

  track("premium_active", {
    plan: "premium",
    isActive: true,
    provider: status.provider,
    source: SOURCE,
  });
}
