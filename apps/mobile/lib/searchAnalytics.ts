// Mobile Search導線(Home入口・Search画面・一覧/人気神社/地図からの選択・詳細遷移・
// 外部経路CTA)のAnalytics契約を集約するhelper。
//
// Event名・Payloadの根拠は docs/analytics/mobile-search-events.md を正本とする。
// track()自体がnull/undefined除去・primitive型への制限・送信失敗の握り潰しを担うため、
// ここではEvent名とPayloadの型・組み立てのみに責務を絞る(UIからPostHog providerを直接呼ばない)。
import { track } from "./analytics";
import {
  recommendationAnalyticsProperties,
  type RecommendationAnalyticsProvenance,
} from "../../../packages/shared/recommendationAnalyticsProvenance";

const SOURCE_HOME = "home";
const SOURCE_SEARCH = "mobile_search";
const SOURCE_MAP = "map";
const SOURCE_SHRINE_DETAIL = "shrine_detail";

export type SearchCardPosition = "list" | "popular" | "map";

export function trackSearchEntryClick(): void {
  track("search_entry_click", { source: SOURCE_HOME, platform: "mobile" });
}

export function trackSearchScreenView(): void {
  track("search_screen_view", { source: SOURCE_SEARCH, platform: "mobile" });
}

// 神社一覧・人気の神社・地図選択カードいずれも「カードを押して神社詳細へ進む」という
// 同じ行動のため、position(list/popular/map)だけで区別しEvent名は1つに揃える。
export function trackShrineCardClick(params: { shrineId: string; position: SearchCardPosition }): void {
  track("shrine_card_click", {
    source: params.position === "map" ? SOURCE_MAP : SOURCE_SEARCH,
    shrineId: params.shrineId,
    position: params.position,
    platform: "mobile",
  });
}

// 地図上でMarker(または座標欠損リスト・Web fallback一覧)を選択した操作。
// 神社詳細への遷移ではないため、trackShrineCardClickとは別Eventとして扱う。
export function trackMapMarkerSelect(params: { shrineId: string }): void {
  track("map_marker_select", {
    source: SOURCE_MAP,
    shrineId: params.shrineId,
    position: "map",
    platform: "mobile",
  });
}

// 神社詳細画面の外部経路CTA(Googleマップ起動)。Web版のroute_openと同一Event名・
// 同一の意味で送る(source/routeTargetの値も揃える)。
export function trackRouteOpen(params: {
  shrineId: string | number;
  provenance?: RecommendationAnalyticsProvenance;
}): void {
  track("route_open", {
    source: SOURCE_SHRINE_DETAIL,
    shrineId: params.shrineId,
    routeTarget: "google_maps",
    platform: "mobile",
    ...(params.provenance ? recommendationAnalyticsProperties(params.provenance) : {}),
  });
}
