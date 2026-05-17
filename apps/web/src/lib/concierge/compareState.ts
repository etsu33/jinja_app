

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

  return {
    previous,
    current,
    changedNeedTags,
    continuedNeedTags,
    summary: buildSummary(changedNeedTags, continuedNeedTags),
  };
}
