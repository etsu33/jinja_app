import { readFileSync } from "node:fs";
import path from "node:path";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  WORLDVIEW_BACKDROP_SPECS,
  WORLDVIEW_BACKDROP_VARIANTS,
  WorldviewBackdrop,
  worldviewAtmosphere,
} from "@/components/worldview/WorldviewBackdrop";

// 共通の世界観Backdropの契約を検証する。
// - 装飾レイヤーとしての a11y 契約 (aria-hidden / pointer-events-none)
// - 色は --kt-world-* のみを参照し、Home専用 --home-* と実値(hex)に依存しない
// - home variant が旧 HomeBackdrop と同一の構図を出力する（Homeの見た目の保全）
// - standard / quiet の構図上の差（Orb / 波線の有無）

// コメント中の説明文（旧名への言及など）は契約の対象外とし、コードだけを検査する。
const componentSource = readFileSync(path.resolve(__dirname, "../WorldviewBackdrop.tsx"), "utf-8")
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "");

function renderVariant(variant: (typeof WORLDVIEW_BACKDROP_VARIANTS)[number]) {
  const { container } = render(<WorldviewBackdrop variant={variant} />);
  const root = container.querySelector(`[data-worldview-backdrop="${variant}"]`);
  if (!root) throw new Error(`backdrop root for ${variant} not found`);
  return root;
}

describe("WorldviewBackdrop: 装飾レイヤーの契約", () => {
  it.each(WORLDVIEW_BACKDROP_VARIANTS)("%s: ルートは aria-hidden かつ pointer-events-none", (variant) => {
    const root = renderVariant(variant);
    expect(root.getAttribute("aria-hidden")).toBe("true");
    expect(root.className).toContain("pointer-events-none");
    expect(root.className).toContain("absolute");
    expect(root.className).toContain("inset-0");
  });

  it.each(WORLDVIEW_BACKDROP_VARIANTS)("%s: フォーカス可能な要素・読み上げ要素を持たない", (variant) => {
    const root = renderVariant(variant);
    expect(root.querySelectorAll("a, button, input, textarea, select, [tabindex]")).toHaveLength(0);
    expect(root.querySelectorAll("title, desc, img")).toHaveLength(0);
    for (const svg of root.querySelectorAll("svg")) {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
      expect(svg.getAttribute("focusable")).toBe("false");
    }
  });
});

describe("WorldviewBackdrop: Tokenの参照契約", () => {
  it("Home専用の --home-* に依存しない", () => {
    expect(componentSource).not.toMatch(/--home-/);
  });

  it("色の実値(hex / rgb / hsl)を持たない", () => {
    expect(componentSource).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(componentSource).not.toMatch(/\b(rgb|rgba|hsl|hsla|oklch)\(/);
  });

  it.each(WORLDVIEW_BACKDROP_VARIANTS)("%s: 大気は --kt-world-ground を最背面に持つ", (variant) => {
    const layers = worldviewAtmosphere(variant);
    expect(layers.endsWith("var(--kt-world-ground)")).toBe(true);
    const vars = layers.match(/var\(--[a-z0-9-]+\)/g) ?? [];
    for (const v of vars) {
      expect(v).toMatch(/^var\(--kt-world-/);
    }
  });

  it.each(WORLDVIEW_BACKDROP_VARIANTS)("%s: 波線の色は --kt-world-path / --kt-world-path-lit のみ", (variant) => {
    const root = renderVariant(variant);
    for (const stop of root.querySelectorAll("stop")) {
      expect(["var(--kt-world-path)", "var(--kt-world-path-lit)"]).toContain(stop.getAttribute("stop-color"));
    }
  });
});

describe("WorldviewBackdrop: variantの構図", () => {
  it("home: 波線3本 + Main Orb", () => {
    const root = renderVariant("home");
    expect(root.querySelectorAll("path")).toHaveLength(3);
    expect(root.querySelectorAll('[data-worldview-layer="orb"]')).toHaveLength(1);
  });

  it("standard: 波線2本、Orbなし、champagneの発光なし", () => {
    const root = renderVariant("standard");
    expect(root.querySelectorAll("path")).toHaveLength(2);
    expect(root.querySelectorAll('[data-worldview-layer="orb"]')).toHaveLength(0);
    for (const stop of root.querySelectorAll("stop")) {
      expect(stop.getAttribute("stop-color")).toBe("var(--kt-world-path)");
    }
  });

  it("quiet: 地と上方の光のみで、波線もOrbも持たない", () => {
    const root = renderVariant("quiet");
    expect(root.querySelectorAll("svg")).toHaveLength(0);
    expect(root.querySelectorAll('[data-worldview-layer="orb"]')).toHaveLength(0);
    expect(WORLDVIEW_BACKDROP_SPECS.quiet.atmosphere).toEqual(["lit", "ground"]);
  });

  it("gradient id は variant ごとに一意で、path の stroke が同じ id を参照する", () => {
    const ids = new Set<string>();
    for (const variant of WORLDVIEW_BACKDROP_VARIANTS) {
      const root = renderVariant(variant);
      const gradients = root.querySelectorAll("defs > *");
      expect(gradients.length).toBe(root.querySelectorAll("path").length);
      for (const gradient of gradients) {
        expect(ids.has(gradient.id)).toBe(false);
        ids.add(gradient.id);
      }
      for (const p of root.querySelectorAll("path")) {
        const ref = p.getAttribute("stroke")?.match(/^url\(#(.+)\)$/)?.[1];
        expect(ref && root.querySelector(`defs > [id="${ref}"]`)).toBeTruthy();
      }
    }
  });
});

// 旧 features/home/components/HomeBackdrop.tsx の出力を固定値として保持する。
// home variant を変更するとHomeの見た目が変わるため、意図的な変更時のみ更新すること。
describe("WorldviewBackdrop: home variant は旧 HomeBackdrop と同一の構図", () => {
  it("大気の4層", () => {
    expect(worldviewAtmosphere("home")).toBe(
      [
        "radial-gradient(122% 46% at 50% -8%, var(--kt-world-ground-lit) 0%, transparent 66%)",
        "radial-gradient(56% 22% at 50% 0%, color-mix(in oklab, var(--kt-world-path) 7%, transparent) 0%, transparent 74%)",
        "radial-gradient(150% 52% at 50% 106%, color-mix(in oklab, var(--kt-world-surface-elevated) 58%, transparent) 0%, transparent 72%)",
        "var(--kt-world-ground)",
      ].join(", "),
    );
  });

  it("波線帯の位置・座標系", () => {
    const root = renderVariant("home");
    const svg = root.querySelector("svg");
    expect(svg?.getAttribute("viewBox")).toBe("0 0 390 660");
    expect(svg?.getAttribute("preserveAspectRatio")).toBe("none");
    expect(svg?.getAttribute("style")).toContain("top: 280px");
    expect(svg?.getAttribute("style")).toContain("height: 660px");
  });

  it("波線3本の形・太さ・描画順", () => {
    const root = renderVariant("home");
    const paths = [...root.querySelectorAll("path")].map((p) => ({
      d: p.getAttribute("d"),
      width: p.getAttribute("stroke-width"),
      linecap: p.getAttribute("stroke-linecap"),
      effect: p.getAttribute("vector-effect"),
    }));
    expect(paths).toEqual([
      {
        d: "M -24 260 C 56 266, 116 306, 180 330 C 252 357, 330 398, 414 430",
        width: "0.8",
        linecap: "round",
        effect: "non-scaling-stroke",
      },
      {
        d: "M -24 420 C 60 428, 126 468, 190 490 C 262 515, 336 552, 414 580",
        width: "1",
        linecap: "round",
        effect: "non-scaling-stroke",
      },
      {
        d: "M -24 118 C 48 120, 104 166, 164 190 C 232 217, 292 246, 414 268",
        width: "1.6",
        linecap: "round",
        effect: "non-scaling-stroke",
      },
    ]);
  });

  it("主線の発光 (brass → champagne → brass)", () => {
    const root = renderVariant("home");
    const stops = [...root.querySelectorAll('[id="worldview-home-path-main"] stop')].map(
      (s) => [s.getAttribute("offset"), s.getAttribute("stop-color"), s.getAttribute("stop-opacity")],
    );
    const brass = "var(--kt-world-path)";
    const lit = "var(--kt-world-path-lit)";
    expect(stops).toEqual([
      ["0%", brass, "0.09"],
      ["24%", brass, "0.3"],
      ["38%", lit, "0.7"],
      ["44%", lit, "0.86"],
      ["54%", brass, "0.42"],
      ["72%", brass, "0.18"],
      ["100%", brass, "0.07"],
    ]);
  });

  it("副線の明るさ", () => {
    const root = renderVariant("home");
    const read = (id: string) =>
      [...root.querySelectorAll(`[id="${id}"] stop`)].map((s) => [
        s.getAttribute("offset"),
        s.getAttribute("stop-opacity"),
      ]);
    expect(read("worldview-home-path-sub-1")).toEqual([
      ["0%", "0.07"],
      ["46%", "0.36"],
      ["100%", "0.1"],
    ]);
    expect(read("worldview-home-path-sub-2")).toEqual([
      ["0%", "0.04"],
      ["52%", "0.17"],
      ["100%", "0.05"],
    ]);
  });

  it("Main Orb は主線の通過点 (164, 190) に 184px で乗る", () => {
    expect(WORLDVIEW_BACKDROP_SPECS.home.band?.orb).toEqual({ x: 164, y: 190, size: 184 });
    const orb = renderVariant("home").querySelector<HTMLElement>('[data-worldview-layer="orb"]');
    expect(orb?.style.left).toBe(`${(164 / 390) * 100}%`);
    expect(orb?.style.top).toBe("470px");
    expect(orb?.style.width).toBe("184px");
    expect(orb?.style.height).toBe("184px");
    expect(orb?.style.transform).toBe("translate(-50%, -50%)");
  });
});
