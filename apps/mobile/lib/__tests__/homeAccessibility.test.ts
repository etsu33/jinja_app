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

describe("iOSホーム改修の境界", () => {
  it("装飾は読み上げ対象・操作対象にしない", () => {
    expect(home).toContain('pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants"');
    expect(home).toContain('resizeMode="contain" accessible={false}');
  });

  it("配色とロゴをiOSに限定し、Web/Androidの既定表示を保持する", () => {
    expect(home).toContain('const isIndigoHome = Platform.OS === "ios";');
    expect(home).toContain('isIndigoHome ? <Image source={require("../../assets/icon.png")}');
    expect(home).toContain('isIndigoHome ? indigoStyles.searchEntryCta : styles.searchEntryCta');
    expect(home).toContain('isIndigoHome ? indigoStyles.primaryCtaPressed : styles.primaryCtaPressed');
    const layout = readFileSync(new URL("../../app/(tabs)/_layout.tsx", import.meta.url), "utf8");
    expect(layout).toContain('from "../../design/platformTheme"');
    expect(layout).toContain('tabBarActiveTintColor: theme.accent');
  });

  it("ホーム表示中だけ明色のステータスバーを重ねる", () => {
    expect(home).toContain('isIndigoHome && isHomeFocused ? <StatusBar style="light" /> : null');
    expect(home).toContain('return () => setHomeFocused(false)');
  });

  it("空入力と入力済みの相談遷移・検索の計測を維持する", () => {
    expect(home).toContain('const text = consultation.trim();');
    expect(home).toContain('if (!text) {\n      router.push("/consultation");\n      return;\n    }');
    expect(home).toContain('router.push(`/consultation?q=${encodeURIComponent(text)}&topicDone=1`)');
    expect(home).toContain('trackSearchEntryClick();');
    expect(home).toContain('router.push("/search")');
  });
});
