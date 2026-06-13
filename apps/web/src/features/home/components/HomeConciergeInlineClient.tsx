"use client";

export function HomeConciergeInlineClient({ className }: { className?: string }) {
  return (
    <div className={className}>
      <div className="rounded-3xl border border-stone-200/25 bg-stone-50/50 px-6 py-8 sm:px-7 sm:py-9">
        <p className="text-[9px] font-normal tracking-[0.24em] text-stone-500">QUIET GUIDE</p>
        <p className="mt-3 text-sm leading-7 text-stone-500">必要なときにだけ、言葉を静かに整えられます。</p>
      </div>
    </div>
  );
}
