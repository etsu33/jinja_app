// apps/web/src/features/home/components/HomeNearbySection.tsx
"use client";

import Link from "next/link";

export function HomeNearbySection() {
  return (
    <div className="rounded-3xl border border-stone-200/25 bg-white/60 px-5 py-7 sm:py-8">
      <div className="space-y-1">
        <p className="text-sm font-medium text-stone-800">近くの神社を地図でも確認する</p>
        <p className="text-xs text-stone-500">相談のあとに、距離や周辺を補助的に見る</p>
      </div>

      <div className="mt-5">
        <Link
          href="/map"
          className="inline-flex min-h-[36px] items-center justify-center rounded-full border border-stone-200/55 bg-stone-50/80 px-4 py-1.5 text-sm font-normal text-stone-700 transition hover:bg-stone-100"
        >
          地図でも確認する
        </Link>
      </div>
    </div>
  );
}
