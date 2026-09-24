import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// /terms 配下の世界観フレーム（App-wide Web Worldview, variant: standard）。
export default function TermsWorldviewLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
