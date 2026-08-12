// Regression test: does the closed-card preset toggle ("静か"/"駅近")
// actually dispatch filter_set_visit_preferences alongside filter_set_extra?
// (ConciergeSectionsRenderer.tsx togglePreset(), added in PR #2405.)
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: false, loading: false })),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: authMock.useAuth,
}));

vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: vi.fn() }));

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
  visitPreferences: [],
};

const heroRec = {
  shrine_id: 1,
  display_name: "第一候補神社",
  reason: "第一候補の理由文です。",
  address: "東京都千代田区1-1-1",
  trust_metadata: {
    rank_class: "由緒あり",
    cultural_status: ["重要文化財"],
    lineage: "式内社",
    origin_summary: "古くから信仰を集める神社です。",
  },
};

describe("closed-card preset toggle -> filter_set_visit_preferences", () => {
  it("clicking 静か dispatches filter_set_visit_preferences with ['quiet']", () => {
    const onAction = vi.fn();
    const u: any = { data: { recommendations: [heroRec] }, thread: { id: 1 } };
    const payload = buildPayloadFromUnified(u, baseFilterState);
    render(
      <ConciergeSectionsRenderer payload={payload!} threadId={1} onAction={onAction} isEntryRoute={false} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "静か" }));

    expect(onAction).toHaveBeenCalledWith(
      expect.objectContaining({ type: "filter_set_extra" }),
    );
    expect(onAction).toHaveBeenCalledWith({
      type: "filter_set_visit_preferences",
      visitPreferences: ["quiet"],
    });
  });

  it("clicking 駅近 dispatches filter_set_visit_preferences with ['nearby']", () => {
    const onAction = vi.fn();
    const u: any = { data: { recommendations: [heroRec] }, thread: { id: 1 } };
    const payload = buildPayloadFromUnified(u, baseFilterState);
    render(
      <ConciergeSectionsRenderer payload={payload!} threadId={1} onAction={onAction} isEntryRoute={false} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "駅近" }));

    expect(onAction).toHaveBeenCalledWith({
      type: "filter_set_visit_preferences",
      visitPreferences: ["nearby"],
    });
  });

  it("clicking ひとり (no canonical mapping) does NOT dispatch filter_set_visit_preferences", () => {
    const onAction = vi.fn();
    const u: any = { data: { recommendations: [heroRec] }, thread: { id: 1 } };
    const payload = buildPayloadFromUnified(u, baseFilterState);
    render(
      <ConciergeSectionsRenderer payload={payload!} threadId={1} onAction={onAction} isEntryRoute={false} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "ひとり" }));

    expect(onAction).toHaveBeenCalledWith(
      expect.objectContaining({ type: "filter_set_extra" }),
    );
    expect(onAction).not.toHaveBeenCalledWith(
      expect.objectContaining({ type: "filter_set_visit_preferences" }),
    );
  });
});
