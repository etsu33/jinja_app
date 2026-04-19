import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import ShrinesPage from "../page";
import { fetchShrines } from "@/lib/api/shrinesSearch";

const pushMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
  usePathname: () => "/shrines",
}));

vi.mock("@/lib/api/shrinesSearch", () => ({
  fetchShrines: vi.fn(),
}));

vi.mock("@/lib/shrine/buildShrineListCardModel", () => ({
  buildShrineListCardModel: (shrine: {
    id: number;
    name_jp: string;
    address?: string | null;
  }) => ({
    shrineId: shrine.id,
    title: shrine.name_jp,
    address: shrine.address ?? null,
    description: null,
    imageUrl: null,
    badges: [],
  }),
}));

vi.mock("@/components/shrines/ShrineCard", () => ({
  ShrineCard: ({ name }: { name: string }) => <div>{name}</div>,
}));

const mockedFetchShrines = vi.mocked(fetchShrines);

describe("/shrines page", () => {
  const originalWindowLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search: "",
      },
    });
  });

  it("qありで0件ならCTAを表示する", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search: "?q=%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      },
    });

    mockedFetchShrines.mockResolvedValue({
      results: [],
      count: 0,
    });

    render(<ShrinesPage />);

    await waitFor(() => {
      expect(mockedFetchShrines).toHaveBeenCalledWith({
        q: "未登録テスト神社20260419",
      });
    });

    expect(await screen.findByText("お探しの神社が見つかりませんか？")).toBeInTheDocument();

    const cta = await screen.findByRole("button", { name: "神社を追加する" });
    expect(cta).toBeInTheDocument();

    fireEvent.click(cta);

    expect(pushMock).toHaveBeenCalledWith(
      "/shrines/new?returnTo=%2Fshrines%3Fq%3D%25E6%259C%25AA%25E7%2599%25BB%25E9%258C%25B2%25E3%2583%2586%25E3%2582%25B9%25E3%2583%2588%25E7%25A5%259E%25E7%25A4%25BE20260419",
    );
  });

  it("submitted=1 & status=pending なら審査中メッセージを表示する", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search:
          "?submitted=1&status=pending&name=%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      },
    });

    mockedFetchShrines.mockResolvedValue({
      results: [
        {
          id: 23,
          name_jp: "神田神社（神田明神）",
          address: "東京都千代田区外神田2-16-2",
        } as never,
      ],
      count: 1,
    });

    render(<ShrinesPage />);

    await waitFor(() => {
      expect(mockedFetchShrines).toHaveBeenCalled();
    });

    expect(
      await screen.findByText("「未登録テスト神社20260419」の投稿を受け付けました。現在審査中です。"),
    ).toBeInTheDocument();
  });
});
