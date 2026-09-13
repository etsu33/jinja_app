// 認証状態の入口は ConciergeSectionsRenderer の useAuth() 1箇所に保つ。
// ConciergeFilterPanel は useAuth() を直接呼ばず、boolean prop で受け取る。
// このファイルは「Renderer が認証状態を正しくPanelへ伝えていること」と
// 「filter_set_birthdate の契約が壊れていないこと」を固定する。
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: false, loading: false })),
}));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: authMock.useAuth }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: vi.fn() }));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";

const NOTICE = "ログイン中は、生年月日を保存してコンシェルジュとコンパスで共通利用します。";

const openFilterState: any = {
  isOpen: true,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
  visitPreferences: [],
  plannedVisitDate: "",
  userOrigin: null,
};

function buildOpenFilterPayload() {
  const u: any = {
    data: { recommendations: [{ shrine_id: 1, display_name: "第一候補神社", reason: "理由文" }] },
    thread: { id: 1 },
  };
  const payload = buildPayloadFromUnified(u, openFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function renderOpenFilter(onAction?: (a: unknown) => void) {
  return render(
    <ConciergeSectionsRenderer
      payload={buildOpenFilterPayload()}
      threadId={1}
      isEntryRoute={false}
      onAction={onAction as never}
    />,
  );
}

describe("ConciergeSectionsRenderer → FilterPanel の保存説明の伝達", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
  });

  it("ログイン中は保存説明が表示される", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });

    renderOpenFilter();

    expect(screen.getByLabelText("誕生日")).toBeInTheDocument();
    expect(screen.getByText(NOTICE)).toBeInTheDocument();
  });

  it("Guestでは保存説明が表示されない", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });

    renderOpenFilter();

    expect(screen.getByLabelText("誕生日")).toBeInTheDocument();
    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
  });

  it("auth解決前（loading）は保存説明を出さない", () => {
    // 未確定の間に「保存します」と出して、Guestのまま消えるのを避ける。
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: true });

    renderOpenFilter();

    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
  });

  it("filter_set_birthdate の契約が壊れていない（ログイン状態に依らない）", () => {
    for (const auth of [
      { isLoggedIn: true, loading: false },
      { isLoggedIn: false, loading: false },
    ]) {
      authMock.useAuth.mockReturnValue(auth);
      const onAction = vi.fn();
      const { unmount } = renderOpenFilter(onAction);

      fireEvent.change(screen.getByLabelText("誕生日"), { target: { value: "1990-05-20" } });

      expect(onAction).toHaveBeenCalledWith({
        type: "filter_set_birthdate",
        birthdate: "1990-05-20",
      });
      unmount();
    }
  });
});
