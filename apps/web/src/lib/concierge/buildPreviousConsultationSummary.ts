

import type { ConciergeThreadDetail } from "@/lib/api/concierge";
import type { PreviousConsultationSummary } from "./stateComparison";
import { pickExplanationPayloadFromThread } from "./pickExplanationPayloadFromThread";

export function buildPreviousConsultationSummary(
  thread: ConciergeThreadDetail | null | undefined,
): PreviousConsultationSummary | null {
  if (!thread) {
    return null;
  }

  const recs = thread.recommendations_v2 ?? thread.recommendations ?? [];
  const first = recs[0];
  const shrineId = Number(first?.shrine_id ?? first?.id);
  const payload = Number.isFinite(shrineId)
    ? pickExplanationPayloadFromThread(thread, shrineId)
    : null;

  const recommendationNames = [
    ...(thread.recommendations_v2 ?? []),
    ...(thread.recommendations ?? []),
  ]
    .map((r) => r?.name)
    .filter((name): name is string => Boolean(name));

  return {
    threadId: thread.thread.id,
    createdAt: thread.thread.last_message_at ?? null,
    consultationSummary: payload?.original_reason ?? null,
    matchedNeedTags:
      first?.breakdown?.matched_need_tags ?? (payload?.primary_need_tag ? [payload.primary_need_tag] : []),
    primaryNeedLabelJa: payload?.primary_need_label_ja ?? null,
    primaryReasonLabelJa: payload?.primary_reason?.label_ja ?? null,
    recommendationNames,
  };
}
