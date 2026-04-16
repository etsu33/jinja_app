"use client";

import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchRanking } from "@/lib/api/ranking";
import type { RankingItem } from "@/lib/api/ranking";
import { useFavorite } from "@/hooks/useFavorite";
import { preloadFavoritesByShrineIds, type FavoritePreloadMap } from "@/lib/api/favorites";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

function FavButton({ shrineId, initial, loading = false }: { shrineId: number; initial?: boolean; loading?: boolean }) {
  const { fav, busy, toggle } = useFavorite({ shrineId, initial });
  const disabled = busy || loading;
  return (
    <button onClick={toggle} disabled={disabled} aria-pressed={fav} className="text-sm">
      {disabled && loading ? "…" : busy ? "…" : fav ? "★" : "☆"}
    </button>
  );
}

function RankingList({ data, favoriteMap, loading }: { data: RankingItem[]; favoriteMap: FavoritePreloadMap; loading: boolean }) {
  const hasData = Array.isArray(data) && data.length > 0;
  return (
    <ol role="list" className="space-y-4">
      {!hasData && <li className="p-4 text-gray-500">ランキングデータがありません</li>}
      {hasData &&
        data.map((shrine, idx) => (
          <li key={shrine.id ?? idx}>
            <Card className="p-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-3 text-lg">
                  <span>{shrine?.name_jp ?? "名称不明"}</span>
                  {typeof shrine.id === "number" && (
                    <span className="ml-auto">
                      <FavButton shrineId={shrine.id} initial={favoriteMap[String(shrine.id)]?.fav} loading={loading} />
                    </span>
                  )}
                </CardTitle>
              </CardHeader>

              <CardContent>
                <p>{shrine?.address ?? "住所不明"}</p>
                {typeof shrine.id === "number" && (
                  <Link href={buildShrineHref(shrine.id)} className="text-blue-600 underline text-sm">
                    詳細へ
                  </Link>
                )}
              </CardContent>
            </Card>
          </li>
        ))}
    </ol>
  );
}

export default function RankingPage() {
  const [monthly, setMonthly] = useState<RankingItem[]>([]);
  const [yearly, setYearly] = useState<RankingItem[]>([]);
  const [favoriteMap, setFavoriteMap] = useState<FavoritePreloadMap>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [m, y] = await Promise.all([fetchRanking("monthly"), fetchRanking("yearly")]);
      setMonthly(m);
      setYearly(y);

      try {
        const ids = [...m, ...y].map((s) => s.id);
        const map = await preloadFavoritesByShrineIds(ids);
        setFavoriteMap(map);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <main className="p-4 mx-auto max-w-3xl">
      <h1 className="text-xl font-bold mb-4">人気神社ランキング</h1>

      <Tabs defaultValue="monthly">
        <TabsList className="mb-6">
          <TabsTrigger value="monthly">月間TOP10</TabsTrigger>
          <TabsTrigger value="yearly">年間TOP10</TabsTrigger>
        </TabsList>

        <TabsContent value="monthly">
          <RankingList data={monthly} favoriteMap={favoriteMap} loading={loading} />
        </TabsContent>

        <TabsContent value="yearly">
          <RankingList data={yearly} favoriteMap={favoriteMap} loading={loading} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
