// apps/web/src/lib/analytics/identity.ts
//
// ログインユーザーの識別（identify / reset）を AnalyticsProvider 経由で行う入口。
// 「本番のみ・キー未設定なら何もしない」のガードは Provider 側が持つ。
// analytics の失敗で認証の流れを止めないよう、例外はここで握りつぶす。
import { getAnalyticsProvider } from "@/lib/analytics/providers";

/** 内部のユーザーIDだけを文字列にして identify する。ほかの属性は受け取らない。 */
export function identifyAnalyticsUser(userId: number | string): void {
  try {
    getAnalyticsProvider().identify(String(userId));
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[analytics identify]", error);
    }
  }
}

export function resetAnalyticsIdentity(): void {
  try {
    getAnalyticsProvider().reset();
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[analytics reset]", error);
    }
  }
}
