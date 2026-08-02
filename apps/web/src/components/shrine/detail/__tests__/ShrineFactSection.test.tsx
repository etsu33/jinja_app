// apps/web/src/components/shrine/detail/__tests__/ShrineFactSection.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineFactSection from "../ShrineFactSection";
import type { DetailFactSection } from "../types";

function makeSection(overrides: Partial<DetailFactSection> = {}): DetailFactSection {
  return {
    kind: "fact",
    heading: "神社について",
    deities: [],
    histories: [],
    ...overrides,
  };
}

describe("ShrineFactSection", () => {
  it("deities/historiesが両方空ならnullを返す（非表示）", () => {
    const { container } = render(<ShrineFactSection section={makeSection()} />);
    expect(container.firstChild).toBeNull();
  });

  describe("full Fact（回帰: 現行表示を完全維持する）", () => {
    it("full Deityはdisputedラベルを表示しない", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            deities: [{ display_name: "確定祭神", sort_order: 0, displayState: "full" }],
          })}
        />,
      );
      expect(screen.getByText("確定祭神")).toBeInTheDocument();
      expect(screen.queryByText("異なる見解を含む情報")).not.toBeInTheDocument();
    });

    it("full Historyはdisputedラベルを表示しない", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                history_type: "founding",
                history_type_label: "創始",
                title: "確定由緒",
                content: "確定した内容",
                period_text: "大正9年",
                sort_order: 0,
                displayState: "full",
              },
            ],
          })}
        />,
      );
      expect(screen.getByText("確定由緒")).toBeInTheDocument();
      expect(screen.getByText("確定した内容")).toBeInTheDocument();
      expect(screen.getByText("大正9年")).toBeInTheDocument();
      expect(screen.queryByText("異なる見解を含む情報")).not.toBeInTheDocument();
    });
  });

  describe("disputed Fact", () => {
    it("disputed Deityは状態ラベルを表示する", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            deities: [{ display_name: "矛盾祭神", sort_order: 0, displayState: "disputed" }],
          })}
        />,
      );
      expect(screen.getByText("矛盾祭神")).toBeInTheDocument();
      expect(screen.getByText("異なる見解を含む情報")).toBeInTheDocument();
    });

    it("disputed Historyは状態ラベルを表示し、本文はそのまま表示される", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                history_type: "founding",
                history_type_label: "創始",
                title: "矛盾由緒",
                content: "矛盾している内容そのもの",
                period_text: "",
                sort_order: 0,
                displayState: "disputed",
              },
            ],
          })}
        />,
      );
      expect(screen.getByText("矛盾由緒")).toBeInTheDocument();
      expect(screen.getByText("矛盾している内容そのもの")).toBeInTheDocument();
      expect(screen.getByText("異なる見解を含む情報")).toBeInTheDocument();
    });

    it("複数disputed Historyは自動統合・自動グルーピングされず個別表示される", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                history_type: "founding",
                history_type_label: "創始",
                title: "説A",
                content: "説Aの内容",
                period_text: "",
                sort_order: 0,
                displayState: "disputed",
              },
              {
                history_type: "historical_event",
                history_type_label: "歴史",
                title: "説B",
                content: "説Bの内容",
                period_text: "",
                sort_order: 1,
                displayState: "disputed",
              },
            ],
          })}
        />,
      );
      expect(screen.getByText("説A")).toBeInTheDocument();
      expect(screen.getByText("説Aの内容")).toBeInTheDocument();
      expect(screen.getByText("説B")).toBeInTheDocument();
      expect(screen.getByText("説Bの内容")).toBeInTheDocument();
      // 「複数説があります」等の自動生成メタ文言が存在しないことを確認する
      expect(screen.queryByText(/複数の説/)).not.toBeInTheDocument();
      expect(screen.queryByText(/複数説/)).not.toBeInTheDocument();
      // 状態ラベルは各Factごとに独立して2つ存在する（1つへ統合されない）
      expect(screen.getAllByText("異なる見解を含む情報")).toHaveLength(2);
    });

    it("full/disputedが混在しても、それぞれ独立して正しい表示になる", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            deities: [
              { display_name: "確定祭神", sort_order: 0, displayState: "full" },
              { display_name: "矛盾祭神", sort_order: 1, displayState: "disputed" },
            ],
          })}
        />,
      );
      expect(screen.getByText("確定祭神")).toBeInTheDocument();
      expect(screen.getByText("矛盾祭神")).toBeInTheDocument();
      expect(screen.getAllByText("異なる見解を含む情報")).toHaveLength(1);
    });

    it("正誤判定・比較文・矛盾の断定文言を生成しない", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            deities: [{ display_name: "矛盾祭神", sort_order: 0, displayState: "disputed" }],
          })}
        />,
      );
      expect(screen.queryByText(/誤り/)).not.toBeInTheDocument();
      expect(screen.queryByText(/間違い/)).not.toBeInTheDocument();
      expect(screen.queryByText(/矛盾しています/)).not.toBeInTheDocument();
      expect(screen.queryByText(/正しい/)).not.toBeInTheDocument();
      expect(screen.queryByText(/有力/)).not.toBeInTheDocument();
    });
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("disputedラベルがradius-pill / border-defaultを参照する", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            deities: [{ display_name: "矛盾祭神", sort_order: 0, displayState: "disputed" }],
          })}
        />,
      );
      const badge = screen.getByText("異なる見解を含む情報");
      expect(badge.className).toContain("rounded-[var(--kt-radius-pill)]");
      expect(badge.className).toContain("border-[var(--kt-color-border-default)]");
      expect(badge.className).toContain("text-[var(--kt-color-text-muted)]");
    });
  });
});
