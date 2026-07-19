import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DetailDisclosureBlock from "../DetailDisclosureBlock";

describe("DetailDisclosureBlock", () => {
  it("初期状態では閉じており、aria-expandedはfalseでchildrenは表示されない", () => {
    render(
      <DetailDisclosureBlock title="ご利益" summary="要約テキスト">
        <p>詳細本文</p>
      </DetailDisclosureBlock>,
    );

    const trigger = screen.getByRole("button", { name: /ご利益/ });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("詳細本文")).not.toBeInTheDocument();
  });

  it("クリックすると開き、aria-expandedがtrueになりchildrenが表示される", () => {
    render(
      <DetailDisclosureBlock title="ご利益" summary="要約テキスト">
        <p>詳細本文</p>
      </DetailDisclosureBlock>,
    );

    fireEvent.click(screen.getByRole("button", { name: /ご利益/ }));

    const trigger = screen.getByRole("button", { name: /ご利益/ });
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("詳細本文")).toBeInTheDocument();
  });

  it("再度クリックすると閉じ、childrenが非表示になる", () => {
    render(
      <DetailDisclosureBlock title="ご利益" summary="要約テキスト">
        <p>詳細本文</p>
      </DetailDisclosureBlock>,
    );

    const trigger = screen.getByRole("button", { name: /ご利益/ });
    fireEvent.click(trigger);
    fireEvent.click(trigger);

    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("詳細本文")).not.toBeInTheDocument();
  });

  it("defaultOpenがtrueの場合、初期状態から開いて表示する", () => {
    render(
      <DetailDisclosureBlock title="ご利益" summary="要約テキスト" defaultOpen>
        <p>詳細本文</p>
      </DetailDisclosureBlock>,
    );

    expect(screen.getByRole("button", { name: /ご利益/ })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("詳細本文")).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("外枠がradius-card / surface-defaultを参照する", () => {
      const { container } = render(
        <DetailDisclosureBlock title="ご利益" summary="要約テキスト">
          <p>詳細本文</p>
        </DetailDisclosureBlock>,
      );

      const wrapper = container.firstElementChild;
      expect(wrapper?.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(wrapper?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });

    it("titleがtext-primaryを、開閉パネルがsurface-defaultを参照する", () => {
      render(
        <DetailDisclosureBlock title="ご利益" summary="要約テキスト" hint="補足ヒント">
          <p>詳細本文</p>
        </DetailDisclosureBlock>,
      );

      expect(screen.getByText("ご利益").className).toContain("text-[var(--kt-color-text-primary)]");

      fireEvent.click(screen.getByRole("button", { name: /ご利益/ }));

      expect(screen.getByText("補足ヒント").className).toContain("text-[var(--kt-color-text-muted)]");
    });

    it("levelバッジがradius-pillを参照する", () => {
      render(
        <DetailDisclosureBlock title="ご利益" summary="要約テキスト" level="strong">
          <p>詳細本文</p>
        </DetailDisclosureBlock>,
      );

      expect(screen.getByText("高").className).toContain("rounded-[var(--kt-radius-pill)]");
    });

    it("materialsがある場合、材料ブロックがradius-panel / surface-defaultを参照する", () => {
      render(
        <DetailDisclosureBlock
          title="ご利益"
          summary="要約テキスト"
          materials={[{ label: "五行", value: "木" }]}
        >
          <p>詳細本文</p>
        </DetailDisclosureBlock>,
      );

      const materialsHeading = screen.getByText("材料");
      const materialsBlock = materialsHeading.parentElement;
      expect(materialsBlock?.className).toContain("rounded-[var(--kt-radius-panel)]");
      expect(materialsBlock?.className).toContain("bg-[var(--kt-color-surface-default)]");
    });
  });
});
