// apps/web/src/components/shrine/detail/ShrineJudgeSection.tsx
import type { DetailMeaningItem, DetailMeaningSection } from "@/components/shrine/detail/types";

type Props = {
  section: DetailMeaningSection;
};

function isSupplementSection(section: DetailMeaningSection): boolean {
  return section.heading.startsWith("補足");
}

function getItemClassName(item: DetailMeaningItem): string {
  if (item.key === "action_meaning") {
    return "rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm";
  }

  if (item.key === "today_flow") {
    return "rounded-xl border border-slate-100 bg-white p-3";
  }

  if (item.key === "after_visit_reflection") {
    return "rounded-xl border border-emerald-100 bg-emerald-50/70 p-3";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "rounded-xl border border-slate-100 bg-slate-50/70 p-3";
  }

  return "rounded-xl bg-slate-50 p-3";
}

function getTitleClassName(item: DetailMeaningItem): string {
  if (item.key === "action_meaning") {
    return "text-sm font-semibold text-amber-950";
  }

  if (item.key === "after_visit_reflection") {
    return "text-sm font-semibold text-emerald-950";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "text-xs font-semibold tracking-[0.04em] text-slate-500";
  }

  return "text-sm font-medium text-slate-700";
}

function getBodyClassName(item: DetailMeaningItem): string {
  if (item.key === "action_meaning") {
    return "mt-2 text-[15px] leading-7 text-amber-950";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "mt-1 text-xs leading-6 text-slate-500";
  }

  return "mt-1 text-sm leading-7 text-slate-600";
}

function MeaningItems({ items }: { items: DetailMeaningItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.key} className={getItemClassName(item)}>
          <h3 className={getTitleClassName(item)}>{item.title}</h3>
          <p className={getBodyClassName(item)}>{item.body}</p>
        </div>
      ))}
    </div>
  );
}

export default function ShrineJudgeSection({ section }: Props) {
  if (isSupplementSection(section)) {
    return (
      <details className="rounded-2xl border border-slate-200 bg-white p-4">
        <summary className="cursor-pointer list-none text-sm font-medium text-slate-700">
          <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
            {section.heading}
          </span>
        </summary>

        <div className="mt-4">
          <MeaningItems items={section.items} />
        </div>
      </details>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <h2 className="text-base font-semibold text-slate-900">{section.heading}</h2>

      <div className="mt-4">
        <MeaningItems items={section.items} />
      </div>
    </section>
  );
}
