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

  actionState: "visited" | "saved" | "none" | null;
};

export type CombinationChange = {
  previousTitle: string | null;
  currentTitle: string | null;
  changed: boolean;
  summary: string | null;
};

export type StateTransitionType = "continuation" | "progression" | "recovery" | "regression" | "transition" | "unknown";

export type StateTransitionNarrative = {
  type: StateTransitionType;
  title: string;
  summary: string | null;
};

export type ActionReflectionType = "visited" | "saved" | "none";

export type ActionReflection = {
  type: ActionReflectionType;
  title: string;
  summary: string;
  nextActionLabel: string;
};

export type StateDelta = {
  previous: PreviousConsultationSummary | null;
  current: PreviousConsultationSummary | null;
  changedNeedTags: string[];
  continuedNeedTags: string[];
  daysSincePrevious: number | null;
  within7DaysSincePrevious: boolean;
  summary: string | null;
  combinationChange: CombinationChange;
  transitionNarrative: StateTransitionNarrative;
  actionReflection: ActionReflection | null;
};
