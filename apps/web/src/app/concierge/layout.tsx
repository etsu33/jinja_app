import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

type Props = {
  children: ReactNode;
};

// Concierge の Route 背景責務（data-app-frame="concierge"）は従来どおりここが持つ。
// 世界観の背景は WorldviewFrame（variant: standard）へ委ねる。
export default function ConciergeRouteLayout({ children }: Props) {
  return (
    <div
      data-app-frame="concierge"
      className="min-h-full w-full bg-[var(--kt-color-background-base)]"
    >
      <WorldviewFrame variant="standard">{children}</WorldviewFrame>
    </div>
  );
}
