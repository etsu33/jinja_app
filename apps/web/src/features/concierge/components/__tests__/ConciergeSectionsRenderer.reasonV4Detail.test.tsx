import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
  const u: any = {
    data: { recommendations },
    thread: { id: 900 },
  };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function detailFixture(overrides: Partial<{ fact: any; interpretation: any; action: any; reason_text: string }> = {}) {
  return {
    version: "v4",
    reason_text: overrides.reason_text ?? "根津神社は仕事運に関わる神社です。",
    fact: {
      label: "根津神社",
      name: "根津神社",
      deity: null,
      shrine_history: null,
      place_context: null,
      history_theme: "再出発",
      goriyaku: "仕事運",
      visit_style_tags: [],
      evidence: ["history_theme:再出発"],
      ...(overrides.fact ?? {}),
    },
    interpretation: {
      theme: "再出発",
      text: "相談内容から、今扱いたいテーマを読み取っています。",
      ...(overrides.interpretation ?? {}),
    },
    action: {
      text: "参拝前に、問いを一つに絞ることを決めておきます。",
      source: "meaning_translation.action_context",
      ...(overrides.action ?? {}),
    },
  };
}

const heroRecWithDetail = {
  shrine_id: 1,
  display_name: "根津神社",
  reason: "旧型の理由文",
  address: "東京都文京区1-1-1",
  recommendation_reason_v4: "根津神社は仕事運に関わる神社です。",
  recommendation_reason_v4_detail: detailFixture(),
};

describe("ConciergeSectionsRenderer - Reason V4構造化表示", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    window.localStorage.clear();
  });

  it("Heroでfact/interpretation/actionの3セクションが表示される", () => {
    const payload = buildTestPayload([heroRecWithDetail]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(screen.getByTestId("recommendation-reason-v4-fact")).toHaveTextContent("仕事運");
    expect(screen.getByTestId("recommendation-reason-v4-interpretation")).toHaveTextContent(
      "相談内容から、今扱いたいテーマを読み取っています。",
    );
    expect(screen.getByTestId("recommendation-reason-v4-action")).toHaveTextContent(
      "参拝前に、問いを一つに絞ることを決めておきます。",
    );
  });

  it("action.sourceは表示されない", () => {
    const payload = buildTestPayload([heroRecWithDetail]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(screen.queryByText("meaning_translation.action_context")).not.toBeInTheDocument();
  });

  it("構造化セクションが表示できる場合、reason_textと同内容を重複表示しない", () => {
    const payload = buildTestPayload([heroRecWithDetail]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(screen.queryByTestId("recommendation-standard-reason")).not.toBeInTheDocument();
    expect(screen.queryByText("根津神社は仕事運に関わる神社です。")).not.toBeInTheDocument();
  });

  it("構造化fieldがすべて空の場合、reason_textへfallbackする", () => {
    const rec = {
      ...heroRecWithDetail,
      recommendation_reason_v4_detail: detailFixture({
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
        reason_text: "reason_textのfallback文言",
      }),
    };
    const payload = buildTestPayload([rec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(screen.queryByTestId("recommendation-reason-v4-fact")).not.toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-reason-v4-interpretation")).not.toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-reason-v4-action")).not.toBeInTheDocument();
    expect(screen.getByTestId("recommendation-standard-reason")).toHaveTextContent("reason_textのfallback文言");
  });

  it("recommendation_reason_v4_detailが無くてもクラッシュせず表示される", () => {
    const rec = {
      shrine_id: 2,
      display_name: "小網神社",
      reason: "旧型の理由文のみの候補",
    };
    const payload = buildTestPayload([rec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(screen.getByText("小網神社")).toBeInTheDocument();
    expect(screen.getByTestId("recommendation-standard-reason")).toHaveTextContent("旧型の理由文のみの候補");
    expect(screen.queryByTestId("recommendation-reason-v4-fact")).not.toBeInTheDocument();
  });

  it("Heroのcard_view analyticsイベントの内容は変化しない", () => {
    const payload = buildTestPayload([heroRecWithDetail]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={true} />);

    expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        event: "card_view",
        cardId: "shrine_hero",
        source: "concierge_result",
        shrineId: 1,
        recommendationRank: 1,
      }),
    );
  });
});
