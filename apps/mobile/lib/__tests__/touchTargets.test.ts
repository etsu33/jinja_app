// 押せる要素の最小タップ領域(HIG 44pt)を検証する
// (routerStructure.test.ts と同じくソースをテキストとして読む)。
//
// 文字と余白だけで組むと、13〜15ptの文字では37pt前後にしかならない。
// 高さを明示していない要素は、Typography Tokenの行高が変わるたびに
// 気づかないまま44ptを割るため、対象をここに列挙して固定する。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

const MINIMUM = 44;

// [ファイル, スタイル名] — 文字量に関係なく高さが決まる押せる要素。
// 画像や複数行を含むカード(popularCard, actionV4Item など)は中身で44ptを超えるため対象外。
// hitSlopで領域を足している要素(ranking の heartBtn)も対象外。
const SIZED_TARGETS: [string, string][] = [
  ["app/(tabs)/index.tsx", "themePill"],
  ["app/(tabs)/index.tsx", "accordionToggle"],
  ["app/(tabs)/index.tsx", "primaryCta"],
  ["app/profile/index.tsx", "selectButton"],
  ["components/profile/ProfilePickerModal.tsx", "closeButton"],
  ["components/profile/ProfilePickerModal.tsx", "option"],
  ["components/common/AuthPrompt.tsx", "signupButton"],
  ["components/common/AuthPrompt.tsx", "closeButton"],
  ["app/login.tsx", "linkButton"],
  ["app/signup.tsx", "linkButton"],
];

function readStyle(file: string, key: string): string {
  const source = readFileSync(resolve(mobileRoot, file), "utf8");
  const match = source.match(new RegExp(`\\n {2}${key}: \\{([^{}]*)\\},`));
  if (!match) throw new Error(`${file} に ${key} が無い`);
  return match[1];
}

describe("最小タップ領域", () => {
  it.each(SIZED_TARGETS)("%s の %s が44pt以上の高さを持つ", (file, key) => {
    const body = readStyle(file, key);
    const height = body.match(/(?<![a-zA-Z])height: ([0-9]+)/)?.[1];
    const minHeight = body.match(/minHeight: ([0-9]+)/)?.[1];
    const effective = Number(height ?? minHeight ?? 0);

    expect(effective).toBeGreaterThanOrEqual(MINIMUM);
  });

  it("共通Buttonのサイズが44pt以上", () => {
    const source = readFileSync(resolve(mobileRoot, "design/ctaSizes.ts"), "utf8");
    const sizes = ["primaryHeight", "mediumHeight", "smallHeight"].map(
      (key) => Number(source.match(new RegExp(`${key}: ([0-9]+)`))?.[1]),
    );

    for (const size of sizes) expect(size).toBeGreaterThanOrEqual(MINIMUM);
  });
});
