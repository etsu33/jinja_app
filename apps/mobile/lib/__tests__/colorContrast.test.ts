// 明基調パレットのコントラストを実測で検証する。
//
// 配色は docs/design/color-direction-v1.md の決定に基づく。色は後から
// 「少しだけ」調整されやすく、そのとき読めなくなったことに気づけない。
// WCAG 2.1 の相対輝度をここで計算し、文字色が全ての面で AA を満たすことを固定する。
import { readFileSync, globSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

import { dawn, homeIndigo, iosIndigoColors, iosIndigoSemanticTheme, selectAppTheme, kamimusubiLight as light } from "../../design/theme";

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

  it("朱を本文の色に使わない", () => {
    // 朱は「塗り」と「小さな印」のための色で、読ませる文字の色ではない
    // (ios-ui-spec-v2.md 05節)。最暗面でのコントラストは 4.51 と境界上で、
    // 数値では守れないため、使われ方そのものを検査する。
    // 強調は深藍(accent)が受ける。
    const screens = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot });
    const offenders = screens.filter((file) =>
      /color: theme\.vermilion/.test(readFileSync(resolve(mobileRoot, file), "utf8")),
    );

    expect(offenders).toEqual([]);
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

  it("選択中の面が、非選択(白)と見分けられる", () => {
    // ios-ui-spec-v2.md 15節: 選択は「深藍の線 + 薄い深藍系の面」。
    // 全面塗りをやめた分、面の差と線で選択を示す。
    expect(contrast(light.selectedSurface, light.surface)).toBeGreaterThanOrEqual(1.15);
    expect(contrast(light.accent, light.selectedSurface)).toBeGreaterThanOrEqual(4.5);
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
    expect(theme.appColors.background).toBe("#F5EEDC");
    // Splash の下端と地が一致していること。起動から本編へ色が繋がる。
    expect(theme.appColors.background).toBe(theme.dawn.colors[theme.dawn.colors.length - 1]);
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

  it.each(screens)("%s で朱の塗りを2つ以上置かない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");
    const code = source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");

    // 数えるのは面を塗っているものだけ。15節は小さな朱の印(チェックなど)を許す。
    // 押下状態 (*Pressed) は同じ要素の別状態なので1つとして数える。
    const filled = new Set(
      [...code.matchAll(/\n {2}([A-Za-z0-9_]+): \{[^{}]*backgroundColor: theme\.vermilion/g)].map(([, key]) =>
        key.replace(/Pressed$/, ""),
      ),
    );

    expect([...filled].length).toBeLessThanOrEqual(1);
  });

  it("朱を使う画面がアプリ全体で限られている", () => {
    const users = screens.filter((file) =>
      readFileSync(resolve(mobileRoot, file), "utf8").includes("theme.vermilion"),
    );

    expect(users).toEqual(["app/(tabs)/index.tsx", "app/consultation/index.tsx"]);
  });
});

describe("和の朝焼け（区切りの画面のグラデーション）", () => {
  // 線形補間でグラデ上の任意位置の色を出す。
  function colorAt(position: number): string {
    const { colors, locations } = dawn;
    for (let i = 0; i < locations.length - 1; i += 1) {
      const [a, b] = [locations[i], locations[i + 1]];
      if (position < a || position > b) continue;

      const t = b > a ? (position - a) / (b - a) : 0;
      const from = colors[i].replace("#", "");
      const to = colors[i + 1].replace("#", "");
      const channel = (offset: number) => {
        const x = parseInt(from.slice(offset, offset + 2), 16);
        const y = parseInt(to.slice(offset, offset + 2), 16);
        return Math.round(x + (y - x) * t);
      };
      return `#${[0, 2, 4].map((o) => channel(o).toString(16).padStart(2, "0")).join("")}`;
    }
    return colors[colors.length - 1];
  }

  it("上から下へ、色が6段で定義されている", () => {
    expect(dawn.colors).toHaveLength(dawn.locations.length);
    expect(dawn.locations[0]).toBe(0);
    expect(dawn.locations[dawn.locations.length - 1]).toBe(1);

    // 位置は単調増加。空の向きを反転させない。
    for (let i = 1; i < dawn.locations.length; i += 1) {
      expect(dawn.locations[i]).toBeGreaterThan(dawn.locations[i - 1]);
    }
  });

  it("白文字を置ける上限までは AA を満たす", () => {
    for (let p = 0; p <= dawn.safeTextLimit; p += 0.04) {
      expect(contrast("#FFFFFF", colorAt(p)), `上から ${Math.round(p * 100)}%`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("上限より下は白文字が読めないことを明示する", () => {
    // 50% の薄縹で 4.46。ここに白文字を置く変更をテストで止める。
    expect(contrast("#FFFFFF", colorAt(0.5))).toBeLessThan(4.5);
  });

  it("焼けの帯には墨文字なら置ける", () => {
    for (const p of [0.86, 0.95]) {
      expect(contrast(light.text, colorAt(p)), `上から ${Math.round(p * 100)}%`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("Splash のロゴが、白文字を置ける範囲にある", () => {
    const source = readFileSync(resolve(mobileRoot, "components/common/DawnSplash.tsx"), "utf8");
    const markTop = Number(source.match(/const MARK_TOP = "(\d+)%"/)?.[1]) / 100;

    expect(markTop).toBeLessThanOrEqual(dawn.safeTextLimit);
    expect(contrast("#FFFFFF", colorAt(markTop))).toBeGreaterThanOrEqual(4.5);
  });

  it("グラデーションは区切り画面と承認済みのiOSホームに限る", () => {
    // 2026-11-24承認: iOSホームのみIndigo & Goldを適用。他画面は従来どおり。
    const users = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot })
      .filter((file) => readFileSync(resolve(mobileRoot, file), "utf8").includes("LinearGradient"))
      .sort();

    expect(users).toEqual(["app/(tabs)/index.tsx", "components/common/DawnSplash.tsx"]);
  });
});

describe("iOSホームのIndigo & Goldの可読性", () => {
  it("本文・補助文字が背景全域と入力面でAAを満たす", () => {
    for (const surface of [homeIndigo.background, homeIndigo.backgroundSubtle, homeIndigo.surface]) {
      for (const text of [homeIndigo.text, homeIndigo.secondaryText]) {
        expect(contrast(text, surface)).toBeGreaterThanOrEqual(4.5);
      }
      expect(contrast(homeIndigo.border, surface)).toBeGreaterThanOrEqual(3);
    }
  });

  it("主要CTAと検索CTA・選択中タブを識別できる", () => {
    expect(contrast(homeIndigo.actionText, homeIndigo.action)).toBeGreaterThanOrEqual(4.5);
    for (const background of [homeIndigo.background, homeIndigo.backgroundSubtle]) {
      expect(contrast(homeIndigo.action, background)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("iOS全画面テーマの可読性とプラットフォーム分離", () => {
  const surfaces = [iosIndigoColors.background, iosIndigoColors.surfaceSoft, iosIndigoColors.surface, iosIndigoColors.surfaceRaised, iosIndigoColors.selectedSurface];

  it("本文・補足・状態文字が全ての面でAAを満たす", () => {
    const texts = [iosIndigoColors.text, iosIndigoColors.mutedSoft, iosIndigoColors.mutedDark, iosIndigoColors.accent, iosIndigoColors.warning, iosIndigoColors.error];
    for (const text of texts) for (const surface of surfaces) {
      expect(contrast(text, surface), `${text} on ${surface}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("入力枠・選択線は全ての面に対して3以上ある", () => {
    for (const border of [iosIndigoColors.borderSoft, iosIndigoColors.border, iosIndigoColors.borderStrong, iosIndigoColors.borderAccent]) {
      for (const surface of surfaces) expect(contrast(border, surface), `${border} on ${surface}`).toBeGreaterThanOrEqual(3);
    }
  });

  it("塗りボタン上の文字と成功・エラー表示が読める", () => {
    for (const fill of [iosIndigoColors.vermilion, iosIndigoColors.vermilionDeep, iosIndigoColors.accent, iosIndigoColors.premiumAccent]) {
      expect(contrast(iosIndigoSemanticTheme["action.primaryText"], fill)).toBeGreaterThanOrEqual(4.5);
    }
    expect(contrast(iosIndigoColors.cedar, iosIndigoColors.cedarSurface)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(iosIndigoColors.error, iosIndigoColors.errorSurface)).toBeGreaterThanOrEqual(4.5);
  });

  it("Web/Android/その他は既存テーマの実体を返す", async () => {
    const original = await import("../../design/theme");
    for (const platform of ["web", "android", "windows"]) {
      const selected = selectAppTheme(platform);
      expect(selected.colors).toBe(original.appColors);
      expect(selected.semantic).toBe(original.appSemanticTheme);
      expect(selected.splash).toBe(original.dawn);
      expect(selected.statusBarStyle).toBe("dark");
    }
  });

  it("iOSだけ承認済みホームと同じ基調色を返す", () => {
    const selected = selectAppTheme("ios");
    expect(selected.colors).toBe(iosIndigoColors);
    expect(selected.semantic).toBe(iosIndigoSemanticTheme);
    expect(selected.colors.background).toBe(homeIndigo.background);
    expect(selected.semantic["action.primary"]).toBe(homeIndigo.action);
    expect(selected.statusBarStyle).toBe("light");
    expect(selected.primaryActionText).toBe(homeIndigo.actionText);
    expect(selected.splash.colors[0]).toBe(dawn.colors[0]);
  });
});

describe("実行時adapterの選択", () => {
  it.each(["ios", "android", "web"])("%sでテーマと入力外観を選べる", async (platform) => {
    vi.resetModules();
    vi.doMock("react-native", () => ({ Platform: { OS: platform } }));
    try {
      const runtime = await import("../../design/platformTheme");
      const expected = selectAppTheme(platform);
      expect(runtime.appColors).toEqual(expected.colors);
      expect(runtime.appSemanticTheme).toEqual(expected.semantic);
      expect(runtime.statusBarStyle).toBe(expected.statusBarStyle);
      expect(runtime.inputAppearance).toEqual(platform === "ios"
        ? { keyboardAppearance: "dark", selectionColor: homeIndigo.action }
        : {});
    } finally {
      vi.doUnmock("react-native");
      vi.resetModules();
    }
  });

  it("全画面と共通部品が実行時adapter経由で色を読む", () => {
    const sources = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot });
    for (const file of sources) {
      const source = readFileSync(resolve(mobileRoot, file), "utf8");
      expect(source, file).not.toMatch(/from ["'][^"']*design\/theme["']/);
    }
  });
});
