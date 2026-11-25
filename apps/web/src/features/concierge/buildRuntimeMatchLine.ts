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
import { toDisplayLabel } from "@/lib/concierge/displayLabel";
import { toNeedTagLabels } from "@/lib/concierge/needTagLabelMap";

export function buildRuntimeMatchLines(params: {
  needTags: string[];
  /** 表示用の名前(label_ja、無ければ label)。英字・数字・記号だけの内部名は画面に出さない。 */
  goriyakuLabel: string | null;
  /**
   * Backend が goriyaku_tag を主な根拠に選んだか。表示名が無い(内部名だけの)ときも、
   * 名前を入れない文で「重なっている」ことは伝える。
   */
  goriyakuMatched?: boolean;
}): string[] {
  const needLabels = toNeedTagLabels(params.needTags).slice(0, 2);
  const goriyaku = toDisplayLabel(params.goriyakuLabel);
  const hasGoriyakuMatch = Boolean(goriyaku) || params.goriyakuMatched === true;

  if (needLabels.length === 0 && !hasGoriyakuMatch) return [];

  if (hasGoriyakuMatch) {
    const needPart = needLabels.length > 0 ? `今回の相談テーマ「${needLabels.join("」「")}」と、` : "今回の相談内容と、";
    if (!goriyaku) return [`${needPart}この神社に登録されている情報が重なっています。`];
    return [`${needPart}この神社に登録されている「${goriyaku}」に関する情報が重なっています。`];
  }

  return [`今回の相談テーマ「${needLabels.join("」「")}」に関する情報が、この神社に登録されています。`];
}
