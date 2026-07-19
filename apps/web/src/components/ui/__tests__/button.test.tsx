// apps/web/src/components/ui/__tests__/button.test.tsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "../button";

describe("Button", () => {
  it("calls onClick when button is clicked", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click Me</Button>);

    fireEvent.click(screen.getByRole("button", { name: "Click Me" }));
    expect(onClick).toHaveBeenCalled();
  });

  it("renders with different variants and sizes", () => {
    render(
      <div>
        <Button variant="destructive" size="sm">
          Small Destructive
        </Button>
        <Button variant="secondary" size="lg">
          Large Secondary
        </Button>
      </div>,
    );

    expect(screen.getByText("Small Destructive")).toBeInTheDocument();
    expect(screen.getByText("Large Secondary")).toBeInTheDocument();
  });

  it("renders with text and handles click", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>押す</Button>);

    const btn = screen.getByRole("button", { name: "押す" });
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("supports variant/size props", () => {
    render(
      <div>
        <Button variant="secondary" size="sm">
          Sec
        </Button>
        <Button variant="destructive" size="lg">
          Danger
        </Button>
      </div>,
    );

    expect(screen.getByRole("button", { name: "Sec" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Danger" })).toBeInTheDocument();
  });

  it("asChild=true では子要素をそのまま使う", () => {
    render(
      <Button asChild>
        <a href="/mypage">マイページリンク</a>
      </Button>,
    );

    const link = screen.getByRole("link", { name: "マイページリンク" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/mypage");
  });

  it("追加のclassNameがButtonへ維持される", () => {
    render(<Button className="custom-extra-class">追加class</Button>);
    expect(screen.getByRole("button", { name: "追加class" })).toHaveClass("custom-extra-class");
  });

  it("disabledのとき操作不能になる", () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        無効
      </Button>,
    );
    const btn = screen.getByRole("button", { name: "無効" });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("baseクラスがradius Semantic Tokenを参照する", () => {
      render(<Button>Base</Button>);
      expect(screen.getByRole("button", { name: "Base" }).className).toContain(
        "rounded-[var(--kt-radius-control)]",
      );
    });

    it("default variantがshadow Semantic Tokenを参照する", () => {
      render(<Button variant="default">Default</Button>);
      expect(screen.getByRole("button", { name: "Default" }).className).toContain(
        "shadow-[var(--kt-shadow-low)]",
      );
    });

    it("destructive variantがstatus-error Semantic Tokenを参照する", () => {
      render(<Button variant="destructive">Destructive</Button>);
      const className = screen.getByRole("button", { name: "Destructive" }).className;
      expect(className).toContain("bg-[var(--kt-color-status-error)]");
      expect(className).toContain("shadow-[var(--kt-shadow-low)]");
    });

    it("outline variantがsurface-default Semantic Tokenを参照する", () => {
      render(<Button variant="outline">Outline</Button>);
      const className = screen.getByRole("button", { name: "Outline" }).className;
      expect(className).toContain("bg-[var(--kt-color-surface-default)]");
      expect(className).toContain("shadow-[var(--kt-shadow-low)]");
    });

    it("secondary variantがshadow Semantic Tokenを参照する", () => {
      render(<Button variant="secondary">Secondary</Button>);
      expect(screen.getByRole("button", { name: "Secondary" }).className).toContain(
        "shadow-[var(--kt-shadow-low)]",
      );
    });
  });
});
