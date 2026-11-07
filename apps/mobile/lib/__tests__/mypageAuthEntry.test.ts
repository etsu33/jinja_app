// MyPage のログイン・新規登録の入口を検証する(mypageAccountDeletion.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/mypage/index.tsx"), "utf8");
const body = source.slice(source.indexOf("export default function MyPageScreen"));

describe("MyPage ログイン・新規登録の入口", () => {
  it("「アカウント」セクションを、ログイン中も未ログインのときも出す", () => {
    expect(body).toMatch(/\{loggedIn \? \(\s*<View style=\{styles\.section\}>\s*<Text style=\{styles\.sectionTitle\}>アカウント<\/Text>/);
    expect(body).toMatch(/\) : \(\s*<View style=\{styles\.section\}>\s*<Text style=\{styles\.sectionTitle\}>アカウント<\/Text>/);
  });

  it("ログイン中は、ユーザー名(取れなければ「ログイン中」)と「ログアウト」を出し、ログイン・新規登録は出さない", () => {
    const loggedInBranch = body.slice(body.indexOf("{loggedIn ? ("), body.indexOf(") : (", body.indexOf("{loggedIn ? (")));

    expect(loggedInBranch).toContain("title={accountUsername ?? LOGOUT_MESSAGES.signedInFallbackName}");
    expect(loggedInBranch).toContain('actionLabel="ログアウト"');
    expect(loggedInBranch).toContain("onPress={confirmAndLogout}");
    expect(loggedInBranch).not.toContain('title="ログイン"');
    expect(loggedInBranch).not.toContain('title="新規登録"');
  });

  it("未ログインのときは「ログイン」「新規登録」を出し、ログアウトは出さない", () => {
    const start = body.indexOf(") : (", body.indexOf("{loggedIn ? ("));
    const notLoggedInBranch = body.slice(start, body.indexOf(">プロフィール<"));

    expect(notLoggedInBranch).toContain('title="ログイン"');
    expect(notLoggedInBranch).toContain('title="新規登録"');
    expect(notLoggedInBranch).not.toContain("ログアウト");
  });

  it("「ログアウト」は確認を出してから処理し、終わったらその場で表示を切り替える", () => {
    expect(source).toMatch(/confirmLogout\(Alert\.alert, \(\) => \{\s*void runLogout\(\);/);
    expect(source).toMatch(/await logout\(\);\s*setLoggedIn\(false\);\s*setAccountUsername\(null\);/);
  });

  it("ログイン中だけユーザー名を取りにいく", () => {
    expect(source).toMatch(/if \(!value\) \{\s*setAccountUsername\(null\);\s*return;\s*\}[\s\S]*fetchAccountUsername\(\)/);
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
