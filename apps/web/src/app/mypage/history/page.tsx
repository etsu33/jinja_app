// apps/web/src/app/mypage/history/page.tsx
import ConsultationHistoryListView from "@/components/views/ConsultationHistoryListView";
import { getConciergeThreadsServer } from "@/lib/api/concierge.server";
import type { ConciergeThread } from "@/lib/api/concierge/types";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function ConsultationHistoryListPage() {
  let threads: ConciergeThread[] = [];
  let fetchFailed = false;

  try {
    threads = await getConciergeThreadsServer();
  } catch {
    fetchFailed = true;
  }

  return <ConsultationHistoryListView initialThreads={threads} fetchFailed={fetchFailed} />;
}
