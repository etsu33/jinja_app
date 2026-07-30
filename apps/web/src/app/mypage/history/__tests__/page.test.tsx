import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const getConciergeThreadsServerMock = vi.fn();

vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadsServer: getConciergeThreadsServerMock,
}));

vi.mock("@/components/views/ConsultationHistoryListView", () => ({
  default: ({ initialThreads, fetchFailed }: { initialThreads: unknown[]; fetchFailed: boolean }) => (
    <div data-testid="view" data-fetch-failed={String(fetchFailed)} data-count={initialThreads.length} />
  ),
}));

describe("ConsultationHistoryListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("正常系: 取得したthreadsをそのままViewへ渡す", async () => {
    getConciergeThreadsServerMock.mockResolvedValue([
      { id: 1, title: "相談A", last_message: "", last_message_at: null, message_count: 1 },
    ]);

    const { default: Page } = await import("../page");
    const element = await Page();
    render(element);

    const view = screen.getByTestId("view");
    expect(view).toHaveAttribute("data-fetch-failed", "false");
    expect(view).toHaveAttribute("data-count", "1");
  });

  it("Error: getConciergeThreadsServerが例外を投げたときfetchFailed=trueをViewへ渡す", async () => {
    getConciergeThreadsServerMock.mockRejectedValue(new Error("getConciergeThreadsServer failed: 500"));

    const { default: Page } = await import("../page");
    const element = await Page();
    render(element);

    const view = screen.getByTestId("view");
    expect(view).toHaveAttribute("data-fetch-failed", "true");
    expect(view).toHaveAttribute("data-count", "0");
  });
});
