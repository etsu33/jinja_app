"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

function buildConciergeHref(theme: string, options?: { openFilter?: boolean }): string {
  const params = new URLSearchParams();
  const trimmed = theme.trim();

  if (trimmed) params.set("theme", trimmed);
  if (options?.openFilter) params.set("openFilter", "1");

  const qs = params.toString();
  return qs ? `/concierge?${qs}` : "/concierge";
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
  const [isConditionHintOpen, setIsConditionHintOpen] = useState(false);

  const canSubmit = useMemo(() => theme.trim().length > 0, [theme]);

  const submitTheme = (value: string) => {
    const href = buildConciergeHref(value, { openFilter: isConditionHintOpen });
    router.push(href);
  };

  return (
    <div className="w-full max-w-2xl rounded-[2rem] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-elevated)] p-4 text-left shadow-sm sm:p-5">
      <label htmlFor="home-hero-consultation" className="block text-[11px] font-medium text-[var(--kt-color-text-muted)]">
        今の気持ちを少しだけ書く
      </label>

      <textarea
        id="home-hero-consultation"
        value={theme}
        onChange={(event) => setTheme(event.target.value)}
        placeholder="例: 気持ちを切り替えたい、これからのことを考えたい"
        rows={3}
        className="mt-2 w-full resize-none rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-4 py-3 text-sm leading-7 text-[var(--kt-color-text-primary)] outline-none transition placeholder:text-[var(--kt-color-text-muted)] focus:border-[var(--kt-color-border-focus)] focus:ring-1 focus:ring-[var(--kt-color-border-focus)]"
      />

      <div className="mt-3">
        <p className="text-[11px] font-medium text-[var(--kt-color-text-muted)]">相談のきっかけ</p>
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
                    ? "border-[var(--kt-color-action-primary)] bg-[var(--kt-color-background-subtle)] text-[var(--kt-color-action-primary)] shadow-sm"
                    : "border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)]",
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

      <div className="mt-3 border-t border-[var(--kt-color-border-default)] pt-3">
        <button
          type="button"
          className="inline-flex items-center rounded-full px-1 text-xs font-medium text-[var(--kt-color-text-secondary)] transition hover:text-[var(--kt-color-action-primary)]"
          onClick={() => setIsConditionHintOpen((current) => !current)}
          aria-expanded={isConditionHintOpen}
        >
          ＋ 条件を追加する
        </button>
        {isConditionHintOpen ? (
          <p className="mt-2 rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-2 text-xs leading-6 text-[var(--kt-color-text-muted)]">
            誕生日やご利益、参拝スタイルなどの条件は次のステップで追加できます。
          </p>
        ) : null}
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          className="inline-flex min-h-[40px] w-full items-center justify-center rounded-full border border-[var(--kt-color-action-primary)] bg-[var(--kt-color-background-subtle)] px-5 py-2 text-sm font-medium text-[var(--kt-color-action-primary)] transition hover:bg-[var(--kt-color-surface-default)] disabled:cursor-not-allowed disabled:opacity-45"
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
