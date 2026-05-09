// apps/web/src/features/map/components/MapPageClient.tsx
"use client";

import { useState } from "react";
import { PlaceSuggestBox } from "@/components/PlaceSuggestBox";
import type { Shrine } from "@/lib/api/shrines";
import NearbyShrineCardListClient from "@/features/map/components/NearbyShrineCardListClient";

function PlaceSelectedCard({ item }: { item: Shrine }) {
  return (
    <div className="rounded-3xl border border-stone-200/45 bg-white/75 px-5 py-6">
      <div className="space-y-1">
        <p className="text-sm font-medium text-stone-900">{item.name_jp}</p>
        {"address" in item && (item as any).address ? (
          <p className="text-xs text-stone-500">{(item as any).address}</p>
        ) : null}
        <p className="text-[11px] text-stone-400">{String((item as any).id ?? "")}</p>
      </div>
    </div>
  );
}

export default function MapPageClient() {
  const [keyword, setKeyword] = useState("");
  const [selected, setSelected] = useState<Shrine | null>(null);

  const mode: "nearby" | "search" = selected ? "search" : "nearby";

  return (
    <div className="space-y-6">
      <PlaceSuggestBox value={keyword} onChange={setKeyword} onSelect={(it) => setSelected(it)} />

      {mode === "nearby" && <NearbyShrineCardListClient />}

      {mode === "search" && selected && (
        <div className="space-y-3">
          <p className="text-[11px] font-medium tracking-[0.2em] text-stone-500">SELECTED PLACE</p>
          <PlaceSelectedCard item={selected} />
        </div>
      )}
    </div>
  );
}
