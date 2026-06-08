import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import ShrinesPage from "../page";
import { fetchShrines } from "@/lib/api/shrinesSearch";
import { getGoriyakuTags } from "@/lib/api/tags";

const pushMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
  useSearchParams: () => new URLSearchParams(window.location.search),
  usePathname: () => "/shrines",
}));

vi.mock("@/lib/api/shrinesSearch", () => ({
  fetchShrines: vi.fn(),
}));

vi.mock("@/lib/api/tags", () => ({
  getGoriyakuTags: vi.fn(),
}));

vi.mock("@/lib/shrine/buildShrineListCardModel", () => ({
  buildShrineListCardModel: (shrine: { id: number; name_jp: string; address?: string | null }) => ({
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
const mockedGetGoriyakuTags = vi.mocked(getGoriyakuTags);

describe("/shrines page", () => {
  const originalWindowLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetGoriyakuTags.mockResolvedValue([]);

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

  it("submitted=1 & status=pending なら公開準備中メッセージだけを表示する", async () => {
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
      expect(screen.getByText("「未登録テスト神社20260419」の投稿を受け付けました")).toBeInTheDocument();
      expect(
        screen.getByText("現在公開準備中です。確認が完了するまで公開検索には表示されません。"),
      ).toBeInTheDocument();
      expect(screen.getByText("ご利益タグなどの内容は確認時の参考情報として扱います。")).toBeInTheDocument();
    });

    expect(mockedFetchShrines).not.toHaveBeenCalled();
    expect(screen.queryByText("神田神社（神田明神）")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "神社を探すへ戻る" })).toBeInTheDocument();
  });

  it("投稿完了後に神社を探すへ戻れる", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalWindowLocation,
        search:
          "?submitted=1&status=pending&name=%E6%9C%AA%E7%99%BB%E9%8C%B2%E3%83%86%E3%82%B9%E3%83%88%E7%A5%9E%E7%A4%BE20260419",
      },
    });

    render(<ShrinesPage />);

    const button = await screen.findByRole("button", { name: "神社を探すへ戻る" });
    fireEvent.click(button);

    expect(pushMock).toHaveBeenCalledWith("/shrines");
  });

  it("検索語を入力して検索すると検索URLへ遷移する", async () => {
    render(<ShrinesPage />);

    fireEvent.change(screen.getByPlaceholderText("神社名や願いごとを、そっと入力"), {
      target: { value: "稲荷" },
    });

    fireEvent.click(screen.getByRole("button", { name: "ひらく" }));

    expect(pushMock).toHaveBeenCalledWith("/shrines?q=%E7%A8%B2%E8%8D%B7");
  });

  it("ご利益タグを表示し、クリックするとタグ名で検索URLへ遷移する", async () => {
    mockedGetGoriyakuTags.mockResolvedValue([
      { id: 1, name: "縁結び" },
      { id: 5, name: "金運・商売繁盛" },
    ]);

    render(<ShrinesPage />);

    expect(await screen.findByText("TAGS")).toBeInTheDocument();

    const tagButton = await screen.findByRole("button", { name: "縁結び" });
    fireEvent.click(tagButton);

    expect(pushMock).toHaveBeenCalledWith("/shrines?q=%E7%B8%81%E7%B5%90%E3%81%B3");
  });
});
