// 実在の神社に、その神社のものでない写真を結びつけないことを固定する。
//
// 以前 data/shrines.ts の imageUrl は picsum.photos のランダム画像で、
// 明治神宮・伏見稲荷大社・神田明神の写真として表示されていた。
// ブランド指示書の「神社ごとの写真が存在しない場合、架空の建築画像を
// 実在神社の写真として扱わない。画像の使用権利と出典を確認すること」に反する。
//
// あわせて、実測ではない評価値・お気に入り数を持たないことも固定する。
// 画面に出ていなくても、データにあると後から繋がれてしまう。
import { globSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { SHRINES } from "../../data/shrines";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

/** コメントを除いたコード本体。旧実装の名前は説明として残すため、検査からは外す。 */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

// 被写体を指定できない、ランダム画像・プレースホルダ画像の配信元。
const PLACEHOLDER_IMAGE_HOSTS = [
  "picsum.photos",
  "placehold.co",
  "placeholder.com",
  "placekitten.com",
  "dummyimage.com",
  "loremflickr.com",
  "source.unsplash.com",
];

describe("神社の写真", () => {
  it("ローカルの神社データは写真を持たない", () => {
    // 出典と権利を確認した写真が用意できたら、このテストを更新したうえで入れる。
    const withPhoto = SHRINES.filter((shrine) => shrine.imageUrl);
    expect(withPhoto).toEqual([]);
  });

  it("どのソースもプレースホルダ画像を神社の写真に使わない", () => {
    const files = globSync(["app/**/*.tsx", "lib/**/*.ts", "components/**/*.tsx", "data/**/*.ts"], {
      cwd: mobileRoot,
    }).filter((file) => !file.includes("__tests__"));

    const offenders: string[] = [];
    for (const file of files) {
      const source = withoutComments(readFileSync(resolve(mobileRoot, file), "utf8"));
      for (const host of PLACEHOLDER_IMAGE_HOSTS) {
        if (source.includes(host)) offenders.push(`${file} -> ${host}`);
      }
    }

    expect(offenders).toEqual([]);
  });

  it("実測でない評価値・お気に入り数を持たない", () => {
    for (const shrine of SHRINES) {
      expect(shrine).not.toHaveProperty("rating");
      expect(shrine).not.toHaveProperty("favorites");
    }
  });
});

describe("写真が無いときの表示", () => {
  it("検索の一覧は、写真が無ければ枠ごと出さない", () => {
    const search = readFileSync(resolve(mobileRoot, "app/search/index.tsx"), "utf8");
    // 無条件の <Image> だと uri: undefined で空の箱が残る。
    expect(search).toMatch(/\{s\.imageUrl \? <Image source=\{\{ uri: s\.imageUrl \}\}/);
  });
});
