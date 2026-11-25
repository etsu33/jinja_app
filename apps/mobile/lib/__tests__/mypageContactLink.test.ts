// MyPage「お問い合わせ」カードの有効化と、mailto契約の検証。
//
// Mobileのテスト環境は environment: "node" で、React Nativeの
// レンダリング基盤を持たない。そのため routerStructure.test.ts と同じく
// app配下のソースをテキストとして読み、構造と契約を検証する。
// (このタスクのために新しいテスト基盤は追加しない)
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(mobileRoot, "app/(tabs)/mypage/index.tsx"), "utf8");

/** <MyPageCard ... /> を1枚ずつ取り出し、title -> props本文 のMapにする。 */
function readCards(): Map<string, string> {
  const cards = new Map<string, string>();
  for (const [, props] of source.matchAll(/<MyPageCard\s+([\s\S]*?)\/>/g)) {
    const title = props.match(/title="([^"]+)"/)?.[1];
    if (title) cards.set(title, props);
  }
  return cards;
}

/** ソース中の文字列定数を取り出す。 */
function readConst(name: string): string {
  const value = source.match(new RegExp(`const ${name} = "([^"]+)"`))?.[1];
  if (value === undefined) throw new Error(`${name} が見つからない`);
  return value;
}

// Mother Ship承認済みの契約
const APPROVED_EMAIL = "j33db05@gmail.com";
const APPROVED_SUBJECT = "KAMI MUSUBI お問い合わせ";
const APPROVED_MAILTO =
  "mailto:j33db05@gmail.com?subject=KAMI%20MUSUBI%20%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B";

describe("MyPage お問い合わせカード", () => {
  it("お問い合わせカードがonPressを持ち、activeになる", () => {
    expect(readCards().get("お問い合わせ")).toMatch(/onPress=\{openContactMail\}/);
  });

  it("「設定・サポート」セクションのカードがすべてonPressを持つ", () => {
    // 押せない飾りのカードを置かない(App Store Review Guideline 2.1 / 4.2)。
    // 中身の無かった「設定」カードは削除し、規約類はWebページへ繋いだ。
    const support = source.slice(source.indexOf("設定・サポート"));

    expect(support).not.toContain('title="設定"');
    for (const [, props] of support.matchAll(/<MyPageCard\s+([\s\S]*?)\/>/g)) {
      expect(props).toMatch(/onPress=/);
    }
  });

  it("利用規約とプライバシーポリシーをWebページへ繋ぐ", () => {
    // App Store Review Guideline 3.1.2 は、自動更新サブスクリプションを持つ
    // アプリに「機能する」リンクをバイナリ内へ置くことを求める。
    expect(source).toMatch(/title=\{LEGAL_LABELS\.terms\}[\s\S]*?onPress=\{openTerms\}/);
    expect(source).toMatch(/title=\{LEGAL_LABELS\.privacy\}[\s\S]*?onPress=\{openPrivacy\}/);
    expect(source).toMatch(/openLegalDocument\("terms", Linking\.openURL\)/);
    expect(source).toMatch(/openLegalDocument\("privacy", Linking\.openURL\)/);
  });

  it("宛先と件名を可読な定数として保持する", () => {
    expect(readConst("CONTACT_EMAIL")).toBe(APPROVED_EMAIL);
    expect(readConst("CONTACT_SUBJECT")).toBe(APPROVED_SUBJECT);
  });

  it("subjectをencodeURIComponentで構築する", () => {
    expect(source).toMatch(/encodeURIComponent\(CONTACT_SUBJECT\)/);
  });

  it("組み立てられるmailtoが承認契約に一致する", () => {
    const url = `mailto:${readConst("CONTACT_EMAIL")}?subject=${encodeURIComponent(readConst("CONTACT_SUBJECT"))}`;
    expect(url).toBe(APPROVED_MAILTO);
  });

  it("mailtoに生の非ASCIIが残らず、デコードすると承認済みの件名になる", () => {
    const url = `mailto:${readConst("CONTACT_EMAIL")}?subject=${encodeURIComponent(readConst("CONTACT_SUBJECT"))}`;
    // 失敗時に該当文字が見えるよう、差分として表明する。
    expect([...url].filter((ch) => ch.charCodeAt(0) > 0x7f)).toEqual([]);

    const parsed = new URL(url);
    expect(parsed.protocol).toBe("mailto:");
    expect(parsed.pathname).toBe(APPROVED_EMAIL);
    expect(parsed.searchParams.get("subject")).toBe(APPROVED_SUBJECT);
  });

  it("openURLのrejectを未処理のまま残さない", () => {
    expect(source).toMatch(/Linking\.openURL\(CONTACT_MAILTO_URL\)\.catch\(/);
  });

  it("expo-linkingを使う（新しいdependencyを足さない）", () => {
    expect(source).toMatch(/import \* as Linking from "expo-linking";/);
  });
});
