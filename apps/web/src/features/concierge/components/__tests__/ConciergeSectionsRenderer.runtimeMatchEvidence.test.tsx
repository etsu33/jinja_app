import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Concierge Evidence Explanation PR
//
// "今回の相談との接点"(Runtime Match)ブロックは、既にBackend/既存Adapterが選定済みの
// signal(matched_need_tags、reason_facts is_primary goriyaku_tag)だけを表示する。新しい
// 一致判定・スコアリングは一切行わない。Evidenceが無ければブロック自体を表示しない
// (捏造しない)。内部tag key(未知のASCII識別子)はラベル化できない場合、raw文字列を
// 画面へ露出させない。

const analyticsMocks = vi.hoisted(() => ({ trackSearchEvent: vi.fn(), trackCardEvent: vi.fn() }));
const authMock = vi.hoisted(() => ({ useAuth: vi.fn(() => ({ isLoggedIn: false, loading: false })) }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: authMock.useAuth }));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";

const baseFilterState: any = {
  isOpen: false,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
};

function buildTestPayload(recommendations: any[], meta: any = {}) {
  const u: any = { data: { recommendations }, thread: { id: 700 }, meta };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

function heroRec(overrides: Partial<any> = {}) {
  return {
    shrine_id: 1,
    display_name: "検証神社",
    reason: "旧型の理由文",
    ...overrides,
  };
}

function renderHero(rec: any, meta: any = {}) {
  const payload = buildTestPayload([rec], meta);
  render(<ConciergeSectionsRenderer payload={payload} threadId={700} isPremiumActive={true} />);
}

describe("Concierge Runtime Match Evidence block", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    window.localStorage.clear();
  });

  it("matched_need_tags(既知key)のみ → 今回の相談との接点ブロックにラベル化済みで表示される", () => {
    renderHero(heroRec({ breakdown: { matched_need_tags: ["career"] } }));

    const block = screen.getByTestId("recommendation-runtime-match");
    expect(block).toHaveTextContent("今回の相談との接点");
    expect(block).toHaveTextContent("仕事や転機を見直したい");
    // 内部key(英語のraw文字列)そのものは露出しない
    expect(block).not.toHaveTextContent("career");
  });

  it("reason_facts is_primary=goriyaku_tagのみ → タスク仕様どおりの文で表示される", () => {
    renderHero(
      heroRec({
        reason_facts: [{ type: "goriyaku_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
      }),
    );

    const block = screen.getByTestId("recommendation-runtime-match");
    expect(block).toHaveTextContent("この神社に登録されている「仕事運」に関する情報が重なっています");
  });

  it("matched_need_tags + goriyaku_tagの両方 → 1つの短い文へ統合され、ブロックが重複しない", () => {
    renderHero(
      heroRec({
        breakdown: { matched_need_tags: ["career"] },
        reason_facts: [{ type: "goriyaku_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
      }),
    );

    const blocks = screen.getAllByTestId("recommendation-runtime-match");
    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toHaveTextContent("仕事や転機を見直したい");
    expect(blocks[0]).toHaveTextContent("仕事運");
  });

  it("Evidenceが何も無い → ブロック自体を表示しない(placeholderで埋めない)", () => {
    renderHero(heroRec({}));

    expect(screen.queryByTestId("recommendation-runtime-match")).not.toBeInTheDocument();
  });

  it("未知のASCII internal tag keyのみ → raw文字列を露出させず、Evidence無しとしてブロックを表示しない", () => {
    renderHero(heroRec({ breakdown: { matched_need_tags: ["some_new_internal_key"] } }));

    expect(screen.queryByTestId("recommendation-runtime-match")).not.toBeInTheDocument();
    expect(screen.queryByText(/some_new_internal_key/)).not.toBeInTheDocument();
  });

  it("Reason V4 fact.goriyakuがwinner(reason_factsにgoriyaku_tagが無い場合) → Runtime Matchへ反映される", () => {
    renderHero(
      heroRec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "検証神社は縁結びのご利益があります。",
          fact: { label: "検証神社", name: "検証神社", deity: null, shrine_history: null, goriyaku: "縁結び", history_theme: null },
          interpretation: { text: "相談内容から、今扱いたいテーマを読み取っています。" },
          action: { text: "" },
        },
      }),
    );

    const block = screen.getByTestId("recommendation-runtime-match");
    expect(block).toHaveTextContent("縁結び");
  });

  it("Fact/Meaning境界: history_theme由来のFrontend解釈テンプレートは「KAMI MUSUBIの解釈」であることが見出しから分かる", () => {
    renderHero(heroRec({ history_theme: "再出発" }));

    const historyBlock = screen.getByTestId("recommendation-history-theme");
    expect(historyBlock).toHaveTextContent("KAMI MUSUBIの解釈");
  });

  it("相談から見た意味(shrineMeaning)の見出しにも解釈であることが明示される(premium表示時)", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    renderHero(heroRec({ breakdown: { matched_need_tags: ["career"] } }));

    expect(screen.getByText("相談から見た意味（KAMI MUSUBIの解釈）")).toBeInTheDocument();
  });
});
