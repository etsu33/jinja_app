"use client";

type Props = {
  summary: string;
  modeLabel?: string | null;
  appliedLabel?: string | null;
};

/**
 * Consultation context ("今回の相談の整理").
 *
 * PR-G1 (docs/design/premium-meaning-ui-direction.md §7, Direction C): this is
 * Layer 1 of the recommendation reading flow, so it renders as a borderless
 * editorial section -- an <h2> heading and a plain paragraph -- not a boxed card.
 * The previous rounded/border/shadow surface + pill row made it read as one more
 * equal-weight card in the stack (audit #2656 A-C1/A-C5) and the bold body copy
 * over-emphasised it (A-C4 / V11). `modeLabel` / `appliedLabel` stay as quiet
 * inline notes next to the heading.
 */
export default function ConciergeConsultationSummary({ summary, modeLabel = null, appliedLabel = null }: Props) {
  const cleanedSummary = summary.trim();

  if (!cleanedSummary) return null;

  return (
    <section>
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">今回の相談の整理</h2>

        {modeLabel ? (
          <span className="text-xs font-medium text-[var(--kt-color-text-muted)]">{modeLabel}</span>
        ) : null}

        {appliedLabel ? (
          <span className="text-xs font-medium text-[var(--kt-color-text-muted)]">{appliedLabel}</span>
        ) : null}
      </div>

      <p className="mt-2 text-[15px] leading-7 text-[var(--kt-color-text-primary)]">{cleanedSummary}</p>
    </section>
  );
}
