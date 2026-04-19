"use client";

import { useEffect, useState } from "react";
import type { Shrine } from "@/lib/api/popular";

function labelFor(s: Shrine): string {
  const anyS = s as Shrine & { name?: string };
  return anyS.name_jp || anyS.name || "（名称不明）";
}

function toItems(data: unknown): Shrine[] {
  if (Array.isArray(data)) return data as Shrine[];
  if (data && typeof data === "object") {
    const o = data as Record<string, unknown>;
    if (Array.isArray(o.results)) return o.results as Shrine[];
    if (Array.isArray(o.items)) return o.items as Shrine[];
  }
  return [];
}

export default function PopularShrinesListPage() {
  const [items, setItems] = useState<Shrine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const sp = new URLSearchParams();
    sp.set("limit", "50");

    fetch(`/api/populars/?${sp.toString()}`, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error("failed to fetch popular shrines");
        return res.json() as Promise<unknown>;
      })
      .then((data) => {
        if (!cancelled) setItems(toItems(data));
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "fetch failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

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
