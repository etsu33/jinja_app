import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { HomeMainClient } from "../HomeMainClient";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("HomeMainClient", () => {
  it("既存のConcierge Heroをそのまま保持する", () => {
    render(<HomeMainClient />);
    expect(screen.getByRole("heading", { level: 1, name: "今の相談から、向かう神社を見つける" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "この相談ではじめる" })).toBeInTheDocument();
  });

  it("Compassへの独立した入口を、SUB PATHSとは別セクションとして表示する", () => {
    render(<HomeMainClient />);

    const compassHeading = screen.getByRole("heading", { level: 2, name: "方向から探す" });
    expect(compassHeading).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "参拝コンパスを見る" })).toHaveAttribute("href", "/compass?ref=home");
  });

  it("Compassセクションの見出しは、Concierge前提のSUB PATHS見出しとは異なる文言を持つ", () => {
    render(<HomeMainClient />);

    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toContain("方向から探す");
    expect(headings).toContain("相談のあとに、場所でも確かめる");
    // Compass's own heading must not presuppose Concierge came first.
    expect(screen.getByRole("heading", { level: 2, name: "方向から探す" }).textContent).not.toMatch(/相談/);
  });

  it("既存SUB PATHS（地図・神社一覧）はそのまま保持される", () => {
    render(<HomeMainClient />);
    expect(screen.getByRole("link", { name: "地図でも確認する" })).toHaveAttribute("href", "/map");
    expect(screen.getByRole("link", { name: "神社一覧も見る" })).toHaveAttribute("href", "/shrines");
  });

  it("見出しの出現順はHero → Compass入口 → SUB PATHSの順を維持する", () => {
    render(<HomeMainClient />);
    const headingTexts = [
      screen.getByRole("heading", { level: 1 }).textContent,
      ...screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent),
    ];
    expect(headingTexts).toEqual([
      "今の相談から、向かう神社を見つける",
      "方向から探す",
      "相談のあとに、場所でも確かめる",
    ]);
  });
});
