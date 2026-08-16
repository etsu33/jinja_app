import type { ShrineKnowledgeSource } from "@/lib/api/types";

export type DetailReasonGroup = {
  title: string;
  items: string[];
};

export type DetailReasonSection = {
  kind: "reason";
  heading: string;
  groups: DetailReasonGroup[];
};

export type DetailProposalSection = {
  kind: "proposal";
  heading: string;
  lead: string;
  body?: string | null;
};

export type DetailMeaningItem = {
  key: string;
  title: string;
  body: string;
};

export type DetailMeaningSection = {
  kind: "meaning";
  heading: string;
  lead?: string;
  items: DetailMeaningItem[];
};

export type DetailActionSection = {
  kind: "action";
  heading: string;
  items: DetailMeaningItem[];
};

export type DetailSupplementGroup = {
  title: string;
  items: string[];
};

export type DetailSupplementSection = {
  kind: "supplement";
  heading: string;
  groups: DetailSupplementGroup[];
};

// 神社Fact（祭神・由緒・歴史）。Interpretation(meaning)・Recommendation(reason)・Action とは
// 独立した表示責務として扱う。Premium gatingの対象にしない。
//
// Backend verification_statusをUI componentへ直接渡さず、buildShrineFactSection.ts内で
// この型へ変換してから渡す（PR-C4B2）。hiddenはBackend側で既に除外されているため、
// Web ViewModelはfull/disputedの2状態のみを持つ。
export type FactDisplayState = "full" | "disputed";

export type DetailFactDeity = {
  display_name: string;
  sort_order: number;
  displayState: FactDisplayState;
};

export type DetailFactHistoryItem = {
  // Backend id (ShrineHistory.id), preserved for stable identity across Presentation Grouping
  // (docs/audit/shrine-knowledge-grouping-implementation-readiness.md §9). Optional so existing
  // hand-written fixtures/tests that predate this field keep type-checking unchanged.
  id?: number;
  history_type: string;
  history_type_label: string;
  title: string;
  content: string;
  period_text: string;
  sort_order: number;
  displayState: FactDisplayState;
  // Per-Fact provenance (readiness audit §10). Never shared/merged across Facts, including when
  // multiple Facts render under one Presentation Grouping heading.
  sources?: ShrineKnowledgeSource[];
};

export type DetailFactSection = {
  kind: "fact";
  heading: string;
  deities: DetailFactDeity[];
  histories: DetailFactHistoryItem[];
};

export type ShrineDetailSectionModel =
  | DetailReasonSection
  | DetailProposalSection
  | DetailMeaningSection
  | DetailActionSection
  | DetailSupplementSection
  | DetailFactSection;
