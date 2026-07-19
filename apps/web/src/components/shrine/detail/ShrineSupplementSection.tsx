import type { DetailSupplementSection } from "@/components/shrine/detail/types";

export default function ShrineSupplementSection({ section }: { section: DetailSupplementSection }) {
  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-3 space-y-3">
        {section.groups.map((group) => (
          <div key={group.title} className="space-y-1">
            <h3 className="text-sm font-medium text-[var(--kt-color-text-secondary)]">{group.title}</h3>
            <div className="flex flex-wrap gap-1.5">
              {group.items.map((item) => (
                <span
                  key={`${group.title}:${item}`}
                  className="inline-flex items-center rounded-[var(--kt-radius-pill)] bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
