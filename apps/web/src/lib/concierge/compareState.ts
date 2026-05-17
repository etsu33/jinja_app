import type {
  PreviousConsultationSummary,
  StateDelta,
} from "./stateComparison";
import { toNeedTagLabel } from "./needTagLabelMap";

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

  return {
    previous,
    current,
    changedNeedTags,
    continuedNeedTags,
    daysSincePrevious,
    within7DaysSincePrevious,
    summary: buildSummary(changedNeedTags, continuedNeedTags),
  };
}
