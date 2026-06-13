"use client";

import Link from "next/link";

const THEME_EXAMPLES = [
  "気持ちを切り替えたい",
  "静かな場所で整えたい",
  "仕事やこれからを相談したい",
] as const;

export function HomeConciergeInlineClient({ className }: { className?: string }) {
  return (
    <div className={className}>
      <div className="rounded-3xl border border-stone-200/25 bg-stone-50/50 px-6 py-8 sm:px-7 sm:py-9">
        <p className="text-[9px] font-normal tracking-[0.24em] text-stone-500">QUIET GUIDE</p>
        <div className="mt-3 space-y-3">
          <h2 className="text-base font-medium leading-7 text-stone-800">今の相談からはじめる</h2>
          <p className="text-sm leading-7 text-stone-500">
            迷っていることを一言にすると、今の状態に合う神社を探しやすくなります。
          </p>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {THEME_EXAMPLES.map((label) => (
            <Link
              key={label}
              href={`/concierge?theme=${encodeURIComponent(label)}`}
              className="rounded-full border border-stone-200/55 bg-white/80 px-3 py-1.5 text-xs font-medium text-stone-700 transition hover:bg-stone-100"
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="mt-6">
          <Link
            href="/concierge"
            className="inline-flex min-h-[38px] w-full items-center justify-center rounded-full border border-emerald-200/70 bg-emerald-50/90 px-4 py-2 text-sm font-medium text-emerald-900 transition hover:bg-emerald-100"
          >
            相談を書いて選ぶ
          </Link>
        </div>
      </div>
    </div>
  );
}
