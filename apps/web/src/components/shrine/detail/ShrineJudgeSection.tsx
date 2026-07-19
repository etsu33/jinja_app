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
    return "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-premium-border)] bg-[var(--kt-color-premium-surface)] p-4 shadow-[var(--kt-shadow-medium)]";
  }

  if (item.key === "today_flow") {
    return "rounded-[var(--kt-radius-panel)] border border-slate-100 bg-[var(--kt-color-surface-default)] p-3";
  }

  if (item.key === "after_visit_reflection") {
    return "rounded-[var(--kt-radius-panel)] border border-emerald-100 bg-emerald-50/70 p-3";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "rounded-[var(--kt-radius-panel)] border border-slate-100 bg-slate-50/70 p-3";
  }

  return "rounded-[var(--kt-radius-panel)] bg-[var(--kt-color-background-subtle)] p-3";
}

function getTitleClassName(item: DetailMeaningItem): string {
  if (item.key === "action_meaning") {
    return "text-sm font-semibold text-amber-950";
  }

  if (item.key === "after_visit_reflection") {
    return "text-sm font-semibold text-emerald-950";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "text-xs font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]";
  }

  return "text-sm font-medium text-[var(--kt-color-text-secondary)]";
}

function getBodyClassName(item: DetailMeaningItem): string {
  if (item.key === "action_meaning") {
    return "mt-2 text-[15px] leading-7 text-amber-950";
  }

  if (item.key === "history_context" || item.key === "deity_symbol" || item.key === "benefit_action") {
    return "mt-1 text-xs leading-6 text-[var(--kt-color-text-muted)]";
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
      <details className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
        <summary className="cursor-pointer list-none text-sm font-medium text-[var(--kt-color-text-secondary)]">
          <span className="inline-flex items-center rounded-[var(--kt-radius-pill)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] px-3 py-1.5 text-sm text-[var(--kt-color-text-secondary)]">
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
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4">
        <MeaningItems items={section.items} />
      </div>
    </section>
  );
}
