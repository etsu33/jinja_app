import { render, screen, within } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackCardEvent: vi.fn(),
  trackSearchEvent: vi.fn(),
  trackShrineInteraction: vi.fn(() => Promise.resolve()),
}));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction: analyticsMocks.trackShrineInteraction }));
import CompassRecommendationsSection from "../CompassRecommendationsSection";
import type { CompassRecommendation } from "../../types";

const ORIGIN = { lat: 35.0, lng: 135.0 };

const LONG_HISTORY =
  "古くより地域の守りとして祀られてきたと伝わる。社殿は幾度かの再建を経て現在の姿となり、例祭には周辺の集落から多くの参拝者が集まる。" +
  "境内には樹齢数百年とされる御神木があり、地域の人々に親しまれてきた。";

function renderOne(rec: CompassRecommendation, origin: { lat: number; lng: number } | null = ORIGIN) {
  return render(
    <CompassRecommendationsSection recommendationInstanceId="compass01" origin={origin} recommendations={[rec]} />,
  );
}

describe("CompassRecommendationsSection (Candidate Card v2)", () => {
  beforeEach(() => {
    analyticsMocks.trackCardEvent.mockClear();
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackShrineInteraction.mockClear();
  });

  it("名前 → 所在地+距離 → 接点 → 区切り → この神社について → CTA の順で描画する", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      address: "東京都千代田区",
      distance_m: 1200,
      reason_facts: [{ type: "goriyaku_tag", label: "仕事運", label_ja: "仕事運", is_primary: true }],
      shrine_facts: {
        deity: { display_name: "天照大神" },
        history: { history_type: "official_origin", content: "古くより祀られてきた。" },
      },
    });

    const article = screen.getByRole("article");
    const order = [
      within(article).getByRole("heading", { level: 3, name: "北西神社" }),
      within(article).getByTestId("shrine-card-candidate-location"),
      within(article).getByTestId("compass-candidate-meaning"),
      within(article).getByTestId("compass-candidate-divider"),
      within(article).getByTestId("compass-candidate-shrine-facts"),
      within(article).getByRole("link", { name: "神社を見る" }),
      within(article).getByRole("link", { name: "経路を見る" }),
    ];
    for (let i = 1; i < order.length; i += 1) {
      expect(order[i - 1].compareDocumentPosition(order[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }

    expect(within(article).getByTestId("shrine-card-candidate-location")).toHaveTextContent("東京都千代田区");
    expect(within(article).getByTestId("shrine-card-candidate-location")).toHaveTextContent("約1.2km");
    expect(within(article).getByText("今のあなたとの接点")).toBeInTheDocument();
    expect(within(article).getByText("この神社について")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Meaning（reason_facts）
  // -------------------------------------------------------------------------

  it("Meaningはis_primary=trueかつlabel_jaが空でない最初のreason_factだけを使う", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      reason_facts: [
        { type: "need_tag", label: "career", label_ja: "転機・仕事", is_primary: false },
        { type: "goriyaku_tag", label: "空", label_ja: "   ", is_primary: true },
        { type: "goriyaku_tag", label: "仕事運", label_ja: "仕事運", is_primary: true },
        { type: "goriyaku_tag", label: "商売繁盛", label_ja: "商売繁盛", is_primary: true },
      ],
    });

    const meaning = screen.getByTestId("compass-candidate-meaning");
    expect(meaning).toHaveTextContent("仕事運");
    expect(meaning).not.toHaveTextContent("転機・仕事");
    expect(meaning).not.toHaveTextContent("商売繁盛");
  });

  it("primaryが無ければlegacy reasonへfallbackせずMeaningブロックを出さない", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      reason: "ご利益のご利益で知られる神社です。",
      reason_facts: [{ type: "need_tag", label: "career", label_ja: "転機・仕事", is_primary: false }],
    });

    expect(screen.queryByTestId("compass-candidate-meaning")).not.toBeInTheDocument();
    expect(screen.queryByText("今のあなたとの接点")).not.toBeInTheDocument();
    expect(screen.queryByText(/ご利益のご利益/)).not.toBeInTheDocument();
    expect(screen.queryByText("転機・仕事")).not.toBeInTheDocument();
  });

  it("reason_factsが無い場合もlegacy reasonを表示しない", () => {
    renderOne({ shrine_id: 1, name: "北西神社", reason: "仕事運とのご利益一致" });

    expect(screen.queryByTestId("compass-candidate-meaning")).not.toBeInTheDocument();
    expect(screen.queryByText("仕事運とのご利益一致")).not.toBeInTheDocument();
  });

  it("history_themeのprimaryはKAMI MUSUBIの解釈として明示する", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      reason_facts: [{ type: "history_theme", label: "守り", label_ja: "守り", is_primary: true }],
    });

    expect(screen.getByTestId("compass-candidate-meaning")).toHaveTextContent("守りという文脈（KAMI MUSUBIの解釈）");
  });

  it("history_theme以外のMeaningにはKAMI MUSUBIの解釈表記を付けない", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      reason_facts: [{ type: "goriyaku_tag", label: "仕事運", label_ja: "仕事運", is_primary: true }],
    });

    expect(screen.getByTestId("compass-candidate-meaning")).not.toHaveTextContent("KAMI MUSUBIの解釈");
  });

  // -------------------------------------------------------------------------
  // Shrine Fact（shrine_facts）
  // -------------------------------------------------------------------------

  it("deityのみの場合は祭神だけを表示し、由緒ブロックを出さない", () => {
    renderOne({ shrine_id: 1, name: "北西神社", shrine_facts: { deity: { display_name: "天照大神" } } });

    const facts = screen.getByTestId("compass-candidate-shrine-facts");
    expect(within(facts).getByTestId("compass-candidate-deity")).toHaveTextContent("祭神天照大神");
    expect(within(facts).queryByTestId("compass-candidate-history")).not.toBeInTheDocument();
  });

  it("historyのみの場合は由緒だけを表示し、祭神ブロックを出さない", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      shrine_facts: { history: { history_type: "tradition", content: "伝承の由緒。" } },
    });

    const facts = screen.getByTestId("compass-candidate-shrine-facts");
    expect(within(facts).queryByTestId("compass-candidate-deity")).not.toBeInTheDocument();
    expect(within(facts).getByTestId("compass-candidate-history")).toHaveTextContent("伝承の由緒。");
  });

  it("deity/historyとも無ければ「この神社について」セクションを出さない", () => {
    for (const shrine_facts of [undefined, null, {}]) {
      const { unmount } = renderOne({ shrine_id: 1, name: "北西神社", shrine_facts });
      expect(screen.queryByTestId("compass-candidate-shrine-facts")).not.toBeInTheDocument();
      expect(screen.queryByText("この神社について")).not.toBeInTheDocument();
      unmount();
    }
  });

  it("MeaningかFactの片方しか無い場合は区切り線を出さない", () => {
    renderOne({ shrine_id: 1, name: "北西神社", shrine_facts: { deity: { display_name: "天照大神" } } });
    expect(screen.queryByTestId("compass-candidate-divider")).not.toBeInTheDocument();
  });

  it("history.contentはCSS line-clamp-2で表示し、JSで切り詰めない（全文がDOMに残る）", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      shrine_facts: { history: { history_type: "official_origin", content: LONG_HISTORY } },
    });

    const history = screen.getByTestId("compass-candidate-history");
    expect(history).toHaveClass("line-clamp-2");
    expect(history.textContent).toBe(LONG_HISTORY);
    expect(history.textContent).not.toMatch(/…|\.\.\.$/);
  });

  it.each([
    ["official_origin", "由緒"],
    ["founding", "由緒"],
    ["historical_event", "歴史"],
    ["tradition", "伝承"],
    ["regional_context", "地域との関わり"],
    ["editorial_summary", "概要"],
  ])("history_type=%s は「%s」と表示する", (historyType, label) => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      shrine_facts: { history: { history_type: historyType, content: "内容。" } },
    });

    expect(screen.getByTestId("compass-candidate-history-type")).toHaveTextContent(label);
  });

  it("未知のhistory_typeは種別ラベルを出さない（生のtype文字列を表示しない）", () => {
    renderOne({
      shrine_id: 1,
      name: "北西神社",
      shrine_facts: { history: { history_type: "future_type", content: "内容。" } },
    });

    expect(screen.queryByTestId("compass-candidate-history-type")).not.toBeInTheDocument();
    expect(screen.queryByText("future_type")).not.toBeInTheDocument();
    expect(screen.getByTestId("compass-candidate-history")).toHaveTextContent("内容。");
  });

  // -------------------------------------------------------------------------
  // Distance / Order
  // -------------------------------------------------------------------------

  it("distance_mが未取得の候補では距離を省略する（undefined/nullを表示しない）", () => {
    renderOne({ shrine_id: 1, name: "北西神社", address: "東京都千代田区" });

    const location = screen.getByTestId("shrine-card-candidate-location");
    expect(location).toHaveTextContent("東京都千代田区");
    expect(location).not.toHaveTextContent(/km|約/);
    expect(screen.queryByText("undefined")).not.toBeInTheDocument();
    expect(screen.queryByText("null")).not.toBeInTheDocument();
    expect(screen.queryByText("NaN")).not.toBeInTheDocument();
  });

  it("複数候補は与えられた順序どおりに描画される（Rankingの並びを変更しない）", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[
          { shrine_id: 1, name: "神社A", distance_m: 500 },
          { shrine_id: 2, name: "神社B", distance_m: 100, shrine_facts: { deity: { display_name: "祭神B" } } },
          { shrine_id: 3, name: "神社C", distance_m: 2000 },
        ]}
      />,
    );

    const names = screen.getAllByRole("heading", { level: 3 }).map((el) => el.textContent);
    // 神社Bが最短距離・唯一のFact保有でも並び替えない。
    expect(names).toEqual(["神社A", "神社B", "神社C"]);
    expect(screen.getAllByRole("article")).toHaveLength(3);
  });

  // -------------------------------------------------------------------------
  // Detail CTA（既存attributionを維持）
  // -------------------------------------------------------------------------

  it("「神社を見る」はctx=compassのbuildShrineHref attributionを維持する", () => {
    renderOne({ shrine_id: 42, name: "北西神社" });

    expect(screen.getByRole("link", { name: "神社を見る" })).toHaveAttribute(
      "href",
      "/shrines/42?ctx=compass&recommendation_instance_id=compass01&recommendation_rank=1",
    );
  });

  it("共通impression/clickイベントへ同じCompass attributionを渡す", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[
          { shrine_id: 10, name: "神社A" },
          { shrine_id: 20, name: "神社B" },
        ]}
      />,
    );

    expect(analyticsMocks.trackCardEvent).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        event: "card_view",
        source: "compass",
        shrineId: 20,
        recommendationRank: 2,
        recommendationInstanceId: "compass01",
      }),
    );

    fireEvent.click(screen.getAllByRole("link", { name: "神社を見る" })[1]);
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith("shrine_detail_transition", {
      source: "compass",
      shrineId: 20,
      recommendationRank: 2,
      recommendationInstanceId: "compass01",
      position: "compact",
    });
  });

  // -------------------------------------------------------------------------
  // Route CTA
  // -------------------------------------------------------------------------

  it("「経路を見る」は送信済みoriginとaddressでGoogle Maps経路URLを作る", () => {
    renderOne({ shrine_id: 42, name: "北西神社", address: "東京都千代田区1-1" });

    const route = screen.getByRole("link", { name: "経路を見る" });
    const url = new URL(route.getAttribute("href") ?? "");
    expect(url.origin + url.pathname).toBe("https://www.google.com/maps/dir/");
    expect(url.searchParams.get("destination")).toBe("東京都千代田区1-1");
    expect(url.searchParams.get("origin")).toBe("35,135");
    expect(route).toHaveAttribute("target", "_blank");
  });

  it("addressが無ければ神社名をdestinationにする", () => {
    renderOne({ shrine_id: 42, name: "北西神社" });

    const url = new URL(screen.getByRole("link", { name: "経路を見る" }).getAttribute("href") ?? "");
    expect(url.searchParams.get("destination")).toBe("北西神社");
  });

  it("originが無ければdestinationのみの経路URLにする", () => {
    renderOne({ shrine_id: 42, name: "北西神社", address: "東京都千代田区" }, null);

    const url = new URL(screen.getByRole("link", { name: "経路を見る" }).getAttribute("href") ?? "");
    expect(url.searchParams.get("origin")).toBeNull();
  });

  it("destinationを解決できない候補では経路CTAを出さない", () => {
    renderOne({ shrine_id: 42, name: "  ", address: null });

    expect(screen.queryByRole("link", { name: "経路を見る" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "神社を見る" })).toBeInTheDocument();
  });

  it("経路クリックはsource=compass / shrineId / ctx=compass / recommendationInstanceIdを送る", () => {
    renderOne({ shrine_id: 42, name: "北西神社", address: "東京都千代田区" });

    fireEvent.click(screen.getByRole("link", { name: "経路を見る" }));

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "route_open",
      expect.objectContaining({
        source: "compass",
        routeTarget: "google_maps",
        shrineId: 42,
        ctx: "compass",
        recommendationInstanceId: "compass01",
      }),
    );
    expect(analyticsMocks.trackShrineInteraction).toHaveBeenCalledWith(
      expect.objectContaining({
        shrineId: 42,
        actionType: "route_open",
        source: "compass",
        metadata: expect.objectContaining({ ctx: "compass", recommendation_instance_id: "compass01" }),
      }),
    );
    // 経路クリックは詳細遷移イベントを送らない。
    expect(analyticsMocks.trackSearchEvent).not.toHaveBeenCalledWith("shrine_detail_transition", expect.anything());
  });

  // -------------------------------------------------------------------------
  // F-1: `id` は identity authority ではない
  // docs/audit/compass-shrine-id-presence-audit.md §14
  // -------------------------------------------------------------------------
  it("shrine_idとidが食い違う場合、navigation・analyticsともshrine_idのみを使う（idをidentityにしない）", () => {
    renderOne({
      shrine_id: 42,
      // COMPATIBILITY_FIELD。identity authority ではない。
      id: 999,
      name: "識別子乖離神社",
      address: "東京都千代田区",
    });

    const link = screen.getByRole("link", { name: "神社を見る" });
    expect(link).toHaveAttribute(
      "href",
      "/shrines/42?ctx=compass&recommendation_instance_id=compass01&recommendation_rank=1",
    );
    expect(link.getAttribute("href")).not.toContain("999");

    expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        event: "card_view",
        source: "compass",
        shrineId: 42,
        recommendationRank: 1,
        recommendationInstanceId: "compass01",
      }),
    );

    fireEvent.click(link);
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith("shrine_detail_transition", {
      source: "compass",
      shrineId: 42,
      recommendationRank: 1,
      recommendationInstanceId: "compass01",
      position: "compact",
    });

    fireEvent.click(screen.getByRole("link", { name: "経路を見る" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "route_open",
      expect.objectContaining({ shrineId: 42 }),
    );

    for (const [payload] of analyticsMocks.trackCardEvent.mock.calls) {
      expect(payload.shrineId).not.toBe(999);
    }
    for (const [, payload] of analyticsMocks.trackSearchEvent.mock.calls) {
      expect(payload?.shrineId).not.toBe(999);
    }
  });
});
