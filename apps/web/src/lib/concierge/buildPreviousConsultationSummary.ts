import type { ConciergeThreadDetail } from "@/lib/api/concierge";
import { resolveNeedCombinationNarrative } from "@/lib/concierge/narrative/needCombinationMap";
import type { NeedTag } from "@/lib/concierge/narrative/types";
import { pickExplanationPayloadFromThread } from "./pickExplanationPayloadFromThread";
import type { PreviousConsultationSummary } from "./stateComparison";

export function buildPreviousConsultationSummary(
  thread: ConciergeThreadDetail | null | undefined,
): PreviousConsultationSummary | null {
  if (!thread) {
    return null;
  }

  const root = thread as ConciergeThreadDetail & {
    id?: number | null;
    last_message_at?: string | null;
  };
  const threadLike = thread.thread ?? root;

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

  const matchedNeedTags =
    first?.breakdown?.matched_need_tags ?? (payload?.primary_need_tag ? [payload.primary_need_tag] : []);
  const combination = resolveNeedCombinationNarrative(matchedNeedTags as NeedTag[]);

  return {
    threadId: typeof threadLike.id === "number" ? threadLike.id : null,
    createdAt: threadLike.last_message_at ?? null,
    consultationSummary: payload?.original_reason ?? null,
    matchedNeedTags,
    combination: combination
      ? {
          key: combination.key,
          title: combination.title,
          summary: combination.summary,
        }
      : null,
    primaryNeedLabelJa: payload?.primary_need_label_ja ?? null,
    primaryReasonLabelJa: payload?.primary_reason?.label_ja ?? null,
    recommendationNames,
    actionState: first?.action_state ?? null,
  };
}
