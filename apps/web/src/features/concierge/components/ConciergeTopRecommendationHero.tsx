"use client";

import Link from "next/link";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { buildHeroNextActionLines } from "@/features/concierge/buildHeroConclusion";
import type { ActionSuggestionV4PreviewViewModel } from "@/viewmodels/conciergeResultItem";

type Props = {
  name: string;
  href?: string | null;
  address?: string | null;
  topReasonLabel?: string | null;
  eyebrowLabel?: string | null;
  trustLabels?: string[];
  originSummary?: string | null;
  // Recommendation Result Hero Card consolidation
  // (docs/product/recommendation-result-information-architecture.md §6, §13, §15
  // PR2): pre-composed by buildHeroConclusionLines() upstream (ConciergeSectionsRenderer)
  // from the existing, already-Authority-decided reason text (primaryReason / factReason
  // / interpretationReason / legacy fallback). This component never re-decides which
  // line wins -- it only lays the given lines out in the given order.
  conclusionLines?: string[];
  actionReason?: string | null;
  actionSuggestionV4Preview?: ActionSuggestionV4PreviewViewModel | null;
  analyticsSource?: "concierge_result" | "shrine_detail" | "map" | "shrines" | null;
  threadId?: string | null;
  resultSetId?: string | null;
  shrineId?: number | string | null;
  recommendationRank?: number | null;
  historyTheme?: string | null;
  routeLabel?: string;
  secondaryActionSlot?: ReactNode;
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
  address = null,
  topReasonLabel = null,
  eyebrowLabel = null,
  trustLabels = [],
  originSummary = null,
  conclusionLines = [],
  actionReason = null,
  actionSuggestionV4Preview = null,
  analyticsSource = "concierge_result",
  threadId = null,
  resultSetId = null,
  shrineId = null,
  recommendationRank = null,
  historyTheme = null,
  routeLabel = "詳しく見る",
  secondaryActionSlot = null,
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
  // Merges Reason V4's action advice with the (already gated/resolved) Action
  // Suggestion preview summary into one Next Action block -- neither is dropped or
  // re-attributed, see buildHeroConclusion.ts.
  const nextActionLines = buildHeroNextActionLines({
    actionText: actionReason,
    actionSuggestionSummary: actionSuggestionV4Summary || null,
  });
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
            <h2 className="text-xl font-semibold leading-8 text-[var(--kt-color-text-primary)]">{name}</h2>

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

            {originSummary ? <p className="text-sm leading-7 text-[var(--kt-color-text-secondary)]">{originSummary}</p> : null}
            {address ? <div className="text-xs leading-5 text-[var(--kt-color-text-muted)]">{address}</div> : null}
          </div>
        </div>

        {conclusionLines.length > 0 ? (
          <div
            className="rounded-[var(--kt-radius-card)] border border-emerald-100 bg-white/70 px-4 py-3 shadow-sm shadow-emerald-900/5"
            data-testid="recommendation-conclusion"
          >
            <div className="space-y-1.5">
              <p className="text-[11px] font-semibold tracking-[0.14em] text-emerald-700">相談内容・ご利益との一致</p>
              {conclusionLines.map((line, index) => (
                <p key={index} className="text-sm font-semibold leading-6 text-slate-800">
                  {line}
                </p>
              ))}
              {topReasonLabel ? <p className="text-xs leading-5 text-[var(--kt-color-text-muted)]">{topReasonLabel}</p> : null}
            </div>
          </div>
        ) : null}

        {nextActionLines.length > 0 ? (
          <div
            className="rounded-[var(--kt-radius-card)] border border-teal-100 bg-teal-50/70 px-4 py-3 shadow-sm shadow-teal-900/5"
            data-testid="recommendation-next-action"
          >
            <div className="space-y-1">
              <p className="text-[11px] font-semibold tracking-[0.14em] text-teal-700">参拝前にできること</p>
              {nextActionLines.map((line, index) => (
                <p key={index} className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
                  {line}
                </p>
              ))}
            </div>
          </div>
        ) : null}

        <div className="pt-2">
          {href ? (
            <Link
              href={href}
              onClick={onDetailClick}
              className="inline-flex w-full items-center justify-center rounded-[var(--kt-radius-card)] bg-[var(--kt-color-action-primary)] px-5 py-3.5 text-sm font-bold text-[var(--kt-color-action-primary-text)] shadow-md shadow-emerald-900/20 transition hover:bg-[var(--kt-color-action-primary-hover)]"
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
