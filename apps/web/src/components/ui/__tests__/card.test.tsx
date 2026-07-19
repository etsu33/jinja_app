import { render, screen } from "@testing-library/react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
  CardAction,
} from "../card"; // ← CardActionを追加

describe("Card", () => {
  it("renders header/content/footer", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>タイトル</CardTitle>
        </CardHeader>
        <CardContent>本文</CardContent>
        <CardFooter>フッタ</CardFooter>
      </Card>
    );
    expect(screen.getByText("タイトル")).toBeInTheDocument();
    expect(screen.getByText("本文")).toBeInTheDocument();
    expect(screen.getByText("フッタ")).toBeInTheDocument();
  });

  it("renders card action", () => {
    render(
      <Card>
        <CardAction>Click me</CardAction>
      </Card>
    );
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("renders description", () => {
    render(
      <Card>
        <CardDescription>説明文</CardDescription>
      </Card>,
    );
    expect(screen.getByText("説明文")).toBeInTheDocument();
  });

  it("追加のclassNameがCardへ維持される", () => {
    const { container } = render(<Card className="custom-extra-class">本文</Card>);
    expect(container.querySelector('[data-slot="card"]')).toHaveClass("custom-extra-class");
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("Cardがsurface-default / shadow-medium Semantic Tokenを参照する", () => {
      const { container } = render(<Card>本文</Card>);
      const className = container.querySelector('[data-slot="card"]')?.className ?? "";
      expect(className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(className).toContain("shadow-[var(--kt-shadow-medium)]");
    });

    it("CardDescriptionがtext-muted Semantic Tokenを参照する", () => {
      const { container } = render(
        <Card>
          <CardDescription>説明</CardDescription>
        </Card>,
      );
      const className = container.querySelector('[data-slot="card-description"]')?.className ?? "";
      expect(className).toContain("text-[var(--kt-color-text-muted)]");
    });
  });
});
