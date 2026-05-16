export type PreviousConsultationSummary = {
  threadId: number | null;
  createdAt: string | null;
  consultationSummary: string | null;
  matchedNeedTags: string[];
  primaryNeedLabelJa: string | null;
  primaryReasonLabelJa: string | null;
  recommendationNames: string[];
};

export type StateDelta = {
  previous: PreviousConsultationSummary | null;
  current: PreviousConsultationSummary | null;
  changedNeedTags: string[];
  continuedNeedTags: string[];
  summary: string | null;
};
