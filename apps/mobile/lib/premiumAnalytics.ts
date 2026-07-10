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
