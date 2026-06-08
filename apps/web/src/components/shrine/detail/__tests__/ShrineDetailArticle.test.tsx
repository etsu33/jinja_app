import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackCardEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/cardEvents", () => ({
  trackCardEvent: analyticsMocks.trackCardEvent,
}));

import ShrineDetailArticle from "../ShrineDetailArticle";

vi.mock("@/components/shrine/detail/PublicGoshuinSection", () => ({
  default: () => <div data-testid="public-goshuin-section" />,
}));

vi.mock("@/components/shrine/detail/ShrineJudgeSection", () => ({
  default: () => <div data-testid="shrine-judge-section" />,
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
    expect(screen.getByText("マイページの保存した神社から見返せます")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "保存先を見る" })).toHaveAttribute(
      "href",
      "/mypage?tab=favorites",
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
    expect(screen.queryByRole("link", { name: "保存先を見る" })).not.toBeInTheDocument();
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
});
