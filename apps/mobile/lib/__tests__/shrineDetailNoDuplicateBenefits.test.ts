// 神社詳細で、同じご利益が何度も出ないことを確かめる(shrineDetailHeadings.test.ts と同じくソースをテキストとして読む)。
//
// - 「神社の意味を知る」と「神社について」の欄は置かない。神社詳細の窓口(GET /shrines/<id>/)は
//   説明文(description / explanation)を返さず、ご利益の文字列(goriyaku)が代わりに出ていたため。
// - ご利益の名前は、上部のご利益の札(goriyaku_tags)だけで示す。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/shrines/[id].tsx"), "utf8");

/** 画面に出す文字(<Text> の中身)を集める。 */
function textNodes(): string[] {
  return [...source.matchAll(/<Text\b[^>]*>([^<]*)<\/Text>/g)].map((m) => m[1].trim()).filter(Boolean);
}

describe("神社詳細に、同じご利益を何度も出さない", () => {
  it("「神社の意味を知る」の見出しが画面に無い", () => {
    expect(source).not.toContain("神社の意味を知る");
  });

  it("「神社について」の見出しが画面に無い(「この神社について」は残る)", () => {
    expect(textNodes()).not.toContain("神社について");
    // 「この神社について」以外の「神社について」が、どこにも残っていない
    expect(source.replaceAll("この神社について", "")).not.toContain("神社について");
    expect(source).toContain("{ABOUT_SHRINE_HEADING}");
  });

  it("使わなくなった控えの文・仮の文が残っていない", () => {
    expect(source).not.toContain("の由緒やご利益を確認しながら");
    expect(source).not.toContain("ご利益や混雑、アクセス、御朱印情報などをここに表示します。");
  });

  it("説明文(description / explanation)とご利益の文字列(goriyaku)を、窓口の結果から読まない", () => {
    expect(source).not.toMatch(/api\.description\b/);
    expect(source).not.toMatch(/api\.explanation\b/);
    expect(source).not.toMatch(/api\.goriyaku\b(?!_tags)/);
    expect(source).not.toMatch(/shrine\??\.description\b/);
    expect(source).not.toMatch(/shrine\??\.explanation\b/);
  });

  it("神社のご利益(tags)は、上部のご利益の札だけで出す", () => {
    // tags は goriyaku_tags の名前だけから作る
    expect(source).toContain("tags: api.goriyaku_tags?.map((tag) => tag.name) ?? [],");
    // tags を画面に出すのは、ご利益の札の1か所だけ
    const renders = [...source.matchAll(/\btags\.map\(/g)];
    expect(renders).toHaveLength(1);
    expect(source).toMatch(/\{tags\.map\(\(t\) => \(\s*<View key=\{t\} style=\{styles\.tagPill\}>/);
  });

  it("使わなくなったスタイルが残っていない", () => {
    for (const name of ["explanationCard", "descCard", "descLabel", "descText"]) {
      expect(source).not.toContain(`${name}:`);
      expect(source).not.toContain(`styles.${name}`);
    }
  });
});
