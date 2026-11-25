import { beforeEach, describe, expect, it } from "vitest";

import {
  HOME_ORIGIN_HANDOFF_KEY,
  consumeHomeOriginHandoff,
  saveHomeOriginHandoff,
} from "../homeOriginHandoff";
import type { UserOrigin } from "../../../../../../packages/shared/userOrigin";

const shinjuku: UserOrigin = {
  latitude: 35.6896,
  longitude: 139.7006,
  source: "station",
  displayName: "新宿駅",
  accuracy: "precise",
};

beforeEach(() => {
  sessionStorage.clear();
});

describe("homeOriginHandoff", () => {
  it("保存した出発地を1回だけ受け取れる（受け取ったら消える）", () => {
    saveHomeOriginHandoff(shinjuku, 1_000);
    expect(consumeHomeOriginHandoff(2_000)).toEqual(shinjuku);
    expect(sessionStorage.getItem(HOME_ORIGIN_HANDOFF_KEY)).toBeNull();
    expect(consumeHomeOriginHandoff(3_000)).toBeNull();
  });

  it("null を保存すると前の出発地を消す", () => {
    saveHomeOriginHandoff(shinjuku, 1_000);
    saveHomeOriginHandoff(null, 2_000);
    expect(consumeHomeOriginHandoff(3_000)).toBeNull();
  });

  it("10分より古い出発地は使わない（それでも消す）", () => {
    saveHomeOriginHandoff(shinjuku, 0);
    expect(consumeHomeOriginHandoff(10 * 60 * 1000 + 1)).toBeNull();
    expect(sessionStorage.getItem(HOME_ORIGIN_HANDOFF_KEY)).toBeNull();
  });

  it("壊れた値・範囲外の座標は使わない", () => {
    sessionStorage.setItem(HOME_ORIGIN_HANDOFF_KEY, "{not json");
    expect(consumeHomeOriginHandoff()).toBeNull();

    sessionStorage.setItem(
      HOME_ORIGIN_HANDOFF_KEY,
      JSON.stringify({ origin: { ...shinjuku, latitude: 200 }, savedAt: Date.now() }),
    );
    expect(consumeHomeOriginHandoff()).toBeNull();

    sessionStorage.setItem(
      HOME_ORIGIN_HANDOFF_KEY,
      JSON.stringify({ origin: { ...shinjuku, source: "gps" }, savedAt: Date.now() }),
    );
    expect(consumeHomeOriginHandoff()).toBeNull();
  });
});
