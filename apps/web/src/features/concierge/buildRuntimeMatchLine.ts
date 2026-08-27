// apps/web/src/features/concierge/buildRuntimeMatchLine.ts
//
// "今回の相談との接点" (Runtime Match) block for the Concierge Result Hero Card
// (Concierge Evidence Explanation PR). Pure presentation-layer composition ONLY --
// this module never scores, matches, or decides which need tag / goriyaku label
// "won"; it only turns signals ALREADY selected by Backend + existing adapters
// (matched_need_tags, reason_facts is_primary goriyaku_tag) into a single short
// sentence. If neither signal is available, it returns an empty array and the
// caller must not fabricate a placeholder (docs/product/
// recommendation-signal-authority.md §10 Explanation Contract: never present a
// causal match that Ranking didn't actually use).
import { toNeedTagLabels } from "@/lib/concierge/needTagLabelMap";

export function buildRuntimeMatchLines(params: {
  needTags: string[];
  goriyakuLabel: string | null;
}): string[] {
  const needLabels = toNeedTagLabels(params.needTags).slice(0, 2);
  const goriyaku = params.goriyakuLabel?.trim() || null;

  if (needLabels.length === 0 && !goriyaku) return [];

  if (goriyaku) {
    const needPart = needLabels.length > 0 ? `今回の相談テーマ「${needLabels.join("」「")}」と、` : "今回の相談内容と、";
    return [`${needPart}この神社に登録されている「${goriyaku}」に関する情報が重なっています。`];
  }

  return [`今回の相談テーマ「${needLabels.join("」「")}」に関する情報が、この神社に登録されています。`];
}
