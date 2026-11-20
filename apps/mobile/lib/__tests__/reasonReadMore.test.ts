// 推薦結果の理由文は3行で畳み、切れているときだけ「続きを読む」を出す。
//
// 以前は numberOfLines={3} で切りっぱなしで、続きがあることが分からなかった。
// 全文は神社詳細で読めるが、そこへ行く手がかりが無い状態だった。
//
// 重要な前提: これは表示だけの変更。Backend へ送る相談内容も、返ってきた
// 文章も変えない。「相談内容が提案に反映される」は変わらない。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

const concierge = withoutComments(
  readFileSync(resolve(mobileRoot, "app/(tabs)/concierge/index.tsx"), "utf8"),
);

// 理由文の節。すべて同じ部品で描く。
const SECTIONS = [
  "この神社について",
  "今の相談とのつながり",
  "参拝前にできること",
  "この神社を選んだ理由",
];

describe("理由文の畳みかた", () => {
  it.each(SECTIONS)("%s は ReasonSection で描く", (label) => {
    expect(concierge).toContain(`<ReasonSection label="${label}"`);
  });

  it("理由文を素の Text で切りっぱなしにしない", () => {
    // 切れていることが分からない表示を残さない。
    expect(concierge).not.toMatch(/styles\.cardReason\} numberOfLines=\{3\}/);
  });

  it("畳む行数を一箇所で決める", () => {
    expect(concierge).toMatch(/const REASON_COLLAPSED_LINES = 3/);
    expect(concierge).toMatch(/numberOfLines=\{expanded \? undefined : REASON_COLLAPSED_LINES\}/);
  });

  it("行数を実測してから「続きを読む」の要否を決める", () => {
    // 文字数で決めると、短いが折り返す文と、長いが収まる文を取り違える。
    expect(concierge).toMatch(/onTextLayout=\{handleMeasure\}/);
    expect(concierge).toMatch(/lines\.length > REASON_COLLAPSED_LINES/);
    // 測り終えるまでの写しは読み上げに乗せない。
    expect(concierge).toMatch(/accessibilityElementsHidden[\s\S]{0,120}?onTextLayout/);
  });

  it("切れていないときは出さない", () => {
    expect(concierge).toMatch(/\{truncatable \? \([\s\S]{0,400}?続きを読む/);
  });

  it("タップ領域が 44pt 以上ある", () => {
    expect(concierge).toMatch(/readMore: \{[\s\S]*?minHeight: 44/);
  });

  it("開いたあと閉じられる", () => {
    expect(concierge).toContain('expanded ? "閉じる" : "続きを読む"');
  });
});

describe("送信する内容は変えない", () => {
  it("相談文を切り詰めない", () => {
    // Backend へ渡すのは全文。表示だけを畳む。
    expect(concierge).toMatch(/consultation: queryText/);
    expect(concierge).not.toMatch(/queryText\.slice\(/);
    expect(concierge).not.toMatch(/queryText\.substring\(/);
  });

  it("入力に文字数制限をかけない", () => {
    // 入力項目の削除・追加、バリデーション変更は変更禁止事項。
    const home = withoutComments(
      readFileSync(resolve(mobileRoot, "app/(tabs)/index.tsx"), "utf8"),
    );
    const consultation = withoutComments(
      readFileSync(resolve(mobileRoot, "app/consultation/index.tsx"), "utf8"),
    );

    for (const [name, source] of [["ホーム", home], ["相談画面", consultation]] as const) {
      expect(source, `${name} に maxLength がある`).not.toContain("maxLength");
    }
  });
});
