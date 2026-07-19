import { describe, expect, it } from "vitest";

import { SEMANTIC_COLOR_KEYS } from "../semanticColorTokens";
import { kamimusubiDarkSemanticTheme } from "../../theme";
import { SEMANTIC_SPACING_KEYS, semanticSpacing } from "../spacing";
import { SEMANTIC_RADIUS_KEYS, semanticRadius } from "../radius";
import { SEMANTIC_SHADOW_KEYS, semanticShadow } from "../shadow";

describe("kamimusubiDarkSemanticTheme (Semantic Color契約)", () => {
  it("SEMANTIC_COLOR_KEYSの全キーを持つ", () => {
    for (const key of SEMANTIC_COLOR_KEYS) {
      expect(kamimusubiDarkSemanticTheme).toHaveProperty(key);
      expect(typeof kamimusubiDarkSemanticTheme[key]).toBe("string");
      expect(kamimusubiDarkSemanticTheme[key].length).toBeGreaterThan(0);
    }
  });

  it("SEMANTIC_COLOR_KEYS以外の余分なキーを持たない", () => {
    const actualKeys = Object.keys(kamimusubiDarkSemanticTheme).sort();
    const expectedKeys = [...SEMANTIC_COLOR_KEYS].sort();
    expect(actualKeys).toEqual(expectedKeys);
  });
});

describe("semanticSpacing (Semantic Spacing契約)", () => {
  it("SEMANTIC_SPACING_KEYSの全キーを持ち、正の数値である", () => {
    for (const key of SEMANTIC_SPACING_KEYS) {
      expect(semanticSpacing).toHaveProperty(key);
      expect(typeof semanticSpacing[key]).toBe("number");
      expect(semanticSpacing[key]).toBeGreaterThan(0);
    }
  });
});

describe("semanticRadius (Semantic Radius契約)", () => {
  it("SEMANTIC_RADIUS_KEYSの全キーを持ち、正の数値である", () => {
    for (const key of SEMANTIC_RADIUS_KEYS) {
      expect(semanticRadius).toHaveProperty(key);
      expect(typeof semanticRadius[key]).toBe("number");
      expect(semanticRadius[key]).toBeGreaterThan(0);
    }
  });
});

describe("semanticShadow (Semantic Shadow/Elevation契約)", () => {
  it("SEMANTIC_SHADOW_KEYSの全キーを持ち、elevationを持つ", () => {
    for (const key of SEMANTIC_SHADOW_KEYS) {
      expect(semanticShadow).toHaveProperty(key);
      expect(typeof semanticShadow[key].elevation).toBe("number");
    }
  });

  it("noneはelevation 0である", () => {
    expect(semanticShadow.none.elevation).toBe(0);
  });
});
