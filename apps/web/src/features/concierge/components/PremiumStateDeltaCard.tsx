import { useEffect } from "react";
import Link from "next/link";

import type { StateDelta } from "@/lib/concierge/stateComparison";
import { toNeedTagLabels } from "@/lib/concierge/needTagLabelMap";
import { trackRetentionEvent } from "@/lib/analytics/retentionEvents";

type Props = {
  stateDelta: StateDelta;
  isPremium: boolean;
};

function renderTagSentence(tags: string[] | undefined | null, emptyText: string) {
  if (!Array.isArray(tags) || tags.length === 0) {
    return emptyText;
  }

  if (tags.length === 1) {
    return `「${tags[0]}」が見えています。`;
  }

  return `「${tags.join("」「")}」が見えています。`;
}

export default function PremiumStateDeltaCard({ stateDelta, isPremium }: Props) {

  const changedNeedTags = toNeedTagLabels(stateDelta.changedNeedTags ?? []);
  const continuedNeedTags = toNeedTagLabels(stateDelta.continuedNeedTags ?? []);

  useEffect(() => {
    if (!isPremium) return;

    trackRetentionEvent("premium_history_comparison_view", {
      source: "state_delta_card",
      hasSummary: Boolean(stateDelta.summary),
      hasCombinationChange: Boolean(stateDelta.combinationChange?.summary),
      combinationChanged: Boolean(stateDelta.combinationChange?.changed),
      hasTransitionNarrative: Boolean(stateDelta.transitionNarrative?.summary),
      transitionType: stateDelta.transitionNarrative?.type ?? "unknown",
      changedNeedTagCount: changedNeedTags.length,
      continuedNeedTagCount: continuedNeedTags.length,
      daysSincePrevious: stateDelta.daysSincePrevious,
      within7DaysSincePrevious: stateDelta.within7DaysSincePrevious,
    });
  }, [
    changedNeedTags.length,
    continuedNeedTags.length,
    isPremium,
    stateDelta.combinationChange?.changed,
    stateDelta.combinationChange?.summary,
    stateDelta.daysSincePrevious,
    stateDelta.summary,
    stateDelta.transitionNarrative?.summary,
    stateDelta.transitionNarrative?.type,
    stateDelta.within7DaysSincePrevious,
  ]);

  if (!isPremium) {
    return (
      <section className="mx-4 mt-4 rounded-3xl border border-[var(--kt-color-premium-border)] bg-amber-50/80 p-4">
        <div className="space-y-2">
          <p className="text-sm font-semibold text-amber-950">前回との違いをPremiumで確認できます。</p>

          <p className="text-xs leading-6 text-slate-600">気持ちの変化や、続いているテーマをあとから振り返れます。</p>

          <Link
            href="/billing/upgrade?source=state_delta_card&funnelStep=comparison_preview"
            className="inline-flex rounded-2xl bg-[var(--kt-color-premium-accent)] px-4 py-2 text-sm font-semibold text-white"
            onClick={() =>
              trackRetentionEvent("premium_history_comparison_click", {
                source: "state_delta_card",
                funnelStep: "comparison_preview",
              })
            }
          >
            前回との違いを見る
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-4 mt-4 rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4 shadow-sm">
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">前回との違い</p>

          <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {stateDelta.summary ??
              "今回の相談内容から、前回との違いを整理しています。相談を重ねるほど、変化の見え方が安定します。"}
          </p>
        </div>

        {stateDelta.combinationChange?.summary ? (
          <div className="rounded-2xl bg-[var(--kt-color-background-subtle)] p-3">
            <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">状態の重なり</p>

            <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">{stateDelta.combinationChange.summary}</p>
          </div>
        ) : null}

        {stateDelta.transitionNarrative?.summary ? (
          <div className="rounded-2xl bg-emerald-50/60 p-3">
            <p className="text-xs font-semibold text-emerald-700">今の流れ</p>

            <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">
              {stateDelta.transitionNarrative.title}
            </p>

            <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">{stateDelta.transitionNarrative.summary}</p>
          </div>
        ) : null}

        {stateDelta.actionReflection ? (
          <div className="rounded-2xl bg-amber-50/70 p-3">
            <p className="text-xs font-semibold text-[var(--kt-color-premium-accent)]">前回の行動</p>
            <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">{stateDelta.actionReflection.title}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">{stateDelta.actionReflection.summary}</p>
            <p className="mt-2 text-xs font-semibold text-[var(--kt-color-premium-accent)]">{stateDelta.actionReflection.nextActionLabel}</p>
          </div>
        ) : null}

        <div className="rounded-2xl bg-[var(--kt-color-background-subtle)] p-3">
          <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">今回強く出ているテーマ</p>

          <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {renderTagSentence(
              changedNeedTags,
              "今回は新しく強まったテーマを断定するより、今見えている流れを優先して整理しています。",
            )}
          </p>
        </div>

        <div className="rounded-2xl bg-[var(--kt-color-background-subtle)] p-3">
          <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">継続しているテーマ</p>

          <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {renderTagSentence(
              continuedNeedTags,
              "今回は前回と同じテーマが中心に続くというより、別の方向に意識が向き始めています。",
            )}
          </p>
        </div>
      </div>
    </section>
  );
}
