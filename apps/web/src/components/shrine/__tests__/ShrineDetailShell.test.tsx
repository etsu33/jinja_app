import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineDetailShell from "../ShrineDetailShell";

describe("ShrineDetailShell", () => {
  it("titleとsubtitleを表示する", () => {
    render(
      <ShrineDetailShell title="乃木神社" subtitle="東京都港区赤坂" close={{ kind: "back", label: "戻る" }} />,
    );

    expect(screen.getByText("乃木神社")).toBeInTheDocument();
    expect(screen.getByText("東京都港区赤坂")).toBeInTheDocument();
  });

  it("操作対象がない場合は操作sectionを表示しない", () => {
    render(<ShrineDetailShell title="乃木神社" close={{ kind: "back", label: "戻る" }} />);

    expect(screen.queryByText("操作")).not.toBeInTheDocument();
  });

  it("hideActionsがtrueの場合、CTAがあっても操作sectionを表示しない", () => {
    render(
      <ShrineDetailShell
        title="乃木神社"
        close={{ kind: "back", label: "戻る" }}
        googleDirHref="https://maps.google.com/?q=1,1"
        hideActions
      />,
    );

    expect(screen.queryByText("操作")).not.toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("titleがtext-primaryを、subtitleがtext-mutedを参照する", () => {
      render(
        <ShrineDetailShell title="乃木神社" subtitle="東京都港区赤坂" close={{ kind: "back", label: "戻る" }} />,
      );

      expect(screen.getByText("乃木神社").className).toContain("text-[var(--kt-color-text-primary)]");
      expect(screen.getByText("東京都港区赤坂").className).toContain("text-[var(--kt-color-text-muted)]");
    });

    it("経路案内CTAがradius-panel / text-inverseを参照する", () => {
      render(
        <ShrineDetailShell
          title="乃木神社"
          close={{ kind: "back", label: "戻る" }}
          googleDirHref="https://maps.google.com/?q=1,1"
        />,
      );

      const cta = screen.getByRole("link", { name: "Googleマップで経路案内" });
      expect(cta.className).toContain("rounded-[var(--kt-radius-panel)]");
      expect(cta.className).toContain("text-[var(--kt-color-text-inverse)]");
      // Route CTAはPrimary Action(Emerald)として表示する。旧slate-900のliteral直書きは使わない。
      expect(cta.className).toContain("bg-[var(--kt-color-action-primary)]");
      expect(cta.className).toContain("hover:bg-[var(--kt-color-action-primary-hover)]");
      expect(cta.className).not.toContain("slate-900");
      expect(cta.className).not.toContain("slate-800");
    });

    it("御朱印追加CTAがradius-panel / surface-default / text-primaryを参照する", () => {
      render(
        <ShrineDetailShell
          title="乃木神社"
          close={{ kind: "back", label: "戻る" }}
          addGoshuinHref="/shrines/17/goshuins/new"
        />,
      );

      const cta = screen.getByRole("link", { name: "御朱印を追加" });
      expect(cta.className).toContain("rounded-[var(--kt-radius-panel)]");
      expect(cta.className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(cta.className).toContain("text-[var(--kt-color-text-primary)]");
    });
  });
});
