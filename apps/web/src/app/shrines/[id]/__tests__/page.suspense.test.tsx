// /shrines/[id] の Suspense 境界の構造テスト。
// Page 自体は await せずに Suspense を返し、fallback は Route loading と同じ skeleton、
// server fetch はすべて境界内の content が行う（docs/audit/shrine-detail-transition-flash.md）。
import { Suspense, type ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction: vi.fn().mockResolvedValue(undefined) }));

const getShrineDetailServerMock = vi.fn();
vi.mock("@/lib/api/shrines.server", () => ({
  getShrineDetailServer: (...args: unknown[]) => getShrineDetailServerMock(...args),
}));

const getConciergeThreadServerMock = vi.fn();
vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadServer: (...args: unknown[]) => getConciergeThreadServerMock(...args),
  getConciergeThreadsServer: vi.fn().mockResolvedValue([]),
}));

const getBillingStatusServerMock = vi.fn().mockResolvedValue({ plan: "free", is_active: false });
vi.mock("@/lib/api/billing.server", () => ({
  getBillingStatusServer: (...args: unknown[]) => getBillingStatusServerMock(...args),
}));
vi.mock("@/lib/api/publicGoshuins.server", () => ({
  fetchPublicGoshuinsForShrineServer: vi.fn().mockResolvedValue([]),
}));
vi.mock("@/lib/server/favorites.server", () => ({
  getShrineFavoriteInitialState: vi.fn().mockResolvedValue({ fav: false, favorite_id: null, guestMode: true }),
}));
vi.mock("@/lib/api/shrineMeaning.server", () => ({
  fetchShrineMeaningPayloadV2Server: vi.fn().mockResolvedValue(null),
}));
vi.mock("@/lib/shrine/buildShrineDetailModel", () => ({
  buildShrineDetailModel: vi.fn().mockReturnValue({}),
}));
vi.mock("@/components/shrine/detail/ShrineDetailArticle", () => ({
  default: () => <div data-testid="shrine-detail-article-stub" />,
}));

type BoundaryProps = { fallback: ReactElement; children: ReactElement<Record<string, unknown>> };

async function callPage(id: string, searchParams: Record<string, string> = {}) {
  const { default: Page } = await import("../page");
  const props = { params: Promise.resolve({ id }), searchParams: Promise.resolve(searchParams) };
  const boundary = Page(props) as ReactElement<BoundaryProps>;
  return { props, boundary };
}

async function renderContent(boundary: ReactElement<BoundaryProps>) {
  const content = boundary.props.children;
  const render_ = content.type as (p: Record<string, unknown>) => Promise<ReactElement>;
  render(await render_(content.props));
}

describe("/shrines/[id] Suspense boundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getShrineDetailServerMock.mockResolvedValue({
      id: 42,
      name_jp: "検証神社",
      latitude: 35.0,
      longitude: 139.0,
      goriyaku_tags: [],
      goriyaku: null,
    });
  });

  it("Page は Promise ではなく Suspense 要素を同期で返し、fallback は Route loading と同じ skeleton", async () => {
    const { boundary } = await callPage("42");
    const { default: ShrineDetailLoading } = await import("../loading");

    expect(boundary).not.toBeInstanceOf(Promise);
    expect(boundary.type).toBe(Suspense);
    expect(boundary.props.fallback.type).toBe(ShrineDetailLoading);
  });

  it("Page 呼び出し時点では server fetch を行わず、params / searchParams をそのまま境界内へ渡す", async () => {
    const { props, boundary } = await callPage("42", { ctx: "concierge", tid: "768" });

    expect(getShrineDetailServerMock).not.toHaveBeenCalled();
    expect(getBillingStatusServerMock).not.toHaveBeenCalled();
    expect(getConciergeThreadServerMock).not.toHaveBeenCalled();
    expect(boundary.props.children.props.params).toBe(props.params);
    expect(boundary.props.children.props.searchParams).toBe(props.searchParams);
  });

  it("fallback の skeleton は読み込み中の status を1つだけ描画する", async () => {
    const { boundary } = await callPage("42");
    render(boundary.props.fallback);

    expect(screen.getByRole("status")).toHaveTextContent("神社の情報を読み込み中です");
  });

  it("境界内 content: 不正IDは従来どおりの表示で、server fetch を行わない", async () => {
    const { boundary } = await callPage("abc");
    await renderContent(boundary);

    expect(screen.getByText("不正な神社IDです。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "← 地図に戻る" })).toHaveAttribute("href", "/map");
    expect(getShrineDetailServerMock).not.toHaveBeenCalled();
  });

  it("境界内 content: shrine 取得失敗は従来どおりの not-found Shell を返す", async () => {
    getShrineDetailServerMock.mockRejectedValue(new Error("boom"));
    const { boundary } = await callPage("42");
    await renderContent(boundary);

    expect(screen.getByText("神社の詳細情報が見つかりませんでした。")).toBeInTheDocument();
    expect(screen.queryByTestId("shrine-detail-article-stub")).toBeNull();
  });

  it("境界内 content: 正常時は Shell と Article を描画する", async () => {
    const { boundary } = await callPage("42");
    await renderContent(boundary);

    expect(screen.getByTestId("shrine-detail-article-stub")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Googleマップで経路案内" })).toBeInTheDocument();
  });
});
