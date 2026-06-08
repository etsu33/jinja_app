"use client";

import { useEffect, useState } from "react";
import type { Shrine } from "@/lib/api/shrines";
import { fetchPlaceCacheSuggest } from "@/lib/api/placeCaches";
import { fetchPlacesResolveSuggest } from "@/lib/api/placesResolveSuggest";
import type { SuggestItem } from "./placeSuggest.types";

const DB_MIN = 3;
const PLACES_LIMIT = 5;

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSelect: (it: Shrine) => void;
  limit?: number;
};

async function ingest(place_id: string): Promise<Shrine> {
  const r = await fetch("/api/my/shrines/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({ place_id }),
  });
  if (!r.ok) throw new Error(`ingest failed: ${r.status}`);
  return r.json();
}

export function PlaceSuggestBox({ value, onChange, onSelect, limit = 10 }: Props) {
  const [debounced, setDebounced] = useState(value);
  const [items, setItems] = useState<SuggestItem[]>([]);
  const [loading, setLoading] = useState(false);

  const [ingestingKey, setIngestingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value.trim()), 300);
    return () => window.clearTimeout(id);
  }, [value]);

  useEffect(() => {
    if (!debounced || debounced.length < 2) {
      setItems([]);
      return;
    }

    let cancelled = false;
    setLoading(true);

    (async () => {
      try {
        const db = await fetchPlaceCacheSuggest(debounced, limit);
        const dbItems: SuggestItem[] = db.map((shrine) => ({
          kind: "db",
          key: `db:${(shrine as any).id ?? shrine.name_jp ?? ""}`,
          shrine,
        }));

        if (db.length >= DB_MIN) {
          if (!cancelled) setItems(dbItems);
          return;
        }

        const places = await fetchPlacesResolveSuggest(debounced, PLACES_LIMIT);
        const placeItems: SuggestItem[] = places.map((p) => ({
          kind: "places",
          key: `places:${p.place_id}`,
          place: p,
        }));

        if (!cancelled) setItems([...dbItems, ...placeItems]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [debounced, limit]);

  return (
    <div className="space-y-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="神社名や場所を、そっと入れる"
        className="w-full rounded-3xl border border-stone-200/35 bg-stone-50/25 px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400"
      />

      {loading ? <div className="text-xs text-stone-500 opacity-70">候補を整えています…</div> : null}
      {error ? <div className="text-xs text-rose-600">{error}</div> : null}

      {items.length ? (
        <div className="rounded-3xl border border-stone-200/25 bg-white/60 py-0.5">
          {items.map((it) => {
            if (it.kind === "db") {
              const s = it.shrine;
              return (
                <button
                  key={it.key}
                  type="button"
                  onClick={() => onSelect(s)}
                  className="block w-full px-3 py-2 text-left text-sm text-stone-800 hover:bg-stone-50/50"
                >
                  <div className="font-medium">{s.name_jp}</div>
                  {(s as any).address ? (
                    <div className="mt-0.5 text-xs text-stone-500 opacity-70">{(s as any).address}</div>
                  ) : null}
                </button>
              );
            }

            // places
            const p = it.place;
            const busy = ingestingKey === it.key;

            return (
              <button
                key={it.key}
                type="button"
                disabled={busy}
                onClick={async () => {
                  try {
                    setError(null);
                    setIngestingKey(it.key);
                    const shrine = await ingest(p.place_id);
                    onSelect(shrine);
                  } catch (e) {
                    const msg = e instanceof Error ? e.message : String(e);
                    setError(msg.includes("401") ? "取り込みにはログインが必要です。" : msg);
                  } finally {
                    setIngestingKey(null);
                  }
                }}
                className={`block w-full px-3 py-2 text-left text-sm text-stone-800 hover:bg-stone-50/50 ${
                  busy ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                <div className="font-medium">{p.name}</div>
                {p.address ? <div className="mt-0.5 text-xs text-stone-500 opacity-70">{p.address}</div> : null}
                <div className="mt-0.5 text-[11px] text-emerald-700 opacity-75">
                  {busy ? "取り込み中…" : "未登録: 取り込んで選択"}
                </div>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
