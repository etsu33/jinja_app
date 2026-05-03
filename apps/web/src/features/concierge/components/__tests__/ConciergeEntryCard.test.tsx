

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ConciergeEntryCard from "../ConciergeEntryCard";

describe("ConciergeEntryCard", () => {
  const baseProps = {
    displayName: null,
    displayLabel: "エツコ",
    sessionState: { sessionNickname: null },
    setSessionNickname: vi.fn(),
    canSaveConciergeThread: true,
    isUiPaywall: false,
    redirectToAuth: vi.fn(),
    needText: "",
    setNeedText: vi.fn(),
    feelExamples: [
      { label: "金運", text: "金運を整えたい" },
      { label: "切り替え", text: "気持ちを切り替えたい" },
    ],
    onPickExample: vi.fn(),
    isBusy: false,
    canSend: true,
    onSubmit: vi.fn(),
    onClear: vi.fn(),
  };

  it("renders the entry copy, input prompt, examples, and primary CTA", () => {
    render(<ConciergeEntryCard {...baseProps} needText="金運を整えたい" />);

    expect(screen.getByText("神社コンシェルジュ")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "今の気持ちに合う神社を見つける" })).toBeInTheDocument();
    expect(screen.getByText("今の状態をもとに、行き先の候補を静かに整理します。")).toBeInTheDocument();
    expect(screen.getByLabelText("今、何に迷っていますか？")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("例：金運を整えたい、気持ちを切り替えたい、静かな場所で参拝したい")).toBeInTheDocument();
    expect(screen.getByText("迷ったら選んでください")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "金運" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "切り替え" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "今の気持ちに合う神社を探す" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "クリア" })).toBeEnabled();
  });

  it("calls handlers for nickname, textarea, example, submit, and clear", () => {
    const setSessionNickname = vi.fn();
    const setNeedText = vi.fn();
    const onPickExample = vi.fn();
    const onSubmit = vi.fn();
    const onClear = vi.fn();

    render(
      <ConciergeEntryCard
        {...baseProps}
        needText="金運を整えたい"
        setSessionNickname={setSessionNickname}
        setNeedText={setNeedText}
        onPickExample={onPickExample}
        onSubmit={onSubmit}
        onClear={onClear}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("例: えつこ"), { target: { value: "えつこ" } });
    fireEvent.change(screen.getByLabelText("今、何に迷っていますか？"), { target: { value: "静かな場所に行きたい" } });
    fireEvent.click(screen.getByRole("button", { name: "切り替え" }));
    fireEvent.click(screen.getByRole("button", { name: "今の気持ちに合う神社を探す" }));
    fireEvent.click(screen.getByRole("button", { name: "クリア" }));

    expect(setSessionNickname).toHaveBeenCalledWith("えつこ");
    expect(setNeedText).toHaveBeenCalledWith("静かな場所に行きたい");
    expect(onPickExample).toHaveBeenCalledWith("気持ちを切り替えたい");
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("shows auth actions when saving requires login", () => {
    const redirectToAuth = vi.fn();

    render(<ConciergeEntryCard {...baseProps} canSaveConciergeThread={false} redirectToAuth={redirectToAuth} />);

    expect(screen.getByText("未ログインでも検索できます。保存にはログインが必要です。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));
    fireEvent.click(screen.getByRole("button", { name: "新規登録" }));

    expect(redirectToAuth).toHaveBeenCalledWith("login");
    expect(redirectToAuth).toHaveBeenCalledWith("register");
  });
});
