import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/product/recommendation-result-information-architecture.md §15
// Compact Recommendation Reason / Explanation Consistency
// docs/product/recommendation-signal-authority.md §8 Knowledge Authority (A: 現状維持)
//
// PR #2442 (Explanation-only Fact Visual Distinction) はHeroにのみ適用され、Compact Card
// (2位以降候補)はdeity/shrine_historyの区別を継承していなかった(docs/audit/
// recommendation-result-ia-v2-final.md Should item)。ここではCompact CardでもHeroと同じ
// reasonV4FactPriority.ts / buildHeroReasonV4Sections.tsのExplanation-only分類をそのまま
// 再利用し(Compact独自のAuthority再実装はしない)、旧2見出し(「相談内容・ご利益との一致」+
// 「この神社を選んだ理由」)の反復を1つのreason blockへ整理したことを検証する。

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
  const u: any = { data: { recommendations }, thread: { id: 800 }, meta };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

const heroRec = {
  shrine_id: 1,
  display_name: "第一候補神社",
  reason: "第一候補の理由文です。",
};

function compactRec(overrides: Partial<any> = {}) {
  return {
    shrine_id: 2,
    display_name: "第二候補神社",
    reason: "第二候補の理由文です。",
    ...overrides,
  };
}

function openOthers() {
  fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
}

function compactCardOf(name: string) {
  const card = screen.getByText(name).closest("article");
  if (!card) throw new Error(`compact card not found: ${name}`);
  return card;
}

describe("Compact Recommendation Reason / Explanation Consistency", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    window.localStorage.clear();
  });

  it("1. need_tag → Compactのreason blockへPrimaryとして表示される", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({ reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }] }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    expect(card.querySelector('[data-testid="recommendation-match-reason"]')).toHaveTextContent("仕事運");
  });

  it("2. history_theme → Compactのreason blockへPrimaryとして表示される", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({ reason_facts: [{ type: "history_theme", label: "再出発", score: 1, evidence: [], is_primary: true }] }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    expect(card.querySelector('[data-testid="recommendation-match-reason"]')).toHaveTextContent("再出発");
  });

  it("3. deity → Compactでも「参考情報」ラベル付きでExplanation-only表示され、reason blockには混ざらない", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({
        reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "第二候補神社は天照大神が祀られています。",
          fact: { label: "第二候補神社", name: "第二候補神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
          interpretation: { text: "" },
          action: { text: "" },
        },
      }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    const reasonBlock = card.querySelector('[data-testid="recommendation-match-reason"]');
    expect(reasonBlock).not.toHaveTextContent("天照大神");

    const explanationOnly = card.querySelector('[data-testid="recommendation-compact-explanation-only-fact"]');
    expect(explanationOnly).toHaveTextContent("参考情報");
    expect(explanationOnly).toHaveTextContent("天照大神");
  });

  it("4. shrine_history → Compactでも「参考情報」ラベル付きでExplanation-only表示される(deityが無い場合)", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({
        reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "第二候補神社は古い由緒を持ちます。",
          fact: { label: "第二候補神社", name: "第二候補神社", deity: null, shrine_history: "創建は平安時代に遡ります。", goriyaku: null, history_theme: null },
          interpretation: { text: "" },
          action: { text: "" },
        },
      }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    const explanationOnly = card.querySelector('[data-testid="recommendation-compact-explanation-only-fact"]');
    expect(explanationOnly).toHaveTextContent("創建は平安時代に遡ります。");
  });

  it("5. fallback + deity → deityがreason blockのPrimary理由として扱われない(false attributionなし)", () => {
    const payload = buildTestPayload(
      [
        heroRec,
        compactRec({
          // reason_facts無し・reasonV4のstructuredもdeityのみ -- 構造化されたRecommendation
          // 理由が存在しないfallbackケース。
          recommendation_reason_v4_detail: {
            version: "v4",
            reason_text: "近くの神社として候補に入っています。",
            fact: { label: "第二候補神社", name: "第二候補神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
            interpretation: { text: "" },
            action: { text: "" },
          },
        }),
      ],
      { resultState: { fallback_mode: "nearby_unfiltered" } },
    );
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    const reasonBlock = card.querySelector('[data-testid="recommendation-match-reason"]');
    expect(reasonBlock).not.toHaveTextContent("天照大神");

    // deity自体は参考情報として引き続き提示される。
    expect(card.querySelector('[data-testid="recommendation-compact-explanation-only-fact"]')).toHaveTextContent("天照大神");
  });

  it("6. Knowledgeなし(deity/shrine_historyともに無い) → 参考情報UIを一切表示しない", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({ reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }] }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    expect(card.querySelector('[data-testid="recommendation-compact-explanation-only-fact"]')).toBeNull();
    expect(card).not.toHaveTextContent("参考情報");
  });

  it("7. heading重複なし: reason blockは1つだけで、旧「この神社を選んだ理由」見出しは存在しない", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({
        reason:
          "この長い理由文は44文字を大きく超える想定で書かれており、compactTextによって句点や記号の位置で自然に切り詰められることを検証するためのテキストです。",
      }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    const card = compactCardOf("第二候補神社");
    expect(card.querySelectorAll('[data-testid="recommendation-match-reason"]')).toHaveLength(1);
    expect(card.querySelector('[data-testid="recommendation-standard-reason"]')).toBeNull();
    expect(screen.queryByText("この神社を選んだ理由")).not.toBeInTheDocument();
  });

  it("8. legacy path(reason_facts/reasonV4Detailどちらも無し)でもクラッシュせず表示される(non-regression)", () => {
    const payload = buildTestPayload([heroRec, compactRec()]);

    expect(() => {
      render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
      openOthers();
    }).not.toThrow();

    const card = compactCardOf("第二候補神社");
    expect(card.querySelector('[data-testid="recommendation-match-reason"]')).not.toBeNull();
  });

  it("既存のDetailクリックanalytics(shrine_detail_transition)は変化しない", () => {
    const payload = buildTestPayload([
      heroRec,
      compactRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "第二候補神社は天照大神が祀られています。",
          fact: { label: "第二候補神社", name: "第二候補神社", deity: "天照大神", shrine_history: null, goriyaku: null, history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={true} />);
    openOthers();

    fireEvent.click(screen.getByText("詳細だけ見る"));

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_transition",
      expect.objectContaining({ source: "concierge_result", position: "compact", shrineId: 2, recommendationRank: 2 }),
    );
  });
});
