"use client";

import Link from "next/link";

import { SectionCard } from "@/components/layout/SectionCard";
import { HomeConciergeInlineClient } from "./HomeConciergeInlineClient";
import { HomeNearbySection } from "./HomeNearbySection";
import HomeGoshuinFeedSection from "@/features/home/components/HomeGoshuinFeedSection";

export function HomeMainClient() {
  return (
    <>
      <SectionCard>
        <HomeConciergeInlineClient />
      </SectionCard>

      <SectionCard title="今いる場所の近くの神社" description="位置情報をもとに、徒歩圏内の神社を優先して表示します。">
        <div className="space-y-4">
          <HomeNearbySection />

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-slate-900">名前やご利益から探したい場合はこちら</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              神社名がわかる時や、縁結び・金運などのご利益から探したい時は検索ページを使えます。
            </p>
            <Link
              href="/shrines"
              className="mt-3 inline-flex rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100"
            >
              神社を検索する
            </Link>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="参拝の記録" description="みんなの御朱印から、参拝後の雰囲気を見られます。">
        <HomeGoshuinFeedSection limit={6} />
      </SectionCard>
    </>
  );
}
