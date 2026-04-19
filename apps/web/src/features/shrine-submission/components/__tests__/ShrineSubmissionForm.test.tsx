import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ShrineSubmissionForm } from "../ShrineSubmissionForm";
import { createShrineSubmission } from "@/lib/api/shrineSubmissions";
import { fetchShrines } from "@/lib/api/shrinesSearch";

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

vi.mock("@/lib/api/shrinesSearch", () => ({
  fetchShrines: vi.fn(),
}));

vi.mock("@/lib/api/errors", () => ({
  isApiError: (err: unknown) => {
    return Boolean(err) && typeof err === "object" && "status" in (err as Record<string, unknown>);
  },
}));

const mockedCreateShrineSubmission = vi.mocked(createShrineSubmission);
const mockedFetchShrines = vi.mocked(fetchShrines);

describe("ShrineSubmissionForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchShrines.mockResolvedValue({ results: [], count: 0 });
  });

  it("duplicate_candidate を受けたら候補表示UIを出し、1件時は詳細導線を出す", async () => {
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
    expect(screen.getByText("神田神社（神田明神）")).toBeInTheDocument();
    expect(screen.getByText("東京都千代田区外神田2-16-2")).toBeInTheDocument();

    const detailButton = screen.getByRole("button", { name: "既存神社の詳細を見る" });
    expect(detailButton).toBeInTheDocument();

    fireEvent.click(detailButton);
    expect(pushMock).toHaveBeenCalledWith("/shrines/23");
  });
});
