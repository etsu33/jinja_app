// App Store / Google Play がアイコンに課す条件を、提出前ではなくここで落とす。
//
// とくにアルファチャンネルは、App Store Connect へのアップロード時に
// "Invalid large app icon" で弾かれる。ビルドが通ってもそこで止まるので、
// 画像の中身をバイト列から直接検査する。
//
// 他の契約テストと同じく、ソースをテキスト/バイト列として読む(描画はしない)。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

/** PNG の IHDR から幅・高さ・カラータイプを読む。 */
function readPngHeader(relativePath: string) {
  const buf = readFileSync(resolve(mobileRoot, relativePath));

  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  expect(buf.subarray(0, 8).equals(signature), `${relativePath} が PNG ではない`).toBe(true);
  expect(buf.subarray(12, 16).toString("ascii")).toBe("IHDR");

  return {
    width: buf.readUInt32BE(16),
    height: buf.readUInt32BE(20),
    // 0=グレー 2=RGB 3=パレット 4=グレー+α 6=RGBA
    colorType: buf.readUInt8(25),
    bytes: buf.length,
  };
}

// PNG のカラータイプのうち、アルファを持つもの。
const COLOR_TYPES_WITH_ALPHA = [4, 6];

const appConfig = readFileSync(resolve(mobileRoot, "app.config.ts"), "utf8");

describe("アプリアイコン", () => {
  it("app.config.ts がアイコンを指している", () => {
    expect(appConfig).toContain('icon: "./assets/icon.png"');
  });

  it("1024x1024 の正方形である", () => {
    const { width, height } = readPngHeader("assets/icon.png");
    expect(width).toBe(1024);
    expect(height).toBe(1024);
  });

  it("アルファチャンネルを持たない", () => {
    // 透過を含むと App Store Connect のアップロードで弾かれる。
    const { colorType } = readPngHeader("assets/icon.png");
    expect(COLOR_TYPES_WITH_ALPHA).not.toContain(colorType);
  });
});

describe("Android アダプティブアイコン", () => {
  it("app.config.ts が前景と背景色を持つ", () => {
    expect(appConfig).toContain('foregroundImage: "./assets/adaptive-icon.png"');
    // 背景色は元画像の地と同じ紺。継ぎ目が出ないようにする。
    expect(appConfig).toMatch(/backgroundColor: "#010E28"/);
  });

  it("前景も 1024x1024 である", () => {
    const { width, height } = readPngHeader("assets/adaptive-icon.png");
    expect(width).toBe(1024);
    expect(height).toBe(1024);
  });
});
