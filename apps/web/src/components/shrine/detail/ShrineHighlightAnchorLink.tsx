"use client";

import type { ReactNode } from "react";

import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { cn } from "@/lib/utils";

// 由緒・歴史のタイトルや見どころの名前が長くても（空白の無い長い英語を含む）、カードの幅で折り返す。
// 親が flex のとき a 自身が flex アイテムになるので min-w-0 で縮められるようにし、
// wrap-anywhere（overflow-wrap:anywhere）で最小幅の計算にも折り返しを効かせる（break-words だけでは flex の最小幅が縮まない）。
export const SHRINE_HIGHLIGHT_ANCHOR_WRAP_CLASS = "min-w-0 max-w-full wrap-anywhere";

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
      className={cn(SHRINE_HIGHLIGHT_ANCHOR_WRAP_CLASS, className)}
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
