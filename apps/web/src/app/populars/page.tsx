"use client";

import { usePopularShrines } from "@/hooks/usePopularShrines";
import type { Shrine } from "@/lib/api/popular";

function labelFor(s: Shrine): string {
  const anyS = s as Shrine & { name?: string };
  return anyS.name_jp || anyS.name || "（名称不明）";
}

export default function PopularShrinesListPage() {
  const { items, loading, error } = usePopularShrines({ limit: 50 });

  return (
    <main className="mx-auto max-w-lg p-4">
      <h1 className="mb-4 text-lg font-semibold">人気神社一覧</h1>

      {loading && <p className="text-sm text-gray-500">読み込み中です…</p>}

      {error && !loading && (
        <p className="text-sm text-red-600">データを取得できませんでした。時間をおいて再度お試しください。</p>
      )}

      {!loading && !error && (
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {items.length === 0 ? (
            <li className="list-none pl-0 text-gray-500">表示できる神社がありません。</li>
          ) : (
            items.map((s) => <li key={s.id}>{labelFor(s)}</li>)
          )}
        </ul>
      )}
    </main>
  );
}
