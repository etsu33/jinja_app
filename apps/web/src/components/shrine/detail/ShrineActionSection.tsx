// apps/web/src/components/shrine/detail/ShrineActionSection.tsx
import type { DetailActionSection, DetailMeaningItem } from "@/components/shrine/detail/types";

type Props = {
  section: DetailActionSection;
};

function ActionItems({ items }: { items: DetailMeaningItem[] }) {
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

export default function ShrineActionSection({ section }: Props) {
  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4">
        <ActionItems items={section.items} />
      </div>
    </section>
  );
}
