import { fireEvent, render, screen } from "@testing-library/react";
import MyPageView from "@/components/views/MyPageView";

const mocks = vi.hoisted(() => ({ trackConsultationHistoryEntryClicked: vi.fn() }));
const initialUser = {
  id: 1,
  username: "tarou",
  email: "tarou@example.com",
  profile: { nickname: "太郎", is_public: true, birthday: null, birth_time: null, birth_place: "", worship_style: "" },
};

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => "profile" }),
}));
vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => ({ user: initialUser, loading: false, isLoggedIn: true, refreshMe: vi.fn() }),
}));
vi.mock("@/lib/api/users", () => ({ updateUser: vi.fn() }));
vi.mock("@/lib/analytics/consultationHistoryEvents", () => ({
  trackConsultationHistoryEntryClicked: mocks.trackConsultationHistoryEntryClicked,
}));

describe("MyPage 相談履歴導線", () => {
  it("相談履歴リンクは/mypage/historyを指し、クリックでconsultation_history_entry_clickedを送る", () => {
    render(<MyPageView initialFavorites={[]} />);

    const link = screen.getByRole("link", { name: "相談履歴" });
    expect(link).toHaveAttribute("href", "/mypage/history");

    fireEvent.click(link);

    expect(mocks.trackConsultationHistoryEntryClicked).toHaveBeenCalledTimes(1);
  });
});
