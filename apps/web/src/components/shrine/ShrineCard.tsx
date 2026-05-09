// apps/web/src/components/shrine/ShrineCard.tsx
"use client";

import * as React from "react";
import ConciergeCard from "@/components/ConciergeCard";
import { useFavorite } from "@/hooks/useFavorite";
import type { ConciergeBreakdown } from "@/lib/api/concierge";
import { buildOneLiner } from "@/lib/concierge/pickAClause";
import ConciergeBreakdownBody, { pickReasonLabel } from "@/components/concierge/ConciergeBreakdownBody";

type Props = {
  shrineId: number;
  title: string;
  address?: string | null;
  description: string;
  imageUrl?: string | null;

  // ✅ 既存
  hideDescription?: boolean;

  // ✅ passthrough（追加）
  subtitle?: string;
  hideBadges?: boolean;
  hideLeftMark?: boolean;
  hideAddress?: boolean;

  showFavorite?: boolean;
  readOnly?: boolean;
  initialFav?: boolean;
  detailHref?: string;
  breakdown?: ConciergeBreakdown | null;
  badgesOverride?: string[];
  hideDetailLink?: boolean;
  variant?: "list" | "detail";
  hideDisclosure?: boolean;
};

function DisclosureSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/30 bg-secondary/30 p-4">
      <div className="text-xs font-medium text-muted-foreground">{title}</div>
      <div className="mt-2 text-sm leading-relaxed text-foreground/70">{children}</div>
    </div>
  );
}

export default function ShrineCard({
  shrineId,
  title,
  address,
  description,
  imageUrl,

  hideDescription = false,

  // ✅ passthrough（追加）
  subtitle,
  hideBadges = false,
  hideLeftMark = false,
  hideAddress = false,

  showFavorite = true,
  initialFav = false,
  readOnly = false,
  detailHref,
  breakdown,
  badgesOverride,
  hideDetailLink = false,
  hideDisclosure = false,
  variant = "list",
}: Props) {
  const { fav, busy, toggle } = useFavorite({ shrineId, initial: initialFav });
  const safeDescription = hideDescription ? "" : description;

  const favButton = !showFavorite ? null : (
    <button
      onClick={toggle}
      disabled={busy || readOnly}
      className="text-sm font-semibold"
      aria-pressed={fav}
      aria-label={fav ? "お気に入り解除" : "お気に入りに追加"}
      title={fav ? "お気に入り解除" : "お気に入りに追加"}
    >
      {fav ? "★" : "☆"}
    </button>
  );

  const safeDetailHref = detailHref ?? (Number.isFinite(shrineId) ? `/shrines/${shrineId}` : undefined);
  const cardDetailHref = hideDetailLink ? undefined : safeDetailHref;

  const reasonLabel = pickReasonLabel(breakdown);
  const defaultBadges = ["正式登録", reasonLabel ? `おすすめ理由：${reasonLabel}` : null]
    .filter((v): v is string => typeof v === "string" && v.trim().length > 0)
    .slice(0, 2);

  const badges =
    badgesOverride?.filter((v): v is string => typeof v === "string" && v.trim().length > 0) ?? defaultBadges;

  const addr = hideAddress ? "" : (address ?? "").trim() || "住所情報は準備中です。";

  const shouldHideDisclosure = hideDisclosure || variant === "detail";

  const disclosureTitle = shouldHideDisclosure ? undefined : "なぜこの場所を選んだか";
  const disclosureBody = shouldHideDisclosure ? undefined : (
    <div className="space-y-4">
      <DisclosureSection title="選んだ理由">
        <p className="text-sm leading-relaxed text-foreground/70">
          {breakdown ? buildOneLiner(breakdown) : "あなたの今の気持ちに合う場所としてお選びしました。"}
        </p>
      </DisclosureSection>

      {breakdown && (
        <DisclosureSection title="詳しい理由">
          <ConciergeBreakdownBody breakdown={breakdown} />
        </DisclosureSection>
      )}
    </div>
  );

  return (
    <ConciergeCard
      title={title}
      address={addr || undefined}
      imageUrl={imageUrl}
      description={safeDescription}
      subtitle={subtitle}
      hideBadges={hideBadges}
      hideLeftMark={hideLeftMark}
      isPrimary
      badges={badges}
      detailHref={cardDetailHref}
      headerRight={favButton}
      disclosureTitle={disclosureTitle}
      disclosureBody={disclosureBody}
    />
  );
}
