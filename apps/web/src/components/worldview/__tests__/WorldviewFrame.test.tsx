import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

// WorldviewFrame の契約:
// - 世界観フレームの目印と variant を持つ
// - Backdrop はちょうど1つ（入れ子にしても1画面1 backdrop になるよう、Frame自身は1つだけ描く）
// - Backdrop は装飾 (aria-hidden / pointer-events-none) で、本文は z-10 で上に重なる
// - 業務ロジックを持たない（children をそのまま描く）

describe("WorldviewFrame", () => {
  it("既定は standard variant で、Backdrop をちょうど1つ描く", () => {
    const { container } = render(
      <WorldviewFrame>
        <p>本文</p>
      </WorldviewFrame>,
    );
    const frame = container.querySelector("[data-worldview-frame]");
    expect(frame?.getAttribute("data-worldview-frame")).toBe("standard");
    expect(container.querySelectorAll("[data-worldview-backdrop]")).toHaveLength(1);
    expect(container.querySelector("[data-worldview-backdrop]")?.getAttribute("data-worldview-backdrop")).toBe(
      "standard",
    );
  });

  it("quiet variant を渡せる", () => {
    const { container } = render(
      <WorldviewFrame variant="quiet">
        <p>本文</p>
      </WorldviewFrame>,
    );
    expect(container.querySelector("[data-worldview-frame]")?.getAttribute("data-worldview-frame")).toBe("quiet");
    expect(container.querySelector("[data-worldview-backdrop]")?.getAttribute("data-worldview-backdrop")).toBe("quiet");
  });

  it("Backdrop は装飾で、操作と読み上げを奪わない", () => {
    const { container } = render(
      <WorldviewFrame>
        <button type="button">操作</button>
      </WorldviewFrame>,
    );
    const backdrop = container.querySelector("[data-worldview-backdrop]");
    expect(backdrop?.getAttribute("aria-hidden")).toBe("true");
    expect(backdrop?.className).toContain("pointer-events-none");
    expect(backdrop?.contains(container.querySelector("button"))).toBe(false);
  });

  it("重なり順を分離し、本文は Backdrop より上に描く", () => {
    const { container, getByText } = render(
      <WorldviewFrame>
        <p>本文</p>
      </WorldviewFrame>,
    );
    const frame = container.querySelector("[data-worldview-frame]");
    expect(frame).toHaveClass("relative", "isolate", "bg-[var(--kt-color-background-base)]");
    const content = getByText("本文").parentElement;
    expect(content).toHaveClass("relative", "z-10");
    expect(content?.parentElement).toBe(frame);
  });

  it("幅・余白を足さない（ページ固有の余白は各ページが持つ）", () => {
    const { container } = render(
      <WorldviewFrame>
        <p>本文</p>
      </WorldviewFrame>,
    );
    const frame = container.querySelector("[data-worldview-frame]") as HTMLElement;
    expect(frame.className).not.toMatch(/\b(max-w-|mx-auto|p[xytblr]?-\d)/);
  });
});
