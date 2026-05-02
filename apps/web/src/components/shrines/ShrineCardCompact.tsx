import Link from "next/link";
import Image from "next/image";

function formatDistance(m?: number | null) {
  if (typeof m !== "number" || !Number.isFinite(m)) return null;
  if (m < 1000) return `${Math.round(m)}m`;
  return `${(m / 1000).toFixed(1)}km`;
}

function clean(value?: string | null) {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

export type ShrineCardCompactProps = {
  name: string;
  href?: string | null;
  imageUrl?: string | null;
  address?: string | null;
  summary?: string | null;
  primaryReason?: string | null;
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
  tags = [],
  distanceM = null,
  onDetailClick,
}: ShrineCardCompactProps) {
  const distText = formatDistance(distanceM);
  const resolvedPrimaryReason = clean(primaryReason) || null;

  const visibleTags = tags.filter(Boolean).slice(0, 1);

  return (
    <article className="rounded-2xl border border-slate-100 bg-white/90 p-3">
      <div className="flex gap-3">
        <div className="h-14 w-16 shrink-0 overflow-hidden rounded-xl bg-slate-100">
          {imageUrl ? (
            <Image src={imageUrl} alt={name} width={64} height={56} className="h-full w-full object-cover" />
          ) : null}
        </div>

        <div className="min-w-0 flex-1">
          <div className="space-y-1">
            <h3 className="truncate text-sm font-semibold text-slate-900">{name}</h3>

            {resolvedPrimaryReason ? (
              <p className="line-clamp-1 text-xs leading-5 text-slate-600">{resolvedPrimaryReason}</p>
            ) : null}
          </div>

          {address || distText || visibleTags.length > 0 || href ? (
            <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              {address ? <span className="truncate text-xs text-slate-500">{address}</span> : null}

              {!address && distText ? <span className="text-xs text-slate-500">{distText}</span> : null}

              {visibleTags.map((tag) => (
                <span key={tag} className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-500">
                  {tag}
                </span>
              ))}

              {href ? (
                <Link
                  href={href}
                  onClick={onDetailClick}
                  className="ml-auto inline-flex items-center text-xs font-medium text-slate-500 transition hover:text-slate-800"
                >
                  → 詳細
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}
