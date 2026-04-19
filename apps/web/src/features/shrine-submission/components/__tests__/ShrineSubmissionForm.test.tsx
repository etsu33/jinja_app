import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ShrineSubmissionForm } from "../ShrineSubmissionForm";
import { createShrineSubmission } from "@/lib/api/shrineSubmissions";
import { fetchShrineSuggest } from "@/lib/api/shrinesSuggest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
  }),
}));

vi.mock("@/lib/api/tags", () => ({
  getGoriyakuTags: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/lib/api/shrineSubmissions", () => ({
  createShrineSubmission: vi.fn(),
}));

vi.mock("@/lib/api/shrinesSuggest", () => ({
  fetchShrineSuggest: vi.fn(),
}));

vi.mock("@/lib/api/errors", () => ({
  isApiError: (err: unknown) => {
    return Boolean(err) && typeof err === "object" && "status" in (err as Record<string, unknown>);
  },
}));

const mockedCreateShrineSubmission = vi.mocked(createShrineSubmission);
const mockedFetchShrineSuggest = vi.mocked(fetchShrineSuggest);

describe("ShrineSubmissionForm", () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    mockedFetchShrineSuggest.mockResolvedValue({ results: [], count: 0 });
  });

  it("name suggest が 1 件なら詳細導線を優先して出す", async () => {
    mockedFetchShrineSuggest.mockResolvedValueOnce({
      count: 1,
      results: [
        {
          id: 23,
          name: "神田神社（神田明神）",
          address: "東京都千代田区外神田2-16-2",
        },
      ],
    });

    render(
      <ShrineSubmissionForm
        onSubmitted={vi.fn()}
        onRequireAuth={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "神田神社" },
    });

    await waitFor(() => {
      expect(mockedFetchShrineSuggest).toHaveBeenCalledWith("神田神社");
    });

    expect(await screen.findByText("既存の神社候補")).toBeInTheDocument();
    expect(screen.getByText("入力補助です。重複判定は投稿時に行われます。")).toBeInTheDocument();

    const detailButton = screen.getByRole("button", { name: "既存の神社を見る" });
    fireEvent.click(detailButton);

    expect(pushMock).toHaveBeenCalledWith("/shrines/23");
  });

  it("name suggest が複数件なら一覧導線を優先して出す", async () => {
    mockedFetchShrineSuggest.mockResolvedValueOnce({
      count: 2,
      results: [
        {
          id: 23,
          name: "神田神社（神田明神）",
          address: "東京都千代田区外神田2-16-2",
        },
        {
          id: 24,
          name: "神田神社",
          address: "東京都千代田区神田1-2-3",
        },
      ],
    });

    render(
      <ShrineSubmissionForm
        onSubmitted={vi.fn()}
        onRequireAuth={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "神田神社" },
    });

    const listButton = await screen.findByRole("button", { name: "候補を一覧で見る" });
    fireEvent.click(listButton);

    expect(pushMock).toHaveBeenCalledWith("/shrines?q=%E7%A5%9E%E7%94%B0%E7%A5%9E%E7%A4%BE");
  });

  it("duplicate_candidate を受けたら suggestion より優先して候補表示UIを出し、編集で解除する", async () => {
    mockedFetchShrineSuggest.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 23,
          name: "神田神社（神田明神）",
          address: "東京都千代田区外神田2-16-2",
        },
      ],
    });

    mockedCreateShrineSubmission.mockRejectedValue({
      status: 400,
      body: {
        code: "duplicate_candidate",
        message: "この神社はすでに登録されている可能性があります。",
        candidates: [
          {
            id: 23,
            name: "神田神社（神田明神）",
            address: "東京都千代田区外神田2-16-2",
          },
        ],
      },
    });

    render(
      <ShrineSubmissionForm
        onSubmitted={vi.fn()}
        onRequireAuth={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "神田神社（神田明神）" },
    });
    expect(await screen.findByText("既存の神社候補")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("住所"), {
      target: { value: "東京都千代田区外神田2-16-2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "審査用に投稿する" }));

    await waitFor(() => {
      expect(mockedCreateShrineSubmission).toHaveBeenCalled();
    });

    expect(
      screen.getByText("この神社はすでに登録されている可能性があります。"),
    ).toBeInTheDocument();
    expect(screen.getByText("既存の神社をご確認ください。")).toBeInTheDocument();
    expect(screen.queryByText("入力補助です。重複判定は投稿時に行われます。")).not.toBeInTheDocument();
    expect(screen.getByText("神田神社（神田明神）")).toBeInTheDocument();
    expect(screen.getByText("東京都千代田区外神田2-16-2")).toBeInTheDocument();

    const detailButton = screen.getByRole("button", { name: "既存神社の詳細を見る" });
    expect(detailButton).toBeInTheDocument();

    fireEvent.click(detailButton);
    expect(pushMock).toHaveBeenCalledWith("/shrines/23");

    fireEvent.change(screen.getByLabelText("住所"), {
      target: { value: "東京都千代田区外神田2-16-3" },
    });

    expect(screen.queryByText("既存の神社をご確認ください。")).not.toBeInTheDocument();

    expect(await screen.findByText("入力補助です。重複判定は投稿時に行われます。")).toBeInTheDocument();
  });
});
