// packages/shared/recommendationReasonAuthority.ts
//
// 神社の事実(recommendation_reason_v4_detail.fact)を「② 選ばれた背景」(推薦の根拠)として
// 出してよいかを判定する。Web / モバイルの神社詳細で同じ基準を使う。
//
// 次の2つを両方満たすときだけ、推薦の根拠として扱う。
// 1. 表示する項目が、順位に関わる項目(ご利益 goriyaku / 歴史のテーマ history_theme)であること。
//    御祭神(deity)・由緒(shrine_history)は順位に一切関わらない(Signal Authority 正本 §8)。
// 2. Backend が選んだ主な根拠(reason_facts の is_primary)の type が、意味の一致を表す種類であること
//    (backend recommendation_reason_v4 の semantic_authority と同じ4種類)。
//
// 主な根拠が分からないとき(reason_facts が無い・is_primary が無い)は、根拠として扱わない。
// 補助情報の文があるかどうか(reason_text の中身)では判定しない。

// backend/temples/services/recommendation_reason_v4.py の _build_reason_text にある
// semantic_authority の一覧(primary_source in {"history_theme", "need_tag", "text_hint", "goriyaku_tag"})
// と同じ4種類。どちらかを変えるときは、もう一方も合わせて変えること。
export const RECOMMENDATION_AUTHORITY_PRIMARY_TYPES: ReadonlySet<string> = new Set([
  "history_theme",
  "need_tag",
  "text_hint",
  "goriyaku_tag",
]);

export const RANKING_RELATED_FACT_SOURCES: ReadonlySet<string> = new Set(["goriyaku", "history_theme"]);

/** Backend が is_primary にした reason_fact の type。無ければ null。 */
export function primaryReasonFactType(reasonFacts: unknown): string | null {
  if (!Array.isArray(reasonFacts)) return null;

  for (const fact of reasonFacts) {
    if (!fact || typeof fact !== "object" || Array.isArray(fact)) continue;
    const candidate = fact as Record<string, unknown>;
    if (candidate.is_primary !== true) continue;
    const type = typeof candidate.type === "string" ? candidate.type.trim() : "";
    return type || null;
  }

  return null;
}

/** 主な根拠が、意味の一致を表す種類か。分からないときは false。 */
export function hasRecommendationAuthority(reasonFacts: unknown): boolean {
  const type = primaryReasonFactType(reasonFacts);
  return type !== null && RECOMMENDATION_AUTHORITY_PRIMARY_TYPES.has(type);
}

/** 表示する事実を「② 選ばれた背景」(推薦の根拠)に出してよいか。 */
export function isRecommendationReasonFact(factSource: string | null | undefined, reasonFacts: unknown): boolean {
  if (!factSource || !RANKING_RELATED_FACT_SOURCES.has(factSource)) return false;
  return hasRecommendationAuthority(reasonFacts);
}

/** 推薦の根拠になっている事実の見出し(Web / モバイルの神社詳細で共通)。 */
export const RECOMMENDATION_REASON_FACT_HEADING = "② 選ばれた背景";
/** 推薦の根拠になっていない神社の事実の見出し。選ばれた理由ではなく神社の紹介だと伝える。 */
export const ABOUT_SHRINE_HEADING = "この神社について";
/** 「この神社について」の下の小見出し(表示する項目ごと)。 */
export const ABOUT_SHRINE_GROUP_TITLE_BY_SOURCE: Readonly<Record<string, string>> = {
  deity: "神社の由緒・御祭神",
  shrine_history: "神社の由緒・御祭神",
  goriyaku: "ご利益",
  history_theme: "歴史のテーマ",
};
