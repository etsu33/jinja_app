"use client";

import Link from "next/link";

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
  onRouteClick,
  onDetailClick,
}: Props) {
  return (
    <section className="rounded-[28px] border border-emerald-100 bg-white p-5 shadow-sm shadow-emerald-900/5">
      <div className="space-y-4">
        <div className="space-y-3">
          {topReasonLabel ? (
            <div className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              {topReasonLabel}
            </div>
          ) : null}

          <div className="space-y-2">
            <div className="text-xs font-semibold tracking-[0.18em] text-emerald-700">今回のおすすめ</div>
            <h2 className="text-xl font-semibold leading-8 text-slate-950">{name}</h2>
            {address ? <div className="text-xs leading-5 text-slate-500">{address}</div> : null}
          </div>
        </div>

        <div className="rounded-2xl bg-emerald-50/70 px-4 py-3">
          <p className="text-base font-semibold leading-7 text-slate-900">{catchCopy}</p>
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

        <div className="flex flex-col gap-2 pt-1 sm:flex-row">
          {onRouteClick ? (
            <button
              type="button"
              onClick={onRouteClick}
              className="inline-flex flex-1 items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              {routeLabel}
            </button>
          ) : null}

          {href ? (
            <Link
              href={href}
              onClick={onDetailClick}
              className="inline-flex flex-1 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              詳細を見る
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}
