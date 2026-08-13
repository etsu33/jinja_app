import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/recommendation-instance-identity-propagation.md:
// impression -> click must carry the identical Backend-issued recommendationInstanceId
// for the same recommendation, and it must stay stable across re-normalization
// (simulating a re-render).

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

function buildTestPayload(recommendations: any[]) {
  const u: any = { data: { recommendations }, thread: { id: 768 } };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

describe("Recommendation Instance Identity: impression -> click", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    window.localStorage.clear();
  });

  it("concierge_result_impressionとshrine_detail_transitionが同じrecommendationInstanceIdを送る", () => {
    const heroRec = {
      shrine_id: 1,
      display_name: "第一候補神社",
      reason: "第一候補の理由文です。",
      recommendation_instance_id: "a1b2c3d4",
    };
    const payload = buildTestPayload([heroRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    const impressionCall = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "concierge_result_impression",
    );
    expect(impressionCall?.[1]).toMatchObject({ shrineId: 1, recommendationInstanceId: "a1b2c3d4" });

    fireEvent.click(screen.getByRole("link", { name: "神社の詳細を見る" }));

    const clickCall = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "shrine_detail_transition",
    );
    expect(clickCall?.[1]).toMatchObject({ shrineId: 1, recommendationInstanceId: "a1b2c3d4" });
    expect(clickCall?.[1].recommendationInstanceId).toBe(impressionCall?.[1].recommendationInstanceId);
  });

  it("recommendation_instance_idが無いDirectアクセス相当の候補ではidentityを合成しない", () => {
    const heroRec = { shrine_id: 2, display_name: "識別子なし神社", reason: "理由" };
    const payload = buildTestPayload([heroRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    const impressionCall = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "concierge_result_impression",
    );
    expect(impressionCall?.[1].recommendationInstanceId).toBeNull();
  });

  it("再normalizeしてもrecommendationInstanceIdは不変(rerender相当)", () => {
    const heroRec = {
      shrine_id: 5,
      display_name: "再検証神社",
      reason: "理由",
      recommendation_instance_id: "stable-9f8e",
    };
    const payload = buildTestPayload([heroRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);
    const first = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "concierge_result_impression",
    )?.[1].recommendationInstanceId;

    const rebuiltPayload = buildTestPayload([heroRec]);
    const rebuiltHero = (rebuiltPayload.sections.find((s: any) => s.type === "recommendations") as any).items[0];

    expect(rebuiltHero.recommendationInstanceId).toBe(first);
    expect(first).toBe("stable-9f8e");
  });
});
