// MyPage のログイン・新規登録の入口を検証する(mypageAccountDeletion.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/mypage/index.tsx"), "utf8");
const body = source.slice(source.indexOf("export default function MyPageScreen"));

describe("MyPage ログイン・新規登録の入口", () => {
  it("未ログインのときだけ「アカウント」セクションを出す", () => {
    expect(body).toMatch(/\{loggedIn \? null : \(\s*<View style=\{styles\.section\}>\s*<Text style=\{styles\.sectionTitle\}>アカウント<\/Text>/);
  });

  it("「アカウント」セクションを、プロフィールより上(マイページのいちばん上)に置く", () => {
    const accountIndex = body.indexOf(">アカウント<");
    const profileIndex = body.indexOf(">プロフィール<");

    expect(accountIndex).toBeGreaterThan(-1);
    expect(accountIndex).toBeLessThan(profileIndex);
  });

  it("ログインはログイン画面、新規登録は新規登録画面へ移る", () => {
    const section = body.slice(body.indexOf(">アカウント<"), body.indexOf(">プロフィール<"));

    expect(section).toContain('title="ログイン"');
    expect(section).toContain('router.push("/login")');
    expect(section).toContain('title="新規登録"');
    expect(section).toContain('router.push("/signup")');
  });

  it("画面が表示されるたびにログイン状態を取り直す", () => {
    expect(source).toMatch(/useFocusEffect\(\s*React\.useCallback\(\(\) => \{\s*let mounted = true;\s*isLoggedIn\(\)/);
  });
});
