import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/recommendation-result-ia-v2-final.md (Should item) +
// docs/product/recommendation-result-information-architecture.md §6/§11/§15 PR3:
// the fallback escape-hatch ("近くの神社を静かに見る" / "条件を広げて見直す") must stay
// available under the same conditions and dispatch the same actions as before -- only its
// visual weight changes, so it never reads as visually on par with Hero's Primary CTA
// ("神社の詳細を見る", the only strong CTA on the Result screen).

const PRIMARY_CTA_CLASS_FRAGMENT = "bg-[var(--kt-color-action-primary)]";

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

function buildTestPayload(recommendations: any[], signals: any = {}) {
  const u: any = { data: { recommendations, _signals: signals }, thread: { id: 900 } };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

const semanticHeroRec = {
  shrine_id: 1,
  display_name: "根津神社",
  reason: "仕事運に関わる神社です。",
  reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
};

describe("Fallback Escape-hatch CTA Visual Weight Polish", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    window.localStorage.clear();
  });

  it("1. fallback(_signals.result_state.fallback_mode=nearby_unfiltered) → escape-hatchが表示される", () => {
    const payload = buildTestPayload([semanticHeroRec], { result_state: { fallback_mode: "nearby_unfiltered" } });
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    expect(screen.getByRole("button", { name: "近くの神社を静かに見る" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "条件を広げて見直す" })).toBeInTheDocument();
  });

  it("1b. fallback(is_dummy候補) → escape-hatchが表示される", () => {
    const payload = buildTestPayload([{ ...semanticHeroRec, is_dummy: true }]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    expect(screen.getByRole("button", { name: "近くの神社を静かに見る" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "条件を広げて見直す" })).toBeInTheDocument();
  });

  it("2. semantic Primary(fallbackでもdummyでもない) → escape-hatchは表示されない", () => {
    const payload = buildTestPayload([semanticHeroRec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    expect(screen.queryByRole("button", { name: "近くの神社を静かに見る" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "条件を広げて見直す" })).not.toBeInTheDocument();
  });

  it("3. Primary CTAはfallback時もstrongのまま(bg-action-primaryの塗りを維持)", () => {
    const payload = buildTestPayload([semanticHeroRec], { result_state: { fallback_mode: "nearby_unfiltered" } });
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    const primaryCta = screen.getByRole("link", { name: "神社の詳細を見る" });
    expect(primaryCta.className).toContain(PRIMARY_CTA_CLASS_FRAGMENT);
  });

  it("4. escape-hatchはPrimary CTAと同等のstrong styleではない(bg-action-primaryを持たず、塗りボタンでもない)", () => {
    const payload = buildTestPayload([semanticHeroRec], { result_state: { fallback_mode: "nearby_unfiltered" } });
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    const openMap = screen.getByRole("button", { name: "近くの神社を静かに見る" });
    const widen = screen.getByRole("button", { name: "条件を広げて見直す" });

    for (const btn of [openMap, widen]) {
      expect(btn.className).not.toContain(PRIMARY_CTA_CLASS_FRAGMENT);
      // 塗り(solid fill)スタイルへ後退していないこと -- 旧bg-neutral-900のような
      // 単色塗りボタンは、Primary CTAと並んだ時に同格の強さに見えてしまう。
      expect(btn.className).not.toMatch(/bg-neutral-900|bg-black|text-white/);
      // outline/枠のみスタイルへ格下げされていること。
      expect(btn.className).toContain("border");
    }
  });

  it("5. clickで既存のonAction(open_map / filter_clear)が維持される(navigation先変更0)", () => {
    const onAction = vi.fn();
    const payload = buildTestPayload([semanticHeroRec], { result_state: { fallback_mode: "nearby_unfiltered" } });
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} onAction={onAction} />);

    fireEvent.click(screen.getByRole("button", { name: "近くの神社を静かに見る" }));
    expect(onAction).toHaveBeenCalledWith({ type: "open_map" });

    fireEvent.click(screen.getByRole("button", { name: "条件を広げて見直す" }));
    expect(onAction).toHaveBeenCalledWith({ type: "filter_clear" });
  });

  it("6. fallback表示中もHero側のanalytics(card_view/shrine_detail_transition)は変化しない", () => {
    const payload = buildTestPayload([semanticHeroRec], { result_state: { fallback_mode: "nearby_unfiltered" } });
    render(<ConciergeSectionsRenderer payload={payload} threadId={900} isPremiumActive={false} />);

    expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
      expect.objectContaining({ event: "card_view", cardId: "shrine_hero", shrineId: 1, recommendationRank: 1 }),
    );

    fireEvent.click(screen.getByRole("link", { name: "神社の詳細を見る" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_transition",
      expect.objectContaining({ source: "concierge_result", position: "hero_primary", shrineId: 1 }),
    );
  });
});
