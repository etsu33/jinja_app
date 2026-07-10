import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackCardEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
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
    function renderWithVisitCta() {
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

    it("失敗後はエラー表示になり、再操作可能な状態に戻る", async () => {
      visitsMocks.addVisit.mockRejectedValue(new Error("failed"));

      renderWithVisitCta();
      fireEvent.click(screen.getByRole("button", { name: "参拝しました" }));

      const retryButton = await screen.findByRole("button", { name: "参拝しました" });
      expect(screen.getByText("参拝記録に失敗しました")).toBeInTheDocument();
      expect(retryButton).not.toBeDisabled();
    });
  });
});
