// apps/web/src/features/mypage/components/FavoritesSection.tsx
"use client";

import Link from "next/link";
import type { Favorite } from "@/lib/api/favorites";
import { useFavorites } from "./hooks/useFavorites";
import { FavoriteShrineCard } from "./FavoriteShrineCard";

type Props = { initialFavorites: Favorite[] };

export default function FavoritesSection({ initialFavorites }: Props) {
  const { items, count, unSave, error } = useFavorites({ initialFavorites });

  const hasData = count > 0;

  const sorted = [...items].sort((a, b) => {
    const aCount = Number(a.public_goshuin_count ?? 0);
    const bCount = Number(b.public_goshuin_count ?? 0);

    const aHas = aCount > 0;
    const bHas = bCount > 0;

    if (aHas !== bHas) return aHas ? -1 : 1;
    if (aCount !== bCount) return bCount - aCount;

    const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
    const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;

    return bTime - aTime;
  });

  const visible = sorted.slice(0, 3);

  return (
    <section className="space-y-3 rounded-2xl border border-stone-200/20 bg-stone-50/30 p-5 sm:p-6">
      <header className="flex items-center justify-between gap-2 text-xs text-stone-500">
        <p>
          <span className="font-medium text-stone-700">保存した神社</span>
          <span className="ml-2 text-[11px] text-stone-400">{hasData ? `${count}件` : "0件"}</span>
        </p>
        {hasData && (
          <Link
            href="/favorites"
            className="rounded-full border border-stone-200/40 bg-stone-50/20 px-3 py-1 text-[11px] text-stone-600 transition hover:bg-stone-100/50"
          >
            すべて見る
          </Link>
        )}
      </header>

      {error && (
        <div className="rounded-xl border border-rose-700/10 bg-rose-50/50 px-3 py-2 text-sm text-rose-700">{error}</div>
      )}

      {!hasData ? (
        <div className="space-y-2 rounded-2xl border border-stone-200/20 bg-stone-50/20 px-4 py-6 text-center text-sm text-stone-700">
          <p className="font-medium">保存した神社はまだありません</p>
          <p className="text-xs text-stone-500">気になる神社を保存できます。</p>
          <Link
            href="/map"
            className="mt-2 inline-block rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-900"
          >
            近くの神社を探す
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((f) => (
            <FavoriteShrineCard key={f.id} favorite={f} onUnsave={() => unSave(f)} />
          ))}
        </div>
      )}
    </section>
  );
}
