import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import MyPageView from "@/components/views/MyPageView";

const mocks = vi.hoisted(() => ({ updateUser: vi.fn(), refreshMe: vi.fn() }));
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
  useAuth: () => ({ user: initialUser, loading: false, isLoggedIn: true, refreshMe: mocks.refreshMe }),
}));
vi.mock("@/lib/api/users", () => ({ updateUser: mocks.updateUser }));

describe("MyPage profile editing", () => {
  it("saves the four profile fields and previews derived values", async () => {
    mocks.updateUser.mockResolvedValue({
      ...initialUser,
      profile: { ...initialUser.profile, birthday: "1984-05-15", birth_time: "05:25:00", birth_place: "東京都", worship_style: "朝参り" },
    });

    render(<MyPageView initialFavorites={[]} />);
    fireEvent.change(screen.getByLabelText("生年月日"), { target: { value: "1984-05-15" } });
    fireEvent.change(screen.getByLabelText(/出生時間/), { target: { value: "05:25" } });
    fireEvent.change(screen.getByLabelText("出生地"), { target: { value: "東京都" } });
    fireEvent.click(screen.getByRole("button", { name: "朝参り" }));

    expect(screen.getByText("七赤金星")).toBeInTheDocument();
    expect(screen.getByText("ライフパス").parentElement).toHaveTextContent("6");
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith(expect.objectContaining({
      birthday: "1984-05-15", birth_time: "05:25", birth_place: "東京都", worship_style: "朝参り",
    })));
    expect(await screen.findByText("プロフィールを保存しました。")).toBeInTheDocument();
  });
});
