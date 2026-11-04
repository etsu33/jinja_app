// MyPage「退会する」導線の構造を検証する(mypageContactLink.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/mypage/index.tsx"), "utf8");

describe("MyPage 退会導線", () => {
  it("「設定・サポート」セクションの設定カードの直後に「退会する」カードを置く", () => {
    const section = source.slice(source.indexOf("設定・サポート"));
    const settingsIndex = section.indexOf('title="設定"');
    const deleteIndex = section.indexOf('title="退会する"');
    const termsIndex = section.indexOf('title="利用規約"');

    expect(settingsIndex).toBeGreaterThan(-1);
    expect(deleteIndex).toBeGreaterThan(settingsIndex);
    expect(deleteIndex).toBeLessThan(termsIndex);
  });

  it("確認ダイアログを2段階で出してから退会処理を呼ぶ", () => {
    expect(source).toContain("ACCOUNT_DELETION_MESSAGES.confirmTitle");
    expect(source).toContain("ACCOUNT_DELETION_MESSAGES.finalConfirmTitle");
    expect(source.indexOf("ACCOUNT_DELETION_MESSAGES.confirmTitle")).toBeLessThan(
      source.indexOf("ACCOUNT_DELETION_MESSAGES.finalConfirmTitle"),
    );
    expect(source).toContain("deleteAccount()");
  });

  it("成功時はトップへ遷移して「退会しました」を表示する", () => {
    expect(source).toMatch(/router\.replace\("\/"\);\s*Alert\.alert\(ACCOUNT_DELETION_MESSAGES\.done\)/);
  });
});
