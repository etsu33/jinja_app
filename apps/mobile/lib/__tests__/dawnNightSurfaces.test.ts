// 藍の地(dawnNight)の上に置く文字・面・線の濃さを検証する。
//
// 地はグラデーションなので、いちばん明るいところ(colors[2])でも基準を
// 満たす必要がある。目分量で opacity を足すと、ここが割れる。
//
// 実際に割っていた。opacity 0.6 の文字が 3.57(本文基準 4.5)、枠線
// rgba(...,0.34) が 2.15(UI部品の輪郭 3.0)。5画面にまたがっていた。
import { globSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { dawnNight } from "../../design/theme";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

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

/** 不透明度 alpha で前景を地に重ねた実効色。 */
function over(foreground: string, ground: string, alpha: number): string {
  const f = foreground.replace("#", "");
  const g = ground.replace("#", "");
  const mix = (i: number) =>
    Math.round(parseInt(f.slice(i, i + 2), 16) * alpha + parseInt(g.slice(i, i + 2), 16) * (1 - alpha));
  return `#${[0, 2, 4].map((i) => mix(i).toString(16).padStart(2, "0")).join("")}`;
}

/** "rgba(245, 238, 220, 0.52)" から不透明度を取り出す。 */
function alphaOf(rgba: string): number {
  const match = rgba.match(/rgba\([^)]*,\s*([\d.]+)\s*\)/);
  if (!match) throw new Error(`不透明度を読めない: ${rgba}`);
  return Number(match[1]);
}

// いちばん不利な地。ここで満たせば、どの位置でも満たす。
const LIGHTEST = dawnNight.colors[dawnNight.colors.length - 1];

describe("藍の地の上の濃さ", () => {
  it("不透明な文字はどの地でも本文基準を満たす", () => {
    for (const ground of dawnNight.colors) {
      expect(contrast(dawnNight.text, ground), ground).toBeGreaterThanOrEqual(4.5);
      expect(contrast(dawnNight.mark, ground), ground).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("薄い文字の2段が、いちばん明るい地でも本文基準を満たす", () => {
    for (const [name, alpha] of [
      ["textBody", dawnNight.textBody],
      ["textMuted", dawnNight.textMuted],
    ] as const) {
      const effective = over(dawnNight.text, LIGHTEST, alpha);
      expect(contrast(effective, LIGHTEST), name).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("プレースホルダも文字なので本文基準を満たす", () => {
    const alpha = alphaOf(dawnNight.placeholder);
    const effective = over(dawnNight.text, LIGHTEST, alpha);
    expect(contrast(effective, LIGHTEST)).toBeGreaterThanOrEqual(4.5);
  });

  it("操作できる部品の輪郭が UI 基準を満たす", () => {
    const alpha = alphaOf(dawnNight.border);
    const effective = over(dawnNight.text, LIGHTEST, alpha);
    expect(contrast(effective, LIGHTEST)).toBeGreaterThanOrEqual(3);
  });

  it("薄い文字は textMuted より下げない", () => {
    expect(dawnNight.textMuted).toBeLessThanOrEqual(dawnNight.textBody);
    // 0.73 が本文基準の下限(実測)。
    expect(dawnNight.textMuted).toBeGreaterThanOrEqual(0.73);
  });
});

describe("濃さの指定のしかた", () => {
  const DARK_SCREENS = [
    "app/(tabs)/index.tsx",
    "app/(tabs)/records/index.tsx",
    "app/(tabs)/mypage/index.tsx",
    "app/(tabs)/_layout.tsx",
    "app/consultation/index.tsx",
    "components/ConditionFieldsCard.tsx",
    "components/MobileOriginSelector.tsx",
  ];

  // 目分量の opacity を禁じる。読みやすさは dawnNight の2段(textBody /
  // textMuted)だけで表し、画面ごとに数字を足さない。
  it.each(DARK_SCREENS)("%s は opacity の数値を直接書かない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");

    expect(source.match(/opacity: 0?\.\d+/g) ?? []).toEqual([]);
  });

  it("どの画面にも生成りの rgba を手書きしない", () => {
    const handwritten = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot })
      .filter((file) => /rgba\(245, 238, 220/.test(readFileSync(resolve(mobileRoot, file), "utf8")))
      .sort();

    expect(handwritten).toEqual([]);
  });
});
