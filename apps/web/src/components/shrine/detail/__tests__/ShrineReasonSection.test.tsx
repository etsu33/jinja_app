import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineReasonSection from "../ShrineReasonSection";
import type { DetailReasonSection } from "../types";

const section: DetailReasonSection = {
  kind: "reason",
  heading: "この神社が候補に入った理由",
  groups: [{ title: "主理由", items: ["理由テキスト"] }],
};

describe("ShrineReasonSection", () => {
  it("見出し・group.title・itemを表示する", () => {
    render(<ShrineReasonSection section={section} />);
    expect(screen.getByText("この神社が候補に入った理由")).toBeInTheDocument();
    expect(screen.getByText("主理由")).toBeInTheDocument();
    expect(screen.getByText("理由テキスト")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("sectionがradius-card / border-default / surface-defaultを参照する", () => {
      const { container } = render(<ShrineReasonSection section={section} />);
      const outer = container.querySelector("section");
      expect(outer?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(outer?.className).toContain("border-[var(--kt-color-border-default)]");
      expect(outer?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("見出しがtext-primaryを、group.titleとitemがtext-secondaryを参照する", () => {
      render(<ShrineReasonSection section={section} />);
      expect(screen.getByText("この神社が候補に入った理由").className).toContain(
        "text-[var(--kt-color-text-primary)]",
      );
      expect(screen.getByText("主理由").className).toContain("text-[var(--kt-color-text-secondary)]");
      expect(screen.getByText("理由テキスト").className).toContain("text-[var(--kt-color-text-secondary)]");
    });
  });
});
