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
export type DetailFactDeity = {
  display_name: string;
  sort_order: number;
};

export type DetailFactHistoryItem = {
  history_type: string;
  history_type_label: string;
  title: string;
  content: string;
  period_text: string;
  sort_order: number;
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
