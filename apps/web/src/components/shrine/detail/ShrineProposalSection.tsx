// apps/web/src/components/shrine/detail/ShrineProposalSection.tsx
import type { DetailProposalSection } from "@/components/shrine/detail/types";

export default function ShrineProposalSection({ section }: { section: DetailProposalSection }) {
  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-3 space-y-2">
        <p className="text-sm leading-7 text-slate-800">{section.lead}</p>
        {section.body ? <p className="text-sm leading-7 text-slate-600">{section.body}</p> : null}
      </div>
    </section>
  );
}
