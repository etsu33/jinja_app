// タブバーに出さない画面が、expo-router 58 でホームへ移されないことを検証する
// (mypageAccountDeletion.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/_layout.tsx"), "utf8");

const HIDDEN_ROUTES = [
  "journey/index",
  "premium/index",
  "favorites/index",
  "goshuin/index",
  "goshuin/upload",
  "visit-history/index",
  "reflection-history/index",
  "consultation-history/index",
  "consultation-history/[id]",
  "recently-viewed/index",
  "profile/index",
  "search/index",
  "shrines/[id]",
  "ranking/index",
  "login",
  "signup",
];

describe("タブバーに出さない画面", () => {
  it("href: null を使わない(expo-router 58 では開くとホームへ移されるため)", () => {
    expect(source).not.toMatch(/\{\s*href:\s*null/);
  });

  it("hidden: true を使わない(href: null と同じくホームへ移されるため)", () => {
    expect(source).not.toMatch(/\{\s*hidden:\s*true/);
  });

  it("ボタンだけを見えなくする options を定義している", () => {
    expect(source).toMatch(
      /const hiddenTabOptions = \{\s*tabBarItemStyle: \{ display: "none" \},\s*tabBarButton: \(\) => null,\s*\} as const;/,
    );
  });

  it.each(HIDDEN_ROUTES)("%s は hiddenTabOptions でボタンだけを隠す", (name) => {
    expect(source).toContain(`<Tabs.Screen name="${name}" options={hiddenTabOptions} />`);
  });
});
