import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/product/recommendation-result-information-architecture.md §6, §11, §13, §15 PR3:
// Primary CTA("神社の詳細を見る")がHero Result画面で唯一の強いCTAであること、
// Save / Premium誘導がそれと競合しない従属表現であること、trustMetadataが
// Ranking理由として再解釈されずShrine Fact/Conclusionと意味的に連続する位置に
// あることを固定する。Ranking / Authority / Reason生成 / Action Grounding /
// Analytics semanticsはこのPRの対象外(禁止事項)であり、ここでは検証しない。

const PRIMARY_CTA_CLASS_FRAGMENT = "bg-[var(--kt-color-action-primary)]";

const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackCardEvent: vi.fn(),
  track: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
}));

vi.mock("@/lib/analytics/track", () => ({
  track: analyticsMocks.track,
}));

const authMock = vi.hoisted(() => ({
  useAuth: vi.fn(() => ({ isLoggedIn: true, loading: false })),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: authMock.useAuth,
}));

const useFavoriteMock = vi.hoisted(() =>
  vi.fn((_args: unknown) => ({ fav: false, busy: false, toggle: vi.fn().mockResolvedValue(undefined) })),
);
vi.mock("@/hooks/useFavorite", () => ({
  useFavorite: (args: unknown) => useFavoriteMock(args),
}));

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
  const u: any = { data: { recommendations }, thread: { id: 500 }, meta };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

const trustFixture = {
  rank_class: "由緒あり",
  cultural_status: ["重要文化財"],
  lineage: "式内社",
  origin_summary: "古くから信仰を集める神社です。",
};

function heroRec(overrides: Partial<any> = {}) {
  return {
    shrine_id: 1,
    display_name: "根津神社",
    reason: "仕事運に関わる神社です。",
    recommendation_reason_v4_detail: {
      version: "v4",
      reason_text: "根津神社は仕事運に関わる神社です。",
      fact: {
        label: "根津神社",
        name: "根津神社",
        history_theme: "再出発",
        goriyaku: "仕事運",
        evidence: ["history_theme:再出発"],
      },
      interpretation: { theme: "再出発", text: "相談内容から、今扱いたいテーマを読み取っています。" },
      action: { text: "参拝前に、問いを一つに絞ることを決めておきます。" },
    },
    ...overrides,
  };
}

function strongCtaElements() {
  return screen.getAllByRole("link").filter((el) => el.className.includes(PRIMARY_CTA_CLASS_FRAGMENT));
}

// Hero直下のShrineSaveButton(variant="subtle")は下部のsave_promptボタンと
// ラベルが同じため、aria-pressedを持つ方(ShrineSaveButton固有)で一意に特定する。
function heroSaveButton() {
  return screen.getAllByRole("button").find((el) => el.hasAttribute("aria-pressed"))!;
}

describe("Recommendation Result CTA Hierarchy & Trust Placement", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    analyticsMocks.track.mockClear();
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    useFavoriteMock.mockReturnValue({ fav: false, busy: false, toggle: vi.fn().mockResolvedValue(undefined) });
    window.localStorage.clear();
  });

  it("1. Primary CTA(神社の詳細を見る)だけがstrong CTA class(bg-action-primary)を持つ", () => {
    const payload = buildTestPayload([heroRec({ trust_metadata: trustFixture })]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    const strongCtas = strongCtaElements();
    expect(strongCtas).toHaveLength(1);
    expect(strongCtas[0]).toHaveTextContent("神社の詳細を見る");

    // Save / Premiumはstrong CTAのclassを持たない
    const saveButton = heroSaveButton();
    expect(saveButton.className).not.toContain(PRIMARY_CTA_CLASS_FRAGMENT);

    const premiumCta = screen.getByTestId("recommendation-premium-preview").querySelector("a");
    expect(premiumCta).not.toBeNull();
    expect(premiumCta!.className).not.toContain(PRIMARY_CTA_CLASS_FRAGMENT);
  });

  it("2. Saveは削除されずHero下に残る(authenticated/free, Save可能)", () => {
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    expect(heroSaveButton()).toHaveTextContent("あとで見返すために保存");
  });

  it("2b. Save不可(anonymous)ではログイン誘導ラベルへ切り替わるが、要素自体は残る", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: false, loading: false });
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    expect(heroSaveButton()).toHaveTextContent("ログインしてあとで見返す");
  });

  it("3. Premium CTAはanonymous/freeで残る(削除されない)", () => {
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    expect(screen.getByTestId("recommendation-premium-preview")).toBeInTheDocument();
  });

  it("3b. premiumユーザーではpremium_previewポリシーどおりhiddenになる(既存gating、非回帰)", () => {
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={true} />);

    expect(screen.queryByTestId("recommendation-premium-preview")).not.toBeInTheDocument();
  });

  it("4. trustMetadataはEvidenceとして推薦理由ナラティブ(historyTheme等)より後段に置かれる", () => {
    // PR-G1 (docs/design/premium-meaning-ui-direction.md §7/§9, Direction C):
    // trustMetadata は Shrine Fact = Evidence(Layer 8)であり、reason/meaning の
    // ナラティブ(historyTheme を含む)より後に、控えめな recessed surface で表示する。
    // 以前の §13「trust 直後に historyTheme」グルーピングはこの階層設計で置き換わった。
    // trust が Conclusion / Primary Reason に混ざらないことは test 5 で引き続き検証する。
    const payload = buildTestPayload([heroRec({ trust_metadata: trustFixture, history_theme: "再出発" })]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    const trust = screen.getByTestId("recommendation-trust");
    const history = screen.getByTestId("recommendation-history-theme");
    expect(trust).toHaveTextContent("由緒あり");
    expect(trust).toHaveTextContent("古くから信仰を集める神社です。");
    expect(history).toBeInTheDocument();

    // DOM順序: historyTheme(ナラティブ)が trustMetadata(Evidence)より先
    const position = history.compareDocumentPosition(trust);
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("4b. trustMetadataなしでもクラッシュせず表示される", () => {
    const payload = buildTestPayload([heroRec()]);

    expect(() => {
      render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);
    }).not.toThrow();

    expect(screen.queryByTestId("recommendation-trust")).not.toBeInTheDocument();
    expect(screen.getByText("根津神社")).toBeInTheDocument();
  });

  it("5. fallbackでもtrustMetadataはConclusionへ含まれず、Ranking reasonとして扱われない", () => {
    const payload = buildTestPayload(
      [heroRec({ trust_metadata: trustFixture })],
      { resultState: { fallback_mode: "nearby_unfiltered" } },
    );
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).not.toHaveTextContent("由緒あり");
    expect(conclusion).not.toHaveTextContent("重要文化財");
    expect(conclusion).not.toHaveTextContent("古くから信仰を集める神社です。");

    // trustMetadata自体は(Shrine Factとして)引き続き表示される
    expect(screen.getByTestId("recommendation-trust")).toHaveTextContent("由緒あり");
  });

  it("6. Save analyticsのclick contract(favorite_click / shrine_decision)は変化しない", async () => {
    const toggle = vi.fn().mockResolvedValue(undefined);
    useFavoriteMock.mockReturnValue({ fav: false, busy: false, toggle });
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    fireEvent.click(heroSaveButton());

    await waitFor(() => expect(toggle).toHaveBeenCalled());
    await waitFor(() =>
      expect(analyticsMocks.track).toHaveBeenCalledWith(
        "favorite_click",
        expect.objectContaining({ shrineId: 1, ctx: "concierge", nextFav: true }),
      ),
    );
    expect(analyticsMocks.track).toHaveBeenCalledWith(
      "shrine_decision",
      expect.objectContaining({ shrineId: 1, action: "save" }),
    );
  });

  it("6b. Premium CTA click analytics(premium_preview_click)は変化しない", () => {
    const payload = buildTestPayload([heroRec()]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={false} />);

    const premiumCta = screen.getByTestId("recommendation-premium-preview").querySelector("a")!;
    fireEvent.click(premiumCta);

    expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
      expect.objectContaining({ event: "premium_preview_click", cardId: "premium_preview", shrineId: 1 }),
    );
  });

  // ---- PR-G1: Concierge Result information hierarchy ------------------------
  // docs/design/premium-meaning-ui-direction.md §7 (Direction C).

  it("7. Consultation Context(今回の相談の整理)が Shrine Meaning より前に読める", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    const payload = buildTestPayload([heroRec({ breakdown: { matched_need_tags: ["career"] } })]);
    // premium: shrine_meaning は teaser ではなく本文が出る = 両方が DOM に存在する
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={true} />);

    const consultation = screen.getByText("今回の相談の整理");
    const shrineMeaning = screen.getByText("相談から見た意味（KAMI MUSUBIの解釈）");

    const position = consultation.compareDocumentPosition(shrineMeaning);
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("8. 推薦理由ナラティブの各セクション見出しが <h2> で、bordered card ではない", () => {
    authMock.useAuth.mockReturnValue({ isLoggedIn: true, loading: false });
    const payload = buildTestPayload([
      heroRec({ trust_metadata: trustFixture, history_theme: "再出発", breakdown: { matched_need_tags: ["career"] } }),
    ]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={500} isPremiumActive={true} />);

    for (const label of [
      "今回の相談との接点",
      "この神社をどう捉えるか（KAMI MUSUBIの解釈）",
      "相談から見た意味（KAMI MUSUBIの解釈）",
      "今の自分への問い",
    ]) {
      const heading = screen.getByText(label);
      expect(heading.tagName).toBe("H2");

      // 見出しを含むセクションが soft card(border + shadow + surface)化していない
      const section = heading.closest("section");
      expect(section).not.toBeNull();
      expect(section!.className).not.toMatch(/\bborder\b/);
      expect(section!.className).not.toMatch(/shadow-\[/);
    }
  });
});
