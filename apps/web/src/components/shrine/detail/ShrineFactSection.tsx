// apps/web/src/components/shrine/detail/ShrineFactSection.tsx
import type { DetailFactDeity, DetailFactHistoryItem, DetailFactSection } from "@/components/shrine/detail/types";

type Props = {
  section: DetailFactSection;
};

function DeityList({ deities }: { deities: DetailFactDeity[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">御祭神</h3>
      <ul className="mt-2 flex flex-wrap gap-2">
        {deities.map((deity, index) => (
          <li
            key={`${deity.display_name}:${index}`}
            className="inline-flex items-center rounded-[var(--kt-radius-pill)] bg-[var(--kt-color-background-subtle)] px-3 py-1 text-sm text-[var(--kt-color-text-secondary)]"
          >
            {deity.display_name}
          </li>
        ))}
      </ul>
    </div>
  );
}

function HistoryList({ histories }: { histories: DetailFactHistoryItem[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">由緒・歴史</h3>
      <div className="mt-2 space-y-3">
        {histories.map((history, index) => (
          <div
            key={`${history.title}:${index}`}
            className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-3"
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">
                {history.history_type_label}
              </span>
              {history.title ? (
                <h4 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">{history.title}</h4>
              ) : null}
              {history.period_text ? (
                <span className="text-xs text-[var(--kt-color-text-muted)]">{history.period_text}</span>
              ) : null}
            </div>
            {history.content ? (
              <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-[var(--kt-color-text-secondary)]">
                {history.content}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ShrineFactSection({ section }: Props) {
  const hasDeities = section.deities.length > 0;
  const hasHistories = section.histories.length > 0;

  if (!hasDeities && !hasHistories) return null;

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4 space-y-4">
        {hasDeities ? <DeityList deities={section.deities} /> : null}
        {hasHistories ? <HistoryList histories={section.histories} /> : null}
      </div>
    </section>
  );
}
