import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ConsultationHistoryDetailView from "../ConsultationHistoryDetailView";
import type { ConciergeThreadDetail } from "@/lib/api/concierge/types";

const refreshMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: refreshMock, push: vi.fn() }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

const THREAD: ConciergeThreadDetail = {
  id: 42,
  title: "縁結びの相談",
  last_message: "ありがとうございました。",
  last_message_at: "2026-07-20T10:00:00Z",
  message_count: 2,
  messages: [
    { id: 1, thread_id: 42, role: "user", content: "良い神社を探しています。", created_at: "2026-07-20T09:00:00Z" },
    { id: 2, thread_id: 42, role: "assistant", content: "こちらはいかがでしょうか。", created_at: "2026-07-20T09:05:00Z" },
  ],
  recommendations_v2: [
    {
      shrine_id: 5,
      name: "根津神社",
      address: "東京都文京区根津1-28-9",
      action_state: "saved",
      recommendation_reason_v4_detail: {
        version: "v4",
        reason_text: "縁結びの神として知られています。",
        fact: {
          label: "根津神社",
          name: "根津神社",
          deity: "須佐之男命",
          shrine_history: null,
          place_context: "東京都文京区根津1-28-9",
          history_theme: null,
          goriyaku: null,
          visit_style_tags: [],
          evidence: [],
        },
        interpretation: { theme: "縁結び", text: "新しい縁が結ばれる時期です。" },
        action: { text: "静かに参拝してみましょう。", source: "template" },
      },
    },
  ],
};

describe("ConsultationHistoryDetailView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("認証状態読み込み中はLoading状態を表示する", () => {
    useAuthMock.mockReturnValue({ loading: true, isLoggedIn: false });
    render(<ConsultationHistoryDetailView tid="42" thread={null} fetchFailed={false} />);

    expect(screen.getByText("読み込み中…")).toBeInTheDocument();
  });

  it("未ログイン(401/403相当)のときログイン導線を表示し、returnToにtidを含む", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: false });
    render(<ConsultationHistoryDetailView tid="42" thread={null} fetchFailed={false} />);

    expect(screen.getByRole("link", { name: "ログインへ" })).toHaveAttribute(
      "href",
      "/auth/login?returnTo=%2Fmypage%2Fhistory%2F42",
    );
  });

  it("取得失敗時はError状態とRetry導線を表示し、クリックでrouter.refreshが呼ばれる", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryDetailView tid="42" thread={null} fetchFailed={true} />);

    expect(screen.getByText("相談履歴を読み込めませんでした。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "もう一度読み込む" }));
    expect(refreshMock).toHaveBeenCalledTimes(1);
  });

  it("Direct Navigation: 不正または存在しないtid(thread=null)のとき見つからない旨を表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryDetailView tid="999" thread={null} fetchFailed={false} />);

    expect(screen.getByText("この相談は見つかりませんでした。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "相談履歴の一覧へ戻る" })).toHaveAttribute("href", "/mypage/history");
  });

  it("正常系: 会話履歴と推薦神社カード、Fact要約、action_stateバッジを表示する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryDetailView tid="42" thread={THREAD} fetchFailed={false} />);

    expect(screen.getByRole("heading", { name: "縁結びの相談" })).toBeInTheDocument();
    expect(screen.getByText("良い神社を探しています。")).toBeInTheDocument();
    expect(screen.getByText("こちらはいかがでしょうか。")).toBeInTheDocument();

    expect(screen.getByText("根津神社")).toBeInTheDocument();
    expect(screen.getByText("気になる登録済み")).toBeInTheDocument();
    // Fact優先順位: deityが最優先。place_context(住所)はFact本文として使われない。
    expect(screen.getByText("須佐之男命")).toBeInTheDocument();
  });

  it("Shrine Detail遷移: 推薦神社カードのリンクがctx=concierge&tidを維持する", () => {
    useAuthMock.mockReturnValue({ loading: false, isLoggedIn: true });
    render(<ConsultationHistoryDetailView tid="42" thread={THREAD} fetchFailed={false} />);

    expect(screen.getByRole("link", { name: "神社の詳細を見る" })).toHaveAttribute(
      "href",
      "/shrines/5?ctx=concierge&tid=42",
    );
  });
});
