// 相談内容を書き直したとき、前の相談で選んだ「願うご縁」がそのまま効いてしまう。
// 利用者はこれに気づけず、ずれた条件の提案を受け取る。
//
// 方針は「消さずに知らせる」。誤字の修正でも選択が消えるのは煩わしいため、
// 選択は保持したまま注意書きだけ出し、変えるかどうかは利用者に委ねる。
//
// 他の契約テストと同じく、画面のソースをテキストとして読む。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { kamimusubiLight as light } from "../../design/theme";
import { GORIYAKU_OPTIONS } from "../conditionPayload";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

const consultation = withoutComments(
  readFileSync(resolve(mobileRoot, "app/consultation/index.tsx"), "utf8"),
);

describe("前の相談のご縁が残っているときの注意書き", () => {
  it("相談内容が書き換わったかどうかで判定する", () => {
    // 受け取った文章と、いま入力されている文章の差。これが唯一の判定材料。
    expect(consultation).toMatch(
      /const topicChanged = consultation\.trim\(\) !== \(params\.q \?\? ""\)\.trim\(\)/,
    );
  });

  it("前の相談のご縁が選ばれたままのときだけ出す", () => {
    expect(consultation).toMatch(/const showGoriyakuNotice =\s*\n?\s*topicChanged &&/);
    expect(consultation).toContain("selectedGoriyaku === incomingGoriyaku");
  });

  it("選択を消さない（折衷案）", () => {
    // 注意書きを出すだけで、ご縁の選択は保持する。
    // 自動で外すと、誤字を直しただけでも選び直しになる。
    expect(consultation).not.toMatch(/showGoriyakuNotice[\s\S]{0,200}setSelectedGoriyaku\(undefined\)/);
    expect(consultation).not.toMatch(/topicChanged[\s\S]{0,200}setSelectedGoriyaku\(undefined\)/);
  });

  it("相談文とご縁の意味が合っているかは判定しない", () => {
    // 意味の判定は推薦側の領分。Mobile が対応表を持つと、推薦の意味を
    // 画面側で作ることになる(ブランド指示書の変更禁止事項)。
    // ご利益のラベルが条件分岐の中に直接書かれていないことで担保する。
    for (const label of GORIYAKU_OPTIONS) {
      expect(consultation).not.toContain(`"${label}"`);
    }
  });

  it("読み上げに乗せ、朱は使わない", () => {
    expect(consultation).toMatch(/accessibilityRole="alert"[\s\S]{0,200}styles\.notice/);
    // 相談フローは夜明け前の暗地。朱も warning(朱系の琥珀)も地に沈むため、
    // 曙色で示す。最も明るい地に対して 5.24。
    expect(consultation).toContain("color: dawnNight.mark");
    expect(consultation).not.toMatch(/notice:[\s\S]{0,300}theme\.vermilion/);
  });

  it("注意書きの文字色は全ての面で AA を満たす", () => {
    const channel = (v: number) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };
    const luminance = (hex: string) => {
      const h = hex.replace("#", "");
      const [r, g, b] = [0, 2, 4].map((i) => channel(parseInt(h.slice(i, i + 2), 16)));
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const contrast = (a: string, b: string) => {
      const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
      return (hi + 0.05) / (lo + 0.05);
    };

    // 注意書きの面は surfaceSoft。
    expect(contrast(light.warning, light.surfaceSoft)).toBeGreaterThanOrEqual(4.5);
  });
});
