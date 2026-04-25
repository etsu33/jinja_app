import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import MyPageScreen from "../MyPageScreen";
import React from "react";

const mockUseAuth = vi.fn();
vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockUseMyGoshuin = vi.fn();
vi.mock("@/features/mypage/hooks", () => ({
  useMyGoshuin: (args: any) => mockUseMyGoshuin(args),
}));

const mockSearchParams = new Map<string, string>();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key) ?? null,
  }),
}));

// 子コンポーネントは中身まで追わない（coverage目的）
vi.mock("../GoshuinUploadForm", () => ({
  default: () => <div>UPLOAD_FORM</div>,
}));
vi.mock("../MyGoshuinList", () => ({
  default: () => <div>GOSHUIN_LIST</div>,
}));

describe("MyPageScreen", () => {
  beforeEach(() => {
    mockSearchParams.clear();
    mockUseMyGoshuin.mockReturnValue({
      items: [],
      loading: false,
      error: null,
      addItem: vi.fn(),
      removeItem: vi.fn(),
      toggleVisibility: vi.fn(),
    });
  });

  it("loading=true のとき role=status を表示する", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoggedIn: false,
      loading: true,
      logout: vi.fn(),
    });

    render(<MyPageScreen />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("未ログインのとき ログイン導線を表示する", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoggedIn: false,
      loading: false,
      logout: vi.fn(),
    });

    render(<MyPageScreen />);
    const link = screen.getByRole("link", { name: "ログインへ" });
    const href = link.getAttribute("href")!;
    expect(decodeURIComponent(href)).toBe("/auth/login?returnTo=/mypage?tab=goshuin");
  });

  it("ログイン時は アップロードと一覧を表示する", () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "u" },
      isLoggedIn: true,
      loading: false,
      logout: vi.fn(),
    });

    render(<MyPageScreen />);
    expect(screen.getByText("御朱印アップロード")).toBeInTheDocument();
    expect(screen.getByText("UPLOAD_FORM")).toBeInTheDocument();
    expect(screen.getByText("GOSHUIN_LIST")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ログアウト" })).toBeInTheDocument();

    // enabled の条件が効いてるかも軽く担保
    expect(mockUseMyGoshuin).toHaveBeenCalledWith({ enabled: true });
  });

  it("submitted=1 かつ status=pending のとき submission 受付バナーを表示する", () => {
    mockSearchParams.set("submitted", "1");
    mockSearchParams.set("status", "pending");
    mockSearchParams.set("name", "テスト神社");

    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "u" },
      isLoggedIn: true,
      loading: false,
      logout: vi.fn(),
    });

    render(<MyPageScreen />);

    expect(screen.getByRole("status")).toHaveTextContent(
      /「テスト神社」の投稿を受け付けました。\s*現在審査中のため、公開検索にはまだ表示されません。\s*審査完了後に公開されます。/,
    );
  });

  it("submitted=1 でも status=pending 以外なら submission 受付バナーを表示しない", () => {
    mockSearchParams.set("submitted", "1");
    mockSearchParams.set("status", "approved");
    mockSearchParams.set("name", "テスト神社");

    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "u" },
      isLoggedIn: true,
      loading: false,
      logout: vi.fn(),
    });

    render(<MyPageScreen />);

    expect(
      screen.queryByText(
        "「テスト神社」の投稿を受け付けました。現在審査中のため、公開検索にはまだ表示されません。審査完了後に公開されます。",
      ),
    ).not.toBeInTheDocument();
  });
});
