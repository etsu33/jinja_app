"use client";

import Link from "next/link";

import { HomeNearbySection } from "./HomeNearbySection";
import { HomeCompassSection } from "./HomeCompassSection";
import { HomeHero } from "./HomeHero";

export function HomeMainClient() {
  return (
    <div className="space-y-16">
      <HomeHero />

      {/* Compass's Home-level entry (docs/audit/compass-home-entry-ia.md):
          its own section, not nested under SUB PATHS below -- that
          section's heading ("相談のあとに...") presupposes Concierge came
          first, which would misrepresent Compass as a Concierge follow-up
          rather than an independent product entry. */}
      <section className="space-y-9">
        <div className="space-y-2 px-1">
          <p className="text-[9px] font-normal tracking-[0.24em] text-stone-400">ANOTHER WAY IN</p>
          <h2 className="text-lg font-medium text-stone-800">方向から探す</h2>
        </div>

        <div className="max-w-[34rem]">
          <HomeCompassSection />
        </div>
      </section>

      <section className="space-y-9">
        <div className="space-y-2 px-1">
          <p className="text-[9px] font-normal tracking-[0.24em] text-stone-400">SUB PATHS</p>
          <h2 className="text-lg font-medium text-stone-800">相談のあとに、場所でも確かめる</h2>
        </div>

        <div className="space-y-10">
          <div className="ml-2 max-w-[34rem]">
            <HomeNearbySection />
          </div>

          <div className="ml-auto max-w-[30rem] rounded-3xl border border-stone-200/20 bg-white/55 px-6 py-10 sm:py-11">
            <p className="text-sm font-medium text-stone-800">神社名や地域からも確認する</p>
            <div className="mt-7">
              <Link
                href="/shrines"
                className="inline-flex min-h-[36px] rounded-full border border-stone-200/55 bg-stone-50/80 px-4 py-1.5 text-sm font-normal text-stone-700 transition hover:bg-stone-100"
              >
                神社一覧も見る
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
