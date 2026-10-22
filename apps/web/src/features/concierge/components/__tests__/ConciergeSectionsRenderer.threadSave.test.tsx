import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackCardEvent: vi.fn(),
  track: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/analytics/track", () => ({ track: analyticsMocks.track }));

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: true, loading: false })),
}));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: authMock.useAuth }));

vi.mock("@/hooks/useFavorite", () => ({
  useFavorite: () => ({ fav: false, busy: false, toggle: vi.fn().mockResolvedValue(undefined) }),
}));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";
import type { ConciergeThreadSaveState } from "@/features/concierge/useConciergeThreadSave";

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

function buildPayload() {
  const u: any = {
    data: { recommendations: [{ shrine_id: 1, display_name: "根津神社", reason: "仕事運に関わる神社です。" }] },
    thread: { id: 500 },
  };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

// Hero の ShrineSaveButton と同ラベルのため、feedback 領域の直前要素で save_prompt ボタンを特定する。
function savePromptButton() {
  return screen.getByTestId("concierge-thread-save-feedback").previousElementSibling as HTMLButtonElement;
}

function renderWith(threadSaveState?: ConciergeThreadSaveState, onAction = vi.fn()) {
  render(
    <ConciergeSectionsRenderer
      payload={buildPayload()}
      threadId={500}
      onAction={onAction}
      threadSaveState={threadSaveState}
    />,
  );
  return onAction;
}

describe("ConciergeSectionsRenderer - save_prompt 保存フィードバック", () => {
  beforeEach(() => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    window.localStorage.clear();
  });

  it("idle: 既存ラベルでクリックすると save_concierge_thread を発火する", () => {
    const onAction = renderWith({ status: "idle", error: null, historyHref: null });

    const button = savePromptButton();
    expect(button).toHaveTextContent("あとで見返すために保存");
    expect(button).toBeEnabled();
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledWith({ type: "save_concierge_thread" });
  });

  it("saving: 確認中はボタンを無効化して重複クリックを防ぐ", () => {
    const onAction = renderWith({ status: "saving", error: null, historyHref: null });

    const button = savePromptButton();
    expect(button).toHaveTextContent("保存を確認しています…");
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(onAction).not.toHaveBeenCalled();
  });

  it("saved: 保存済み表示と履歴詳細へのリンクを出す", () => {
    renderWith({ status: "saved", error: null, historyHref: "/mypage/history/500" });

    expect(savePromptButton()).toHaveTextContent("保存済み");
    const feedback = screen.getByTestId("concierge-thread-save-feedback");
    expect(feedback).toHaveTextContent("相談履歴に保存されています。");
    expect(within(feedback).getByRole("link", { name: "履歴で見返す" })).toHaveAttribute(
      "href",
      "/mypage/history/500",
    );
  });

  it("error: 失敗理由を表示し、成功表示は出さない", () => {
    renderWith({ status: "error", error: "network", historyHref: null });

    expect(savePromptButton()).toHaveTextContent("あとで見返すために保存");
    const feedback = screen.getByTestId("concierge-thread-save-feedback");
    expect(feedback).toHaveTextContent("保存を確認できませんでした");
    expect(within(feedback).queryByRole("link")).toBeNull();
  });

  it("未ログイン: ログイン誘導ラベルのままで保存フィードバックは出さない", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    renderWith({ status: "saved", error: null, historyHref: "/mypage/history/500" });

    expect(savePromptButton()).toHaveTextContent("ログインしてあとで見返す");
    expect(screen.getByTestId("concierge-thread-save-feedback")).toBeEmptyDOMElement();
  });
});
