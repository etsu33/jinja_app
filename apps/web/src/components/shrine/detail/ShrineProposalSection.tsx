// apps/web/src/components/shrine/detail/ShrineProposalSection.tsx
import type { DetailProposalSection } from "@/components/shrine/detail/types";
import { SHRINE_DETAIL_SECTION_CARD_CLASS, type ShrineDetailSectionVariant } from "@/components/shrine/detail/sectionVariant";

export default function ShrineProposalSection({
  section,
  variant = "card",
}: {
  section: DetailProposalSection;
  variant?: ShrineDetailSectionVariant;
}) {
  return (
    <section className={variant === "plain" ? "" : SHRINE_DETAIL_SECTION_CARD_CLASS}>
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-3 space-y-2">
        <p className="text-sm leading-7 text-slate-800">{section.lead}</p>
        {section.body ? <p className="text-sm leading-7 text-slate-600">{section.body}</p> : null}
      </div>
    </section>
  );
}
