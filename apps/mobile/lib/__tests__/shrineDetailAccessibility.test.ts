import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync(new URL("../../app/shrines/[id].tsx", import.meta.url), "utf8");

describe("神社詳細のアクセシビリティ契約", () => {
  it("お気に入りボタンの名前と現在の状態を公開する", () => {
    const favorite = source.match(/<Pressable\s+onPress=\{onToggleFav\}[^>]*>/)?.[0];
    expect(favorite).toContain('accessibilityRole="button"');
    expect(favorite).toContain('accessibilityLabel="お気に入りの切り替え"');
    expect(favorite).toContain("accessibilityState={{ selected: fav }}");
    expect(source).toMatch(/const now = await toggleFavorite\(String\(shrineId\)\);\s*setFav\(now\);/);
  });

  it("振り返り入力欄に名前がある", () => {
    const input = source.match(/<TextInput\b[\s\S]*?\/>/g)
      ?.find((tag) => tag.includes("value={reflectionAnswer}"));
    expect(input).toContain('accessibilityLabel="参拝後の振り返り"');
    expect(input).toContain('placeholder="参拝して感じたことを一言で残す"');
  });

  it("振り返り保存の成功分岐で状態を更新し、スクリーンリーダーへ通知する", () => {
    const save = source.slice(source.indexOf("const onSaveReflection"), source.indexOf("const onGoToConsultation"));
    expect(save).toContain("const saved = await createShrineReflection(");
    expect(save).toMatch(
      /if \(saved\) \{\s*setReflectionSaved\(true\);\s*trackReflectionSaved\(\{[^}]*\}\);\s*AccessibilityInfo\.announceForAccessibility\("振り返りを保存しました"\);\s*\}/,
    );
    expect(save).not.toContain("router.");
  });

  it("参拝記録と保存後の相談への遷移を既存の操作に結び付ける", () => {
    expect(source).toMatch(
      /title=\{visited \? "参拝済みとして記録しました" : "参拝したことを記録する"\}[^>]*onPress=\{onVisitDone\}/,
    );
    const visit = source.match(/const onVisitDone = [\s\S]*?\n  \}, \[[^\]]*\]\);/)?.[0];
    expect(visit).toMatch(/const result = await createVisitByShrineId\(targetShrineId\);\s*if \(!result\) return;\s*setVisited\(true\);/);
    expect(visit).not.toContain("announceForAccessibility");
    const consultation = source.match(/const onGoToConsultation = [\s\S]*?\n  \}, \[[^\]]*\]\);/)?.[0];
    expect(consultation).toContain('router.push("/concierge");');
    expect(source).toMatch(/\{reflectionSaved \? \(\s*<View style=\{styles\.nextConsultationWrap\}>\s*<Button[^>]*onPress=\{onGoToConsultation\}/);
  });
});
