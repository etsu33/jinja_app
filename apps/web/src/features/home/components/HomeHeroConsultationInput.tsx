"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const THEME_EXAMPLES = [
  "気持ちを切り替えたい",
  "静かな場所で整えたい",
  "仕事やこれからを相談したい",
] as const;

function buildConciergeHref(theme: string): string {
  const trimmed = theme.trim();
  if (!trimmed) return "/concierge";

  return `/concierge?theme=${encodeURIComponent(trimmed)}`;
}

export function HomeHeroConsultationInput() {
  const router = useRouter();
  const [theme, setTheme] = useState("");

  const canSubmit = useMemo(() => theme.trim().length > 0, [theme]);

  const submitTheme = (value: string) => {
    const href = buildConciergeHref(value);
    router.push(href);
  };

  return (
    <div className="w-full max-w-2xl rounded-[2rem] border border-white/70 bg-white/70 p-4 text-left shadow-sm shadow-stone-900/5 sm:p-5">
      <label htmlFor="home-hero-consultation" className="block text-[11px] font-medium text-stone-500">
        今の気持ちを少しだけ書く
      </label>

      <textarea
        id="home-hero-consultation"
        value={theme}
        onChange={(event) => setTheme(event.target.value)}
        placeholder="例: 気持ちを切り替えたい、これからのことを考えたい"
        rows={3}
        className="mt-2 w-full resize-none rounded-3xl border border-stone-200/50 bg-stone-50/70 px-4 py-3 text-sm leading-7 text-stone-900 outline-none transition placeholder:text-stone-400 focus:border-emerald-200 focus:ring-1 focus:ring-emerald-100"
      />

      <div className="mt-3 flex flex-wrap gap-2">
        {THEME_EXAMPLES.map((label) => (
          <button
            key={label}
            type="button"
            className="rounded-full border border-stone-200/55 bg-white/80 px-3 py-1.5 text-xs font-medium text-stone-700 transition hover:bg-stone-100"
            onClick={() => submitTheme(label)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          className="inline-flex min-h-[40px] w-full items-center justify-center rounded-full border border-emerald-200/70 bg-emerald-50/90 px-5 py-2 text-sm font-medium text-emerald-900 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-45"
          disabled={!canSubmit}
          onClick={() => submitTheme(theme)}
        >
          この相談ではじめる
        </button>

        <button
          type="button"
          className="inline-flex min-h-[40px] w-full items-center justify-center rounded-full border border-stone-200/70 bg-white/70 px-5 py-2 text-sm font-medium text-stone-700 transition hover:bg-stone-100"
          onClick={() => router.push("/concierge?openFilter=1")}
        >
          必要なら条件を添える
        </button>
      </div>
    </div>
  );
}

export { buildConciergeHref };
