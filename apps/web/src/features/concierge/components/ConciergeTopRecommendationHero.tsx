"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  name: string;
  href?: string | null;
  imageUrl?: string | null;
  address?: string | null;
  topReasonLabel?: string | null;
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
  catchCopy,
  whyTop = null,
  primaryReason = null,
  secondaryReason: _secondaryReason = null,
  differenceFromOthers: _differenceFromOthers = null,
  nextActionHint = null,
  tags = [],
  routeLabel = "経路案内",
  secondaryActionSlot = null,
  onRouteClick,
  onDetailClick,
}: Props) {
  return (
    <section className="rounded-[30px] border border-emerald-200 bg-gradient-to-b from-emerald-50/80 to-white p-6 shadow-lg shadow-emerald-900/10 ring-1 ring-emerald-100">
      <div className="space-y-5">
        <div className="space-y-3">
          {topReasonLabel ? (
            <div className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              {topReasonLabel}
            </div>
          ) : null}

          <div className="space-y-2">
            <div className="text-xs font-semibold tracking-[0.18em] text-emerald-700">今回いちばん合う神社</div>
            <h2 className="text-xl font-semibold leading-8 text-slate-950">{name}</h2>
            <p className="text-sm font-semibold leading-6 text-emerald-800">今のあなたには、まずここを軸に見るのがおすすめです。</p>
            <p className="text-xs font-medium leading-6 text-slate-600">
              他の候補を見る前に、まずここを確認すると判断しやすくなります。
            </p>
            {address ? <div className="text-xs leading-5 text-slate-500">{address}</div> : null}
          </div>
        </div>

        <div className="rounded-2xl border border-emerald-100 bg-white/85 px-4 py-4 shadow-sm shadow-emerald-900/5">
          <p className="text-base font-semibold leading-7 text-slate-950">{catchCopy}</p>
        </div>

        {whyTop || primaryReason ? (
          <div className="space-y-2 text-sm leading-7 text-slate-700">
            {whyTop ? <p>{whyTop}</p> : null}
            {primaryReason ? <p className="text-slate-600">{primaryReason}</p> : null}
          </div>
        ) : null}

        {nextActionHint ? (
          <div className="border-t border-slate-100 pt-3 text-xs leading-6 text-slate-500">
            <p>{nextActionHint}</p>
          </div>
        ) : null}

        {tags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {tags.slice(0, 3).map((tag) => (
              <span key={tag} className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        <div className="pt-2">
          {onRouteClick ? (
            <button
              type="button"
              onClick={onRouteClick}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-5 py-3.5 text-sm font-bold text-white shadow-md shadow-emerald-900/20 transition hover:bg-emerald-700"
            >
              {routeLabel}
            </button>
          ) : null}

          {href || secondaryActionSlot ? (
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2" data-testid="hero-secondary-actions">
              {href ? (
                <Link
                  href={href}
                  onClick={onDetailClick}
                  className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-slate-700"
                >
                  詳しく見る
                </Link>
              ) : null}
              {secondaryActionSlot}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
