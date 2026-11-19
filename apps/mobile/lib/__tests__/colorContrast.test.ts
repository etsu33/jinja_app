// 明基調パレットのコントラストを実測で検証する。
//
// 配色は docs/design/color-direction-v1.md の決定に基づく。色は後から
// 「少しだけ」調整されやすく、そのとき読めなくなったことに気づけない。
// WCAG 2.1 の相対輝度をここで計算し、文字色が全ての面で AA を満たすことを固定する。
import { readFileSync, globSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

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
    for (const fill of [light.accent, light.premiumAccent, light.vermilion, light.vermilionDeep]) {
      expect(contrast(light.surfaceRaised, fill)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("朱は塗り専用で、文字には使えない", () => {
    // 最も暗い面(surfaceSoft)の上で AA に届かない。
    // 文字色へ昇格させる変更をここで止める。強調は深藍(accent)で受ける。
    expect(contrast(light.vermilion, light.surfaceSoft)).toBeLessThan(4.5);
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

  it("カードが地から面として見える差を持つ", () => {
    // 1.15 を下回ると、線や影に頼らないと紙の上の紙に見えない。
    expect(contrast(light.surface, light.background)).toBeGreaterThanOrEqual(1.15);
  });

  it("面の明度が outside < surfaceSoft < background <= surface の順である", () => {
    const ramp = [light.outside, light.surfaceSoft, light.background, light.surface].map(luminance);
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
    expect(theme.appColors.background).toBe("#F1ECE1");
    expect(theme.appSemanticTheme).toBeDefined();
    expect(theme.appSemanticTheme["action.primary"]).toBe("#B53A2D");
  });
});

describe("朱の使い方", () => {
  // docs/design/color-direction-v1.md: 「朱色は1画面に1つ。印であって地ではない」
  //
  // 明基調へ切り替えた最初の実装では、旧 gold の参照をそのまま朱に置き換えた結果、
  // ホーム画面だけで朱の塗りが4つ(送信ボタン・選択チップ・主CTA・タブ)出て、
  // 安売りの広告のような見え方になった。静かな強調は深藍(accent)が受け持つ。
  const screens = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot }).sort();

  it.each(screens)("%s で朱を2箇所以上の要素に使わない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");
    const code = source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");

    // backgroundColor と shadowColor の対は1つの要素なので、style キーの数で数える。
    const keys = new Set(
      [...code.matchAll(/\n {2}([A-Za-z0-9_]+): \{[^{}]*theme\.vermilion/g)].map(([, key]) => key),
    );

    expect([...keys].length).toBeLessThanOrEqual(1);
  });

  it("朱を使う画面がアプリ全体で限られている", () => {
    const users = screens.filter((file) =>
      readFileSync(resolve(mobileRoot, file), "utf8").includes("theme.vermilion"),
    );

    expect(users).toEqual(["app/(tabs)/index.tsx"]);
  });
});
