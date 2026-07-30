// apps/mobile/lib/consultationHistoryUi.ts
//
// 相談履歴の一覧・詳細Screen(apps/mobile/app/consultation-history/)が使う表示用の純粋関数。
// vitestのtest discovery(vitest.config.ts)はlib/__tests__/配下の.test.tsのみを対象とするため、
// Screen(.tsx)側に置くとテスト対象外になってしまう。単体テスト可能にするためlib側へ切り出す。
import { isHttpError, isUnauthenticatedError } from "./http";
import type { ConciergeRecommendation, ConciergeThreadListItem } from "./consultationHistory";

// 401(UnauthenticatedError)と、それ以外(403/404/network error等)を区別する。
// 「未ログイン」と「取得失敗」を同じメッセージへ握り潰さないための分類関数。
export function classifyThreadsLoadError(error: unknown): "unauthenticated" | "error" {
  return isUnauthenticatedError(error) ? "unauthenticated" : "error";
}

// 401(UnauthenticatedError)・404(HttpError)・その他(network error等)を区別する。
// 「未ログイン」「不正または存在しないtid」「取得失敗」を同じ状態へ握り潰さないための分類関数。
export function classifyThreadDetailLoadError(error: unknown): "unauthenticated" | "not_found" | "error" {
  if (isUnauthenticatedError(error)) return "unauthenticated";
  if (isHttpError(error) && error.status === 404) return "not_found";
  return "error";
}

export function formatThreadDate(value: string | null | undefined): string {
  if (!value) return "日付未記録";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日付未記録";

  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function formatThreadDateTime(value: string | null | undefined): string {
  if (!value) return "日時未記録";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日時未記録";

  return date.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatThreadDateGroupLabel(value: string | null | undefined): string {
  if (!value) return "日付未記録";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "日付未記録";

  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });
}

export function normalizeThreadPreview(value: string | null | undefined): string {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text || "相談内容はまだ記録されていません。";
}

export type ConsultationGroup = {
  label: string;
  items: ConciergeThreadListItem[];
};

export function groupThreadsByDate(threads: ConciergeThreadListItem[]): ConsultationGroup[] {
  const groups = new Map<string, ConciergeThreadListItem[]>();

  threads.forEach((thread) => {
    const label = formatThreadDateGroupLabel(thread.last_message_at);
    const current = groups.get(label) ?? [];
    current.push(thread);
    groups.set(label, current);
  });

  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

export const ACTION_STATE_LABEL: Partial<Record<NonNullable<ConciergeRecommendation["action_state"]>, string>> = {
  saved: "気になる登録済み",
  visited: "参拝済み",
  reflected: "振り返り済み",
};

export function extractRecommendationShrineId(rec: ConciergeRecommendation): string | null {
  const raw = rec.shrine_id ?? rec.id;
  if (raw === null || raw === undefined) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? String(n) : null;
}
