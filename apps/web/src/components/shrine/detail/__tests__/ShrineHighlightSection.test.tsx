import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { trackSearchEvent } = vi.hoisted(() => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent }));

import ShrineFactSection from "../ShrineFactSection";
import ShrineHighlightSection from "../ShrineHighlightSection";
import type { DetailFactSection, DetailHighlightItem, DetailHighlightSection } from "../types";

function item(overrides: Partial<DetailHighlightItem> = {}): DetailHighlightItem {
  return {
    id: 7,
    categoryLabel: "建築",
    name: "拝殿の彫刻",
    description: "正面上部の龍の彫刻を見る。",
    historicalConnection: "",
    locationHint: "",
    linkedHistories: [],
    sources: [],
    observedOnLabel: null,
    ...overrides,
  };
}

function section(items: DetailHighlightItem[]): DetailHighlightSection {
  return { kind: "highlight", heading: "ここで見られるもの", items };
}

describe("ShrineHighlightSection", () => {
  const originalObserver = globalThis.IntersectionObserver;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    globalThis.IntersectionObserver = originalObserver;
  });

  it("見どころが無ければ何も出さない", () => {
    const { container } = render(<ShrineHighlightSection section={section([])} />);
    expect(container.firstChild).toBeNull();
  });

  it("名前・カテゴリー・場所の目安・説明・伝える歴史・現地確認・出典を出す", () => {
    render(
      <ShrineHighlightSection
        section={section([
          item({
            locationHint: "鳥居をくぐって正面",
            historicalConnection: "再建のときに彫られた。",
            observedOnLabel: "2026年11月21日",
            sources: [
              {
                id: 1,
                source_type: "shrine_official",
                title: "公式サイト",
                publisher: "",
                url: "https://example.com",
                verification_status: "source_confirmed",
                confidence: "",
              },
            ],
          }),
        ])}
      />,
    );
    expect(screen.getByRole("heading", { name: "ここで見られるもの" })).toBeInTheDocument();
    expect(screen.getByText("建築")).toBeInTheDocument();
    expect(screen.getByText("拝殿の彫刻")).toBeInTheDocument();
    expect(screen.getByText("鳥居をくぐって正面")).toBeInTheDocument();
    expect(screen.getByText("正面上部の龍の彫刻を見る。")).toBeInTheDocument();
    expect(screen.getByText("この見どころが伝える歴史")).toBeInTheDocument();
    expect(screen.getByText("再建のときに彫られた。")).toBeInTheDocument();
    expect(screen.getByText("2026年11月21日に現地で確認")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "公式サイト" })).toHaveAttribute("href", "https://example.com");
  });

  it("出典は「出典（N件）」の折りたたみで出し、最初は閉じている", () => {
    const sources = [1, 2].map((id) => ({
      id,
      source_type: "shrine_official",
      title: `公式サイト${id}`,
      publisher: "",
      url: `https://example.com/${id}`,
      verification_status: "source_confirmed",
      confidence: "",
    }));
    render(<ShrineHighlightSection section={section([item({ sources })])} />);
    const summary = screen.getByText("出典（2件）");
    const details = summary.closest("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");
    expect(details?.querySelectorAll("a")).toHaveLength(2);
    expect(screen.queryByRole("heading", { name: "出典" })).not.toBeInTheDocument();
  });

  it("空の項目は見出しごと出さない", () => {
    render(<ShrineHighlightSection section={section([item()])} />);
    expect(screen.queryByText("この見どころが伝える歴史")).not.toBeInTheDocument();
    expect(screen.queryByText(/場所の目安/)).not.toBeInTheDocument();
    expect(screen.queryByText(/現地で確認/)).not.toBeInTheDocument();
    expect(screen.queryByText(/出典/)).not.toBeInTheDocument();
  });

  it("各見どころに画面内リンク用の id をつける", () => {
    render(<ShrineHighlightSection section={section([item({ id: 12 })])} />);
    expect(document.getElementById("shrine-highlight-12")).not.toBeNull();
  });

  it("由緒・歴史へのリンクを出し、押したら計測する", () => {
    render(
      <ShrineHighlightSection
        shrineId={5}
        section={section([item({ id: 12, linkedHistories: [{ id: 30, title: "龍の伝承" }] })])}
      />,
    );
    const link = screen.getByRole("link", { name: "由緒・歴史を読む：龍の伝承" });
    expect(link).toHaveAttribute("href", "#shrine-history-30");
    fireEvent.click(link);
    expect(trackSearchEvent).toHaveBeenCalledWith("shrine_highlight_link_click", {
      source: "shrine_detail",
      shrineId: 5,
      highlightId: 12,
      linkDirection: "highlight_to_history",
    });
  });

  it("節が画面に入ったら件数つきで1回だけ計測する", () => {
    let callback: IntersectionObserverCallback = () => {};
    const disconnect = vi.fn();
    globalThis.IntersectionObserver = vi.fn(function (this: unknown, cb: IntersectionObserverCallback) {
      callback = cb;
      return { observe: vi.fn(), disconnect, unobserve: vi.fn(), takeRecords: vi.fn() };
    }) as unknown as typeof IntersectionObserver;

    render(<ShrineHighlightSection shrineId={5} section={section([item({ id: 1 }), item({ id: 2 })])} />);
    expect(trackSearchEvent).not.toHaveBeenCalled();

    const observer = {} as IntersectionObserver;
    callback([{ isIntersecting: false } as IntersectionObserverEntry], observer);
    expect(trackSearchEvent).not.toHaveBeenCalled();
    callback([{ isIntersecting: true } as IntersectionObserverEntry], observer);
    callback([{ isIntersecting: true } as IntersectionObserverEntry], observer);

    expect(trackSearchEvent).toHaveBeenCalledTimes(1);
    expect(trackSearchEvent).toHaveBeenCalledWith("shrine_highlights_view", {
      source: "shrine_detail",
      shrineId: 5,
      highlightCount: 2,
    });
    expect(disconnect).toHaveBeenCalled();
  });

  it("IntersectionObserver が無い環境では表示時に計測する", () => {
    // @ts-expect-error テストのために消す
    delete globalThis.IntersectionObserver;
    render(<ShrineHighlightSection shrineId={5} section={section([item()])} />);
    expect(trackSearchEvent).toHaveBeenCalledWith("shrine_highlights_view", {
      source: "shrine_detail",
      shrineId: 5,
      highlightCount: 1,
    });
  });
});

describe("ShrineFactSection と見どころのリンク", () => {
  beforeEach(() => vi.clearAllMocks());

  function facts(highlightLinks?: { id: number; name: string }[]): DetailFactSection {
    return {
      kind: "fact",
      heading: "神社について",
      deities: [],
      histories: [
        {
          id: 30,
          history_type: "tradition",
          history_type_label: "伝承",
          title: "龍の伝承",
          content: "本文",
          period_text: "",
          sort_order: 0,
          displayState: "full",
          highlightLinks,
        },
      ],
    };
  }

  it("由緒・歴史に画面内リンク用の id をつける", () => {
    render(<ShrineFactSection section={facts()} />);
    expect(document.getElementById("shrine-history-30")).not.toBeNull();
  });

  it("見どころへのリンクが無ければ「現地で見られる場所」を出さない", () => {
    render(<ShrineFactSection section={facts()} />);
    expect(screen.queryByText("現地で見られる場所：")).not.toBeInTheDocument();
  });

  it("「現地で見られる場所」から見どころへ移り、押したら計測する", () => {
    render(
      <ShrineFactSection
        shrineId={5}
        section={facts([
          { id: 12, name: "龍の彫刻" },
          { id: 13, name: "御神木" },
        ])}
      />,
    );
    expect(screen.getByText("現地で見られる場所：")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: "龍の彫刻" });
    expect(link).toHaveAttribute("href", "#shrine-highlight-12");
    expect(screen.getByRole("link", { name: "御神木" })).toHaveAttribute("href", "#shrine-highlight-13");
    fireEvent.click(link);
    expect(trackSearchEvent).toHaveBeenCalledWith("shrine_highlight_link_click", {
      source: "shrine_detail",
      shrineId: 5,
      highlightId: 12,
      linkDirection: "history_to_highlight",
    });
  });
});
