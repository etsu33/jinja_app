import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  new URL("../../components/profile/ProfilePickerModal.tsx", import.meta.url),
  "utf8",
);
const option = source.match(/<Pressable\s+key=\{option\.value\}[\s\S]*?(?=>\s*<Text)/)?.[0];

describe("ProfilePickerModalのアクセシビリティ契約", () => {
  it("選択肢の名前と現在の選択状態をradioとして公開する", () => {
    expect(option).toContain('accessibilityRole="radio"');
    expect(option).toContain("accessibilityLabel={option.label}");
    expect(option).toContain("accessibilityState={{ checked: selected }}");
    expect(source).toContain("const selected = option.value === selectedValue;");
  });

  it("選択時は閉じてから値を渡す", () => {
    expect(option).toMatch(/onPress=\{\(\) => \{\s*onClose\(\);\s*onSelect\(option\.value\);\s*\}\}/);
  });

  it("閉じる操作にボタンの役割と名前がある", () => {
    const close = source.match(/<Pressable\b[^>]*>\s*<Text style=\{styles\.close\}>/)?.[0];
    expect(close).toContain("onPress={onClose}");
    expect(close).toContain('accessibilityRole="button"');
    expect(close).toContain('accessibilityLabel="閉じる"');
  });
});
