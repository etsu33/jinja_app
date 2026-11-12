// コンシェルジュでは生年月日を使わない（生年月日との相性はコンパスの役割）。
// 条件を開いたとき、Renderer 経由でもコンパスへの案内が出て、誕生日の入力・保存説明は出ない。
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: true, loading: false })),
}));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: authMock.useAuth }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: vi.fn() }));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";

const openFilterState: any = {
  isOpen: true,
  goriyakuTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
  visitPreferences: [],
  plannedVisitDate: "",
  userOrigin: null,
};

function renderOpenFilter() {
  const u: any = {
    data: { recommendations: [{ shrine_id: 1, display_name: "第一候補神社", reason: "理由文" }] },
    thread: { id: 1 },
  };
  const payload = buildPayloadFromUnified(u, openFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return render(<ConciergeSectionsRenderer payload={payload} threadId={1} isEntryRoute={false} onAction={vi.fn() as never} />);
}

describe("ConciergeSectionsRenderer → FilterPanel のコンパスへの案内", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each([true, false])("ログイン状態(%s)に依らず案内を出し、誕生日の入力と保存説明は出さない", (isLoggedIn) => {
    authMock.useAuth.mockReturnValue({ isLoggedIn, loading: false });
    const { container } = renderOpenFilter();

    expect(screen.getByText("生年月日からの相性は、コンパスで見られます。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "コンパスで相性を見る" })).toHaveAttribute("href", "/compass");
    expect(screen.queryByLabelText("誕生日")).not.toBeInTheDocument();
    expect(container.textContent ?? "").not.toContain("生年月日を保存");
  });
});
