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

  it.each(TAB_SCREENS)("%s がスクロール領域の外側で inset を確保する", (file) => {
    // contentContainerStyle 側に inset を足すとコンテンツがステータスバーの
    // 下へ潜り、ヘッダーのぼかしが無いこれらの画面では Dynamic Island と
    // 電波・バッテリーに文字が重なる(iPhone 17 / iOS 26 で確認)。
    // スクロール領域そのものを inset の内側に置く。
    expect(read(file)).toMatch(/paddingTop: insets\.top(?!\s*\+)/);
  });

  it.each(TAB_SCREENS)("%s が inset をスクロール中身の余白に足さない", (file) => {
    expect(read(file)).not.toMatch(/paddingTop: insets\.top\s*\+/);
  });
});
