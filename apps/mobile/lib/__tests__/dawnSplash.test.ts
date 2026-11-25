// 起動時の DawnSplash が、ネイティブSplashに隠れたまま終わらないことを固定する。
//
// app.config.ts に expo-splash-screen の plugin を入れてネイティブSplashが
// 実在するようになってから、release build で実際に起きた不具合:
//   hideAsync() を投げっぱなしにして即タイマーを始めると、最前面のネイティブ
//   Splashが消えるまでの間に保持時間とフェードを消化してしまい、この画面が
//   一度も見えないまま本編へ抜ける。
//
// 他の契約テストと同じく、ソースをテキストとして読む。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { dawn } from "../../design/theme";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

const splash = withoutComments(
  readFileSync(resolve(mobileRoot, "components/common/DawnSplash.tsx"), "utf8"),
);
const appConfig = readFileSync(resolve(mobileRoot, "app.config.ts"), "utf8");

describe("起動Splashの順序", () => {
  it("ネイティブSplashを隠し終えてから保持を始める", () => {
    // hideAsync() の解決後に startHold() を呼ぶ形であること。
    expect(splash).toMatch(/SplashScreen\.hideAsync\(\)[\s\S]{0,200}?\.then\([\s\S]{0,200}?startHold\(\)/);
  });

  it("hideAsync を待たずにタイマーを始めない", () => {
    // 旧実装: hideAsync() を投げっぱなしにし、直後に setTimeout していた。
    expect(splash).not.toMatch(/void SplashScreen\.hideAsync\(\)\.catch\([^)]*\);\s*\n/);
    // setTimeout は startHold の中だけに置く。
    const timers = splash.match(/setTimeout\(/g) ?? [];
    expect(timers).toHaveLength(1);
    expect(splash).toMatch(/const startHold = \(\) => \{[\s\S]*?setTimeout\(/);
  });

  it("hideAsync が失敗しても本編へ進む", () => {
    // ネイティブSplashに留まり続けると、アプリが起動しないように見える。
    expect(splash).toMatch(/\.catch\(\(\) => undefined\)/);
  });

  it("後片付けでタイマーを止める", () => {
    expect(splash).toMatch(/cancelled = true;[\s\S]{0,80}clearTimeout\(timer\)/);
  });
});

describe("ネイティブSplashとの色の継ぎ目", () => {
  it("app.config.ts の背景色が朝焼けの先頭と同じ", () => {
    // ここがずれると、ネイティブSplashから DawnSplash へ移る瞬間に色が飛ぶ。
    const first = dawn.colors[0];
    expect(appConfig).toContain(`backgroundColor: "${first}"`);
  });
});
