

import type {
  PreviousConsultationSummary,
  StateDelta,
} from "./stateComparison";

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

function buildSummary(
  changedNeedTags: string[],
  continuedNeedTags: string[],
): string | null {
  if (changedNeedTags.length > 0) {
    return `前回より「${changedNeedTags.join("」「")}」の傾向が強まっています。`;
  }

  if (continuedNeedTags.length > 0) {
    return `前回から継続して「${continuedNeedTags.join("」「")}」がテーマになっています。`;
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
