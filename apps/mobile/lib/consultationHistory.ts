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

type PaginatedResponse<T> = {
  results: T[];
};

export async function listConciergeThreads(): Promise<ConciergeThreadListItem[]> {
  try {
    const data = await getAuth<ConciergeThreadListItem[] | PaginatedResponse<ConciergeThreadListItem>>(
      "/concierge-threads/",
    );

    return Array.isArray(data) ? data : (data.results ?? []);
  } catch (error) {
    if (__DEV__) {
      console.warn("[listConciergeThreads] failed", error);
    }
    return [];
  }
}
