import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// 英語の相談ページ（限定公開）も、日本語のコンシェルジュと同じ世界観の背景を使う。
export default function EnConciergeLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
