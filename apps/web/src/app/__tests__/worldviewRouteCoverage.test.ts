import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// App-wide Web Worldview の Route 被覆契約。
//
// - app/ 配下の全 page.tsx を分類する（未分類の Route が増えたら失敗する）
// - USER_FACING_WORLDVIEW の各 Route は、root から page までの経路上で
//   世界観フレームをちょうど1つ持つ（Home は home frame、他は WorldviewFrame）
// - WorldviewFrame の variant は standard / quiet のいずれか
// - 1画面に WorldviewBackdrop は1つまで（フレームを入れ子にしない）
//
// JSX の見た目の細部（Tailwind class）は検証しない。構造上の契約だけを見る。

const appRoot = path.resolve(__dirname, "..");

type Category = "USER_FACING_WORLDVIEW" | "INTERNAL_DEBUG" | "NON_VISUAL_REDIRECT";

// Route coverage matrix（PR本文の表と一致させる）
const ROUTE_MATRIX: Record<string, Category> = {
  "/": "USER_FACING_WORLDVIEW",
  "/auth/login": "USER_FACING_WORLDVIEW",
  "/auth/register": "USER_FACING_WORLDVIEW",
  "/billing": "USER_FACING_WORLDVIEW",
  "/billing/cancel": "USER_FACING_WORLDVIEW",
  "/billing/manage": "USER_FACING_WORLDVIEW",
  "/billing/success": "USER_FACING_WORLDVIEW",
  "/billing/upgrade": "USER_FACING_WORLDVIEW",
  "/compass": "USER_FACING_WORLDVIEW",
  "/concierge": "USER_FACING_WORLDVIEW",
  "/concierge/full": "USER_FACING_WORLDVIEW",
  "/consultation": "USER_FACING_WORLDVIEW",
  "/favorites": "USER_FACING_WORLDVIEW",
  "/g/[username]": "USER_FACING_WORLDVIEW",
  "/goshuin/new": "USER_FACING_WORLDVIEW",
  "/map": "USER_FACING_WORLDVIEW",
  "/mypage": "USER_FACING_WORLDVIEW",
  "/mypage/history": "USER_FACING_WORLDVIEW",
  "/mypage/history/[tid]": "USER_FACING_WORLDVIEW",
  "/mypage/settings": "USER_FACING_WORLDVIEW",
  "/plan": "USER_FACING_WORLDVIEW",
  "/populars": "USER_FACING_WORLDVIEW",
  "/privacy": "USER_FACING_WORLDVIEW",
  "/ranking": "USER_FACING_WORLDVIEW",
  "/routes": "USER_FACING_WORLDVIEW",
  "/shrines": "USER_FACING_WORLDVIEW",
  "/shrines/[id]": "USER_FACING_WORLDVIEW",
  "/shrines/[id]/goshuins": "USER_FACING_WORLDVIEW",
  "/shrines/new": "USER_FACING_WORLDVIEW",
  "/terms": "USER_FACING_WORLDVIEW",
  "/users/[username]": "USER_FACING_WORLDVIEW",
  "/debug/concierge": "INTERNAL_DEBUG",
  "/debug/concierge-fixture": "INTERNAL_DEBUG",
  "/debug/location": "INTERNAL_DEBUG",
  "/debug/score-v3-dashboard": "INTERNAL_DEBUG",
  // 描画前に redirect() するだけの Route（見た目を持たない）
  "/goshuins": "NON_VISUAL_REDIRECT",
  "/goshuins/public": "NON_VISUAL_REDIRECT",
  "/login": "NON_VISUAL_REDIRECT",
  "/signup": "NON_VISUAL_REDIRECT",
  "/shrines/hub/[id]": "NON_VISUAL_REDIRECT",
  "/shrines/resolve": "NON_VISUAL_REDIRECT",
};

function listPages(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) {
      if (name === "api" || name === "__tests__") return [];
      return listPages(full);
    }
    return name === "page.tsx" ? [full] : [];
  });
}

function routeOf(pageFile: string): string {
  const rel = path.relative(appRoot, path.dirname(pageFile)).split(path.sep).filter(Boolean);
  const segments = rel.filter((s) => !(s.startsWith("(") && s.endsWith(")")));
  return "/" + segments.join("/");
}

/** root layout から page までの経路上のファイル（layout.tsx…, page.tsx）。 */
function chainOf(pageFile: string): string[] {
  const rel = path.relative(appRoot, path.dirname(pageFile)).split(path.sep).filter(Boolean);
  const chain: string[] = [];
  let dir = appRoot;
  for (const seg of ["", ...rel]) {
    dir = seg ? path.join(dir, seg) : dir;
    const layout = path.join(dir, "layout.tsx");
    if (existsSync(layout)) chain.push(layout);
  }
  chain.push(pageFile);
  return chain;
}

const read = (f: string) => readFileSync(f, "utf-8");
const usesFrame = (src: string) => /<WorldviewFrame\b/.test(src);
const usesBackdropDirectly = (src: string) => /<WorldviewBackdrop\b/.test(src);
const FRAME_VARIANT = /<WorldviewFrame\b[^>]*variant="([a-z]+)"/g;

const pages = listPages(appRoot);

describe("Worldview Route coverage", () => {
  it("app/ 配下の全 page.tsx が Route coverage matrix で分類されている", () => {
    const unclassified = pages.map(routeOf).filter((r) => !(r in ROUTE_MATRIX));
    expect(unclassified, "新しい Route は ROUTE_MATRIX に分類を追加すること").toEqual([]);
  });

  it("matrix に実在しない Route が残っていない", () => {
    const actual = new Set(pages.map(routeOf));
    expect(Object.keys(ROUTE_MATRIX).filter((r) => !actual.has(r))).toEqual([]);
  });

  const userFacing = pages.filter((p) => ROUTE_MATRIX[routeOf(p)] === "USER_FACING_WORLDVIEW");

  it.each(userFacing.map((p) => [routeOf(p), p]))("%s: 世界観フレームをちょうど1つ持つ", (route, pageFile) => {
    const chain = chainOf(pageFile);
    const frames = chain.filter((f) => usesFrame(read(f)));
    if (route === "/") {
      // Home は features/home/HomePage.tsx の home frame（home variant）が担う
      expect(frames).toEqual([]);
      expect(read(pageFile)).toMatch(/features\/home\/HomePage/);
      return;
    }
    expect(frames.map((f) => path.relative(appRoot, f))).toHaveLength(1);
    // Backdrop を Frame 経由でなく直接描いて二重にしていない
    expect(chain.filter((f) => usesBackdropDirectly(read(f)))).toEqual([]);
  });

  it("WorldviewFrame の variant は standard / quiet のいずれか", () => {
    const files = [
      ...readdirSync(appRoot, { recursive: true })
        .map(String)
        .filter((f) => f.endsWith(".tsx") && !f.includes("__tests__"))
        .map((f) => path.join(appRoot, f)),
    ];
    const variants = files.flatMap((f) => [...read(f).matchAll(FRAME_VARIANT)].map((m) => m[1]));
    expect(variants.length).toBeGreaterThan(0);
    for (const v of variants) expect(["standard", "quiet"]).toContain(v);
  });

  it("Root の error / not-found boundary は自身で世界観フレームを持つ（Segment layout の外で描画されるため）", () => {
    for (const f of ["error.tsx", "not-found.tsx"]) {
      expect(usesFrame(read(path.join(appRoot, f))), f).toBe(true);
    }
  });

  it("Segment の error / loading boundary はフレームを重ねない（Segment layout が持つ）", () => {
    for (const f of ["map/error.tsx", "map/loading.tsx", "mypage/error.tsx", "mypage/loading.tsx"]) {
      expect(usesFrame(read(path.join(appRoot, f))), f).toBe(false);
      expect(usesBackdropDirectly(read(path.join(appRoot, f))), f).toBe(false);
    }
  });

  it("Home は home variant の Backdrop を使い、WorldviewFrame を重ねない", () => {
    const home = read(path.resolve(appRoot, "../features/home/HomePage.tsx"));
    expect(home).toMatch(/<WorldviewBackdrop variant="home" \/>/);
    expect(usesFrame(home)).toBe(false);
    expect(home).toMatch(/data-app-frame="home"/);
  });
});
