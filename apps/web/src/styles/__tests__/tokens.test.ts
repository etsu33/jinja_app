import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// このテストは、Design Token v1定義基盤(docs/design/design-token.md)における
// WebのCSS Token契約のみを検証する。
//
// 意図的にapps/mobileのソースは読まない。Web/Mobile間のSemantic Token
// キーの意味対応は、実行時のクロスファイル突合ではなく
// docs/design/design-token.md (正本) で管理する。Web側はWeb自身の
// 契約(tokens.cssが正本ドキュメントの記載キーを過不足なく持つか)のみを
// 検証し、Mobile側はapps/mobile側の型契約(satisfies PlatformColorTheme等)
// で独立して保証する。
//
// 以下のキー一覧は docs/design/design-token.md の
// Color / Spacing / Radius / Shadow / Elevation 節に列挙された
// Semantic Tokenキーをこのテストファイル内にのみ複製したものであり、
// 新たな共有Token定義ファイルではない。

const REQUIRED_COLOR_KEYS = [
  "background-base",
  "background-subtle",
  "surface-default",
  "surface-elevated",
  "text-primary",
  "text-secondary",
  "text-muted",
  "text-inverse",
  "border-default",
  "border-strong",
  "border-focus",
  "action-primary",
  "action-primary-hover",
  "action-primary-text",
  "action-disabled",
  "status-success",
  "status-warning",
  "status-error",
  "status-info",
  "premium-accent",
  "premium-surface",
  "premium-border",
  "overlay-default",
];

const REQUIRED_SPACE_KEYS = ["page-x", "section-y", "card", "control-x", "control-y", "inline-gap", "stack-gap"];

const REQUIRED_RADIUS_KEYS = ["control", "card", "panel", "modal", "image", "pill"];

const REQUIRED_SHADOW_KEYS = ["none", "low", "medium", "high", "brand"];

const tokensCssPath = path.resolve(__dirname, "../tokens.css");
const globalsCssPath = path.resolve(__dirname, "../../app/globals.css");

const tokensCss = readFileSync(tokensCssPath, "utf-8");
const globalsCss = readFileSync(globalsCssPath, "utf-8");

function expectDeclared(prefix: string, keys: string[]) {
  for (const key of keys) {
    const cssVarName = `${prefix}-${key}`;
    const declarationPattern = new RegExp(`${cssVarName}\\s*:`);
    expect(tokensCss, `${cssVarName} がtokens.cssに存在しない`).toMatch(declarationPattern);
  }
}

describe("Web Design Token: tokens.css の必須キー網羅性", () => {
  it("Color: design-token.md記載のSemantic Color Keyに対応する --kt-color-* 宣言が存在する", () => {
    expectDeclared("--kt-color", REQUIRED_COLOR_KEYS);
  });

  it("Spacing: design-token.md記載のSemantic Spacing Keyに対応する --kt-space-* 宣言が存在する", () => {
    expectDeclared("--kt-space", REQUIRED_SPACE_KEYS);
  });

  it("Radius: design-token.md記載のSemantic Radius Keyに対応する --kt-radius-* 宣言が存在する", () => {
    expectDeclared("--kt-radius", REQUIRED_RADIUS_KEYS);
  });

  it("Shadow: design-token.md記載のSemantic Shadow Keyに対応する --kt-shadow-* 宣言が存在する", () => {
    expectDeclared("--kt-shadow", REQUIRED_SHADOW_KEYS);
  });
});

describe("Web Design Token: 既存Tokenの非破壊確認", () => {
  it("globals.cssが新しいtokens.cssをimportしている", () => {
    expect(globalsCss).toMatch(/@import\s+["']\.\.\/styles\/tokens\.css["'];/);
  });

  it("既存のshadcn Semantic Token (--background 等) がglobals.cssに残っている", () => {
    const requiredExistingTokens = [
      "--background:",
      "--foreground:",
      "--primary:",
      "--secondary:",
      "--muted:",
      "--accent:",
      "--destructive:",
      "--border:",
      "--input:",
      "--ring:",
      "--radius:",
    ];
    for (const token of requiredExistingTokens) {
      expect(globalsCss, `${token} がglobals.cssから失われている`).toContain(token);
    }
  });

  it("既存の@theme inlineブロックが残っている", () => {
    expect(globalsCss).toContain("@theme inline");
    expect(globalsCss).toContain("--color-background: var(--background);");
  });

  it("新しいkt-*変数名は既存のshadcn変数名(プレフィックスなし)と衝突しない", () => {
    // tokens.css内の全カスタムプロパティ宣言が --kt- プレフィックスを持つことを確認する
    const declarationLines = tokensCss
      .split("\n")
      .filter((line) => /^\s*--[a-zA-Z0-9-]+\s*:/.test(line));

    expect(declarationLines.length).toBeGreaterThan(0);

    for (const line of declarationLines) {
      expect(line, `tokens.css内の宣言が --kt- プレフィックスを持たない: ${line.trim()}`).toMatch(
        /--kt-/,
      );
    }
  });
});
