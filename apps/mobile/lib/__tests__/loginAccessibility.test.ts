import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync(new URL("../../app/login.tsx", import.meta.url), "utf8");

describe("Login画面の操作契約", () => {
  it("中央寄せのフォームをスクロールでき、キーボード表示中も操作できる構造を持つ", () => {
    const root = source.match(/return\s*\(\s*(<ScrollView\b[^>]*>)/)?.[1];
    expect(root).toContain("style={styles.screen}");
    expect(root).toContain("contentContainerStyle={styles.content}");
    expect(root).toContain('keyboardShouldPersistTaps="handled"');
    expect(source).toMatch(
      /content:\s*\{\s*flexGrow: 1,\s*justifyContent: "center",\s*padding: spacing\.screenX,\s*\}/,
    );
  });

  it.each([
    ["username", "ユーザー名"],
    ["password", "パスワード"],
  ])("%sの入力欄に名前がある", (field, label) => {
    const inputs = source.match(/<TextInput\b[^>]*\/>/g) ?? [];
    const input = inputs.find((tag) => tag.includes(`value={${field}}`));
    expect(input).toContain(`accessibilityLabel="${label}"`);
  });

  it("ログインエラーをalertとして表示する", () => {
    const error = source.match(/<Text\b[^>]*>\s*\{errorMessage\}\s*<\/Text>/)?.[0];
    expect(error).toContain('accessibilityRole="alert"');
  });

  it("既存の認証先、トークン保存、成功後の遷移を維持する", () => {
    expect(source).toMatch(/post<JwtCreateResponse>\("\/auth\/jwt\/create\/",\s*\{/);
    expect(source).toMatch(/await setTokens\(data\.access, data\.refresh\);\s*router\.replace\("\/mypage"\);/);
  });

  it("戻る履歴がなければマイページへ遷移する", () => {
    expect(source).toContain('router.canGoBack() ? router.back() : router.replace("/mypage")');
  });
});
