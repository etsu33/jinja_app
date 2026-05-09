"use client";

import Link from "next/link";

import { HomeNearbySection } from "./HomeNearbySection";
import { HomeHero } from "./HomeHero";

export function HomeMainClient() {
  return (
    <div className="space-y-16">
      <HomeHero />

      <section className="space-y-9">
        <div className="space-y-2 px-1">
          <p className="text-[9px] font-normal tracking-[0.24em] text-stone-500">QUIET PATHS</p>
          <h2 className="text-lg font-medium text-stone-900">近くの空気を、静かにたどる</h2>
        </div>

        <div className="space-y-10">
          <div className="ml-2 max-w-[34rem]">
            <HomeNearbySection />
          </div>

          <div className="ml-auto max-w-[30rem] rounded-3xl border border-stone-200/20 bg-white/55 px-6 py-10 sm:py-11">
            <p className="text-sm font-medium text-stone-900">心に浮かぶ場所を、そっと見る</p>
            <div className="mt-7">
              <Link
                href="/shrines"
                className="inline-flex min-h-[36px] rounded-full border border-stone-200/55 bg-stone-50/80 px-4 py-1.5 text-sm font-normal text-stone-700 transition hover:bg-stone-100"
              >
                場所一覧を見る
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
