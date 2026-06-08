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

    render(<ShrineSubmissionForm onSubmitted={vi.fn()} onRequireAuth={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "神田神社" },
    });

    await waitFor(() => {
      expect(mockedFetchShrineSuggest).toHaveBeenCalledWith("神田神社");
    });

    expect(await screen.findByText("既存の神社候補")).toBeInTheDocument();
    expect(
      screen.getByText(
        "同じ名前でも場所が違う神社があります。住所が近いか確認してください。違う神社なら、そのまま投稿できます。",
      ),
    ).toBeInTheDocument();

    const detailButton = screen.getByRole("button", { name: "この神社と同じか確認する" });
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

    render(<ShrineSubmissionForm onSubmitted={vi.fn()} onRequireAuth={vi.fn()} />);

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

    render(<ShrineSubmissionForm onSubmitted={vi.fn()} onRequireAuth={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "神田神社（神田明神）" },
    });
    expect(await screen.findByText("既存の神社候補")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/住所/), {
      target: { value: "東京都千代田区外神田2-16-2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "神社を追加する" }));

    await waitFor(() => {
      expect(mockedCreateShrineSubmission).toHaveBeenCalled();
    });

    expect(screen.getByText("この神社はすでに登録されている可能性があります。")).toBeInTheDocument();
    expect(screen.getByText("同じ神社がすでに登録されている場合、追加投稿は不要です。")).toBeInTheDocument();
    expect(
      screen.queryByText("同じ名前でも場所が違う神社があります。住所が近いか確認してください。違う神社なら、そのまま投稿できます。"),
    ).not.toBeInTheDocument();
    expect(screen.getByText("神田神社（神田明神）")).toBeInTheDocument();
    expect(screen.getByText("東京都千代田区外神田2-16-2")).toBeInTheDocument();
    expect(screen.getByText("住所が一致する場合は、既存の神社の可能性が高いです。")).toBeInTheDocument();

    const detailButton = screen.getByRole("button", { name: "既存神社の詳細を見る" });
    expect(detailButton).toBeInTheDocument();

    fireEvent.click(detailButton);
    expect(pushMock).toHaveBeenCalledWith("/shrines/23");

    fireEvent.change(screen.getByLabelText(/住所/), {
      target: { value: "東京都千代田区外神田2-16-3" },
    });

    expect(screen.queryByText("同じ神社がすでに登録されている場合、追加投稿は不要です。")).not.toBeInTheDocument();

    expect(
      await screen.findByText("同じ名前でも場所が違う神社があります。住所が近いか確認してください。違う神社なら、そのまま投稿できます。"),
    ).toBeInTheDocument();
  });

  it("duplicate_candidate が複数件なら複数候補UI を表示し、一覧導線を優先する", async () => {
    const onSubmitted = vi.fn();

    mockedCreateShrineSubmission.mockRejectedValue({
      status: 400,
      body: {
        code: "duplicate_candidate",
        message: "この神社はすでに登録されている可能性があります。",
        candidates: [
          {
            id: 101,
            name: "複数候補神社",
            address: "東京都複数1区1-1-1",
          },
          {
            id: 102,
            name: "複数候補神社",
            address: "東京都複数2区2-2-2",
          },
        ],
      },
    });

    render(<ShrineSubmissionForm onSubmitted={onSubmitted} onRequireAuth={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "複数候補神社" },
    });
    fireEvent.change(screen.getByLabelText(/住所/), {
      target: { value: "東京都新規区3-3-3" },
    });

    fireEvent.click(screen.getByRole("button", { name: "神社を追加する" }));

    await waitFor(() => {
      expect(mockedCreateShrineSubmission).toHaveBeenCalled();
    });

    // 重複メッセージが表示される
    expect(await screen.findByText("この神社はすでに登録されている可能性があります。")).toBeInTheDocument();
    expect(screen.getByText("同じ神社がすでに登録されている場合、追加投稿は不要です。")).toBeInTheDocument();

    // 複数候補の場合は各候補が個別に表示される
    // 複数候補の場合、複数候補神社 というテキストは複数存在する（各候補の名前として）
    const candidateNames = screen.getAllByText("複数候補神社");
    expect(candidateNames.length).toBe(2);
    expect(screen.getByText("東京都複数1区1-1-1")).toBeInTheDocument();
    expect(screen.getByText("東京都複数2区2-2-2")).toBeInTheDocument();
    expect(screen.getAllByText("住所が一致する場合は、既存の神社の可能性が高いです。").length).toBe(2);

    // 複数件なので "候補一覧を見る" ボタンが表示される
    const listButton = screen.getByRole("button", { name: "候補一覧を見る" });
    expect(listButton).toBeInTheDocument();

    // "既存神社の詳細を見る" ボタンは表示されない
    expect(screen.queryByRole("button", { name: "既存神社の詳細を見る" })).not.toBeInTheDocument();

    // 一覧ボタンをクリック
    fireEvent.click(listButton);
    expect(pushMock).toHaveBeenCalledWith("/shrines?q=%E8%A4%87%E6%95%B0%E5%80%99%E8%A3%9C%E7%A5%9E%E7%A4%BE");

    // submit callback は呼ばれない
    expect(onSubmitted).not.toHaveBeenCalled();

    // 編集で候補を解除できる
    fireEvent.change(screen.getByLabelText("神社名"), {
      target: { value: "新規神社" },
    });

    expect(screen.queryByText("同じ神社がすでに登録されている場合、追加投稿は不要です。")).not.toBeInTheDocument();
  });
});
