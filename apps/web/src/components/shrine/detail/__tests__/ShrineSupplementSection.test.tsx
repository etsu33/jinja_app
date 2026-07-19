import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineSupplementSection from "../ShrineSupplementSection";
import type { DetailSupplementSection } from "../types";

const section: DetailSupplementSection = {
  kind: "supplement",
  heading: "神社情報",
  groups: [{ title: "ご利益", items: ["健康"] }],
};

describe("ShrineSupplementSection", () => {
  it("見出し・group.title・タグを表示する", () => {
    render(<ShrineSupplementSection section={section} />);
    expect(screen.getByText("神社情報")).toBeInTheDocument();
    expect(screen.getByText("ご利益")).toBeInTheDocument();
    expect(screen.getByText("健康")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("sectionがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(<ShrineSupplementSection section={section} />);
      const outer = container.querySelector("section");
      expect(outer?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(outer?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(outer?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("見出しがtext-primaryを、group.titleがtext-secondaryを参照する", () => {
      render(<ShrineSupplementSection section={section} />);
      expect(screen.getByText("神社情報").className).toContain("text-[var(--kt-color-text-primary)]");
      expect(screen.getByText("ご利益").className).toContain("text-[var(--kt-color-text-secondary)]");
    });

    it("タグがradius-pillを参照する", () => {
      render(<ShrineSupplementSection section={section} />);
      expect(screen.getByText("健康").className).toContain("rounded-[var(--kt-radius-pill)]");
    });
  });
});
