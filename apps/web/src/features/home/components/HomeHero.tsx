"use client";

import { HomeHeroConsultationInput } from "./HomeHeroConsultationInput";

export function HomeHero() {
  return (
    <section className="rounded-3xl bg-[var(--kt-color-surface-elevated)] px-6 py-16 sm:px-10 sm:py-24">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-10 text-center">
        <div className="space-y-4">
          <p className="text-xs font-medium tracking-[0.35em] text-[var(--kt-color-text-muted)]">KAMI MUSUBI</p>
          <h1 className="text-3xl font-semibold leading-tight text-[var(--kt-color-text-primary)] sm:text-4xl">
            今の相談から、向かう神社を見つける
          </h1>
          <p className="mx-auto max-w-xl text-sm leading-7 text-[var(--kt-color-text-muted)]">
            迷っていることを一言にすると、今の気持ちに合わせて神社との出会いを整えます。
          </p>
        </div>

        <HomeHeroConsultationInput />
      </div>
    </section>
  );
}
