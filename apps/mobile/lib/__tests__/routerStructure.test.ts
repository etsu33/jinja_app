import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const rootLayout = readFileSync(resolve(mobileRoot, "app/_layout.tsx"), "utf8");
const tabsLayout = readFileSync(resolve(mobileRoot, "app/(tabs)/_layout.tsx"), "utf8");

/** コメントを除いたコード本体。旧実装の名前は説明として残すため、検査からは外す。 */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

const tabsLayoutCode = withoutComments(tabsLayout);

describe("Expo Router structure", () => {
  it("rootはStackで、(tabs)を初期routeにする", () => {
    // initialRouteNameが無いと、深いリンクで直接開いたときに戻り先が無くなり、
    // ネイティブの戻るボタンもスワイプバックも出ない。
    expect(rootLayout).toMatch(/<Stack\b/);
    expect(rootLayout).toMatch(/export const unstable_settings = \{\s*anchor: "\(tabs\)",\s*\};/);
    expect(rootLayout).toContain('<Stack.Screen name="(tabs)" options={{ headerShown: false }} />');
  });

  it("正式な4タブだけをタブバーに出す", () => {
    const visibleScreens = [...tabsLayout.matchAll(/<Tabs\.Screen\s+name="([^"]+)"/g)].map(([, name]) => name);

    expect(visibleScreens).toEqual(["index", "concierge/index", "records/index", "mypage/index"]);
  });

  it("隠しタブの回避策を一切使わない", () => {
    // 旧実装は下層15画面をTabs.Screenとして登録し、ボタンだけを消していた。
    for (const source of [rootLayout, tabsLayout]) {
      expect(source).not.toMatch(/\{\s*href:\s*null/);
      expect(source).not.toMatch(/\{\s*hidden:\s*true/);
      expect(source).not.toContain("tabBarButton: () => null");
      expect(source).not.toContain('tabBarItemStyle: { display: "none" }');
    }
  });

  it("アイコンをIoniconsに統一し、MaterialIconsを使わない", () => {
    // 旧実装は MaterialIcons で、iOSにAndroidのイディオムが出ていた。
    expect(tabsLayoutCode).toContain('import Ionicons from "@expo/vector-icons/Ionicons";');
    expect(tabsLayoutCode).not.toContain("MaterialIcons");
  });

  it("非選択は線画、選択は塗りで区別する", () => {
    expect(tabsLayoutCode).toMatch(/focused \? TAB_ICONS\[key\] : \(`\$\{TAB_ICONS\[key\]\}-outline`/);
  });

  it("中央タブだけを大きくしたり浮かせたりしない", () => {
    // 旧実装は中央に 54pt の円を marginTop: -18 で浮かせており、他アイコン(24pt)の
    // 2.25倍かつ、はみ出した部分がタブボタンの当たり判定の外で押せなかった。
    expect(tabsLayoutCode).not.toMatch(/marginTop: -/);
    expect(tabsLayoutCode).not.toMatch(/borderRadius:.*\/ 2/);
    expect(tabsLayoutCode).not.toContain("featuredIcon");

    // 4タブとも同じ生成関数からアイコンを受け取る。
    const icons = [...tabsLayoutCode.matchAll(/tabBarIcon: (\w+)\(/g)].map(([, fn]) => fn);
    expect(icons).toEqual(["tabIcon", "tabIcon", "tabIcon", "tabIcon"]);
  });

  it("タブバーの高さを固定しない(ホームインジケータのinsetを潰さないため)", () => {
    const tabBarStyle = tabsLayout.slice(tabsLayout.indexOf("tabBarStyle: {"), tabsLayout.indexOf("}", tabsLayout.indexOf("tabBarStyle: {")));

    expect(tabBarStyle).not.toMatch(/\bheight:/);
  });

  it("login / signup をStack screenとして登録し、相互に導線を持つ", () => {
    expect(rootLayout).toMatch(/\blogin: "/);
    expect(rootLayout).toMatch(/\bsignup: "/);

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
    expect(rootLayout).not.toContain('name="design/');
    expect(rootLayout).not.toContain('name="theme"');
    expect(() => readdirSync(resolve(mobileRoot, "app/design"))).toThrow();
    expect(() => readFileSync(resolve(mobileRoot, "app/theme.ts"), "utf8")).toThrow();
    expect(readdirSync(resolve(mobileRoot, "design")).sort()).toEqual([
      "cardSizes.ts",
      "ctaSizes.ts",
      "platformTheme.ts",
      "radius.ts",
      "semanticColorTokens.ts",
      "shadow.ts",
      "spacing.ts",
      "theme.ts",
      "typography.ts",
    ]);
  });
});
