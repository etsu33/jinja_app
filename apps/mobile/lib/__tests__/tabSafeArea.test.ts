// タブ画面の上部セーフエリアを検証する
// (routerStructure.test.ts と同じくソースをテキストとして読む)。
//
// 下層画面はStackのネイティブヘッダーがDynamic Island / ステータスバーを避けるが、
// タブ4画面はヘッダーを持たないため、自分で inset を足す必要がある。
// 対応前は全画面が画面最上端から描画しており、iPhoneでブランドヘッダーや
// 見出しがDynamic Islandに隠れていた。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

const TAB_SCREENS = [
  "app/(tabs)/index.tsx",
  "app/(tabs)/concierge/index.tsx",
  "app/(tabs)/records/index.tsx",
  "app/(tabs)/mypage/index.tsx",
];

function read(file: string): string {
  return readFileSync(resolve(mobileRoot, file), "utf8");
}

describe("タブ画面の上部セーフエリア", () => {
  it.each(TAB_SCREENS)("%s が useSafeAreaInsets を取る", (file) => {
    const source = read(file);

    expect(source).toContain('import { useSafeAreaInsets } from "react-native-safe-area-context";');
    expect(source).toContain("const insets = useSafeAreaInsets();");
  });

  it.each(TAB_SCREENS)("%s が inset を上余白に足す", (file) => {
    expect(read(file)).toMatch(/paddingTop: insets\.top \+ /);
  });

  it.each(TAB_SCREENS)("%s の最上位コンテナに固定の paddingTop を残さない", (file) => {
    // StyleSheet 側に paddingTop を残すと inset を足した値に上書きされるか、
    // 逆に上書きしてしまい、どちらが効くかがソースから読めなくなる。
    const source = read(file);
    const styleBlocks = [...source.matchAll(/\n {2}(content|header|screen): \{([^{}]*)\},/g)];

    for (const [, key, body] of styleBlocks) {
      expect(body, key).not.toMatch(/paddingTop: [0-9]/);
    }
  });
});
