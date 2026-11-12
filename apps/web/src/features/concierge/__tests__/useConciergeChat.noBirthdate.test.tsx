// コンシェルジュでは生年月日を使わない（生年月日との相性はコンパスの役割）。
// 相談の送信に生年月日・profile_context を入れず、モードは常に need。送信で生年月日を保存しない。
import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  postConciergeChat: vi.fn(),
  persistBirthday: vi.fn(),
  trackRecommendationQuality: vi.fn(),
}));

vi.mock("@/lib/api/concierge", () => ({
  fetchThreads: vi.fn(),
  fetchThreadDetail: vi.fn(),
  postConciergeChat: mocks.postConciergeChat,
}));

vi.mock("@/lib/api/concierge/normalize", () => ({
  normalizeRecommendations: (value: unknown) => (Array.isArray(value) ? value : []),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackRecommendationQuality: mocks.trackRecommendationQuality,
}));

vi.mock("@/lib/profile/useSharedBirthdayPersistence", () => ({
  useSharedBirthdayPersistence: () => ({
    savedBirthday: null,
    isLoggedIn: true,
    persistBirthday: mocks.persistBirthday,
  }),
}));

import { useConciergeChat } from "@/features/concierge/hooks";

function successPayload() {
  return {
    ok: true,
    plan: "free",
    remaining: 2,
    limit: 3,
    limitReached: false,
    thread: { id: 10, title: "相談" },
    data: { recommendations: [] },
  };
}

describe("useConciergeChat は生年月日を送らない・保存しない", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("入力・filters・profile_context の生年月日と compat を外して送り、生年月日を保存しない", async () => {
    mocks.postConciergeChat.mockResolvedValue(successPayload());
    const { result } = renderHook(() => useConciergeChat(null, { filters: { birthdate: "1984-05-15" } }));

    await act(async () => {
      await result.current.send({
        version: 1,
        mode: "compat",
        query: "仕事について整理したいです",
        birthdate: "1990-01-01",
        filters: { birthdate: "1990-01-01" },
        profile_context: { user_profile: { birthday: "1990-01-01" }, derived_profile: { gogyo: "水" } },
      } as any);
    });

    expect(mocks.postConciergeChat).toHaveBeenCalledTimes(1);
    const sent = mocks.postConciergeChat.mock.calls[0][0];
    expect(sent.mode).toBe("need");
    expect(sent).not.toHaveProperty("birthdate");
    expect(sent).not.toHaveProperty("profile_context");
    expect(sent.filters ?? {}).not.toHaveProperty("birthdate");
    expect(JSON.stringify(sent)).not.toContain("1990");
    expect(JSON.stringify(sent)).not.toContain("1984");
    expect(mocks.persistBirthday).not.toHaveBeenCalled();
  });

  it("日付だけの相談文は送らない（生年月日として扱わない）", async () => {
    mocks.postConciergeChat.mockResolvedValue(successPayload());
    const { result } = renderHook(() => useConciergeChat(null));

    await act(async () => {
      await result.current.send({ version: 1, mode: "compat", query: "1990-01-01" } as any);
    });

    const sent = mocks.postConciergeChat.mock.calls[0]?.[0];
    if (sent) {
      expect(sent).not.toHaveProperty("birthdate");
      expect(sent.mode).toBe("need");
    }
    expect(mocks.persistBirthday).not.toHaveBeenCalled();
  });
});
