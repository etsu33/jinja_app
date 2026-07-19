import { fireEvent, render, screen } from "@testing-library/react";
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
    thread: { id: 768 },
  };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

const heroRec = {
  shrine_id: 1,
  display_name: "第一候補神社",
  reason: "第一候補の理由文です。",
  address: "東京都千代田区1-1-1",
};

const otherRecWithAddress = {
  shrine_id: 2,
  display_name: "他候補神社A",
  reason:
    "この長い理由文は44文字を大きく超える想定で書かれており、compactTextによって句点や記号の位置で自然に切り詰められることを検証するためのテキストです。",
  address: "東京都中央区2-2-2",
};

const otherRecWithoutAddress = {
  shrine_id: 3,
  display_name: "他候補神社B",
  reason: "他候補神社Bの短い理由。",
};

describe("ConciergeSectionsRenderer - 他候補の開閉UI", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    window.localStorage.clear();
  });

  it("他候補一覧は初期状態で非表示である", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    expect(screen.getByText("迷った時だけ、ほかの神社を見る")).toBeInTheDocument();
    expect(screen.queryByText("他候補神社A")).not.toBeInTheDocument();
  });

  it("ワンタップで展開し、再度クリックすると折りたたまれ、もう一度開ける", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    const toggle = screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" });
    fireEvent.click(toggle);

    expect(screen.getByText("他候補神社A")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ほかの神社を閉じる" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "ほかの神社を閉じる" }));
    expect(screen.queryByText("他候補神社A")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
    expect(screen.getByText("他候補神社A")).toBeInTheDocument();
  });

  it("aria-expandedが開閉stateと同期し、aria-controlsがContainerのidと一致する", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    const toggle = screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(toggle);

    const opened = screen.getByRole("button", { name: "ほかの神社を閉じる" });
    expect(opened).toHaveAttribute("aria-expanded", "true");

    const controlsId = opened.getAttribute("aria-controls");
    expect(controlsId).toBeTruthy();
    expect(document.getElementById(controlsId as string)).not.toBeNull();
    expect(document.getElementById(controlsId as string)?.textContent).toContain("ほかの神社");
  });

  it("開閉後もトリガーボタンにフォーカスが残る", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    const toggle = screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" });
    toggle.focus();
    fireEvent.click(toggle);

    const opened = screen.getByRole("button", { name: "ほかの神社を閉じる" });
    expect(document.activeElement).toBe(opened);

    fireEvent.click(opened);
    const closed = screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" });
    expect(document.activeElement).toBe(closed);
  });

  it("他候補カードにaddressが表示される", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));

    expect(screen.getByText("東京都中央区2-2-2")).toBeInTheDocument();
  });

  it("他候補カードの理由は44字以内に圧縮された1ブロックのみ表示され、summary・tagsは表示されない", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));

    // primaryPhraseはreason_facts/breakdown由来のテンプレート文であり、
    // 元のreasonテキストをそのまま切り詰めたものではないため、
    // 「1ブロックのみ・44字以内」という配線・表示制約のみを検証する。
    const compactCard = screen.getByText("他候補神社A").closest("article");
    expect(compactCard).not.toBeNull();

    const reasonParagraphs = Array.from(compactCard?.querySelectorAll("p") ?? []);
    expect(reasonParagraphs).toHaveLength(1);
    expect((reasonParagraphs[0].textContent ?? "").length).toBeGreaterThan(0);
    expect((reasonParagraphs[0].textContent ?? "").length).toBeLessThanOrEqual(44);
  });

  it("addressがない他候補カードでもエラーにならず表示される", () => {
    const payload = buildTestPayload([heroRec, otherRecWithoutAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
    expect(screen.getByText("他候補神社B")).toBeInTheDocument();
  });

  it("Heroの表示・詳細リンクに変更がない", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    expect(screen.getByText("第一候補神社")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "神社の詳細を見る" })).toBeInTheDocument();
  });

  it("他候補の詳細クリックで既存のshrine_detail_transitionイベントが従来どおり発火する", () => {
    const payload = buildTestPayload([heroRec, otherRecWithAddress]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
    fireEvent.click(screen.getByText("詳細だけ見る"));

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_transition",
      expect.objectContaining({
        source: "concierge_result",
        position: "compact",
        shrineId: 2,
        recommendationRank: 2,
      }),
    );
  });
});
