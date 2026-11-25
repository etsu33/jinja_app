// docs/design/ios-ui-spec-v2.md 27/28節。
// 推薦結果を読み物にする。「大量の独立カードに分断しない」。
//
// 旧実装は card > 塗りの箱 > 塗りの箱 の3段で、1件の結果に塗られた箱が
// 5つ以上積まれていた。節の区切りは細い罫と余白で作る。
//
// あわせて、同じ内容を2画面に重複させない。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

function read(relativePath: string): string {
  return withoutComments(readFileSync(resolve(mobileRoot, relativePath), "utf8"));
}

const concierge = read("app/(tabs)/concierge/index.tsx");
const shrineDetail = read("app/shrines/[id].tsx");

/** StyleSheet の1エントリ分の本文を取り出す。 */
function styleBody(source: string, name: string): string | null {
  const match = source.match(new RegExp(`\\n  ${name}: \\{([^}]*)\\}`));
  return match ? match[1] : null;
}

// 結果カードの中の節。どれも塗り・枠・角丸を持たない。
const SECTION_STYLES = [
  "reasonBlock",
  "reasonFactsCard",
  "directionReferenceCard",
  "actionV4Card",
  "actionV4Item",
];

describe("推薦結果を読み物にする(27/28節)", () => {
  it.each(SECTION_STYLES)("%s は塗りの箱にしない", (name) => {
    const body = styleBody(concierge, name);
    expect(body, `${name} が見つからない`).not.toBeNull();

    // カードの中で、さらに塗って枠で囲って角を丸めない。
    expect(body).not.toMatch(/backgroundColor:/);
    expect(body).not.toMatch(/borderRadius:/);
    expect(body).not.toMatch(/\bborderWidth:/);
  });

  it("節の区切りは罫で作る", () => {
    for (const name of ["reasonBlock", "reasonFactsCard", "directionReferenceCard", "actionV4Card"]) {
      expect(styleBody(concierge, name), `${name}`).toMatch(/borderTopWidth: 1/);
    }
    // 押せる項目だけは左罫にして、並びであることを示す。
    expect(styleBody(concierge, "actionV4Item")).toMatch(/borderLeftWidth: 2/);
  });

  it("順位は同じ数字を2回出さない", () => {
    // 旧実装は塗りの丸バッジ(rankBadge)と「ご縁1」で同じ数字を並べていた。
    expect(concierge).not.toContain("rankBadge");
    expect(concierge).toContain("ご縁{rank}");
  });
});

describe("2画面に同じ内容を置かない", () => {
  it("「参拝前にできること」は推薦結果だけが持つ", () => {
    // 神社詳細にも同じ3項目が出ていた。しかも1つめは「まず詳細を見て…」で、
    // 詳細を開いている画面で言うことではない。
    expect(concierge).toContain("参拝前にできること");

    const detailActionBlocks = shrineDetail.match(/参拝前にできること/g) ?? [];
    // 旧 V4 データが無いときのフォールバック1箇所だけ。
    expect(detailActionBlocks).toHaveLength(1);
    expect(shrineDetail).toContain("参拝前の問い");
  });

  it("見出しを英語にしない", () => {
    expect(shrineDetail).not.toContain("NEXT ACTION");
  });
});
