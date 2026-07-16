// Visit/Reflection Analyticsイベント契約
// apps/web/src/lib/analytics/searchEvents.ts のイベント名・フィールド名の意味に合わせる。
// packages/sharedはpnpm-workspaceからapps/mobileが除外されており(pnpm-workspace.yaml参照)、
// 型そのものをWeb/Mobileで共有する基盤がまだ無いため、契約(イベント名・フィールドの意味)のみを揃え、
// 型定義はこのファイルに個別で持つ。
import { track } from "./analytics";

const SOURCE = "shrine_detail";

export type VisitReflectionFormType = "one_line" | "mood_delta" | "theme_reflection";
export type VisitReflectionContext = "visit_done" | "mypage" | "night_reflection";

type BasePayloadParams = {
  shrineId: number | string;
  threadId?: number | string | null;
  historyTheme?: string | null;
};

function buildBasePayload({ shrineId, threadId, historyTheme }: BasePayloadParams): Record<string, unknown> {
  return {
    source: SOURCE,
    platform: "mobile",
    shrineId,
    threadId: threadId || undefined,
    historyTheme: historyTheme || undefined,
  };
}

export function trackVisitDone(params: BasePayloadParams): void {
  track("visit_done", buildBasePayload(params));
}

export type ReflectionPromptViewParams = BasePayloadParams & {
  reflectionFormType: VisitReflectionFormType;
  reflectionContext: VisitReflectionContext;
};

export function trackReflectionPromptView(params: ReflectionPromptViewParams): void {
  track("reflection_prompt_view", {
    ...buildBasePayload(params),
    reflectionFormType: params.reflectionFormType,
    reflectionContext: params.reflectionContext,
  });
}

export type ReflectionSavedParams = BasePayloadParams & {
  reflectionFormType: VisitReflectionFormType;
  reflectionContext: VisitReflectionContext;
  answerLength: number;
  moodBefore?: string | null;
  moodAfter?: string | null;
};

export function trackReflectionSaved(params: ReflectionSavedParams): void {
  track("reflection_saved", {
    ...buildBasePayload(params),
    reflectionFormType: params.reflectionFormType,
    reflectionContext: params.reflectionContext,
    answerLength: params.answerLength,
    moodBefore: params.moodBefore || undefined,
    moodAfter: params.moodAfter || undefined,
  });
}
