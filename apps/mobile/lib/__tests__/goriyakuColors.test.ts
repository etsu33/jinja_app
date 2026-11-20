// ご利益の色が、札の面と画面の地の両方で読めることを固定する。
//
// 検索一覧と推薦結果は複数の神社を見比べる画面で、札がすべて同じ灰色だと
// 文字を読むしかない。色を持たせると形で拾える。色が情報を運ぶので装飾ではない。
//
// ただし色を増やすほど、どれかが読めなくなる危険が増える。全色を機械で検査する。
import { globSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { GORIYAKU_COLORS, GORIYAKU_FALLBACK, goriyakuColor } from "../../design/goriyakuColors";
import { kamimusubiLight as light } from "../../design/theme";
import { GORIYAKU_OPTIONS } from "../conditionPayload";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

function channel(value: number): number {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => channel(parseInt(h.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const entries = Object.entries(GORIYAKU_COLORS);

describe("ご利益の色", () => {
  it.each(entries)("%s は札の面の上で AA を満たす", (_label, tone) => {
    expect(contrast(tone.text, tone.surface)).toBeGreaterThanOrEqual(4.5);
  });

  it.each(entries)("%s は画面の地の上でも AA を満たす", (_label, tone) => {
    // 札の面が地に近い色なので、取り違えても読めなくならないことを確かめる。
    expect(contrast(tone.text, light.background)).toBeGreaterThanOrEqual(4.5);
  });

  it.each(entries)("%s の面は白カードと見分けがつく", (_label, tone) => {
    // 札であることが分かる程度に、白から離れていること。
    expect(contrast(tone.surface, light.surface)).toBeGreaterThan(1.02);
  });

  it("相談で選べるご利益はすべて色を持つ", () => {
    for (const label of GORIYAKU_OPTIONS) {
      expect(GORIYAKU_COLORS[label], `${label} に色がない`).toBeDefined();
    }
  });

  it("知らないご利益は既定の見た目へ落ちる", () => {
    // Backend は一覧に無いタグも返す(IT守護 など)。色を増やすより静かに出す。
    expect(goriyakuColor("IT守護")).toBe(GORIYAKU_FALLBACK);
    expect(GORIYAKU_FALLBACK.text).toBe(light.mutedSoft);
  });

  it("色が重複していない", () => {
    const texts = entries.map(([, tone]) => tone.text);
    expect(new Set(texts).size).toBe(texts.length);
  });
});

describe("色を使う場所", () => {
  const read = (file: string) => withoutComments(readFileSync(resolve(mobileRoot, file), "utf8"));

  it("見比べる画面だけが使う", () => {
    const users = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot }).filter(
      (file) => /goriyakuColor\(/.test(read(file)),
    );

    expect(users.sort()).toEqual(["app/(tabs)/concierge/index.tsx", "app/search/index.tsx"]);
  });

  it("神社詳細では使わない", () => {
    // 1社・札2〜3枚で探す行為が無い。色は意味を持たず飾りになる。
    expect(read("app/shrines/[id].tsx")).not.toContain("goriyakuColor");
  });

  it("相談フローでも使わない", () => {
    // 暗地のため。選択中は朝焼けの曙色で示す。
    expect(read("app/consultation/index.tsx")).not.toContain("goriyakuColor");
  });
});
