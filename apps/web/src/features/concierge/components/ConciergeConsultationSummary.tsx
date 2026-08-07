"use client";

type Props = {
  summary: string;
  modeLabel?: string | null;
  appliedLabel?: string | null;
};

export default function ConciergeConsultationSummary({ summary, modeLabel = null, appliedLabel = null }: Props) {
  const cleanedSummary = summary.trim();

  if (!cleanedSummary) return null;

  return (
    <section className="rounded-2xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-5 shadow-sm">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold tracking-[0.04em] text-slate-600">
            今回の相談の整理
          </span>

          {modeLabel ? (
            <span className="inline-flex rounded-full bg-[var(--kt-color-status-success-surface)] px-3 py-1 text-[11px] font-semibold tracking-[0.04em] text-emerald-700">
              {modeLabel}
            </span>
          ) : null}

          {appliedLabel ? (
            <span className="inline-flex rounded-full bg-[var(--kt-color-background-subtle)] px-3 py-1 text-[11px] font-medium tracking-[0.04em] text-[var(--kt-color-text-muted)]">
              {appliedLabel}
            </span>
          ) : null}
        </div>

        <p className="text-base font-semibold leading-8 text-[var(--kt-color-text-primary)]">{cleanedSummary}</p>
      </div>
    </section>
  );
}
