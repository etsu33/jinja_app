import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineDetailHeroCard from "../ShrineDetailHeroCard";

describe("ShrineDetailHeroCard", () => {
  it("神社名を表示する", () => {
    render(<ShrineDetailHeroCard title="乃木神社" />);
    expect(screen.getByText("乃木神社")).toBeInTheDocument();
  });

  it("imageUrlがない場合はimg要素を表示しない", () => {
    const { container } = render(<ShrineDetailHeroCard title="乃木神社" imageUrl={null} />);
    expect(container.querySelector("img")).not.toBeInTheDocument();
  });

  it("imageUrlがある場合はimg要素を表示する", () => {
    render(<ShrineDetailHeroCard title="乃木神社" imageUrl="https://example.com/photo.jpg" />);
    expect(screen.getByAltText("乃木神社")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("外枠カードがradius-card / border-default / surface-default / shadow-mediumを参照する", () => {
      const { container } = render(<ShrineDetailHeroCard title="乃木神社" />);

      const article = container.querySelector("article");
      expect(article?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(article?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(article?.className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(article?.className).toContain("shadow-[var(--kt-shadow-medium)]");
    });

    it("神社名がtext-primaryを参照する", () => {
      render(<ShrineDetailHeroCard title="乃木神社" />);
      expect(screen.getByText("乃木神社").className).toContain("text-[var(--kt-color-text-primary)]");
    });
  });
});
