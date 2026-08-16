import type { ShrineDeity, ShrineHistory } from "@/lib/api/types";
import type {
  DetailFactHistoryItem,
  DetailFactSection,
  FactDisplayState,
} from "@/components/shrine/detail/types";

// docs/knowledge/shrine-knowledge-contract.md「分類案（To-Be）」の定義に基づく固定ラベル。
// 宗教的・歴史的な意味を新たに解釈しない。
//
// このオブジェクトのkey順が、Presentation Grouping（groupShrineHistoryFacts）における
// group表示順の正本でもある（docs/knowledge/shrine-knowledge-contract.md「Presentation
// Groupingの契約」§canonical-type限定の確認、docs/audit/
// shrine-knowledge-grouping-implementation-readiness.md §13）。新しいhistory_typeを
// backend/temples/models.pyのHISTORY_TYPE_CHOICESへ追加する場合はここにも追記する。
const HISTORY_TYPE_LABELS: Record<string, string> = {
  official_origin: "由緒",
  founding: "創始",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域史",
  editorial_summary: "要約",
};

const HISTORY_TYPE_ORDER = Object.keys(HISTORY_TYPE_LABELS);

function resolveHistoryTypeLabel(historyType: string): string {
  return HISTORY_TYPE_LABELS[historyType] ?? historyType;
}

// Backend verification_status（PR-C4B1でDetail APIはfull相当/disputedのみ返す）を
// Web ViewModel専用のFactDisplayStateへ変換する唯一の地点。UI component（例:
// ShrineFactSection.tsx）はこの変換結果だけを見て、Backendのverification_status文字列を
// 直接判定しない。想定外の値が来た場合はdisputedへ昇格させず、現行互換のfullとして扱う
// （fail-safe。confidence/history_typeはこの判定に使わない）。
function resolveFactDisplayState(verificationStatus: string): FactDisplayState {
  return verificationStatus === "disputed" ? "disputed" : "full";
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
    displayState: resolveFactDisplayState(deity.verification_status),
  }));

  const sortedHistories: DetailFactHistoryItem[] = sortBySortOrder(histories).map((history) => ({
    id: history.id,
    history_type: history.history_type,
    history_type_label: resolveHistoryTypeLabel(history.history_type),
    title: history.title,
    content: history.content,
    period_text: history.period_text,
    sort_order: history.sort_order,
    displayState: resolveFactDisplayState(history.verification_status),
    sources: Array.isArray(history.sources) ? history.sources : [],
  }));

  return {
    kind: "fact",
    heading: "神社について",
    deities: sortedDeities,
    histories: sortedHistories,
  };
}

export type ShrineHistoryFactGroup = {
  historyType: string;
  label: string;
  items: DetailFactHistoryItem[];
};

export type GroupedShrineHistoryFacts = {
  // 既存canonical history_typeの一致のみでグルーピングされた、disputedを除く各group。
  // 表示順はHISTORY_TYPE_ORDER（HISTORY_TYPE_LABELSのkey順）、group内はsort_order順を維持する。
  groups: ShrineHistoryFactGroup[];
  // disputedなFactは、この関数ではグルーピングしない。呼び出し側は既存の個別表示契約
  // （docs/knowledge/shrine-knowledge-contract.md「Shrine Detail Multi-View Contract」）どおり、
  // 1件ずつ独立して表示する。
  disputed: DetailFactHistoryItem[];
};

/**
 * 「神社について」History Factを、Presentation Grouping契約
 * （docs/knowledge/shrine-knowledge-contract.md「Presentation Groupingの契約」）に基づき、
 * 既存canonical history_typeの完全一致のみでグルーピングする。
 *
 * - Fact本文・id・sourcesは一切変更しない（Operation A/Bを行わない、引用元のオブジェクトを
 *   そのまま各groupへ振り分けるのみ）
 * - disputedなFactはグルーピング対象から除外する（§Disputed Evidence Contract）
 * - group内の順序は入力配列の順序（=既存のsort_order順）をそのまま保持する
 * - 未知のhistory_typeもFactを失わず、その値自体をkeyとする独立groupへ入れる
 */
export function groupShrineHistoryFacts(histories: DetailFactHistoryItem[]): GroupedShrineHistoryFacts {
  const disputed: DetailFactHistoryItem[] = [];
  const byType = new Map<string, DetailFactHistoryItem[]>();

  for (const history of histories) {
    if (history.displayState === "disputed") {
      disputed.push(history);
      continue;
    }

    const bucket = byType.get(history.history_type);
    if (bucket) {
      bucket.push(history);
    } else {
      byType.set(history.history_type, [history]);
    }
  }

  const knownTypes = HISTORY_TYPE_ORDER.filter((type) => byType.has(type));
  const unknownTypes = [...byType.keys()].filter((type) => !HISTORY_TYPE_ORDER.includes(type));

  const groups: ShrineHistoryFactGroup[] = [...knownTypes, ...unknownTypes].map((historyType) => {
    const items = byType.get(historyType) as DetailFactHistoryItem[];
    return {
      historyType,
      label: items[0].history_type_label,
      items,
    };
  });

  return { groups, disputed };
}
