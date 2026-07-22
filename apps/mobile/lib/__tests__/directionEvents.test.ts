import { beforeEach, describe, expect, it, vi } from "vitest";

const { track } = vi.hoisted(() => ({ track: vi.fn() }));
vi.mock("../analytics", () => ({ track }));

import { DIRECTION_EVENT_NAMES } from "../../../../packages/shared/directionAnalytics";
import { trackMobileDirection } from "../directionEvents";

describe("direction analytics", () => {
  beforeEach(() => track.mockClear());

  it("Webとモバイルで共有するイベント名をすべて受け付ける", () => {
    for (const name of DIRECTION_EVENT_NAMES) trackMobileDirection(name);
    expect(track.mock.calls.map(([name]) => name)).toEqual(DIRECTION_EVENT_NAMES);
  });

  it("イベント別allowlist以外の位置情報・個人情報を送らない", () => {
    trackMobileDirection("direction_condition_submitted", {
      has_visit_date: true,
      has_origin: true,
      latitude: 35.6812,
      longitude: 139.7671,
      address: "東京都千代田区",
      station_name: "東京駅",
      prefecture_name: "東京都",
      birthdate: "1990-01-01",
      consultation: "相談文",
      query: "検索語",
    } as never);

    expect(track).toHaveBeenCalledWith("direction_condition_submitted", {
      platform: "mobile",
      has_visit_date: true,
      has_origin: true,
    });
  });

  it("不正なenum値と順位を除外する", () => {
    trackMobileDirection("direction_match_impression", {
      matched: true,
      recommendation_rank: -1,
      origin_type: "Tokyo",
    } as never);
    expect(track).toHaveBeenCalledWith("direction_match_impression", {
      platform: "mobile",
      matched: true,
    });
  });

  it("Webと共通の経路候補位置を同じ分類値で扱う", () => {
    trackMobileDirection("direction_match_route_clicked", {
      matched: true,
      candidate_position: "hero",
      route_url: "https://www.google.com/maps/dir/?destination=35,139",
      shrine_name: "テスト神社",
    } as never);
    expect(track).toHaveBeenCalledWith("direction_match_route_clicked", {
      platform: "mobile",
      matched: true,
      candidate_position: "hero",
    });
  });

  it("分析送信例外を利用操作へ伝播させない", () => {
    track.mockImplementationOnce(() => { throw new Error("analytics unavailable"); });
    expect(() => trackMobileDirection("direction_visit_date_set")).not.toThrow();
  });
});
