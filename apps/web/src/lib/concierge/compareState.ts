import type {
  PreviousConsultationSummary,
  StateDelta,
} from "./stateComparison";
import { toNeedTagLabel } from "./needTagLabelMap";
import { buildStateTransitionNarrative } from "./stateTransitionNarrative";

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

function buildSummary(
  changedNeedTags: string[],
  continuedNeedTags: string[],
): string | null {
  if (changedNeedTags.length > 0) {
    const labels = changedNeedTags.map(toNeedTagLabel);
    return `前回より「${labels.join("」「")}」を意識する流れが強まっています。`;
  }

  if (continuedNeedTags.length > 0) {
    const labels = continuedNeedTags.map(toNeedTagLabel);
    return `前回から継続して「${labels.join("」「")}」がテーマになっています。`;
  }

  return null;
}

function buildCombinationChange(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): StateDelta["combinationChange"] {
  const previousCombination = previous?.combination ?? null;
  const currentCombination = current?.combination ?? null;
  const previousTitle = previousCombination?.title ?? null;
  const currentTitle = currentCombination?.title ?? null;

  if (!previousCombination && !currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: false,
      summary: null,
    };
  }

  if (!previousCombination && currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: true,
      summary: `今回は「${currentTitle}」が状態の重なりとして見えています。`,
    };
  }

  if (previousCombination && !currentCombination) {
    return {
      previousTitle,
      currentTitle,
      changed: true,
      summary: previousTitle
        ? `前回見えていた「${previousTitle}」とは違い、今回は単一のテーマが中心に出ています。`
        : null,
    };
  }

  const changed = previousCombination?.key !== currentCombination?.key;

  if (!changed) {
    return {
      previousTitle,
      currentTitle,
      changed: false,
      summary: currentTitle ? `前回から「${currentTitle}」が継続して見えています。` : null,
    };
  }

  return {
    previousTitle,
    currentTitle,
    changed: true,
    summary:
      previousTitle && currentTitle
        ? `前回は「${previousTitle}」が見えていましたが、今回は「${currentTitle}」が強く出ています。`
        : null,
  };
}

function calculateDaysSincePrevious(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): number | null {
  if (!previous?.createdAt || !current?.createdAt) return null;

  const previousTime = new Date(previous.createdAt).getTime();
  const currentTime = new Date(current.createdAt).getTime();

  if (!Number.isFinite(previousTime) || !Number.isFinite(currentTime)) return null;

  const diffMs = currentTime - previousTime;
  if (diffMs < 0) return null;

  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

export function compareState(
  previous: PreviousConsultationSummary | null,
  current: PreviousConsultationSummary | null,
): StateDelta {
  const previousTags = unique(previous?.matchedNeedTags ?? []);
  const currentTags = unique(current?.matchedNeedTags ?? []);

  const changedNeedTags = currentTags.filter(
    (tag) => !previousTags.includes(tag),
  );

  const continuedNeedTags = currentTags.filter((tag) =>
    previousTags.includes(tag),
  );

  const daysSincePrevious = calculateDaysSincePrevious(previous, current);
  const within7DaysSincePrevious = daysSincePrevious !== null && daysSincePrevious <= 7;
  const combinationChange = buildCombinationChange(previous, current);
  const transitionNarrative = buildStateTransitionNarrative({
    previousNeedTags: previousTags,
    currentNeedTags: currentTags,
    changedNeedTags,
    continuedNeedTags,
    combinationChanged: combinationChange.changed,
  });

  return {
    previous,
    current,
    changedNeedTags,
    continuedNeedTags,
    daysSincePrevious,
    within7DaysSincePrevious,
    summary: buildSummary(changedNeedTags, continuedNeedTags),
    combinationChange,
    transitionNarrative,
  };
}
