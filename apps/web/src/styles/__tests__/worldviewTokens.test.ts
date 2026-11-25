import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// KAMI MUSUBI Worldview Token (--kt-world-*) の契約を検証する。
// - 必須キーが tokens.css に宣言されている
// - Home専用 --home-* は --kt-world-* の別名であり、実値を二重に持たない
// - 実値(hex)は tokens.css のWorldviewブロックにだけ存在する
// - Home以外のComponentが --home-* に依存しない

const srcRoot = path.resolve(__dirname, "../..");
const tokensCss = readFileSync(path.resolve(srcRoot, "styles/tokens.css"), "utf-8");
const globalsCss = readFileSync(path.resolve(srcRoot, "app/globals.css"), "utf-8");

const REQUIRED_WORLD_TOKENS = [
  "ground",
  "ground-lit",
  "surface",
  "surface-elevated",
  "border",
  "border-strong",
  "text-primary",
  "text-secondary",
  "text-muted",
  "path",
  "path-lit",
  "font-display",
] as const;

// 旧 --home-* の実値。Homeの見た目を変えないため、Worldview Tokenはこれと同一値を持つ。
const PRESERVED_HOME_VALUES: Record<string, string> = {
  ground: "#0b111c",
  "ground-lit": "#16203a",
  surface: "#192231",
  "surface-elevated": "#222d3e",
  border: "#455063",
  "border-strong": "#718096",
  "text-primary": "#fffdf8",
  "text-secondary": "#e7eaf0",
  "text-muted": "#c5cbd6",
  path: "var(--kt-color-action-primary)",
  "path-lit": "var(--kt-color-premium-accent)",
};

function worldBlock(css: string): string {
  const start = css.indexOf("KAMI MUSUBI Worldview Token");
  expect(start, "Worldview Tokenブロックが見つからない").toBeGreaterThan(-1);
  const open = css.indexOf(":root {", start);
  const close = css.indexOf("\n}", open);
  return css.slice(open, close);
}

function homeBlock(css: string): string {
  const open = css.indexOf('body:has([data-app-frame="home"]) {');
  expect(open, "Home Art Direction Layerが見つからない").toBeGreaterThan(-1);
  const close = css.indexOf("\n}", open);
  return css.slice(open, close);
}

function declarations(block: string): Map<string, string> {
  const map = new Map<string, string>();
  const pattern = /(--[a-z0-9-]+)\s*:\s*([^;]+);/g;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(block)) !== null) {
    map.set(m[1], m[2].replace(/\s+/g, " ").trim());
  }
  return map;
}

function listSourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return listSourceFiles(full);
    return /\.(ts|tsx|css)$/.test(name) ? [full] : [];
  });
}

describe("Worldview Token: tokens.css の宣言", () => {
  const world = declarations(worldBlock(tokensCss));

  it.each(REQUIRED_WORLD_TOKENS)("--kt-world-%s が宣言されている", (key) => {
    expect(world.has(`--kt-world-${key}`)).toBe(true);
  });

  it.each(Object.entries(PRESERVED_HOME_VALUES))("--kt-world-%s は旧Home値 %s と同一", (key, value) => {
    expect(world.get(`--kt-world-${key}`)).toBe(value);
  });

  it("明朝Displayは Webfont を読み込まず、OS標準明朝 → serif へフォールバックする", () => {
    const font = world.get("--kt-world-font-display") ?? "";
    expect(font.startsWith('"Hiragino Mincho ProN"')).toBe(true);
    expect(font.endsWith("serif")).toBe(true);
    expect(tokensCss).not.toMatch(/@font-face|@import\s+url/);
  });

  it("既存の Dark Forest Semantic Token を再定義しない", () => {
    for (const name of world.keys()) {
      expect(name.startsWith("--kt-world-")).toBe(true);
    }
  });
});

describe("Worldview Token: Home Art Direction Layer との関係", () => {
  const home = declarations(homeBlock(globalsCss));

  it("--home-* は実値を持たず、--kt-world-* (または --home-* 内) の別名である", () => {
    expect(home.size).toBeGreaterThan(0);
    for (const [name, value] of home) {
      expect(value, `${name} が実値を持っている`).toMatch(/^var\(--(kt-world|home)-[a-z0-9-]+\)$/);
    }
  });

  it("既存の --home-* 名は維持されている（Home Componentの参照を壊さない）", () => {
    const expected = [
      ...Object.keys(PRESERVED_HOME_VALUES).map((k) => `--home-${k}`),
      "--home-ground-moss",
      "--home-font-display",
    ];
    for (const name of expected) {
      expect(home.has(name), `${name} が失われている`).toBe(true);
    }
  });
});

describe("Worldview Token: 参照範囲", () => {
  const files = listSourceFiles(srcRoot).filter((f) => !f.includes(`${path.sep}__tests__${path.sep}`));

  it("--home-* を var() で参照するのは features/home と globals.css だけ", () => {
    const offenders = files.filter((file) => {
      const rel = path.relative(srcRoot, file);
      if (rel.startsWith(`features${path.sep}home${path.sep}`) || rel === path.join("app", "globals.css")) {
        return false;
      }
      return /var\(--home-/.test(readFileSync(file, "utf-8"));
    });
    expect(offenders).toEqual([]);
  });

  it("Worldviewの実値(hex)は tokens.css 以外のソースへ複製されていない", () => {
    const worldHexes = Object.values(PRESERVED_HOME_VALUES).filter((v) => v.startsWith("#"));
    const offenders = files.flatMap((file) => {
      if (file.endsWith(path.join("styles", "tokens.css"))) return [];
      const text = readFileSync(file, "utf-8").toLowerCase();
      return worldHexes.filter((hex) => text.includes(hex)).map((hex) => `${path.relative(srcRoot, file)}: ${hex}`);
    });
    expect(offenders).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// App-wide Web Worldview Rollout
// ---------------------------------------------------------------------------

function darkBlock(css: string, anchor: string): string {
  const start = css.indexOf(anchor);
  expect(start, `${anchor} が見つからない`).toBeGreaterThan(-1);
  const open = css.indexOf(".dark {", start);
  const close = css.indexOf("\n}", open);
  return css.slice(open, close);
}

describe("App-wide Worldview: 中立の Semantic Token は Worldview を経由して解決する", () => {
  const kt = declarations(darkBlock(tokensCss, "Dark UI Token Foundation"));
  const shadcn = declarations(darkBlock(globalsCss, "shadcn Semantic Token"));

  const NEUTRAL_KT: Record<string, string> = {
    "--kt-color-background-base": "var(--kt-world-ground)",
    "--kt-color-surface-default": "var(--kt-world-surface)",
    "--kt-color-surface-elevated": "var(--kt-world-surface-elevated)",
    "--kt-color-text-primary": "var(--kt-world-text-primary)",
    "--kt-color-text-secondary": "var(--kt-world-text-secondary)",
    "--kt-color-text-muted": "var(--kt-world-text-muted)",
    "--kt-color-border-default": "var(--kt-world-border)",
    "--kt-color-border-strong": "var(--kt-world-border-strong)",
  };

  it.each(Object.entries(NEUTRAL_KT))("%s → %s", (name, value) => {
    expect(kt.get(name)).toBe(value);
  });

  it("導出される中立Token (subtle / emphasis / notice) は Worldview / 中立Tokenだけから作られ、実値を持たない", () => {
    for (const name of [
      "--kt-color-background-subtle",
      "--kt-color-surface-emphasis",
      "--kt-color-surface-emphasis-hover",
      "--kt-color-notice-bg",
      "--kt-color-notice-border",
      "--kt-color-notice-text",
    ]) {
      const value = kt.get(name) ?? "";
      expect(value, name).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
      expect(value, name).toMatch(/var\(--kt-(world|color)-/);
    }
  });

  const NEUTRAL_SHADCN: Record<string, string> = {
    "--background": "var(--kt-world-ground)",
    "--foreground": "var(--kt-world-text-primary)",
    "--card": "var(--kt-world-surface)",
    "--popover": "var(--kt-world-surface-elevated)",
    "--muted-foreground": "var(--kt-world-text-muted)",
    "--border": "var(--kt-world-border)",
  };

  it.each(Object.entries(NEUTRAL_SHADCN))("shadcn %s → %s", (name, value) => {
    expect(shadcn.get(name)).toBe(value);
  });

  it("html にも地を与え、overscroll で旧色を露出させない（:has() に依存しない）", () => {
    expect(globalsCss).toMatch(/html\.dark\s*\{\s*background-color:\s*var\(--kt-color-background-base\);/);
  });
});

describe("App-wide Worldview: 状態・意味を持つ Token は中立の Worldview Token に置き換えない", () => {
  const kt = declarations(darkBlock(tokensCss, "Dark UI Token Foundation"));
  const SEMANTIC = [
    "--kt-color-border-focus",
    "--kt-color-action-primary",
    "--kt-color-action-primary-hover",
    "--kt-color-action-primary-text",
    "--kt-color-action-disabled",
    "--kt-color-status-success",
    "--kt-color-status-success-text",
    "--kt-color-status-success-surface",
    "--kt-color-status-success-border",
    "--kt-color-status-warning",
    "--kt-color-status-error",
    "--kt-color-status-info",
    "--kt-color-premium-accent",
    "--kt-color-premium-surface",
    "--kt-color-premium-border",
    "--kt-color-overlay-default",
    "--kt-color-selection-background",
    "--kt-color-selection-border",
    "--kt-color-message-own-background",
    "--kt-color-message-own-text",
    "--kt-color-saved-background",
    "--kt-color-saved-text",
    "--kt-color-saved-border",
  ];

  it.each(SEMANTIC)("%s は --kt-world-* を参照しない", (name) => {
    const value = kt.get(name);
    expect(value, `${name} が .dark に宣言されていない`).toBeDefined();
    expect(value).not.toMatch(/--kt-world-/);
  });

  it("gold は focus / action / premium の責務にだけ残る（中立の線・面・文字に使わない）", () => {
    for (const name of [
      "--kt-color-border-default",
      "--kt-color-border-strong",
      "--kt-color-surface-default",
      "--kt-color-text-primary",
    ]) {
      expect(kt.get(name)).not.toMatch(/path|action-primary|premium/);
    }
  });
});
