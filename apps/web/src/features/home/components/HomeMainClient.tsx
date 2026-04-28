"use client";

import Link from "next/link";

import { SectionCard } from "@/components/layout/SectionCard";
import { HomeConciergeInlineClient } from "./HomeConciergeInlineClient";
import { HomeNearbySection } from "./HomeNearbySection";
import HomeGoshuinFeedSection from "@/features/home/components/HomeGoshuinFeedSection";

export function HomeMainClient() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold text-emerald-700">どう探しますか？</p>
        <h1 className="text-2xl font-bold text-slate-950">今のあなたに合う探し方を選んでください</h1>
        <p className="text-sm leading-6 text-slate-600">
          迷っている時は相談から、近くで探したい時は地図から、条件が決まっている時は検索から進めます。
        </p>
      </div>

      <SectionCard>
        <HomeConciergeInlineClient />
      </SectionCard>

      <SectionCard title="今すぐ行きたい方へ" description="位置情報をもとに、徒歩圏内の神社を優先して表示します。">
        <div className="space-y-4">
          <HomeNearbySection />

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-slate-900">探したい神社が決まっている方へ</p>
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
    </div>
  );
}
