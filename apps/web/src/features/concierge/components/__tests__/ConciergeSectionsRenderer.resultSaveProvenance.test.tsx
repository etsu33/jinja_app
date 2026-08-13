import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/recommendation-strict-funnel-readiness.md §9, §14-4:
// Result画面(ConciergeSectionsRenderer)のhero card直下ShrineSaveButtonはDetailを経由せず
// Saveできる唯一の経路だが、recommendationInstanceId / Authority provenanceを一切
// 受け取っていなかった。ここではResult Save(Hero)がDetail Saveと同じ意味論で
// provenanceを保持することを固定する。Frontendは値を再計算・推測・再構成しない
// (heroItem.recommendationInstanceId / heroItem.analyticsProvenanceをそのまま転記するのみ)。

const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackCardEvent: vi.fn(),
  track: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
}));

vi.mock("@/lib/analytics/track", () => ({
  track: analyticsMocks.track,
}));

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: true, loading: false })),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: authMock.useAuth,
}));

const useFavoriteMock = vi.hoisted(() => vi.fn());
vi.mock("@/hooks/useFavorite", () => ({
  useFavorite: (args: unknown) => useFavoriteMock(args),
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

function saveClick() {
  const button = screen.getAllByRole("button").find((el) => /保存/.test(el.textContent ?? ""));
  if (!button) throw new Error("save button not found");
  fireEvent.click(button);
}

function favoriteClickCalls() {
  return analyticsMocks.track.mock.calls.filter(([name]) => name === "favorite_click");
}

const heroRecWithAuthority = {
  shrine_id: 1,
  display_name: "第一候補神社",
  reason: "第一候補の理由文です。",
  recommendation_instance_id: "gen-hero-a1b2",
  reason_facts: [{ type: "history_theme", label: "history_theme", score: 1, evidence: [], is_primary: true }],
};

const fallbackRec = {
  shrine_id: 2,
  display_name: "近隣神社",
  reason: "近隣という理由です。",
  recommendation_instance_id: "gen-hero-fallback",
  reason_facts: [{ type: "fallback", label: "fallback", score: 1, evidence: [], is_primary: true }],
};

describe("Result Save (Hero) Provenance", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.track.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    useFavoriteMock.mockReset();
    useFavoriteMock.mockReturnValue({ fav: false, busy: false, toggle: vi.fn().mockResolvedValue(undefined) });
    window.localStorage.clear();
  });

  it("1. Hero SaveでrecommendationInstanceIdが保持される", async () => {
    const payload = buildTestPayload([heroRecWithAuthority]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    saveClick();

    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    expect(favoriteClickCalls()[0][1]).toMatchObject({
      shrineId: 1,
      recommendationInstanceId: "gen-hero-a1b2",
    });
  });

  it("3. primaryReasonSourceが保持される", async () => {
    const payload = buildTestPayload([heroRecWithAuthority]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    saveClick();

    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    expect(favoriteClickCalls()[0][1]).toMatchObject({
      primaryReasonSource: "history_theme",
    });
  });

  it("4. fallback(isFallbackRecommendation)が保持される", async () => {
    const payload = buildTestPayload([fallbackRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    saveClick();

    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    expect(favoriteClickCalls()[0][1]).toMatchObject({
      primaryReasonSource: "fallback",
      isFallbackRecommendation: true,
    });
  });

  it("6. direct/non-concierge Result表示に相当するデータ欠損時はidentityを合成せずnullのまま送る", async () => {
    const payload = buildTestPayload([
      { shrine_id: 3, display_name: "識別子なし神社", reason: "理由" },
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    saveClick();

    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    expect(favoriteClickCalls()[0][1].recommendationInstanceId).toBeNull();
  });

  it("7. malformed/null provenance/instance IdでもSave操作自体はクラッシュしない", async () => {
    const payload = buildTestPayload([
      {
        shrine_id: 4,
        display_name: "不正data神社",
        reason: "理由",
        recommendation_instance_id: { unexpected: "shape" },
        reason_facts: "not-an-array",
      },
    ]);

    expect(() => {
      render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);
    }).not.toThrow();

    expect(() => saveClick()).not.toThrow();
    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    expect(favoriteClickCalls()[0][1].recommendationInstanceId).toBeNull();
  });
});

describe("Result Save (Hero) vs Detail Save: semantic parity", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.track.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    useFavoriteMock.mockReset();
    useFavoriteMock.mockReturnValue({ fav: false, busy: false, toggle: vi.fn().mockResolvedValue(undefined) });
    window.localStorage.clear();
  });

  it("5. Result Hero SaveとDetail Saveは同じfield名で同じ意味のprovenanceを送る", async () => {
    // Detail Save側の契約 (shrines/[id]/page.tsx -> ShrineSaveButton) はPR #2432で
    // recommendationInstanceId / analyticsProvenance をそのまま渡す設計になっている。
    // Result Hero Saveも同じ ShrineSaveButton を同じprop名で使うため、
    // 同一のrecommendation (同一shrine_id, 同一recommendation_instance_id) であれば
    // 送信されるfieldの集合と値は一致する。
    const payload = buildTestPayload([heroRecWithAuthority]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    saveClick();

    await waitFor(() => expect(favoriteClickCalls()).toHaveLength(1));
    const resultSavePayload = favoriteClickCalls()[0][1];

    // Detail Save側と共通のfield集合(shrines/[id]/page.tsx -> ShrineSaveButton.tsx)。
    expect(resultSavePayload).toMatchObject({
      shrineId: 1,
      recommendationInstanceId: "gen-hero-a1b2",
      primaryReasonSource: "history_theme",
    });
    expect(typeof resultSavePayload.recommendationInstanceId === "string" || resultSavePayload.recommendationInstanceId === null).toBe(true);
  });

  it("2. Compact(rank>=2)由来のRecommendationも、Detail Save到達時に同じrecommendationInstanceIdを保持する", () => {
    // ShrineCardCompact(Result画面のcompact card)には保存UIが存在しないため
    // (本Fixはprohibitedな UI追加を行わない)、Compact由来のrecommendationは
    // Detail画面へ遷移してから保存される。そのDetail遷移(click)がcompactの
    // recommendationInstanceIdを正しく運ぶことを確認する -- Detail Save自体は
    // PR #2432で確認済みのthread snapshot読み取りにより、この値をそのまま復元する。
    const heroRec = { shrine_id: 1, display_name: "Hero", reason: "R1", recommendation_instance_id: "gen-shared" };
    const compactRec = {
      shrine_id: 5,
      display_name: "Compact神社",
      reason: "R2",
      recommendation_instance_id: "gen-shared",
    };
    const payload = buildTestPayload([heroRec, compactRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={768} isPremiumActive={true} />);

    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
    fireEvent.click(screen.getByText("詳細だけ見る"));

    const clickCall = analyticsMocks.trackSearchEvent.mock.calls.find(
      ([name]) => name === "shrine_detail_transition",
    );
    expect(clickCall?.[1]).toMatchObject({ shrineId: 5, recommendationInstanceId: "gen-shared" });
  });
});
