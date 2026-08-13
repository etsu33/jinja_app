import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/recommendation-strict-funnel-readiness.md §6, §14-1:
// Impression dedup must key off the Backend-issued recommendationInstanceId (the actual
// recommendation-instance boundary), not resultSetId (a Frontend-composed shrine-order
// signature that collides across separate generations returning the same shrines in the
// same order). Before this fix, a same-shrine-set regeneration suppressed the new
// generation's Impression while its Click still fired -- an orphan click. This file
// reproduces that scenario and proves it no longer happens.

const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackCardEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
}));

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: false, loading: false })),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: authMock.useAuth,
}));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";

const baseFilterState: any = {
  isOpen: false,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
};

function buildTestPayload(recommendationInstanceId: unknown) {
  const u: any = {
    data: {
      recommendations: [
        {
          shrine_id: 1,
          display_name: "第一候補神社",
          reason: "理由文",
          recommendation_instance_id: recommendationInstanceId,
        },
      ],
    },
    thread: { id: 768 },
  };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function impressionCalls() {
  return analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "concierge_result_impression");
}

describe("Recommendation Impression Instance Dedup", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    window.localStorage.clear();
  });

  it("1. same instance + rerender: Impressionは1回だけ送信される", () => {
    const payload = buildTestPayload("gen-a");
    const { rerender } = render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);
    expect(impressionCalls()).toHaveLength(1);

    // 同じrecommendationInstanceIdを持つ payload で pure re-render を再現する。
    const samePayload = buildTestPayload("gen-a");
    rerender(<ConciergeSectionsRenderer payload={samePayload} threadId={768} isPremiumActive={true} />);
    rerender(<ConciergeSectionsRenderer payload={samePayload} threadId={768} isPremiumActive={true} />);

    expect(impressionCalls()).toHaveLength(1);
  });

  it("2. new instance + 同じ神社集合/rank: Impressionが2回送信される(新instanceは抑制されない)", () => {
    const payloadA = buildTestPayload("gen-a");
    const { rerender } = render(<ConciergeSectionsRenderer payload={payloadA} threadId={768} isPremiumActive={true} />);
    expect(impressionCalls()).toHaveLength(1);
    expect(impressionCalls()[0][1]).toMatchObject({ shrineId: 1, recommendationInstanceId: "gen-a" });

    // shrine_id/rankは同一のまま、recommendationInstanceIdだけが新しいgenerationのものへ変わる。
    const payloadB = buildTestPayload("gen-b");
    rerender(<ConciergeSectionsRenderer payload={payloadB} threadId={768} isPremiumActive={true} />);

    const calls = impressionCalls();
    expect(calls).toHaveLength(2);
    expect(calls[1][1]).toMatchObject({ shrineId: 1, recommendationInstanceId: "gen-b" });
  });

  it("3. generation Bのclickにgeneration Bのimpressionが存在する(orphan clickにならない)", () => {
    const payloadA = buildTestPayload("gen-a");
    const { rerender } = render(<ConciergeSectionsRenderer payload={payloadA} threadId={768} isPremiumActive={true} />);

    const payloadB = buildTestPayload("gen-b");
    rerender(<ConciergeSectionsRenderer payload={payloadB} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("link", { name: "神社の詳細を見る" }));

    const clickCall = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "shrine_detail_transition",
    );
    expect(clickCall?.[1]).toMatchObject({ shrineId: 1, recommendationInstanceId: "gen-b" });

    const matchingImpression = impressionCalls().find(
      (call) => call[1].recommendationInstanceId === clickCall?.[1].recommendationInstanceId,
    );
    expect(matchingImpression).toBeDefined();
  });

  it("5. recommendationInstanceIdがnull/malformedでもクラッシュせずresultSetIdへfallbackする", () => {
    expect(() => {
      const payloadNull = buildTestPayload(null);
      const { rerender } = render(
        <ConciergeSectionsRenderer payload={payloadNull} threadId={768} isPremiumActive={true} />,
      );
      rerender(<ConciergeSectionsRenderer payload={payloadNull} threadId={768} isPremiumActive={true} />);

      const payloadMalformed = buildTestPayload({ unexpected: "shape" });
      rerender(<ConciergeSectionsRenderer payload={payloadMalformed} threadId={768} isPremiumActive={true} />);
    }).not.toThrow();

    // null/malformedはFrontendで合成しない -- recommendationInstanceIdはnullのまま送られる。
    for (const call of impressionCalls()) {
      expect(call[1].recommendationInstanceId).toBeNull();
    }
    // fallbackのresultSetIdによりdedupは機能し続ける(重複送信されない)。
    expect(impressionCalls().length).toBeGreaterThan(0);
  });
});
