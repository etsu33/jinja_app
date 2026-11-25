"use client";

import { useEffect, useRef } from "react";

import ShrineHighlightAnchorLink from "@/components/shrine/detail/ShrineHighlightAnchorLink";
import { SourceList } from "@/components/shrine/detail/ShrineFactSection";
import type { DetailHighlightItem, DetailHighlightSection } from "@/components/shrine/detail/types";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { shrineHighlightAnchorId, shrineHistoryAnchorId } from "@/lib/shrine/buildShrineHighlightSection";

type Props = {
  section: DetailHighlightSection;
  shrineId?: number | null;
};

// 節が半分以上画面に入ったときに1回だけ計測する。IntersectionObserver が無い環境では表示時に計測する。
function useHighlightsViewTracking(shrineId: number | null, highlightCount: number) {
  const ref = useRef<HTMLElement | null>(null);
  const trackedRef = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || trackedRef.current) return;

    const track = () => {
      if (trackedRef.current) return;
      trackedRef.current = true;
      trackSearchEvent("shrine_highlights_view", { source: "shrine_detail", shrineId, highlightCount });
    };

    if (typeof IntersectionObserver === "undefined") {
      track();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          track();
          observer.disconnect();
        }
      },
      { threshold: 0.5 },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [shrineId, highlightCount]);

  return ref;
}

function HighlightCard({ item, shrineId }: { item: DetailHighlightItem; shrineId: number | null }) {
  return (
    <li
      id={shrineHighlightAnchorId(item.id)}
      className="scroll-mt-24 rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-3"
    >
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        {item.categoryLabel ? (
          <span className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">
            {item.categoryLabel}
          </span>
        ) : null}
        <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">{item.name}</h3>
      </div>

      {item.locationHint ? (
        <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">
          <span className="font-semibold">場所の目安：</span>
          {item.locationHint}
        </p>
      ) : null}

      <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-[var(--kt-color-text-secondary)]">
        {item.description}
      </p>

      {item.historicalConnection ? (
        <div className="mt-3">
          <h4 className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">
            この見どころが伝える歴史
          </h4>
          <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {item.historicalConnection}
          </p>
        </div>
      ) : null}

      {item.linkedHistories.length > 0 ? (
        <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
          {item.linkedHistories.map((history) => (
            <li key={history.id}>
              <ShrineHighlightAnchorLink
                targetId={shrineHistoryAnchorId(history.id)}
                shrineId={shrineId}
                highlightId={item.id}
                direction="highlight_to_history"
                className="text-xs text-[var(--kt-color-action-primary)] underline underline-offset-2"
              >
                由緒・歴史を読む：{history.title}
              </ShrineHighlightAnchorLink>
            </li>
          ))}
        </ul>
      ) : null}

      {item.observedOnLabel ? (
        <p className="mt-2 text-[11px] text-[var(--kt-color-text-muted)]">{item.observedOnLabel}に現地で確認</p>
      ) : null}

      <SourceList sources={item.sources} />
    </li>
  );
}

// 「ここで見られるもの」（Highlights PR-5）。由緒・歴史（ShrineFactSection）のすぐ下に置き、
// 読んだ話を境内のどこで確かめられるかを示す。Fact と同じく Premium で隠さない。
export default function ShrineHighlightSection({ section, shrineId = null }: Props) {
  const ref = useHighlightsViewTracking(shrineId, section.items.length);

  if (section.items.length === 0) return null;

  return (
    <section
      ref={ref}
      aria-labelledby="shrine-highlights-heading"
      className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4"
    >
      <h2 id="shrine-highlights-heading" className="text-base font-semibold text-[var(--kt-color-text-primary)]">
        {section.heading}
      </h2>
      <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">
        境内で実際に見られるものです。参道の順に並べています。
      </p>
      <ul className="mt-4 space-y-3">
        {section.items.map((item) => (
          <HighlightCard key={item.id} item={item} shrineId={shrineId} />
        ))}
      </ul>
    </section>
  );
}
