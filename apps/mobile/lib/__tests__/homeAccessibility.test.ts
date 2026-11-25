import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const home = readFileSync(new URL("../../app/(tabs)/index.tsx", import.meta.url), "utf8");
const consultation = readFileSync(new URL("../../app/consultation/index.tsx", import.meta.url), "utf8");

function pressables(source: string): string[] {
  return source.match(/<Pressable\b[\s\S]*?<\/Pressable>/g) ?? [];
}

describe("Homeのアクセシビリティ", () => {
  it("相談入力欄にアクセシブルな名前がある", () => {
    const input = home.match(/<TextInput\b[\s\S]*?\/>/)?.[0];
    expect(input).toContain('accessibilityLabel="相談内容"');
  });

  it("主CTAがボタンの名前を公開する", () => {
    const cta = pressables(home).find((block) => /styles\.primaryCta\b/.test(block));

    expect(cta).toContain('accessibilityRole="button"');
    expect(cta).toContain('accessibilityLabel="相談を続ける"');
  });
});

describe("相談フローのアクセシビリティ", () => {
  // ios-ui-spec-v2.md 08節で、テーマ・参拝スタイル・ご利益・条件の選択は
  // ホームから相談フローへ移した。名前と状態の公開もここで検証する。
  it("選択カードが選択肢の名前と選択状態を公開する", () => {
    const card = pressables(consultation).find((block) => /styles\.card\b/.test(block));

    expect(card).toContain('accessibilityRole="radio"');
    expect(card).toContain("accessibilityState={{ checked: selected }}");
    expect(card).toContain("accessibilityLabel={label}");
  });

  it("相談入力欄にアクセシブルな名前がある", () => {
    const input = consultation.match(/<TextInput\b[\s\S]*?\/>/)?.[0];
    expect(input).toContain('accessibilityLabel="相談内容"');
  });

  it("戻る・主CTA・スキップが名前を公開する", () => {
    const blocks = pressables(consultation);

    expect(blocks.find((b) => /styles\.backButton\b/.test(b))).toMatch(/accessibilityLabel=\{/);
    expect(blocks.find((b) => /styles\.cta\b/.test(b))).toMatch(/accessibilityLabel=\{/);
    expect(blocks.find((b) => /styles\.secondary\b/.test(b))).toMatch(/accessibilityLabel=\{/);
  });

  it("進捗を progressbar として公開する", () => {
    expect(consultation).toContain('accessibilityRole="progressbar"');
    expect(consultation).toMatch(/accessibilityValue=\{\{ min: 1, max: TOTAL, now: step \+ 1 \}\}/);
  });
});
