"use client";

import { useEffect, useId, useRef, useState } from "react";
import { trackWebDirection } from "@/lib/analytics/directionEvents";
import {
  originSearchAnnouncement,
  originSelectionAnnouncement,
  type OriginSearchStatus,
} from "../../../../../../packages/shared/directionAccessibility";
import {
  PREFECTURE_ORIGINS,
  prefectureOrigin,
  type OriginMode,
  type UserOrigin,
} from "../../../../../../packages/shared/userOrigin";

type Candidate = { place_id: string; name: string | null; lat: number; lng: number; type?: string };

const modes: Array<[OriginMode, string]> = [
  ["device", "現在地を使用"],
  ["manual", "駅名・住所から指定"],
  ["prefecture", "都道府県から指定"],
  ["disabled", "方位情報を使用しない"],
];

export default function OriginSelector({
  origin,
  onChange,
  onUseDevice,
  deviceError,
}: {
  origin: UserOrigin | null;
  onChange: (value: UserOrigin | null) => void;
  onUseDevice: () => void;
  deviceError?: string | null;
}) {
  const [mode, setMode] = useState<OriginMode>(
    origin?.source === "device" ? "device" : origin?.source === "prefecture" ? "prefecture" : origin ? "manual" : "none",
  );
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Candidate[]>([]);
  const [status, setStatus] = useState<OriginSearchStatus>("idle");
  const requestId = useRef(0);
  const listboxId = useId();
  const statusId = useId();

  useEffect(() => {
    if (mode !== "manual" || query.trim().length < 2) {
      setItems([]);
      setStatus("idle");
      return;
    }
    const id = ++requestId.current;
    const timer = setTimeout(async () => {
      setStatus("searching");
      try {
        const res = await fetch(`/api/geocodes/search/?q=${encodeURIComponent(query.trim())}&limit=5&lang=ja`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (id !== requestId.current) return;
        const next = Array.isArray(data.items) ? data.items : [];
        setItems(next);
        setStatus(next.length ? "idle" : "empty");
      } catch {
        if (id === requestId.current) {
          setItems([]);
          setStatus("error");
        }
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [mode, query]);

  const switchMode = (next: OriginMode) => {
    requestId.current++;
    setMode(next);
    onChange(null);
    setItems([]);
    setStatus("idle");
    if (next === "disabled") trackWebDirection("direction_origin_result", { origin_type: "disabled", result: "selected" });
    if (next === "device") onUseDevice();
  };

  const statusMessage = originSearchAnnouncement(status, items.length);

  return (
    <fieldset className="min-w-0 space-y-3">
      <legend className="text-sm font-medium text-stone-600">出発地点</legend>
      <div role="radiogroup" aria-label="出発地点の指定方法" className="grid grid-cols-1 gap-2 min-[360px]:grid-cols-2">
        {modes.map(([value, label]) => {
          const selected = mode === value;
          return (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => switchMode(value)}
              className={`min-h-11 rounded-xl border px-3 py-2 text-left text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 ${selected ? "border-emerald-500 bg-emerald-50 font-semibold text-emerald-900" : "border-stone-300 bg-white text-stone-700"}`}
            >
              <span aria-hidden="true" className="mr-1 inline-block w-4">{selected ? "✓" : ""}</span>{label}
            </button>
          );
        })}
      </div>

      {mode === "manual" ? (
        <div className="space-y-2">
          <input
            role="combobox"
            aria-label="駅名または住所"
            aria-autocomplete="list"
            aria-expanded={items.length > 0}
            aria-controls={listboxId}
            aria-describedby={statusId}
            value={query}
            onChange={(event) => { setQuery(event.target.value); onChange(null); }}
            placeholder="駅名または住所を入力"
            className="min-h-11 w-full rounded-xl border border-stone-300 px-3 py-2 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
          />
          <p id={statusId} role="status" aria-live="polite" className={status === "error" ? "text-sm text-rose-700" : "text-sm text-stone-600"}>
            {statusMessage}
          </p>
          <div id={listboxId} role="listbox" aria-label="出発地点の検索候補">
            {items.map((item) => (
              <button
                type="button"
                role="option"
                aria-selected="false"
                key={item.place_id}
                onClick={() => {
                  onChange({ latitude: item.lat, longitude: item.lng, source: item.type === "station" ? "station" : "address", displayName: item.name ?? query, accuracy: "precise" });
                  setItems([]);
                  setStatus("idle");
                }}
                className="block min-h-11 w-full border-b border-stone-200 px-3 py-2 text-left text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-600"
              >
                {item.name}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {mode === "prefecture" ? (
        <div className="space-y-2">
          <select
            aria-label="都道府県"
            className="min-h-11 w-full rounded-xl border border-stone-300 px-3 py-2 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
            value={origin?.source === "prefecture" ? origin.displayName : ""}
            onChange={(event) => onChange(prefectureOrigin(event.target.value))}
          >
            <option value="">都道府県を選択</option>
            {PREFECTURE_ORIGINS.map((prefecture) => <option key={prefecture.name}>{prefecture.name}</option>)}
          </select>
          {origin?.source === "prefecture" ? <p className="text-sm leading-6 text-stone-600">{origin.displayName}のおおよその位置を出発地点として使用します。方位は参考情報として表示されます。</p> : null}
        </div>
      ) : null}

      {/* Fail-safe copy only. The alternative route is the「駅名・住所から指定」radio
          in the group above, so an in-error CTA would duplicate the control sitting
          right there and make the failure louder than the selection UI itself. */}
      {deviceError && mode === "device" ? (
        <p role="alert" className="text-sm leading-6 text-rose-700">
          {deviceError}
        </p>
      ) : null}

      <p role="status" aria-live="polite" className="text-sm font-medium text-emerald-800">
        {originSelectionAnnouncement(origin)}
      </p>
    </fieldset>
  );
}
