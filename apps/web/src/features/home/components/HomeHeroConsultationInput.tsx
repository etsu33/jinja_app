"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type BuildConciergeHrefOptions = {
  openFilter?: boolean;
};

function buildConciergeHref(theme: string, options: BuildConciergeHrefOptions = {}): string {
  const trimmed = theme.trim();
  const params = new URLSearchParams();

  if (trimmed) {
    params.set("theme", trimmed);
  }

  if (options.openFilter) {
    params.set("openFilter", "1");
  }

  const query = params.toString();
  if (!query) return "/concierge";

  return `/concierge?${query}`;
}

const CONSULTATION_THEME_CHIPS = [
  {
    label: "疲れを整えたい",
    text: "最近少し疲れていて、気持ちを落ち着ける参拝がしたいです",
  },
  {
    label: "迷いを整理したい",
    text: "今の迷いを整理して、落ち着いて考えられる場所に行きたいです",
  },
  {
    label: "前に進みたい",
    text: "気持ちを切り替えて、前に進むきっかけがほしいです",
  },
  {
    label: "静かに考えたい",
    text: "静かな場所で、これからのことをゆっくり考えたいです",
  },
  {
    label: "人との縁を見直したい",
    text: "人とのご縁を見つめ直して、大切にできる参拝がしたいです",
  },
  {
    label: "仕事の流れを整えたい",
    text: "仕事の流れを整えて、次に進むきっかけがほしいです",
  },
] as const;

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

      <div className="mt-3">
        <p className="text-[11px] font-medium text-stone-500">相談のきっかけ</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {CONSULTATION_THEME_CHIPS.map((chip) => {
            const isSelected = theme.trim() === chip.text;
            return (
              <button
                key={chip.label}
                type="button"
                className={[
                  "rounded-full border px-3 py-1.5 text-xs font-medium transition active:scale-[0.98]",
                  isSelected
                    ? "border-emerald-200/80 bg-emerald-50/90 text-emerald-800 shadow-sm shadow-emerald-900/5"
                    : "border-stone-200/60 bg-white/55 text-stone-600 hover:bg-stone-50",
                ].join(" ")}
                onClick={() => setTheme(chip.text)}
                aria-pressed={isSelected}
                title={chip.text}
              >
                {chip.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-3 border-t border-stone-200/50 pt-3">
        <button
          type="button"
          className="inline-flex items-center rounded-full px-1 text-xs font-medium text-stone-600 transition hover:text-emerald-800"
          onClick={() => router.push(buildConciergeHref(theme, { openFilter: true }))}
        >
          ＋ 条件を追加する
        </button>
        <p className="mt-2 rounded-2xl border border-stone-200/55 bg-stone-50/70 px-3 py-2 text-xs leading-6 text-stone-500">
          誕生日やご利益、参拝スタイルなどの条件は次のステップで追加できます。
        </p>
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
      </div>
    </div>
  );
}

export { buildConciergeHref };
