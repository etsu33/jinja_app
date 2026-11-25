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
  "/compass",
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

describe("相談フロー (ios-ui-spec-v2.md 08節)", () => {
  const source = read("app/consultation/index.tsx");

  it("4ステップに分かれている", () => {
    const steps = [...source.matchAll(/^ {4}title: "/gm)];

    expect(steps).toHaveLength(4);
    expect(source).toContain("const TOTAL = STEPS.length;");
  });

  it("入力項目を1つも減らしていない（生年月日は除く）", () => {
    // Concierge へ渡す値は旧ホームの openConcierge と同じ契約を保つ。
    // 生年月日だけは外した（コンシェルジュでは生年月日を使わない。ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」）。
    expect(source).not.toContain('query.set("birthdate"');
    for (const key of ["q", "theme", "plannedVisitDate", "visitStyle", "goriyaku", "support"]) {
      expect(source).toContain(`query.set("${key}"`);
    }
    expect(source).toContain("setOriginSession(origin)");
    expect(source).toContain("resolveGoriyakuTagIds(selectedGoriyaku)");
  });

  it("ホームは相談フローへ渡すだけで、条件入力を持たない", () => {
    const home = read("app/(tabs)/index.tsx");

    expect(home).toContain("/consultation?q=");
    expect(home).toContain("encodeURIComponent(text)");
    expect(home).not.toContain("ConditionFieldsCard");
    expect(home).not.toContain("selectedVisitStyle");
    expect(home).not.toContain("selectedGoriyaku");
  });

  it("タブバーの外に置き、ネイティブヘッダーも出さない", () => {
    // 32節: Guided Journey 中はタブバーを原則非表示。
    // 22節: Navigation Header を大きく作らない(画面内に小さな戻るを持つ)。
    const rootLayout = read("app/_layout.tsx");
    const tabsLayout = read("app/(tabs)/_layout.tsx");

    expect(rootLayout).toContain('<Stack.Screen name="consultation/index" options={{ headerShown: false }} />');
    expect(tabsLayout).not.toContain("consultation");
  });

  it("1ステップの選択肢を6個以下に保つ", () => {
    // 40節: 1画面8個以上の選択肢を置かない。17節: 最大6程度。
    const options = read("lib/conditionPayload.ts");
    const lists: [string, string][] = [
      ["THEMES", source],
      ["VISIT_STYLE_OPTIONS", options],
      ["GORIYAKU_OPTIONS", options],
    ];

    for (const [name, from] of lists) {
      const body = from.match(new RegExp(`const ${name} = \\[([^\\]]*)\\]`))?.[1] ?? "";
      const items = body.match(/"[^"]+"/g) ?? [];

      expect(items.length, name).toBeGreaterThan(0);
      expect(items.length, name).toBeLessThanOrEqual(6);
    }
  });
});
