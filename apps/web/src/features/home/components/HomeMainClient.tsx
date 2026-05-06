"use client";

import Link from "next/link";

import { SectionCard } from "@/components/layout/SectionCard";
import { HomeConciergeInlineClient } from "./HomeConciergeInlineClient";
import { HomeNearbySection } from "./HomeNearbySection";
import HomeGoshuinFeedSection from "@/features/home/components/HomeGoshuinFeedSection";

export function HomeMainClient() {
  return (
    <div className="space-y-6">
      <div className="space-y-2 px-1">
        <p className="text-xs font-semibold text-emerald-700">神社コンシェルジュ</p>
        <h1 className="text-2xl font-semibold leading-tight text-slate-950">今の気持ちに合う探し方を選ぶ</h1>
        <p className="text-sm leading-6 text-slate-600">
          迷っている時は相談から、近くで探したい時は地図から。今の状態に合わせて神社を探せます。
        </p>
      </div>

      <HomeConciergeInlineClient />

      <div className="space-y-4 pt-2">
        <SectionCard
          variant="subtle"
          title="今すぐ行きたい方へ"
          description="位置情報をもとに、徒歩圏内の神社を優先して表示します。"
        >
          <div className="space-y-4">
            <HomeNearbySection />

            <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-none">
              <p className="text-sm font-semibold text-slate-900">探したい神社が決まっている方へ</p>
              <p className="mt-2 text-xs leading-5 text-slate-600">
                神社名がわかる時や、縁結び・金運などのご利益から探したい時は検索ページを使えます。
              </p>
              <Link
                href="/shrines"
                className="mt-4 inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-emerald-200 hover:text-emerald-700"
              >
                神社を検索する
              </Link>
            </div>
          </div>
        </SectionCard>

        <SectionCard variant="subtle" title="参拝の記録" description="みんなの御朱印から、参拝後の雰囲気を見られます。">
          <HomeGoshuinFeedSection limit={6} />
        </SectionCard>
      </div>
    </div>
  );
}
