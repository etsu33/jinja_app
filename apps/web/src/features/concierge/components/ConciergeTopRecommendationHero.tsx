"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";
import type { ReactNode } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackActionEvent } from "@/lib/api/actionEvents";
import { trackActionAnalytics } from "@/lib/analytics/actionEvents";
import type {
  ActionSuggestionV4PreviewViewModel,
  ActionSuggestionViewModel,
} from "@/viewmodels/conciergeResultItem";

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
  actionSuggestions?: ActionSuggestionViewModel[];
  actionSuggestionV4Preview?: ActionSuggestionV4PreviewViewModel | null;
  analyticsSource?: "concierge_result" | "shrine_detail" | "map" | "shrines" | null;
  threadId?: string | null;
  resultSetId?: string | null;
  shrineId?: number | string | null;
  recommendationRank?: number | null;
  historyTheme?: string | null;
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
  primaryReason: _primaryReason = null,
  secondaryReason: _secondaryReason = null,
  differenceFromOthers: _differenceFromOthers = null,
  nextActionHint: _nextActionHint = null,
  tags: _tags = [],
  actionSuggestions = [],
  actionSuggestionV4Preview = null,
  analyticsSource = "concierge_result",
  threadId = null,
  resultSetId = null,
  shrineId = null,
  recommendationRank = null,
  historyTheme = null,
  routeLabel = "詳しく見る",
  secondaryActionSlot = null,
  onRouteClick: _onRouteClick,
  onDetailClick,
}: Props) {
  const visibleTrustLabels = trustLabels.filter(Boolean).slice(0, 4);
  const visibleActionSuggestions = useMemo(
    () => actionSuggestions.filter((item) => item.id && item.title).slice(0, 2),
    [actionSuggestions],
  );
  const visibleActionSuggestionIds = visibleActionSuggestions.map((item) => item.id).join(",");
  const visibleActionSuggestionV4Preview = actionSuggestionV4Preview?.preview === true ? actionSuggestionV4Preview : null;
  const entranceCopySource = subtitle ?? catchCopy;

  const entranceCopy = entranceCopySource.split("。")[0]
    ? `${entranceCopySource.split("。")[0]}。`
    : entranceCopySource;

  useEffect(() => {
    if (visibleActionSuggestions.length === 0) return;

    visibleActionSuggestions.forEach((item, index) => {
      trackSearchEvent("action_suggestion_view", {
        source: analyticsSource,
        threadId,
        resultSetId,
        shrineId,
        recommendationRank,
        position: "hero_primary",
        historyTheme: historyTheme ?? item.historyTheme,
        actionSuggestionId: item.id,
        actionCategory: item.category,
        actionTheme: item.historyTheme,
        actionPosition: index + 1,
      });
    });
  }, [
    analyticsSource,
    historyTheme,
    recommendationRank,
    resultSetId,
    shrineId,
    threadId,
    visibleActionSuggestionIds,
    visibleActionSuggestions,
  ]);

  const buildActionEventPayload = (item: ActionSuggestionViewModel, index: number) => ({
    source: analyticsSource,
    threadId,
    resultSetId,
    shrineId,
    recommendationRank,
    position: "hero_primary" as const,
    historyTheme: historyTheme ?? item.historyTheme,
    actionSuggestionId: item.id,
    actionCategory: item.category,
    actionTheme: item.historyTheme,
    actionPosition: index + 1,
  });


  const handleActionEvent = (
    actionType: "action_started" | "action_completed",
    legacyEventName: "action_suggestion_click" | "action_done",
    item: ActionSuggestionViewModel,
    index: number,
  ) => {
    const payload = buildActionEventPayload(item, index);

    trackSearchEvent(legacyEventName, payload);
    trackActionAnalytics({
      actionType,
      actionSuggestionId: item.id,
      source: analyticsSource,
      shrineId,
      threadId,
      historyTheme: historyTheme ?? item.historyTheme,
      actionCategory: item.category,
      resultSetId,
      recommendationRank,
      position: "hero_primary",
      actionPosition: index + 1,
      metadata: {
        legacyEventName,
        actionTheme: item.historyTheme,
      },
    });

    void trackActionEvent({
      actionType,
      actionSuggestionId: item.id,
      source: analyticsSource,
      shrineId,
      threadId,
      historyTheme: historyTheme ?? item.historyTheme,
      actionCategory: item.category,
      metadata: {
        legacyEventName,
        actionTheme: item.historyTheme,
        resultSetId,
        recommendationRank,
        actionPosition: index + 1,
      },
    });
  };

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
            <p className="text-sm font-semibold leading-6 text-slate-800">{entranceCopy}</p>
            {topReasonLabel ? <p className="text-xs leading-5 text-slate-500">{topReasonLabel}</p> : null}
          </div>
        </div>

        {visibleActionSuggestions.length > 0 ? (
          <div
            className="rounded-2xl border border-amber-100 bg-amber-50/70 px-4 py-3 shadow-sm shadow-amber-900/5"
            data-testid="hero-action-suggestions"
          >
            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-[11px] font-semibold tracking-[0.14em] text-amber-700">次の小さな一歩</p>
                <p className="text-xs leading-5 text-slate-600">今の状態に合わせて、無理なく試せる行動です。</p>
              </div>
              <div className="space-y-2">
                {visibleActionSuggestions.map((item, index) => (
                  <div key={item.id} className="rounded-xl bg-white/80 px-3 py-2 ring-1 ring-amber-100">
                    <p className="text-sm font-semibold leading-6 text-slate-800">{item.title}</p>
                    {item.description ? (
                      <p className="mt-0.5 text-xs leading-5 text-slate-600">{item.description}</p>
                    ) : null}
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        className="rounded-lg border border-amber-200 bg-white px-2 py-1.5 text-xs font-semibold text-amber-800 transition hover:bg-amber-50"
                        onClick={() => handleActionEvent("action_started", "action_suggestion_click", item, index)}
                      >
                        試してみる
                      </button>
                      <button
                        type="button"
                        className="rounded-lg bg-amber-600 px-2 py-1.5 text-xs font-semibold text-white transition hover:bg-amber-700"
                        onClick={() => handleActionEvent("action_completed", "action_done", item, index)}
                      >
                        完了
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {visibleActionSuggestionV4Preview ? (
          <div
            className="rounded-2xl border border-teal-100 bg-teal-50/70 px-4 py-3 shadow-sm shadow-teal-900/5"
            data-testid="hero-action-suggestion-v4-preview"
          >
            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-[11px] font-semibold tracking-[0.14em] text-teal-700">次に取りやすい行動</p>
                <p className="text-xs leading-5 text-slate-600">この候補を見たあとに、無理なく進めるための整理です。</p>
              </div>

              <div className="rounded-xl bg-white/85 px-3 py-2 ring-1 ring-teal-100">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-teal-700">まずやること</p>
                <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">
                  {visibleActionSuggestionV4Preview.primaryAction.label}
                </p>
                <p className="mt-0.5 text-xs leading-5 text-slate-600">
                  {visibleActionSuggestionV4Preview.primaryAction.description}
                </p>
              </div>

              <div className="rounded-xl bg-white/85 px-3 py-2 ring-1 ring-teal-100">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-teal-700">次の候補</p>
                <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">
                  {visibleActionSuggestionV4Preview.secondaryAction.label}
                </p>
                <p className="mt-0.5 text-xs leading-5 text-slate-600">
                  {visibleActionSuggestionV4Preview.secondaryAction.description}
                </p>
              </div>

              <div className="rounded-xl bg-white/85 px-3 py-2 ring-1 ring-teal-100">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-teal-700">参拝前の問い</p>
                <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">
                  {visibleActionSuggestionV4Preview.reflectionPrompt.question}
                </p>
              </div>
            </div>
          </div>
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
