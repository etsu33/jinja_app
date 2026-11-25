import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// 英語の神社詳細（限定公開）も、英語の相談ページと同じ世界観の背景を使う。
export default function EnShrineDetailLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
