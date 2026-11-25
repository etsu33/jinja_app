"use client";

import type { ReactNode } from "react";

import { trackSearchEvent } from "@/lib/analytics/searchEvents";

type Props = {
  targetId: string;
  shrineId?: number | null;
  highlightId: number;
  direction: "history_to_highlight" | "highlight_to_history";
  className?: string;
  children: ReactNode;
};

// 由緒・歴史と見どころを行き来する画面内リンク（Highlights PR-5）。
// 移動はふつうのページ内リンク（#id）に任せ、押したことだけを計測する。本文は送らない。
export default function ShrineHighlightAnchorLink({
  targetId,
  shrineId = null,
  highlightId,
  direction,
  className,
  children,
}: Props) {
  return (
    <a
      href={`#${targetId}`}
      className={className}
      onClick={() => {
        trackSearchEvent("shrine_highlight_link_click", {
          source: "shrine_detail",
          shrineId,
          highlightId,
          linkDirection: direction,
        });
      }}
    >
      {children}
    </a>
  );
}
