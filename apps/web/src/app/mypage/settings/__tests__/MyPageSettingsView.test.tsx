import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import MyPageSettingsView from "@/components/views/MyPageSettingsView";
import type { AuthUser } from "@/lib/auth/types";

const mocks = vi.hoisted(() => ({
  updateUser: vi.fn(),
  refreshMe: vi.fn(),
  logout: vi.fn(),
  replace: vi.fn(),
  useAuth: vi.fn(),
}));

vi.mock("@/lib/api/users", () => ({ updateUser: mocks.updateUser }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace, push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => mocks.useAuth(),
}));

function authUser(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    username: "tarou",
    email: "tarou@example.com",
    profile: { nickname: "太郎", is_public: true },
    ...overrides,
  };
}

describe("/mypage/settings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // clearAllMocks は呼び出し履歴だけを消し、mockResolvedValue /
    // mockRejectedValue の実装は残す。refreshMe を reject させるテストの
    // 設定が後続テストへ漏れるため、実装ごと落としておく。
    mocks.updateUser.mockReset();
    mocks.refreshMe.mockReset();
    mocks.useAuth.mockReturnValue({
      user: authUser(),
      loading: false,
      isLoggedIn: true,
      logout: mocks.logout,
      refreshMe: mocks.refreshMe,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("保存済みnicknameを表示名として表示する", () => {
    render(<MyPageSettingsView />);

    expect(screen.getByLabelText("表示名")).toHaveValue("太郎");
    expect(screen.getByRole("button", { name: "表示名を保存" })).toBeDisabled();
  });

  it("表示名を変更したときnicknameだけを更新する", async () => {
    mocks.updateUser.mockResolvedValue(authUser({ profile: { nickname: "次郎", is_public: true } }));

    render(<MyPageSettingsView />);

    fireEvent.change(screen.getByLabelText("表示名"), { target: { value: "次郎" } });
    fireEvent.click(screen.getByRole("button", { name: "表示名を保存" }));

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ nickname: "次郎" }));
    expect(await screen.findByText("表示名を保存しました。")).toBeInTheDocument();
    await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
  });

  it("表示名保存に失敗しても入力値を保持する", async () => {
    mocks.updateUser.mockRejectedValue(new Error("updateUser failed: 500"));

    render(<MyPageSettingsView />);

    fireEvent.change(screen.getByLabelText("表示名"), { target: { value: "次郎" } });
    fireEvent.click(screen.getByRole("button", { name: "表示名を保存" }));

    expect(
      await screen.findByText("表示名を保存できませんでした。入力内容を確認して、もう一度お試しください。"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("表示名")).toHaveValue("次郎");
  });

  // PATCH は成功しているので、refreshMe の失敗を「保存できませんでした」と
  // 報告すると Backend の実態と食い違う。birthday と同じ失敗境界を固定する。
  it("表示名の保存は成功しrefreshMeだけ失敗した場合、保存失敗として表示しない", async () => {
    mocks.updateUser.mockResolvedValue(authUser({ profile: { nickname: "次郎", is_public: true } }));
    mocks.refreshMe.mockRejectedValue(new Error("refreshMe failed"));

    render(<MyPageSettingsView />);

    fireEvent.change(screen.getByLabelText("表示名"), { target: { value: "次郎" } });
    fireEvent.click(screen.getByRole("button", { name: "表示名を保存" }));

    // PATCH は実行済み
    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ nickname: "次郎" }));
    await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));

    expect(
      await screen.findByText(
        "表示名は保存されましたが、表示の更新に失敗しました。ページを再読み込みしてください。",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("表示名を保存できませんでした。入力内容を確認して、もう一度お試しください。"),
    ).not.toBeInTheDocument();
    // 保存は確定しているので更新後の表示名を維持する
    expect(screen.getByLabelText("表示名")).toHaveValue("次郎");
  });

  it("公開設定の保存は成功しrefreshMeだけ失敗した場合、rollbackも保存失敗表示もしない", async () => {
    // savedIsPublic は true。false へ切り替えた結果が維持されることを見る。
    mocks.updateUser.mockResolvedValue(authUser({ profile: { nickname: "太郎", is_public: false } }));
    mocks.refreshMe.mockRejectedValue(new Error("refreshMe failed"));

    render(<MyPageSettingsView />);

    const checkbox = screen.getByRole("checkbox", { name: "プロフィールを公開" });
    expect(checkbox).toBeChecked();
    fireEvent.click(checkbox);

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ is_public: false }));
    await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));

    expect(
      await screen.findByText(
        "公開設定は保存されましたが、表示の更新に失敗しました。ページを再読み込みしてください。",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("公開設定を保存できませんでした。時間をおいて、もう一度お試しください。"),
    ).not.toBeInTheDocument();
    // returned is_public を維持し、savedIsPublic(true) へ戻さない
    expect(screen.getByRole("checkbox", { name: "プロフィールを公開" })).not.toBeChecked();
  });

  // 生年月日は Shared Birthday Context のセルフ管理対象としてここに出す。
  // それ以外の Personal Context（出生時間 / 出生地 / 参拝スタイル / 九星 / 五行）は
  // 引き続き設定に出さない。この境界を崩さないために除外側を残す。
  it("生年月日以外のPersonal Context入力項目は設定に表示しない", () => {
    render(<MyPageSettingsView />);

    expect(screen.getByLabelText("生年月日")).toBeInTheDocument();
    expect(screen.queryByLabelText(/出生時間/)).toBeNull();
    expect(screen.queryByLabelText("出生地")).toBeNull();
    expect(screen.queryByText("参拝スタイル")).toBeNull();
    expect(screen.queryByText("九星")).toBeNull();
    expect(screen.queryByText("五行")).toBeNull();
  });

  it("プロフィール公開の現在値を表示する", () => {
    render(<MyPageSettingsView />);

    expect(screen.getByRole("checkbox", { name: "プロフィールを公開" })).toBeChecked();
  });

  it("ON/OFFの切り替えでis_publicを更新する", async () => {
    mocks.updateUser.mockResolvedValue(authUser({ profile: { nickname: "太郎", is_public: false } }));

    render(<MyPageSettingsView />);

    fireEvent.click(screen.getByRole("checkbox", { name: "プロフィールを公開" }));

    await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ is_public: false }));
    expect(await screen.findByText("公開設定を保存しました。")).toBeInTheDocument();
    await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("checkbox", { name: "プロフィールを公開" })).not.toBeChecked();
  });

  it("更新に失敗したら元の状態へ戻し、エラーを出す", async () => {
    mocks.updateUser.mockRejectedValue(new Error("updateUser failed: 500"));

    render(<MyPageSettingsView />);

    fireEvent.click(screen.getByRole("checkbox", { name: "プロフィールを公開" }));

    expect(
      await screen.findByText("公開設定を保存できませんでした。時間をおいて、もう一度お試しください。"),
    ).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "プロフィールを公開" })).toBeChecked();
  });

  it("is_public=trueかつusernameありなら公開プロフィールへのリンクを出す", () => {
    render(<MyPageSettingsView />);

    expect(screen.getByRole("link", { name: "/users/tarou" })).toHaveAttribute("href", "/users/tarou");
  });

  it("is_public=falseなら公開プロフィールへのリンクを出さない", () => {
    mocks.useAuth.mockReturnValue({
      user: authUser({ profile: { nickname: "太郎", is_public: false } }),
      loading: false,
      isLoggedIn: true,
      logout: mocks.logout,
      refreshMe: mocks.refreshMe,
    });

    render(<MyPageSettingsView />);

    expect(screen.queryByText("公開プロフィールページ")).toBeNull();
    expect(screen.queryByRole("link", { name: "/users/tarou" })).toBeNull();
  });

  it("ログアウトは確認ダイアログでキャンセルできる", () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);

    render(<MyPageSettingsView />);
    fireEvent.click(screen.getByRole("button", { name: "ログアウト" }));

    expect(window.confirm).toHaveBeenCalledWith("ログアウトしますか？");
    expect(mocks.logout).not.toHaveBeenCalled();
    expect(mocks.replace).not.toHaveBeenCalled();
  });

  it("確認後にログアウトして / へ遷移する", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mocks.logout.mockResolvedValue(undefined);

    render(<MyPageSettingsView />);
    fireEvent.click(screen.getByRole("button", { name: "ログアウト" }));

    await waitFor(() => expect(mocks.logout).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/"));
  });

  describe("生年月日のセルフ管理", () => {
    const CONFIRM_TEXT =
      "生年月日の登録を解除しますか？\n解除すると、コンシェルジュとコンパスで保存済みの生年月日を自動利用しなくなります。";

    function setUser(profile: AuthUser["profile"]) {
      mocks.useAuth.mockReturnValue({
        user: authUser({ profile }),
        loading: false,
        isLoggedIn: true,
        logout: mocks.logout,
        refreshMe: mocks.refreshMe,
      });
    }

    it("保存済みbirthdayを表示する", () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });

      render(<MyPageSettingsView />);

      expect(screen.getByLabelText("生年月日")).toHaveValue("1984-05-15");
      expect(screen.getByText("現在の登録：1984-05-15")).toBeInTheDocument();
      expect(screen.getByText("コンシェルジュとコンパスで共通利用します。")).toBeInTheDocument();
    });

    it("birthday未登録なら「未登録」と登録を促す説明を出し、解除ボタンを出さない", () => {
      setUser({ nickname: "太郎", is_public: true, birthday: null });

      render(<MyPageSettingsView />);

      expect(screen.getByLabelText("生年月日")).toHaveValue("");
      expect(screen.getByText("現在の登録：未登録")).toBeInTheDocument();
      expect(
        screen.getByText("登録すると、コンシェルジュとコンパスで共通利用できます。"),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "登録を解除" })).not.toBeInTheDocument();
    });

    it("変更がないうちは保存できない", () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });

      render(<MyPageSettingsView />);

      expect(screen.getByRole("button", { name: "生年月日を保存" })).toBeDisabled();
    });

    it("birthdayを変更するとupdateUserへ新しい値を渡し、保存後にrefreshMeする", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      mocks.updateUser.mockResolvedValue(
        authUser({ profile: { nickname: "太郎", is_public: true, birthday: "1990-01-02" } }),
      );

      render(<MyPageSettingsView />);

      fireEvent.change(screen.getByLabelText("生年月日"), { target: { value: "1990-01-02" } });
      fireEvent.click(screen.getByRole("button", { name: "生年月日を保存" }));

      await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: "1990-01-02" }));
      expect(await screen.findByText("生年月日を保存しました。")).toBeInTheDocument();
      await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
    });

    it("未登録から新規登録できる", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: null });
      mocks.updateUser.mockResolvedValue(
        authUser({ profile: { nickname: "太郎", is_public: true, birthday: "1990-01-02" } }),
      );

      render(<MyPageSettingsView />);

      fireEvent.change(screen.getByLabelText("生年月日"), { target: { value: "1990-01-02" } });
      fireEvent.click(screen.getByRole("button", { name: "生年月日を保存" }));

      await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: "1990-01-02" }));
    });

    it("保存に失敗したらエラーを表示する", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      mocks.updateUser.mockRejectedValue(new Error("updateUser failed: 400"));

      render(<MyPageSettingsView />);

      fireEvent.change(screen.getByLabelText("生年月日"), { target: { value: "1990-01-02" } });
      fireEvent.click(screen.getByRole("button", { name: "生年月日を保存" }));

      expect(
        await screen.findByText(
          "生年月日を保存できませんでした。入力内容を確認して、もう一度お試しください。",
        ),
      ).toBeInTheDocument();
    });

    // PATCH は成功しているので、refreshMe の失敗を「保存できませんでした」と
    // 報告すると Backend の実態と食い違う。失敗境界を分けたことを固定する。
    it("保存は成功しrefreshMeだけ失敗した場合、保存失敗として表示しない", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      mocks.updateUser.mockResolvedValue(
        authUser({ profile: { nickname: "太郎", is_public: true, birthday: "1990-01-02" } }),
      );
      mocks.refreshMe.mockRejectedValue(new Error("refreshMe failed"));

      render(<MyPageSettingsView />);

      fireEvent.change(screen.getByLabelText("生年月日"), { target: { value: "1990-01-02" } });
      fireEvent.click(screen.getByRole("button", { name: "生年月日を保存" }));

      // PATCH は実行済み
      await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: "1990-01-02" }));
      await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));

      expect(
        await screen.findByText(
          "生年月日は保存されましたが、表示の更新に失敗しました。ページを再読み込みしてください。",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          "生年月日を保存できませんでした。入力内容を確認して、もう一度お試しください。",
        ),
      ).not.toBeInTheDocument();
      // 保存は確定しているので入力値も戻さない
      expect(screen.getByLabelText("生年月日")).toHaveValue("1990-01-02");
    });

    it("解除は成功しrefreshMeだけ失敗した場合、解除失敗として表示しない", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      vi.spyOn(window, "confirm").mockReturnValue(true);
      mocks.updateUser.mockResolvedValue(
        authUser({ profile: { nickname: "太郎", is_public: true, birthday: null } }),
      );
      mocks.refreshMe.mockRejectedValue(new Error("refreshMe failed"));

      render(<MyPageSettingsView />);
      fireEvent.click(screen.getByRole("button", { name: "登録を解除" }));

      await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: null }));
      await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));

      expect(
        await screen.findByText(
          "生年月日の登録解除は完了しましたが、表示の更新に失敗しました。ページを再読み込みしてください。",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          "生年月日の登録を解除できませんでした。時間をおいて、もう一度お試しください。",
        ),
      ).not.toBeInTheDocument();
      // 解除は確定しているので入力は空のまま
      expect(screen.getByLabelText("生年月日")).toHaveValue("");
    });

    it("登録解除の確認でキャンセルするとAPIを呼ばない", () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      vi.spyOn(window, "confirm").mockReturnValue(false);

      render(<MyPageSettingsView />);
      fireEvent.click(screen.getByRole("button", { name: "登録を解除" }));

      expect(window.confirm).toHaveBeenCalledWith(CONFIRM_TEXT);
      expect(mocks.updateUser).not.toHaveBeenCalled();
      expect(mocks.refreshMe).not.toHaveBeenCalled();
    });

    it("登録解除を承認するとbirthday:nullでPATCHし、refreshMe後に未登録状態にする", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      vi.spyOn(window, "confirm").mockReturnValue(true);
      mocks.updateUser.mockResolvedValue(
        authUser({ profile: { nickname: "太郎", is_public: true, birthday: null } }),
      );
      // 「現在の登録」と解除ボタンは auth context の保存値を正本にしている。
      // 実アプリでは refreshMe() が context を更新して未登録状態になるので、
      // その更新をテストでも再現する。
      mocks.refreshMe.mockImplementation(async () => {
        setUser({ nickname: "太郎", is_public: true, birthday: null });
      });

      const { rerender } = render(<MyPageSettingsView />);
      fireEvent.click(screen.getByRole("button", { name: "登録を解除" }));

      await waitFor(() => expect(mocks.updateUser).toHaveBeenCalledWith({ birthday: null }));
      await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
      expect(await screen.findByText("生年月日の登録を解除しました。")).toBeInTheDocument();

      rerender(<MyPageSettingsView />);

      expect(screen.getByLabelText("生年月日")).toHaveValue("");
      expect(screen.getByText("現在の登録：未登録")).toBeInTheDocument();
      expect(
        screen.getByText("登録すると、コンシェルジュとコンパスで共通利用できます。"),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "登録を解除" })).not.toBeInTheDocument();
    });

    it("解除に失敗したらエラーを表示し、登録状態を保つ", async () => {
      setUser({ nickname: "太郎", is_public: true, birthday: "1984-05-15" });
      vi.spyOn(window, "confirm").mockReturnValue(true);
      mocks.updateUser.mockRejectedValue(new Error("updateUser failed: 500"));

      render(<MyPageSettingsView />);
      fireEvent.click(screen.getByRole("button", { name: "登録を解除" }));

      expect(
        await screen.findByText(
          "生年月日の登録を解除できませんでした。時間をおいて、もう一度お試しください。",
        ),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "登録を解除" })).toBeInTheDocument();
    });

    // birthday は Premium専用データではない。plan でUIを変えない。
    it.each(["free", "premium"] as const)("%s プランでも同じUIを出す", (plan) => {
      mocks.useAuth.mockReturnValue({
        user: { ...authUser({ profile: { nickname: "太郎", is_public: true, birthday: "1984-05-15" } }), plan },
        loading: false,
        isLoggedIn: true,
        logout: mocks.logout,
        refreshMe: mocks.refreshMe,
      });

      render(<MyPageSettingsView />);

      expect(screen.getByLabelText("生年月日")).toHaveValue("1984-05-15");
      expect(screen.getByRole("button", { name: "生年月日を保存" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "登録を解除" })).toBeInTheDocument();
    });

    it("Guestには編集UIを出さず、既存のlogin導線のままにする", () => {
      mocks.useAuth.mockReturnValue({
        user: null,
        loading: false,
        isLoggedIn: false,
        logout: mocks.logout,
        refreshMe: mocks.refreshMe,
      });

      render(<MyPageSettingsView />);

      expect(screen.queryByLabelText("生年月日")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "生年月日を保存" })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "登録を解除" })).not.toBeInTheDocument();
      // 既存のlogin導線は変えない
      expect(screen.getByRole("link", { name: "ログインへ" })).toBeInTheDocument();
    });
  });

  describe("アカウント削除", () => {
    const FIRST_CONFIRM =
      "アカウントを削除しますか？\n\nPremium利用中の場合は即時終了し、次回以降の請求を停止します。残りの利用期間は引き継がれず、利用者都合の削除では日割り返金はありません。";

    const FINAL_CONFIRM = "この操作は取り消せません。\n本当にアカウントを削除しますか？";

    it("アカウント削除の説明と削除ボタンを表示する", () => {
      render(<MyPageSettingsView />);

      expect(screen.getByRole("heading", { name: "アカウント削除" })).toBeInTheDocument();

      expect(screen.getByRole("button", { name: "アカウントを削除" })).toBeInTheDocument();

      expect(screen.getByText(/Premium利用中の場合は即時終了/)).toBeInTheDocument();
    });

    it("1回目の確認をキャンセルするとDELETEしない", () => {
      const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
      const fetchMock = vi.spyOn(globalThis, "fetch");

      render(<MyPageSettingsView />);

      fireEvent.click(screen.getByRole("button", { name: "アカウントを削除" }));

      expect(confirm).toHaveBeenCalledTimes(1);
      expect(confirm).toHaveBeenCalledWith(FIRST_CONFIRM);
      expect(fetchMock).not.toHaveBeenCalled();
      expect(mocks.refreshMe).not.toHaveBeenCalled();
      expect(mocks.replace).not.toHaveBeenCalled();
    });

    it("2回目の確認をキャンセルするとDELETEしない", () => {
      const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(true).mockReturnValueOnce(false);

      const fetchMock = vi.spyOn(globalThis, "fetch");

      render(<MyPageSettingsView />);

      fireEvent.click(screen.getByRole("button", { name: "アカウントを削除" }));

      expect(confirm).toHaveBeenCalledTimes(2);
      expect(confirm).toHaveBeenNthCalledWith(1, FIRST_CONFIRM);
      expect(confirm).toHaveBeenNthCalledWith(2, FINAL_CONFIRM);
      expect(fetchMock).not.toHaveBeenCalled();
      expect(mocks.refreshMe).not.toHaveBeenCalled();
      expect(mocks.replace).not.toHaveBeenCalled();
    });

    it("二重確認後にDELETEし、204なら認証状態を再同期してトップへ遷移する", async () => {
      vi.spyOn(window, "confirm").mockReturnValue(true);

      const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));

      mocks.refreshMe.mockResolvedValue(undefined);

      render(<MyPageSettingsView />);

      fireEvent.click(screen.getByRole("button", { name: "アカウントを削除" }));

      await waitFor(() =>
        expect(fetchMock).toHaveBeenCalledWith("/api/users/me/", {
          method: "DELETE",
          credentials: "same-origin",
          cache: "no-store",
        }),
      );

      await waitFor(() => expect(mocks.refreshMe).toHaveBeenCalledTimes(1));
      await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/"));
    });

    it("Backendが204以外なら削除完了扱いにせずエラーを表示する", async () => {
      vi.spyOn(window, "confirm").mockReturnValue(true);

      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "account_deletion_unavailable",
            detail: "failed",
          }),
          {
            status: 503,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );

      render(<MyPageSettingsView />);

      fireEvent.click(screen.getByRole("button", { name: "アカウントを削除" }));

      expect(
        await screen.findByText("アカウントを削除できませんでした。時間をおいて、もう一度お試しください。"),
      ).toBeInTheDocument();

      expect(mocks.refreshMe).not.toHaveBeenCalled();
      expect(mocks.replace).not.toHaveBeenCalled();
    });

    it("通信失敗時も削除完了扱いにせずエラーを表示する", async () => {
      vi.spyOn(window, "confirm").mockReturnValue(true);

      vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network error"));

      render(<MyPageSettingsView />);

      fireEvent.click(screen.getByRole("button", { name: "アカウントを削除" }));

      expect(
        await screen.findByText("アカウントを削除できませんでした。時間をおいて、もう一度お試しください。"),
      ).toBeInTheDocument();

      expect(mocks.refreshMe).not.toHaveBeenCalled();
      expect(mocks.replace).not.toHaveBeenCalled();
    });
  });

  it("未実装の設定placeholderは置かない", () => {
    render(<MyPageSettingsView />);

    for (const label of ["メールアドレスを変更", "パスワードを変更", "通知設定", "プランを管理"]) {
      expect(screen.queryByText(label)).toBeNull();
    }
  });
});
