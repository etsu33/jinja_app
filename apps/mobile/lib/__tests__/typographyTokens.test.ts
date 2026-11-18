// Typography Token契約の検証 (design/typography.ts が正本)。
// Colorと違いTextStyleはtscで網羅を強制できないため、ソースをテキストとして読み、
// 画面側に文字サイズの直接指定が戻らないことをテストで守る。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { globSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { SEMANTIC_TYPOGRAPHY_KEYS, typography } from "../../design/typography";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const screenFiles = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot }).sort();

// 文字ではなく図形・記号・数値を出すスタイル。文字スケールに載せない。
// (⛩ ♡ ↑ ✓ › などのグリフ、円バッジ内の1文字、カウント値、ブランドロゴの字詰め)
const GLYPH_STYLE_KEYS = new Set([
  "brandName",
  "brandRuby",
  "cardPlaceholderText",
  "check",
  "chevron",
  "emptyIcon",
  "heartText",
  "heroPlaceholderText",
  "iconText",
  "imagePlaceholderText",
  "introBadge",
  "logoMark",
  "pickBtnIcon",
  "placeholderIcon",
  "popularRank",
  "rankBadgeText",
  "selectChevron",
  "sendButtonText",
  "sendText",
  "statValue",
  "summaryValue",
]);

describe("Typography Token", () => {
  it("全キーに実値を持つ", () => {
    expect(Object.keys(typography).sort()).toEqual([...SEMANTIC_TYPOGRAPHY_KEYS].sort());
  });

  it("本文は17pt regular、最小は12ptとする", () => {
    expect(typography.body).toMatchObject({ fontSize: 17, fontWeight: "400" });
    expect(Math.min(...Object.values(typography).map((t) => t.fontSize))).toBe(12);
  });

  it("800 / 900 のウェイトを持たない", () => {
    // 旧実装は246スタイル中190が700以上で、小さい文字を極太で補っていた。
    for (const [key, style] of Object.entries(typography)) {
      expect(["400", "500", "600", "700"], key).toContain(style.fontWeight);
    }
  });
});

describe("画面側の文字指定", () => {
  it.each(screenFiles)("%s はグリフ以外で fontSize を直接指定しない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");
    const offenders: string[] = [];

    for (const match of source.matchAll(/\n {2}([A-Za-z0-9_]+): \{([^{}]*)\},/g)) {
      const [, key, body] = match;
      if (!body.includes("fontSize")) continue;
      if (GLYPH_STYLE_KEYS.has(key)) continue;
      offenders.push(key);
    }

    expect(offenders).toEqual([]);
  });

  it.each(screenFiles)("%s はグリフ以外で fontWeight 800 / 900 を使わない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");
    const offenders: string[] = [];

    for (const match of source.matchAll(/\n {2}([A-Za-z0-9_]+): \{([^{}]*)\},/g)) {
      const [, key, body] = match;
      if (!/fontWeight: "[89]00"/.test(body)) continue;
      if (GLYPH_STYLE_KEYS.has(key)) continue;
      offenders.push(key);
    }

    expect(offenders).toEqual([]);
  });
});
