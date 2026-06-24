import { notFound } from "next/navigation";
import ScoreV3DashboardClient from "./ScoreV3DashboardClient";

export default function Page() {
  if (process.env.NEXT_PUBLIC_ENABLE_DEBUG_PAGES !== "1") notFound();
  return <ScoreV3DashboardClient />;
}
