import type { ShrineDeity, ShrineHistory } from "@/lib/api/types";
import type { DetailFactHistoryItem, DetailFactSection } from "@/components/shrine/detail/types";

// docs/knowledge/shrine-knowledge-contract.md「分類案（To-Be）」の定義に基づく固定ラベル。
// 宗教的・歴史的な意味を新たに解釈しない。
const HISTORY_TYPE_LABELS: Record<string, string> = {
  official_origin: "由緒",
  founding: "創始",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域史",
  editorial_summary: "要約",
};

function resolveHistoryTypeLabel(historyType: string): string {
  return HISTORY_TYPE_LABELS[historyType] ?? historyType;
}

function sortBySortOrder<T extends { sort_order: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => a.sort_order - b.sort_order);
}

/**
 * Shrine Detail APIのdeities/historiesを「神社について」Fact Sectionへ変換する。
 * Knowledge未登録（deities/historiesとも空）の場合はnullを返し、呼び出し側はSectionを表示しない。
 * Legacy(sajin/description)へはfallbackしない。
 */
export function buildShrineFactSection(shrine: {
  deities?: ShrineDeity[];
  histories?: ShrineHistory[];
}): DetailFactSection | null {
  const deities = Array.isArray(shrine.deities) ? shrine.deities : [];
  const histories = Array.isArray(shrine.histories) ? shrine.histories : [];

  if (deities.length === 0 && histories.length === 0) {
    return null;
  }

  const sortedDeities = sortBySortOrder(deities).map((deity) => ({
    display_name: deity.display_name,
    sort_order: deity.sort_order,
  }));

  const sortedHistories: DetailFactHistoryItem[] = sortBySortOrder(histories).map((history) => ({
    history_type: history.history_type,
    history_type_label: resolveHistoryTypeLabel(history.history_type),
    title: history.title,
    content: history.content,
    period_text: history.period_text,
    sort_order: history.sort_order,
  }));

  return {
    kind: "fact",
    heading: "神社について",
    deities: sortedDeities,
    histories: sortedHistories,
  };
}
