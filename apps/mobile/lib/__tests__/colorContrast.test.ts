// 明基調パレットのコントラストを実測で検証する。
//
// 配色は docs/design/color-direction-v1.md の決定に基づく。色は後から
// 「少しだけ」調整されやすく、そのとき読めなくなったことに気づけない。
// WCAG 2.1 の相対輝度をここで計算し、文字色が全ての面で AA を満たすことを固定する。
import { describe, expect, it } from "vitest";

import { kamimusubiLight as light } from "../../design/theme";

function channel(value: number): number {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => channel(parseInt(h.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// 文字が載りうる面。いちばん暗い surfaceSoft が最悪条件になる。
const SURFACES = [
  ["background", light.background],
  ["surfaceSoft", light.surfaceSoft],
  ["surface", light.surface],
  ["surfaceRaised", light.surfaceRaised],
] as const;

// 面の上に置く文字色。
const TEXT_COLORS = [
  ["text", light.text],
  ["mutedSoft", light.mutedSoft],
  ["muted", light.muted],
  ["mutedDark", light.mutedDark],
  ["navMuted", light.navMuted],
  ["accent", light.accent],
  ["accentSoft", light.accentSoft],
  ["premiumAccent", light.premiumAccent],
  ["cedar", light.cedar],
  ["warning", light.warning],
  ["error", light.error],
] as const;

describe("明基調パレットのコントラスト", () => {
  it.each(TEXT_COLORS)("%s は全ての面で AA (4.5) を満たす", (name, color) => {
    for (const [surfaceName, surface] of SURFACES) {
      expect(contrast(color, surface), `${name} on ${surfaceName}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("塗りボタンの白文字が AA を満たす", () => {
    expect(contrast(light.surfaceRaised, light.accent)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(light.surfaceRaised, light.premiumAccent)).toBeGreaterThanOrEqual(4.5);
  });

  it("状態を示す境界が UI部品の基準 (3.0) を満たす", () => {
    // WCAG 1.4.11。入力欄の枠など、形が状態を伝える線。
    expect(contrast(light.borderStrong, light.surface)).toBeGreaterThanOrEqual(3.0);
  });

  it("色付きの面の上でも文字が読める", () => {
    expect(contrast(light.cedar, light.cedarSurface)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(light.error, light.errorSurface)).toBeGreaterThanOrEqual(4.5);
  });

  it("金茶は文字に使えないことを明示する", () => {
    // 2.49。線専用。これを文字色へ昇格させる変更をここで止める。
    expect(contrast(light.borderAccent, light.background)).toBeLessThan(3.0);
  });

  it("面の明度が outside < surfaceSoft < background < surface < surfaceRaised の順である", () => {
    const ramp = [light.outside, light.surfaceSoft, light.background, light.surface, light.surfaceRaised].map(luminance);
    for (let i = 1; i < ramp.length; i += 1) {
      expect(ramp[i], `面 ${i}`).toBeGreaterThan(ramp[i - 1]);
    }
  });
});

describe("Theme の export", () => {
  it("画面が参照する appColors / appSemanticTheme が実体を持つ", async () => {
    // 参照名を変えたとき、型は通るのに実行時だけ undefined になる事故を止める。
    const theme = await import("../../design/theme");

    expect(theme.appColors).toBeDefined();
    expect(theme.appColors.background).toBe("#F5F1E8");
    expect(theme.appSemanticTheme).toBeDefined();
    expect(theme.appSemanticTheme["action.primary"]).toBe("#B53A2D");
  });
});
