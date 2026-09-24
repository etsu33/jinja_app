import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// /plan 配下の世界観フレーム（App-wide Web Worldview, variant: standard）。
export default function PlanWorldviewLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
