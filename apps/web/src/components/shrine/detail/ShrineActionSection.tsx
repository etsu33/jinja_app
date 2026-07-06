// apps/web/src/components/shrine/detail/ShrineActionSection.tsx
import type { DetailActionSection, DetailMeaningItem } from "@/components/shrine/detail/types";

type Props = {
  section: DetailActionSection;
};

function ActionItems({ items }: { items: DetailMeaningItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.key} className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-amber-950">{item.title}</h3>
          <p className="mt-2 text-[15px] leading-7 text-amber-950">{item.body}</p>
        </div>
      ))}
    </div>
  );
}

export default function ShrineActionSection({ section }: Props) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <h2 className="text-base font-semibold text-slate-900">{section.heading}</h2>

      <div className="mt-4">
        <ActionItems items={section.items} />
      </div>
    </section>
  );
}
