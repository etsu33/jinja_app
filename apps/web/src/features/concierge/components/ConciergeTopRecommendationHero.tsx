"use client";

import Link from "next/link";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
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

function pickActionSuggestionV4Summary(preview: ActionSuggestionV4PreviewViewModel): string {
  const primaryLabel = preview.primaryAction.label.trim();
  if (primaryLabel) return primaryLabel;

  return preview.reflectionPrompt.question.trim();
}

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
  actionSuggestions: _actionSuggestions = [],
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
  const visibleActionSuggestionV4Preview = actionSuggestionV4Preview?.preview === true ? actionSuggestionV4Preview : null;
  const actionSuggestionV4Summary = visibleActionSuggestionV4Preview
    ? pickActionSuggestionV4Summary(visibleActionSuggestionV4Preview)
    : "";
  const visibleActionSuggestionV4PreviewKey = visibleActionSuggestionV4Preview
    ? [
        visibleActionSuggestionV4Preview.primaryAction.actionType,
        visibleActionSuggestionV4Preview.primaryAction.label,
        visibleActionSuggestionV4Preview.reflectionPrompt.promptType,
        visibleActionSuggestionV4Preview.reflectionPrompt.question,
        visibleActionSuggestionV4Preview.actionSource.source,
      ].join("|")
    : "";
  const entranceCopySource = subtitle ?? catchCopy;

  const entranceCopy = entranceCopySource.split("。")[0]
    ? `${entranceCopySource.split("。")[0]}。`
    : entranceCopySource;

  useEffect(() => {
    if (!visibleActionSuggestionV4Preview || !actionSuggestionV4Summary) return;

    const basePayload = {
      source: analyticsSource,
      threadId,
      resultSetId,
      shrineId,
      recommendationRank,
      position: "hero_primary" as const,
      historyTheme,
      actionSuggestionVersion: visibleActionSuggestionV4Preview.version,
      primaryActionType: visibleActionSuggestionV4Preview.primaryAction.actionType,
      secondaryActionType: visibleActionSuggestionV4Preview.secondaryAction.actionType,
      actionPromptType: visibleActionSuggestionV4Preview.reflectionPrompt.promptType,
      actionSource: visibleActionSuggestionV4Preview.actionSource.source,
      sourceKeys: visibleActionSuggestionV4Preview.sourceKeys.join(","),
      summaryLine: actionSuggestionV4Summary,
    };

    trackSearchEvent("action_suggestion_preview_view", basePayload);
    // Action Suggestionのreflection promptは「実際にReflection入力UIが表示された」ことを意味しないため、
    // reflection_prompt_view ではなく専用イベントで計測する。
    trackSearchEvent("action_suggestion_reflection_preview_view", {
      ...basePayload,
      reflectionPromptSourceSeed: visibleActionSuggestionV4Preview.reflectionPrompt.sourceSeed,
    });
  }, [
    actionSuggestionV4Summary,
    analyticsSource,
    historyTheme,
    recommendationRank,
    resultSetId,
    shrineId,
    threadId,
    visibleActionSuggestionV4Preview,
    visibleActionSuggestionV4PreviewKey,
  ]);

  return (
    <section className="rounded-[30px] border border-emerald-200 bg-gradient-to-b from-emerald-50/80 to-white p-6 shadow-lg shadow-emerald-900/10 ring-1 ring-emerald-100">
      <div className="space-y-5">
        <div className="space-y-3">
          <div className="space-y-2">
            <div className="text-xs font-semibold tracking-[0.18em] text-emerald-700">
              {eyebrowLabel ?? "今の相談に近い神社"}
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

        {actionSuggestionV4Summary ? (
          <div
            className="rounded-2xl border border-teal-100 bg-teal-50/70 px-4 py-3 shadow-sm shadow-teal-900/5"
            data-testid="hero-action-suggestion-v4-preview"
          >
            <p className="text-[11px] font-semibold tracking-[0.14em] text-teal-700">次の一歩</p>
            <p className="mt-1 truncate text-sm leading-6 text-slate-700">{actionSuggestionV4Summary}</p>
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
