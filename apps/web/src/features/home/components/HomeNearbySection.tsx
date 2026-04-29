// apps/web/src/features/home/components/HomeNearbySection.tsx
"use client";

import Link from "next/link";

export function HomeNearbySection() {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-none">
      <div className="space-y-1">
        <p className="text-sm font-semibold text-slate-900">近くの神社を探す</p>
        <p className="text-xs text-slate-600">地図から周辺の神社を探せます。</p>
      </div>

      <div className="mt-4">
        <Link
          href="/map"
          className="inline-flex min-h-[40px] items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:border-emerald-200 hover:text-emerald-700"
        >
          地図を開く
        </Link>
      </div>
    </div>
  );
}
