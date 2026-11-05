// Premium画面のログイン案内(AuthPrompt)が「あとで」で閉じることを検証する
// (mypageAccountDeletion.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/premium/index.tsx"), "utf8");
const promptBlock = source.slice(source.indexOf("<AuthPrompt"));

describe("Premium画面 ログイン案内", () => {
  it("未ログインでも、閉じた後は案内を表示しない", () => {
    expect(promptBlock).toMatch(/visible=\{state\.kind === "unauthenticated" && !authPromptDismissed\}/);
  });

  it("閉じる操作では、案内を閉じた状態にしてからマイページへ移る", () => {
    expect(promptBlock).toMatch(/setAuthPromptDismissed\(true\);\s*router\.replace\("\/mypage"\);/);
  });
});
