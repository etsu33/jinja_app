// タブ画面の上部セーフエリアを検証する
// (routerStructure.test.ts と同じくソースをテキストとして読む)。
//
// 下層画面はStackのネイティブヘッダーがDynamic Island / ステータスバーを避けるが、
// タブ4画面はヘッダーを持たないため、自分で inset を足す必要がある。
// 対応前は全画面が画面最上端から描画しており、iPhoneでブランドヘッダーや
// 見出しがDynamic Islandに隠れていた。
//
// 守りたいのは「文字が inset の内側に収まること」。満たし方は2通りある。
//
//  A. スクロール領域そのものを inset の内側に置く（3画面）
//  B. 色の付いた帯をステータスバーの下まで伸ばし、その中身を inset + 余白で
//     下げる（ホーム）。帯が暗色で、かつステータスバーを明色へ切り替えている
//     ことが条件。この3つが揃って初めて安全になる。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

// A の画面。スクロール領域の外側で inset を確保する。
const INSET_OUTSIDE_SCROLL = [
  "app/(tabs)/concierge/index.tsx",
  "app/(tabs)/records/index.tsx",
  "app/(tabs)/mypage/index.tsx",
];

// B の画面。深藍の帯がステータスバーの下まで伸びる。
const BANDED_SCREEN = "app/(tabs)/index.tsx";

const TAB_SCREENS = [...INSET_OUTSIDE_SCROLL, BANDED_SCREEN];

function read(file: string): string {
  return readFileSync(resolve(mobileRoot, file), "utf8");
}

describe("タブ画面の上部セーフエリア", () => {
  it.each(TAB_SCREENS)("%s が useSafeAreaInsets を取る", (file) => {
    const source = read(file);

    expect(source).toContain('import { useSafeAreaInsets } from "react-native-safe-area-context";');
    expect(source).toContain("const insets = useSafeAreaInsets();");
  });

  it.each(INSET_OUTSIDE_SCROLL)("%s がスクロール領域の外側で inset を確保する", (file) => {
    // contentContainerStyle 側に inset を足すとコンテンツがステータスバーの
    // 下へ潜り、ヘッダーのぼかしが無いこれらの画面では Dynamic Island と
    // 電波・バッテリーに文字が重なる(iPhone 17 / iOS 26 で確認)。
    expect(read(file)).toMatch(/paddingTop: insets\.top(?!\s*\+)/);
  });

  it.each(INSET_OUTSIDE_SCROLL)("%s が inset をスクロール中身の余白に足さない", (file) => {
    expect(read(file)).not.toMatch(/paddingTop: insets\.top\s*\+/);
  });
});

describe("ホームの帯がステータスバーの下まで伸びる条件", () => {
  const home = read(BANDED_SCREEN);

  it("帯の中身は inset に余白を足して下げる", () => {
    expect(home).toMatch(/paddingTop: insets\.top \+ MASTHEAD_TOP_PADDING/);
  });

  it("帯は藍で塗られている", () => {
    // 塗りが無いと、ただ文字がステータスバーへ潜るだけになる。
    // 実際の地は LinearGradient。読み込み前の下地として同系色を置く。
    expect(home).toMatch(/masthead: \{[\s\S]*?backgroundColor: dawnNight\.colors\[0\]/);
    expect(home).toMatch(/<LinearGradient[\s\S]{0,200}?dawnNight\.colors\[0\]/);
  });

  it("この画面にいる間だけステータスバーを明色にする", () => {
    // root の _layout.tsx は地が生成りの前提で "dark" を指定している。
    // 暗い帯の上では暗い文字が読めないため切り替え、離れるときに戻す。
    expect(home).toContain('setStatusBarStyle("light")');
    expect(home).toMatch(/return \(\) => setStatusBarStyle\("dark"\)/);
    expect(home).toContain("useFocusEffect");
  });

  it("帯はスクロールしない", () => {
    // 帯が流れると、生成りが明色のステータスバーの下へ来て文字が消える。
    // masthead が ScrollView より前にあること。
    const mastheadAt = home.indexOf("styles.masthead");
    const scrollAt = home.indexOf("<ScrollView");
    expect(mastheadAt).toBeGreaterThan(0);
    expect(mastheadAt).toBeLessThan(scrollAt);
  });
});
