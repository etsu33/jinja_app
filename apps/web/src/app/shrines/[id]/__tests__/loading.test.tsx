import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineDetailLoading from "../loading";

const source = readFileSync(path.resolve(__dirname, "../loading.tsx"), "utf8");

describe("/shrines/[id] loading boundary", () => {
  it("読み込み中であることを status 1つで伝える", () => {
    render(<ShrineDetailLoading />);

    const statuses = screen.getAllByRole("status");
    expect(statuses).toHaveLength(1);
    expect(statuses[0]).toHaveTextContent("神社の情報を読み込み中です");
  });

  it("Shrine Detail の主要な骨格（header / 操作 / 神社名 / 本文）を描画する", () => {
    const { container } = render(<ShrineDetailLoading />);

    const regions = Array.from(container.querySelectorAll("[data-skeleton-region]")).map((el) =>
      el.getAttribute("data-skeleton-region"),
    );
    expect(regions).toEqual(["header", "actions", "title", "section", "section"]);
  });

  it("骨格の図形は支援技術から隠し、status 以外の文言を持たない", () => {
    const { container } = render(<ShrineDetailLoading />);

    const decorative = container.querySelector('[aria-hidden="true"]');
    expect(decorative).not.toBeNull();
    expect(decorative?.textContent?.trim()).toBe("");
    expect(screen.queryByRole("heading")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();

    const root = screen.getByTestId("shrine-detail-loading");
    expect(root.textContent?.trim()).toBe("神社の情報を読み込み中です");
  });

  it("実データや API に依存せず、世界観フレームを重ねない（app/shrines/layout.tsx が持つ）", () => {
    expect(source).not.toMatch(/^import /m);
    expect(source).not.toMatch(/WorldviewFrame|WorldviewBackdrop/);
  });

  it("Shell と同じ外枠を持ち、ライト前提の固定色を使わない", () => {
    render(<ShrineDetailLoading />);

    const root = screen.getByTestId("shrine-detail-loading");
    expect(root.className).toContain("min-h-[calc(100vh-64px)]");
    expect(root.className).toContain("max-w-md");
    expect(source).not.toMatch(/\b(bg-white|(bg|text|border)-(stone|slate|gray)-\d)/);
  });
});
