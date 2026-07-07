import { getAuth } from "./http";

export type ConciergeThreadListItem = {
  id: number;
  title: string;
  last_message: string;
  created_at: string;
  updated_at: string;
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
