// 選択中の印(Ionicons)が、その面の上で見えることを固定する。
//
// グリフの ✓ を Ionicons へ移したとき、ConditionFieldsCard で印の色を
// theme.accent にしてしまった。選択中のピルの面も theme.accent(紺)なので、
// 紺の上に紺で描かれ、コントラスト 1.00 で完全に見えなくなっていた。
// 文字(pillTextActive)は theme.background を持っていたが、Text の外へ
// 出した Ionicons はその色を継がない。
//
// 面と印の組を直接押さえる。色を動かしたら落ちる。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { dawnNight, kamimusubiLight as light } from "../../design/theme";

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

// 選択中の面と、その上に置く印。WCAG 1.4.11 のUI部品の基準 3.0 を満たすこと。
// 相談フローは夜明け前の暗地になった。薄い膜(10%)の上なので、面の実効色は
// グラデの地にほぼ等しい。最も明るい地で見えれば、どこでも見える。
const DARK_GROUND = dawnNight.colors[dawnNight.colors.length - 1];

const MARK_ON_SURFACE: [string, string, string][] = [
  ["条件のピル(相談フロー)", DARK_GROUND, dawnNight.mark],
  ["出発地点の選択(相談フロー)", DARK_GROUND, dawnNight.mark],
  ["相談のカード(相談フロー)", DARK_GROUND, dawnNight.mark],
];

describe("選択中の印が面の上で見える", () => {
  it.each(MARK_ON_SURFACE)("%s", (_name, surface, mark) => {
    expect(contrast(mark, surface)).toBeGreaterThanOrEqual(3);
  });

  it("印の色が面の色と同じでない", () => {
    for (const [name, surface, mark] of MARK_ON_SURFACE) {
      expect(mark, `${name}: 印と面が同色`).not.toBe(surface);
    }
  });

  it("コードが期待どおりの色を渡している", () => {
    // 以前は面が theme.accent(紺)で、印にも theme.accent を渡していたため
    // コントラスト 1.00 で見えなかった。暗地になった今は曙色で示す。
    for (const file of [
      "components/ConditionFieldsCard.tsx",
      "components/MobileOriginSelector.tsx",
      "app/consultation/index.tsx",
    ]) {
      const source = readFileSync(resolve(mobileRoot, file), "utf8");
      expect(source, `${file} の印`).toMatch(/name="checkmark"[^/]*color=\{dawnNight\.mark\}/);
      // 地と同系の色を印に使わない。
      expect(source, `${file} が地と同じ色の印を持つ`).not.toMatch(
        /name="checkmark"[^/]*color=\{theme\.accent\}/,
      );
    }
  });
});
