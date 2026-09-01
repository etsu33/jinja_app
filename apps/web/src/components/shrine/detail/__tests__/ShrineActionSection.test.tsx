import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineActionSection from "../ShrineActionSection";
import type { DetailActionSection } from "../types";

const section: DetailActionSection = {
  kind: "action",
  heading: "参拝するときの視点",
  items: [{ key: "action_meaning", title: "向き合い方", body: "本文" }],
};

describe("ShrineActionSection", () => {
  it("見出しとitemのtitle/bodyを表示する", () => {
    render(<ShrineActionSection section={section} />);
    expect(screen.getByText("参拝するときの視点")).toBeInTheDocument();
    expect(screen.getByText("向き合い方")).toBeInTheDocument();
    expect(screen.getByText("本文")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("外枠sectionがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(<ShrineActionSection section={section} />);
      const outer = container.querySelector("section");
      expect(outer?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(outer?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(outer?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("見出しがtext-primaryを参照する", () => {
      render(<ShrineActionSection section={section} />);
      expect(screen.getByText("参拝するときの視点").className).toContain(
        "text-[var(--kt-color-text-primary)]",
      );
    });

    it("itemカードがpremium-border / premium-surface / shadow-mediumを参照する", () => {
      render(<ShrineActionSection section={section} />);
      const item = screen.getByText("向き合い方").closest("div");
      expect(item?.className).toContain("border-[var(--kt-color-premium-border)]");
      expect(item?.className).toContain("bg-[var(--kt-color-premium-surface)]");
      expect(item?.className).toContain("shadow-[var(--kt-shadow-medium)]");
    });
  });

  describe("variant=plain (PR-G3 editorial flow)", () => {
    it("borderless: 外枠section・itemにborder/surface/shadow/amberを持たず、title/bodyは維持する", () => {
      const { container } = render(<ShrineActionSection section={section} variant="plain" />);

      const outer = container.querySelector("section")!;
      expect(outer.className).not.toMatch(/\bborder\b/);
      expect(outer.className).not.toContain("bg-[var(--kt-color-surface-default)]");

      const item = screen.getByText("向き合い方").closest("div")!;
      expect(item.className).not.toMatch(/amber-\d/);
      expect(item.className).not.toContain("bg-[var(--kt-color-premium-surface)]");
      expect(item.className).not.toMatch(/shadow-\[/);

      expect(screen.getByText("参拝するときの視点").tagName).toBe("H2");
      expect(screen.getByText("向き合い方")).toBeInTheDocument();
      expect(screen.getByText("本文")).toBeInTheDocument();
    });
  });
});
