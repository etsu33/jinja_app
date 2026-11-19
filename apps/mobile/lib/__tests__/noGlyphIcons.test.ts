// アイコンの代わりに文字のグリフを置かないことを固定する。
//
// 絵文字や記号(⛩ □ ♡ ✓)は端末のフォント次第で字形が変わり、豆腐になることもある。
// ブランドの同一性を保てず、作りかけに見える。アイコンは Ionicons に統一する
// (ios-ui-spec-v2.md / app/(tabs)/_layout.tsx の方針)。
//
// 写真が無い場所に絵文字の鳥居を置いていたのが典型で、「写真が無いこと」を
// 画面いっぱいに見せていた。枠ごと出さないのが正しい。
import { globSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

/** コメントを除いたコード本体。旧実装の名前は説明として残すため、検査からは外す。 */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

// アイコン・印の代用として使われうる記号。
// 矢印(→ など)は対象外。本文中で2つの値をつなぐ用途(気分の変化「前 → 後」)があり、
// それはアイコンの代用ではないため。アイコンとしての矢印は Ionicons を使う。
const GLYPHS_AS_ICONS = ["⛩", "♡", "♥", "✓", "✔", "□", "■", "★", "☆"];

function isEmoji(codePoint: number): boolean {
  return (
    (codePoint >= 0x1f300 && codePoint <= 0x1faff) || (codePoint >= 0x2600 && codePoint <= 0x27bf)
  );
}

const SCREEN_FILES = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot });

describe("アイコンに文字のグリフを使わない", () => {
  it("画面のコードに記号の印が残っていない", () => {
    const offenders: string[] = [];

    for (const file of SCREEN_FILES) {
      const code = withoutComments(readFileSync(resolve(mobileRoot, file), "utf8"));
      for (const glyph of GLYPHS_AS_ICONS) {
        if (code.includes(glyph)) offenders.push(`${file} -> ${glyph}`);
      }
    }

    expect(offenders).toEqual([]);
  });

  it("画面のコードに絵文字が残っていない", () => {
    const offenders: string[] = [];

    for (const file of SCREEN_FILES) {
      const code = withoutComments(readFileSync(resolve(mobileRoot, file), "utf8"));
      for (const char of code) {
        if (isEmoji(char.codePointAt(0) ?? 0)) {
          offenders.push(`${file} -> ${char}`);
          break;
        }
      }
    }

    expect(offenders).toEqual([]);
  });
});

describe("写真が無いときの置き換え", () => {
  it("写真が無ければ画像の枠ごと出さない", () => {
    // 代替画像も灰色の箱も置かない。その神社のものではないため。
    const cases: [string, RegExp][] = [
      ["app/shrines/[id].tsx", /shrine\.imageUrl \? \([\s\S]{0,160}?\) : null\}/],
      ["app/favorites/index.tsx", /shrine\.photo_url \? \([\s\S]{0,200}?\) : null\}/],
      ["app/recently-viewed/index.tsx", /shrine\.photo_url \? \([\s\S]{0,160}?\) : null\}/],
      ["components/search/SelectedShrineMapCard.tsx", /shrine\.imageUrl \? \([\s\S]{0,160}?\) : null\}/],
    ];

    for (const [file, pattern] of cases) {
      const code = withoutComments(readFileSync(resolve(mobileRoot, file), "utf8"));
      expect(code, `${file} が写真無しのときに枠を残している`).toMatch(pattern);
    }
  });
});
