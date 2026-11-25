import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// 見どころ単位の推薦 PR-3：推薦カードの「ここで見る」と計測。

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

function buildTestPayload(recommendations: any[]) {
  const payload = buildPayloadFromUnified({ data: { recommendations }, thread: { id: 800 } } as any, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function pick(shrineId: number, highlightId: number, name: string) {
  return {
    highlight_id: highlightId,
    shrine_id: shrineId,
    name,
    need_tag: "career",
    answer_text: `${name}の由来が、今の相談と重なるかもしれない。`,
  };
}

const hero = { shrine_id: 1, display_name: "第一候補神社", reason: "第一候補の理由文です。" };
const compact = { shrine_id: 2, display_name: "第二候補神社", reason: "第二候補の理由文です。" };

function openOthers() {
  fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
}

function impressions() {
  return analyticsMocks.trackSearchEvent.mock.calls
    .filter(([name]) => name === "concierge_result_impression")
    .map(([, payload]) => payload);
}

describe("ConciergeSectionsRenderer - ここで見る（highlight_pick）", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    window.localStorage.clear();
  });

  it("第一候補：見どころの名前・アンサーの文・詳細の見どころへのリンクを出す", () => {
    const payload = buildTestPayload([{ ...hero, highlight_pick: pick(1, 7, "芸能浅間神社") }, compact]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);

    const block = screen.getByTestId("concierge-highlight-pick");
    expect(within(block).getByText("ここで見る")).toBeTruthy();
    expect(within(block).getByText("芸能浅間神社の由来が、今の相談と重なるかもしれない。")).toBeTruthy();
    const link = within(block).getByRole("link", { name: "芸能浅間神社" });
    expect(link.getAttribute("href")).toBe("/shrines/1?ctx=concierge&tid=800#shrine-highlight-7");
  });

  it("推薦理由の節（今回の相談との接点）の中には入れない", () => {
    const payload = buildTestPayload([
      {
        ...hero,
        reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
        highlight_pick: pick(1, 7, "芸能浅間神社"),
      },
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);

    const block = screen.getByTestId("concierge-highlight-pick");
    expect(
      block.closest('[data-testid="recommendation-runtime-match"], [data-testid="recommendation-history-theme"]'),
    ).toBeNull();
    // 推薦理由の文（reason_facts 由来）に見どころの名前を混ぜない
    expect(screen.getAllByText(/芸能浅間神社/).every((el) => block.contains(el))).toBe(true);
  });

  it("2位以降のカードにも出す", () => {
    const payload = buildTestPayload([hero, { ...compact, highlight_pick: pick(2, 9, "唐獅子") }]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);
    openOthers();

    const block = screen.getByTestId("concierge-highlight-pick");
    expect(within(block).getByRole("link", { name: "唐獅子" }).getAttribute("href")).toBe(
      "/shrines/2?ctx=concierge&tid=800#shrine-highlight-9",
    );
  });

  it("無ければ何も出さない（代わりの文も出さない）", () => {
    const payload = buildTestPayload([hero, compact]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);
    openOthers();
    expect(screen.queryByTestId("concierge-highlight-pick")).toBeNull();
    expect(screen.queryByText("ここで見る")).toBeNull();
  });

  it("押すと concierge_highlight_pick_click を送る（文は送らない）", () => {
    const payload = buildTestPayload([{ ...hero, highlight_pick: pick(1, 7, "芸能浅間神社") }]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);

    fireEvent.click(screen.getByRole("link", { name: "芸能浅間神社" }));

    const clicks = analyticsMocks.trackSearchEvent.mock.calls.filter(([name]) => name === "concierge_highlight_pick_click");
    expect(clicks).toHaveLength(1);
    const payloadSent = clicks[0][1];
    expect(payloadSent).toMatchObject({
      source: "concierge_result",
      shrineId: 1,
      recommendationRank: 1,
      highlightId: 7,
      highlightNeedTag: "career",
    });
    expect(JSON.stringify(payloadSent)).not.toContain("重なるかもしれない");
  });

  it("表示の計測に、見どころを出したかどうかが入る", () => {
    const payload = buildTestPayload([{ ...hero, highlight_pick: pick(1, 7, "芸能浅間神社") }, compact]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={800} isPremiumActive={false} />);

    const byShrine = Object.fromEntries(impressions().map((p: any) => [p.shrineId, p]));
    expect(byShrine[1]).toMatchObject({ hasHighlightPick: true, highlightId: 7, highlightNeedTag: "career" });
    expect(byShrine[2]).toMatchObject({ hasHighlightPick: false, highlightId: null, highlightNeedTag: null });
  });
});
