
// apps/web/src/components/ConciergeCard.tsx
"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";

export type BaseCardProps = {
  title: string;
  address?: string | null;
  imageUrl?: string | null;

  description: string;
  subtitle?: string;

  isPrimary?: boolean;

  badges?: string[];
  hideBadges?: boolean;
  hideLeftMark?: boolean;

  detailHref?: string;
  detailLabel?: string;

  headerRight?: React.ReactNode;

  disclosureTitle?: string;
  disclosureBody?: React.ReactNode;
};

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 20 20"
      aria-hidden="true"
      className={cn("size-4 text-neutral-500 transition-transform duration-200", open && "rotate-180")}
    >
      <path
        d="M5.5 7.5 10 12l4.5-4.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function ConciergeCard(props: BaseCardProps) {
  const {
    title,
    address,
    imageUrl,
    description,
    subtitle,
    isPrimary = false,
    badges = [],
    hideBadges = false,
    hideLeftMark: _hideLeftMark = false,
    detailHref,
    detailLabel = "この神社を見る",
    headerRight,
    disclosureTitle = "詳細",
    disclosureBody,
  } = props;

  const [open, setOpen] = React.useState(false);

  // disclosureBody があるカードは「閉=clamp」, 「開=clamp解除」
  // disclosureBody が無いカードは「isPrimary ならclampしない / それ以外clamp」
  const clampDesc = disclosureBody ? !open : !isPrimary;

  const sub = (subtitle ?? "").trim();
  const desc = (description ?? "").trim();

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl bg-card",
        "border border-border/40",
        "transition duration-300",
      )}
    >
      {/* media - より大きく、静かな印象に */}
      <div className="relative aspect-[16/10] w-full">
        {imageUrl ? (
          <Image
            src={imageUrl}
            alt={title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 600px"
            priority={isPrimary}
            unoptimized
          />
        ) : (
          <div className="h-full w-full bg-gradient-to-br from-secondary to-muted" />
        )}

        {/* 画像上の薄いレイヤー */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/15 via-transparent to-transparent" />
      </div>

      <div className="space-y-4 px-5 py-5 sm:px-6 sm:py-6">
        {/* Header with favorite */}
        {headerRight && (
          <div className="flex items-center justify-end">
            <div className="shrink-0">{headerRight}</div>
          </div>
        )}

        {/* Title and address - 静かで読みやすく */}
        <div className="space-y-2">
          <h3 className="text-lg font-medium leading-snug tracking-wide text-foreground">
            {title}
          </h3>
          {address && (
            <p className="text-sm text-muted-foreground">
              {address}
            </p>
          )}
        </div>

        {/* Subtitle if present */}
        {sub && (
          <p className="text-sm font-medium leading-relaxed text-foreground/80">
            {sub}
          </p>
        )}

        {/* Description - おすすめ理由を穏やかに伝える */}
        {desc && (
          <div className="border-l-2 border-primary/30 pl-4">
            <p className={cn(
              "text-sm leading-relaxed text-foreground/70",
              clampDesc && "line-clamp-3"
            )}>
              {desc}
            </p>
          </div>
        )}

        {/* Badges - 控えめに */}
        {!hideBadges && badges.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {badges.slice(0, 2).map((badge) => (
              <span
                key={badge}
                className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs text-muted-foreground"
              >
                {badge}
              </span>
            ))}
          </div>
        )}

        {/* CTA - 1つだけ、静かだが明確 */}
        {detailHref && (
          <div className="pt-2">
            <Link
              href={detailHref}
              className={cn(
                "inline-flex min-h-[44px] w-full items-center justify-center rounded-full px-5 py-3",
                "text-sm font-medium tracking-wide",
                "border border-primary/40 bg-primary/8 text-foreground/90",
                "transition-all duration-300",
                "hover:border-primary/50 hover:bg-primary/12",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
              )}
            >
              {detailLabel}
            </Link>
          </div>
        )}
      </div>

      {/* Disclosure - より静かに */}
      {disclosureBody && (
        <div className="border-t border-border/30 bg-secondary/30">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className={cn(
              "flex w-full items-center justify-between px-5 py-4 text-left sm:px-6",
              "transition hover:bg-secondary/50",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
            )}
            aria-expanded={open}
          >
            <span className="text-xs font-medium text-foreground/60">{disclosureTitle}</span>
            <Chevron open={open} />
          </button>

          {open && (
            <div className="px-5 pb-5 pt-1 text-sm leading-relaxed text-foreground/70 sm:px-6 sm:pb-6">
              {disclosureBody}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
