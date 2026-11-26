"use client";

import { useEffect, useRef } from "react";

import ShrineHighlightAnchorLink from "@/components/shrine/detail/ShrineHighlightAnchorLink";
import type { DetailHighlightItem, DetailHighlightSection } from "@/components/shrine/detail/types";
import type { ShrineKnowledgeSource } from "@/lib/api/types";
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

// 見どころの出典は各ブロックに「出典（N件）」の1行で出し、押すとそのブロックの出典が開く（折りたたみ）。
// 根拠を読んだ事実のすぐ横で開けるようにしつつ、画面の情報量を抑える。
// 決定：ドライブ「KAMI MUSUBI 文章と見どころの選定・表現ルール v1.0（案）」6章⑤（2026-11-26 えつこさん）。
export function CollapsibleSourceList({ sources }: { sources: ShrineKnowledgeSource[] }) {
  if (sources.length === 0) return null;

  return (
    <details className="group mt-3 border-t border-[var(--kt-color-border-default)] pt-1">
      <summary className="flex min-h-[44px] cursor-pointer list-none items-center gap-1 text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)] [&::-webkit-details-marker]:hidden">
        <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90">
          ›
        </span>
        出典（{sources.length}件）
      </summary>
      <ul className="mb-1 flex flex-wrap gap-x-3 gap-y-1">
        {sources.map((source, index) => {
          const label = source.title || source.publisher || "出典";
          return (
            <li key={`${source.id}:${index}`}>
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-xs text-[var(--kt-color-text-muted)] underline underline-offset-2"
                >
                  {label}
                </a>
              ) : (
                <span className="text-xs text-[var(--kt-color-text-muted)]">{label}</span>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
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

      <CollapsibleSourceList sources={item.sources} />
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
