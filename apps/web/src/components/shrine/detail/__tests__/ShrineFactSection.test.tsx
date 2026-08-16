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

  // docs/knowledge/shrine-knowledge-contract.md「Presentation Groupingの契約」
  describe("Presentation Grouping (PR-B)", () => {
    it("1件だけのcanonical typeも見出し付きで自然に表示される", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                id: 1,
                history_type: "founding",
                history_type_label: "創始",
                title: "単独の由緒",
                content: "単独の内容",
                period_text: "",
                sort_order: 0,
                displayState: "full",
                sources: [],
              },
            ],
          })}
        />,
      );

      expect(screen.getByText("創始")).toBeInTheDocument();
      expect(screen.getByText("単独の由緒")).toBeInTheDocument();
    });

    it("同一history_typeの非disputed Factは1つの見出しの下にまとまり、両方のFactが表示される", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                id: 1,
                history_type: "historical_event",
                history_type_label: "歴史",
                title: "説A",
                content: "説Aの内容",
                period_text: "",
                sort_order: 0,
                displayState: "full",
                sources: [],
              },
              {
                id: 2,
                history_type: "historical_event",
                history_type_label: "歴史",
                title: "説B",
                content: "説Bの内容",
                period_text: "",
                sort_order: 1,
                displayState: "full",
                sources: [],
              },
            ],
          })}
        />,
      );

      // 見出し「歴史」は1つだけ（各cardの個別ラベルとしては重複表示しない）
      expect(screen.getAllByText("歴史")).toHaveLength(1);
      expect(screen.getByText("説A")).toBeInTheDocument();
      expect(screen.getByText("説Aの内容")).toBeInTheDocument();
      expect(screen.getByText("説B")).toBeInTheDocument();
      expect(screen.getByText("説Bの内容")).toBeInTheDocument();
    });

    it("history_typeが異なるFactは別々の見出しの下に分かれる", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                id: 1,
                history_type: "founding",
                history_type_label: "創始",
                title: "創始の由緒",
                content: "内容",
                period_text: "",
                sort_order: 0,
                displayState: "full",
                sources: [],
              },
              {
                id: 2,
                history_type: "tradition",
                history_type_label: "伝承",
                title: "伝承の由緒",
                content: "内容",
                period_text: "",
                sort_order: 1,
                displayState: "full",
                sources: [],
              },
            ],
          })}
        />,
      );

      expect(screen.getByText("創始")).toBeInTheDocument();
      expect(screen.getByText("伝承")).toBeInTheDocument();
      expect(screen.getByText("創始の由緒")).toBeInTheDocument();
      expect(screen.getByText("伝承の由緒")).toBeInTheDocument();
    });

    it("disputedなFactは通常のgroupingへ折り込まれず、既存どおり個別のtype labelとdisputedラベル付きで表示される", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                id: 1,
                history_type: "tradition",
                history_type_label: "伝承",
                title: "確定した伝承",
                content: "内容A",
                period_text: "",
                sort_order: 0,
                displayState: "full",
                sources: [],
              },
              {
                id: 2,
                history_type: "tradition",
                history_type_label: "伝承",
                title: "対立する説",
                content: "内容B",
                period_text: "",
                sort_order: 1,
                displayState: "disputed",
                sources: [],
              },
            ],
          })}
        />,
      );

      // グルーピングされた「伝承」見出しは1つ、disputed Factは個別のtype labelを保持するため
      // 「伝承」というテキストは見出し用1つ + disputed cardの個別ラベル1つ = 合計2つ表示される
      expect(screen.getAllByText("伝承")).toHaveLength(2);
      expect(screen.getByText("確定した伝承")).toBeInTheDocument();
      expect(screen.getByText("対立する説")).toBeInTheDocument();
      expect(screen.getByText("異なる見解を含む情報")).toBeInTheDocument();
    });

    it("各Factは自身のsourcesのみを表示する（groupで共有・曖昧化しない）", () => {
      render(
        <ShrineFactSection
          section={makeSection({
            histories: [
              {
                id: 1,
                history_type: "tradition",
                history_type_label: "伝承",
                title: "説A",
                content: "内容A",
                period_text: "",
                sort_order: 0,
                displayState: "full",
                sources: [
                  {
                    id: 100,
                    source_type: "shrine_official",
                    title: "史料A",
                    publisher: "",
                    url: "https://example.com/a",
                    verification_status: "source_confirmed",
                    confidence: "high",
                  },
                ],
              },
              {
                id: 2,
                history_type: "tradition",
                history_type_label: "伝承",
                title: "説B",
                content: "内容B",
                period_text: "",
                sort_order: 1,
                displayState: "full",
                sources: [
                  {
                    id: 101,
                    source_type: "local_history",
                    title: "史料B",
                    publisher: "",
                    url: "",
                    verification_status: "source_confirmed",
                    confidence: "high",
                  },
                ],
              },
            ],
          })}
        />,
      );

      const sourceALink = screen.getByRole("link", { name: "史料A" });
      expect(sourceALink).toHaveAttribute("href", "https://example.com/a");
      expect(screen.getByText("史料B")).toBeInTheDocument();
      expect(screen.queryByRole("link", { name: "史料B" })).not.toBeInTheDocument();
    });

    it("sourcesが空/未指定のFactはSource一覧を表示しない（クラッシュしない）", () => {
      expect(() =>
        render(
          <ShrineFactSection
            section={makeSection({
              histories: [
                {
                  id: 1,
                  history_type: "founding",
                  history_type_label: "創始",
                  title: "由緒A",
                  content: "内容A",
                  period_text: "",
                  sort_order: 0,
                  displayState: "full",
                },
              ],
            })}
          />,
        ),
      ).not.toThrow();

      expect(screen.getByText("由緒A")).toBeInTheDocument();
    });
  });
});
