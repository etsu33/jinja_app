import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackCardEvent: vi.fn(),
  trackSearchEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

const visitsMocks = vi.hoisted(() => ({
  addVisit: vi.fn(),
  getVisits: vi.fn(),
}));

vi.mock("@/lib/api/visits", () => ({
  addVisit: visitsMocks.addVisit,
  getVisits: visitsMocks.getVisits,
}));

import ShrineDetailArticle from "../ShrineDetailArticle";

vi.mock("@/components/shrine/detail/PublicGoshuinSection", () => ({
  default: () => <div data-testid="public-goshuin-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineJudgeSection", () => ({
  default: () => <div data-testid="shrine-judge-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineActionSection", () => ({
  default: () => <div data-testid="shrine-action-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineProposalSection", () => ({
  default: () => <div data-testid="shrine-proposal-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineReasonSection", () => ({
  default: () => <div data-testid="shrine-reason-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineSupplementSection", () => ({
  default: () => <div data-testid="shrine-supplement-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineDetailHeroCard", () => ({
  default: () => <div data-testid="shrine-detail-hero-card" />,
}));

vi.mock("@/components/shrine/DetailDisclosureBlock", () => ({
  default: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="detail-disclosure-block">{children}</div>
  ),
}));

function SaveActionStub({ onToggleSuccess }: { onToggleSuccess?: (nextFav: boolean) => void }) {
  return (
    <div>
      <button type="button" onClick={() => onToggleSuccess?.(true)}>
        emit-save
      </button>
      <button type="button" onClick={() => onToggleSuccess?.(false)}>
        emit-remove
      </button>
    </div>
  );
}

describe("ShrineDetailArticle", () => {
  beforeEach(() => {
    analyticsMocks.trackCardEvent.mockClear();
    analyticsMocks.trackSearchEvent.mockClear();
    visitsMocks.addVisit.mockReset();
    visitsMocks.getVisits.mockReset();
    visitsMocks.getVisits.mockResolvedValue([]);
  });
  it("保存成功時の notice と保存先導線を表示する", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        recommendationMeta={null}
        saveActionNode={<SaveActionStub />}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "emit-save" }));

    expect(screen.getByText("保存しました")).toBeInTheDocument();
    expect(screen.getByText("あとで記録から見返せます")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "保存した神社を見る" })).toHaveAttribute(
      "href",
      "/favorites",
    );
    expect(screen.queryByText("保存を解除しました")).not.toBeInTheDocument();
  });

  it("解除成功時は解除 notice のみ表示する", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        recommendationMeta={null}
        saveActionNode={<SaveActionStub />}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "emit-remove" }));

    expect(screen.getByText("保存を解除しました")).toBeInTheDocument();
    expect(screen.queryByText("保存しました")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "保存した神社を見る" })).toHaveAttribute(
      "href",
      "/favorites",
    );
  });

  it("保存・参拝ブロックを御朱印セクションより前に表示する", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          shrineId: 17,
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref="/shrines/17/goshuins"
        showGoshuinSection
        sections={[]}
        recommendationMeta={null}
        saveActionNode={<SaveActionStub />}
      />,
    );

    const saveAction = screen.getByRole("button", { name: "emit-save" });
    const goshuinSection = screen.getByTestId("public-goshuin-section");

    expect(saveAction.compareDocumentPosition(goshuinSection) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("directionSupportCopy がある場合だけ方位補助コピーを弱表示する", () => {
    const baseProps = {
      cardProps: {
        title: "乃木神社",
        href: "/shrines/17",
        imageUrl: null,
        badges: [],
        metaChips: [],
        address: "東京都港区赤坂",
      } as any,
      heroImageUrl: null,
      heroMeaningCopy: null,
      benefitLabels: [],
      tags: [],
      publicGoshuinsPreview: [],
      publicGoshuinsViewAllHref: "",
      sections: [],
      recommendationMeta: null,
      saveActionNode: null,
    };

    const { rerender } = render(
      <ShrineDetailArticle
        {...baseProps}
        directionSupportCopy="方位は主理由ではなく、補助要素として参考にしています。"
      />,
    );

    expect(screen.getByText("方位は主理由ではなく、補助要素として参考にしています。")).toBeInTheDocument();

    rerender(<ShrineDetailArticle {...baseProps} directionSupportCopy={null} />);

    expect(screen.queryByText("方位は主理由ではなく、補助要素として参考にしています。")).not.toBeInTheDocument();
  });

  it("context reason はHero直下の詳細sectionとして表示し、premium meaning より先に出す", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          shrineId: 17,
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        freeDisplaySections={[
          {
            tier: "free",
            layer: "context",
            section: { kind: "reason" },
          },
        ] as any}
        premiumDisplaySections={[
          {
            tier: "premium",
            layer: "context",
            section: { kind: "meaning", items: [] },
          },
        ] as any}
        isPremiumActive
        recommendationMeta={null}
        saveActionNode={null}
      />,
    );

    const reason = screen.getByTestId("shrine-reason-section");
    const meaning = screen.getByTestId("shrine-judge-section");

    expect(reason).toBeInTheDocument();
    expect(meaning).toBeInTheDocument();
    expect(reason.compareDocumentPosition(meaning) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("action section は meaning section の後に表示する", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          shrineId: 17,
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        freeDisplaySections={[]}
        premiumDisplaySections={[
          {
            tier: "premium",
            layer: "context",
            section: { kind: "meaning", items: [] },
          },
          {
            tier: "premium",
            layer: "context",
            section: { kind: "action", items: [] },
          },
        ] as any}
        isPremiumActive
        recommendationMeta={null}
        saveActionNode={null}
      />,
    );

    const meaning = screen.getByTestId("shrine-judge-section");
    const action = screen.getByTestId("shrine-action-section");

    expect(meaning).toBeInTheDocument();
    expect(action).toBeInTheDocument();
    expect(meaning.compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("free では personal meaning section を表示せず、context reason のみを表示する", () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          shrineId: 17,
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        freeDisplaySections={[
          {
            tier: "free",
            layer: "context",
            section: { kind: "reason" },
          },
        ] as any}
        premiumDisplaySections={[]}
        isPremiumActive={false}
        recommendationMeta={null}
        saveActionNode={null}
      />,
    );

    expect(screen.getByTestId("shrine-reason-section")).toBeInTheDocument();
    expect(screen.queryByTestId("shrine-judge-section")).not.toBeInTheDocument();
  });

  it("推薦理由と前回比較の view イベントを送信する", async () => {
    render(
      <ShrineDetailArticle
        cardProps={{
          shrineId: 17,
          title: "乃木神社",
          href: "/shrines/17",
          imageUrl: null,
          badges: [],
          metaChips: [],
          address: "東京都港区赤坂",
        } as any}
        heroImageUrl={null}
        heroMeaningCopy={null}
        benefitLabels={[]}
        tags={[]}
        publicGoshuinsPreview={[]}
        publicGoshuinsViewAllHref=""
        sections={[]}
        isPremiumActive
        recommendationMeta={{
          rankTitle: "この神社が1位の理由",
          rankBody: "相談内容との一致が主因です。",
          rankComparison: {
            is_top: true,
            gap_from_top: 0,
          },
        }}
        stateDelta={{
          previous: null,
          current: null,
          changedNeedTags: ["career"],
          continuedNeedTags: ["mental"],
          daysSincePrevious: 1,
          within7DaysSincePrevious: true,
          summary: "前回より行動に意識が向いています。",
          combinationChange: {
            previousTitle: null,
            currentTitle: "仕事と不安",
            changed: true,
            summary: "状態の重なりが変化しています。",
          },
          transitionNarrative: {
            type: "progression",
            title: "動き出し",
            summary: "前回より次の行動が見えています。",
          },
          hasPreviousAction: false,
          actionReflection: null,
        }}
        saveActionNode={null}
      />,
    );

    await waitFor(() => {
      expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          event: "card_view",
          cardId: "recommendation_meta",
          source: "shrine_detail",
          accessLevel: "premium",
          visibility: "visible",
          shrineId: 17,
        }),
      );
      expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          event: "card_view",
          cardId: "previous_comparison",
          source: "shrine_detail",
          accessLevel: "premium",
          visibility: "visible",
          shrineId: 17,
        }),
      );
    });
  });

  describe("Result <-> Detail duplicate-exposure join (docs/audit/recommendation-result-detail-instrumentation-contract.md §7)", () => {
    const meaningSection = {
      kind: "meaning",
      items: [{ key: "consultation_summary" }, { key: "shrine_meaning" }, { key: "action_meaning" }],
    } as any;

    function renderWithMeaningSection(recommendationInstanceId?: string | null) {
      return render(
        <ShrineDetailArticle
          cardProps={{
            shrineId: 17,
            title: "乃木神社",
            href: "/shrines/17",
            imageUrl: null,
            badges: [],
            metaChips: [],
            address: "東京都港区赤坂",
          } as any}
          heroImageUrl={null}
          heroMeaningCopy={null}
          benefitLabels={[]}
          tags={[]}
          publicGoshuinsPreview={[]}
          publicGoshuinsViewAllHref=""
          sections={[meaningSection]}
          isPremiumActive
          recommendationMeta={null}
          saveActionNode={null}
          recommendationInstanceId={recommendationInstanceId}
        />,
      );
    }

    it("shrine_meaning / action_meaning / consultation_summaryのcard_viewがrecommendationInstanceId + shrineIdを送る", async () => {
      renderWithMeaningSection("a1b2c3d4");

      await waitFor(() => {
        for (const cardId of ["consultation_summary", "shrine_meaning", "action_meaning"] as const) {
          expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
            expect.objectContaining({
              event: "card_view",
              cardId,
              source: "shrine_detail",
              shrineId: 17,
              recommendationInstanceId: "a1b2c3d4",
            }),
          );
        }
      });
    });

    it("recommendationInstanceIdが無い場合はnullを送り、クラッシュせず既存fieldは維持される", async () => {
      expect(() => renderWithMeaningSection(undefined)).not.toThrow();

      await waitFor(() => {
        expect(analyticsMocks.trackCardEvent).toHaveBeenCalledWith(
          expect.objectContaining({
            event: "card_view",
            cardId: "shrine_meaning",
            source: "shrine_detail",
            accessLevel: "premium",
            visibility: "visible",
            shrineId: 17,
            recommendationInstanceId: null,
          }),
        );
      });
    });
  });

  it.each([
    [true, "参拝お疲れさまでした"],
    [false, null],
  ])(
    "actionState が %p のとき、参拝後コピーの表示を検証する",
    (actionState, expectedText) => {
      render(
        <ShrineDetailArticle
          cardProps={{
            title: "乃木神社",
            href: "/shrines/17",
            imageUrl: null,
            badges: [],
            metaChips: [],
            address: "東京都港区赤坂",
          } as any}
          heroImageUrl={null}
          heroMeaningCopy={null}
          benefitLabels={[]}
          tags={[]}
          publicGoshuinsPreview={[]}
          publicGoshuinsViewAllHref=""
          sections={[]}
          recommendationMeta={null}
          saveActionNode={null}
          actionState={actionState ? "visited" : "none"}
        />,
      );

      if (expectedText) {
        expect(screen.getByText(expectedText)).toBeInTheDocument();
      } else {
        expect(screen.queryByText("参拝お疲れさまでした")).not.toBeInTheDocument();
      }
    },
  );

  describe("参拝CTA", () => {
    function renderWithVisitCta(overrides: { ctx?: string | null; historyTheme?: string | null; tid?: string | number | null } = {}) {
      return render(
        <ShrineDetailArticle
          cardProps={{
            shrineId: 17,
            title: "乃木神社",
            href: "/shrines/17",
            imageUrl: null,
            badges: [],
            metaChips: [],
            address: "東京都港区赤坂",
          } as any}
          heroImageUrl={null}
          heroMeaningCopy={null}
          benefitLabels={[]}
          tags={[]}
          publicGoshuinsPreview={[]}
          publicGoshuinsViewAllHref=""
          sections={[]}
          recommendationMeta={null}
          saveActionNode={<SaveActionStub />}
          ctx={overrides.ctx ?? null}
          historyTheme={overrides.historyTheme ?? null}
          tid={overrides.tid ?? null}
        />,
      );
    }

    it("未参拝時は補助説明と「参拝しました」ボタンを表示する", () => {
      renderWithVisitCta();

      expect(screen.getByText("参拝後に記録できます")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "参拝しました" })).toBeInTheDocument();
    });

    it("送信中はボタンが「記録中...」でdisabledになる", async () => {
      let resolveAddVisit: (value?: unknown) => void = () => {};
      visitsMocks.addVisit.mockReturnValue(
        new Promise((resolve) => {
          resolveAddVisit = resolve;
        }),
      );

      renderWithVisitCta();
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      const submittingButton = await screen.findByRole("button", { name: "記録中..." });
      expect(submittingButton).toBeDisabled();

      resolveAddVisit();
      await waitFor(() => expect(screen.queryByRole("button", { name: "記録中..." })).not.toBeInTheDocument());
    });

    it("二重クリックしてもaddVisitは1回しか呼ばれない", async () => {
      let resolveAddVisit: (value?: unknown) => void = () => {};
      visitsMocks.addVisit.mockReturnValue(
        new Promise((resolve) => {
          resolveAddVisit = resolve;
        }),
      );

      renderWithVisitCta();
      const button = screen.getByRole("button", { name: "参拝しました" });
      fireEvent.click(button);
      fireEvent.click(button);

      expect(visitsMocks.addVisit).toHaveBeenCalledTimes(1);

      resolveAddVisit();
      await waitFor(() => expect(screen.getByText("参拝を記録しました")).toBeInTheDocument());
    });

    it("成功後はCTAが消え、完了表示とReflectionPromptが表示される", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta();
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => {
        expect(screen.queryByRole("button", { name: "参拝しました" })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "記録中..." })).not.toBeInTheDocument();
      });

      expect(screen.getByText("参拝を記録しました")).toBeInTheDocument();
      expect(screen.getByText("参拝後の振り返り")).toBeInTheDocument();
    });

    it("visit_doneはsource/shrineId/historyTheme/accessLevelを送信し、ctxは含まない", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta({ ctx: "map", historyTheme: "静寂", tid: "tid-1" });
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => {
        expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
          "visit_done",
          expect.objectContaining({
            source: "shrine_detail",
            shrineId: 17,
            threadId: "tid-1",
            historyTheme: "静寂",
            accessLevel: expect.any(String),
          }),
        );
      });

      const visitDoneCall = analyticsMocks.trackSearchEvent.mock.calls.find(([eventName]) => eventName === "visit_done");
      expect(visitDoneCall?.[1]).not.toHaveProperty("ctx");
      expect(visitDoneCall?.[1]?.mode).toBeUndefined();
    });

    it("ctx=concierge の場合、visit_doneはmode:needを送信する", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta({ ctx: "concierge" });
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => {
        expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
          "visit_done",
          expect.objectContaining({ mode: "need" }),
        );
      });
    });

    it("ctx=compass の場合、visit_doneはsource=compassを送る（PR-C）", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta({ ctx: "compass", historyTheme: "静寂", tid: "tid-1" });
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => {
        expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
          "visit_done",
          expect.objectContaining({ source: "compass", shrineId: 17 }),
        );
      });

      // Compass is never a Concierge mode -- unaffected, same as ctx=null/map today.
      const visitDoneCall = analyticsMocks.trackSearchEvent.mock.calls.find(([eventName]) => eventName === "visit_done");
      expect(visitDoneCall?.[1]?.mode).toBeUndefined();
    });

    it("ctxが未指定（直接遷移）の場合、visit_doneのsourceはCompassへ漏れずshrine_detailのまま（PR-C）", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta();
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => {
        expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
          "visit_done",
          expect.objectContaining({ source: "shrine_detail" }),
        );
      });
    });

    it("visit_doneのペイロードにbirthdate・座標を含めない（PR-C PIIチェック）", async () => {
      visitsMocks.addVisit.mockResolvedValue({});

      renderWithVisitCta({ ctx: "compass" });
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      await waitFor(() => expect(analyticsMocks.trackSearchEvent).toHaveBeenCalled());

      const visitDoneCall = analyticsMocks.trackSearchEvent.mock.calls.find(([eventName]) => eventName === "visit_done");
      expect(visitDoneCall?.[1]).not.toHaveProperty("birthdate");
      expect(visitDoneCall?.[1]).not.toHaveProperty("latitude");
      expect(visitDoneCall?.[1]).not.toHaveProperty("longitude");
    });

    it("失敗後はエラー表示になり、再操作可能な状態に戻る", async () => {
      visitsMocks.addVisit.mockRejectedValue(new Error("failed"));

      renderWithVisitCta();
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      const retryButton = await screen.findByRole("button", { name: "参拝しました" });
      expect(screen.getByText("参拝記録に失敗しました")).toBeInTheDocument();
      expect(retryButton).not.toBeDisabled();
    });
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("Hero Headerがradius-card / surface-default / shadow-medium / text-primary / text-mutedを参照する", () => {
      render(
        <ShrineDetailArticle
          cardProps={{
            title: "乃木神社",
            href: "/shrines/17",
            imageUrl: null,
            badges: [],
            metaChips: [],
            address: "東京都港区赤坂",
          } as any}
          heroImageUrl={null}
          heroMeaningCopy={null}
          benefitLabels={[]}
          tags={[]}
          publicGoshuinsPreview={[]}
          publicGoshuinsViewAllHref=""
          sections={[]}
          recommendationMeta={null}
          saveActionNode={null}
        />,
      );

      const heading = screen.getByRole("heading", { name: "乃木神社" });
      const heroSection = heading.closest("section");
      expect(heroSection?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(heroSection?.className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(heroSection?.className).toContain("shadow-[var(--kt-shadow-medium)]");
      expect(heading.className).toContain("text-[var(--kt-color-text-primary)]");
      expect(screen.getByText("この神社の意味").className).toContain("text-[var(--kt-color-text-muted)]");
    });

    it("directionSupportCopyがradius-card / border-default / background-subtle / text-mutedを参照する", () => {
      render(
        <ShrineDetailArticle
          cardProps={{
            title: "乃木神社",
            href: "/shrines/17",
            imageUrl: null,
            badges: [],
            metaChips: [],
            address: "東京都港区赤坂",
          } as any}
          heroImageUrl={null}
          heroMeaningCopy={null}
          benefitLabels={[]}
          tags={[]}
          publicGoshuinsPreview={[]}
          publicGoshuinsViewAllHref=""
          sections={[]}
          recommendationMeta={null}
          saveActionNode={null}
          directionSupportCopy="方位は主理由ではなく、補助要素として参考にしています。"
        />,
      );

      const copy = screen.getByText("方位は主理由ではなく、補助要素として参考にしています。");
      expect(copy.className).toContain("text-[var(--kt-color-text-muted)]");
      const wrapper = copy.parentElement;
      expect(wrapper?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(wrapper?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(wrapper?.className).toContain("bg-[var(--kt-color-background-subtle)]");
    });
  });

  describe("神社について(Fact) Section", () => {
    const baseProps = {
      cardProps: {
        title: "乃木神社",
        href: "/shrines/17",
        imageUrl: null,
        badges: [],
        metaChips: [],
        address: "東京都港区赤坂",
      } as any,
      heroImageUrl: null,
      heroMeaningCopy: null,
      benefitLabels: [],
      tags: [],
      publicGoshuinsPreview: [],
      publicGoshuinsViewAllHref: "",
      sections: [],
      recommendationMeta: null,
      saveActionNode: null,
    };

    it("factSectionがnullの場合「神社について」を表示しない", () => {
      render(<ShrineDetailArticle {...baseProps} factSection={null} />);

      expect(screen.queryByText("神社について")).not.toBeInTheDocument();
    });

    it("御祭神とHistoryを表示する", () => {
      render(
        <ShrineDetailArticle
          {...baseProps}
          factSection={{
            kind: "fact",
            heading: "神社について",
            deities: [
              { display_name: "明治天皇", sort_order: 0, displayState: "full" },
              { display_name: "昭憲皇太后", sort_order: 1, displayState: "full" },
            ],
            histories: [
              {
                history_type: "official_origin",
                history_type_label: "由緒",
                title: "明治神宮の創建",
                content: "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
                period_text: "大正9年（1920）",
                sort_order: 0,
                displayState: "full",
              },
            ],
          }}
        />,
      );

      expect(screen.getByText("神社について")).toBeInTheDocument();
      expect(screen.getByText("御祭神")).toBeInTheDocument();
      expect(screen.getByText("明治天皇")).toBeInTheDocument();
      expect(screen.getByText("昭憲皇太后")).toBeInTheDocument();
      expect(screen.getByText("由緒・歴史")).toBeInTheDocument();
      expect(screen.getByText("明治神宮の創建")).toBeInTheDocument();
      expect(
        screen.getByText("明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。"),
      ).toBeInTheDocument();
    });

    it("複数Historyをすべて表示する（品川神社相当）", () => {
      render(
        <ShrineDetailArticle
          {...baseProps}
          factSection={{
            kind: "fact",
            heading: "神社について",
            deities: [],
            histories: [
              {
                history_type: "founding",
                history_type_label: "創始",
                title: "文治3年（1187年）の創始",
                content: "創始の内容",
                period_text: "文治3年（1187年）",
                sort_order: 0,
                displayState: "full",
              },
              {
                history_type: "historical_event",
                history_type_label: "歴史",
                title: "元応元年（1319年）の宇賀之売命奉祀",
                content: "1319年の内容",
                period_text: "元応元年（1319年）",
                sort_order: 1,
                displayState: "full",
              },
              {
                history_type: "historical_event",
                history_type_label: "歴史",
                title: "文明10年（1478年）の素盞嗚尊奉祀",
                content: "1478年の内容",
                period_text: "文明10年（1478年）",
                sort_order: 2,
                displayState: "full",
              },
            ],
          }}
        />,
      );

      expect(screen.getByText("文治3年（1187年）の創始")).toBeInTheDocument();
      expect(screen.getByText("元応元年（1319年）の宇賀之売命奉祀")).toBeInTheDocument();
      expect(screen.getByText("文明10年（1478年）の素盞嗚尊奉祀")).toBeInTheDocument();
      // 御祭神が無い場合は見出しを出さない
      expect(screen.queryByText("御祭神")).not.toBeInTheDocument();
      // Presentation Grouping（PR-B）: 同じhistory_type="historical_event"の2件は
      // 「歴史」という1つの共通見出しの下にまとまり、「創始」1件は別見出しの下に残る。
      // 見出し「歴史」は1つだけ（2枚のcardそれぞれの個別ラベルとしては重複表示しない）。
      expect(screen.getAllByText("歴史")).toHaveLength(1);
      expect(screen.getByText("創始")).toBeInTheDocument();
    });
  });
});
