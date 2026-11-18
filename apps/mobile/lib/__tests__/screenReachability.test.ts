// すべての画面にアプリ内の導線があることを検証する
// (routerStructure.test.ts と同じくソースをテキストとして読む)。
//
// 参拝履歴 / 最近見た神社 / ランキングは、実装済みのままアプリ内のどこからも
// リンクされていなかった(導入コミット以降、一度もリンクされた形跡が無い)。
// 一方でマイページには件数、検索には人気上位3件という「要約」だけが出ており、
// その行き先が無い状態だった。同じ状態へ戻らないよう、導線の有無をテストで守る。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { globSync } from "node:fs";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function read(file: string): string {
  return readFileSync(resolve(mobileRoot, file), "utf8");
}

const screenSources = globSync(["app/**/*.tsx"], { cwd: mobileRoot })
  .filter((file) => !file.endsWith("_layout.tsx"))
  .map((file) => read(file))
  .join("\n");

// ルート -> そこへ push / replace する画面があることを期待する
const ROUTES_NEEDING_ENTRY = [
  "/favorites",
  "/goshuin",
  "/journey",
  "/login",
  "/premium",
  "/profile",
  "/ranking",
  "/recently-viewed",
  "/search",
  "/signup",
  "/visit-history",
  "/consultation-history",
];

describe("画面の到達性", () => {
  it.each(ROUTES_NEEDING_ENTRY)("%s へ移る導線がアプリ内にある", (route) => {
    expect(screenSources).toMatch(new RegExp(`["'\`]${route}["'\`]`));
  });

  it("マイページの利用状況の数字が、すべて対応する一覧へ繋がる", () => {
    const source = read("app/(tabs)/mypage/index.tsx");
    const usage = source.slice(source.indexOf(">利用状況<"), source.indexOf(">Premium<"));

    for (const [, props] of usage.matchAll(/<UsageStat\s+([\s\S]*?)\/>/g)) {
      expect(props).toMatch(/onPress=\{\(\) => router\.push\("\/[a-z-]+"\)\}/);
    }
  });

  it("マイページの御朱印の件数を実データから出す", () => {
    // 以前は value="0" のハードコードで、helperも「次フェーズで連携」だった。
    // getCounts() は stamps を返しているのに捨てていた。
    const source = read("app/(tabs)/mypage/index.tsx");

    expect(source).toMatch(/getCounts\(\)\s*\.then\(\(\{ visits, stamps \}\)/);
    expect(source).toContain("setStampCount(stamps);");
    expect(source).not.toContain("次フェーズで連携");
  });

  it("検索の人気の神社から、全件のランキングへ行ける", () => {
    // 検索側は上位3件だけを出している(slice(0, 3))。
    const source = read("app/search/index.tsx");

    expect(source).toContain(".slice(0, 3)");
    expect(source).toMatch(/onPress=\{\(\) => router\.push\("\/ranking"\)\}/);
  });

  it("振り返り履歴を持たない(ご縁の歩みと内容が重複するため削除した)", () => {
    expect(globSync(["app/reflection-history/**"], { cwd: mobileRoot })).toEqual([]);
    expect(screenSources).not.toContain("/reflection-history");
  });
});
