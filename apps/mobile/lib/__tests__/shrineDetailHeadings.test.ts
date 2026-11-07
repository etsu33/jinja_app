// 神社詳細の見出しに丸数字を入れないことを確かめる(mypageAuthEntry.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import * as shared from "../../../../packages/shared/recommendationReasonAuthority";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/shrines/[id].tsx"), "utf8");
const CIRCLED_NUMBER = /[①②③④⑤⑥⑦⑧⑨]/;

describe("神社詳細の見出し", () => {
  it("共通の見出しの言葉に丸数字が入らない", () => {
    const headings = [
      shared.CONSULTATION_SUMMARY_HEADING,
      shared.RECOMMENDATION_REASON_FACT_HEADING,
      shared.LEGACY_RECOMMENDATION_REASON_HEADING,
      shared.CONSULTATION_MEANING_HEADING,
      shared.SHRINE_MEANING_HEADING,
      shared.VISIT_PERSPECTIVE_HEADING,
      shared.ABOUT_SHRINE_HEADING,
    ];
    expect(headings).toEqual([
      "今回の相談の整理",
      "選ばれた背景",
      "選ばれた理由",
      "今回の相談との意味",
      "この神社で受け取る意味",
      "参拝するときの視点",
      "この神社について",
    ]);
    for (const heading of headings) {
      expect(heading).not.toMatch(CIRCLED_NUMBER);
    }
  });

  it("モバイルの神社詳細の画面に、丸数字の見出しが残っていない", () => {
    const cardTitles = [...source.matchAll(/<Text style=\{styles\.cardTitle\}>([^<]*)<\/Text>/g)].map((m) => m[1]);
    expect(cardTitles.length).toBeGreaterThan(0);
    for (const title of cardTitles) {
      expect(title).not.toMatch(CIRCLED_NUMBER);
    }
  });

  it("相談から開いたときの見出しは、共通の見出しの言葉を使う", () => {
    for (const name of [
      "CONSULTATION_SUMMARY_HEADING",
      "RECOMMENDATION_REASON_FACT_HEADING",
      "LEGACY_RECOMMENDATION_REASON_HEADING",
      "CONSULTATION_MEANING_HEADING",
      "SHRINE_MEANING_HEADING",
      "VISIT_PERSPECTIVE_HEADING",
      "ABOUT_SHRINE_HEADING",
    ]) {
      expect(source).toContain(`{${name}}`);
    }
  });

  it("「この神社について」の出し分けに、確認済みの御祭神・由緒のデータの有無を渡す", () => {
    expect(source).toMatch(/hasDeities: \(shrine\?\.deities\?\.length \?\? 0\) > 0/);
    expect(source).toMatch(/hasHistories: \(shrine\?\.histories\?\.length \?\? 0\) > 0/);
  });
});
