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

const mockGetMyShrineSubmissions = vi.fn();
vi.mock("@/lib/api/shrineSubmissions", () => ({
  getMyShrineSubmissions: () => mockGetMyShrineSubmissions(),
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
    mockGetMyShrineSubmissions.mockResolvedValue([]);
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

    render(<MyPageScreen activeTab="goshuin" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("未ログインのとき ログイン導線を表示する", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoggedIn: false,
      loading: false,
      logout: vi.fn(),
    });

    render(<MyPageScreen activeTab="goshuin" />);
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

    render(<MyPageScreen activeTab="goshuin" />);
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

    render(<MyPageScreen activeTab="goshuin" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      /「テスト神社」の投稿を受け付けました。\s*公開までしばらくお待ちください。/,
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

    render(<MyPageScreen activeTab="goshuin" />);

    expect(
      screen.queryByText(
        "「テスト神社」の投稿を受け付けました。現在審査中のため、公開検索にはまだ表示されません。審査完了後に公開されます。",
      ),
    ).not.toBeInTheDocument();
  });

  it("ログイン時に投稿履歴を取得して pending / approved を表示する", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "u" },
      isLoggedIn: true,
      loading: false,
      logout: vi.fn(),
    });

    mockGetMyShrineSubmissions.mockResolvedValue([
      {
        id: 1,
        name: "審査中神社",
        address: "東京都千代田区1-1-1",
        lat: null,
        lng: null,
        goriyaku_tags: [],
        note: "",
        status: "pending",
        created_at: "2026-04-01T00:00:00Z",
      },
      {
        id: 2,
        name: "公開済み神社",
        address: "東京都中央区2-2-2",
        lat: null,
        lng: null,
        goriyaku_tags: [],
        note: "",
        status: "approved",
        created_at: "2026-04-02T00:00:00Z",
        reviewed_at: "2026-04-03T00:00:00Z",
      },
    ]);

    render(<MyPageScreen activeTab="submissions" />);

    expect(await screen.findByText("審査中神社")).toBeInTheDocument();
    expect(screen.getAllByText("審査中")).toHaveLength(2);
    expect(screen.getByText("公開までしばらくお待ちください。")).toBeInTheDocument();

    expect(screen.getByText("公開済み神社")).toBeInTheDocument();
    expect(screen.getAllByText("公開済み")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "検索で見る" })).toHaveAttribute(
      "href",
      "/shrines?q=%E5%85%AC%E9%96%8B%E6%B8%88%E3%81%BF%E7%A5%9E%E7%A4%BE",
    );
    expect(screen.queryByText("差し戻し")).not.toBeInTheDocument();
  });

  it("投稿履歴取得に失敗したらエラーを表示する", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "u" },
      isLoggedIn: true,
      loading: false,
      logout: vi.fn(),
    });
    mockGetMyShrineSubmissions.mockRejectedValue(new Error("failed"));

    render(<MyPageScreen activeTab="submissions" />);

    expect(await screen.findByText("投稿した神社を読み込めませんでした。")).toBeInTheDocument();
  });
});
