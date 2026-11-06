// 根拠一覧を表示する2画面が、値の無い行(value: null)で値の行を出さないことを検証する
// (mypageAccountDeletion.test.ts と同じくソースをテキストとして読む)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

describe.each([
  ["相談結果画面", "app/concierge/index.tsx"],
  ["神社詳細画面", "app/shrines/[id].tsx"],
])("%s の根拠一覧", (_name, path) => {
  const source = readFileSync(resolve(mobileRoot, path), "utf8");

  it("keyは buildReasonFactItems が作る item.key を使う", () => {
    expect(source).toContain("key={item.key}");
  });

  it("値があるときだけ値の行を表示する", () => {
    expect(source).toContain(
      "{item.value ? <Text style={styles.reasonFactText}>{item.value}</Text> : null}",
    );
  });
});
