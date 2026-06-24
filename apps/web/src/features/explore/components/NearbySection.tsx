

"use client";

import Link from "next/link";

import NearbyShrineCardListClient from "@/features/map/components/NearbyShrineCardListClient";

type NearbySectionProps = {
  showNearbyList?: boolean;
};

export function NearbySection({ showNearbyList = false }: NearbySectionProps) {
  return (
    <section className="rounded-3xl border border-stone-200/25 bg-white/55 p-4 sm:p-5">
      <div className="space-y-1">
        <p className="text-[11px] font-medium tracking-[0.2em] text-stone-500">NEARBY</p>
        <h2 className="text-sm font-medium text-stone-800">近くで探す</h2>
        <p className="text-xs leading-6 text-stone-500">
          今いる場所から行きやすい神社を確認できます。
        </p>
      </div>

      <div className="mt-4">
        {showNearbyList ? (
          <NearbyShrineCardListClient />
        ) : (
          <Link
            href="/map"
            className="inline-flex min-h-[36px] items-center justify-center rounded-full border border-stone-200/55 bg-stone-50/80 px-4 py-1.5 text-sm font-normal text-stone-700 transition hover:bg-stone-100"
          >
            地図で近くの神社を見る
          </Link>
        )}
      </div>
    </section>
  );
}
