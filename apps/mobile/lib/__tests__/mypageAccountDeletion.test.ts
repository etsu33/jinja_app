// MyPage「退会する」導線の構造を検証する(mypageContactLink.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/(tabs)/mypage/index.tsx"), "utf8");

describe("MyPage 退会導線", () => {
  it("「設定・サポート」セクションの先頭に「退会する」カードを置き、規約類より前に出す", () => {
    // 「設定」カードは中身の無い「準備中」表示だったため削除した
    // (App Store Review Guideline 2.1 / 4.2)。退会がセクションの先頭になる。
    const section = source.slice(source.indexOf("設定・サポート"));
    const deleteIndex = section.indexOf('title="退会する"');
    const termsIndex = section.indexOf("LEGAL_LABELS.terms");

    expect(section).not.toContain('title="設定"');
    expect(deleteIndex).toBeGreaterThan(-1);
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
