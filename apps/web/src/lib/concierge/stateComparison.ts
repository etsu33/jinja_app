export type PreviousConsultationSummary = {
  threadId: number | null;
  createdAt: string | null;
  consultationSummary: string | null;
  matchedNeedTags: string[];
  combination: {
    key: string;
    title: string;
    summary: string;
  } | null;
  primaryNeedLabelJa: string | null;
  primaryReasonLabelJa: string | null;
  recommendationNames: string[];
};

export type StateDelta = {
  previous: PreviousConsultationSummary | null;
  current: PreviousConsultationSummary | null;
  changedNeedTags: string[];
  continuedNeedTags: string[];
  daysSincePrevious: number | null;
  within7DaysSincePrevious: boolean;
  summary: string | null;
};
