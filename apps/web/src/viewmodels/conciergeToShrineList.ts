import type {
  ActionSuggestionV4ActionViewModel,
  ActionSuggestionV4PreviewViewModel,
  ActionSuggestionV4ReflectionPromptViewModel,
  ActionSuggestionV4SourceViewModel,
  ConciergeResultItem,
} from "@/viewmodels/conciergeResultItem";
import { buildRecommendationReasonViewModel } from "@/lib/concierge/buildRecommendationReasonViewModel";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import {
  buildNeedPrimaryShortCopy,
  isNeedDisplayTag,
  labelNeedDisplayTag,
  type NeedDisplayTag,
  type ShrineTone,
} from "@/features/concierge/copy/needDisplayCopy";

export type ConciergeResponse = {
  ok: boolean;
  plan?: "anonymous" | "free" | "premium" | null;
  remaining?: number | null;
  limit?: number | null;
  limitReached?: boolean;
  reply?: string | null;
  thread_id?: string | null;
  data?: {
    thread_id?: string | null;
    _need?: { tags?: string[] };
    _signals?: Record<string, unknown> | null;
    message?: string | null;
    recommendations?: any[];
  };
};

function normalizeShrineName(name?: string | null): string {
  return (name ?? "").replace(/\s+/g, "").trim();
}

function getShrineTone(shrineName?: string | null): ShrineTone {
  const name = normalizeShrineName(shrineName);

  if (name.includes("三峯")) return "strong";
  if (name.includes("伊勢神宮") || name.includes("内宮")) return "quiet";
  if (name.includes("乃木")) return "tight";

  return "neutral";
}

function resolveListPrimaryTag(args: {
  primaryReasonLabel?: string | null;
  fallbackTags?: string[] | null;
}): NeedDisplayTag | null {
  const primaryReasonLabel = (args.primaryReasonLabel ?? "").trim();

  if (isNeedDisplayTag(primaryReasonLabel)) {
    return primaryReasonLabel;
  }

  const fallbackTags = Array.isArray(args.fallbackTags) ? args.fallbackTags : [];
  const tags = fallbackTags
    .filter((t): t is string => typeof t === "string")
    .map((t) => t.trim())
    .filter(isNeedDisplayTag);

  if (tags.includes("courage")) return "courage";
  if (tags.includes("money")) return "money";
  if (tags.includes("career")) return "career";
  if (tags.includes("mental")) return "mental";
  if (tags.includes("rest")) return "rest";
  if (tags.includes("love")) return "love";
  if (tags.includes("study")) return "study";

  return tags[0] ?? null;
}

function safeId(r: NonNullable<NonNullable<ConciergeResponse["data"]>["recommendations"]>[number]) {
  if (typeof r.shrine_id === "number") return `shrine_${r.shrine_id}`;
  if (r.place_id) return `place_${r.place_id}`;
  return `name_${encodeURIComponent(r.name)}`;
}

function normalizeTagList(tags: string[] | null | undefined): string[] {
  if (!Array.isArray(tags)) return [];
  return tags
    .filter((t): t is string => typeof t === "string")
    .map((t) => t.trim())
    .filter(Boolean);
}

function normalizeTrustMetadata(raw: any) {
  if (!raw || typeof raw !== "object") return null;

  const culturalStatusRaw = raw.cultural_status ?? raw.culturalStatus;
  const culturalStatus = Array.isArray(culturalStatusRaw)
    ? culturalStatusRaw.filter((v): v is string => typeof v === "string" && v.trim().length > 0).map((v) => v.trim())
    : [];

  return {
    rankClass:
      typeof raw.rank_class === "string" ? raw.rank_class : typeof raw.rankClass === "string" ? raw.rankClass : null,
    culturalStatus,
    lineage: typeof raw.lineage === "string" ? raw.lineage : null,
    originSummary:
      typeof raw.origin_summary === "string"
        ? raw.origin_summary
        : typeof raw.originSummary === "string"
          ? raw.originSummary
          : null,
  };
}

function toDisplayTag(tag: string): string {
  return labelNeedDisplayTag(tag);
}

const ACTION_SUGGESTION_V4_ACTION_TYPES = ["detail_open", "route_open", "save", "visit", "reflect", "pause"] as const;
const ACTION_SUGGESTION_V4_PROMPT_TYPES = ["before_visit", "after_visit", "decision", "emotion", "constraint"] as const;
const ACTION_SUGGESTION_V4_SOURCES = [
  "decision_context",
  "constraint_profile",
  "outcome_hint",
  "action_context",
  "reflection_question_seed",
  "fallback",
] as const;

function isActionSuggestionV4ActionType(value: unknown): value is ActionSuggestionV4ActionViewModel["actionType"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_ACTION_TYPES.includes(value as any);
}

function isActionSuggestionV4PromptType(
  value: unknown,
): value is ActionSuggestionV4ReflectionPromptViewModel["promptType"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_PROMPT_TYPES.includes(value as any);
}

function isActionSuggestionV4Source(value: unknown): value is ActionSuggestionV4SourceViewModel["source"] {
  return typeof value === "string" && ACTION_SUGGESTION_V4_SOURCES.includes(value as any);
}

function asTrimmedString(val: any): string | null {
  return typeof val === "string" && val.trim() ? val.trim() : null;
}

function normalizeActionSuggestionV4Action(raw: any): ActionSuggestionV4ActionViewModel | null {
  if (!raw || typeof raw !== "object") return null;

  const label = asTrimmedString(raw.label);
  const description = asTrimmedString(raw.description);
  const actionTypeRaw = raw.action_type ?? raw.actionType;
  const confidenceRaw = typeof raw.confidence === "number" ? raw.confidence : Number(raw.confidence);

  if (!label || !description || !isActionSuggestionV4ActionType(actionTypeRaw) || !Number.isFinite(confidenceRaw)) {
    return null;
  }

  return {
    label,
    description,
    actionType: actionTypeRaw,
    confidence: Math.max(0, Math.min(1, confidenceRaw)),
  };
}

function normalizeActionSuggestionV4ReflectionPrompt(raw: any): ActionSuggestionV4ReflectionPromptViewModel | null {
  if (!raw || typeof raw !== "object") return null;

  const question = asTrimmedString(raw.question);
  const promptTypeRaw = raw.prompt_type ?? raw.promptType;
  const sourceSeed = asTrimmedString(raw.source_seed ?? raw.sourceSeed);

  if (!question || !isActionSuggestionV4PromptType(promptTypeRaw) || !sourceSeed) {
    return null;
  }

  return {
    question,
    promptType: promptTypeRaw,
    sourceSeed,
  };
}

function normalizeActionSuggestionV4Source(raw: any): ActionSuggestionV4SourceViewModel | null {
  if (!raw || typeof raw !== "object") return null;

  const sourceRaw = raw.source;
  const reason = asTrimmedString(raw.reason);

  if (!isActionSuggestionV4Source(sourceRaw) || !reason) {
    return null;
  }

  return {
    source: sourceRaw,
    reason,
  };
}

function normalizeActionSuggestionV4Preview(raw: any): ActionSuggestionV4PreviewViewModel | null {
  if (!raw || typeof raw !== "object") return null;

  const primaryAction = normalizeActionSuggestionV4Action(raw.primary_action ?? raw.primaryAction);
  const secondaryAction = normalizeActionSuggestionV4Action(raw.secondary_action ?? raw.secondaryAction);
  const reflectionPrompt = normalizeActionSuggestionV4ReflectionPrompt(raw.reflection_prompt ?? raw.reflectionPrompt);
  const actionSource = normalizeActionSuggestionV4Source(raw.action_source ?? raw.actionSource);
  const sourceKeysRaw = raw.source_keys ?? raw.sourceKeys;
  const sourceKeys = Array.isArray(sourceKeysRaw)
    ? sourceKeysRaw.map((item) => asTrimmedString(item)).filter((item): item is string => Boolean(item))
    : [];

  if (!primaryAction || !secondaryAction || !reflectionPrompt || !actionSource) {
    return null;
  }

  return {
    primaryAction,
    secondaryAction,
    reflectionPrompt,
    actionSource,
    preview: raw.preview === true,
    version: "v4",
    sourceKeys,
  };
}

export function conciergeToShrineListItems(resp: ConciergeResponse): ConciergeResultItem[] {
  if (!resp?.ok) {
    return [];
  }

  const recs = resp.data?.recommendations ?? [];
  const threadId =
    typeof resp.thread_id === "string" && resp.thread_id.trim()
      ? resp.thread_id.trim()
      : typeof resp.data?.thread_id === "string" && resp.data.thread_id.trim()
        ? resp.data.thread_id.trim()
        : null;

  const items = recs
    .filter((r): r is typeof r & { shrine_id: number } => typeof r.shrine_id === "number")
    .map((r, index) => {
      const id = safeId(r);
      const name = r.display_name ?? r.name;
      const trustMetadata = normalizeTrustMetadata(r.trust_metadata ?? r.trustMetadata ?? null);
      const actionSuggestions = Array.isArray(r._explanation_payload?.action_suggestions)
        ? r._explanation_payload.action_suggestions
            .map((item: any) => ({
              id: String(item.id ?? ""),
              historyTheme: String(item.history_theme ?? ""),
              title: String(item.title ?? ""),
              description: String(item.description ?? ""),
              category: String(item.category ?? ""),
              timing: String(item.timing ?? ""),
              difficulty: String(item.difficulty ?? ""),
              timeEstimate: String(item.time_estimate ?? ""),
              measurementKey: String(item.measurement_key ?? ""),
            }))
            .filter((item: any) => item.id && item.title)
        : [];

      const actionSuggestionV4Preview = normalizeActionSuggestionV4Preview(
        r.action_suggestion_v4_preview ?? r.actionSuggestionV4Preview,
      );

      const matchedTags = normalizeTagList(r.breakdown?.matched_need_tags);
      const rawTags = matchedTags.length ? matchedTags : normalizeTagList(resp.data?._need?.tags);
      const tags = rawTags.map(toDisplayTag).slice(0, 3);

      const reasonVm = buildRecommendationReasonViewModel({
        index,
        needTags: rawTags,
        rec: {
          display_name: name,
          name,
          reason: r.reason ?? null,
          breakdown: r.breakdown ?? null,
          distance_m: r.distance_m ?? null,
          popular_score: r.popular_score ?? null,
          astro_elements: r.astro_elements ?? null,
          astro_priority: r.astro_priority ?? null,
          fallback_mode: r.fallback_mode ?? null,
          explanation: r.explanation ?? null,
          reason_facts: r.reason_facts ?? null,
        },
      });

      const explanationSummary = r.explanation?.summary?.trim() || reasonVm.list.summary;
      const rawReason =
        r.recommendation_reason_v4?.trim() ||
        r._explanation_payload?.original_reason?.trim() ||
        r.reason?.trim() ||
        explanationSummary ||
        null;

      const primaryReasonLabel = r._explanation_payload?.primary_reason?.label?.trim() || null;
      const primaryTag = resolveListPrimaryTag({
        primaryReasonLabel,
        fallbackTags: rawTags,
      });
      const primaryMeaning =
        buildNeedPrimaryShortCopy({
          primaryTag,
          shrineTone: getShrineTone(name),
          fallbackText: rawReason,
        }) ?? reasonVm.list.primaryPhrase;

      const deepReason = {
        interpretation: reasonVm.detail.consultationSummary,
        shrineMeaning: reasonVm.detail.shrineMeaning,
        action: reasonVm.detail.actionMeaning ?? null,
        short: reasonVm.list.primaryPhrase,
        heroMeaningCopy: reasonVm.detail.heroMeaningCopy,
      };

      const detailHref = buildShrineHref(r.shrine_id, {
        query: threadId
          ? {
              ctx: "concierge",
              tid: threadId,
            }
          : {
              ctx: "concierge",
            },
      });

      return {
        id,
        tid: threadId,
        detailHref,
        trustMetadata,
        actionSuggestions,
        actionSuggestionV4Preview,
        cardProps: {
          shrineId: r.shrine_id,
          title: name,
          address: r.address ?? r.location ?? undefined,
          imageUrl: null,
          explanationSummary,
          explanationPrimaryReason: primaryMeaning,
          breakdown: r.breakdown ?? null,
          badgesOverride: tags,
        },
        deepReason,
      };
    });

  return items;
}
