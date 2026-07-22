import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const layoutSource = readFileSync(resolve(mobileRoot, "app/_layout.tsx"), "utf8");

describe("Expo Router structure", () => {
  it("正式な4タブだけを表示する", () => {
    const visibleScreens = [...layoutSource.matchAll(/<Tabs\.Screen\s+name="([^"]+)"[\s\S]*?options=\{\{([\s\S]*?)\}\}\s*\/>/g)]
      .filter(([, , options]) => !options.includes("href: null"))
      .map(([, name]) => name);

    expect(visibleScreens).toEqual(["index", "concierge/index", "records/index", "mypage/index"]);
  });

  it("designをrouteとして登録せず、app配下にもdesignファイルを置かない", () => {
    expect(layoutSource).not.toContain('name="design/');
    expect(() => readdirSync(resolve(mobileRoot, "app/design"))).toThrow();
    expect(readdirSync(resolve(mobileRoot, "design")).sort()).toEqual([
      "cardSizes.ts",
      "ctaSizes.ts",
      "radius.ts",
      "semanticColorTokens.ts",
      "shadow.ts",
      "spacing.ts",
    ]);
  });
});
