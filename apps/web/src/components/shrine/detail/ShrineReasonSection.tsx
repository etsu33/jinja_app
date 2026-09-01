import type { DetailReasonSection } from "@/components/shrine/detail/types";
import { SHRINE_DETAIL_SECTION_CARD_CLASS, type ShrineDetailSectionVariant } from "@/components/shrine/detail/sectionVariant";

/**
 * ① 推薦判断
 * - 主理由
 * - 補助理由
 * - 1位理由
 *
 * rule:
 * - ラベルの羅列ではなく、説明文として読める形で表示する
 * - group.title を見出しとして使い、group.items は本文として縦に表示する
 * - 推薦判断の説明を行い、状態整理や行動意味は混ぜない
 *
 * variant (PR-G3): "card" (default, unchanged) or "plain" -- borderless
 * editorial flow for the Shrine Detail Meaning narrative (facts stay carded,
 * interpretation reads as one narrative). Content is identical either way.
 */
export default function ShrineReasonSection({
  section,
  variant = "card",
}: {
  section: DetailReasonSection;
  variant?: ShrineDetailSectionVariant;
}) {
  return (
    <section className={variant === "plain" ? "" : SHRINE_DETAIL_SECTION_CARD_CLASS}>
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-3 space-y-4">
        {section.groups.map((group) => (
          <div key={group.title} className="space-y-2">
            <h3 className="text-sm font-medium text-[var(--kt-color-text-secondary)]">{group.title}</h3>
            <div className="space-y-2">
              {group.items.map((item) => (
                <p
                  key={`${group.title}:${item}`}
                  className="text-sm leading-7 text-[var(--kt-color-text-secondary)]"
                >
                  {item}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
