import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const getConciergeThreadServerMock = vi.fn();

vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadServer: getConciergeThreadServerMock,
}));

vi.mock("@/components/views/ConsultationHistoryDetailView", () => ({
  default: ({ tid, thread, fetchFailed }: { tid: string; thread: unknown; fetchFailed: boolean }) => (
    <div
      data-testid="view"
      data-tid={tid}
      data-has-thread={String(thread != null)}
      data-fetch-failed={String(fetchFailed)}
    />
  ),
}));

describe("ConsultationHistoryDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("正常系: 取得したthreadをそのままViewへ渡す", async () => {
    getConciergeThreadServerMock.mockResolvedValue({
      id: 42,
      title: "相談A",
      last_message: "",
      last_message_at: null,
      message_count: 0,
      messages: [],
    });

    const { default: Page } = await import("../page");
    const element = await Page({ params: Promise.resolve({ tid: "42" }) });
    render(element);

    const view = screen.getByTestId("view");
    expect(view).toHaveAttribute("data-tid", "42");
    expect(view).toHaveAttribute("data-has-thread", "true");
    expect(view).toHaveAttribute("data-fetch-failed", "false");
  });

  it("Direct Navigation: 不正または存在しないtidはthread=nullをViewへ渡す", async () => {
    getConciergeThreadServerMock.mockResolvedValue(null);

    const { default: Page } = await import("../page");
    const element = await Page({ params: Promise.resolve({ tid: "999" }) });
    render(element);

    const view = screen.getByTestId("view");
    expect(view).toHaveAttribute("data-has-thread", "false");
    expect(view).toHaveAttribute("data-fetch-failed", "false");
  });

  it("Error: getConciergeThreadServerが例外を投げたときfetchFailed=trueをViewへ渡す", async () => {
    getConciergeThreadServerMock.mockRejectedValue(new Error("getConciergeThreadServer failed: 500"));

    const { default: Page } = await import("../page");
    const element = await Page({ params: Promise.resolve({ tid: "42" }) });
    render(element);

    const view = screen.getByTestId("view");
    expect(view).toHaveAttribute("data-fetch-failed", "true");
  });
});
