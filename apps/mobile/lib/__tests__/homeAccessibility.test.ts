import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync(new URL("../../app/index.tsx", import.meta.url), "utf8");
const pressables = source.match(/<Pressable\b[\s\S]*?<\/Pressable>/g) ?? [];

describe("Homeのアクセシビリティ", () => {
  it("相談入力欄にアクセシブルな名前がある", () => {
    const input = source.match(/<TextInput\b[^>]*\/>/)?.[0];
    expect(input).toContain('accessibilityLabel="相談内容"');
  });

  it.each([
    ["sendButton", '"相談内容を送信する"'],
    ["themePill", "{t}", "{{ selected: active }}"],
    ["accordionToggle", "{conditionToggleLabel}", "{{ expanded: showConditions }}"],
    ["primaryCta", '"この相談からご縁を見る"'],
  ])("%sがボタンの名前と必要な状態を公開する", (style, label, state?: string) => {
    const styleReference = new RegExp(`styles\\.${style}\\b`);
    const pressable = pressables.find((block) => styleReference.test(block));

    expect(pressable).toContain('accessibilityRole="button"');
    expect(pressable).toContain(`accessibilityLabel=${label}`);
    if (state) {
      expect(pressable).toContain(`accessibilityState=${state}`);
    }
  });
});
