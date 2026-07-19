import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// このテストは、Design Token v1定義基盤(docs/design/design-token.md)の
// 契約を検証する。CSS文字列の丸ごと比較(スナップショット)は行わず、
// 「必須のSemantic Tokenキーがtokens.css内に宣言として存在するか」
// 「Mobile側(apps/mobile)のSemantic Tokenキー一覧と意味上対応しているか」
// という契約レベルの検証に限定する。

const tokensCssPath = path.resolve(__dirname, "../tokens.css");
const globalsCssPath = path.resolve(__dirname, "../../app/globals.css");

const mobileSemanticColorPath = path.resolve(
  __dirname,
  "../../../../mobile/app/design/semanticColorTokens.ts",
);
const mobileSpacingPath = path.resolve(__dirname, "../../../../mobile/app/design/spacing.ts");
const mobileRadiusPath = path.resolve(__dirname, "../../../../mobile/app/design/radius.ts");
const mobileShadowPath = path.resolve(__dirname, "../../../../mobile/app/design/shadow.ts");

const tokensCss = readFileSync(tokensCssPath, "utf-8");
const globalsCss = readFileSync(globalsCssPath, "utf-8");

// dot区切り・camelCaseのMobileキー(例: "action.primaryHover")を、
// Web側のkebab-case CSS変数名の末尾部分(例: "action-primary-hover")へ変換する。
function toKebabSegments(key: string): string {
  return key
    .split(".")
    .map((segment) => segment.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase())
    .join("-");
}

// TypeScriptソースの `export const XXX_KEYS = [...] as const;` から
// 文字列リテラルのキー一覧を抽出する(importせず、テキストとして読むことで
// apps/web から apps/mobile への実行時モジュール依存を作らない)。
function extractKeysFromArrayLiteral(source: string, constName: string): string[] {
  const pattern = new RegExp(`export const ${constName} = \\[([\\s\\S]*?)\\] as const;`);
  const match = source.match(pattern);
  if (!match) {
    throw new Error(`${constName} not found in source`);
  }
  const body = match[1];
  const keyPattern = /"([^"]+)"/g;
  const keys: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = keyPattern.exec(body)) !== null) {
    keys.push(m[1]);
  }
  return keys;
}

describe("Web Design Token: tokens.css の必須キー網羅性", () => {
  const mobileColorSource = readFileSync(mobileSemanticColorPath, "utf-8");
  const semanticColorKeys = extractKeysFromArrayLiteral(mobileColorSource, "SEMANTIC_COLOR_KEYS");

  it("Mobile SEMANTIC_COLOR_KEYSの各キーに対応する --kt-color-* 宣言がtokens.cssに存在する", () => {
    expect(semanticColorKeys.length).toBeGreaterThan(0);

    for (const key of semanticColorKeys) {
      const cssVarName = `--kt-color-${toKebabSegments(key)}`;
      const declarationPattern = new RegExp(`${cssVarName}\\s*:`);
      expect(tokensCss, `${cssVarName} (Mobile key: "${key}") がtokens.cssに存在しない`).toMatch(
        declarationPattern,
      );
    }
  });

  const mobileSpacingSource = readFileSync(mobileSpacingPath, "utf-8");
  const semanticSpacingKeys = extractKeysFromArrayLiteral(mobileSpacingSource, "SEMANTIC_SPACING_KEYS");

  it("Mobile SEMANTIC_SPACING_KEYSの各キーに対応する --kt-space-* 宣言がtokens.cssに存在する", () => {
    expect(semanticSpacingKeys.length).toBeGreaterThan(0);

    for (const key of semanticSpacingKeys) {
      const cssVarName = `--kt-space-${toKebabSegments(key)}`;
      const declarationPattern = new RegExp(`${cssVarName}\\s*:`);
      expect(tokensCss, `${cssVarName} (Mobile key: "${key}") がtokens.cssに存在しない`).toMatch(
        declarationPattern,
      );
    }
  });

  const mobileRadiusSource = readFileSync(mobileRadiusPath, "utf-8");
  const semanticRadiusKeys = extractKeysFromArrayLiteral(mobileRadiusSource, "SEMANTIC_RADIUS_KEYS");

  it("Mobile SEMANTIC_RADIUS_KEYSの各キーに対応する --kt-radius-* 宣言がtokens.cssに存在する", () => {
    expect(semanticRadiusKeys.length).toBeGreaterThan(0);

    for (const key of semanticRadiusKeys) {
      const cssVarName = `--kt-radius-${toKebabSegments(key)}`;
      const declarationPattern = new RegExp(`${cssVarName}\\s*:`);
      expect(tokensCss, `${cssVarName} (Mobile key: "${key}") がtokens.cssに存在しない`).toMatch(
        declarationPattern,
      );
    }
  });

  const mobileShadowSource = readFileSync(mobileShadowPath, "utf-8");
  const semanticShadowKeys = extractKeysFromArrayLiteral(mobileShadowSource, "SEMANTIC_SHADOW_KEYS");

  it("Mobile SEMANTIC_SHADOW_KEYSの各キーに対応する --kt-shadow-* 宣言がtokens.cssに存在する", () => {
    expect(semanticShadowKeys.length).toBeGreaterThan(0);

    for (const key of semanticShadowKeys) {
      const cssVarName = `--kt-shadow-${toKebabSegments(key)}`;
      const declarationPattern = new RegExp(`${cssVarName}\\s*:`);
      expect(tokensCss, `${cssVarName} (Mobile key: "${key}") がtokens.cssに存在しない`).toMatch(
        declarationPattern,
      );
    }
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
