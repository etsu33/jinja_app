// apps/web/src/lib/analytics/consultationHistoryEvents.ts
//
// 相談履歴導線(MyPage入口・一覧表示・一覧→詳細遷移・詳細表示・詳細→神社詳細遷移)の
// Analytics契約を集約するhelper。Event名・Payload・発火条件の根拠は
// docs/analytics/consultation-history-events.md を正本とする。
//
// track()自体がセッションID付与・開発ログ・送信失敗の握り潰しを担うため、
// ここではEvent名とPayloadの組み立てのみに責務を絞る(画面からPostHog SDKを直接呼ばない)。
import { track } from "@/lib/analytics/track";

const PLATFORM = "web";
const SOURCE_MYPAGE = "mypage";
const SOURCE_LIST = "consultation_history";
const SOURCE_LIST_CARD = "consultation_history_list";
const SOURCE_DETAIL = "consultation_history_detail";

export function trackConsultationHistoryEntryClicked(): void {
  track("consultation_history_entry_clicked", {
    platform: PLATFORM,
    source: SOURCE_MYPAGE,
  });
}

export function trackConsultationHistoryListViewed(params: { historyCount: number }): void {
  track("consultation_history_list_viewed", {
    platform: PLATFORM,
    source: SOURCE_LIST,
    historyCount: params.historyCount,
  });
}

export function trackConsultationHistoryDetailOpened(params: {
  threadId: string | number;
  position: number;
}): void {
  track("consultation_history_detail_opened", {
    platform: PLATFORM,
    source: SOURCE_LIST_CARD,
    threadId: params.threadId,
    position: params.position,
  });
}

export function trackConsultationHistoryDetailViewed(params: {
  threadId: string | number;
  recommendationCount: number;
  messageCount: number;
}): void {
  track("consultation_history_detail_viewed", {
    platform: PLATFORM,
    source: SOURCE_DETAIL,
    threadId: params.threadId,
    recommendationCount: params.recommendationCount,
    messageCount: params.messageCount,
  });
}

export function trackConsultationHistoryShrineOpened(params: {
  threadId: string | number;
  shrineId: string | number;
  recommendationRank: number;
}): void {
  track("consultation_history_shrine_opened", {
    platform: PLATFORM,
    source: SOURCE_DETAIL,
    threadId: params.threadId,
    shrineId: params.shrineId,
    recommendationRank: params.recommendationRank,
  });
}
