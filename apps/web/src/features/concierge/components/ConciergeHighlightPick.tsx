"use client";

import Link from "next/link";

import DetailSection from "@/components/shrine/DetailSection";
import type { ConciergeHighlightPick as HighlightPick } from "@/features/concierge/highlightPick";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";

type Props = {
  pick: HighlightPick;
  /** hero：第一候補（見出しつき）／ compact：2位以降のカードの下（小さめ） */
  variant: "hero" | "compact";
  shrineId: number;
  recommendationRank: number;
  threadId?: string | null;
  resultSetId?: string | null;
  recommendationInstanceId?: string | null;
};

// 見どころ単位の推薦 段階A（PR-3）：推薦カードの「ここで見る」。
// - 推薦理由ではなく、参拝で何を見るか（Action Layer）。推薦理由の見出しの中には入れない
// - 押すと神社詳細の見どころの位置へ移る。押したことだけを計測し、文は送らない
export default function ConciergeHighlightPick({
  pick,
  variant,
  shrineId,
  recommendationRank,
  threadId = null,
  resultSetId = null,
  recommendationInstanceId = null,
}: Props) {
  const onClick = () => {
    trackSearchEvent("concierge_highlight_pick_click", {
      source: "concierge_result",
      threadId: threadId ?? undefined,
      resultSetId,
      shrineId,
      recommendationRank,
      highlightId: pick.highlightId,
      highlightNeedTag: pick.needTag,
      recommendationInstanceId,
    });
  };

  const link = (
    <Link
      href={pick.href}
      onClick={onClick}
      className="font-semibold text-[var(--kt-color-text-primary)] underline underline-offset-4 hover:opacity-80"
    >
      {pick.name}
    </Link>
  );

  if (variant === "compact") {
    return (
      <div
        data-testid="concierge-highlight-pick"
        className="space-y-1 px-1 text-sm leading-6 text-[var(--kt-color-text-secondary)]"
      >
        <p>
          <span className="mr-2 text-xs font-semibold text-[var(--kt-color-text-muted)]">ここで見る</span>
          {link}
        </p>
        <p>{pick.answerText}</p>
      </div>
    );
  }

  return (
    <div data-testid="concierge-highlight-pick">
      <DetailSection variant="plain" title="ここで見る">
        <div className="space-y-2">
          <p className="text-[15px] leading-7">{link}</p>
          <p className="text-[15px] leading-7 text-[var(--kt-color-text-primary)]">{pick.answerText}</p>
        </div>
      </DetailSection>
    </div>
  );
}
