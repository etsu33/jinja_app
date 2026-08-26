// apps/web/src/features/home/components/HomeNearbySection.tsx
"use client";

import Link from "next/link";

export function HomeNearbySection() {
  return (
    <div className="rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-5 py-7 sm:py-8">
      <div className="space-y-1">
        <p className="text-sm font-medium text-[var(--kt-color-text-primary)]">近くの神社を地図でも確認する</p>
        <p className="text-xs text-[var(--kt-color-text-muted)]">相談のあとに、距離や周辺を補助的に見る</p>
      </div>

      <div className="mt-5">
        <Link
          href="/map"
          className="inline-flex min-h-[36px] items-center justify-center rounded-full border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-4 py-1.5 text-sm font-normal text-[var(--kt-color-text-secondary)] transition hover:bg-[var(--kt-color-background-subtle)]"
        >
          地図でも確認する
        </Link>
      </div>
    </div>
  );
}
