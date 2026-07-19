import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Input } from "../input";

describe("Input", () => {
  it("入力欄として描画される", () => {
    render(<Input placeholder="例: なまえ" />);
    expect(screen.getByPlaceholderText("例: なまえ")).toBeInTheDocument();
  });

  it("value/onChangeが機能する", () => {
    const onChange = vi.fn();
    render(<Input value="初期値" onChange={onChange} readOnly={false} />);
    const input = screen.getByDisplayValue("初期値");
    fireEvent.change(input, { target: { value: "変更後" } });
    expect(onChange).toHaveBeenCalled();
  });

  it("disabledのとき操作不能になる", () => {
    render(<Input disabled placeholder="無効" />);
    expect(screen.getByPlaceholderText("無効")).toBeDisabled();
  });

  it("追加のclassNameが維持される", () => {
    render(<Input className="custom-extra-class" placeholder="test" />);
    expect(screen.getByPlaceholderText("test")).toHaveClass("custom-extra-class");
  });

  it("aria-invalidを受け取れる", () => {
    render(<Input aria-invalid="true" placeholder="不正値" />);
    expect(screen.getByPlaceholderText("不正値")).toHaveAttribute("aria-invalid", "true");
  });

  it("refで実DOM要素を参照できる", () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Input ref={ref} placeholder="ref確認" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("type='file'を指定できる(file input互換)", () => {
    const { container } = render(<Input type="file" />);
    const input = container.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("border-default / shadow-low / radius-control / text-muted / status-errorを参照する", () => {
      render(<Input placeholder="token" />);
      const className = screen.getByPlaceholderText("token").className;
      expect(className).toContain("border-[var(--kt-color-border-default)]");
      expect(className).toContain("shadow-[var(--kt-shadow-low)]");
      expect(className).toContain("rounded-[var(--kt-radius-control)]");
      expect(className).toContain("placeholder:text-[var(--kt-color-text-muted)]");
      expect(className).toContain("aria-invalid:border-[var(--kt-color-status-error)]");
    });
  });
});
