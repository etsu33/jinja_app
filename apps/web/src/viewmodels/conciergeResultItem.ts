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

export type ConciergeResultItem = {
  id: string;
  tid: string | null;
  trustMetadata?: ShrineTrustMetadataViewModel | null;
  actionSuggestions?: ActionSuggestionViewModel[];
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
