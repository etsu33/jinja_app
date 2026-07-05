// src/features/home/components/HomeRankingSection.tsx
"use client";

import Link from "next/link";

type ShrineRankingItem = {
  id: number;
  name: string;
  area: string;
  reason: string;
};

const mockRanking: ShrineRankingItem[] = [
  {
    id: 1,
    name: "赤坂氷川神社",
    area: "東京・赤坂",
    reason: "縁結びと仕事運の両方で人気",
  },
  {
    id: 2,
    name: "東京大神宮",
    area: "東京・飯田橋",
    reason: "恋愛成就の代表的な神社",
  },
  {
    id: 3,
    name: "日枝神社",
    area: "東京・永田町",
    reason: "出世・仕事運のご利益で知られる",
  },
];

export function HomeRankingSection() {
  const items = mockRanking; // TODO: 後でAPI連携に差し替え

  return (
    <section className="space-y-4">
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">参考にしたい人気の神社</h2>
          <p className="mt-2 text-xs text-slate-600">相談で迷ったあとに、みんなが見ている神社も参考にできます。</p>
        </div>
        <Link href="/ranking" className="text-xs font-medium text-slate-600 underline-offset-2 hover:text-emerald-700 hover:underline">
          参考ランキングを見る
        </Link>
      </div>

      <div className="flex flex-col gap-2">
        {items.map((item, index) => (
          <Link
            key={item.id}
            href="/ranking"
            className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-xs shadow-sm transition active:scale-[0.99]"
          >
            <div className="mt-1 flex h-6 w-6 items-center justify-center rounded-full bg-stone-100 text-[11px] font-semibold text-slate-700">
              {index + 1}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                <span className="text-[10px] text-slate-500">{item.area}</span>
              </div>
              <p className="mt-1 text-[11px] leading-snug text-slate-600">{item.reason}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
