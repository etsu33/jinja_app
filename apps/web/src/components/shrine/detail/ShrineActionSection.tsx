// apps/web/src/components/shrine/detail/ShrineActionSection.tsx
import type { DetailActionSection, DetailMeaningItem } from "@/components/shrine/detail/types";
import { SHRINE_DETAIL_SECTION_CARD_CLASS, type ShrineDetailSectionVariant } from "@/components/shrine/detail/sectionVariant";

type Props = {
  section: DetailActionSection;
  variant?: ShrineDetailSectionVariant;
};

function ActionItems({ items, variant }: { items: DetailMeaningItem[]; variant: ShrineDetailSectionVariant }) {
  if (variant === "plain") {
    // Borderless editorial: no per-item gold sub-card, tokened text (dark-safe).
    return (
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.key}>
            <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">{item.title}</h3>
            <p className="mt-1 text-[15px] leading-7 text-[var(--kt-color-text-secondary)]">{item.body}</p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.key} className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-premium-border)] bg-[var(--kt-color-premium-surface)] p-4 shadow-[var(--kt-shadow-medium)]">
          <h3 className="text-sm font-semibold text-amber-950">{item.title}</h3>
          <p className="mt-2 text-[15px] leading-7 text-amber-950">{item.body}</p>
        </div>
      ))}
    </div>
  );
}

export default function ShrineActionSection({ section, variant = "card" }: Props) {
  return (
    <section className={variant === "plain" ? "" : SHRINE_DETAIL_SECTION_CARD_CLASS}>
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4">
        <ActionItems items={section.items} variant={variant} />
      </div>
    </section>
  );
}
