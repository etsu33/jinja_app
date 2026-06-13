"use client";

import { HomeHeroConsultationInput } from "./HomeHeroConsultationInput";

export function HomeHero() {
  return (
    <section className="rounded-3xl bg-stone-100/80 px-6 py-16 sm:px-10 sm:py-24">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-10 text-center">
        <div className="space-y-4">
          <p className="text-xs font-medium tracking-[0.35em] text-stone-500">KAMI MUSUBI</p>
          <h1 className="text-3xl font-semibold leading-tight text-stone-900 sm:text-4xl">
            今の相談から、向かう神社を見つける
          </h1>
          <p className="mx-auto max-w-xl text-sm leading-7 text-stone-500">
            悩みや願いをもとに、今の状態に合う神社を提案します。
          </p>
        </div>

        <HomeHeroConsultationInput />
      </div>
    </section>
  );
}
