// apps/web/src/lib/api/concierge.ts
import axios from "axios";
import api from "./client";
import { apiPost } from "./http";

export type {
  ConciergeThread,
  ConciergeMessage,
  ConciergeRecommendation,
  ConciergeChatRequest,
  ConciergeChatData,
  ConciergeChatResponse,
  ConciergeThreadDetail,
  ConciergeNeed,
  ConciergeBreakdown,
  ConciergeReasonFactAxis,
  ConciergeReasonFact,
  ConciergeReasonFacts,
  RecommendationReasonV4Detail,
  RecommendationReasonV4Fact,
  RecommendationReasonV4Interpretation,
  RecommendationReasonV4Action,
  ConsultationMeaning,
  ConsultationMeaningEvidence,
  SituationSignalType,
  DesiredOutcomeSignalType,
  ExplicitConstraintSignalType,
} from "./concierge/types";

import type {
  ConciergeThread,
  ConciergeChatRequest,
  ConciergeChatResponse,
  ConciergeThreadDetail,
} from "./concierge/types";

/* ====== チャット API ====== */

export async function postConciergeChat(body: ConciergeChatRequest): Promise<ConciergeChatResponse> {
  return apiPost<ConciergeChatResponse>("/concierge/chat/", body);
}

/* ====== スレッド API ====== */

export async function fetchThreads(): Promise<ConciergeThread[]> {
  const res = await api.get<ConciergeThread[] | { results: ConciergeThread[] }>("/concierge-threads/");
  const data = res.data as any;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;

  return [];
}

/**
 * 保存確認用の厳格版。fetchThreads() は想定外の body を [] に丸めるため、
 * 200 で HTML 等が返ると「履歴に無い」と区別できない。こちらは形式不正を throw する。
 */
export class ConciergeThreadsResponseError extends Error {
  constructor() {
    super("unexpected /concierge-threads/ response shape");
    this.name = "ConciergeThreadsResponseError";
  }
}

export async function fetchThreadsStrict(): Promise<ConciergeThread[]> {
  const res = await api.get<ConciergeThread[] | { results: ConciergeThread[] }>("/concierge-threads/");
  const data = res.data as any;

  if (Array.isArray(data)) return data;
  if (data && typeof data === "object" && Array.isArray(data.results)) return data.results;

  throw new ConciergeThreadsResponseError();
}

export async function getConciergeThread(tid: string): Promise<ConciergeThreadDetail | null> {
  try {
    const res = await api.get<ConciergeThreadDetail>(`/concierge-threads/${encodeURIComponent(tid)}/`);
    return res.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const status = err.response?.status;
      if (status === 401 || status === 403 || status === 404) {
        return null;
      }
    }
    throw err;
  }
}

export async function fetchThreadDetail(threadId: string): Promise<ConciergeThreadDetail | null> {
  return getConciergeThread(threadId);
}
