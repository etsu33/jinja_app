// actionSuggestionV4Preview.ts
// raw API payload (snake_case or camelCase, backend or legacy shape) -> ActionSuggestionV4PreviewViewModel
// boundary normalizer, shared by every call site that reads action_suggestion_v4_preview /
// actionSuggestionV4Preview off a recommendation so none of them can pass the raw payload
// through to a component that assumes the ViewModel's camelCase shape.
import type {
  ActionSuggestionV4ActionViewModel,
  ActionSuggestionV4PreviewViewModel,
  ActionSuggestionV4ReflectionPromptViewModel,
  ActionSuggestionV4SourceViewModel,
} from "@/viewmodels/conciergeResultItem";

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

function isActionSuggestionV4PromptType(value: unknown): value is ActionSuggestionV4ReflectionPromptViewModel["promptType"] {
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
  // Backend allows an empty description (action_suggestion_builder.py: `description: str`,
  // not required non-empty) -- only label is user-facing and required to be non-empty.
  const description = typeof raw.description === "string" ? raw.description.trim() : null;
  const actionTypeRaw = raw.action_type ?? raw.actionType;
  const confidenceRaw = typeof raw.confidence === "number" ? raw.confidence : Number(raw.confidence);

  if (!label || description === null || !isActionSuggestionV4ActionType(actionTypeRaw) || !Number.isFinite(confidenceRaw)) {
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

export function normalizeActionSuggestionV4Preview(raw: any): ActionSuggestionV4PreviewViewModel | null {
  if (!raw || typeof raw !== "object") return null;

  const primaryAction = normalizeActionSuggestionV4Action(raw.primary_action ?? raw.primaryAction);
  const secondaryAction = normalizeActionSuggestionV4Action(raw.secondary_action ?? raw.secondaryAction);
  const reflectionPrompt = normalizeActionSuggestionV4ReflectionPrompt(raw.reflection_prompt ?? raw.reflectionPrompt);
  const actionSource = normalizeActionSuggestionV4Source(raw.action_source ?? raw.actionSource);
  const sourceKeysRaw = raw.source_keys ?? raw.sourceKeys;
  const sourceKeys = Array.isArray(sourceKeysRaw)
    ? sourceKeysRaw
        .map((item) => asTrimmedString(item))
        .filter((item): item is string => Boolean(item))
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
