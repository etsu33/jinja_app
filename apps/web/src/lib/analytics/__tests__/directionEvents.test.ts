import { beforeEach, describe, expect, it, vi } from "vitest";

const { track } = vi.hoisted(() => ({ track: vi.fn() }));
vi.mock("../track", () => ({ track }));

import { DIRECTION_EVENT_NAMES } from "../../../../../../packages/shared/directionAnalytics";
import { trackWebDirection } from "../directionEvents";

describe("direction analytics", () => {
  beforeEach(() => track.mockClear());

  it("Webとモバイルで共有するイベント名をすべて受け付ける", () => {
    for (const name of DIRECTION_EVENT_NAMES) trackWebDirection(name);
    expect(track.mock.calls.map(([name]) => name)).toEqual(DIRECTION_EVENT_NAMES);
  });

  it("イベント別allowlist以外の位置情報・個人情報を送らない", () => {
    trackWebDirection("direction_origin_result", {
      origin_type: "prefecture",
      result: "selected",
      latitude: 35.6812,
      longitude: 139.7671,
      address: "東京都千代田区",
      station_name: "東京駅",
      prefecture_name: "東京都",
      birthdate: "1990-01-01",
      consultation: "相談文",
      query: "検索語",
    } as never);

    expect(track).toHaveBeenCalledWith("direction_origin_result", {
      platform: "web",
      origin_type: "prefecture",
      result: "selected",
    });
  });

  it("イベントと無関係な共通属性も除外する", () => {
    trackWebDirection("direction_visit_date_set", {
      has_visit_date: true,
      recommendation_rank: 1,
    } as never);
    expect(track).toHaveBeenCalledWith("direction_visit_date_set", { platform: "web" });
  });

  it("経路クリックは候補位置と一致状態だけを許可し、候補情報とURLを除外する", () => {
    trackWebDirection("direction_match_route_clicked", {
      matched: false,
      candidate_position: "other",
      shrine_name: "テスト神社",
      shrine_address: "東京都千代田区",
      route_url: "https://www.google.com/maps/dir/?destination=35,139",
      place_id: "secret-place-id",
      latitude: 35,
      longitude: 139,
    } as never);
    expect(track).toHaveBeenCalledWith("direction_match_route_clicked", {
      platform: "web",
      matched: false,
      candidate_position: "other",
    });
  });
});
