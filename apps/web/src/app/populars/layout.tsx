import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// /populars 配下の世界観フレーム（App-wide Web Worldview, variant: standard）。
export default function PopularsWorldviewLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
