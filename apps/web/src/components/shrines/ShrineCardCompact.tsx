import Link from "next/link";
import Image from "next/image";

export function formatDistance(m?: number | null) {
  if (typeof m !== "number" || !Number.isFinite(m)) return null;
  if (m < 1000) return `${Math.round(m)}m`;
  return `${(m / 1000).toFixed(1)}km`;
}

export type ShrineCardCompactTrustMetadata = {
  rankClass?: string | null;
  culturalStatus?: string[] | null;
  lineage?: string | null;
  originSummary?: string | null;
};

export type ShrineCardCompactProps = {
  name: string;
  href?: string | null;
  imageUrl?: string | null;
  address?: string | null;
  // Single, already-resolved "why this candidate" text (docs/product/
  // recommendation-result-information-architecture.md §15 Compact Recommendation Reason /
  // Explanation Consistency): the caller picks one already-Authority-decided source
  // (primary reason phrase, or legacy reason text as fallback) -- this component never
  // chooses between multiple reason sources itself, and never re-decides which one wins.
  reason?: string | null;
  // Explanation-only Knowledge fact (deity/shrine_history) -- docs/product/
  // recommendation-signal-authority.md §8. Same Explanation-only classification Hero uses
  // (reasonV4FactPriority.ts / buildHeroReasonV4Sections.ts via the caller), rendered here
  // as a single small muted line -- deliberately lighter than Hero's own "参考情報" block,
  // since Compact's responsibility is a short candidate summary, not a Hero-sized Conclusion.
  explanationOnlyFactText?: string | null;
  trustMetadata?: ShrineCardCompactTrustMetadata | null;
  tags?: string[];
  distanceM?: number | null;
  // Opt-in only (docs/audit/compass-result-experience.md Section 26-3,
  // P2 finding): a pre-formatted, already-existing-data comparison label
  // (e.g. "約1.2km") shown near the shrine name, independent of the
  // address/distanceM either-or row below. Deliberately a separate prop
  // from distanceM -- that field already drives the existing address-vs-
  // distance fallback (line ~107) used by every current caller (Concierge
  // included); adding a render path gated on distanceM alone would change
  // Concierge's own cards wherever it already passes distanceM. This prop
  // defaults to null and no caller other than Compass sets it, so every
  // other card (Concierge) renders byte-for-byte unchanged.
  distanceLabel?: string | null;
  onDetailClick?: () => void;
};

export default function ShrineCardCompact({
  name,
  href = null,
  imageUrl = null,
  address = null,
  reason = null,
  explanationOnlyFactText = null,
  trustMetadata = null,
  tags: _tags = [],
  distanceM = null,
  distanceLabel = null,
  onDetailClick,
}: ShrineCardCompactProps) {
  const distText = formatDistance(distanceM);
  const trustLabels = [
    trustMetadata?.rankClass,
    ...(trustMetadata?.culturalStatus ?? []),
    trustMetadata?.lineage,
  ].filter((label): label is string => typeof label === "string" && label.trim().length > 0);
  const visibleTrustLabels = trustLabels.slice(0, 2);
  const originSummary = trustMetadata?.originSummary?.trim() || null;

  return (
    <article className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-3">
      <div className="flex gap-3">
        <div className="h-14 w-16 shrink-0 overflow-hidden rounded-[var(--kt-radius-image)] bg-[var(--kt-color-background-subtle)]">
          {imageUrl ? (
            <Image src={imageUrl} alt={name} width={64} height={56} className="h-full w-full object-cover" />
          ) : null}
        </div>

        <div className="min-w-0 flex-1">
          <div className="space-y-1.5">
            <h3 className="truncate text-sm font-semibold text-[var(--kt-color-text-primary)]">{name}</h3>
            {visibleTrustLabels.length > 0 || distanceLabel ? (
              <div className="flex flex-wrap gap-1">
                {distanceLabel ? (
                  <span className="rounded-full bg-[var(--kt-color-background-subtle)] px-2 py-0.5 text-[10px] font-semibold text-[var(--kt-color-text-secondary)]">
                    {distanceLabel}
                  </span>
                ) : null}
                {visibleTrustLabels.map((label) => (
                  <span
                    key={label}
                    className="rounded-full bg-[var(--kt-color-background-subtle)] px-2 py-0.5 text-[10px] font-semibold text-[var(--kt-color-text-secondary)]"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : null}
            {originSummary ? <p className="line-clamp-1 text-xs leading-5 text-[var(--kt-color-text-muted)]">{originSummary}</p> : null}
            {reason ? (
              <div data-testid="recommendation-match-reason">
                <p className="text-[10px] font-semibold text-emerald-700">相談内容・ご利益との一致</p>
                <p className="line-clamp-1 text-xs leading-5 text-[var(--kt-color-text-muted)]">{reason}</p>
              </div>
            ) : null}
            {explanationOnlyFactText ? (
              <p
                className="line-clamp-1 text-[10px] leading-4 text-[var(--kt-color-text-muted)]"
                data-testid="recommendation-compact-explanation-only-fact"
              >
                <span className="font-semibold text-slate-500">参考情報: </span>
                {explanationOnlyFactText}
              </p>
            ) : null}
          </div>

          {address || distText || href ? (
            <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              {address ? <span className="truncate text-xs text-[var(--kt-color-text-muted)]">{address}</span> : null}

              {!address && distText ? <span className="text-xs text-[var(--kt-color-text-muted)]">{distText}</span> : null}

              {href ? (
                <Link
                  href={href}
                  onClick={onDetailClick}
                  className="-m-3 ml-auto inline-flex items-center p-3 text-[11px] font-normal text-[var(--kt-color-text-muted)] transition hover:text-[var(--kt-color-text-secondary)]"
                >
                  詳細だけ見る
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}
