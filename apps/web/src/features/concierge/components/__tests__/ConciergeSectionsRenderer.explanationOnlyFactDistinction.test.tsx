import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/product/recommendation-result-information-architecture.md §13, §15 PR5, Finding 9
// docs/product/recommendation-signal-authority.md §8 Knowledge Authority (A: 現状維持)
//
// deity/shrine_history(Explanation-only)とgoriyaku/history_theme(Ranking-related)を
// 視覚的に区別する。Signal Authorityの判断(どちらがPrimaryか、どのfactが採用されるか)は
// 一切再計算しない -- reasonV4FactPriority.tsの既存優先順位(deity > shrine_history >
// goriyaku > history_theme)そのままの結果を、どこに・どのトーンで表示するかだけを変える。

const analyticsMocks = vi.hoisted(() => ({ trackSearchEvent: vi.fn(), trackCardEvent: vi.fn() }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: () => ({ isLoggedIn: false, loading: false }) }));

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

function buildTestPayload(recommendations: any[], meta: any = {}) {
  const u: any = { data: { recommendations }, thread: { id: 700 }, meta };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function heroRec(overrides: Partial<any> = {}) {
  return {
    shrine_id: 1,
    display_name: "検証神社",
    reason: "旧型の理由文",
    ...overrides,
  };
}

function renderHero(rec: any, meta: any = {}) {
  const payload = buildTestPayload([rec], meta);
  render(<ConciergeSectionsRenderer payload={payload} threadId={700} isPremiumActive={true} />);
}

describe("Recommendation Explanation-only Fact Visual Distinction", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    window.localStorage.clear();
  });

  it("1. deity → Explanation-only表示(参考情報ラベル、Conclusionには入らない)", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は天照大神が祀られています。",
          fact: { label: "検証神社", name: "検証神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    const explanationOnly = screen.getByTestId("recommendation-explanation-only-fact");
    expect(explanationOnly).toHaveTextContent("参考情報");
    expect(explanationOnly).toHaveTextContent("天照大神");

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).not.toHaveTextContent("天照大神");
  });

  it("2. shrine_history → Explanation-only表示(deityが無い場合)", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は古い由緒を持ちます。",
          fact: { label: "検証神社", name: "検証神社", deity: null, shrine_history: "創建は平安時代に遡ります。", goriyaku: null, history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    const explanationOnly = screen.getByTestId("recommendation-explanation-only-fact");
    expect(explanationOnly).toHaveTextContent("参考情報");
    expect(explanationOnly).toHaveTextContent("創建は平安時代に遡ります。");

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).not.toHaveTextContent("創建は平安時代に遡ります。");
  });

  it("3. goriyaku → 通常のsupporting factとしてConclusionへ含まれる(Explanation-only扱いにしない)", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は仕事運のご利益があります。",
          fact: { label: "検証神社", name: "検証神社", deity: null, shrine_history: null, goriyaku: "仕事運", history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).toHaveTextContent("仕事運");

    expect(screen.queryByTestId("recommendation-explanation-only-fact")).not.toBeInTheDocument();
  });

  it("4. history_theme → 通常のsupporting factとしてConclusionへ含まれる(Explanation-only扱いにしない)", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は再出発を象徴します。",
          fact: { label: "検証神社", name: "検証神社", deity: null, shrine_history: null, goriyaku: null, history_theme: "再出発" },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).toHaveTextContent("再出発");

    expect(screen.queryByTestId("recommendation-explanation-only-fact")).not.toBeInTheDocument();
  });

  it("5. fallback + deity → deityがPrimary理由化せず、Conclusionはlegacy reasonへfallbackする", () => {
    renderHero(
      heroRec({
        reason: "旧型の理由文",
        recommendation_reason_v4_detail: {
          version: "v4",
          // reason_text自体はBackend確定済みのlegacy narrativeであり、deityの単語を含んで
          // いなくてもよいことを明示するため、ここではdeityと無関係な文言にする(§10
          // Explanation Contract上、reason_text自体がdeityへ言及すること自体は禁止されて
          // いないが、この分岐が実際に検証したいのは「構造化fact由来のdeityテキストが
          // Conclusionの内容として使われないこと」なので、混同を避ける)。
          reason_text: "近くの神社として候補に入っています。",
          fact: { label: "検証神社", name: "検証神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
          // interpretation/actionともに空 -- 構造化されたRecommendation理由が存在しない
          // (deity単独ではhasStructuredを成立させない、Fallback Contract)。
          interpretation: { text: "" },
          action: { text: "" },
        },
      }),
      { resultState: { fallback_mode: "nearby_unfiltered" } },
    );

    const conclusion = screen.getByTestId("recommendation-conclusion");
    // "神様が◯◯だから推薦した"と読める形で、構造化fact由来のdeityがConclusionへ現れてはならない。
    expect(conclusion).not.toHaveTextContent("天照大神");
    // legacy reason_text(Backend確定済みのfallback文言)がそのまま使われる。
    expect(conclusion).toHaveTextContent("近くの神社として候補に入っています。");

    // deity自体は「参考情報」として引き続き提示される(消えない、Primary化もしない)。
    const explanationOnly = screen.getByTestId("recommendation-explanation-only-fact");
    expect(explanationOnly).toHaveTextContent("天照大神");
  });

  it("6. Knowledgeなし(deity/shrine_historyともに無い) → 補助UIを一切表示しない", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は仕事運のご利益があります。",
          fact: { label: "検証神社", name: "検証神社", deity: null, shrine_history: null, goriyaku: null, history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    expect(screen.queryByTestId("recommendation-explanation-only-fact")).not.toBeInTheDocument();
    expect(screen.queryByText("参考情報")).not.toBeInTheDocument();
  });

  it("7. legacy path(reason_factsのみ、Reason V4 detailなし)でも非回帰でクラッシュせず表示される", () => {
    renderHero(
      heroRec({
        reason_facts: [{ type: "need_tag", label: "縁結び", score: 1, evidence: [], is_primary: true }],
      }),
    );

    expect(screen.getAllByTestId("recommendation-conclusion")).toHaveLength(1);
    expect(screen.queryByTestId("recommendation-explanation-only-fact")).not.toBeInTheDocument();
  });

  it("deity表示はAuthority/Analyticsに影響しない(card_view analyticsの内容は変化しない)", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は天照大神が祀られています。",
          fact: { label: "検証神社", name: "検証神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
      expect.objectContaining({ event: "card_view", cardId: "shrine_hero", shrineId: 1, recommendationRank: 1 }),
    );
  });
});
