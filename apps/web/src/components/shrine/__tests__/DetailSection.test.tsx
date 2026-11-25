import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DetailSection, { type DetailSectionVariant } from "../DetailSection";

const ALL_VARIANTS: DetailSectionVariant[] = ["primary", "secondary", "tertiary", "plain"];

describe("DetailSection", () => {
  it("renders the title as an <h2> and the children, for every variant", () => {
    ALL_VARIANTS.forEach((variant) => {
      const { unmount } = render(
        <DetailSection title={`見出し-${variant}`} variant={variant}>
          <p>本文-{variant}</p>
        </DetailSection>,
      );

      const heading = screen.getByRole("heading", { level: 2, name: `見出し-${variant}` });
      expect(heading.tagName).toBe("H2");
      expect(screen.getByText(`本文-${variant}`)).toBeInTheDocument();

      unmount();
    });
  });

  it("defaults to the secondary variant when none is given", () => {
    const { container } = render(
      <DetailSection title="既定">
        <p>本文</p>
      </DetailSection>,
    );

    const section = container.querySelector("section");
    expect(section?.className).toContain("border-[var(--kt-color-border-default)]");
    expect(section?.className).toContain("bg-[var(--kt-color-surface-default)]");
    expect(section?.className).toContain("shadow-[var(--kt-shadow-medium)]");
  });

  it("renders the optional right slot", () => {
    render(
      <DetailSection title="右スロット" right={<span>2026年8月</span>}>
        <p>本文</p>
      </DetailSection>,
    );

    expect(screen.getByText("2026年8月")).toBeInTheDocument();
  });

  describe("plain variant (additive, borderless editorial section)", () => {
    it("draws no surface: no border, background, shadow, radius, or padding class", () => {
      const { container } = render(
        <DetailSection title="意味" variant="plain">
          <p>本文</p>
        </DetailSection>,
      );

      const section = container.querySelector("section");
      const cls = section?.className ?? "";
      expect(cls).not.toMatch(/\bborder\b/);
      expect(cls).not.toMatch(/\bbg-\[/);
      expect(cls).not.toMatch(/\bshadow-\[/);
      expect(cls).not.toMatch(/\brounded-\[/);
      expect(cls).not.toMatch(/\bp-\d/);
    });

    it("keeps the strong heading weight (same title class as primary) and text-primary token", () => {
      render(
        <DetailSection title="意味" variant="plain">
          <p>本文</p>
        </DetailSection>,
      );

      const heading = screen.getByRole("heading", { level: 2, name: "意味" });
      expect(heading.className).toContain("text-base");
      expect(heading.className).toContain("font-semibold");
      expect(heading.className).toContain("text-[var(--kt-color-text-primary)]");
    });

    it("still applies a caller-supplied className (and does not leave stray whitespace)", () => {
      const { container } = render(
        <DetailSection title="意味" variant="plain" className="mt-6">
          <p>本文</p>
        </DetailSection>,
      );

      const section = container.querySelector("section");
      expect(section?.getAttribute("class")).toBe("mt-6");
    });
  });

  describe("surface variants keep their Design Token references", () => {
    it("primary references border-strong / surface-default / shadow-high", () => {
      const { container } = render(
        <DetailSection title="主" variant="primary">
          <p>本文</p>
        </DetailSection>,
      );

      const cls = container.querySelector("section")?.className ?? "";
      expect(cls).toContain("border-[var(--kt-color-border-strong)]");
      expect(cls).toContain("bg-[var(--kt-color-surface-default)]");
      expect(cls).toContain("shadow-[var(--kt-shadow-high)]");
    });

    it("tertiary references background-subtle and carries no shadow", () => {
      const { container } = render(
        <DetailSection title="補足" variant="tertiary">
          <p>本文</p>
        </DetailSection>,
      );

      const cls = container.querySelector("section")?.className ?? "";
      expect(cls).toContain("bg-[var(--kt-color-background-subtle)]");
      expect(cls).not.toContain("shadow-[");
    });
  });
});
