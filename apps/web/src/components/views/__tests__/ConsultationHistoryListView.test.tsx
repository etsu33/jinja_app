import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ConsultationHistoryListView from "../ConsultationHistoryListView";
import type { ConciergeThread } from "@/lib/api/concierge/types";

const refreshMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: refreshMock, push: vi.fn() }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

const THREADS: ConciergeThread[] = [
  { id: 1, title: "縁結びの相談", last_message: "ありがとうございました。", last_message_at: "2026-07-20T10:00:00Z", message_count: 4 },
  { id: 2, title: "仕事運の相談", last_message: "参考になりました。", last_message_at: "2026-07-10T10:00:00Z", message_count: 2 },
];

describe("ConsultationHistoryListView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("認証状態読み込み中はLoading状態を表示する", () => {
    useAuthMock.mockReturnValue({ loading: true, isLoggedIn: false });
    render(<ConsultationHistoryListView initialThreads={[]} fetchFailed={false} />);

    expect(screen.getByText("読み込み中…")).toBeInTheDocument();
  });

  it("未ログイン(401/403相当)のときEmptyとは別のログイン導線を表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: false });
    render(<ConsultationHistoryListView initialThreads={[]} fetchFailed={false} />);

    expect(screen.getByText("ログインすると、これまでの相談履歴を見返せます。")).toBeInTheDocument();
    expect(screen.queryByText("まだ相談履歴がありません。")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ログインへ" })).toHaveAttribute(
      "href",
      "/auth/login?returnTo=%2Fmypage%2Fhistory",
    );
  });

  it("取得失敗時はError状態とRetry導線を表示し、クリックでrouter.refreshが呼ばれる", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryListView initialThreads={[]} fetchFailed={true} />);

    expect(screen.getByText("相談履歴を読み込めませんでした。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "もう一度読み込む" }));
    expect(refreshMock).toHaveBeenCalledTimes(1);
  });

  it("ログイン済みで0件のときEmpty状態を表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryListView initialThreads={[]} fetchFailed={false} />);

    expect(screen.getByText("まだ相談履歴がありません。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "コンシェルジュに相談する" })).toHaveAttribute("href", "/concierge");
  });

  it("正常系: 相談履歴一覧を表示し、詳細画面へのリンクを持つ", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryListView initialThreads={THREADS} fetchFailed={false} />);

    expect(screen.getByText("縁結びの相談")).toBeInTheDocument();
    expect(screen.getByText("仕事運の相談")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /縁結びの相談/ })).toHaveAttribute("href", "/mypage/history/1");
    expect(screen.getByRole("link", { name: /仕事運の相談/ })).toHaveAttribute("href", "/mypage/history/2");
  });
});
