import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineJudgeSection from "../ShrineJudgeSection";
import type { DetailMeaningSection } from "../types";

function buildSection(overrides: Partial<DetailMeaningSection> = {}): DetailMeaningSection {
  return {
    kind: "meaning",
    heading: "この神社で受け取る意味",
    items: [
      { key: "shrine_meaning", title: "この神社の意味", body: "本文A" },
      { key: "action_meaning", title: "参拝するときの視点", body: "本文B" },
      { key: "today_flow", title: "今日の流れ", body: "本文C" },
      { key: "history_context", title: "由緒", body: "本文D" },
    ],
    ...overrides,
  };
}

describe("ShrineJudgeSection", () => {
  it("free/premium区分にかかわらずitemsのtitle/bodyを表示する", () => {
    render(<ShrineJudgeSection section={buildSection()} />);

    expect(screen.getByText("この神社の意味")).toBeInTheDocument();
    expect(screen.getByText("本文A")).toBeInTheDocument();
    expect(screen.getByText("参拝するときの視点")).toBeInTheDocument();
    expect(screen.getByText("本文B")).toBeInTheDocument();
  });

  it("見出しが「補足」で始まる場合、details/summaryのfallback表示になる", () => {
    const { container } = render(
      <ShrineJudgeSection section={buildSection({ heading: "補足情報" })} />,
    );

    expect(container.querySelector("details")).toBeInTheDocument();
    expect(container.querySelector("summary")).toBeInTheDocument();
    expect(screen.getByText("補足情報")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("通常sectionがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(<ShrineJudgeSection section={buildSection()} />);
      const section = container.querySelector("section");
      expect(section?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(section?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(section?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("見出しがtext-primaryを参照する", () => {
      render(<ShrineJudgeSection section={buildSection()} />);
      expect(screen.getByText("この神社で受け取る意味").className).toContain(
        "text-[var(--kt-color-text-primary)]",
      );
    });

    it("action_meaning itemがpremium-border / premium-surface / shadow-mediumを参照する", () => {
      render(<ShrineJudgeSection section={buildSection()} />);
      const item = screen.getByText("参拝するときの視点").closest("div");
      expect(item?.className).toContain("border-[var(--kt-color-premium-border)]");
      expect(item?.className).toContain("bg-[var(--kt-color-premium-surface)]");
      expect(item?.className).toContain("shadow-[var(--kt-shadow-medium)]");
    });

    it("history_context itemのtitleとbodyがtext-mutedを参照する", () => {
      render(<ShrineJudgeSection section={buildSection()} />);
      expect(screen.getByText("由緒").className).toContain("text-[var(--kt-color-text-muted)]");
      expect(screen.getByText("本文D").className).toContain("text-[var(--kt-color-text-muted)]");
    });

    it("補足sectionのdetails/summaryがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(
        <ShrineJudgeSection section={buildSection({ heading: "補足情報" })} />,
      );
      const details = container.querySelector("details");
      expect(details?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(details?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(details?.className).toContain("bg-[var(--kt-color-surface-default)]");

      const badge = screen.getByText("補足情報");
      expect(badge.className).toContain("rounded-[var(--kt-radius-pill)]");
      expect(badge.className).toContain("border-[var(--kt-color-border-default)]");
      expect(badge.className).toContain("bg-[var(--kt-color-background-subtle)]");
    });
  });
});
