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
      { label: "仕事について考えたい", text: "仕事や働き方について、今の流れを整理したいです" },
      { label: "少し休みたい", text: "最近少し疲れていて、気持ちを落ち着ける時間がほしいです" },
    ],
    onPickExample: vi.fn(),
    isBusy: false,
    canSend: true,
    onSubmit: vi.fn(),
    onClear: vi.fn(),
  };

  it("renders the entry copy, input prompt, examples, and primary CTA", () => {
    render(<ConciergeEntryCard {...baseProps} needText="仕事や働き方について、今の流れを整理したいです" />);

    expect(screen.getByText("KAMI MUSUBI GUIDE")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "相談から、向かう神社を見つける" })).toBeInTheDocument();
    expect(screen.getByText("相談をもとに、今向かいやすい神社との出会いを整えます。")).toBeInTheDocument();
    expect(screen.getByLabelText("必要なら、今の状況を少しだけ書く")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("例: 仕事の迷いを整理したい、少し休みたい")).toBeInTheDocument();
    expect(screen.getByText("相談テーマ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "仕事について考えたい" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "少し休みたい" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "この相談で神社を提案してもらう" })).toBeEnabled();
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
        needText="仕事や働き方について、今の流れを整理したいです"
        setSessionNickname={setSessionNickname}
        setNeedText={setNeedText}
        onPickExample={onPickExample}
        onSubmit={onSubmit}
        onClear={onClear}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("例: なまえ"), { target: { value: "なまえ" } });
    fireEvent.change(screen.getByLabelText("必要なら、今の状況を少しだけ書く"), { target: { value: "静かな場所に行きたい" } });
    fireEvent.click(screen.getByRole("button", { name: "少し休みたい" }));
    fireEvent.click(screen.getByRole("button", { name: "この相談で神社を提案してもらう" }));
    fireEvent.click(screen.getByRole("button", { name: "クリア" }));

    expect(setSessionNickname).toHaveBeenCalledWith("なまえ");
    expect(setNeedText).toHaveBeenCalledWith("静かな場所に行きたい");
    expect(onPickExample).toHaveBeenCalledWith({ label: "少し休みたい", text: "最近少し疲れていて、気持ちを落ち着ける時間がほしいです" });
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("shows auth actions when saving requires login", () => {
    const redirectToAuth = vi.fn();

    render(<ConciergeEntryCard {...baseProps} canSaveConciergeThread={false} redirectToAuth={redirectToAuth} />);

    expect(screen.getByText("未ログインでも相談できます。保存にはログインが必要です。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));
    fireEvent.click(screen.getByRole("button", { name: "新規登録" }));

    expect(redirectToAuth).toHaveBeenCalledWith("login");
    expect(redirectToAuth).toHaveBeenCalledWith("register");
  });
});
