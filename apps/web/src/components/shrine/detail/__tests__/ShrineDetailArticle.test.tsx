import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
});
