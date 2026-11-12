// バックエンドが決めた主な根拠(primary_reason_source)を、画面の言い方を決める唯一の元にする。
//
// ここでは一致の判定はしない。バックエンドが選んだ値を「画面で何と言ってよいか」の3種類に
// 分けるだけ。分け方は backend/temples/services/recommendation_reason_v4.py の
// _align_interpretation_with_authority() と同じにする:
//   - user_selected_tag        → 選んだ条件との一致(相談との一致とは言わない)
//   - element / visit_style / fallback → 「明確な意味的一致が確認できない」
//   - それ以外の主な根拠       → 相談との一致
// 値が無い・知らない値のときは「一致」とは言わない側(none)に倒す。

export type PrimaryReasonMatchKind = "consultation" | "selected_condition" | "none";

const CONSULTATION_MATCH_SOURCES: ReadonlySet<string> = new Set([
  "need_tag",
  "text_hint",
  "goriyaku_tag",
  "history_theme",
]);

export function resolvePrimaryReasonMatchKind(source: unknown): PrimaryReasonMatchKind {
  const value = typeof source === "string" ? source.trim() : "";
  if (CONSULTATION_MATCH_SOURCES.has(value)) return "consultation";
  if (value === "user_selected_tag") return "selected_condition";
  return "none";
}

/** 推薦理由の枠(Hero の結論・ほかの神社のカード)の見出し。 */
export const MATCH_SECTION_LABEL: Readonly<Record<PrimaryReasonMatchKind, string>> = {
  consultation: "相談内容・ご利益との一致",
  selected_condition: "選んだ条件との一致",
  none: "この神社が候補に入った理由",
};
