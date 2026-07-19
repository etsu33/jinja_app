import Link from "next/link";
import Image from "next/image";

function formatDistance(m?: number | null) {
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
  summary?: string | null;
  primaryReason?: string | null;
  trustMetadata?: ShrineCardCompactTrustMetadata | null;
  tags?: string[];
  distanceM?: number | null;
  onDetailClick?: () => void;
};

export default function ShrineCardCompact({
  name,
  href = null,
  imageUrl = null,
  address = null,
  summary: _summary = null,
  primaryReason = null,
  trustMetadata = null,
  tags: _tags = [],
  distanceM = null,
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
    <article className="rounded-2xl border border-slate-100 bg-white/90 p-3">
      <div className="flex gap-3">
        <div className="h-14 w-16 shrink-0 overflow-hidden rounded-xl bg-slate-100">
          {imageUrl ? (
            <Image src={imageUrl} alt={name} width={64} height={56} className="h-full w-full object-cover" />
          ) : null}
        </div>

        <div className="min-w-0 flex-1">
          <div className="space-y-1.5">
            <h3 className="truncate text-sm font-semibold text-slate-900">{name}</h3>
            {visibleTrustLabels.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {visibleTrustLabels.map((label) => (
                  <span
                    key={label}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : null}
            {originSummary ? <p className="line-clamp-1 text-xs leading-5 text-slate-500">{originSummary}</p> : null}
            {!originSummary && primaryReason ? (
              <p className="line-clamp-1 text-xs leading-5 text-slate-500">{primaryReason}</p>
            ) : null}
          </div>

          {address || distText || href ? (
            <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              {address ? <span className="truncate text-xs text-slate-500">{address}</span> : null}

              {!address && distText ? <span className="text-xs text-slate-500">{distText}</span> : null}

              {href ? (
                <Link
                  href={href}
                  onClick={onDetailClick}
                  className="-m-3 ml-auto inline-flex items-center p-3 text-[11px] font-normal text-slate-400 transition hover:text-slate-600"
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
