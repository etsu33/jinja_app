"use client";

import { useRouter } from "next/navigation";

export function HomeConciergeInlineClient({ className }: { className?: string }) {
  const router = useRouter();

  return (
    <div className={className}>
      <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <p className="text-xs font-semibold text-amber-700">迷っている方へ</p>
        <p className="mt-2 text-base font-bold text-slate-950">今の状況や気持ちから、あなたに合う神社を整理します</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">
          願いや悩みを言葉にすると、コンシェルジュが参拝先の候補を提案します。
        </p>
        <button
          type="button"
          onClick={() => router.push("/concierge")}
          className="mt-4 w-full rounded-full bg-amber-500 py-3 text-sm font-semibold text-slate-950 transition-colors hover:bg-amber-400"
        >
          相談して神社を見つける
        </button>
      </div>
    </div>
  );
}
