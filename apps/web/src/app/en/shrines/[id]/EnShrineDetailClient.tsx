"use client";

import { useEffect, useState } from "react";

import {
  buildEnShrineSections,
  pickEnFeatureWords,
  pickEnShrineBasics,
  type EnFeatureWord,
  type EnShrineBasics,
  type EnShrineSection,
} from "@/features/en-shrine/buildEnShrineDetailModel";
import api from "@/lib/api/client";

type LoadState = "loading" | "ready" | "not_found" | "error";

// 現在地を1回だけ取る（距離の表示だけに使う。URL や送信には入れない）。取れなければ null。
function getCurrentOrigin(): Promise<{ lat: number; lng: number } | null> {
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

function FeatureWordList({ words }: { words: EnFeatureWord[] }) {
  return (
    <ul className="mt-2 space-y-1.5">
      {words.map((word) => (
        <li key={word.wordId} className="text-sm">
          <span className="font-medium">{word.labelEn}</span>{" "}
          <a
            href={word.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-neutral-600 underline"
          >
            Source (official site)
          </a>
        </li>
      ))}
    </ul>
  );
}

function Section({ section }: { section: EnShrineSection }) {
  switch (section.kind) {
    case "name_location":
      return (
        <section aria-label="Shrine name and location" data-section="name_location">
          <h1 className="text-2xl font-semibold">{section.nameJa}</h1>
          {section.nameRomaji ? <p className="mt-1 text-sm text-neutral-600">{section.nameRomaji}</p> : null}
          {section.address ? <p className="mt-2 text-sm">{section.address}</p> : null}
        </section>
      );
    case "history_culture":
      return (
        <section aria-label="History and culture" data-section="history_culture" className="mt-6">
          <h2 className="text-lg font-semibold">History and culture</h2>
          <FeatureWordList words={section.words} />
        </section>
      );
    case "scenery_experience":
      return (
        <section aria-label="Scenery and experience" data-section="scenery_experience" className="mt-6">
          <h2 className="text-lg font-semibold">Scenery and experience</h2>
          <FeatureWordList words={section.words} />
        </section>
      );
    case "no_feature_words":
      return (
        <section aria-label="About this shrine" data-section="no_feature_words" className="mt-6">
          <p className="text-sm text-neutral-600">
            We don&apos;t have verified information about this shrine&apos;s history or scenery yet.
          </p>
        </section>
      );
    case "visit":
      return (
        <section aria-label="Visiting" data-section="visit" className="mt-6">
          <h2 className="text-lg font-semibold">Visiting</h2>
          {section.distanceText ? <p className="mt-2 text-sm">{section.distanceText}</p> : null}
          {section.routeUrl ? (
            <a
              href={section.routeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-block rounded-full border px-3 py-1.5 text-sm font-semibold"
            >
              Open the route in Google Maps
            </a>
          ) : null}
        </section>
      );
    default:
      return null;
  }
}

export default function EnShrineDetailClient({ shrineId }: { shrineId: number | null }) {
  const [state, setState] = useState<LoadState>(shrineId ? "loading" : "not_found");
  const [shrine, setShrine] = useState<EnShrineBasics | null>(null);
  const [featureWords, setFeatureWords] = useState<EnFeatureWord[]>([]);
  const [origin, setOrigin] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    if (!shrineId) return;
    let cancelled = false;

    (async () => {
      try {
        const [shrineRes, wordsRes] = await Promise.all([
          api.get(`/shrines/${shrineId}/data/`),
          api.get(`/shrines/${shrineId}/feature-words-en/`).catch(() => ({ data: { items: [] } })),
        ]);
        if (cancelled) return;
        const basics = pickEnShrineBasics(shrineRes.data, shrineId);
        if (!basics) {
          setState("not_found");
          return;
        }
        setShrine(basics);
        setFeatureWords(pickEnFeatureWords(wordsRes.data));
        setState("ready");
      } catch (error) {
        if (cancelled) return;
        const status = (error as { response?: { status?: number } })?.response?.status;
        setState(status === 404 ? "not_found" : "error");
      }
    })();

    void getCurrentOrigin().then((value) => {
      if (!cancelled) setOrigin(value);
    });

    return () => {
      cancelled = true;
    };
  }, [shrineId]);

  return (
    // サイト全体は lang="ja" なので、このページの本文だけ英語として読み上げられるようにする
    <main lang="en" className="mx-auto w-full max-w-2xl px-4 py-8">
      {state === "loading" ? <p className="text-sm text-neutral-600">Loading…</p> : null}
      {state === "not_found" ? <p className="text-sm">This shrine could not be found.</p> : null}
      {state === "error" ? <p className="text-sm">Something went wrong. Please try again.</p> : null}
      {state === "ready" && shrine
        ? buildEnShrineSections({ shrine, featureWords, origin }).map((section) => (
            <Section key={section.kind} section={section} />
          ))
        : null}
      {state === "ready" ? (
        <p className="mt-8 text-xs text-neutral-500">
          Preview: shrine names and addresses are shown in Japanese. Information comes from each shrine&apos;s official
          website.
        </p>
      ) : null}
    </main>
  );
}
