// apps/web/src/features/home/components/HomeCompassSection.tsx
//
// Compass's Home-level entry (docs/audit/compass-home-entry-ia.md). Mirrors
// HomeNearbySection.tsx's exact card styling -- no new tokens, no new
// colors, no new radius. Deliberately a plain link card, not an embedded
// interactive form: Compass's actual purpose/origin/birthdate collection
// already lives at /compass, and duplicating it here would duplicate the
// product experience rather than just entering it (the audit doc's Option A
// rejection).
//
// "use client" + onClick tracking added for PR-A (Compass lifecycle
// analytics, docs/audit/compass-analytics-contract-readiness.md §6): a
// Server Component cannot pass an inline event handler as a prop, even to
// `<Link>`. `?ref=home` is the only query param -- Compass still collects
// everything it needs on its own page; the param exists solely so
// CompassClient can attribute its `compass_entry` event, mirroring the
// existing `ctx=map|concierge` pattern used for Shrine Detail.
"use client";

import Link from "next/link";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";

export function HomeCompassSection() {
  return (
    <div className="rounded-3xl border border-stone-200/25 bg-white/60 px-5 py-7 sm:py-8">
      <div className="space-y-1">
        <p className="text-sm font-medium text-stone-800">今月から探す</p>
        <p className="text-xs text-stone-500">今月の流れと方向から、参拝のきっかけを見つけます。</p>
      </div>

      <div className="mt-5">
        <Link
          href="/compass?ref=home"
          onClick={() => trackSearchEvent("home_compass_entry_click", { source: "home" })}
          className="inline-flex min-h-[36px] items-center justify-center rounded-full border border-stone-200/55 bg-stone-50/80 px-4 py-1.5 text-sm font-normal text-stone-700 transition hover:bg-stone-100"
        >
          参拝コンパスを見る
        </Link>
      </div>
    </div>
  );
}
