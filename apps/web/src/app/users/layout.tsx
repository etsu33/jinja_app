import type { ReactNode } from "react";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// /users 配下の世界観フレーム（App-wide Web Worldview, variant: standard）。
export default function UsersWorldviewLayout({ children }: { children: ReactNode }) {
  return <WorldviewFrame variant="standard">{children}</WorldviewFrame>;
}
