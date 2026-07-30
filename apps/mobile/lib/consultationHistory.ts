import { getAuth } from "./http";

// Backend契約(GET /concierge-threads/, ConciergeThreadListView)は
// id/title/last_message/last_message_at/message_countのみを返す。
// created_at/updated_atは存在しないため型に含めない。
export type ConciergeThreadListItem = {
  id: number;
  title: string;
  last_message: string;
  last_message_at: string | null;
  message_count: number;
};

// Backend契約(GET /concierge-threads/{id}/, ConciergeThreadDetailView)は
// id/title/last_message/last_message_at/message_count/messages/recommendations/recommendations_v2を
// トップレベルに持つフラットな構造で返す(`thread`という入れ子キーは存在しない)。
export type ConciergeMessage = {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string | null;
};

// 推薦itemはConcierge Chat応答と同じ生のsnake_case構造(Snapshotとして保存されたもの)。
// Fact/Interpretation/Action等の構造化fieldは既存の共通ロジック(recommendationReasonV4.ts)で正規化する。
export type ConciergeRecommendation = {
  id?: number | string | null;
  shrine_id?: number | string | null;
  name?: string | null;
  display_name?: string | null;
  address?: string | null;
  location?: string | null;
  formatted_address?: string | null;
  action_state?: "reflected" | "visited" | "saved" | "detail_viewed" | "route_opened" | "none" | null;
  recommendation_reason_v4?: string | null;
  reason_facts?: unknown;
  recommendation_reason_detail?: unknown;
  recommendation_reason_v4_detail?: unknown;
  action_suggestion_v4_preview?: unknown;
};

export type ConciergeThreadDetail = {
  id: number;
  title: string;
  last_message: string;
  last_message_at: string | null;
  message_count: number;
  messages: ConciergeMessage[];
  recommendations?: ConciergeRecommendation[] | null;
  recommendations_v2?: ConciergeRecommendation[] | null;
};

type PaginatedResponse<T> = {
  results: T[];
};

// 401(UnauthenticatedError)・404等を握りつぶさない生の取得関数。
// History画面はこちらを使い、未ログインと0件を呼び出し側で区別すること。
export async function fetchConciergeThreadsRaw(): Promise<ConciergeThreadListItem[]> {
  const data = await getAuth<ConciergeThreadListItem[] | PaginatedResponse<ConciergeThreadListItem>>(
    "/concierge-threads/",
  );

  return Array.isArray(data) ? data : (data.results ?? []);
}

// 既存呼び出し元向けの後方互換ラッパー。401/403/network error等はすべて空配列へfallbackする
// (「0件」と「未認証」を区別できない既知の制約。区別が必要な場合はfetchConciergeThreadsRawを使うこと)。
export async function listConciergeThreads(): Promise<ConciergeThreadListItem[]> {
  try {
    return await fetchConciergeThreadsRaw();
  } catch (error) {
    if (__DEV__) {
      console.warn("[listConciergeThreads] failed", error);
    }
    return [];
  }
}

// 401(UnauthenticatedError)・404(HttpError)を握りつぶさない。呼び出し側で状態を区別すること。
export async function getConciergeThread(tid: string): Promise<ConciergeThreadDetail> {
  return getAuth<ConciergeThreadDetail>(`/concierge-threads/${encodeURIComponent(tid)}/`);
}
