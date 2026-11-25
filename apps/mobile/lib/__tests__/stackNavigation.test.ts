// 下層画面がStackのネイティブヘッダーで戻れることを検証する
// (routerStructure.test.ts と同じくソースをテキストとして読む)。
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const rootLayout = readFileSync(resolve(mobileRoot, "app/_layout.tsx"), "utf8");

// タブバーに出さない下層画面。すべてrootのStackが持ち、戻るはネイティブヘッダーが出す。
const STACK_ROUTES = [
  "search/index",
  "shrines/[id]",
  "favorites/index",
  "ranking/index",
  "journey/index",
  "premium/index",
  "profile/index",
  "goshuin/index",
  "goshuin/upload",
  "visit-history/index",
  "consultation-history/index",
  "consultation-history/[id]",
  "recently-viewed/index",
  "compass/index",
  "login",
  "signup",
];

const SCREEN_FILES = [
  ...STACK_ROUTES.map((route) => `app/${route}.tsx`),
  "app/(tabs)/index.tsx",
  "app/(tabs)/concierge/index.tsx",
  "app/(tabs)/records/index.tsx",
  "app/(tabs)/mypage/index.tsx",
];

describe("下層画面のStack登録", () => {
  it.each(STACK_ROUTES)("%s をStack screenとして登録する", (route) => {
    // 引用符で囲まれたキー("search/index")と、囲まれないキー(login)の両方を許す。
    expect(rootLayout).toMatch(new RegExp(`(^|\\s)"?${route.replace(/[[\]]/g, "\\$&")}"?: "`, "m"));
  });

  it.each(STACK_ROUTES)("%s の画面ファイルが存在する", (route) => {
    expect(existsSync(resolve(mobileRoot, `app/${route}.tsx`))).toBe(true);
  });

  it("Stackに登録するrouteと画面ファイルの数が一致する", () => {
    const table = rootLayout.slice(
      rootLayout.indexOf("const SCREEN_TITLES"),
      rootLayout.indexOf("export default function"),
    );
    const titles = [...table.matchAll(/^ {2}"?([A-Za-z[\]/-]+)"?: "/gm)].map(([, name]) => name);

    expect(titles.sort()).toEqual([...STACK_ROUTES].sort());
  });
});

describe("手書きの戻るUI", () => {
  it.each(SCREEN_FILES)("%s に「← 戻る」を書かない", (file) => {
    const source = readFileSync(resolve(mobileRoot, file), "utf8");
    const jsx = source.slice(0, source.lastIndexOf("StyleSheet.create("));

    // 戻る導線はネイティブヘッダー(Stack)とタブバーが持つ。画面内に矢印付きの
    // 擬似ヘッダーを置くと、タップ領域が44pt未満になりスワイプバックとも二重になる。
    expect(jsx).not.toMatch(/←\s*(戻る|記録へ戻る|マイページへ戻る|相談履歴へ戻る)/);
  });
});
