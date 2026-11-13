"use client";

import { useState } from "react";

import ShrineCardCompact from "@/components/shrines/ShrineCardCompact";
import {
  buildTravelChatPayload,
  pickTravelRecommendations,
  type TravelOrigin,
  type TravelRecommendation,
} from "@/features/concierge/travel/buildTravelChatPayload";
import { postConciergeChat } from "@/lib/api/conciergeChat";

type LocationState = "idle" | "locating" | "ready" | "unavailable";

// 現在地を1回だけ取る。取れなければ null（出発地点なしで送る）。
function getCurrentOrigin(): Promise<TravelOrigin | null> {
  return new Promise((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  });
}

export default function TravelConciergeClient() {
  const [query, setQuery] = useState("");
  const [locationState, setLocationState] = useState<LocationState>("idle");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TravelRecommendation[] | null>(null);

  const canSend = query.trim().length > 0 && !sending;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend) return;

    setSending(true);
    setError(null);
    setLocationState("locating");
    const origin = await getCurrentOrigin();
    setLocationState(origin ? "ready" : "unavailable");

    const payload = buildTravelChatPayload(query, origin);
    if (!payload) {
      setSending(false);
      return;
    }

    try {
      const body = await postConciergeChat(payload);
      setResults(pickTravelRecommendations(body));
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSending(false);
    }
  }

  return (
    // サイト全体は lang="ja" なので、このページの本文だけ英語として読み上げられるようにする
    <main lang="en" className="mx-auto w-full max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Find a shrine to visit</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Tell us what kind of place you are looking for, in your own words. For example: &ldquo;Somewhere quiet with
        old trees&rdquo; or &ldquo;a shrine with a great view after a short hike&rdquo;.
      </p>
      <p className="mt-1 text-xs text-neutral-500">
        Preview: results are currently shown in Japanese. We use your current location as the starting point.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-3">
        <label htmlFor="travel-query" className="block text-sm font-medium">
          What are you looking for?
        </label>
        <textarea
          id="travel-query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          maxLength={500}
          className="w-full rounded-md border border-neutral-300 p-3 text-base"
          placeholder="Somewhere quiet with old trees"
        />
        <button
          type="submit"
          disabled={!canSend}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {sending ? "Searching..." : "Find shrines"}
        </button>
        {locationState === "unavailable" ? (
          <p className="text-xs text-neutral-500" role="status">
            We could not get your location, so results are not based on where you are.
          </p>
        ) : null}
        {error ? (
          <p className="text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}
      </form>

      {results ? (
        <section aria-label="Recommended shrines" className="mt-8 space-y-3">
          {results.length === 0 ? (
            <p className="text-sm text-neutral-600">No shrines found. Try describing it another way.</p>
          ) : (
            results.map((rec) => (
              <ShrineCardCompact
                key={rec.key}
                name={rec.name}
                href={rec.href}
                reason={rec.reason}
                address={rec.address}
                distanceM={rec.distanceM}
              />
            ))
          )}
        </section>
      ) : null}
    </main>
  );
}
