// conciergeResultItem.ts
export type ShrineTrustMetadataViewModel = {
  rankClass?: string | null;
  culturalStatus: string[];
  lineage?: string | null;
  originSummary?: string | null;
};

export type ActionSuggestionViewModel = {
  id: string;
  historyTheme: string;
  title: string;
  description: string;
  category: string;
  timing: string;
  difficulty: string;
  timeEstimate: string;
  measurementKey: string;
};

export type ActionSuggestionV4ActionViewModel = {
  label: string;
  description: string;
  actionType: "detail_open" | "route_open" | "save" | "visit" | "reflect" | "pause";
  confidence: number;
};

export type ActionSuggestionV4ReflectionPromptViewModel = {
  question: string;
  promptType: "before_visit" | "after_visit" | "decision" | "emotion" | "constraint";
  sourceSeed: string;
};

export type ActionSuggestionV4SourceViewModel = {
  source:
    | "decision_context"
    | "constraint_profile"
    | "outcome_hint"
    | "action_context"
    | "reflection_question_seed"
    | "fallback";
  reason: string;
};

export type ActionSuggestionV4PreviewViewModel = {
  primaryAction: ActionSuggestionV4ActionViewModel;
  secondaryAction: ActionSuggestionV4ActionViewModel;
  reflectionPrompt: ActionSuggestionV4ReflectionPromptViewModel;
  actionSource: ActionSuggestionV4SourceViewModel;
  preview: boolean;
  version: "v4";
  sourceKeys: string[];
};

export type ConciergeResultItem = {
  id: string;
  tid: string | null;
  trustMetadata?: ShrineTrustMetadataViewModel | null;
  actionSuggestions?: ActionSuggestionViewModel[];
  actionSuggestionV4Preview?: ActionSuggestionV4PreviewViewModel | null;
  cardProps: {
    shrineId: number;
    title: string;
    address?: string;
    imageUrl?: string | null;
    explanationSummary?: string | null;
    explanationPrimaryReason?: string | null;
    breakdown?: any | null;
    badgesOverride?: string[];
  };
  deepReason?: {
    interpretation: string | null;
    shrineMeaning: string | null;
    action: string | null;
    short: string | null;
  };
};
