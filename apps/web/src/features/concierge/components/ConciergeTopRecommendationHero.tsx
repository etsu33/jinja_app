"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  name: string;
  href?: string | null;
  imageUrl?: string | null;
  address?: string | null;
  topReasonLabel?: string | null;
  eyebrowLabel?: string | null;
  subtitle?: string | null;
  trustLabels?: string[];
  originSummary?: string | null;
  catchCopy: string;
  whyTop?: string | null;
  primaryReason?: string | null;
  secondaryReason?: string | null;
  differenceFromOthers?: string | null;
  nextActionHint?: string | null;
  tags?: string[];
  routeLabel?: string;
  secondaryActionSlot?: ReactNode;
  onRouteClick?: () => void;
  onDetailClick?: () => void;
};

export default function ConciergeTopRecommendationHero({
  name,
  href = null,
  imageUrl: _imageUrl = null,
  address = null,
  topReasonLabel = null,
  eyebrowLabel = null,
  subtitle = null,
  trustLabels = [],
  originSummary = null,
  catchCopy,
  whyTop: _whyTop = null,
  primaryReason = null,
  secondaryReason: _secondaryReason = null,
  differenceFromOthers: _differenceFromOthers = null,
  nextActionHint: _nextActionHint = null,
  tags: _tags = [],
  routeLabel = "詳しく見る",
  secondaryActionSlot = null,
  onRouteClick: _onRouteClick,
  onDetailClick,
}: Props) {
  const visibleTrustLabels = trustLabels.filter(Boolean).slice(0, 4);

  return (
    <section className="rounded-[30px] border border-emerald-200 bg-gradient-to-b from-emerald-50/80 to-white p-6 shadow-lg shadow-emerald-900/10 ring-1 ring-emerald-100">
      <div className="space-y-5">
        <div className="space-y-3">
          <div className="space-y-2">
            <div className="text-xs font-semibold tracking-[0.18em] text-emerald-700">
              {eyebrowLabel ?? "信頼できる神社候補"}
            </div>
            <h2 className="text-xl font-semibold leading-8 text-slate-950">{name}</h2>

            {visibleTrustLabels.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {visibleTrustLabels.map((label) => (
                  <span
                    key={label}
                    className="rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-semibold text-emerald-800 ring-1 ring-emerald-100"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : null}

            {originSummary ? <p className="text-sm leading-7 text-slate-700">{originSummary}</p> : null}
            {address ? <div className="text-xs leading-5 text-slate-500">{address}</div> : null}
          </div>
        </div>

        <div className="rounded-2xl border border-emerald-100 bg-white/70 px-4 py-3 shadow-sm shadow-emerald-900/5">
          <div className="space-y-1.5">
            <p className="text-[11px] font-semibold tracking-[0.14em] text-emerald-700">今回の入口</p>
            <p className="text-sm font-semibold leading-6 text-slate-800">
              {subtitle ?? catchCopy}
            </p>
            {topReasonLabel ? <p className="text-xs leading-5 text-slate-500">{topReasonLabel}</p> : null}
          </div>
        </div>

        {primaryReason ? (
          <p className="text-sm leading-7 text-slate-700">{primaryReason.split("。")[0] || primaryReason}</p>
        ) : null}

        <div className="pt-2">
          {href ? (
            <Link
              href={href}
              onClick={onDetailClick}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-5 py-3.5 text-sm font-bold text-white shadow-md shadow-emerald-900/20 transition hover:bg-emerald-700"
            >
              {routeLabel}
            </Link>
          ) : null}

          {secondaryActionSlot ? (
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2" data-testid="hero-secondary-actions">
              {secondaryActionSlot}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
