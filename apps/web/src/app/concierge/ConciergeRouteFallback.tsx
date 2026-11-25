"use client";

// /concierge の route Suspense fallback。
// ?theme=...（Home からの自動送信ルート）の時だけ待機表示を出し、それ以外は従来どおり何も出さない。
//
// useSearchParams は静的 prerender では bailout するため、内側の Suspense（fallback null）で包む。
// これにより prerender HTML は従来と同じ（空）のまま、client 遷移時だけ theme を読んで描画される。
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import {
  ConciergeAutoSubmitPendingFrame,
  readAutoSubmitTheme,
} from "@/features/concierge/components/ConciergeAutoSubmitPending";

function ThemeAwareFallback() {
  const theme = readAutoSubmitTheme(useSearchParams());
  return theme ? <ConciergeAutoSubmitPendingFrame theme={theme} /> : null;
}

export default function ConciergeRouteFallback() {
  return (
    <Suspense fallback={null}>
      <ThemeAwareFallback />
    </Suspense>
  );
}
