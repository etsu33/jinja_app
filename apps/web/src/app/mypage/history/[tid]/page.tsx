// apps/web/src/app/mypage/history/[tid]/page.tsx
import ConsultationHistoryDetailView from "@/components/views/ConsultationHistoryDetailView";
import { getConciergeThreadServer } from "@/lib/api/concierge.server";
import type { ConciergeThreadDetail } from "@/lib/api/concierge/types";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function ConsultationHistoryDetailPage({
  params,
}: {
  params: Promise<{ tid: string }>;
}) {
  const { tid } = await params;

  let thread: ConciergeThreadDetail | null = null;
  let fetchFailed = false;

  try {
    thread = await getConciergeThreadServer(tid);
  } catch {
    fetchFailed = true;
  }

  return <ConsultationHistoryDetailView tid={tid} thread={thread} fetchFailed={fetchFailed} />;
}
