// src/features/home/components/HomeHero.tsx
"use client";

import Link from "next/link";

export function HomeHero() {
  return (
    <div className="flex flex-col gap-4 pt-2">
      <div>
        <div className="text-3xl mb-1">⛩</div>
        <h1 className="text-2xl font-semibold leading-tight text-slate-950">
          人生の節目を整理する
          <br />
          神社コンシェルジュ
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          今の悩みや迷いを書くだけで
          <br />
          相性のよい神社を整理して提案します
        </p>
      </div>

      <Link
        href="/concierge"
        className="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:scale-[0.98]"
      >
        相談して神社を見つける
      </Link>

      <Link
        href="/map"
        className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700 active:scale-[0.98]"
      >
        地図から神社を見る
      </Link>
    </div>
  );
}
