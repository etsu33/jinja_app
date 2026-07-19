import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineProposalSection from "../ShrineProposalSection";
import type { DetailProposalSection } from "../types";

const section: DetailProposalSection = {
  kind: "proposal",
  heading: "今の状態整理",
  lead: "リード文",
  body: "本文",
};

describe("ShrineProposalSection", () => {
  it("見出し・lead・bodyを表示する", () => {
    render(<ShrineProposalSection section={section} />);
    expect(screen.getByText("今の状態整理")).toBeInTheDocument();
    expect(screen.getByText("リード文")).toBeInTheDocument();
    expect(screen.getByText("本文")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("sectionがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(<ShrineProposalSection section={section} />);
      const outer = container.querySelector("section");
      expect(outer?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(outer?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(outer?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("見出しがtext-primaryを参照する", () => {
      render(<ShrineProposalSection section={section} />);
      expect(screen.getByText("今の状態整理").className).toContain("text-[var(--kt-color-text-primary)]");
    });
  });
});
