// ShrineHistory.history_type の Web 表示ラベル（canonical）。
//
// docs/knowledge/shrine-knowledge-contract.md「分類案（To-Be）」の定義に基づく固定ラベル。
// 宗教的・歴史的な意味を新たに解釈しない。
//
// Shrine Detail（buildShrineFactSection.ts）と Compass Candidate Card の両方が
// この1つの対応表を使う。画面ごとに別のラベル辞書を持たない。
//
// このオブジェクトのkey順が、Presentation Grouping（groupShrineHistoryFacts）における
// group表示順の正本でもある（docs/knowledge/shrine-knowledge-contract.md「Presentation
// Groupingの契約」§canonical-type限定の確認、docs/audit/
// shrine-knowledge-grouping-implementation-readiness.md §13）。新しいhistory_typeを
// backend/temples/models.pyのHISTORY_TYPE_CHOICESへ追加する場合はここにも追記する。
export const SHRINE_HISTORY_TYPE_LABELS: Readonly<Record<string, string>> = {
  official_origin: "由緒",
  founding: "創始",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域史",
  editorial_summary: "要約",
};

/**
 * canonical な history_type のラベルだけを返す。未知の値は null（生のtype文字列を返さない）。
 * 未知の値をどう表示するかは呼び出し側の契約に委ねる。
 */
export function resolveCanonicalHistoryTypeLabel(historyType: unknown): string | null {
  if (typeof historyType !== "string") return null;
  return Object.prototype.hasOwnProperty.call(SHRINE_HISTORY_TYPE_LABELS, historyType)
    ? SHRINE_HISTORY_TYPE_LABELS[historyType]
    : null;
}
