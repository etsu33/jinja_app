// apps/web/src/features/home/components/HomeNearbySection.tsx
"use client";

import Link from "next/link";

export function HomeNearbySection() {
  return (
    <div className="flex flex-col items-center py-6 text-center sm:py-8">
      <p className="max-w-xs text-pretty text-sm font-light leading-relaxed tracking-wide text-foreground/60">
        現在地から、歩いて行ける距離の神社を地図でお探しいただけます
      </p>

      <Link
        href="/map"
        className="mt-8 inline-flex items-center gap-2 rounded-full border border-border/40 bg-transparent px-6 py-2.5 text-xs font-light tracking-wider text-foreground/60 transition-all duration-500 hover:border-primary/30 hover:bg-primary/5 hover:text-foreground/80"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-60"
        >
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
          <circle cx="12" cy="10" r="3" />
        </svg>
        地図を開く
      </Link>
    </div>
  );
}
