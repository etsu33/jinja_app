// apps/web/src/features/home/components/HomeNearbySection.tsx
"use client";

import Link from "next/link";

export function HomeNearbySection() {
  return (
    <div className="flex flex-col items-center py-4 text-center sm:py-6">
      <p className="max-w-sm text-pretty text-sm font-normal leading-relaxed text-muted-foreground">
        現在地から歩いて行ける神社を地図でお探しいただけます
      </p>

      <Link
        href="/map"
        className="mt-6 inline-flex items-center gap-2.5 rounded-full border border-border/50 bg-card px-6 py-3 text-sm font-normal text-foreground/70 shadow-sm transition-all duration-300 hover:border-primary/40 hover:bg-primary/5 hover:text-foreground/90 sm:mt-8"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-primary/60"
        >
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
          <circle cx="12" cy="10" r="3" />
        </svg>
        地図から探す
      </Link>
    </div>
  );
}
