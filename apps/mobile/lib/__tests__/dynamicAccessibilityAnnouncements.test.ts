import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const concierge = readFileSync(new URL("../../app/concierge/index.tsx", import.meta.url), "utf8");
const signup = readFileSync(new URL("../../app/signup.tsx", import.meta.url), "utf8");
const premium = readFileSync(new URL("../../app/premium/index.tsx", import.meta.url), "utf8");

describe("Conciergeの結果通知", () => {
  it("推薦APIの成功時だけ、0件を含む結果件数を通知する", () => {
    expect(concierge).toMatch(/import \{[^}]*\bAccessibilityInfo\b[^}]*\} from "react-native";/);
    expect(concierge).toMatch(
      /const recommendations = await fetchConciergeRecommendations\([\s\S]*?\);\s*setResults\(recommendations\);\s*AccessibilityInfo\.announceForAccessibility\(\s*`神社の提案結果を更新しました。\$\{recommendations\.length\}件です。`,?\s*\);\s*\} catch/,
    );
    expect(concierge.match(/AccessibilityInfo\.announceForAccessibility\(/g)).toHaveLength(1);
  });

  it("通信失敗をalertで伝え、前回結果を保持する", () => {
    expect(concierge).toMatch(/<Text\b[^>]*accessibilityRole="alert"[^>]*>\s*\{errorMessage\}\s*<\/Text>/);
    expect(concierge).toContain(
      'setErrorMessage("通信に失敗しました。前回の結果を表示したまま、もう一度相談できます。");',
    );
    expect(concierge.match(/\bsetResults\(/g)).toHaveLength(1);
  });
});

describe("Signupのエラー通知", () => {
  it.each(["username", "email", "password", "form"])("%s のエラーをalertで伝える", (field) => {
    const error = signup.match(/<Text\b[^>]*>\s*\{errors\.\w+\}\s*<\/Text>/g)
      ?.find((tag) => tag.includes(`{errors.${field}}`));
    expect(error).toContain('accessibilityRole="alert"');
  });

  it("既存の入力検証と登録成功後のMyPage遷移を維持する", () => {
    expect(signup).toMatch(/const validationErrors = validateSignupInput\(input\);\s*if \(hasSignupErrors\(validationErrors\)\) \{\s*setErrors\(validationErrors\);\s*return;/);
    expect(signup).toMatch(/const result = await signupAndLogin\(input\);\s*if \(result\.kind === "success"\) \{\s*router\.replace\("\/mypage"\);/);
  });
});

describe("Premiumの決済エラー通知", () => {
  it("決済エラーをalertで伝え、既存のチェックアウト処理を維持する", () => {
    expect(premium).toMatch(/<Text\b[^>]*accessibilityRole="alert"[^>]*>\s*\{checkoutError\}\s*<\/Text>/);
    expect(premium).toMatch(/await createBillingCheckoutSession\(\{\s*successUrl: CHECKOUT_SUCCESS_URL,\s*cancelUrl: CHECKOUT_CANCEL_URL,\s*\}\)/);
    expect(premium).toContain("await Linking.openURL(session.checkout_url);");
  });
});
