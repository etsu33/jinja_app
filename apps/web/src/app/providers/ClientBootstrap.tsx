"use client";
import { useEffect } from "react";
import { getAnalyticsProvider } from "@/lib/analytics/providers";
// 旧: import { install401Retry } from "@/lib/axios";
// 何もせずにマウントだけ（client.ts の interceptors が有効）

export default function ClientBootstrap() {
  useEffect(() => {
    // api interceptors are defined in "@/lib/api/client"
    if (process.env.NODE_ENV !== "production") return;

    try {
      getAnalyticsProvider().track("posthog_health_check", {
        source: "client_bootstrap",
      });
    } catch (error) {
      // analytics の失敗で UI を止めない
      console.warn("POSTHOG_HEALTH_CHECK_FAILED", error);
    }
  }, []);
  return null;
}
