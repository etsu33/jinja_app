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

  it("login / signup を非表示routeとして登録し、相互に導線を持つ", () => {
    expect(layoutSource).toMatch(/<Tabs\.Screen name="login" options=\{\{ href: null \}\} \/>/);
    expect(layoutSource).toMatch(/<Tabs\.Screen name="signup" options=\{\{ href: null \}\} \/>/);

    const loginSource = readFileSync(resolve(mobileRoot, "app/login.tsx"), "utf8");
    const signupSource = readFileSync(resolve(mobileRoot, "app/signup.tsx"), "utf8");
    const authPromptSource = readFileSync(resolve(mobileRoot, "components/common/AuthPrompt.tsx"), "utf8");

    expect(loginSource).toContain('router.replace("/signup")');
    expect(loginSource).toContain("新規登録はこちら");
    expect(signupSource).toContain('router.replace("/login")');
    expect(signupSource).toContain("ログインはこちら");
    expect(authPromptSource).toContain('router.push("/signup")');
  });

  it("designをrouteとして登録せず、app配下にもdesignファイルを置かない", () => {
    expect(layoutSource).not.toContain('name="design/');
    expect(layoutSource).not.toContain('name="theme"');
    expect(() => readdirSync(resolve(mobileRoot, "app/design"))).toThrow();
    expect(() => readFileSync(resolve(mobileRoot, "app/theme.ts"), "utf8")).toThrow();
    expect(readdirSync(resolve(mobileRoot, "design")).sort()).toEqual([
      "cardSizes.ts",
      "ctaSizes.ts",
      "radius.ts",
      "semanticColorTokens.ts",
      "shadow.ts",
      "spacing.ts",
      "theme.ts",
    ]);
  });
});
